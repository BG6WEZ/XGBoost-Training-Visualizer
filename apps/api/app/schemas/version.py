"""
模型版本管理 Schema

P1-T13: 模型版本管理
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class ModelVersionCreate(BaseModel):
    """创建模型版本请求"""
    experiment_id: str = Field(..., description="实验ID")
    tags: Optional[List[str]] = Field(default=None, description="版本标签")
    description: Optional[str] = Field(default=None, description="版本描述")


class ModelVersionResponse(BaseModel):
    """模型版本响应"""
    id: str = Field(..., description="版本ID")
    experiment_id: str = Field(..., description="实验ID")
    version_number: str = Field(..., description="版本号，如 v1.0.0")
    config_snapshot: Dict[str, Any] = Field(..., description="配置快照")
    metrics_snapshot: Dict[str, Any] = Field(..., description="指标快照")
    tags: List[str] = Field(default_factory=list, description="版本标签")
    is_active: bool = Field(..., description="是否为当前激活版本")
    source_model_id: Optional[str] = Field(None, description="源模型ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ModelVersionListResponse(BaseModel):
    """模型版本列表响应"""
    id: str
    experiment_id: str
    version_number: str
    metrics_snapshot: Dict[str, Any]
    tags: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VersionCompareRequest(BaseModel):
    """版本比较请求"""
    version_ids: List[str] = Field(..., min_length=2, max_length=3, description="要比较的版本ID列表（2-3个）")


class ConfigDiff(BaseModel):
    """配置差异"""
    param_name: str = Field(..., description="参数名")
    values: Dict[str, Any] = Field(..., description="各版本的参数值")


class MetricsDiff(BaseModel):
    """指标差异"""
    metric_name: str = Field(..., description="指标名")
    values: Dict[str, float] = Field(..., description="各版本的指标值")
    change: Optional[Dict[str, float]] = Field(None, description="相对于第一个版本的变化百分比")


class VersionCompareResponse(BaseModel):
    """版本比较响应"""
    versions: List[ModelVersionResponse] = Field(..., description="参与比较的版本列表")
    config_diffs: List[ConfigDiff] = Field(..., description="配置差异列表")
    metrics_diffs: List[MetricsDiff] = Field(..., description="指标差异列表")


class VersionRollbackResponse(BaseModel):
    """版本回滚响应"""
    success: bool = Field(..., description="回滚是否成功")
    previous_active_version_id: Optional[str] = Field(None, description="之前激活的版本ID")
    new_active_version_id: str = Field(..., description="新激活的版本ID")
    message: str = Field(..., description="回滚结果说明")


class VersionTagUpdate(BaseModel):
    """版本标签更新请求"""
    tags: List[str] = Field(..., description="新的标签列表")
