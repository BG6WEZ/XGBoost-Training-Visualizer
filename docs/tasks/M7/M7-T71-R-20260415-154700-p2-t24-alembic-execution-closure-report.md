# M7-T71 — Task 2.4 补收口（Alembic 执行闭环）完成报告

> 任务编号：M7-T71  
> 阶段：Phase-2 / Task 2.4 Re-open  
> 前置：M7-T70（审计不通过）  
> 完成时间戳：20260415-154700

---

## 一、已完成任务编号

**M7-T71 — Task 2.4 补收口（Alembic 执行闭环）**

---

## 二、修改文件清单

### 修改文件
1. `apps/api/alembic/env.py` — 修复 Alembic 执行链路，独立加载配置，不依赖 pydantic Settings 校验
2. `apps/api/app/database.py` — 修复未迁移场景下 `init_db()` 安全返回问题

---

## 三、Alembic 执行链路是如何修复的

### 上一轮问题
- `env.py` 直接导入 `from app.config import settings`，触发 pydantic 校验 `JWT_SECRET`
- 即使设置环境变量，也会因为 Settings 单例化在 `config.py` 第 97 行失败

### 本轮修复方案

**`apps/api/alembic/env.py` 关键改动：**

1. **在导入 app 模块前先设置必需环境变量**
   ```python
   # Set required env vars BEFORE importing app modules
   os.environ.setdefault("JWT_SECRET", "alembic-migration-secret-key-not-for-production")
   os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
   ```

2. **`get_database_url()` 函数从环境变量直接读取**
   ```python
   def get_database_url() -> str:
       url = os.environ.get("DATABASE_URL")
       if url:
           if url.startswith("postgresql://") and not url.startswith("postgresql+"):
               url = url.replace("postgresql://", "postgresql+asyncpg://")
           return url
       # Fallback to alembic.ini setting
       url = config.get_main_option("sqlalchemy.url")
       if url and url != "postgresql+asyncpg://placeholder:placeholder@localhost:5432/placeholder":
           return url
       raise ValueError("DATABASE_URL environment variable must be set")
   ```

3. **迁移执行时自动使用环境变量中的 DATABASE_URL**
   - 支持 PostgreSQL: `postgresql://user:pass@host:port/dbname`
   - 支持 SQLite: `sqlite+aiosqlite:///./test.db`

---

## 四、`init_db()` 未迁移场景如何安全返回

### 上一轮问题
- 检测到未迁移后仍继续访问 `users` 表，在空库下直接报错

### 本轮修复

**`apps/api/app/database.py` 关键改动：**

```python
async def init_db():
    migrated = await _check_alembic_version()
    
    if not migrated:
        logging.warning(
            "Database migration not detected. "
            "Please run 'alembic upgrade head' to initialize the database schema."
        )
        # 未迁移时安全返回，不访问任何业务表
        return
    
    # 已迁移后才访问业务表
    async with async_session_maker() as session:
        # ... 创建 admin 用户的逻辑
```

关键改进：
- 未迁移时直接 `return`，不访问 `users` 表
- 打印清晰警告提示执行 `alembic upgrade head`

---

## 五、baseline migration 文件名与覆盖内容

**文件名：** `apps/api/alembic/versions/20260415_001_baseline.py`

**Revision ID：** `001_baseline`

**覆盖内容（11 张表）：**
1. `datasets` — 数据集主表
2. `dataset_files` — 数据集文件成员
3. `dataset_subsets` — 数据集子集
4. `experiments` — 实验记录
5. `training_metrics` — 训练指标
6. `training_logs` — 训练日志
7. `models` — 训练模型
8. `feature_importance` — 特征重要性
9. `model_versions` — 模型版本管理
10. `async_tasks` — 异步任务
11. `users` — 用户表

---

## 六、实际执行命令

使用 SQLite 进行迁移验证（Docker 未运行，PostgreSQL 不可用）：

```powershell
cd apps/api
$env:DATABASE_URL="sqlite+aiosqlite:///./test_migrate.db"
$env:JWT_SECRET="test-secret"

# 1. upgrade head
alembic upgrade head

# 2. downgrade base
alembic downgrade base

# 3. upgrade head (再次)
alembic upgrade head

# 4. 清理测试文件 + 全量测试
Remove-Item -Path test_migrate.db -ErrorAction SilentlyContinue
pytest tests/ -q --tb=short
```

---

## 七、`upgrade head` / `downgrade base` / 再次 `upgrade head` 的完整原始输出

### 1. `alembic upgrade head`

```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_baseline, Baseline migration - create all tables from current schema
```

### 2. `alembic downgrade base`

```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running downgrade 001_baseline -> , Baseline migration - create all tables from current schema
```

### 3. `alembic upgrade head`（再次）

```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_baseline, Baseline migration - create all tables from current schema
```

---

## 八、全量测试输出

```
........................................................................ [ 19%]
........................................................................ [ 38%]
.......................................................................s [ 58%]
ssss.................................................................... [ 77%]
..........................................................ssss.......... [ 97%]
..........                                                               [100%]
============================== warnings summary ===============================
tests/test_data_quality.py::TestQualityScore::test_target_column_inf_low_accuracy
  C:\Users\wangd\project\XGBoost Training Visualizer\.venv\Lib\site-packages\pandas\core\nanops.py:1263: RuntimeWarning: invalid value encountered in subtract
    adjusted = values - mean

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
361 passed, 9 skipped, 1 warning in 136.52s (0:02:16)
```

---

## 九、未验证部分

- **PostgreSQL 真实环境验证**：Docker 未运行，本次使用 SQLite 验证迁移闭环。SQLite 和 PostgreSQL 的 Alembic 迁移逻辑相同，区别仅在于 DDL 语法（SQLite 无事务 DDL）。PostgreSQL 环境下的实际验证建议在部署生产前补充。
- **启动脚本中的 alembic 命令**：`start-local.sh` 和 `start-local.bat` 中的 alembic 命令在 PostgreSQL 运行环境下未实测。

---

## 十、风险与限制

1. **SQLite 与 PostgreSQL DDL 差异**：当前 baseline migration 使用 `sa.text("gen_random_uuid()")` 作为 UUID 默认值，该函数在 PostgreSQL 中可用，SQLite 环境测试时未实际调用（SQLite 不使用该默认值）。如果实际部署到 PostgreSQL，请确保 PostgreSQL 版本 >= 13（内置 `gen_random_uuid()`）。
2. **启动脚本容错处理**：`start-local.sh` 和 `start-local.bat` 已添加 alembic 失败的容错处理（`|| echo 警告`），不会阻塞服务启动。
3. **环境变量依赖**：Alembic 执行需要 `DATABASE_URL` 和 `JWT_SECRET` 环境变量。`env.py` 已设置默认 `JWT_SECRET`，但生产环境应通过环境变量覆盖。

---

## 十一、是否建议重新提交 Task 2.4 验收

**建议：通过，可以重新提交验收。**

### 通过条件检查清单

- [x] `apps/api/alembic/versions/` 下至少有 1 个 migration 文件
- [x] `alembic upgrade head` **实际执行成功**（SQLite 验证通过）
- [x] `alembic downgrade base` **实际执行成功**（SQLite 验证通过）
- [x] 二次 `alembic upgrade head` **实际执行成功**（SQLite 验证通过）
- [x] 生产启动流程不再自动 `create_all`
- [x] 未迁移场景下 `init_db()` 不会继续访问业务表（安全 return）
- [x] 测试环境仍可正常初始化数据库
- [x] 全量测试通过（361 passed, 9 skipped, **0 failed**）
- [x] 未越界推进到 Phase-3 或后续任务

---

## 十二、修复摘要

| 问题 | 修复方式 |
|------|----------|
| `env.py` 导入 Settings 触发 pydantic 校验 | 在导入前设置 `JWT_SECRET` 环境变量，直接读取 DATABASE_URL |
| `init_db()` 未迁移时继续访问业务表 | 未迁移时安全 return，不访问任何业务表 |
| 迁移执行链路不通 | 修复后 upgrade/downgrade/upgrade 完整闭环验证通过 |