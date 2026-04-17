from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
import uuid
import os
import re
import pandas as pd
import json
import aiofiles
from datetime import datetime

from app.database import get_db
from app.models import Dataset, DatasetFile, FileRole
from app.config import settings
from app.schemas.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetListResponse,
    DatasetFileCreate,
    DatasetFileResponse,
    DatasetPreview,
    PreprocessingRequest,
    PreprocessingResponse,
    FeatureEngineeringRequest,
    FeatureEngineeringResponse,
    AsyncTaskStatus,
    AsyncTaskListResponse,
    SplitRequest,
    SplitResponse,
    UploadResponse,
    QualityScoreResponse,
    QualityDimensionScores,
    JoinRequest,
    JoinResult,
)
from app.services.queue import QueueService, get_queue_service
from app.models import AsyncTask

router = APIRouter()


ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.parquet'}


def _sanitize_upload_filename(filename: str) -> str:
    """Normalize browser-provided upload filename to a safe local filename."""
    # Some browsers send relative paths for folder uploads, e.g. data/weather/a.csv.
    basename = os.path.basename(filename.replace('\\', '/'))
    sanitized = re.sub(r'[^A-Za-z0-9._-]+', '_', basename).strip('._')
    return sanitized or f"upload_{uuid.uuid4().hex}.csv"


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    上传数据文件
    
    支持 CSV、Excel、Parquet 格式
    文件将保存到 WORKSPACE_DIR/uploads 目录
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    original_filename = file.filename
    safe_filename = _sanitize_upload_filename(original_filename)
    
    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    upload_dir = os.path.join(settings.WORKSPACE_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    max_file_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024 if settings.MAX_FILE_SIZE_MB > 0 else None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{safe_filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    file_size = 0
    async with aiofiles.open(file_path, 'wb') as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            file_size += len(chunk)
            if max_file_size_bytes is not None and file_size > max_file_size_bytes:
                await f.close()
                os.remove(file_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
                )
            await f.write(chunk)
    
    if file_size == 0:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Empty file is not allowed")
    
    # 根据文件大小选择行计数策略
    SMALL_THRESHOLD = 10 * 1024 * 1024  # 10MB
    MEDIUM_THRESHOLD = 100 * 1024 * 1024  # 100MB

    estimated = False
    row_count = None
    column_count = None
    columns_info = None

    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path, nrows=100)
            column_count = len(df.columns)
            columns_info = [
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "is_numeric": pd.api.types.is_numeric_dtype(df[col]),
                    "is_datetime": pd.api.types.is_datetime64_any_dtype(df[col]),
                }
                for col in df.columns
            ]
            # 行计数策略：统一使用异步实现
            if file_size < SMALL_THRESHOLD:
                from app.services.storage import count_lines_async
                row_count = await count_lines_async(file_path)
                if row_count > 0:
                    row_count -= 1  # 减去表头
            elif file_size < MEDIUM_THRESHOLD:
                from app.services.storage import count_lines_async
                row_count = await count_lines_async(file_path)
                if row_count > 0:
                    row_count -= 1  # 减去表头
            else:
                from app.services.storage import estimate_line_count
                row_count = await estimate_line_count(file_path)
                estimated = True
        elif file_ext in {'.xlsx', '.xls'}:
            df = pd.read_excel(file_path, nrows=100)
            row_count = len(pd.read_excel(file_path))
            column_count = len(df.columns)
            columns_info = [
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "is_numeric": pd.api.types.is_numeric_dtype(df[col]),
                    "is_datetime": pd.api.types.is_datetime64_any_dtype(df[col]),
                }
                for col in df.columns
            ]
        elif file_ext == '.parquet':
            df = pd.read_parquet(file_path)
            row_count = len(df)
            column_count = len(df.columns)
            columns_info = [
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "is_numeric": pd.api.types.is_numeric_dtype(df[col]),
                    "is_datetime": pd.api.types.is_datetime64_any_dtype(df[col]),
                }
                for col in df.columns
            ]
    except Exception:
        pass

    return UploadResponse(
        file_path=file_path,
        file_name=safe_filename,
        file_size=file_size,
        row_count=row_count,
        column_count=column_count,
        columns_info=columns_info,
        message="File uploaded successfully",
        estimated=estimated if file_ext == '.csv' and file_size >= MEDIUM_THRESHOLD else None
    )


def _build_dataset_response(dataset: Dataset) -> dict:
    """构建数据集响应"""
    return {
        "id": str(dataset.id),
        "name": dataset.name,
        "description": dataset.description,
        "time_column": dataset.time_column,
        "entity_column": dataset.entity_column,
        "target_column": dataset.target_column,
        "total_row_count": dataset.total_row_count,
        "total_column_count": dataset.total_column_count,
        "total_file_size": dataset.total_file_size,
        "files": [
            {
                "id": str(f.id),
                "file_path": f.file_path,
                "file_name": f.file_name,
                "role": f.role,
                "row_count": f.row_count,
                "column_count": f.column_count,
                "file_size": f.file_size,
                "columns_info": f.columns_info,
                "created_at": f.created_at,
            }
            for f in dataset.files
        ],
        "created_at": dataset.created_at,
        "updated_at": dataset.updated_at,
    }


@router.get("/", response_model=List[DatasetListResponse])
async def list_datasets(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取数据集列表"""
    # 查询数据集及其文件数量
    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .order_by(Dataset.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    datasets = result.scalars().all()

    return [
        {
            "id": str(d.id),
            "name": d.name,
            "description": d.description,
            "total_row_count": d.total_row_count,
            "total_column_count": d.total_column_count,
            "total_file_size": d.total_file_size,
            "file_count": len(d.files),
            "created_at": d.created_at,
        }
        for d in datasets
    ]


@router.post("/", response_model=DatasetResponse)
async def create_dataset(
    data: DatasetCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建数据集 - 支持多文件"""
    # 创建数据集
    dataset = Dataset(
        name=data.name,
        description=data.description,
        time_column=data.time_column,
        entity_column=data.entity_column,
        target_column=data.target_column,
    )

    # 添加文件
    total_rows = 0
    total_columns = 0
    total_size = 0

    for file_data in data.files:
        file_record = DatasetFile(
            file_path=file_data.file_path,
            file_name=file_data.file_name,
            role=file_data.role.value,
            row_count=file_data.row_count or 0,
            column_count=file_data.column_count or 0,
            file_size=file_data.file_size or 0,
            columns_info=file_data.columns_info,
        )
        dataset.files.append(file_record)

        # 汇总统计
        total_rows += file_data.row_count or 0
        total_columns = max(total_columns, file_data.column_count or 0)
        total_size += file_data.file_size or 0

    # 更新汇总统计
    dataset.total_row_count = total_rows
    dataset.total_column_count = total_columns
    dataset.total_file_size = total_size

    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    # 重新加载关联
    await db.refresh(dataset, ["files"])

    return _build_dataset_response(dataset)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取数据集详情"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return _build_dataset_response(dataset)


@router.get("/{dataset_id}/quality-score", response_model=QualityScoreResponse)
async def get_dataset_quality_score(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取数据集质量评分
    
    返回四维评分（完整性、准确性、一致性、分布）和总分
    """
    from app.services.data_quality_validator import calculate_quality_score
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    primary_file = None
    for f in dataset.files:
        if f.role == FileRole.primary:
            primary_file = f
            break
    
    if not primary_file:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "NO_PRIMARY_FILE",
                "message": "数据集没有主文件，无法进行质量评分"
            }
        )
    
    if not os.path.exists(primary_file.file_path):
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "FILE_NOT_ACCESSIBLE",
                "message": f"数据文件不可访问: {primary_file.file_path}"
            }
        )
    
    try:
        score_result = calculate_quality_score(
            file_path=primary_file.file_path,
            target_column=dataset.target_column,
            time_column=dataset.time_column
        )
        
        return QualityScoreResponse(
            dataset_id=dataset_id,
            overall_score=score_result["overall_score"],
            dimension_scores=QualityDimensionScores(
                completeness=score_result["dimension_scores"]["completeness"],
                accuracy=score_result["dimension_scores"]["accuracy"],
                consistency=score_result["dimension_scores"]["consistency"],
                distribution=score_result["dimension_scores"]["distribution"]
            ),
            errors=score_result["errors"],
            warnings=score_result["warnings"],
            recommendations=score_result["recommendations"],
            stats=score_result["stats"],
            evaluated_at=score_result["evaluated_at"],
            weights=score_result["weights"]
        )
    except Exception as e:
        import logging
        logging.error(f"质量评分计算失败: dataset_id={dataset_id}, error={str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "QUALITY_SCORE_ERROR",
                "message": f"质量评分计算失败: {str(e)}"
            }
        )


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    data: DatasetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新数据集信息"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 更新字段
    if data.name is not None:
        dataset.name = data.name
    if data.description is not None:
        dataset.description = data.description
    if data.time_column is not None:
        dataset.time_column = data.time_column
    if data.entity_column is not None:
        dataset.entity_column = data.entity_column
    if data.target_column is not None:
        dataset.target_column = data.target_column

    await db.commit()
    await db.refresh(dataset, ["files"])

    return _build_dataset_response(dataset)


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除数据集"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(select(Dataset).where(Dataset.id == dataset_uuid))
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    await db.delete(dataset)
    await db.commit()

    return {"status": "deleted", "id": dataset_id}


@router.get("/{dataset_id}/files", response_model=List[DatasetFileResponse])
async def list_dataset_files(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取数据集文件列表"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(DatasetFile)
        .where(DatasetFile.dataset_id == dataset_uuid)
        .order_by(DatasetFile.created_at)
    )
    files = result.scalars().all()

    return [
        {
            "id": str(f.id),
            "file_path": f.file_path,
            "file_name": f.file_name,
            "role": f.role,
            "row_count": f.row_count,
            "column_count": f.column_count,
            "file_size": f.file_size,
            "columns_info": f.columns_info,
            "created_at": f.created_at,
        }
        for f in files
    ]


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
async def preview_dataset(
    dataset_id: str,
    file_id: str = None,
    rows: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """预览数据集内容"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    # 获取文件
    if file_id:
        try:
            file_uuid = uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        result = await db.execute(
            select(DatasetFile)
            .where(DatasetFile.id == file_uuid)
            .where(DatasetFile.dataset_id == dataset_uuid)
        )
    else:
        # 默认取第一个主文件
        result = await db.execute(
            select(DatasetFile)
            .where(DatasetFile.dataset_id == dataset_uuid)
            .where(DatasetFile.role == FileRole.primary.value)
            .limit(1)
        )

    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # 读取文件
    file_path = file_record.file_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found on disk: {file_path}")

    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, nrows=rows)
        elif file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path).head(rows)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    # 获取总行数
    total_rows = file_record.row_count
    if total_rows == 0:
        # 如果没有记录，尝试获取
        if file_path.endswith('.csv'):
            total_rows = sum(1 for _ in open(file_path)) - 1

    return {
        "file_id": str(file_record.id),
        "file_name": file_record.file_name,
        "columns": list(df.columns),
        "data": df.to_dict(orient='records'),
        "total_rows": total_rows,
        "preview_rows": len(df),
    }


# ========== 文件管理接口 ==========

@router.post("/{dataset_id}/files", response_model=DatasetResponse)
async def add_dataset_file(
    dataset_id: str,
    file_data: DatasetFileCreate,
    db: AsyncSession = Depends(get_db)
):
    """向数据集添加文件"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 创建新文件记录
    new_file = DatasetFile(
        dataset_id=dataset_uuid,
        file_path=file_data.file_path,
        file_name=file_data.file_name,
        role=file_data.role.value,
        row_count=file_data.row_count or 0,
        column_count=file_data.column_count or 0,
        file_size=file_data.file_size or 0,
        columns_info=file_data.columns_info,
    )
    db.add(new_file)

    # 更新聚合统计
    dataset.total_row_count += file_data.row_count or 0
    dataset.total_column_count = max(dataset.total_column_count, file_data.column_count or 0)
    dataset.total_file_size += file_data.file_size or 0

    await db.commit()
    await db.refresh(dataset, ["files"])

    return _build_dataset_response(dataset)


@router.delete("/{dataset_id}/files/{file_id}", response_model=DatasetResponse)
async def remove_dataset_file(
    dataset_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    """从数据集移除文件"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # 获取数据集和文件
    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    result = await db.execute(
        select(DatasetFile)
        .where(DatasetFile.id == file_uuid)
        .where(DatasetFile.dataset_id == dataset_uuid)
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found in dataset")

    # 更新聚合统计
    dataset.total_row_count -= file_record.row_count
    dataset.total_file_size -= file_record.file_size
    # 重新计算最大列数
    remaining_files = [f for f in dataset.files if str(f.id) != file_id]
    dataset.total_column_count = max((f.column_count for f in remaining_files), default=0)

    # 删除文件
    await db.delete(file_record)
    await db.commit()
    await db.refresh(dataset, ["files"])

    return _build_dataset_response(dataset)


@router.put("/{dataset_id}/files", response_model=DatasetResponse)
async def replace_dataset_files(
    dataset_id: str,
    files: List[DatasetFileCreate],
    db: AsyncSession = Depends(get_db)
):
    """替换数据集的文件列表"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 删除所有现有文件
    for existing_file in dataset.files:
        await db.delete(existing_file)

    # 添加新文件
    total_rows = 0
    total_columns = 0
    total_size = 0

    for file_data in files:
        new_file = DatasetFile(
            dataset_id=dataset_uuid,
            file_path=file_data.file_path,
            file_name=file_data.file_name,
            role=file_data.role.value,
            row_count=file_data.row_count or 0,
            column_count=file_data.column_count or 0,
            file_size=file_data.file_size or 0,
            columns_info=file_data.columns_info,
        )
        db.add(new_file)

        total_rows += file_data.row_count or 0
        total_columns = max(total_columns, file_data.column_count or 0)
        total_size += file_data.file_size or 0

    # 更新聚合统计
    dataset.total_row_count = total_rows
    dataset.total_column_count = total_columns
    dataset.total_file_size = total_size

    await db.commit()
    await db.refresh(dataset, ["files"])

    return _build_dataset_response(dataset)


# ========== 预处理和特征工程接口 ==========

@router.post("/{dataset_id}/preprocess", response_model=PreprocessingResponse)
async def preprocess_dataset(
    dataset_id: str,
    request: PreprocessingRequest,
    db: AsyncSession = Depends(get_db),
    queue: QueueService = Depends(get_queue_service)
):
    """
    触发数据集预处理任务

    预处理包括：
    - 缺失值处理
    - 重复行删除
    - 异常值处理
    """
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 获取主文件路径
    primary_file = next(
        (f for f in dataset.files if f.role == FileRole.primary.value),
        dataset.files[0] if dataset.files else None
    )

    if not primary_file:
        raise HTTPException(status_code=400, detail="No primary file in dataset")

    # 构建任务配置
    task_config = {
        "dataset_path": primary_file.file_path,
        "missing_value_strategy": request.config.missing_value_strategy,
        "encoding_strategy": request.config.encoding_strategy,
        "target_columns": request.config.target_columns,
        "remove_duplicates": request.config.remove_duplicates,
        "handle_outliers": request.config.handle_outliers,
        "output_path": request.config.output_path,
    }

    # 创建数据库任务记录（持久化）
    task_id = uuid.uuid4()
    async_task = AsyncTask(
        id=task_id,
        task_type="preprocessing",
        dataset_id=dataset_uuid,
        status="queued",
        config=task_config,
    )
    db.add(async_task)
    await db.commit()

    # 发布任务到队列
    await queue.redis.rpush(
        "preprocessing:queue",
        json.dumps({
            "task_id": str(task_id),
            "dataset_id": dataset_id,
            "config": task_config
        })
    )

    return PreprocessingResponse(
        task_id=str(task_id),
        dataset_id=dataset_id,
        status="queued",
        message="Preprocessing task has been queued"
    )


@router.post("/{dataset_id}/feature-engineering", response_model=FeatureEngineeringResponse)
async def feature_engineering_dataset(
    dataset_id: str,
    request: FeatureEngineeringRequest,
    db: AsyncSession = Depends(get_db),
    queue: QueueService = Depends(get_queue_service)
):
    """
    触发特征工程任务

    特征工程包括：
    - 时间特征提取
    - 滞后特征
    - 滚动统计特征
    """
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 获取主文件路径
    primary_file = next(
        (f for f in dataset.files if f.role == FileRole.primary.value),
        dataset.files[0] if dataset.files else None
    )

    if not primary_file:
        raise HTTPException(status_code=400, detail="No primary file in dataset")

    # 构建任务配置
    task_config = {
        "dataset_path": primary_file.file_path,
        "time_features": request.config.time_features.model_dump(),
        "lag_features": request.config.lag_features.model_dump(),
        "rolling_features": request.config.rolling_features.model_dump(),
        "output_path": request.config.output_path,
    }

    # 创建数据库任务记录（持久化）
    task_id = uuid.uuid4()
    async_task = AsyncTask(
        id=task_id,
        task_type="feature_engineering",
        dataset_id=dataset_uuid,
        status="queued",
        config=task_config,
    )
    db.add(async_task)
    await db.commit()

    # 发布任务到队列
    await queue.redis.rpush(
        "feature_engineering:queue",
        json.dumps({
            "task_id": str(task_id),
            "dataset_id": dataset_id,
            "config": task_config
        })
    )

    return FeatureEngineeringResponse(
        task_id=str(task_id),
        dataset_id=dataset_id,
        status="queued",
        message="Feature engineering task has been queued"
    )


# ========== 异步任务状态查询接口 ==========

@router.get("/tasks/{task_id}", response_model=AsyncTaskStatus)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    查询异步任务状态

    用于查询预处理/特征工程任务的执行状态和结果
    """
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    result = await db.execute(
        select(AsyncTask).where(AsyncTask.id == task_uuid)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return AsyncTaskStatus(
        id=str(task.id),
        task_type=task.task_type,
        dataset_id=str(task.dataset_id),
        status=task.status,
        error_message=task.error_message,
        config=task.config,
        result=task.result,
        created_at=task.created_at,
        started_at=task.started_at,
        finished_at=task.finished_at,
    )


@router.get("/{dataset_id}/tasks", response_model=List[AsyncTaskListResponse])
async def list_dataset_tasks(
    dataset_id: str,
    task_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    获取数据集的异步任务列表

    可按任务类型过滤（preprocessing, feature_engineering）
    """
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    query = select(AsyncTask).where(AsyncTask.dataset_id == dataset_uuid)

    if task_type:
        query = query.where(AsyncTask.task_type == task_type)

    query = query.order_by(AsyncTask.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [
        AsyncTaskListResponse(
            id=str(t.id),
            task_type=t.task_type,
            dataset_id=str(t.dataset_id),
            status=t.status,
            created_at=t.created_at,
            finished_at=t.finished_at,
        )
        for t in tasks
    ]


@router.post("/{dataset_id}/split", response_model=SplitResponse)
async def split_dataset(
    dataset_id: str,
    request: SplitRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    切分数据集为训练集、验证集、测试集

    支持两种切分方式：
    - random: 随机切分（默认）
    - time: 时间切分（适用于时序数据）

    时间切分参数：
    - time_column: 时间列名（如果数据集已配置可省略）
    - train_end_date: 训练集结束日期
    - val_start_date: 验证集开始日期
    - val_end_date: 验证集结束日期
    - test_start_date: 测试集开始日期
    """
    from app.models import DatasetSubset
    import json

    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    primary_file = next(
        (f for f in dataset.files if f.role == FileRole.primary.value),
        dataset.files[0] if dataset.files else None
    )

    if not primary_file:
        raise HTTPException(status_code=400, detail="No primary file in dataset")

    try:
        df = pd.read_csv(primary_file.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read dataset: {str(e)}")

    # 使用统一的 WORKSPACE_DIR 配置
    workspace = settings.WORKSPACE_DIR
    os.makedirs(f"{workspace}/splits", exist_ok=True)

    effective_time_column = request.time_column or dataset.time_column

    if request.split_method == "time":
        if not effective_time_column:
            raise HTTPException(
                status_code=400,
                detail="Time column is required for time-based split. "
                       "Please specify time_column or configure it on the dataset."
            )

        if effective_time_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Time column '{effective_time_column}' not found in dataset. "
                       f"Available columns: {list(df.columns)}"
            )

        try:
            df[effective_time_column] = pd.to_datetime(df[effective_time_column])
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse time column: {str(e)}"
            )

        df = df.sort_values(effective_time_column).reset_index(drop=True)

        time_min = df[effective_time_column].min()
        time_max = df[effective_time_column].max()

        train_end_date = request.train_end_date
        if not train_end_date:
            total_rows = len(df)
            train_rows = int(total_rows * (1 - request.test_size))
            train_end_ts = df[effective_time_column].iloc[train_rows - 1]
            train_end_date = train_end_ts.strftime("%Y-%m-%d %H:%M:%S")

        train_end_dt = pd.to_datetime(train_end_date)

        train_mask = df[effective_time_column] <= train_end_dt
        train_df = df[train_mask].copy()

        remaining_df = df[~train_mask].copy()

        val_df = pd.DataFrame()
        if request.val_start_date and request.val_end_date:
            val_start_dt = pd.to_datetime(request.val_start_date)
            val_end_dt = pd.to_datetime(request.val_end_date)
            val_mask = (remaining_df[effective_time_column] >= val_start_dt) & \
                       (remaining_df[effective_time_column] <= val_end_dt)
            val_df = remaining_df[val_mask].copy()
            test_df = remaining_df[~val_mask].copy()
        else:
            test_df = remaining_df

        split_config = {
            "method": "time",
            "time_column": effective_time_column,
            "train_end_date": train_end_date,
            "val_start_date": request.val_start_date,
            "val_end_date": request.val_end_date,
            "test_start_date": request.test_start_date,
            "time_range": {
                "min": str(time_min),
                "max": str(time_max)
            }
        }

    else:
        train_df = df.sample(frac=1 - request.test_size, random_state=request.random_seed)
        test_df = df.drop(train_df.index)
        val_df = pd.DataFrame()

        split_config = {
            "method": "random",
            "test_size": request.test_size,
            "random_seed": request.random_seed
        }

    subsets_to_create = []

    train_path = f"{workspace}/splits/{dataset_id}_train.csv"
    train_df.to_csv(train_path, index=False)
    subsets_to_create.append({
        "name": f"{dataset.name} - Train",
        "purpose": "train",
        "file_path": train_path,
        "row_count": len(train_df),
        "split_config": {**split_config, "subset": "train"}
    })

    if len(val_df) > 0:
        val_path = f"{workspace}/splits/{dataset_id}_val.csv"
        val_df.to_csv(val_path, index=False)
        subsets_to_create.append({
            "name": f"{dataset.name} - Validation",
            "purpose": "validation",
            "file_path": val_path,
            "row_count": len(val_df),
            "split_config": {**split_config, "subset": "validation"}
        })

    test_path = f"{workspace}/splits/{dataset_id}_test.csv"
    test_df.to_csv(test_path, index=False)
    subsets_to_create.append({
        "name": f"{dataset.name} - Test",
        "purpose": "test",
        "file_path": test_path,
        "row_count": len(test_df),
        "split_config": {**split_config, "subset": "test"}
    })

    created_subsets = []
    for subset_info in subsets_to_create:
        subset = DatasetSubset(
            parent_dataset_id=dataset_uuid,
            name=subset_info["name"],
            purpose=subset_info["purpose"],
            file_path=subset_info["file_path"],
            row_count=subset_info["row_count"],
            split_config=subset_info["split_config"]
        )
        db.add(subset)
        created_subsets.append(subset)

    await db.commit()

    response_subsets = []
    for subset in created_subsets:
        await db.refresh(subset)
        response_subsets.append({
            "id": str(subset.id),
            "name": subset.name,
            "purpose": subset.purpose,
            "row_count": subset.row_count,
            "file_path": subset.file_path
        })

    return SplitResponse(
        dataset_id=dataset_id,
        split_method=request.split_method,
        subsets=response_subsets,
        split_config=split_config
    )


# ========== Data Join Interface ==========


@router.post("/{dataset_id}/join", response_model=JoinResult)
async def join_dataset(
    dataset_id: str,
    request: JoinRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    多表级联Join
    
    将主数据集与多个从表进行Join操作，支持多种Join类型：
    - left: 左连接，保留主表所有行
    - inner: 内连接，只保留匹配的行
    - right: 右连接，保留从表所有行
    - outer: 外连接，保留所有行
    
    自动处理：
    - 编码问题（UTF-8, GBK, Latin-1等）
    - 列重名问题（自动重命名）
    - 行数变化统计
    """
    from app.services.data_fusion import execute_data_join, DataFusionError
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")
    
    # 获取数据集
    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_uuid)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # 获取主文件
    primary_file = next(
        (f for f in dataset.files if f.role == FileRole.primary.value),
        dataset.files[0] if dataset.files else None
    )
    
    if not primary_file:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "NO_PRIMARY_FILE",
                "message": "数据集没有主文件，无法执行Join操作"
            }
        )
    
    # 执行Join
    output_dir = os.path.join(settings.WORKSPACE_DIR, "joined")
    
    try:
        join_result = execute_data_join(
            main_file_path=primary_file.file_path,
            main_join_key=request.main_join_key,
            join_tables=request.join_tables,
            output_dir=output_dir
        )
        
        return JoinResult(
            success=join_result["success"],
            before_rows=join_result["before_rows"],
            after_rows=join_result["after_rows"],
            rows_lost=join_result["rows_lost"],
            rows_added_columns=join_result["rows_added_columns"],
            message=join_result["message"],
            joined_columns=join_result["joined_columns"],
            output_file_path=join_result["output_file_path"]
        )
        
    except DataFusionError as e:
        # 根据错误类型返回不同的HTTP状态码
        error_code = e.error_code
        
        if error_code == "MAIN_JOIN_KEY_NOT_FOUND":
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": error_code,
                    "message": e.message,
                    "details": e.details
                }
            )
        elif error_code in ["JOIN_TABLE_FILE_NOT_FOUND", "JOIN_TABLE_KEY_NOT_FOUND"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": error_code,
                    "message": e.message,
                    "details": e.details
                }
            )
        elif error_code == "MAIN_FILE_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": error_code,
                    "message": e.message,
                    "details": e.details
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": error_code,
                    "message": e.message,
                    "details": e.details
                }
            )
    except Exception as e:
        import logging
        logging.error(f"Join操作失败: dataset_id={dataset_id}, error={str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOIN_ERROR",
                "message": f"Join操作失败: {str(e)}"
            }
        )