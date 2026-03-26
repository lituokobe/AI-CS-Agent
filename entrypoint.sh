#!/bin/bash

echo "========================================"
echo "🚀 Starting AI Services Container"
echo "========================================"

# Set Python path
export PYTHONPATH=/app:$PYTHONPATH
# Ensure required directories exist
mkdir -p /app/logs /app/data /app/models /app/persistence 2>/dev/null || true
chmod 755 /app/logs /app/data 2>/dev/null || true
# Set working directory
cd /app || { echo "❌ Failed to change to /app directory"; exit 1; }

# Function to check if port is listening
check_port() {
    local port=$1
    # Try multiple methods to check port
    timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$port" 2>/dev/null && return 0
    return 1
}

# Function to check process
check_pid() {
    kill -0 $1 2>/dev/null
}

# Health check with endpoint-specific paths
check_health() {
    local port=$1
    if [ "$port" = "5001" ]; then
        # Gateway health endpoint
        curl -f -s http://localhost:5001/gateway/health >/dev/null 2>&1
    else
        # Model service health endpoint
        curl -f -s http://localhost:$port/health >/dev/null 2>&1
    fi
}

# Start service function
start_service() {
    local service_name=$1
    local script_path=$2
    local port=$3
    local log_file=$4

    echo "Starting $service_name (port $port)..."

    # 🔍 DEBUG: Reveal exact log_file value
    echo "🔍 [DEBUG] log_file raw: [${log_file}]" >&2
    echo "🔍 [DEBUG] log_file hex: $(printf '%s' "${log_file}" | xxd -p 2>/dev/null || echo 'xxd not available')" >&2
    echo "🔍 [DEBUG] log_file length: ${#log_file}" >&2

    # Check target directory
    local log_dir="$(dirname "${log_file}")"
    echo "🔍 [DEBUG] log_dir: [${log_dir}]" >&2
    echo "🔍 [DEBUG] dir exists: $(test -d "${log_dir}" && echo YES || echo NO)" >&2
    echo "🔍 [DEBUG] dir writable: $(test -w "${log_dir}" && echo YES || echo NO)" >&2

    # Try a simple redirect test with the exact variable
    if ! touch "${log_file}.test" 2>&1; then
        echo "❌ [DEBUG] Cannot create file with this variable value!" >&2
    else
        echo "✅ [DEBUG] File creation with variable succeeded" >&2
        rm -f "${log_file}.test"
    fi

    # Start service in background
    python "$script_path" > "$log_file" 2>&1 &
    local pid=$!
    echo "$service_name PID: $pid"

    # Wait for port to be ready
    echo "⏳ Waiting for $service_name to start..."
    for i in {1..60}; do
        if ! check_pid $pid; then
            echo "❌ $service_name process died!"
            tail -20 "$log_file"
            return 1
        fi

        if check_port $port; then
            echo "✅ $service_name is listening on port $port"
            return 0
        fi

        sleep 2
    done

    echo "❌ $service_name failed to start within 120 seconds"
    tail -50 "$log_file"
    return 1
}

# Main startup sequence
echo "Starting AI Model Service..."
if ! start_service "AI Model Service" "models/ai_service.py" 5002 "/app/logs/model.log"; then
    echo "Failed to start AI Model Service"
    exit 1
fi

echo "Waiting for AI Model Service health..."
sleep 10  # Give it time to fully initialize
if check_health 5002; then
    echo "✅ AI Model Service health check passed"
else
    echo "⚠️ AI Model Service health check failed, but continuing..."
fi

echo "Starting AI Gateway Service..."
if ! start_service "AI Gateway Service" "models/ai_gateway_service.py" 5001 "/app/logs/gateway.log"; then
    echo "Failed to start AI Gateway Service"
    exit 1
fi

echo "Waiting for AI Gateway Service health..."
sleep 5
if check_health 5001; then
    echo "✅ AI Gateway Service health check passed"
else
    echo "⚠️ AI Gateway Service health check failed, but continuing..."
fi

echo ""
echo "========================================"
echo "🟢 All services are running!"
echo "   AI Gateway: http://localhost:5001"
echo "   AI Model:   http://localhost:5002"
echo "========================================"
echo ""

# Clear /tmp
echo "🧹 /tmp auto-clearance service..."
(
  while true; do
    sleep 3600  # clean every hour

    echo "🧹 safe clearance for /tmp ($(date))..."

    # only clean files inactive more than one hours
    find /tmp -type f -amin +60 -not -path '*/.X11-unix/*' -not -path '*/.ICE-unix/*' -delete 2>/dev/null || true

    # only clean empty directories
    find /tmp -type d -empty -amin +60 -delete 2>/dev/null || true

    # show status after clear
    tmp_usage=$(du -sh /tmp 2>/dev/null | cut -f1 || echo "0B")
    echo "✅ /tmp clearance finished, current usage: $tmp_usage"
  done
)&
echo "✅ Background tasks started"

# Keep container alive
echo ""
echo "📊 Monitoring services..."
echo "Press Ctrl+C to stop all services"
tail -f /dev/null