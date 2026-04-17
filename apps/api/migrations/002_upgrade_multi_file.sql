-- ============================================================================
-- XGBoost Training Visualizer - 数据库升级脚本
-- 版本: 1.0
-- 适用场景: 旧库升级（从单文件数据集升级到多文件数据集）
-- 执行方式: psql -f 002_upgrade_multi_file.sql
-- 注意: 执行前请备份数据库
-- ============================================================================

-- 开始事务
BEGIN;

-- ============================================================================
-- 1. 数据集表：新增字段
-- ============================================================================
-- 检查并添加新字段（幂等操作）
DO $$
BEGIN
    -- time_column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'datasets' AND column_name = 'time_column') THEN
        ALTER TABLE datasets ADD COLUMN time_column VARCHAR(100);
    END IF;

    -- entity_column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'datasets' AND column_name = 'entity_column') THEN
        ALTER TABLE datasets ADD COLUMN entity_column VARCHAR(100);
    END IF;

    -- target_column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'datasets' AND column_name = 'target_column') THEN
        ALTER TABLE datasets ADD COLUMN target_column VARCHAR(100);
    END IF;

    -- total_row_count
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'datasets' AND column_name = 'total_row_count') THEN
        ALTER TABLE datasets ADD COLUMN total_row_count INTEGER DEFAULT 0;
    END IF;

    -- total_column_count
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'datasets' AND column_name = 'total_column_count') THEN
        ALTER TABLE datasets ADD COLUMN total_column_count INTEGER DEFAULT 0;
    END IF;

    -- total_file_size
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'datasets' AND column_name = 'total_file_size') THEN
        ALTER TABLE datasets ADD COLUMN total_file_size BIGINT DEFAULT 0;
    END IF;
END $$;

-- ============================================================================
-- 2. 创建 dataset_files 表（如果不存在）
-- ============================================================================
CREATE TABLE IF NOT EXISTS dataset_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT DEFAULT 0,
    role VARCHAR(50) DEFAULT 'primary',
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,
    columns_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dataset_files_dataset_id ON dataset_files(dataset_id);

-- ============================================================================
-- 3. 数据迁移：将旧数据集的 file_path 迁移到 dataset_files
-- ============================================================================
-- 注意：此步骤假设旧 datasets 表有 file_path 字段
-- 如果旧表没有 file_path 字段，此步骤会被跳过
DO $$
DECLARE
    rec RECORD;
    col_exists BOOLEAN;
BEGIN
    -- 检查 datasets 表是否有 file_path 字段
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'datasets' AND column_name = 'file_path'
    ) INTO col_exists;

    IF col_exists THEN
        -- 迁移数据
        FOR rec IN SELECT id, file_path, name, row_count, column_count, file_size
                   FROM datasets WHERE file_path IS NOT NULL
        LOOP
            INSERT INTO dataset_files (dataset_id, file_path, file_name, role, row_count, column_count, file_size)
            VALUES (rec.id, rec.file_path, rec.name || '.csv', 'primary',
                    COALESCE(rec.row_count, 0), COALESCE(rec.column_count, 0), COALESCE(rec.file_size, 0))
            ON CONFLICT DO NOTHING;
        END LOOP;

        -- 更新聚合统计
        UPDATE datasets d SET
            total_row_count = COALESCE((SELECT SUM(row_count) FROM dataset_files WHERE dataset_id = d.id), 0),
            total_column_count = COALESCE((SELECT MAX(column_count) FROM dataset_files WHERE dataset_id = d.id), 0),
            total_file_size = COALESCE((SELECT SUM(file_size) FROM dataset_files WHERE dataset_id = d.id), 0);
    END IF;
END $$;

-- ============================================================================
-- 4. 创建 dataset_subsets 表（如果不存在）
-- ============================================================================
CREATE TABLE IF NOT EXISTS dataset_subsets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    row_count INTEGER,
    split_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dataset_subsets_parent_id ON dataset_subsets(parent_dataset_id);

-- ============================================================================
-- 5. 实验表：新增 subset_id 字段
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'experiments' AND column_name = 'subset_id') THEN
        ALTER TABLE experiments ADD COLUMN subset_id UUID REFERENCES dataset_subsets(id);
    END IF;
END $$;

-- ============================================================================
-- 6. 模型表：新增存储相关字段
-- ============================================================================
DO $$
BEGIN
    -- storage_type
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'models' AND column_name = 'storage_type') THEN
        ALTER TABLE models ADD COLUMN storage_type VARCHAR(20) DEFAULT 'local';
    END IF;

    -- object_key（可为空，用于历史数据兼容）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'models' AND column_name = 'object_key') THEN
        ALTER TABLE models ADD COLUMN object_key VARCHAR(500);
    END IF;

    -- file_size
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'models' AND column_name = 'file_size') THEN
        ALTER TABLE models ADD COLUMN file_size BIGINT;
    END IF;
END $$;

-- ============================================================================
-- 7. 创建 async_tasks 表（如果不存在）
-- ============================================================================
CREATE TABLE IF NOT EXISTS async_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type VARCHAR(50) NOT NULL,
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'queued',
    error_message TEXT,
    config JSONB,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_async_tasks_dataset_id ON async_tasks(dataset_id);
CREATE INDEX IF NOT EXISTS idx_async_tasks_status ON async_tasks(status);

-- ============================================================================
-- 8. 创建更新触发器（如果不存在）
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 datasets 表创建触发器（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_datasets_updated_at') THEN
        CREATE TRIGGER update_datasets_updated_at BEFORE UPDATE ON datasets
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- 为 experiments 表创建触发器（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_experiments_updated_at') THEN
        CREATE TRIGGER update_experiments_updated_at BEFORE UPDATE ON experiments
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- 提交事务
COMMIT;

-- ============================================================================
-- 验证
-- ============================================================================
-- 执行以下命令验证迁移结果：
-- \d datasets
-- \d dataset_files
-- \d dataset_subsets
-- \d experiments
-- \d models
-- \d async_tasks