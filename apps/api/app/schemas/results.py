"""
结果接口响应 Schema

定义所有 results 相关接口的响应结构
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# ========== 单个实验结果 ==========

class ExperimentMetrics(BaseModel):
    """实验指标"""
    train_rmse: Optional[float] = None
    val_rmse: Optional[float] = None
    r2: Optional[float] = None
    mae: Optional[float] = None


class FeatureImportanceItem(BaseModel):
    """特征重要性项"""
    feature_name: str
    importance: float
    rank: int


class ModelInfo(BaseModel):
    """模型信息"""
    id: Optional[str] = None
    format: Optional[str] = None
    file_size: Optional[int] = None
    storage_type: Optional[str] = None
    object_key: Optional[str] = None


class ExperimentResultResponse(BaseModel):
    """实验结果响应"""
    experiment_id: str
    experiment_name: str
    status: str
    metrics: ExperimentMetrics
    feature_importance: List[FeatureImportanceItem]
    model: Optional[ModelInfo] = None
    training_time_seconds: Optional[float] = None

    class Config:
        from_attributes = True


# ========== 特征重要性 ==========

class FeatureImportanceDetail(BaseModel):
    """特征重要性详情"""
    feature_name: str
    importance: float
    importance_pct: float
    rank: int


class FeatureImportanceResponse(BaseModel):
    """特征重要性响应"""
    experiment_id: str
    total_features: int
    total_importance: float
    features: List[FeatureImportanceDetail]


# ========== 指标历史 ==========

class MetricsHistoryResponse(BaseModel):
    """指标历史响应"""
    experiment_id: str
    iterations: List[int]
    train_loss: List[Optional[float]]
    val_loss: List[Optional[float]]
    train_metric: List[Optional[float]]
    val_metric: List[Optional[float]]


# ========== 实验对比 ==========

class ExperimentComparisonItem(BaseModel):
    """实验对比项"""
    experiment_id: str
    name: str
    status: str
    config: Optional[Dict[str, Any]] = None
    metrics: ExperimentMetrics


class CompareExperimentsResponse(BaseModel):
    """实验对比响应"""
    experiments: List[ExperimentComparisonItem]
    best_val_rmse: Optional[float] = None
    comparison: Dict[str, Any] = Field(default_factory=dict)


# ========== 模型下载 ==========

class ModelDownloadInfo(BaseModel):
    """模型下载信息"""
    experiment_id: str
    model_id: str
    format: str
    file_size: int
    storage_type: str
    download_url: Optional[str] = None


# ========== 报告导出 ==========

class ExperimentReportExperiment(BaseModel):
    """报告中的实验信息"""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class ReportMetricItem(BaseModel):
    """报告中的指标项"""
    iteration: int
    train_loss: Optional[float] = None
    val_loss: Optional[float] = None


class ReportFeatureImportance(BaseModel):
    """报告中的特征重要性"""
    feature_name: str
    importance: float
    rank: int


class ReportModelInfo(BaseModel):
    """报告中的模型信息"""
    format: Optional[str] = None
    file_size: Optional[int] = None
    file_path: Optional[str] = None


class ExperimentReportResponse(BaseModel):
    """实验报告响应（JSON 格式）"""
    experiment: ExperimentReportExperiment
    final_metrics: Optional[Dict[str, Any]] = None
    metrics_history: List[ReportMetricItem]
    feature_importance: List[ReportFeatureImportance]
    model_info: Optional[ReportModelInfo] = None

    class Config:
        from_attributes = True


# ========== 错误响应 ==========

class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    error_code: Optional[str] = None