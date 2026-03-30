# XGBoost 训练可视化工具 - 技术架构设计

## 1. 系统架构概览

### 1.1 整体架构图

```
                              用户浏览器
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx 反向代理                           │
│                    (静态资源 + API 代理)                          │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────────────┐
│      前端应用 (React)      │   │         后端服务 (Python)          │
│  ┌─────────────────────┐  │   │  ┌─────────────────────────────┐  │
│  │ React 18            │  │   │  │ FastAPI 服务 (apps/api)     │  │
│  │ TypeScript          │  │   │  │ - 数据资产管理              │  │
│  │ Tailwind CSS        │  │   │  │ - 实验管理                  │  │
│  │ Recharts            │  │   │  │ - 训练调度                  │  │
│  │ TanStack Query      │  │   │  │ - 结果查询                  │  │
│  └─────────────────────┘  │   │  └─────────────────────────────┘  │
└───────────────────────────┘   │  ┌─────────────────────────────┐  │
                                │  │ Worker 服务 (apps/worker)   │  │
                                │  │ - 数据预处理任务            │  │
                                │  │ - XGBoost 训练执行          │  │
                                │  │ - 特征工程任务              │  │
                                │  └─────────────────────────────┘  │
                                └───────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
        ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
        │    PostgreSQL     │     │      Redis        │     │   MinIO/本地存储  │
        │  ┌─────────────┐  │     │  ┌─────────────┐  │     │  ┌─────────────┐  │
        │  │ experiments │  │     │  │ 任务队列    │  │     │  │ 数据集文件  │  │
        │  │ datasets    │  │     │  │ 实时状态    │  │     │  │ 模型文件    │  │
        │  │ models      │  │     │  │ 缓存        │  │     │  │ 预处理输出  │  │
        │  │ async_tasks │  │     │  └─────────────┘  │     │  └─────────────┘  │
        │  └─────────────┘  │     └───────────────────┘     └───────────────────┘
        └───────────────────┘
```

### 1.2 架构分层

| 层级 | 职责 | 技术组件 |
|------|------|----------|
| 表现层 | 用户界面渲染、交互处理 | React, Tailwind CSS |
| API 网关 | 请求路由、认证授权 | Nginx |
| 应用层 | 业务逻辑处理、API 服务 | Python, FastAPI |
| Worker 层 | 后台任务、训练执行 | Python, asyncio |
| 数据层 | 数据持久化、缓存 | PostgreSQL, Redis |
| 存储层 | 文件存储（本地或对象存储） | MinIO / 本地文件系统 |

---

## 2. Monorepo 项目结构

### 2.1 实际项目结构

```
xgboost-training-visualizer/
├── apps/                          # 应用程序
│   ├── web/                       # 前端应用 (React)
│   │   ├── src/
│   │   │   ├── app/               # 应用入口
│   │   │   │   ├── App.tsx
│   │   │   │   └── router.tsx
│   │   │   ├── components/        # 组件
│   │   │   │   └── ui/            # shadcn/ui 组件
│   │   │   ├── lib/               # 工具函数
│   │   │   └── main.tsx
│   │   ├── package.json
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   │
│   ├── api/                       # Python FastAPI 服务
│   │   ├── app/
│   │   │   ├── main.py            # FastAPI 入口
│   │   │   ├── config.py          # 配置
│   │   │   ├── database.py        # 数据库连接
│   │   │   │
│   │   │   ├── routers/           # 路由定义
│   │   │   │   ├── datasets.py    # 数据集管理
│   │   │   │   ├── experiments.py # 实验管理
│   │   │   │   ├── training.py    # 训练调度
│   │   │   │   ├── results.py     # 结果查询
│   │   │   │   └── health.py      # 健康检查
│   │   │   │
│   │   │   ├── models/            # SQLAlchemy 模型
│   │   │   │   └── models.py
│   │   │   │
│   │   │   ├── schemas/           # Pydantic 模式
│   │   │   │   ├── dataset.py
│   │   │   │   ├── experiment.py
│   │   │   │   └── results.py
│   │   │   │
│   │   │   └── services/          # 业务服务
│   │   │       ├── queue.py       # Redis 队列服务
│   │   │       └── storage.py     # 统一存储适配层
│   │   │
│   │   ├── tests/                 # 测试
│   │   ├── requirements.txt
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── worker/                    # Python Worker 服务
│       ├── app/
│       │   ├── main.py            # Worker 入口
│       │   ├── config.py          # 配置
│       │   ├── models.py          # 数据模型
│       │   ├── storage.py         # 存储服务
│       │   └── tasks/
│       │       └── training.py    # 训练任务实现
│       │
│       ├── requirements.txt
│       └── Dockerfile
│
├── packages/                      # 共享包（规划中，暂未实现）
│   ├── types/                     # @xgboost-vis/types
│   │   ├── src/
│   │   │   └── index.ts           # TypeScript 类型定义
│   │   └── package.json
│   │
│   └── utils/                     # @xgboost-vis/utils
│       ├── src/
│       │   └── index.ts           # 工具函数
│       └── package.json
│
├── docker/                        # Docker 配置
│   ├── docker-compose.yml         # 生产环境编排
│   └── docker-compose.dev.yml     # 开发环境编排
│
├── docs/                          # 项目文档
│   ├── architecture/              # 架构文档
│   ├── planning/                  # 规划文档
│   └── specification/             # 规格说明
│
├── dataset/                       # 示例数据集
├── workspace/                     # 运行时工作目录
├── .env.example                   # 环境变量示例
├── package.json                   # 根 package.json
├── pnpm-workspace.yaml            # pnpm workspace 配置
└── turbo.json                     # Turborepo 配置
```

---

## 3. 后端架构设计 (apps/api)

### 3.1 目录结构

```
apps/api/app/
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理
├── database.py          # 数据库连接
├── routers/             # API 路由
│   ├── datasets.py      # /api/datasets
│   ├── experiments.py   # /api/experiments
│   ├── training.py      # /api/training
│   ├── results.py       # /api/results
│   └── health.py        # /health, /ready, /live
├── models/              # SQLAlchemy 模型
│   └── models.py
├── schemas/             # Pydantic 模式
│   ├── dataset.py
│   ├── experiment.py
│   └── results.py
└── services/            # 业务服务
    ├── queue.py         # Redis 队列服务
    └── storage.py       # 统一存储适配层
```

### 3.2 核心服务

#### 3.2.1 FastAPI 主入口

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.routers import datasets, experiments, training, results, health
from app.database import init_db
from app.services.queue import get_queue_service
from app.services.storage import init_storage_service, StorageConfig

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()

    # 初始化存储服务
    storage_config = StorageConfig(
        storage_type=os.getenv("STORAGE_TYPE", "local"),
        local_base_path=settings.WORKSPACE_DIR,
        minio_endpoint=settings.MINIO_ENDPOINT,
        minio_access_key=settings.MINIO_ACCESS_KEY,
        minio_secret_key=settings.MINIO_SECRET_KEY,
        minio_bucket=settings.MINIO_BUCKET,
        minio_secure=settings.MINIO_SECURE
    )
    await init_storage_service(storage_config)

    # 初始化队列服务
    queue = await get_queue_service()

    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 注册路由
app.include_router(health.router, tags=["health"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(results.router, prefix="/api/results", tags=["results"])
```

#### 3.2.2 统一存储适配层

```python
# app/services/storage.py
class StorageAdapter(ABC):
    """存储适配器基类"""

    @abstractmethod
    async def save(self, object_key: str, data: bytes, content_type: str) -> FileInfo:
        pass

    @abstractmethod
    async def read(self, object_key: str) -> bytes:
        pass

    @abstractmethod
    async def health_check(self) -> Tuple[bool, str]:
        pass

class LocalStorageAdapter(StorageAdapter):
    """本地文件系统存储"""
    def __init__(self, base_path: str = "./workspace"):
        self.base_path = os.path.abspath(base_path)

class MinIOStorageAdapter(StorageAdapter):
    """MinIO 对象存储"""
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        ...

class StorageService:
    """统一存储服务"""
    async def save_model(self, experiment_id: str, data: bytes, format: str = "json") -> FileInfo:
        ...

    async def get_model(self, experiment_id: str, format: str = "json") -> bytes:
        ...

    async def save_preprocessing_output(self, dataset_id: str, task_id: str, data: bytes) -> FileInfo:
        ...

    async def save_feature_engineering_output(self, dataset_id: str, task_id: str, data: bytes) -> FileInfo:
        ...
```

#### 3.2.3 队列服务

```python
# app/services/queue.py
class QueueService:
    """Redis 队列服务"""

    TRAINING_QUEUE = "training:queue"
    PREPROCESSING_QUEUE = "preprocessing:queue"
    FEATURE_ENGINEERING_QUEUE = "feature_engineering:queue"

    async def enqueue_training(self, experiment_id: str, dataset_id: str, config: dict, subset_id: str = None) -> str:
        """入队训练任务"""
        ...

    async def increment_task_version(self, experiment_id: str) -> int:
        """递增任务版本号（用于竞态保护）"""
        ...
```

### 3.3 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 基础健康检查 |
| `/ready` | GET | 就绪检查（含 DB、存储、Redis） |
| `/live` | GET | 存活检查 |
| `/api/datasets/` | GET | 获取数据集列表 |
| `/api/datasets/` | POST | 创建数据集（JSON 格式） |
| `/api/datasets/{id}` | GET | 获取数据集详情 |
| `/api/datasets/{id}` | PATCH | 更新数据集信息 |
| `/api/datasets/{id}` | DELETE | 删除数据集 |
| `/api/datasets/{id}/preprocess` | POST | 触发预处理任务 |
| `/api/datasets/{id}/feature-engineering` | POST | 触发特征工程任务 |
| `/api/datasets/tasks/{task_id}` | GET | 查询异步任务状态 |
| `/api/datasets/{id}/tasks` | GET | 获取数据集的任务列表 |
| `/api/experiments/` | GET | 获取实验列表 |
| `/api/experiments/` | POST | 创建实验 |
| `/api/experiments/{id}` | GET | 获取实验详情 |
| `/api/experiments/{id}` | PATCH | 更新实验信息 |
| `/api/experiments/{id}` | DELETE | 删除实验 |
| `/api/experiments/{id}/start` | POST | 启动训练 |
| `/api/experiments/{id}/stop` | POST | 停止训练 |
| `/api/training/{id}/status` | GET | 查询训练状态 |
| `/api/training/{id}/logs` | GET | 获取训练日志 |
| `/api/training/{id}/metrics` | GET | 获取训练指标历史 |
| `/api/training/{id}/metrics/latest` | GET | 获取最新训练指标 |
| `/api/results/{id}` | GET | 获取实验结果 |
| `/api/results/{id}/feature-importance` | GET | 获取特征重要性 |
| `/api/results/{id}/metrics-history` | GET | 获取指标历史曲线 |
| `/api/results/{id}/download-model` | GET | 下载模型文件 |
| `/api/results/{id}/export-report` | GET | 导出实验报告 |
| `/api/results/compare` | POST | 对比多个实验 |

---

## 4. Worker 服务设计 (apps/worker)

### 4.1 目录结构

```
apps/worker/app/
├── main.py              # Worker 入口
├── config.py            # 配置
├── models.py            # 数据库模型（共享自 API）
├── storage.py           # 存储服务
└── tasks/
    └── training.py      # 训练任务实现
```

### 4.2 Worker 主循环

```python
# app/main.py
class TrainingWorker:
    """训练任务 Worker"""

    TRAINING_QUEUE = "training:queue"
    PREPROCESSING_QUEUE = "preprocessing:queue"
    FEATURE_ENGINEERING_QUEUE = "feature_engineering:queue"

    async def run(self):
        """主循环 - 监听多个队列"""
        await self.connect()
        self.running = True

        while self.running:
            result = await self.redis.blpop(
                [self.TRAINING_QUEUE, self.PREPROCESSING_QUEUE, self.FEATURE_ENGINEERING_QUEUE],
                timeout=5
            )

            if result:
                queue_name, data = result
                task_data = json.loads(data)

                if queue_name == self.TRAINING_QUEUE:
                    await self.process_training_task(task_data)
                elif queue_name == self.PREPROCESSING_QUEUE:
                    await self.process_preprocessing_task(task_data)
                elif queue_name == self.FEATURE_ENGINEERING_QUEUE:
                    await self.process_feature_engineering_task(task_data)
```

### 4.3 队列名称约定

| 队列名 | 用途 |
|--------|------|
| `training:queue` | 训练任务队列 |
| `preprocessing:queue` | 数据预处理任务队列 |
| `feature_engineering:queue` | 特征工程任务队列 |
| `task:version:{experiment_id}` | 任务版本号（竞态保护） |

---

## 5. 数据库设计

### 5.1 核心表

```sql
-- 数据集表
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    time_column VARCHAR(100),
    entity_column VARCHAR(100),
    target_column VARCHAR(100),
    total_row_count INTEGER DEFAULT 0,
    total_column_count INTEGER DEFAULT 0,
    total_file_size INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据集文件表
CREATE TABLE dataset_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'primary',
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,
    file_size INTEGER DEFAULT 0,
    columns_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实验表
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dataset_id UUID REFERENCES datasets(id) NOT NULL,
    subset_id UUID,
    config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',        -- pending, queued, running, paused, completed, failed, cancelled
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

-- 实验状态说明：
-- pending: 初始状态，等待启动
-- queued: 已入队，等待 Worker 消费
-- running: 正在训练
-- paused: 已暂停（当前版本不支持）
-- completed: 训练完成
-- failed: 训练失败
-- cancelled: 已取消

-- 模型表
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE NOT NULL UNIQUE,
    storage_type VARCHAR(20) DEFAULT 'local',    -- local, minio
    object_key VARCHAR(500),                     -- 存储对象键（nullable 用于历史数据兼容）
    format VARCHAR(20) NOT NULL,                 -- json, ubj
    file_size INTEGER,
    file_path VARCHAR(500),                      -- 已弃用，仅用于历史数据兼容
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 训练指标表
CREATE TABLE training_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE NOT NULL,
    iteration INTEGER NOT NULL,
    train_loss FLOAT,
    val_loss FLOAT,
    train_metric FLOAT,
    val_metric FLOAT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 特征重要性表
CREATE TABLE feature_importance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    importance FLOAT NOT NULL,
    rank INTEGER
);

-- 异步任务表
CREATE TABLE async_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(50) NOT NULL,              -- preprocessing, feature_engineering
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',         -- queued, running, completed, failed
    config JSONB,                                -- 任务配置
    result JSONB,                                -- 任务结果
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);
```

---

## 6. 存储策略

### 6.1 存储适配器架构

```
StorageService (统一接口)
    │
    ├── LocalStorageAdapter  (本地文件系统)
    │   └── base_path: WORKSPACE_DIR
    │
    └── MinIOStorageAdapter  (对象存储)
        ├── endpoint
        ├── bucket
        └── credentials
```

### 6.2 对象键命名规范

| 类型 | 对象键格式 |
|------|------------|
| 模型文件 | `models/{experiment_id}/model.{format}` |
| 预处理输出 | `preprocessing/{dataset_id}/{task_id}/processed.csv` |
| 特征工程输出 | `feature_engineering/{dataset_id}/{task_id}/features.csv` |

### 6.3 模型下载路径规则

**新模型（有 object_key）**：
- 主路径：通过 storage adapter 读取
- 存储失败返回 404，不 fallback 到 file_path

**历史模型（object_key 为空）**：
- 兼容路径：通过 file_path 读取
- 仅用于数据迁移期间的历史数据兼容

---

## 7. AsyncTask 流程

### 7.1 状态流转

```
queued -> running -> completed
                  \-> failed
```

**状态语义**：
| 状态 | 说明 |
|------|------|
| `queued` | 任务已入队，等待 Worker 消费 |
| `running` | Worker 正在执行任务 |
| `completed` | 任务执行成功，result 字段包含结果 |
| `failed` | 任务执行失败，error_message 字段包含错误信息 |

### 7.2 预处理任务流程

```
1. API 接收请求 -> 创建 AsyncTask 记录
2. API 入队到 preprocessing:queue
3. Worker 消费任务
4. Worker 更新 AsyncTask.status = "running"
5. Worker 执行预处理 -> 通过 storage adapter 保存输出
6. Worker 更新 AsyncTask.result（含 storage_type, object_key, file_size）
7. Worker 更新 AsyncTask.status = "completed"
```

### 7.3 结果字段结构

```json
{
  "dataset_id": "uuid",
  "status": "completed",
  "storage_type": "local",
  "object_key": "preprocessing/{dataset_id}/{task_id}/processed.csv",
  "file_size": 12345,
  "output_file_name": "processed.csv",
  "full_path": "/workspace/preprocessing/..."  // 仅 local 模式
}
```

---

## 8. 竞态保护机制

### 8.1 版本号绑定

训练任务入队时，版本号写入 payload：

```python
payload = {
    "experiment_id": experiment_id,
    "dataset_id": dataset_id,
    "config": config,
    "task_version": current_version  # 版本号绑定到 payload
}
```

### 8.2 消费时校验

Worker 消费时比较 payload 内版本与 Redis 当前版本：

```python
payload_version = task_data.get("task_version", 0)
current_version = await self.get_task_version(experiment_id)

if current_version > payload_version:
    # 任务已被取消/更新，跳过执行
    return
```

---

## 9. Docker 部署

### 9.1 Docker Compose 服务

```yaml
services:
  frontend:
    build: ./apps/web
    ports: ["3000:3000"]

  api:
    build: ./apps/api
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
      - STORAGE_TYPE=local  # 或 minio

  worker:
    build: ./apps/worker
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
      - STORAGE_TYPE=local

  postgres:
    image: postgres:15-alpine
    volumes: [postgres-data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    volumes: [redis-data:/data]

  minio:  # 可选
    image: minio/minio
    command: server /data --console-address ":9001"
    volumes: [minio-data:/data]
```

---

## 10. 配置说明

### 10.1 环境变量

```bash
# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/xgboost_vis

# Redis
REDIS_URL=redis://localhost:6379

# 存储
STORAGE_TYPE=local  # local 或 minio
WORKSPACE_DIR=./workspace

# MinIO（STORAGE_TYPE=minio 时需要）
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=xgboost-vis
MINIO_SECURE=false

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRE_HOURS=24
```

---

**文档版本**：2.3
**创建日期**：2026-03-23
**更新日期**：2026-03-27
**状态**：开发基线

### 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 2.3 | 2026-03-27 | 标注 packages 目录为规划中暂未实现；修正 Node.js 版本要求为 20+；修正 pnpm 版本要求为 9.0+ |
| 2.2 | 2026-03-26 | 修正前端 React 版本为 18（与 package.json 一致） |
| 2.1 | 2026-03-26 | 修正 API 端点表与真实路由一致；修正 async_tasks 表结构（添加 dataset_id、config、status 默认值）；修正状态流转为 queued->running->completed/failed；添加实验状态说明 |
| 2.0 | 2026-03-26 | 重构文档以反映真实代码库结构；删除不存在的目录和服务；更新存储适配层、AsyncTask 流程、竞态保护机制；新增模型下载路径规则 |
| 1.4 | 2026-03-25 | 统一技术栈为 Python FastAPI |
| 1.0 | 2026-03-23 | 初始版本 |