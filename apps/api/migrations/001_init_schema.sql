-- ============================================================================
-- XGBoost Training Visualizer - 数据库初始化脚本
-- 版本: 1.0
-- 适用场景: 新库初始化
-- 执行方式: psql -f 001_init_schema.sql
-- ============================================================================

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 数据集表
-- ============================================================================
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- 数据集级别的列配置
    time_column VARCHAR(100),
    entity_column VARCHAR(100),
    target_column VARCHAR(100),

    -- 聚合统计（由文件成员汇总）
    total_row_count INTEGER DEFAULT 0,
    total_column_count INTEGER DEFAULT 0,
    total_file_size BIGINT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 数据集文件表（多文件支持）
-- ============================================================================
CREATE TABLE IF NOT EXISTS dataset_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    -- 文件信息
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT DEFAULT 0,

    -- 文件角色: primary, supplementary, metadata
    role VARCHAR(50) DEFAULT 'primary',

    -- 文件统计
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,

    -- 列信息（JSON 格式）
    columns_info JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dataset_files_dataset_id ON dataset_files(dataset_id);

-- ============================================================================
-- 数据集子集表（训练/测试切分）
-- ============================================================================
CREATE TABLE IF NOT EXISTS dataset_subsets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,  -- train, test, compare, transfer_source, transfer_target

    file_path VARCHAR(500) NOT NULL,
    row_count INTEGER,

    -- 切分配置（JSON 格式）
    split_config JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dataset_subsets_parent_id ON dataset_subsets(parent_dataset_id);

-- ============================================================================
-- 实验表
-- ============================================================================
CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,

    dataset_id UUID NOT NULL REFERENCES datasets(id),
    subset_id UUID REFERENCES dataset_subsets(id),

    -- 训练配置（JSON 格式）
    config JSONB NOT NULL,

    -- 状态: pending, queued, running, paused, completed, failed, cancelled
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_experiments_dataset_id ON experiments(dataset_id);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);

-- ============================================================================
-- 训练指标表
-- ============================================================================
CREATE TABLE IF NOT EXISTS training_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,

    iteration INTEGER NOT NULL,
    train_loss FLOAT,
    val_loss FLOAT,
    train_metric FLOAT,
    val_metric FLOAT,

    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_training_metrics_experiment_id ON training_metrics(experiment_id);

-- ============================================================================
-- 训练日志表
-- ============================================================================
CREATE TABLE IF NOT EXISTS training_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,

    level VARCHAR(20) DEFAULT 'INFO',
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_training_logs_experiment_id ON training_logs(experiment_id);

-- ============================================================================
-- 模型表
-- ============================================================================
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE UNIQUE,

    -- 存储信息
    storage_type VARCHAR(20) DEFAULT 'local',  -- local, minio
    object_key VARCHAR(500),  -- 可为空，用于历史数据兼容
    format VARCHAR(20) NOT NULL,  -- json, ubj
    file_size BIGINT,

    -- 兼容旧字段（已弃用，保留用于迁移）
    file_path VARCHAR(500),

    -- 模型评估指标（JSON 格式）
    metrics JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 特征重要性表
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_importance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,

    feature_name VARCHAR(255) NOT NULL,
    importance FLOAT NOT NULL,
    rank INTEGER
);

CREATE INDEX IF NOT EXISTS idx_feature_importance_experiment_id ON feature_importance(experiment_id);

-- ============================================================================
-- 异步任务表（预处理/特征工程）
-- ============================================================================
CREATE TABLE IF NOT EXISTS async_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type VARCHAR(50) NOT NULL,  -- preprocessing, feature_engineering
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    -- 任务状态: queued, running, completed, failed
    status VARCHAR(20) DEFAULT 'queued',
    error_message TEXT,

    -- 任务配置和结果
    config JSONB,
    result JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_async_tasks_dataset_id ON async_tasks(dataset_id);
CREATE INDEX IF NOT EXISTS idx_async_tasks_status ON async_tasks(status);

-- ============================================================================
-- 更新触发器（自动更新 updated_at）
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_datasets_updated_at BEFORE UPDATE ON datasets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiments_updated_at BEFORE UPDATE ON experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 完成
-- ============================================================================
-- 初始化脚本执行完成
-- 下一步：验证表结构
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';