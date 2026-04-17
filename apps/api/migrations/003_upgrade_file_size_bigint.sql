-- ============================================================================
-- XGBoost Training Visualizer - 升级脚本
-- 版本: 1.1
-- 目标: 将文件大小相关字段从 INTEGER 升级为 BIGINT，支持 > 2GB 数据集
-- 执行方式: psql -f 003_upgrade_file_size_bigint.sql
-- ============================================================================

BEGIN;

ALTER TABLE IF EXISTS datasets
    ALTER COLUMN total_file_size TYPE BIGINT;

ALTER TABLE IF EXISTS dataset_files
    ALTER COLUMN file_size TYPE BIGINT;

ALTER TABLE IF EXISTS models
    ALTER COLUMN file_size TYPE BIGINT;

COMMIT;
