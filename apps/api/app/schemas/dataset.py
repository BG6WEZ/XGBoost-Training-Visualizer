from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class FileRoleEnum(str, Enum):
    """文件角色枚举"""
    primary = "primary"
    supplementary = "supplementary"
    metadata = "metadata"


# ========== DatasetFile Schemas ==========

class DatasetFileCreate(BaseModel):
    """数据集文件创建请求"""
    file_path: str
    file_name: str
    role: FileRoleEnum = FileRoleEnum.primary
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    file_size: Optional[int] = None
    columns_info: Optional[List[Dict[str, Any]]] = None


class DatasetFileResponse(BaseModel):
    """数据集文件响应"""
    id: str
    file_path: str
    file_name: str
    role: str
    row_count: int
    column_count: int
    file_size: int
    columns_info: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== Dataset Schemas ==========

class DatasetCreate(BaseModel):
    """数据集创建请求 - 支持多文件"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    files: List[DatasetFileCreate] = Field(..., min_items=1)
    time_column: Optional[str] = None
    entity_column: Optional[str] = None
    target_column: Optional[str] = None


class DatasetUpdate(BaseModel):
    """数据集更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    time_column: Optional[str] = None
    entity_column: Optional[str] = None
    target_column: Optional[str] = None


class DatasetResponse(BaseModel):
    """数据集响应"""
    id: str
    name: str
    description: Optional[str]
    time_column: Optional[str]
    entity_column: Optional[str]
    target_column: Optional[str]
    total_row_count: int
    total_column_count: int
    total_file_size: int
    files: List[DatasetFileResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """数据集列表响应"""
    id: str
    name: str
    description: Optional[str]
    total_row_count: int
    total_column_count: int
    total_file_size: int
    file_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ========== Dataset Preview ==========

class DatasetPreview(BaseModel):
    """数据集预览"""
    file_id: str
    file_name: str
    columns: List[str]
    data: List[Dict[str, Any]]
    total_rows: int
    preview_rows: int


# ========== Dataset Subset Schemas ==========

class DatasetSubsetCreate(BaseModel):
    """数据集子集创建请求"""
    name: str
    purpose: str  # train, test, compare, transfer_source, transfer_target
    row_count: Optional[int] = None
    split_config: Optional[Dict[str, Any]] = None


class DatasetSubsetResponse(BaseModel):
    """数据集子集响应"""
    id: str
    parent_dataset_id: str
    name: str
    purpose: str
    file_path: str
    row_count: int
    split_config: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== Preprocessing Schemas ==========


class MissingValueStrategyEnum(str, Enum):
    """缺失值处理策略枚举"""
    FORWARD_FILL = "forward_fill"
    MEAN_FILL = "mean_fill"
    DROP_ROWS = "drop_rows"


class EncodingStrategyEnum(str, Enum):
    """编码策略枚举"""
    ONE_HOT = "one_hot"
    LABEL_ENCODING = "label_encoding"


class PreprocessingConfig(BaseModel):
    """预处理配置"""
    missing_value_strategy: MissingValueStrategyEnum = MissingValueStrategyEnum.MEAN_FILL
    encoding_strategy: Optional[EncodingStrategyEnum] = None
    remove_duplicates: bool = True
    handle_outliers: bool = False
    output_path: Optional[str] = None
    target_columns: Optional[List[str]] = None  # 目标处理列


class PreprocessingRequest(BaseModel):
    """预处理请求"""
    dataset_id: str
    config: PreprocessingConfig


class PreprocessingResponse(BaseModel):
    """预处理响应"""
    task_id: str
    dataset_id: str
    status: str
    message: str


# ========== Feature Engineering Schemas ==========


class TimeFeatureEnum(str, Enum):
    """时间特征枚举"""
    HOUR = "hour"
    DAYOFWEEK = "dayofweek"
    MONTH = "month"
    IS_WEEKEND = "is_weekend"


class TimeFeatureConfig(BaseModel):
    """时间特征配置"""
    enabled: bool = False
    column: Optional[str] = None
    features: List[TimeFeatureEnum] = [TimeFeatureEnum.HOUR, TimeFeatureEnum.DAYOFWEEK, TimeFeatureEnum.MONTH, TimeFeatureEnum.IS_WEEKEND]
    
    @model_validator(mode='after')
    def validate_time_features(self):
        if self.enabled:
            if not self.column:
                raise ValueError("time_features.column is required when time_features.enabled is True")
            if not self.features:
                raise ValueError("time_features.features cannot be empty when time_features.enabled is True")
        return self


class LagFeatureConfig(BaseModel):
    """滞后特征配置"""
    enabled: bool = False
    columns: List[str] = []
    lags: List[int] = [1, 6, 12, 24]
    
    @field_validator('lags')
    @classmethod
    def validate_lags(cls, v):
        for lag in v:
            if not isinstance(lag, int) or lag <= 0:
                raise ValueError(f"lag value must be a positive integer, got {lag}")
        return v
    
    @model_validator(mode='after')
    def validate_lag_features(self):
        if self.enabled:
            if not self.columns:
                raise ValueError("lag_features.columns cannot be empty when lag_features.enabled is True")
            if not self.lags:
                raise ValueError("lag_features.lags cannot be empty when lag_features.enabled is True")
        return self


class RollingFeatureConfig(BaseModel):
    """滚动特征配置"""
    enabled: bool = False
    columns: List[str] = []
    windows: List[int] = [3, 6, 24]
    
    @field_validator('windows')
    @classmethod
    def validate_windows(cls, v):
        for window in v:
            if not isinstance(window, int) or window <= 0:
                raise ValueError(f"window value must be a positive integer, got {window}")
        return v
    
    @model_validator(mode='after')
    def validate_rolling_features(self):
        if self.enabled:
            if not self.columns:
                raise ValueError("rolling_features.columns cannot be empty when rolling_features.enabled is True")
            if not self.windows:
                raise ValueError("rolling_features.windows cannot be empty when rolling_features.enabled is True")
        return self


class FeatureEngineeringConfig(BaseModel):
    """特征工程配置"""
    time_features: TimeFeatureConfig = TimeFeatureConfig()
    lag_features: LagFeatureConfig = LagFeatureConfig()
    rolling_features: RollingFeatureConfig = RollingFeatureConfig()
    output_path: Optional[str] = None


class FeatureEngineeringRequest(BaseModel):
    """特征工程请求"""
    dataset_id: str
    config: FeatureEngineeringConfig


class FeatureEngineeringResponse(BaseModel):
    """特征工程响应"""
    task_id: str
    dataset_id: str
    status: str
    message: str


# ========== Async Task Schemas ==========

class AsyncTaskStatus(BaseModel):
    """异步任务状态"""
    id: str
    task_type: str
    dataset_id: str
    status: str
    error_message: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AsyncTaskListResponse(BaseModel):
    """异步任务列表响应"""
    id: str
    task_type: str
    dataset_id: str
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SplitRequest(BaseModel):
    """数据切分请求"""
    split_method: str = "random"
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    random_seed: int = 42
    time_column: Optional[str] = None
    train_end_date: Optional[str] = None
    val_start_date: Optional[str] = None
    val_end_date: Optional[str] = None
    test_start_date: Optional[str] = None


class SplitSubsetResponse(BaseModel):
    """切分子集响应"""
    id: str
    name: str
    purpose: str
    row_count: int
    file_path: str


class SplitResponse(BaseModel):
    """数据切分响应"""
    dataset_id: str
    split_method: str
    subsets: List[SplitSubsetResponse]
    split_config: Dict[str, Any]

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """文件上传响应"""
    file_path: str
    file_name: str
    file_size: int
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns_info: Optional[List[Dict[str, Any]]] = None
    message: str = "File uploaded successfully"
    estimated: Optional[bool] = Field(default=None, description="是否为估算行数（大文件采样估算）")


class QualityDimensionScores(BaseModel):
    """质量评分四维得分"""
    completeness: float
    accuracy: float
    consistency: float
    distribution: float


class QualityScoreResponse(BaseModel):
    """数据质量评分响应"""
    dataset_id: str
    overall_score: float
    dimension_scores: QualityDimensionScores
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    recommendations: List[str]
    stats: Dict[str, Any]
    evaluated_at: str
    weights: Dict[str, float]


# ========== Data Join Schemas ==========


class JoinTypeEnum(str, Enum):
    """Join类型枚举"""
    LEFT = "left"
    INNER = "inner"
    RIGHT = "right"
    OUTER = "outer"


class JoinTable(BaseModel):
    """从表Join配置"""
    name: str = Field(..., min_length=1, max_length=255, description="从表名称")
    file_path: str = Field(..., description="从表文件路径")
    join_key: str = Field(..., min_length=1, description="从表Join键")
    join_type: JoinTypeEnum = Field(default=JoinTypeEnum.LEFT, description="Join类型")


class JoinRequest(BaseModel):
    """Join请求"""
    main_join_key: str = Field(..., min_length=1, description="主表Join键")
    join_tables: List[JoinTable] = Field(..., min_length=1, description="从表配置列表")


class JoinResult(BaseModel):
    """Join结果响应"""
    success: bool
    before_rows: int = Field(description="Join前主表行数")
    after_rows: int = Field(description="Join后行数")
    rows_lost: int = Field(description="丢失的行数（inner join时）")
    rows_added_columns: int = Field(description="新增的列数")
    message: str
    joined_columns: List[str] = Field(default_factory=list, description="Join后所有列名")
    output_file_path: Optional[str] = Field(default=None, description="输出文件路径")