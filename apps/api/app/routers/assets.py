"""
数据资产扫描与登记 API

提供：
- 扫描 dataset/ 目录发现可用数据资产
- 获取扫描到的数据资产列表
- 将数据资产登记为可训练数据集
- 自动生成 Schema Profile
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
import logging

from app.database import get_db
from app.models import Dataset, DatasetFile
from app.services.dataset_scanner import (
    DatasetScanner,
    SchemaProfiler,
    register_dataset_asset
)
from app.services.data_quality_validator import (
    DataQualityValidator,
    DataQualityError
)
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== Schemas ==========

class ScannedAssetResponse(BaseModel):
    """扫描到的数据资产响应"""
    name: str
    source_type: str
    source_name: str
    path: str
    path_type: str  # file, directory
    is_raw: bool
    description: Optional[str] = None
    member_files: List[dict]
    registered: bool = False
    registered_dataset_id: Optional[str] = None


class ScanResultResponse(BaseModel):
    """扫描结果响应"""
    total_assets: int
    assets: List[ScannedAssetResponse]


class ColumnInfo(BaseModel):
    """列信息"""
    name: str
    dtype: str
    missing_count: int
    missing_rate: float
    unique_count: int
    is_numeric: bool
    is_datetime: bool
    is_categorical: bool
    is_time_candidate: bool
    is_target_candidate: bool
    is_entity_candidate: bool
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None


class FileProfileResponse(BaseModel):
    """文件 Profile 响应"""
    file_path: str
    file_name: str
    row_count: int
    column_count: int
    columns_info: List[ColumnInfo]
    time_candidates: List[str]
    target_candidates: List[str]
    entity_candidates: List[str]
    quality_summary: dict


class RegisterAssetRequest(BaseModel):
    """登记数据资产请求"""
    asset_name: str
    source_type: str
    path: str
    path_type: str
    is_raw: bool = True
    description: Optional[str] = None
    member_files: List[dict]
    auto_detect_columns: bool = True  # 是否自动检测时间列/目标列


class DatasetSourceInfo(BaseModel):
    """数据源信息"""
    key: str
    name: str
    description: str
    asset_count: int


# ========== API Endpoints ==========

@router.get("/sources", response_model=List[DatasetSourceInfo])
async def list_available_sources():
    """
    列出所有支持的数据源类型
    """
    from app.services.dataset_scanner import DATASET_SOURCES

    return [
        DatasetSourceInfo(
            key=key,
            name=info["name"],
            description=info["description"],
            asset_count=0  # 需要扫描后才能知道
        )
        for key, info in DATASET_SOURCES.items()
    ]


@router.get("/scan", response_model=ScanResultResponse)
async def scan_dataset_directory(
    db: AsyncSession = Depends(get_db)
):
    """
    扫描 dataset/ 目录，发现可登记的数据资产

    返回所有发现的数据资产，并标注是否已登记
    """
    # 获取数据集根目录（配置已使用绝对路径）
    dataset_base = settings.DATASET_DIR

    if not os.path.exists(dataset_base):
        raise HTTPException(
            status_code=404,
            detail=f"Dataset directory not found: {dataset_base}"
        )

    # 扫描目录
    scanner = DatasetScanner(dataset_base)
    try:
        assets = scanner.scan_directory()
    except Exception as e:
        logger.error(f"Failed to scan dataset directory: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

    # 查询已登记的数据集（使用 eager loading 避免懒加载问题）
    result = await db.execute(
        select(Dataset).options(selectinload(Dataset.files))
    )
    existing_datasets = result.scalars().all()

    # 建立路径到数据集的映射
    registered_paths = {}
    for ds in existing_datasets:
        for f in ds.files:
            registered_paths[f.file_path] = str(ds.id)

    # 标记已登记状态
    for asset in assets:
        # 检查是否已登记（根据第一个主文件的路径）
        primary_files = [m for m in asset.get("member_files", []) if m.get("role") == "primary"]
        if primary_files:
            first_primary = primary_files[0]["file_path"]
            if first_primary in registered_paths:
                asset["registered"] = True
                asset["registered_dataset_id"] = registered_paths[first_primary]

    return ScanResultResponse(
        total_assets=len(assets),
        assets=[ScannedAssetResponse(**a) for a in assets]
    )


@router.get("/profile", response_model=FileProfileResponse)
async def profile_file(
    file_path: str,
    sample_rows: int = 1000
):
    """
    分析指定文件的 Schema Profile

    返回列信息、候选列推荐、数据质量摘要
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        profile = SchemaProfiler.profile_file(file_path, sample_rows)
        return FileProfileResponse(**profile)
    except Exception as e:
        logger.error(f"Failed to profile file: {e}")
        raise HTTPException(status_code=500, detail=f"Profile failed: {str(e)}")


@router.post("/register", response_model=dict)
async def register_asset(
    request: RegisterAssetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    将扫描到的数据资产登记为可训练数据集

    自动生成 Schema Profile 并创建数据集记录
    """
    # 检查是否已存在相同路径的数据集（防止重复登记）
    primary_files = [m for m in request.member_files if m.get("role") == "primary"]
    if primary_files:
        first_primary_path = primary_files[0]["file_path"]
        
        # 查询是否存在相同文件路径的数据集
        existing_result = await db.execute(
            select(DatasetFile).where(DatasetFile.file_path == first_primary_path)
        )
        existing_file = existing_result.scalar_one_or_none()
        
        if existing_file:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset already registered with this primary file: {first_primary_path}"
            )
    
    # 构建资产信息
    asset_info = {
        "name": request.asset_name,
        "source_type": request.source_type,
        "path": request.path,
        "path_type": request.path_type,
        "is_raw": request.is_raw,
        "description": request.description,
        "member_files": request.member_files
    }

    try:
        # 登记数据集
        dataset = await register_dataset_asset(
            asset_info,
            db,
            generate_profile=True
        )

        # 自动检测列
        if request.auto_detect_columns:
            # 从第一个主文件的 profile 中获取候选列
            # 使用已创建的文件列表（避免懒加载）
            primary_file_info = None
            for member in request.member_files:
                if member.get("role") == "primary":
                    primary_file_info = member
                    break
            
            if primary_file_info:
                # 直接从文件获取 profile
                try:
                    profile = SchemaProfiler.profile_file(primary_file_info["file_path"])
                    columns_info = profile.get("columns_info", [])
                    
                    # 查找时间列候选
                    time_candidates = [
                        c["name"] for c in columns_info
                        if c.get("is_time_candidate")
                    ]
                    if time_candidates:
                        dataset.time_column = time_candidates[0]

                    # 查找目标列候选
                    target_candidates = [
                        c["name"] for c in columns_info
                        if c.get("is_target_candidate")
                    ]
                    if target_candidates:
                        dataset.target_column = target_candidates[0]

                    # 查找实体列候选
                    entity_candidates = [
                        c["name"] for c in columns_info
                        if c.get("is_entity_candidate")
                    ]
                    if entity_candidates:
                        dataset.entity_column = entity_candidates[0]
                except Exception as e:
                    logger.warning(f"Failed to auto-detect columns: {e}")

        # ========== 数据质量校验 ==========
        # 对主文件进行质量检查
        if primary_file_info:
            try:
                quality_result = DataQualityValidator.validate_for_training(
                    file_path=primary_file_info["file_path"],
                    target_column=dataset.target_column,
                    time_column=dataset.time_column,
                    sample_rows=10000
                )
                
                # 记录质量检查结果（即使通过也有警告信息）
                if quality_result.get("warnings"):
                    logger.info(
                        f"Data quality warnings for {request.asset_name}: "
                        f"{quality_result['warnings']}"
                    )
                    
                logger.info(
                    f"Data quality validation passed for {request.asset_name}: "
                    f"{quality_result['stats']}"
                )
                    
            except DataQualityError as e:
                # 质量检查失败，返回明确的错误信息
                logger.error(
                    f"Data quality validation failed for {request.asset_name}: "
                    f"{e.error_code} - {e.message}"
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_type": "DATA_QUALITY_ERROR",
                        "error_code": e.error_code,
                        "message": e.message,
                        "details": e.details
                    }
                )

        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        
        # 使用 selectinload 预加载 files 关系
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Dataset).options(selectinload(Dataset.files)).where(Dataset.id == dataset.id)
        )
        dataset = result.scalar_one()

        return {
            "id": str(dataset.id),
            "name": dataset.name,
            "time_column": dataset.time_column,
            "entity_column": dataset.entity_column,
            "target_column": dataset.target_column,
            "total_row_count": dataset.total_row_count,
            "total_column_count": dataset.total_column_count,
            "file_count": len(dataset.files),
            "status": "registered"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register asset: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/register-batch", response_model=dict)
async def register_assets_batch(
    assets: List[RegisterAssetRequest],
    db: AsyncSession = Depends(get_db)
):
    """
    批量登记数据资产

    一次性登记多个数据资产
    """
    results = []
    success_count = 0

    for asset_request in assets:
        try:
            # 检查是否已存在相同路径的数据集（防止重复登记）
            primary_files = [m for m in asset_request.member_files if m.get("role") == "primary"]
            if primary_files:
                first_primary_path = primary_files[0]["file_path"]
                
                existing_result = await db.execute(
                    select(DatasetFile).where(DatasetFile.file_path == first_primary_path)
                )
                existing_file = existing_result.scalar_one_or_none()
                
                if existing_file:
                    results.append({
                        "name": asset_request.asset_name,
                        "id": None,
                        "status": "failed",
                        "error": f"Dataset already registered: {first_primary_path}"
                    })
                    continue
            
            asset_info = {
                "name": asset_request.asset_name,
                "source_type": asset_request.source_type,
                "path": asset_request.path,
                "path_type": asset_request.path_type,
                "is_raw": asset_request.is_raw,
                "description": asset_request.description,
                "member_files": asset_request.member_files
            }

            dataset = await register_dataset_asset(
                asset_info,
                db,
                generate_profile=True
            )

            # 自动检测列
            if asset_request.auto_detect_columns:
                # 从第一个主文件的 profile 中获取候选列
                primary_file_info = None
                for member in asset_request.member_files:
                    if member.get("role") == "primary":
                        primary_file_info = member
                        break
                
                if primary_file_info:
                    try:
                        profile = SchemaProfiler.profile_file(primary_file_info["file_path"])
                        columns_info = profile.get("columns_info", [])
                        
                        # 查找时间列候选
                        time_candidates = [
                            c["name"] for c in columns_info
                            if c.get("is_time_candidate")
                        ]
                        if time_candidates:
                            dataset.time_column = time_candidates[0]

                        # 查找目标列候选
                        target_candidates = [
                            c["name"] for c in columns_info
                            if c.get("is_target_candidate")
                        ]
                        if target_candidates:
                            dataset.target_column = target_candidates[0]

                        # 查找实体列候选
                        entity_candidates = [
                            c["name"] for c in columns_info
                            if c.get("is_entity_candidate")
                        ]
                        if entity_candidates:
                            dataset.entity_column = entity_candidates[0]
                    except Exception as e:
                        logger.warning(f"Failed to auto-detect columns: {e}")

            # ========== 数据质量校验 ==========
            if primary_file_info:
                try:
                    quality_result = DataQualityValidator.validate_for_training(
                        file_path=primary_file_info["file_path"],
                        target_column=dataset.target_column,
                        time_column=dataset.time_column,
                        sample_rows=10000
                    )
                    
                    if quality_result.get("warnings"):
                        logger.info(
                            f"Data quality warnings for {asset_request.asset_name}: "
                            f"{quality_result['warnings']}"
                        )
                        
                except DataQualityError as e:
                    results.append({
                        "name": asset_request.asset_name,
                        "id": None,
                        "status": "failed",
                        "error": {
                            "error_type": "DATA_QUALITY_ERROR",
                            "error_code": e.error_code,
                            "message": e.message,
                            "details": e.details
                        }
                    })
                    continue

            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)

            results.append({
                "name": dataset.name,
                "id": str(dataset.id),
                "status": "success"
            })
            success_count += 1

        except HTTPException:
            raise
        except Exception as e:
            results.append({
                "name": asset_request.asset_name,
                "id": None,
                "status": "failed",
                "error": str(e)
            })

    return {
        "total": len(assets),
        "success": success_count,
        "failed": len(assets) - success_count,
        "results": results
    }