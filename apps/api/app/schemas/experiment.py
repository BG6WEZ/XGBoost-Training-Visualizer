from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ExperimentStatus(str, Enum):
    """实验状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class XGBoostParams(BaseModel):
    """XGBoost 参数"""
    learning_rate: float = Field(default=0.1, ge=0.001, le=1.0)
    max_depth: int = Field(default=6, ge=1, le=15)
    n_estimators: int = Field(default=100, ge=10, le=10000)
    subsample: float = Field(default=1.0, ge=0.1, le=1.0)
    colsample_bytree: float = Field(default=1.0, ge=0.1, le=1.0)
    gamma: float = Field(default=0, ge=0)
    alpha: float = Field(default=0, ge=0)
    # 使用 lambda_ 作为属性名，但序列化为 lambda（XGBoost 原生参数名）
    lambda_: float = Field(default=1, ge=0, serialization_alias="lambda", validation_alias="lambda")
    min_child_weight: float = Field(default=1, ge=0)

    class Config:
        populate_by_name = True

    def model_dump(self, **kwargs):
        """重写序列化方法，确保 lambda_ 被序列化为 lambda"""
        data = super().model_dump(**kwargs)
        if "lambda_" in data:
            data["lambda"] = data.pop("lambda_")
        return data


class TrainingConfig(BaseModel):
    """训练配置"""
    task_type: str = "regression"
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    random_seed: int = Field(default=42, ge=0)
    xgboost_params: XGBoostParams = XGBoostParams()
    early_stopping_rounds: Optional[int] = Field(default=10, ge=1)

    def model_dump(self, **kwargs):
        """确保嵌套对象正确序列化"""
        data = super().model_dump(**kwargs)
        if "xgboost_params" in data and isinstance(data["xgboost_params"], dict):
            params = data["xgboost_params"]
            if "lambda_" in params:
                params["lambda"] = params.pop("lambda_")
        return data


class ExperimentCreate(BaseModel):
    """实验创建请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_id: str
    subset_id: Optional[str] = None
    config: TrainingConfig
    tags: Optional[List[str]] = Field(default=None, description="实验标签列表")


class ExperimentUpdate(BaseModel):
    """实验更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[TrainingConfig] = None
    tags: Optional[List[str]] = Field(None, description="实验标签列表")


class ExperimentResponse(BaseModel):
    """实验响应"""
    id: str
    name: str
    description: Optional[str]
    dataset_id: str
    subset_id: Optional[str]
    config: Dict[str, Any]
    tags: Optional[List[str]] = Field(default=None, description="实验标签列表")
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExperimentListResponse(BaseModel):
    """实验列表响应"""
    id: str
    name: str
    description: Optional[str]
    dataset_id: str
    tags: Optional[List[str]] = Field(default=None, description="实验标签列表")
    status: str
    created_at: datetime
    queue_position: Optional[int] = None

    class Config:
        from_attributes = True


class ExperimentFilterParams(BaseModel):
    """实验筛选参数"""
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    tag_match_mode: str = Field(default="any", description="标签匹配模式: any 或 all")
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    name_contains: Optional[str] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class QueueStatsResponse(BaseModel):
    """队列统计响应"""
    running_count: int
    queued_count: int
    max_concurrency: int
    available_slots: int
    running_experiments: List[str] = []
    queue_positions: Dict[str, int] = {}


class ExperimentWithQueueResponse(BaseModel):
    """带队列信息的实验响应"""
    id: str
    name: str
    description: Optional[str]
    dataset_id: str
    subset_id: Optional[str]
    config: Dict[str, Any]
    tags: Optional[List[str]] = Field(default=None, description="实验标签列表")
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    queue_position: Optional[int] = None

    class Config:
        from_attributes = True


class ParamTemplateItem(BaseModel):
    """单个参数模板"""
    learning_rate: float
    max_depth: int
    n_estimators: int
    subsample: float
    colsample_bytree: float
    early_stopping_rounds: int
    description: str


class ParamTemplatesResponse(BaseModel):
    """参数模板响应"""
    templates: Dict[str, ParamTemplateItem]


PARAM_TEMPLATES: Dict[str, ParamTemplateItem] = {
    "conservative": ParamTemplateItem(
        learning_rate=0.01,
        max_depth=3,
        n_estimators=500,
        subsample=0.8,
        colsample_bytree=0.8,
        early_stopping_rounds=20,
        description="适合小数据、防过拟合"
    ),
    "balanced": ParamTemplateItem(
        learning_rate=0.1,
        max_depth=6,
        n_estimators=100,
        subsample=1.0,
        colsample_bytree=1.0,
        early_stopping_rounds=10,
        description="通用默认值"
    ),
    "aggressive": ParamTemplateItem(
        learning_rate=0.3,
        max_depth=9,
        n_estimators=50,
        subsample=1.0,
        colsample_bytree=1.0,
        early_stopping_rounds=5,
        description="快速探索"
    )
}