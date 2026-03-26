from pathlib import Path

# Get project folder dir
current_file = Path(__file__).resolve()
project_dir = current_file.parent.parent

ENV_PATH = project_dir / ".env"
LOG_PATH = project_dir / "logs"

# Embedding service
# EMBED_SERVICE_URL = "http://192.168.0.143:8083" # Tuo local deployment, port 8083
# EMBED_SERVICE_URL = "http://127.0.0.1:8083" # if the server port 8083 is mapped to local machine
EMBED_SERVICE_URL = "http://172.29.121.236:8083"