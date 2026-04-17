from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone
from typing import Any

from app.database import get_db
from app.config import settings
from app.routers.auth import get_current_admin
from app.models.models import User

router = APIRouter()


@router.get("/health")
async def liveness_check() -> dict[str, str]:
    """
    Liveness 探针（存活检查）
    严格只返回最小响应体，不检查任何外部依赖
    
    性能优化 (M7-T101):
    - 使用 response_model 避免 Pydantic 验证开销
    - 不依赖任何 DB 或外部服务
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness 探针（就绪检查）
    检查数据库、存储、Redis 等外部依赖
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

    # 检查存储服务
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
        checks["storage"] = {"status": "error", "message": f"Not initialized: {str(e)}"}
        all_healthy = False
    except Exception as e:
        checks["storage"] = {"status": "error", "message": str(e)[:100]}
        all_healthy = False

    # 检查 Redis（可选，降级为 warning 不阻塞就绪状态）
    try:
        import redis.asyncio as aioredis
        redis = await aioredis.from_url(settings.REDIS_URL)
        try:
            result = await redis.ping()
        except Exception:
            result = redis.ping()
        await redis.aclose()
        checks["redis"] = {"status": "ok", "message": "Connected"}
    except Exception as e:
        checks["redis"] = {"status": "warning", "message": str(e)[:100]}
        # Redis 不是必需的，不影响就绪状态

    # 关键依赖失败时返回 503
    if not all_healthy:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": checks
            }
        )

    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks
    }


@router.get("/health/details")
async def health_details(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    健康详情端点（仅管理员可访问）
    返回各组件的详细状态信息
    """
    from app.services.storage import get_storage_service

    checks: dict[str, Any] = {}

    # 数据库详情
    try:
        result = await db.execute(text("SELECT version()"))
        db_version = result.scalar()
        checks["database"] = {
            "status": "ok",
            "message": "Connected",
            "version": str(db_version)[:50] if db_version else "Unknown"
        }
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)[:100]}

    # Redis 详情
    try:
        import redis.asyncio as aioredis
        redis = await aioredis.from_url(settings.REDIS_URL)
        try:
            info = await redis.info()
            result = await redis.ping()
        except Exception:
            info = redis.info()
            result = redis.ping()
        await redis.aclose()
        checks["redis"] = {
            "status": "ok",
            "message": "Connected",
            "version": info.get("redis_version", "Unknown") if info else "Unknown",
            "memory_used": info.get("used_memory_human", "Unknown") if info else "Unknown"
        }
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)[:100]}

    # 存储详情
    try:
        storage = get_storage_service()
        is_healthy, message = await storage.health_check()
        if is_healthy:
            checks["storage"] = {
                "status": "ok",
                "message": message,
                "type": storage.storage_type,
                "workspace": settings.WORKSPACE_DIR
            }
        else:
            checks["storage"] = {"status": "error", "message": message}
    except RuntimeError as e:
        checks["storage"] = {"status": "error", "message": f"Not initialized: {str(e)}"}
    except Exception as e:
        checks["storage"] = {"status": "error", "message": str(e)[:100]}

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "xgboost-vis-api",
        "version": settings.APP_VERSION,
        "checks": checks
    }


@router.get("/live")
async def liveness_check_legacy() -> dict[str, str]:
    """Legacy liveness endpoint (deprecated, use /health)"""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
