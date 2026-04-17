"""
结果接口响应 Schema

定义所有 results 相关接口的响应结构
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# ========== 单个实验结果 ==========

class MetricAvailability(BaseModel):
    """指标可用性说明
    
    当某指标不可计算时，说明原因
    """
    available: bool = Field(..., description="指标是否可用")
    reason: Optional[str] = Field(None, description="不可用原因（当 available=False 时必填）")


class BenchmarkMetrics(BaseModel):
    """统一 Benchmark 指标结构
    
    P1-T11: 统一输出指标体系
    所有指标字段命名在 schema、router、前端类型定义中保持一致
    """
    rmse: Optional[float] = Field(None, description="均方根误差 (Root Mean Square Error)")
    mae: Optional[float] = Field(None, description="平均绝对误差 (Mean Absolute Error)")
    mape: Optional[float] = Field(None, description="平均绝对百分比误差 (Mean Absolute Percentage Error)")
    r2: Optional[float] = Field(None, description="决定系数 (R-squared)")
    
    rmse_availability: Optional[MetricAvailability] = Field(None, description="RMSE 可用性说明")
    mae_availability: Optional[MetricAvailability] = Field(None, description="MAE 可用性说明")
    mape_availability: Optional[MetricAvailability] = Field(None, description="MAPE 可用性说明")
    r2_availability: Optional[MetricAvailability] = Field(None, description="R2 可用性说明")


class ExperimentMetrics(BaseModel):
    """实验指标（兼容旧结构）"""
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
    benchmark: Optional[BenchmarkMetrics] = Field(None, description="统一 Benchmark 指标")
    benchmark_mode: str = Field(default="standard", description="Benchmark 模式标识")
    feature_importance: List[FeatureImportanceItem]
    model: Optional[ModelInfo] = None
    training_time_seconds: Optional[float] = None
    best_iteration: Optional[int] = None

    class Config:
        from_attributes = True

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


# ========== 预测分析（P1-T10）==========

class ResidualSummary(BaseModel):
    """残差摘要统计
    
    残差定义: residual = actual - predicted
    正值表示预测偏低，负值表示预测偏高
    """
    mean: float = Field(..., description="残差均值")
    std: float = Field(..., description="残差标准差")
    min: float = Field(..., description="最小残差")
    max: float = Field(..., description="最大残差")
    p50: float = Field(..., description="残差中位数")
    p95: float = Field(..., description="残差95分位数")


class PredictionScatterPoint(BaseModel):
    """预测 vs 实际散点数据点"""
    actual: float = Field(..., description="实际值")
    predicted: float = Field(..., description="预测值")


class ResidualHistogramBin(BaseModel):
    """残差直方图 bin"""
    bin_start: float = Field(..., description="bin 起始值")
    bin_end: float = Field(..., description="bin 结束值")
    count: int = Field(..., description="该 bin 内的样本数")


class ResidualScatterPoint(BaseModel):
    """残差散点数据点（残差 vs 预测值）"""
    predicted: float = Field(..., description="预测值")
    residual: float = Field(..., description="残差 (actual - predicted)")


class PredictionAnalysisData(BaseModel):
    """预测分析数据（当数据可用时返回）"""
    sample_count: int = Field(..., description="样本数量")
    actual_values: List[float] = Field(..., description="实际值列表")
    predicted_values: List[float] = Field(..., description="预测值列表")
    residual_values: List[float] = Field(..., description="残差列表 (actual - predicted)")
    residual_summary: ResidualSummary = Field(..., description="残差摘要统计")
    prediction_scatter_points: List[PredictionScatterPoint] = Field(..., description="预测 vs 实际散点数据")
    residual_histogram_bins: List[ResidualHistogramBin] = Field(..., description="残差直方图 bins")
    residual_scatter_points: List[ResidualScatterPoint] = Field(..., description="残差 vs 预测值散点数据")


class PredictionAnalysisResponse(BaseModel):
    """预测分析响应
    
    残差定义: residual = actual - predicted
    该定义在接口文档、代码实现、页面文案中保持一致
    """
    experiment_id: str
    analysis_available: bool = Field(..., description="分析数据是否可用")
    analysis_unavailable_reason: Optional[str] = Field(
        None, 
        description="分析不可用原因（当 analysis_available=False 时必填）"
    )
    data: Optional[PredictionAnalysisData] = Field(
        None, 
        description="分析数据（当 analysis_available=True 时必填）"
    )
    residual_definition: str = Field(
        default="residual = actual - predicted",
        description="残差定义说明"
    )

    class Config:
        from_attributes = True


# ========== 错误响应 ==========

class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    error_code: Optional[str] = None