# M7-T70 — Task 2.4 数据库迁移正规化（Alembic）

> 任务编号：M7-T70  
> 阶段：Phase-2 / Task 2.4  
> 前置：M7-T69（Task 2.3 已通过）  
> 时间戳：20260415-110647

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T69-AUDIT-SUMMARY-20260415-110647.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 2.4`

---

## 一、本轮目标

进入 `Task 2.4 — 数据库迁移正规化（Alembic）`，目标是让数据库 schema 管理从运行时自动 `create_all` 过渡到显式 migration 流程，同时不破坏现有测试体系。

---

## 二、允许修改的范围文件

- `apps/api/alembic.ini`（新增）
- `apps/api/alembic/`（新增目录及文件）
- `apps/api/app/database.py`
- `apps/api/migrations/` 下现有 SQL 文件（只读参考，不建议直接改）
- `apps/api/tests/` 下与数据库初始化直接相关的测试辅助文件
- `start-local.bat`
- `start-local.sh`

如确有必要，可新增极少量与 Alembic 配置直接相关的脚本/模板，但必须与本任务直接相关。

禁止越界到：

- 前端代码
- Worker 业务逻辑
- 认证逻辑
- 与数据库迁移无关的 API 业务代码

---

## 三、必须完成的最小工作

### 1) 初始化 Alembic 并接入当前项目

在 `apps/api/` 下完成：

- 新增 `alembic.ini`
- 新增 `alembic/`
- 配置到当前项目的数据库连接方式

要求：

- 能在当前项目结构下执行 `alembic upgrade head`
- 明确处理 async SQLAlchemy 场景

### 2) 创建 baseline migration

基于当前现有 schema 状态，创建至少 1 个 baseline migration。

要求：

- `apps/api/alembic/versions/` 下至少有 1 个 migration 文件
- baseline 应覆盖当前已有表结构，而不是空迁移
- 可以参考 `apps/api/migrations/` 下现有 SQL 文件的最终结果，但不要只做“拷贝文件不接线”

### 3) 生产启动流程不再自动 `create_all`

在 `apps/api/app/database.py` 中：

- 调整 `init_db()` 行为

要求：

- 生产/正常启动时不再直接执行全量 `create_all`
- 改为检查 `alembic_version` 是否存在
- 若未迁移，打印清晰警告，提示先执行 `alembic upgrade head`

### 4) 保留测试环境的 `create_all`

测试体系不能因为引入 Alembic 而崩掉。

要求：

- `conftest.py` 或现有测试初始化逻辑仍可用 `create_all`
- 全量测试必须继续通过

### 5) 本地启动脚本加入迁移步骤

在以下脚本中加入迁移执行步骤：

- `start-local.bat`
- `start-local.sh`

要求：

- 在启动 API 前执行 `alembic upgrade head`
- 若脚本已有数据库初始化逻辑，要避免重复或冲突

---

## 四、验证命令

至少执行以下命令，并在报告中附实际输出：

```bash
cd apps/api
..\..\.venv\Scripts\alembic.exe upgrade head
..\..\.venv\Scripts\alembic.exe downgrade base
..\..\.venv\Scripts\alembic.exe upgrade head
..\..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

如果你的环境中 `alembic.exe` 路径不同，请在报告里明确说明实际命令。

---

## 五、通过条件（全部满足才算通过）

- [ ] `apps/api/alembic/versions/` 下至少有 1 个 migration 文件
- [ ] `alembic upgrade head` 可执行成功
- [ ] `alembic downgrade base` 可执行成功
- [ ] 生产启动流程不再自动 `create_all`
- [ ] 测试环境仍可正常初始化数据库
- [ ] 全量测试通过（不得新增 failed）
- [ ] 未越界推进到 Phase-3 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T70-R-<timestamp>-p2-t24-alembic-normalization-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. Alembic 初始化结构说明
4. baseline migration 文件名与覆盖内容
5. `database.py` 中去掉自动 `create_all` 的方式
6. 测试环境如何保留 `create_all`
7. 本地启动脚本新增了什么
8. 实际执行命令
9. 实际输出原文
10. 未验证部分
11. 风险与限制
12. 是否建议进入下一阶段

---

## 七、明确禁止

- 不得只生成空 migration 充数
- 不得让生产启动继续自动 `create_all`
- 不得破坏现有测试初始化逻辑
- 不得跳过 upgrade/downgrade 实际验证
- 不得提前进入 Phase-3
