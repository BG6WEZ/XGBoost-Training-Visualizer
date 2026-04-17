from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
import os


# 项目根目录
# 本地开发：向上 3 级到达项目根目录：app -> apps -> project root
# Docker 容器：向上 1 级到达项目根目录：/app/app -> /app
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    # Docker 容器环境
    PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Worker 配置"""

    # 应用信息
    APP_NAME: str = "XGBoost Training Worker"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = "postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "xgboost-vis"
    MINIO_SECURE: bool = False

    # 训练配置
    MAX_CONCURRENT_TRAININGS: int = 3
    TRAINING_TIMEOUT_MINUTES: int = 120

    # 工作目录（与 API 保持一致，使用绝对路径）
    # 优先使用环境变量，否则使用项目根目录下的 workspace
    WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", str(PROJECT_ROOT / "workspace"))

    # 日志级别
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()