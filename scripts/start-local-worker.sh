#!/bin/bash
# Worker 启动脚本 (Unix/Linux/macOS)
# 用法: ./start-local-worker.sh

set -e

echo "============================================================"
echo "XGBoost Training Visualizer - Worker Startup"
echo "============================================================"

cd "$(dirname "$0")/../apps/worker"

echo "[1/3] 检查 Python 环境..."
python3 --version || python --version

echo "[2/3] 检查 Redis 连接..."
python3 -c "import redis; r=redis.from_url('redis://localhost:6379'); r.ping(); print('Redis OK')" 2>/dev/null || echo "[WARN] Redis not available, worker may fail"

echo "[3/3] 启动 Worker..."
echo "============================================================"
echo "Worker starting... Press Ctrl+C to stop"
echo "============================================================"

python3 -m app.main || python -m app.main
