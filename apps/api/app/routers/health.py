from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

from app.database import get_db
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """基础健康检查端点"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "xgboost-vis-api",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    就绪检查端点

    检查所有依赖服务的连接状态
    """
    from app.services.storage import get_storage_service

    checks = {}
    all_healthy = True

    # 检查数据库
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "message": "Connected"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)[:100]}
        all_healthy = False

    # 检查存储服务（使用统一初始化的存储服务）
    try:
        storage = get_storage_service()
        is_healthy, message = await storage.health_check()
        if is_healthy:
            checks["storage"] = {
                "status": "ok",
                "message": message,
                "type": storage.storage_type
            }
        else:
            checks["storage"] = {"status": "error", "message": message}
            all_healthy = False
    except RuntimeError as e:
        # 存储服务未初始化
        checks["storage"] = {"status": "error", "message": f"Not initialized: {str(e)}"}
        all_healthy = False
    except Exception as e:
        checks["storage"] = {"status": "error", "message": str(e)[:100]}
        all_healthy = False

    # 检查 Redis（可选，不阻塞就绪状态）
    try:
        import redis.asyncio as aioredis
        redis = await aioredis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.close()
        checks["redis"] = {"status": "ok", "message": "Connected"}
    except Exception as e:
        checks["redis"] = {"status": "warning", "message": str(e)[:100]}
        # Redis 不是必需的，不影响就绪状态

    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/live")
async def liveness_check():
    """存活检查端点"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }