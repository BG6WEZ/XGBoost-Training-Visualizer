from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from datetime import datetime

from app.database import get_db
from app.models import Experiment, TrainingMetric, TrainingLog, ExperimentStatus
from app.services.queue import get_queue_service

router = APIRouter()


@router.get("/status")
async def get_worker_status():
    """
    获取 Worker 整体状态
    
    用于健康检查和可观测性，返回：
    - worker_status: healthy/degraded/unavailable
    - redis_status: connected/disconnected
    - queue_length: 当前队列长度
    - active_experiments: 正在运行的实验数量
    """
    from app.config import settings
    
    result = {
        "worker_status": "unavailable",
        "redis_status": "disconnected",
        "queue_length": 0,
        "active_experiments": 0,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        queue = await get_queue_service()
        
        if queue.redis is None:
            result["worker_status"] = "unavailable"
            result["redis_status"] = "disconnected"
        else:
            result["redis_status"] = "connected"
            
            try:
                queue_length = await queue.get_queue_length()
                result["queue_length"] = queue_length
                
                if queue_length >= 0:
                    result["worker_status"] = "healthy"
                else:
                    result["worker_status"] = "degraded"
                    
            except Exception as e:
                result["worker_status"] = "degraded"
                result["error"] = str(e)[:100]
                
    except Exception as e:
        result["worker_status"] = "unavailable"
        result["redis_status"] = "disconnected"
        result["error"] = str(e)[:100]
    
    return result


@router.get("/{experiment_id}/status")
async def get_training_status(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取训练状态"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # 计算进度
    progress = 0
    if experiment.status == ExperimentStatus.running.value:
        # 从配置中获取总迭代次数
        n_estimators = experiment.config.get("xgboost_params", {}).get("n_estimators", 100)
        # 查询当前迭代
        metric_result = await db.execute(
            select(TrainingMetric)
            .where(TrainingMetric.experiment_id == exp_uuid)
            .order_by(TrainingMetric.iteration.desc())
            .limit(1)
        )
        latest_metric = metric_result.scalar_one_or_none()
        if latest_metric:
            progress = (latest_metric.iteration + 1) / n_estimators
    elif experiment.status == ExperimentStatus.completed.value:
        progress = 1.0

    return {
        "experiment_id": experiment_id,
        "status": experiment.status,
        "progress": round(progress * 100, 2),
        "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
        "finished_at": experiment.finished_at.isoformat() if experiment.finished_at else None,
        "error_message": experiment.error_message
    }


@router.get("/{experiment_id}/logs")
async def get_training_logs(
    experiment_id: str,
    skip: int = 0,
    limit: int = 100,
    level: str = None,
    db: AsyncSession = Depends(get_db)
):
    """获取训练日志"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    # 验证实验存在
    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # 查询日志
    query = select(TrainingLog).where(TrainingLog.experiment_id == exp_uuid)

    if level:
        query = query.where(TrainingLog.level == level.upper())

    query = query.order_by(TrainingLog.timestamp.asc()).offset(skip).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "experiment_id": experiment_id,
        "total": len(logs),
        "logs": [
            {
                "id": str(log.id),
                "level": log.level,
                "message": log.message,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
    }


@router.get("/{experiment_id}/metrics")
async def get_training_metrics(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取训练指标"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    # 验证实验存在
    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # 查询指标
    result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration.asc())
    )
    metrics = result.scalars().all()

    return {
        "experiment_id": experiment_id,
        "total": len(metrics),
        "metrics": [
            {
                "iteration": m.iteration,
                "train_loss": m.train_loss,
                "val_loss": m.val_loss,
                "train_metric": m.train_metric,
                "val_metric": m.val_metric,
                "recorded_at": m.recorded_at.isoformat()
            }
            for m in metrics
        ]
    }


@router.get("/{experiment_id}/metrics/latest")
async def get_latest_metrics(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取最新训练指标"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration.desc())
        .limit(1)
    )
    metric = result.scalar_one_or_none()

    if not metric:
        return {
            "experiment_id": experiment_id,
            "metric": None
        }

    return {
        "experiment_id": experiment_id,
        "metric": {
            "iteration": metric.iteration,
            "train_loss": metric.train_loss,
            "val_loss": metric.val_loss,
            "train_metric": metric.train_metric,
            "val_metric": metric.val_metric,
            "recorded_at": metric.recorded_at.isoformat()
        }
    }