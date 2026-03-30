# 数据库迁移执行手册

## 概述

本文档描述 XGBoost Training Visualizer 项目的数据库迁移方案，用于处理 Schema 变更。

**迁移文件位置**：`apps/api/migrations/`

---

## 依赖要求

### Python 脚本依赖

| 命令 | 依赖 | 说明 |
|------|------|------|
| `--help` | 无 | 仅显示帮助，无依赖 |
| `--init` | psql | 使用 psql 执行 SQL 文件 |
| `--upgrade` | psql | 使用 psql 执行 SQL 文件 |
| `--check` | sqlalchemy + asyncpg | 连接数据库检查结构 |
| `--verify` | sqlalchemy + asyncpg | 连接数据库验证结果 |

### 安装依赖

```bash
# psql（Windows）
# 通过 PostgreSQL 安装包或 chocolatey 安装
choco install postgresql

# sqlalchemy + asyncpg
pip install sqlalchemy asyncpg
```

### 无 psql 时的替代方案

如果本地未安装 psql，`--init` 和 `--upgrade` 会输出手动执行命令：

```bash
# 脚本会提示类似以下命令
psql -h localhost -U xgboost -d xgboost_vis -f apps/api/migrations/001_init_schema.sql
```

也可以通过 Docker 执行：

```bash
docker exec -i docker-postgres-1 psql -U xgboost -d xgboost_vis < apps/api/migrations/001_init_schema.sql
```

---

## 迁移脚本清单

| 脚本 | 用途 | 适用场景 |
|------|------|----------|
| `001_init_schema.sql` | 完整初始化 | 新库初始化 |
| `002_upgrade_multi_file.sql` | 升级迁移 | 旧库升级到多文件数据集版本 |

---

## 场景一：新库初始化

### 前置条件

1. PostgreSQL 15+ 已安装
2. 数据库 `xgboost_vis` 已创建（或使用超级用户创建）

### 执行步骤

#### 方式一：使用 SQL 脚本（推荐）

```bash
# 1. 创建数据库（如未创建）
psql -U xgboost -d postgres -c "CREATE DATABASE xgboost_vis;"

# 2. 执行初始化脚本
psql -U xgboost -d xgboost_vis -f apps/api/migrations/001_init_schema.sql

# 3. 验证
psql -U xgboost -d xgboost_vis -c "\dt"
```

#### 方式二：使用 Python 脚本

```bash
cd apps/api

# 检查数据库结构
python scripts/migrate_db.py --check

# 初始化新库
python scripts/migrate_db.py --init

# 验证
python scripts/migrate_db.py --verify
```

#### 方式三：使用 API 初始化

```bash
# 启动 API 时自动创建表
cd apps/api
uvicorn app.main:app --reload
# 数据库表会在启动时自动创建
```

### 预期结果

```
                 List of relations
 Schema |         Name          | Type  |  Owner
--------+-----------------------+-------+----------
 public | async_tasks           | table | xgboost
 public | dataset_files         | table | xgboost
 public | dataset_subsets       | table | xgboost
 public | datasets              | table | xgboost
 public | experiments           | table | xgboost
 public | feature_importance    | table | xgboost
 public | models                | table | xgboost
 public | training_logs         | table | xgboost
 public | training_metrics      | table | xgboost
```

---

## 场景二：旧库升级

### 适用情况

已存在旧版本数据库，需要升级以支持：
- 多文件数据集（`dataset_files` 表）
- 数据集子集（`dataset_subsets` 表）
- 异步任务（`async_tasks` 表）
- 模型存储字段（`storage_type`, `object_key`）

### 执行前备份

```bash
# 备份数据库
pg_dump -U xgboost xgboost_vis > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 执行步骤

```bash
# 1. 检查当前结构
psql -U xgboost -d xgboost_vis -c "\d datasets"
psql -U xgboost -d xgboost_vis -c "\d models"

# 2. 执行升级脚本
psql -U xgboost -d xgboost_vis -f apps/api/migrations/002_upgrade_multi_file.sql

# 3. 验证升级结果
psql -U xgboost -d xgboost_vis -c "\d dataset_files"
psql -U xgboost -d xgboost_vis -c "\d async_tasks"
```

### 或使用 Python 脚本

```bash
cd apps/api

# 检查
python scripts/migrate_db.py --check

# 升级
python scripts/migrate_db.py --upgrade

# 验证
python scripts/migrate_db.py --verify
```

---

## 迁移内容说明

### 新增表

| 表名 | 说明 |
|------|------|
| `dataset_files` | 数据集文件成员（多文件支持） |
| `dataset_subsets` | 数据集子集（训练/测试切分） |
| `async_tasks` | 异步任务记录（预处理/特征工程） |

### 修改表

| 表名 | 新增字段 |
|------|----------|
| `datasets` | `time_column`, `entity_column`, `target_column`, `total_row_count`, `total_column_count`, `total_file_size` |
| `experiments` | `subset_id` |
| `models` | `storage_type`, `object_key`, `file_size` |

### 索引

| 索引名 | 表 |
|--------|-----|
| `idx_dataset_files_dataset_id` | `dataset_files` |
| `idx_dataset_subsets_parent_id` | `dataset_subsets` |
| `idx_experiments_dataset_id` | `experiments` |
| `idx_experiments_status` | `experiments` |
| `idx_training_metrics_experiment_id` | `training_metrics` |
| `idx_training_logs_experiment_id` | `training_logs` |
| `idx_feature_importance_experiment_id` | `feature_importance` |
| `idx_async_tasks_dataset_id` | `async_tasks` |
| `idx_async_tasks_status` | `async_tasks` |

---

## 历史数据兼容性

### models 表

| 字段 | 说明 |
|------|------|
| `object_key` | 可为空。新模型必须填写，历史模型为空 |
| `file_path` | 已弃用。仅用于历史数据兼容 |

**模型下载逻辑**：
- `object_key` 不为空：通过存储适配器读取
- `object_key` 为空：尝试通过 `file_path` 读取（历史兼容）

### 数据迁移

**已自动迁移**：
- 旧 `datasets.file_path` → 新 `dataset_files` 表

**未自动迁移**（需手动处理）：
- 历史模型文件的 `object_key` 不会自动填充
- 历史模型仍可通过 `file_path` 下载

---

## 风险点

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据丢失 | 升级前未备份 | 执行前必须备份 |
| 外键约束失败 | 数据不一致 | 检查现有数据完整性 |
| 字段类型不兼容 | 迁移失败 | 脚本使用 IF NOT EXISTS 确保幂等 |
| 索引创建失败 | 性能下降 | 手动创建缺失索引 |

---

## 回滚方案

如果迁移失败，从备份恢复：

```bash
# 删除数据库
psql -U xgboost -d postgres -c "DROP DATABASE xgboost_vis;"

# 重新创建
psql -U xgboost -d postgres -c "CREATE DATABASE xgboost_vis;"

# 恢复备份
psql -U xgboost -d xgboost_vis -f backup_YYYYMMDD_HHMMSS.sql
```

---

## 验证清单

- [ ] 所有 9 张表已创建
- [ ] `datasets` 表包含 `total_row_count` 等聚合字段
- [ ] `dataset_files` 表已创建并包含索引
- [ ] `async_tasks` 表已创建
- [ ] `models` 表包含 `storage_type`, `object_key` 字段
- [ ] 更新触发器已创建

---

## 常见问题

### Q: 执行 SQL 脚本报 "relation already exists"

A: 正常现象，脚本设计为幂等操作。可忽略此警告。

### Q: Python 脚本连接失败

A: 检查 `DATABASE_URL` 环境变量是否正确设置。

### Q: 历史模型无法下载

A: 检查 `models.object_key` 是否为空。如果为空，确保 `file_path` 指向有效文件路径。

---

**文档版本**：1.4
**创建日期**：2026-03-26
**更新日期**：2026-03-26
**状态**：脚本可启动已验证，迁移执行未验证

### 验证状态

#### Codex 复核环境

| 命令 | 验证结果 | 说明 |
|------|----------|------|
| `--help` | ✅ 通过 | 脚本可正常启动并显示帮助 |
| `--init` | 未验证 | 依赖 psql，环境未安装 |
| `--upgrade` | 未验证 | 依赖 psql，环境未安装 |
| `--check` | 未验证 | 依赖 sqlalchemy，环境未安装 |
| `--verify` | 未验证 | 依赖 sqlalchemy，环境未安装 |

#### Claude 本地环境（非 Codex 复核环境）

**环境信息**：
- 操作系统：Windows 11 Pro
- Python：3.14.3
- sqlalchemy：2.0.47
- asyncpg：0.31.0
- psql：未安装

| 命令 | 验证结果 | 说明 |
|------|----------|------|
| `--help` | ✅ 通过 | 脚本可正常启动并显示帮助 |
| `--init` | 未验证 | 依赖 psql，本地未安装 |
| `--upgrade` | 未验证 | 依赖 psql，本地未安装 |
| `--check` | ✅ 通过 | 9 张表全部存在，15 个关键字段全部存在 |
| `--verify` | ✅ 执行成功 | 发现 uuid-ossp 扩展、索引、触发器未创建（数据库通过 SQLAlchemy 自动创建，未执行迁移脚本） |

### 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.4 | 2026-03-26 | 区分 Codex 复核环境与 Claude 本地环境验证结果 |
| 1.3 | 2026-03-26 | 添加验证环境信息；修正验证状态表述 |
| 1.2 | 2026-03-26 | 添加依赖要求章节 |
| 1.1 | 2026-03-26 | 修正迁移脚本文件名 |
| 1.0 | 2026-03-26 | 初版 |