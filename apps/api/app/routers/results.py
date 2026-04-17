from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
import os
import io
import json
import numpy as np

from app.database import get_db
from app.models import Experiment, TrainingMetric, FeatureImportance, Model, ExperimentStatus
from app.schemas.results import (
    ExperimentResultResponse, ExperimentMetrics, FeatureImportanceItem, ModelInfo,
    FeatureImportanceResponse, FeatureImportanceDetail,
    MetricsHistoryResponse,
    CompareExperimentsResponse, ExperimentComparisonItem,
    ExperimentReportResponse, ExperimentReportExperiment,
    ReportMetricItem, ReportFeatureImportance, ReportModelInfo,
    PredictionAnalysisResponse, PredictionAnalysisData,
    ResidualSummary, PredictionScatterPoint, ResidualHistogramBin, ResidualScatterPoint,
    BenchmarkMetrics
)
from app.services.storage import get_storage_service
from app.services.benchmark import calculate_benchmark_metrics

router = APIRouter()


@router.get("/{experiment_id}", response_model=ExperimentResultResponse)
async def get_results(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取实验结果

    返回实验的完整结果信息，包括指标、特征重要性和模型信息
    """
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # 获取最终指标（最后一条记录）
    metric_result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration.desc())
        .limit(1)
    )
    latest_metric = metric_result.scalar_one_or_none()

    # 获取特征重要性
    fi_result = await db.execute(
        select(FeatureImportance)
        .where(FeatureImportance.experiment_id == exp_uuid)
        .order_by(FeatureImportance.rank.asc())
    )
    feature_importance = fi_result.scalars().all()

    # 获取模型信息
    model_result = await db.execute(
        select(Model).where(Model.experiment_id == exp_uuid).limit(1)
    )
    model = model_result.scalar_one_or_none()

    benchmark_metrics = None
    if experiment.status == "completed":
        try:
            storage = get_storage_service()
            prediction_data_bytes = await storage.get_prediction_data(experiment_id)
            prediction_data = json.loads(prediction_data_bytes.decode('utf-8'))
            validation_data = prediction_data.get("validation", {})
            actual_values = validation_data.get("actual_values", [])
            predicted_values = validation_data.get("predicted_values", [])
            if actual_values and predicted_values:
                benchmark_metrics = calculate_benchmark_metrics(actual_values, predicted_values)
        except FileNotFoundError:
            pass
        except RuntimeError:
            pass
        except Exception:
            pass

    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment.name,
        "status": experiment.status,
        "metrics": {
            "train_rmse": latest_metric.train_loss if latest_metric else None,
            "val_rmse": latest_metric.val_loss if latest_metric else None,
            "r2": model.metrics.get("r2") if model and model.metrics else None,
            "mae": model.metrics.get("mae") if model and model.metrics else None,
        },
        "benchmark": benchmark_metrics,
        "benchmark_mode": "standard",
        "feature_importance": [
            {
                "feature_name": fi.feature_name,
                "importance": fi.importance,
                "rank": fi.rank
            }
            for fi in feature_importance
        ],
        "model": {
            "id": str(model.id) if model else None,
            "format": model.format if model else None,
            "file_size": model.file_size if model else None,
            "storage_type": model.storage_type if model else None,
            "object_key": model.object_key if model else None,
        } if model else None,
        "training_time_seconds": (
            (experiment.finished_at - experiment.started_at).total_seconds()
            if experiment.started_at and experiment.finished_at else None
        )
    }


@router.get("/{experiment_id}/feature-importance", response_model=FeatureImportanceResponse)
async def get_feature_importance(
    experiment_id: str,
    top_n: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取特征重要性"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    # 验证实验存在
    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # 查询特征重要性
    result = await db.execute(
        select(FeatureImportance)
        .where(FeatureImportance.experiment_id == exp_uuid)
        .order_by(FeatureImportance.importance.desc())
        .limit(top_n)
    )
    features = result.scalars().all()

    # 计算总重要性
    total_importance = sum(f.importance for f in features)

    return {
        "experiment_id": experiment_id,
        "total_features": len(features),
        "total_importance": total_importance,
        "features": [
            {
                "feature_name": f.feature_name,
                "importance": f.importance,
                "importance_pct": f.importance / total_importance * 100 if total_importance > 0 else 0,
                "rank": f.rank
            }
            for f in features
        ]
    }


@router.get("/{experiment_id}/metrics-history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取指标历史曲线数据"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    # 验证实验存在
    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # 查询所有指标
    result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration.asc())
    )
    metrics = result.scalars().all()

    return {
        "experiment_id": experiment_id,
        "iterations": [m.iteration for m in metrics],
        "train_loss": [m.train_loss for m in metrics],
        "val_loss": [m.val_loss for m in metrics],
        "train_metric": [m.train_metric for m in metrics],
        "val_metric": [m.val_metric for m in metrics],
    }


@router.post("/compare", response_model=CompareExperimentsResponse)
async def compare_experiments(
    experiment_ids: List[str],
    db: AsyncSession = Depends(get_db)
):
    """对比多个实验结果"""
    if len(experiment_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 experiments required for comparison")

    if len(experiment_ids) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 experiments can be compared at once")

    results = []
    for exp_id in experiment_ids:
        try:
            exp_uuid = uuid.UUID(exp_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid experiment ID: {exp_id}")

        result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise HTTPException(status_code=404, detail=f"Experiment not found: {exp_id}")

        # 获取最终指标
        metric_result = await db.execute(
            select(TrainingMetric)
            .where(TrainingMetric.experiment_id == exp_uuid)
            .order_by(TrainingMetric.iteration.desc())
            .limit(1)
        )
        latest_metric = metric_result.scalar_one_or_none()

        results.append({
            "experiment_id": exp_id,
            "name": experiment.name,
            "status": experiment.status,
            "config": experiment.config,
            "metrics": {
                "train_rmse": latest_metric.train_loss if latest_metric else None,
                "val_rmse": latest_metric.val_loss if latest_metric else None,
            }
        })

    # 找出最佳指标
    best_val_rmse = min(
        (r["metrics"]["val_rmse"] for r in results if r["metrics"]["val_rmse"] is not None),
        default=None
    )

    return {
        "experiments": results,
        "best_val_rmse": best_val_rmse,
        "comparison": {
            "best_experiment": next(
                (r["experiment_id"] for r in results if r["metrics"]["val_rmse"] == best_val_rmse),
                None
            ) if best_val_rmse else None
        }
    }


@router.get("/{experiment_id}/download-model")
async def download_model(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    下载模型文件

    通过存储适配层读取模型，支持 local 和 minio 两种存储模式。

    主路径：通过 storage adapter 读取（适用于新数据，有 object_key）
    历史兼容路径：通过 file_path 读取（仅用于历史数据，无 object_key）

    注意：历史兼容路径仅对 object_key 为空的模型记录生效。
    新模型（有 object_key）如果存储失败，不会自动 fallback 到 file_path。
    """
    from app.services.storage import get_storage_service
    from fastapi.responses import StreamingResponse
    import io

    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(
        select(Model).where(Model.experiment_id == exp_uuid).limit(1)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # 判断是否为历史数据：object_key 为空或不存在
    is_legacy_model = not model.object_key

    # 历史数据兼容路径：直接使用 file_path
    if is_legacy_model:
        if model.file_path and os.path.exists(model.file_path):
            return FileResponse(
                path=model.file_path,
                filename=f"model_{experiment_id}.{model.format}",
                media_type="application/json" if model.format == "json" else "application/octet-stream"
            )
        raise HTTPException(status_code=404, detail="Legacy model file not found at file_path")

    # 新模型主路径：通过存储适配层读取
    try:
        storage = get_storage_service()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Storage service not initialized: {str(e)}")

    try:
        model_data = await storage.get_model(experiment_id, model.format)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model file not found in storage")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read model from storage: {str(e)}")

    # 确定媒体类型
    media_type = "application/json" if model.format == "json" else "application/octet-stream"

    # 返回文件流
    return StreamingResponse(
        io.BytesIO(model_data),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="model_{experiment_id}.{model.format}"'
        }
    )


@router.get("/{experiment_id}/export-report", response_model=ExperimentReportResponse)
async def export_report(
    experiment_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """
    导出实验报告

    支持 JSON 和 CSV 格式：
    - JSON: 返回结构化的实验报告（response_model=ExperimentReportResponse）
    - CSV: 返回指标历史的 CSV 文件下载
    """
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # 获取指标历史
    metrics_result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration.asc())
    )
    metrics = metrics_result.scalars().all()

    # 获取特征重要性
    fi_result = await db.execute(
        select(FeatureImportance)
        .where(FeatureImportance.experiment_id == exp_uuid)
        .order_by(FeatureImportance.rank.asc())
    )
    feature_importance = fi_result.scalars().all()

    # 获取模型信息
    model_result = await db.execute(
        select(Model).where(Model.experiment_id == exp_uuid).limit(1)
    )
    model = model_result.scalar_one_or_none()

    report = {
        "experiment": {
            "id": experiment_id,
            "name": experiment.name,
            "description": experiment.description,
            "status": experiment.status,
            "config": experiment.config,
            "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
            "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
            "finished_at": experiment.finished_at.isoformat() if experiment.finished_at else None,
        },
        "final_metrics": model.metrics if model else None,
        "metrics_history": [
            {
                "iteration": m.iteration,
                "train_loss": m.train_loss,
                "val_loss": m.val_loss,
            }
            for m in metrics
        ],
        "feature_importance": [
            {
                "feature_name": fi.feature_name,
                "importance": fi.importance,
                "rank": fi.rank,
            }
            for fi in feature_importance
        ],
        "model_info": {
            "format": model.format if model else None,
            "file_size": model.file_size if model else None,
            "file_path": model.file_path if model else None,
        } if model else None
    }

    if format == "csv":
        import pandas as pd
        import tempfile

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # 导出指标历史
            pd.DataFrame([
                {
                    "iteration": m.iteration,
                    "train_loss": m.train_loss,
                    "val_loss": m.val_loss,
                }
                for m in metrics
            ]).to_csv(f, index=False)
            temp_path = f.name

        return FileResponse(
            path=temp_path,
            filename=f"report_{experiment_id}.csv",
            media_type="text/csv"
        )

    return report


@router.get("/{experiment_id}/prediction-analysis", response_model=PredictionAnalysisResponse)
async def get_prediction_analysis(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取预测分析数据
    
    返回预测值、实际值、残差数据，用于生成预测 vs 实际散点图、残差分布图等。
    
    残差定义: residual = actual - predicted
    - 正值表示预测偏低（实际值大于预测值）
    - 负值表示预测偏高（实际值小于预测值）
    
    若训练产物缺少逐样本预测数据，返回 analysis_unavailable_reason 说明原因。
    """
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status != "completed":
        return PredictionAnalysisResponse(
            experiment_id=experiment_id,
            analysis_available=False,
            analysis_unavailable_reason=f"实验状态为 {experiment.status}，尚未完成训练"
        )

    try:
        storage = get_storage_service()
    except RuntimeError:
        return PredictionAnalysisResponse(
            experiment_id=experiment_id,
            analysis_available=False,
            analysis_unavailable_reason="存储服务未初始化"
        )

    try:
        prediction_data_bytes = await storage.get_prediction_data(experiment_id)
        prediction_data = json.loads(prediction_data_bytes.decode('utf-8'))
    except FileNotFoundError:
        return PredictionAnalysisResponse(
            experiment_id=experiment_id,
            analysis_available=False,
            analysis_unavailable_reason="当前实验缺少逐样本预测工件。此功能需要重新训练实验以生成预测数据。"
        )
    except Exception as e:
        return PredictionAnalysisResponse(
            experiment_id=experiment_id,
            analysis_available=False,
            analysis_unavailable_reason=f"读取预测数据失败: {str(e)}"
        )

    validation_data = prediction_data.get("validation", {})
    actual_values = validation_data.get("actual_values", [])
    predicted_values = validation_data.get("predicted_values", [])
    residual_values = validation_data.get("residual_values", [])

    if not actual_values or not predicted_values:
        return PredictionAnalysisResponse(
            experiment_id=experiment_id,
            analysis_available=False,
            analysis_unavailable_reason="预测数据为空"
        )

    actual_arr = np.array(actual_values)
    predicted_arr = np.array(predicted_values)
    residual_arr = np.array(residual_values)

    if len(residual_arr) == 0:
        residual_arr = actual_arr - predicted_arr

    residual_summary = ResidualSummary(
        mean=float(np.mean(residual_arr)),
        std=float(np.std(residual_arr)),
        min=float(np.min(residual_arr)),
        max=float(np.max(residual_arr)),
        p50=float(np.percentile(residual_arr, 50)),
        p95=float(np.percentile(residual_arr, 95))
    )

    prediction_scatter_points = [
        PredictionScatterPoint(actual=float(a), predicted=float(p))
        for a, p in zip(actual_values, predicted_values)
    ]

    n_bins = 20
    hist, bin_edges = np.histogram(residual_arr, bins=n_bins)
    residual_histogram_bins = [
        ResidualHistogramBin(
            bin_start=float(bin_edges[i]),
            bin_end=float(bin_edges[i + 1]),
            count=int(hist[i])
        )
        for i in range(len(hist))
    ]

    residual_scatter_points = [
        ResidualScatterPoint(predicted=float(p), residual=float(r))
        for p, r in zip(predicted_values, residual_arr.tolist())
    ]

    analysis_data = PredictionAnalysisData(
        sample_count=len(actual_values),
        actual_values=actual_values,
        predicted_values=predicted_values,
        residual_values=residual_arr.tolist(),
        residual_summary=residual_summary,
        prediction_scatter_points=prediction_scatter_points,
        residual_histogram_bins=residual_histogram_bins,
        residual_scatter_points=residual_scatter_points
    )

    return PredictionAnalysisResponse(
        experiment_id=experiment_id,
        analysis_available=True,
        data=analysis_data
    )