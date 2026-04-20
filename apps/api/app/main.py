from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import os
import uuid
import json

from app.config import settings
from app.logging_config import setup_logging, get_logger, request_id_ctx
from app.routers import datasets, experiments, training, results, health, assets, versions, export, auth, users
from app.database import init_db
from app.services.queue import get_queue_service
from app.services.storage import init_storage_service, StorageConfig

logger = get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate or propagate X-Request-ID for each request.

    - Reuses existing X-Request-ID from request headers if present
    - Generates a new UUID if not present
    - Adds X-Request-ID to response headers
    - Injects request_id into log records
    """

    async def dispatch(self, request: Request, call_next):
        # Skip expensive middleware work for the hot liveness path.
        if request.url.path == "/health":
            return await call_next(request)

        # Get or generate request_id
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Set in context variable for logging filter
        token = request_id_ctx.set(request_id)

        try:
            # Process request
            response = await call_next(request)

            # Add request_id to response headers
            response.headers["X-Request-ID"] = request_id

            return response
        finally:
            # Reset context variable
            request_id_ctx.reset(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Initialize logging first
    setup_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

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
    logger.info("Storage service initialized: type=%s", storage_config.storage_type)

    # 初始化队列服务
    try:
        queue = await get_queue_service()
        logger.info("Queue service connected: %s", queue.redis is not None)
    except Exception as e:
        logger.warning("Could not connect to Redis: %s", e)

    logger.info("Application startup complete")

    yield

    # 关闭时
    logger.info("Application shutting down")


api_app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add request_id middleware
api_app.add_middleware(RequestIdMiddleware)

# CORS 配置
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Request-ID"],
)

# 注册路由
api_app.include_router(health.router, tags=["health"])
api_app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
api_app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
api_app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
api_app.include_router(versions.router, prefix="/api", tags=["versions"])
api_app.include_router(training.router, prefix="/api/training", tags=["training"])
api_app.include_router(results.router, prefix="/api/results", tags=["results"])
api_app.include_router(export.router, prefix="/api", tags=["export"])
api_app.include_router(auth.router, prefix="/api", tags=["auth"])
api_app.include_router(users.router, prefix="/api", tags=["users"])


class _HealthBypassApp:
    """Handle the hot liveness path before FastAPI middleware/router overhead."""

    def __init__(self, inner_app):
        self.inner_app = inner_app
        self._health_body = json.dumps({"status": "ok"}).encode("utf-8")
        self._health_headers = [(b"content-type", b"application/json")]

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") == "/health":
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": self._health_headers,
                }
            )
            await send({"type": "http.response.body", "body": self._health_body})
            return

        await self.inner_app(scope, receive, send)


app = _HealthBypassApp(api_app)
