#!/bin/bash
# 本地开发启动脚本

set -e

echo "=== XGBoost Training Visualizer 本地启动 ==="

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行，请先启动 Docker"
    exit 1
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 设置环境变量
export WORKSPACE_DIR="$PROJECT_ROOT/workspace"
export DATASET_DIR="$PROJECT_ROOT/dataset"

echo ""
echo "1. 启动基础设施 (PostgreSQL, Redis)..."
docker compose -f docker/docker-compose.dev.yml up -d postgres redis

# 等待服务就绪
echo "   等待服务就绪..."
sleep 3

echo ""
echo "2. 创建工作目录..."
mkdir -p "$WORKSPACE_DIR/splits"
mkdir -p "$WORKSPACE_DIR/models"

echo ""
echo "3. 启动后端 API..."
cd "$PROJECT_ROOT/apps/api"
if [ ! -d ".venv" ]; then
    echo "   创建虚拟环境..."
    python -m venv .venv
fi

# 激活虚拟环境（如果存在）
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate  # Windows
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate  # Unix
fi

# 安装依赖
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt

# 运行迁移
python scripts/migrate_db.py 2>/dev/null || echo "   数据库迁移跳过（可能已完成）"

# 后台启动 API
echo "   启动 API 服务 (端口 8000)..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo ""
echo "4. 启动 Worker..."
cd "$PROJECT_ROOT/apps/worker"
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
python -m app.main &
WORKER_PID=$!

echo ""
echo "5. 启动前端..."
cd "$PROJECT_ROOT/apps/web"
if command -v pnpm &> /dev/null; then
    pnpm install --silent 2>/dev/null || pnpm install
    pnpm dev &
else
    npm install
    npm run dev &
fi
WEB_PID=$!

echo ""
echo "=== 启动完成 ==="
echo ""
echo "服务地址:"
echo "  - 前端:     http://localhost:3000"
echo "  - API:      http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo ""
echo "进程 ID:"
echo "  - API:    $API_PID"
echo "  - Worker: $WORKER_PID"
echo "  - Web:    $WEB_PID"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待任意子进程结束
wait