# XGBoost Training Visualizer

面向建筑能耗时序建模的 XGBoost 训练可视化工作台。

**当前版本**: RC1 (2026-03-29)

## 项目概述

本项目提供一套完整的机器学习实验工作流，支持：
- **数据资产管理**：扫描、登记和管理多源数据集
- **实验配置**：配置 XGBoost 训练参数
- **训练监控**：实时监控训练进度
- **结果分析**：查看训练结果、特征重要性
- **实验对比**：对比多个实验结果

## 技术栈

- **后端**: FastAPI + PostgreSQL + Redis
- **前端**: React + TypeScript + TailwindCSS
- **训练**: XGBoost + Python Worker
- **存储**: Local / MinIO

## 快速开始

### 环境要求

- Python 3.11+ (推荐 3.11 或 3.12，避免 3.14 的科学计算包兼容问题)
- Node.js 20+ (项目要求 >= 20.0.0)
- pnpm 9.0+ (项目要求 >= 9.0.0)
- Docker & Docker Compose (推荐 Docker Compose V2)

### 快速启动（推荐）

项目提供了便捷的启动脚本，在项目根目录执行：

```bash
# 安装所有 Python 依赖
pnpm install:py

# 启动基础设施 (PostgreSQL, Redis, MinIO)
pnpm docker:dev

# 运行数据库迁移
pnpm db:migrate

# 启动所有服务 (API + Worker + Web)
pnpm dev
```

### 手动启动（分步骤）

#### 1. 启动基础设施

```bash
# 启动 PostgreSQL 和 Redis (Docker Compose V2)
docker compose -f docker/docker-compose.dev.yml up -d postgres redis

# 或使用 Docker Compose V1
docker-compose -f docker/docker-compose.dev.yml up -d postgres redis
```

#### 2. 启动后端 API

```bash
cd apps/api

# 安装依赖
pip install -r requirements.txt

# 设置环境变量 (Windows PowerShell)
$env:WORKSPACE_DIR = "$(pwd)\..\..\workspace"
$env:DATASET_DIR = "$(pwd)\..\..\dataset"

# 设置环境变量 (Unix/Linux/macOS)
export WORKSPACE_DIR="$(pwd)/../../workspace"
export DATASET_DIR="$(pwd)/../../dataset"

# 运行数据库迁移 (方式一：使用迁移脚本)
python scripts/migrate_db.py --init

# 运行数据库迁移 (方式二：使用 Alembic)
alembic upgrade head

# 启动 API 服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 3. 启动 Worker

```bash
cd apps/worker

# 安装依赖
pip install -r requirements.txt

# 设置环境变量 (Windows PowerShell)
$env:WORKSPACE_DIR = "$(pwd)\..\..\workspace"

# 设置环境变量 (Unix/Linux/macOS)
export WORKSPACE_DIR="$(pwd)/../../workspace"

# 启动 Worker
python -m app.main
```

#### 4. 启动前端

```bash
cd apps/web

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

#### 5. 访问应用

- 前端: http://localhost:3000
- API 文档: http://localhost:8000/docs

## 使用流程

### 1. 扫描数据资产

1. 访问「数据资产」页面
2. 点击「扫描 dataset/ 目录」
3. 查看发现的数据资产列表
4. 点击「登记」将数据资产注册为可训练数据集

### 2. 配置数据集

1. 点击已登记的数据集查看详情
2. 系统自动检测时间列、目标列候选
3. 可选择执行数据切分（随机切分/时间切分）

### 3. 创建实验

1. 访问「实验管理」页面
2. 点击「创建实验」
3. 选择数据集，配置训练参数
4. 点击「启动」开始训练

### 4. 监控训练

1. 访问「训练监控」页面
2. 实时查看训练进度

### 5. 查看结果

1. 点击已完成的实验
2. 查看训练指标、损失曲线、特征重要性
3. 下载训练模型

### 6. 对比实验

1. 访问「结果对比」页面
2. 选择 2-4 个已完成的实验
3. 对比各项指标

## 项目结构

```
.
├── apps/
│   ├── api/           # FastAPI 后端服务
│   │   ├── app/
│   │   │   ├── routers/     # API 路由
│   │   │   ├── models/      # 数据模型
│   │   │   ├── schemas/     # Pydantic 模型
│   │   │   └── services/    # 业务逻辑
│   │   └── tests/           # 测试
│   ├── worker/        # Redis Worker
│   │   └── app/
│   │       ├── tasks/       # 训练任务
│   │       └── storage.py   # 存储适配
│   └── web/           # React 前端
│       └── src/
│           ├── app/         # 应用入口
│           ├── components/  # UI 组件
│           ├── pages/       # 页面组件
│           └── lib/         # API 客户端
├── dataset/           # 数据集目录
├── workspace/         # 工作目录（模型、切分结果等）
├── docs/              # 项目文档
│   ├── architecture/        # 技术架构
│   ├── planning/            # 开发计划
│   └── specification/       # 功能规范
└── docker/            # Docker 配置
```

## 数据资产

项目 `dataset/` 目录包含多个真实数据集：

| 数据源 | 描述 | 适用场景 |
|--------|------|----------|
| HEEW | 多建筑能耗与天气数据 | 单/多建筑回归、切分验证 |
| ASHRAE GEP III | 能源预测竞赛数据 | 基准训练、泛化评估 |
| BDG2 | 建筑数据基因组2 | 多站点基准、跨建筑比较 |
| Bldg59 | 单建筑多传感器数据 | 多源特征融合 |

## API 概览

### 数据资产
- `GET /api/assets/sources` - 列出数据源类型
- `GET /api/assets/scan` - 扫描 dataset/ 目录
- `GET /api/assets/profile` - 分析文件 Schema
- `POST /api/assets/register` - 登记数据资产

### 数据集
- `GET /api/datasets/` - 列出数据集
- `POST /api/datasets/` - 创建数据集
- `GET /api/datasets/{id}` - 获取数据集详情
- `GET /api/datasets/{id}/preview` - 预览数据
- `POST /api/datasets/{id}/split` - 切分数据集

### 实验
- `GET /api/experiments/` - 列出实验
- `POST /api/experiments/` - 创建实验
- `POST /api/experiments/{id}/start` - 启动训练
- `POST /api/experiments/{id}/stop` - 停止训练

### 结果
- `GET /api/results/{id}` - 获取实验结果（包含模型信息）
- `GET /api/results/{id}/feature-importance` - 特征重要性
- `GET /api/results/{id}/metrics-history` - 指标历史
- `GET /api/results/{id}/download-model` - 下载模型文件
- `POST /api/results/compare` - 实验对比

## 环境变量

### API 服务
```bash
DATABASE_URL=postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis
REDIS_URL=redis://localhost:6379/0
WORKSPACE_DIR=./workspace
DATASET_DIR=./dataset
STORAGE_TYPE=local  # 或 minio
```

### Worker
```bash
DATABASE_URL=postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis
REDIS_URL=redis://localhost:6379/0
WORKSPACE_DIR=./workspace
```

### 前端
```bash
VITE_API_URL=http://localhost:8000
```

## 测试

### 使用项目虚拟环境

项目使用 `.venv` 作为 Python 虚拟环境。**推荐使用 `.venv` 执行测试**，确保环境一致性。

```bash
# Windows - 激活虚拟环境
.\.venv\Scripts\activate

# Unix/Linux/macOS - 激活虚拟环境
source .venv/bin/activate

# 或直接使用虚拟环境中的 Python（无需激活）
.\.venv\Scripts\python.exe -m pytest apps/api/tests -v  # Windows
.\.venv/bin/python -m pytest apps/api/tests -v          # Unix/Linux/macOS
```

### 测试依赖

核心测试依赖已包含在 `.venv` 中：
- pytest
- pytest-asyncio
- sqlalchemy
- pandas
- numpy

可选依赖（用于 Parquet 测试）：
- pyarrow

### 独立运行测试

```bash
# 后端测试（推荐使用 .venv）
cd apps/api
..\..\.venv\Scripts\python.exe -m pytest -v  # Windows

# 或激活虚拟环境后
pytest

# 前端类型检查
cd apps/web
pnpm typecheck

# 回归验证（路径一致性 + 核心链路冒烟测试）
pnpm test:regression

# 仅运行路径一致性测试
pnpm test:regression:path

# 仅运行冒烟测试
pnpm test:regression:smoke

# 端到端验收（训练 -> 结果读取 -> 模型下载）
pnpm test:e2e:results

# 或以 JSON 格式输出
pnpm test:e2e:results:json
```

### 端到端验收前置条件

端到端验收需要以下服务运行：
1. PostgreSQL 数据库
2. Redis 服务
3. API 服务 (端口 8000)
4. Worker 服务

启动命令：
```bash
# 启动基础设施
pnpm docker:dev

# 启动 API
pnpm dev:api

# 启动 Worker（新终端）
cd apps/worker && python -m app.main

# 或使用 Docker Compose 启动所有服务
docker-compose -f docker/docker-compose.dev.yml up -d
```

### 端到端验收成功判定标准

端到端验收脚本 (`pnpm test:e2e:results`) 成功的标准：

1. **服务健康检查通过**
   - API 服务返回 `healthy` 状态
   - 就绪检查返回 `ready` 状态（数据库和存储正常）

2. **业务步骤全部成功**
   - 数据集切分成功
   - 实验创建成功
   - 训练启动成功
   - 训练完成（状态为 `completed`）
   - 结果获取成功（包含模型信息）
   - 模型下载成功（非空且为有效 JSON）

3. **输出验证**
   - 最终输出 `✅ 端到端验证通过`
   - 退出码为 0

### 门禁等级与判定标准

端到端验收结果分为三个等级：

| 等级 | 条件 | 说明 |
|------|------|------|
| **通过** | 所有步骤成功，模型校验完整 | 生产环境可部署 |
| **降级通过** | 核心步骤成功，Worker 状态不可用 | 可部署，但需关注 Worker 状态 |
| **失败** | 核心步骤失败或模型校验失败 | 不可部署，需修复问题 |

**降级通过条件**：
- Worker 状态为 `unavailable` 或 `not_available`
- 但训练任务仍能成功完成
- 模型下载和校验正常

**失败条件**：
- API 服务不可用
- 数据库或存储服务不可用
- 训练任务失败
- 模型下载失败或内容无效

### Worker 状态说明

Worker 状态通过 `/api/training/status` 端点获取：

| 状态 | 含义 | 影响 |
|------|------|------|
| `healthy` | Worker 正常运行，Redis 连接正常 | 无 |
| `degraded` | Worker 部分功能异常 | 可能影响任务队列 |
| `unavailable` | Worker 未启动或 Redis 断开 | 新任务无法执行 |

### 模型校验语义

模型校验结果包含以下字段：

| 字段 | 说明 |
|------|------|
| `model_type` | 模型类型（如 `xgboost`），通过检测 `learner` + `version` 字段自动识别 |
| `format` | 模型格式（如 `json`） |
| `validation_level` | 校验级别：`full`（完整）或 `partial`（部分） |
| `has_feature_names` | 是否包含特征名称 |
| `has_target` | 是否包含目标列信息 |

**model_type 检测逻辑**：
1. 优先检查显式的 `model_type` 字段
2. 若无显式字段，检测 XGBoost 原生 JSON 格式（顶层包含 `learner` 和 `version` 字段）
3. 若均不满足，返回 `unknown`

### 端到端验收常见失败排查

| 问题 | 可能原因 | 解决方案 |
|------|------|------|
| API 连接失败 | API 服务未启动 | 运行 `pnpm dev:api` |
| Worker 连接失败 | Worker 服务未启动 | 运行 `cd apps/worker && python -m app.main` |
| 数据集不存在 | 未创建测试数据集 | 检查 `dataset/` 目录是否有数据文件 |
| 训练超时 | 训练任务卡住 | 检查 Worker 日志 |
| Redis 连接失败 | Redis 服务未启动 | 检查 Docker 容器状态 |
| 模型下载失败 | 模型文件不存在 | 检查 `workspace/models/` 目录 |

### 测试分层

| 测试类型 | 文件 | 依赖 | 状态 |
|----------|------|------|------|
| 核心测试 | test_workspace_consistency.py | 核心依赖 | 必须 |
| 核心测试 | test_data_quality.py (CSV) | 核心依赖 | 必须 |
| 扩展测试 | test_data_quality.py (Parquet) | pyarrow | 可选 |

## Workspace 目录说明

项目使用统一的 `workspace/` 目录存储训练过程中产生的文件：

- **API 服务** 和 **Worker 服务** 共享同一个 `WORKSPACE_DIR` 配置
- 默认路径为项目根目录下的 `workspace/` 目录
- 包含：模型文件、数据切分结果、预处理输出等

### 环境变量配置

确保 API 和 Worker 使用相同的 `WORKSPACE_DIR` 绝对路径：

```bash
# Windows PowerShell
$env:WORKSPACE_DIR = "C:\path\to\project\workspace"

# Unix/Linux/macOS
export WORKSPACE_DIR="/path/to/project/workspace"
```

### 路径一致性验证

运行以下命令验证 API 和 Worker 的 workspace 配置一致：

```bash
pnpm test:regression:path
```

该测试确保：
- API 和 Worker 使用相同的 `WORKSPACE_DIR` 值
- 路径为绝对路径格式
- 路径指向项目根目录下的 `workspace` 目录

## 许可证

MIT License

---

## RC1 验收入口

### 快速验收

```bash
# 运行 RC1 最终闸门复核脚本
powershell -ExecutionPolicy Bypass -File scripts/rc1_final_gate.ps1
```

### Docker 部署验收

```bash
# 构建镜像
docker build -t xgboost-vis-api:rc1 -f apps/api/Dockerfile apps/api
docker build -t xgboost-vis-worker:rc1 -f apps/worker/Dockerfile apps/worker
docker build -t xgboost-vis-web:rc1 -f apps/web/Dockerfile apps/web

# 启动服务
docker compose -f docker/docker-compose.prod.yml up -d

# 验证服务
curl http://localhost:8000/health
```

### 验收标准

| 检查项 | 状态 |
|--------|------|
| package.json 版本 | 1.0.0-rc1 |
| Docker 镜像构建 | api, worker, web |
| API /health | 200 healthy |
| Worker status | healthy |
| Frontend | 200 OK |

### 相关文档

- [RC1 部署指南](docs/release/RC1_DEPLOYMENT_GUIDE.md)
- [RC1 发布清单](docs/release/RC1_RELEASE_CHECKLIST.md)
- [变更日志](CHANGELOG.md)
