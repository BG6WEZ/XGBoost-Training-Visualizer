"""
导出功能 Schema

P1-T14: 配置/报告导出
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConfigExportResponse(BaseModel):
    """配置导出响应"""
    experiment_id: str
    experiment_name: str
    exported_at: datetime
    config_format: str = Field(..., description="导出格式: json 或 yaml")
    config: Dict[str, Any]
    
    class Config:
        from_attributes = True


class ReportExportRequest(BaseModel):
    """报告导出请求"""
    format: str = Field(default="html", description="导出格式: html 或 pdf")
    include_metrics_history: bool = Field(default=True, description="是否包含指标历史")
    include_feature_importance: bool = Field(default=True, description="是否包含特征重要性")


class ReportExportMetadata(BaseModel):
    """报告导出元数据"""
    experiment_id: str
    experiment_name: str
    exported_at: datetime
    format: str
    file_size: int
