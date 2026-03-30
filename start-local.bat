@echo off
REM 本地开发启动脚本 (Windows)

echo === XGBoost Training Visualizer 本地启动 ===
echo.

REM 获取项目根目录
set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM 设置环境变量
set WORKSPACE_DIR=%PROJECT_ROOT%workspace
set DATASET_DIR=%PROJECT_ROOT%dataset

echo 1. 启动基础设施 (PostgreSQL, Redis)...
docker compose -f docker/docker-compose.dev.yml up -d postgres redis

echo 等待服务就绪...
timeout /t 3 /nobreak > nul

echo.
echo 2. 创建工作目录...
if not exist "%WORKSPACE_DIR%\splits" mkdir "%WORKSPACE_DIR%\splits"
if not exist "%WORKSPACE_DIR%\models" mkdir "%WORKSPACE_DIR%\models"

echo.
echo 3. 启动后端 API...
cd /d "%PROJECT_ROOT%apps\api"

REM 激活虚拟环境（如果存在）
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM 安装依赖
pip install -q -r requirements.txt 2>nul

REM 运行迁移
python scripts/migrate_db.py 2>nul

REM 启动 API
echo 启动 API 服务 (端口 8000)...
start "API Server" cmd /c "set WORKSPACE_DIR=%WORKSPACE_DIR% && set DATASET_DIR=%DATASET_DIR% && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo.
echo 4. 启动 Worker...
cd /d "%PROJECT_ROOT%apps\worker"
pip install -q -r requirements.txt 2>nul
start "Worker" cmd /c "set WORKSPACE_DIR=%WORKSPACE_DIR% && python -m app.main"

echo.
echo 5. 启动前端...
cd /d "%PROJECT_ROOT%apps\web"
where pnpm >nul 2>nul
if %errorlevel% equ 0 (
    pnpm install --silent 2>nul
    start "Web Server" cmd /c "pnpm dev"
) else (
    npm install --silent 2>nul
    start "Web Server" cmd /c "npm run dev"
)

echo.
echo === 启动完成 ===
echo.
echo 服务地址:
echo   - 前端:     http://localhost:3000
echo   - API:      http://localhost:8000
echo   - API 文档: http://localhost:8000/docs
echo.
echo 按任意键退出此窗口（服务将继续运行）...
pause > nul