from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
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
    """应用配置"""

    # 应用信息
    APP_NAME: str = "XGBoost Training Visualizer API"
    APP_VERSION: str = "1.0.0"
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

    # JWT 配置
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    JWT_EXPIRE_HOURS: int = 24

    # 训练配置
    MAX_CONCURRENT_TRAININGS: int = 3
    TRAINING_TIMEOUT_MINUTES: int = 120

    # 文件上传配置
    MAX_FILE_SIZE_MB: int = 1024
    UPLOAD_DIR: str = str(PROJECT_ROOT / "workspace" / "uploads")

    # 存储配置（与 Worker 保持一致，使用绝对路径）
    # 优先使用环境变量，否则使用项目根目录下的 workspace
    WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", str(PROJECT_ROOT / "workspace"))
    
    # 数据集目录配置
    DATASET_DIR: str = os.getenv("DATASET_DIR", str(PROJECT_ROOT / "dataset"))

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # 日志级别
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()