from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models import Experiment, Dataset, DatasetSubset, ExperimentStatus
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
    ExperimentListResponse,
)
from app.services.queue import QueueService, TrainingTask, get_queue_service

router = APIRouter()


def _build_experiment_response(experiment: Experiment) -> dict:
    """构建实验响应"""
    return {
        "id": str(experiment.id),
        "name": experiment.name,
        "description": experiment.description,
        "dataset_id": str(experiment.dataset_id),
        "subset_id": str(experiment.subset_id) if experiment.subset_id else None,
        "config": experiment.config,
        "status": experiment.status,
        "error_message": experiment.error_message,
        "created_at": experiment.created_at,
        "updated_at": experiment.updated_at,
        "started_at": experiment.started_at,
        "finished_at": experiment.finished_at,
    }


@router.get("/", response_model=List[ExperimentListResponse])
async def list_experiments(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取实验列表"""
    query = select(Experiment).order_by(Experiment.created_at.desc())

    if status:
        query = query.where(Experiment.status == status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    experiments = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "name": e.name,
            "description": e.description,
            "dataset_id": str(e.dataset_id),
            "status": e.status,
            "created_at": e.created_at,
        }
        for e in experiments
    ]


@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建实验"""
    # 验证数据集存在
    try:
        dataset_uuid = uuid.UUID(data.dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(select(Dataset).where(Dataset.id == dataset_uuid))
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 如果指定了子集，验证子集存在
    subset_uuid = None
    if data.subset_id:
        try:
            subset_uuid = uuid.UUID(data.subset_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid subset ID format")

        result = await db.execute(
            select(DatasetSubset).where(DatasetSubset.id == subset_uuid)
        )
        subset = result.scalar_one_or_none()

        if not subset:
            raise HTTPException(status_code=404, detail="Subset not found")

        # 校验子集属于指定的数据集
        if subset.parent_dataset_id != dataset_uuid:
            raise HTTPException(
                status_code=400,
                detail="Subset does not belong to the specified dataset"
            )

    # 序列化配置，确保 lambda_ 被正确转换为 lambda
    config_dict = data.config.model_dump()
    if "xgboost_params" in config_dict and "lambda_" in config_dict["xgboost_params"]:
        config_dict["xgboost_params"]["lambda"] = config_dict["xgboost_params"].pop("lambda_")

    # 创建实验
    experiment = Experiment(
        name=data.name,
        description=data.description,
        dataset_id=dataset_uuid,
        subset_id=subset_uuid,
        config=config_dict,
        status=ExperimentStatus.pending.value,
    )
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)

    return _build_experiment_response(experiment)


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取实验详情"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return _build_experiment_response(experiment)


@router.post("/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    queue: QueueService = Depends(get_queue_service)
):
    """启动实验训练"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status not in [ExperimentStatus.pending.value, ExperimentStatus.paused.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start experiment in {experiment.status} status"
        )

    # 更新状态为排队中
    experiment.status = ExperimentStatus.queued.value
    experiment.updated_at = datetime.utcnow()
    await db.commit()

    # 创建训练任务并入队
    task = TrainingTask(
        experiment_id=str(experiment.id),
        dataset_id=str(experiment.dataset_id),
        subset_id=str(experiment.subset_id) if experiment.subset_id else None,
        config=experiment.config,
    )
    await queue.enqueue_training(task)

    return {
        "status": "queued",
        "experiment_id": experiment_id,
        "message": "Experiment has been queued for training",
        "queue_position": await queue.get_queue_length()
    }


@router.post("/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    queue: QueueService = Depends(get_queue_service)
):
    """
    停止实验训练

    竞态保护机制：
    1. 递增任务版本号（原子操作）
    2. 尝试从队列移除任务
    3. 更新数据库状态

    Worker 在消费任务时会检查版本号，如果版本号不匹配则跳过执行
    """
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status not in [ExperimentStatus.running.value, ExperimentStatus.queued.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop experiment in {experiment.status} status"
        )

    # 竞态保护：递增任务版本号
    # Worker 消费时会检查版本号，如果版本号已变化则跳过执行
    new_version = await queue.increment_task_version(experiment_id)

    # 如果在队列中，尝试从队列移除
    removed_from_queue = False
    if experiment.status == ExperimentStatus.queued.value:
        removed_from_queue = await queue.remove_from_queue(experiment_id)

    # 更新状态为已取消
    experiment.status = ExperimentStatus.cancelled.value
    experiment.finished_at = datetime.utcnow()
    experiment.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "status": "cancelled",
        "experiment_id": experiment_id,
        "removed_from_queue": removed_from_queue,
        "task_version": new_version
    }


@router.patch("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: str,
    data: ExperimentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新实验信息"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status != ExperimentStatus.pending.value:
        raise HTTPException(
            status_code=400,
            detail="Can only update experiments in pending status"
        )

    # 更新字段
    if data.name:
        experiment.name = data.name
    if data.description is not None:
        experiment.description = data.description
    if data.config:
        experiment.config = data.config.model_dump()

    experiment.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(experiment)

    return _build_experiment_response(experiment)


@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除实验"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status == ExperimentStatus.running.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a running experiment. Stop it first."
        )

    await db.delete(experiment)
    await db.commit()

    return {"status": "deleted", "id": experiment_id}