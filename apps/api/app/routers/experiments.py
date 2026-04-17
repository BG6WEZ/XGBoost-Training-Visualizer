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
    ExperimentFilterParams,
    ParamTemplatesResponse,
    PARAM_TEMPLATES,
    QueueStatsResponse,
)
from app.services.queue import QueueService, TrainingTask, get_queue_service
from app.services.parameter_validation import ParameterValidationService

router = APIRouter()


def clean_tags(tags: Optional[List[str]]) -> List[str]:
    """
    清洗标签列表
    
    处理规则：
    1. 去掉空字符串
    2. 去掉首尾空格
    3. 去重
    4. 保持原始顺序
    """
    if not tags:
        return []
    
    seen = set()
    cleaned = []
    for tag in tags:
        if not tag:
            continue
        stripped = tag.strip()
        if not stripped:
            continue
        if stripped not in seen:
            seen.add(stripped)
            cleaned.append(stripped)
    
    return cleaned


class ParameterValidationError(HTTPException):
    """参数校验错误"""
    def __init__(self, field_errors: list):
        self.field_errors = field_errors
        super().__init__(
            status_code=422,
            detail={
                "error_code": "PARAM_CONFLICT",
                "message": "训练参数存在冲突",
                "field_errors": [
                    {
                        "fields": e.fields,
                        "rule": e.rule,
                        "current": e.current,
                        "suggestion": e.suggestion
                    }
                    for e in field_errors
                ]
            }
        )


@router.get("/param-templates", response_model=ParamTemplatesResponse)
async def get_param_templates():
    """
    获取参数模板
    
    返回三套预设参数模板：
    - conservative: 保守模板，适合小数据、防过拟合
    - balanced: 平衡模板，通用默认值
    - aggressive: 激进模板，快速探索
    """
    return ParamTemplatesResponse(templates=PARAM_TEMPLATES)


def _build_experiment_response(experiment: Experiment) -> dict:
    """构建实验响应"""
    return {
        "id": str(experiment.id),
        "name": experiment.name,
        "description": experiment.description,
        "dataset_id": str(experiment.dataset_id),
        "subset_id": str(experiment.subset_id) if experiment.subset_id else None,
        "config": experiment.config,
        "tags": experiment.tags if experiment.tags else [],
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
    tags: Optional[str] = None,
    tag_match_mode: str = "any",
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    name_contains: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取实验列表
    
    支持以下筛选参数：
    - status: 按状态筛选
    - tags: 按标签筛选（逗号分隔）
    - tag_match_mode: 标签匹配模式（any=任一匹配, all=全部匹配）
    - created_after: 创建时间起始
    - created_before: 创建时间截止
    - name_contains: 名称模糊搜索
    """
    query = select(Experiment).order_by(Experiment.created_at.desc())

    if status:
        query = query.where(Experiment.status == status)

    if created_after:
        query = query.where(Experiment.created_at >= created_after)

    if created_before:
        query = query.where(Experiment.created_at <= created_before)

    if name_contains:
        query = query.where(Experiment.name.ilike(f"%{name_contains}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    experiments = result.scalars().all()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    filtered_experiments = []
    for e in experiments:
        exp_tags = e.tags if e.tags else []
        
        if tag_list:
            if tag_match_mode == "all":
                if not all(tag in exp_tags for tag in tag_list):
                    continue
            else:
                if not any(tag in exp_tags for tag in tag_list):
                    continue
        
        filtered_experiments.append(e)

    return [
        {
            "id": str(e.id),
            "name": e.name,
            "description": e.description,
            "dataset_id": str(e.dataset_id),
            "tags": e.tags if e.tags else [],
            "status": e.status,
            "created_at": e.created_at,
        }
        for e in filtered_experiments
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
    
    # 参数校验
    xgboost_params = config_dict.get('xgboost_params', {})
    validation_params = {
        'learning_rate': xgboost_params.get('learning_rate', 0.1),
        'max_depth': xgboost_params.get('max_depth', 6),
        'n_estimators': xgboost_params.get('n_estimators', 100),
        'subsample': xgboost_params.get('subsample', 1.0),
        'colsample_bytree': xgboost_params.get('colsample_bytree', 1.0),
        'early_stopping_rounds': config_dict.get('early_stopping_rounds'),
        'min_child_weight': xgboost_params.get('min_child_weight', 1.0),
    }
    
    validation_result = ParameterValidationService.validate_training_params(**validation_params)
    if not validation_result.valid:
        raise ParameterValidationError(validation_result.field_errors)

    # 创建实验
    experiment = Experiment(
        name=data.name,
        description=data.description,
        dataset_id=dataset_uuid,
        subset_id=subset_uuid,
        config=config_dict,
        tags=clean_tags(data.tags),
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
    if data.tags is not None:
        experiment.tags = clean_tags(data.tags)

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


@router.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    queue: QueueService = Depends(get_queue_service)
):
    """
    获取队列统计信息
    
    返回：
    - running_count: 当前运行中的任务数
    - queued_count: 当前排队中的任务数
    - max_concurrency: 并发上限
    - available_slots: 可用槽位数
    - running_experiments: 运行中的实验 ID 列表
    - queue_positions: 排队实验的位置映射
    """
    stats = await queue.get_queue_stats()
    running_experiments = await queue.get_running_tasks()
    queue_positions = await queue.get_all_queue_positions()
    
    return QueueStatsResponse(
        running_count=stats.running_count,
        queued_count=stats.queued_count,
        max_concurrency=stats.max_concurrency,
        available_slots=stats.available_slots,
        running_experiments=running_experiments,
        queue_positions=queue_positions,
    )


@router.get("/with-queue-info", response_model=List[dict])
async def list_experiments_with_queue_info(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    queue: QueueService = Depends(get_queue_service),
):
    """
    获取带队列信息的实验列表
    
    每个实验包含 queue_position 字段：
    - running 状态：queue_position 为 null
    - queued 状态：queue_position 为排队位置（从 1 开始）
    - 其他状态：queue_position 为 null
    """
    query = select(Experiment).order_by(Experiment.created_at.desc())
    
    if status:
        query = query.where(Experiment.status == status)
    
    result = await db.execute(query)
    experiments = result.scalars().all()
    
    queue_positions = await queue.get_all_queue_positions()
    
    response = []
    for e in experiments:
        exp_dict = {
            "id": str(e.id),
            "name": e.name,
            "description": e.description,
            "dataset_id": str(e.dataset_id),
            "status": e.status,
            "created_at": e.created_at,
            "queue_position": None,
        }
        
        if e.status == ExperimentStatus.queued.value:
            exp_dict["queue_position"] = queue_positions.get(str(e.id))
        elif e.status == ExperimentStatus.running.value:
            exp_dict["queue_position"] = None
        
        response.append(exp_dict)
    
    return response