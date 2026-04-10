#!/bin/bash

echo "========================================"
echo "🚀 开启AI服务"
echo "========================================"

# Set Python path
export PYTHONPATH=/app:$PYTHONPATH
# Ensure required directories exist
mkdir -p /app/logs /app/data /app/models /app/persistence 2>/dev/null || true
chmod 755 /app/logs /app/data 2>/dev/null || true
# Set working directory
cd /app || { echo "❌ 转换 /app 目录失败"; exit 1; }

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
    echo "🔍 [DEBUG] log_file 长度: ${#log_file}" >&2

    # Check target directory
    local log_dir="$(dirname "${log_file}")"
    echo "🔍 [DEBUG] log_dir: [${log_dir}]" >&2
    echo "🔍 [DEBUG] 目录存在: $(test -d "${log_dir}" && echo YES || echo NO)" >&2
    echo "🔍 [DEBUG] 目录可写: $(test -w "${log_dir}" && echo YES || echo NO)" >&2

    # Try a simple redirect test with the exact variable
    if ! touch "${log_file}.test" 2>&1; then
        echo "❌ [DEBUG] 无法使用该变量创建文件" >&2
    else
        echo "✅ [DEBUG] 使用用变量创建文件成功" >&2
        rm -f "${log_file}.test"
    fi

    # Start service in background
    python "$script_path" > "$log_file" 2>&1 &
    local pid=$!
    echo "$service_name PID: $pid"

    # Wait for port to be ready
    echo "⏳ 等待 $service_name 开启..."
    for i in {1..60}; do
        if ! check_pid $pid; then
            echo "❌ $service_name 进程终止"
            tail -20 "$log_file"
            return 1
        fi

        if check_port $port; then
            echo "✅ $service_name 正在监听端口 $port"
            return 0
        fi

        sleep 2
    done

    echo "❌ $service_name 120秒内启动失败"
    tail -50 "$log_file"
    return 1
}

# Main startup sequence
echo "开启AI模型服务..."
if ! start_service "AI模型服务" "models/ai_service.py" 5002 "/app/logs/model.log"; then
    echo "AI模型服务启动失败"
    exit 1
fi

echo "等待检查AI模型服务健康..."
sleep 10  # Give it time to fully initialize
if check_health 5002; then
    echo "✅ AI模型服务健康检查通过"
else
    echo "⚠️ AI模型服务健康检查失败，但仍将继续..."
fi

echo "开启AI网关服务..."
if ! start_service "AI网关服务" "models/ai_gateway_service.py" 5001 "/app/logs/gateway.log"; then
    echo "AI网关服务启动失败"
    exit 1
fi

echo "等待AI网关服务健康检查..."
sleep 5
if check_health 5001; then
    echo "✅ AI网关服务健康检查通过"
else
    echo "⚠️ AI网关服务健康检查失败，但仍将继续..."
fi

echo ""
echo "========================================"
echo "🟢 所有AI服务都在运行"
echo "   AI 网关: http://localhost:5001"
echo "   AI 模型: http://localhost:5002"
echo "========================================"
echo ""

# Clear /tmp
echo "🧹 /tmp 自动清理服务..."
(
  while true; do
    sleep 3600  # clean every hour

    echo "🧹 安全清理 /tmp ($(date))..."

    # only clean files inactive more than one hours
    find /tmp -type f -amin +60 -not -path '*/.X11-unix/*' -not -path '*/.ICE-unix/*' -delete 2>/dev/null || true

    # only clean empty directories
    find /tmp -type d -empty -amin +60 -delete 2>/dev/null || true

    # show status after clear
    tmp_usage=$(du -sh /tmp 2>/dev/null | cut -f1 || echo "0B")
    echo "✅ /tmp 清理结束，当前占用: $tmp_usage"
  done
)&
echo "✅ 背景任务开启"

# Keep container alive
echo ""
echo "📊 正在监控服务..."
echo "按 Ctrl+C 停止所有服务"
tail -f /dev/null