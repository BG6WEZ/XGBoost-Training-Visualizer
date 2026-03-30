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


class ExperimentUpdate(BaseModel):
    """实验更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[TrainingConfig] = None


class ExperimentResponse(BaseModel):
    """实验响应"""
    id: str
    name: str
    description: Optional[str]
    dataset_id: str
    subset_id: Optional[str]
    config: Dict[str, Any]
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
    status: str
    created_at: datetime

    class Config:
        from_attributes = True