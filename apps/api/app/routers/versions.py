"""
模型版本管理 Router

P1-T13: 模型版本管理
提供版本创建、列表、比较、回滚等接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.database import get_db
from app.models.models import ModelVersion, Experiment, Model, ExperimentStatus
from app.schemas.version import (
    ModelVersionCreate,
    ModelVersionResponse,
    ModelVersionListResponse,
    VersionCompareRequest,
    VersionCompareResponse,
    VersionRollbackResponse,
    VersionTagUpdate,
    ConfigDiff,
    MetricsDiff,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _generate_version_number(existing_count: int) -> str:
    """
    生成版本号
    
    规则：v{major}.{minor}.{patch}
    - major: 主版本号，重大变更时递增
    - minor: 次版本号，功能增强时递增
    - patch: 补丁版本号，bug修复时递增
    
    初始版本为 v1.0.0，后续版本依次递增 minor
    """
    major = 1
    minor = existing_count
    patch = 0
    return f"v{major}.{minor}.{patch}"


def _build_version_response(version: ModelVersion) -> dict:
    """构建版本响应"""
    return {
        "id": str(version.id),
        "experiment_id": str(version.experiment_id),
        "version_number": version.version_number,
        "config_snapshot": version.config_snapshot or {},
        "metrics_snapshot": version.metrics_snapshot or {},
        "tags": version.tags if version.tags else [],
        "is_active": bool(version.is_active),
        "source_model_id": str(version.source_model_id) if version.source_model_id else None,
        "created_at": version.created_at,
    }


@router.get("/experiments/{experiment_id}/versions", response_model=List[ModelVersionListResponse])
async def list_versions(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取实验的版本列表
    
    返回该实验的所有版本，按创建时间倒序排列
    """
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(Experiment).where(Experiment.id == exp_uuid)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.experiment_id == exp_uuid)
        .order_by(ModelVersion.created_at.desc())
    )
    versions = result.scalars().all()

    return [
        {
            "id": str(v.id),
            "experiment_id": str(v.experiment_id),
            "version_number": v.version_number,
            "metrics_snapshot": v.metrics_snapshot or {},
            "tags": v.tags if v.tags else [],
            "is_active": bool(v.is_active),
            "created_at": v.created_at,
        }
        for v in versions
    ]


@router.get("/versions/{version_id}", response_model=ModelVersionResponse)
async def get_version(
    version_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取版本详情"""
    try:
        version_uuid = uuid.UUID(version_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid version ID format")

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.id == version_uuid)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return _build_version_response(version)


@router.post("/versions", response_model=ModelVersionResponse)
async def create_version(
    data: ModelVersionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    手动创建模型版本
    
    通常版本在训练完成时自动创建，此接口用于手动创建版本
    """
    try:
        exp_uuid = uuid.UUID(data.experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(Experiment).where(Experiment.id == exp_uuid)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status != ExperimentStatus.completed.value:
        raise HTTPException(
            status_code=400,
            detail="Can only create version for completed experiments"
        )

    result = await db.execute(
        select(Model).where(Model.experiment_id == exp_uuid)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found for this experiment")

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.experiment_id == exp_uuid)
    )
    existing_versions = result.scalars().all()
    version_number = _generate_version_number(len(existing_versions))

    version = ModelVersion(
        experiment_id=exp_uuid,
        version_number=version_number,
        config_snapshot=experiment.config,
        metrics_snapshot=model.metrics or {},
        tags=data.tags or [],
        is_active=1,
        source_model_id=model.id,
    )

    result = await db.execute(
        select(ModelVersion).where(
            and_(
                ModelVersion.experiment_id == exp_uuid,
                ModelVersion.is_active == 1
            )
        )
    )
    previous_active = result.scalar_one_or_none()
    if previous_active:
        previous_active.is_active = 0

    db.add(version)
    await db.commit()
    await db.refresh(version)

    logger.info(f"Created version {version_number} for experiment {data.experiment_id}")

    return _build_version_response(version)


@router.post("/versions/compare", response_model=VersionCompareResponse)
async def compare_versions(
    data: VersionCompareRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    比较多个版本
    
    支持 2-3 个版本比较，返回配置差异和指标差异
    """
    if len(data.version_ids) < 2 or len(data.version_ids) > 3:
        raise HTTPException(
            status_code=400,
            detail="Must compare 2-3 versions"
        )

    version_uuids = []
    for vid in data.version_ids:
        try:
            version_uuids.append(uuid.UUID(vid))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid version ID format: {vid}")

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.id.in_(version_uuids))
    )
    versions = result.scalars().all()

    if len(versions) != len(data.version_ids):
        found_ids = {str(v.id) for v in versions}
        missing_ids = set(data.version_ids) - found_ids
        raise HTTPException(
            status_code=404,
            detail=f"Versions not found: {missing_ids}"
        )

    version_map = {str(v.id): v for v in versions}
    ordered_versions = [version_map[vid] for vid in data.version_ids]

    config_diffs = _compute_config_diffs(ordered_versions)
    metrics_diffs = _compute_metrics_diffs(ordered_versions)

    return VersionCompareResponse(
        versions=[_build_version_response(v) for v in ordered_versions],
        config_diffs=config_diffs,
        metrics_diffs=metrics_diffs,
    )


def _compute_config_diffs(versions: List[ModelVersion]) -> List[ConfigDiff]:
    """计算配置差异"""
    all_params = set()
    config_maps = []

    for v in versions:
        config = v.config_snapshot or {}
        xgb_params = config.get("xgboost_params", {})
        all_params.update(xgb_params.keys())
        config_maps.append(xgb_params)

    diffs = []
    for param in sorted(all_params):
        values = {}
        for i, v in enumerate(versions):
            version_label = v.version_number
            values[version_label] = config_maps[i].get(param)

        if len(set(values.values())) > 1:
            diffs.append(ConfigDiff(param_name=param, values=values))

    return diffs


def _compute_metrics_diffs(versions: List[ModelVersion]) -> List[MetricsDiff]:
    """计算指标差异"""
    metric_names = ["train_rmse", "val_rmse", "train_mae", "val_mae", "r2"]
    diffs = []

    base_metrics = versions[0].metrics_snapshot or {}

    for metric in metric_names:
        values = {}
        for v in versions:
            metrics = v.metrics_snapshot or {}
            values[v.version_number] = metrics.get(metric)

        if any(v is not None for v in values.values()):
            change = None
            base_value = base_metrics.get(metric)
            if base_value is not None and base_value != 0:
                change = {}
                for v in versions[1:]:
                    current_value = v.metrics_snapshot.get(metric) if v.metrics_snapshot else None
                    if current_value is not None:
                        change_pct = ((current_value - base_value) / base_value) * 100
                        change[v.version_number] = round(change_pct, 2)

            diffs.append(MetricsDiff(
                metric_name=metric,
                values=values,
                change=change
            ))

    return diffs


@router.post("/versions/{version_id}/rollback", response_model=VersionRollbackResponse)
async def rollback_version(
    version_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    回滚到指定版本
    
    将指定版本设为激活版本，之前的激活版本变为非激活
    注意：此操作仅切换激活状态引用，不触发重新训练
    """
    try:
        version_uuid = uuid.UUID(version_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid version ID format")

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.id == version_uuid)
    )
    target_version = result.scalar_one_or_none()
    if not target_version:
        raise HTTPException(status_code=404, detail="Version not found")

    if target_version.is_active == 1:
        return VersionRollbackResponse(
            success=True,
            previous_active_version_id=None,
            new_active_version_id=str(target_version.id),
            message=f"Version {target_version.version_number} is already active"
        )

    result = await db.execute(
        select(ModelVersion).where(
            and_(
                ModelVersion.experiment_id == target_version.experiment_id,
                ModelVersion.is_active == 1
            )
        )
    )
    previous_active = result.scalar_one_or_none()
    previous_active_id = str(previous_active.id) if previous_active else None

    if previous_active:
        previous_active.is_active = 0

    target_version.is_active = 1
    await db.commit()

    logger.info(
        f"Rolled back to version {target_version.version_number} "
        f"(previous: {previous_active.version_number if previous_active else 'None'})"
    )

    return VersionRollbackResponse(
        success=True,
        previous_active_version_id=previous_active_id,
        new_active_version_id=str(target_version.id),
        message=f"Successfully rolled back to version {target_version.version_number}. "
                f"Note: This only changes the active version reference, "
                f"does not re-train or replace the model file."
    )


@router.patch("/versions/{version_id}/tags", response_model=ModelVersionResponse)
async def update_version_tags(
    version_id: str,
    data: VersionTagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新版本标签"""
    try:
        version_uuid = uuid.UUID(version_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid version ID format")

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.id == version_uuid)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    cleaned_tags = []
    seen = set()
    for tag in data.tags:
        if tag and tag.strip():
            stripped = tag.strip()
            if stripped not in seen:
                seen.add(stripped)
                cleaned_tags.append(stripped)

    version.tags = cleaned_tags
    await db.commit()
    await db.refresh(version)

    return _build_version_response(version)


@router.get("/experiments/{experiment_id}/versions/active", response_model=Optional[ModelVersionResponse])
async def get_active_version(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取实验的当前激活版本"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(ModelVersion).where(
            and_(
                ModelVersion.experiment_id == exp_uuid,
                ModelVersion.is_active == 1
            )
        )
    )
    version = result.scalar_one_or_none()

    if not version:
        return None

    return _build_version_response(version)
