from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.routers import datasets, experiments, training, results, health, assets
from app.database import init_db
from app.services.queue import get_queue_service
from app.services.storage import init_storage_service, StorageConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    await init_db()

    # 初始化存储服务（必须在其他服务之前，使用统一的 WORKSPACE_DIR）
    storage_config = StorageConfig(
        storage_type=os.getenv("STORAGE_TYPE", "local"),
        local_base_path=settings.WORKSPACE_DIR,  # 与 Worker 保持一致
        minio_endpoint=settings.MINIO_ENDPOINT,
        minio_access_key=settings.MINIO_ACCESS_KEY,
        minio_secret_key=settings.MINIO_SECRET_KEY,
        minio_bucket=settings.MINIO_BUCKET,
        minio_secure=settings.MINIO_SECURE
    )
    await init_storage_service(storage_config)
    print(f"Storage service initialized: type={storage_config.storage_type}")

    # 初始化队列服务
    try:
        queue = await get_queue_service()
        print(f"Queue service connected: {queue.redis is not None}")
    except Exception as e:
        print(f"Warning: Could not connect to Redis: {e}")

    yield
    # 关闭时


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, tags=["health"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(results.router, prefix="/api/results", tags=["results"])