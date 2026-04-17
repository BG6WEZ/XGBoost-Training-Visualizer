from sqlalchemy import Column, String, Text, Integer, BigInteger, Float, DateTime, ForeignKey, JSON, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """用户角色"""
    admin = "admin"
    user = "user"


class UserStatus(str, enum.Enum):
    """用户状态"""
    active = "active"
    disabled = "disabled"


class ExperimentStatus(str, enum.Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class FileRole(str, enum.Enum):
    """文件角色"""
    primary = "primary"  # 主数据文件
    supplementary = "supplementary"  # 补充数据文件
    metadata = "metadata"  # 元数据文件


class Dataset(Base):
    """
    逻辑数据集 - 支持多文件组合
    一个数据集可以包含多个 CSV 文件，通过 DatasetFile 关联
    """
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # 数据集级别的列配置
    time_column = Column(String(100), nullable=True)
    entity_column = Column(String(100), nullable=True)
    target_column = Column(String(100), nullable=True)

    # 聚合统计（由文件成员汇总）
    total_row_count = Column(Integer, default=0)
    total_column_count = Column(Integer, default=0)
    total_file_size = Column(BigInteger, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship("DatasetFile", back_populates="dataset", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="dataset")
    subsets = relationship("DatasetSubset", back_populates="parent_dataset")


class DatasetFile(Base):
    """
    数据集文件成员 - 代表数据集中的一个具体文件
    """
    __tablename__ = "dataset_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)

    # 文件信息
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, default=0)

    # 文件角色
    role = Column(String(50), default=FileRole.primary.value)

    # 文件统计
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)

    # 列信息（存储该文件的列结构）
    columns_info = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="files")


class DatasetSubset(Base):
    """数据集子集 - 用于训练/测试切分"""
    __tablename__ = "dataset_subsets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False)  # train, test, compare, transfer_source, transfer_target

    # 子集文件路径
    file_path = Column(String(500), nullable=False)
    row_count = Column(Integer, nullable=True)

    # 切分配置
    split_config = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent_dataset = relationship("Dataset", back_populates="subsets")


class Experiment(Base):
    """实验记录"""
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # 关联数据集（必须）
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)

    # 可选：关联子集
    subset_id = Column(UUID(as_uuid=True), ForeignKey("dataset_subsets.id"), nullable=True)

    # 训练配置
    config = Column(JSON, nullable=False)

    # 标签（P1-T12）
    tags = Column(JSON, nullable=True, default=list)

    # 状态
    status = Column(String(50), default=ExperimentStatus.pending.value)
    error_message = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Relationships
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

    # Relationships
    experiment = relationship("Experiment", back_populates="metrics")


class TrainingLog(Base):
    """训练日志"""
    __tablename__ = "training_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)

    level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
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
    file_size = Column(BigInteger, nullable=True)

    # 兼容旧字段（可选）
    file_path = Column(String(500), nullable=True)  # 已弃用，保留用于迁移

    # 模型评估指标
    metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    experiment = relationship("Experiment", back_populates="model")
    versions = relationship("ModelVersion", back_populates="source_model")


class FeatureImportance(Base):
    """特征重要性"""
    __tablename__ = "feature_importance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)

    feature_name = Column(String(255), nullable=False)
    importance = Column(Float, nullable=False)
    rank = Column(Integer, nullable=True)

    # Relationships
    experiment = relationship("Experiment", back_populates="feature_importance")


class ModelVersion(Base):
    """模型版本管理 - P1-T13
    
    训练完成后自动创建版本快照，支持版本追踪、比较和回滚
    """
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    
    # 版本号（v1.0.0 风格）
    version_number = Column(String(20), nullable=False)
    
    # 配置快照（训练时的完整配置）
    config_snapshot = Column(JSON, nullable=False)
    
    # 指标快照（训练结果的核心指标）
    metrics_snapshot = Column(JSON, nullable=False)
    
    # 版本标签（如 "生产环境"、"最佳模型"）
    tags = Column(JSON, nullable=True, default=list)
    
    # 是否为当前激活版本（每个实验只能有一个激活版本）
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive
    
    # 模型存储引用（指向 Model 表的 object_key）
    source_model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    experiment = relationship("Experiment", back_populates="versions")
    source_model = relationship("Model", back_populates="versions")
    
    __table_args__ = (
        UniqueConstraint("experiment_id", "version_number", name="uq_experiment_version"),
    )


class AsyncTask(Base):
    """异步任务记录（预处理/特征工程等）"""
    __tablename__ = "async_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String(50), nullable=False)  # preprocessing, feature_engineering
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)

    # 任务状态
    status = Column(String(20), default="queued")  # queued, running, completed, failed
    error_message = Column(Text, nullable=True)

    # 任务配置
    config = Column(JSON, nullable=True)

    # 任务结果
    result = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Relationships
    dataset = relationship("Dataset")


class User(Base):
    """用户模型 - P1-T15 简化登录与用户管理"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.user.value)
    status = Column(String(20), default=UserStatus.active.value)
    must_change_password = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("username", name="uq_user_username"),
    )
