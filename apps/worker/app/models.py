"""
Worker 独立的数据模型

与 API 共享数据库表结构，但完全独立定义
"""
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class ExperimentStatus(str, enum.Enum):
    """实验状态枚举"""
    pending = "pending"
    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class FileRole(str, enum.Enum):
    """文件角色"""
    primary = "primary"
    supplementary = "supplementary"
    metadata = "metadata"


class Dataset(Base):
    """数据集"""
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    time_column = Column(String(100), nullable=True)
    entity_column = Column(String(100), nullable=True)
    target_column = Column(String(100), nullable=True)
    total_row_count = Column(Integer, default=0)
    total_column_count = Column(Integer, default=0)
    total_file_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("DatasetFile", back_populates="dataset")
    experiments = relationship("Experiment", back_populates="dataset")
    subsets = relationship("DatasetSubset", back_populates="parent_dataset")


class DatasetFile(Base):
    """数据集文件"""
    __tablename__ = "dataset_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, default=0)
    role = Column(String(50), default=FileRole.primary.value)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    columns_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="files")


class DatasetSubset(Base):
    """数据集子集"""
    __tablename__ = "dataset_subsets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    row_count = Column(Integer, nullable=True)
    split_config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent_dataset = relationship("Dataset", back_populates="subsets")


class Experiment(Base):
    """实验记录"""
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    subset_id = Column(UUID(as_uuid=True), ForeignKey("dataset_subsets.id"), nullable=True)
    config = Column(JSON, nullable=False)
    status = Column(String(50), default=ExperimentStatus.pending.value)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    dataset = relationship("Dataset", back_populates="experiments")
    metrics = relationship("TrainingMetric", back_populates="experiment", cascade="all, delete-orphan")
    logs = relationship("TrainingLog", back_populates="experiment", cascade="all, delete-orphan")
    model = relationship("Model", back_populates="experiment", uselist=False)
    feature_importance = relationship("FeatureImportance", back_populates="experiment", cascade="all, delete-orphan")
    versions = relationship("ModelVersion", back_populates="experiment", cascade="all, delete-orphan")


class TrainingMetric(Base):
    """训练指标记录"""
    __tablename__ = "training_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    iteration = Column(Integer, nullable=False)
    train_loss = Column(Float, nullable=True)
    val_loss = Column(Float, nullable=True)
    train_metric = Column(Float, nullable=True)
    val_metric = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="metrics")


class TrainingLog(Base):
    """训练日志"""
    __tablename__ = "training_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="logs")


class Model(Base):
    """训练模型"""
    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True)

    # 存储信息
    storage_type = Column(String(20), default="local")  # local, minio
    object_key = Column(String(500), nullable=True)  # 存储对象键/相对路径，nullable=True 用于历史数据兼容
    format = Column(String(20), nullable=False)  # json, ubj
    file_size = Column(Integer, nullable=True)

    # 兼容旧字段（可选）
    file_path = Column(String(500), nullable=True)  # 已弃用，保留用于迁移

    # 模型评估指标
    metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="model")


class FeatureImportance(Base):
    """特征重要性"""
    __tablename__ = "feature_importance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    feature_name = Column(String(255), nullable=False)
    importance = Column(Float, nullable=False)
    rank = Column(Integer, nullable=True)

    experiment = relationship("Experiment", back_populates="feature_importance")


class AsyncTask(Base):
    """异步任务记录（预处理/特征工程等）"""
    __tablename__ = "async_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String(50), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="queued")
    error_message = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    dataset = relationship("Dataset")


class ModelVersion(Base):
    """模型版本管理 - P1-T13"""
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    
    version_number = Column(String(20), nullable=False)
    
    config_snapshot = Column(JSON, nullable=False)
    metrics_snapshot = Column(JSON, nullable=False)
    
    tags = Column(JSON, nullable=True, default=list)
    
    is_active = Column(Integer, default=1)
    
    source_model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="versions")
    source_model = relationship("Model")