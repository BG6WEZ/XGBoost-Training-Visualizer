@echo off
REM Worker 启动脚本 (Windows)
REM 用法: start-local-worker.bat

echo ============================================================
echo XGBoost Training Visualizer - Worker Startup
echo ============================================================

cd /d "%~dp0..\..\worker"

echo [1/3] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found
    exit /b 1
)

echo [2/3] 检查 Redis 连接...
python -c "import redis; r=redis.from_url('redis://localhost:6379'); r.ping(); print('Redis OK')"
if errorlevel 1 (
    echo [WARN] Redis not available, worker may fail
)

echo [3/3] 启动 Worker...
echo ============================================================
echo Worker starting... Press Ctrl+C to stop
echo ============================================================

python -m app.main
