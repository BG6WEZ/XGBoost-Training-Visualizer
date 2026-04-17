# M7-T71 — Task 2.4 补收口（Alembic 执行闭环）

> 任务编号：M7-T71  
> 阶段：Phase-2 / Task 2.4 Re-open  
> 前置：M7-T70（审计不通过）  
> 时间戳：20260415-145019

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T70-AUDIT-SUMMARY-20260415-145019.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 2.4`

---

## 一、本轮目标

本轮**不得进入 Phase-3**。只允许继续收口 **Task 2.4 数据库迁移正规化（Alembic）**，补齐上一轮缺失的真实迁移执行闭环。

---

## 二、允许修改的范围文件

- `apps/api/alembic.ini`
- `apps/api/alembic/`
- `apps/api/app/database.py`
- `apps/api/tests/conftest.py`
- `apps/api/tests/test_db_helper.py`
- `start-local.bat`
- `start-local.sh`
- 如确有必要，可新增与 Alembic 执行闭环直接相关的测试/辅助脚本

禁止越界到：

- 前端代码
- Worker 业务逻辑
- 认证逻辑
- 与数据库迁移无关的 API 业务代码

---

## 三、必须完成的最小工作

### 1) 让 `alembic upgrade head` 真正可执行

当前阻断点不是“没有 migration 文件”，而是：

- `alembic upgrade head` 实跑失败

你必须修复 Alembic 执行链路，使其在当前项目环境下能真实跑通。

重点检查：

- `env.py` 如何读取 `DATABASE_URL`
- `app.config.Settings` 对 `.env` 的加载路径是否与 Alembic 执行目录兼容
- `JWT_SECRET` / `DATABASE_URL` 等必需配置在迁移场景下如何提供

要求：

- 不要只让 `history` 能跑
- 必须让 `upgrade` / `downgrade` 真正可执行

### 2) 真实完成迁移往返验证

你必须按任务单真实执行：

1. `alembic upgrade head`
2. `alembic downgrade base`
3. `alembic upgrade head`

要求：

- 报告中附完整原始输出
- 不得用 `--version` / `history` 代替
- 若依赖本地 PostgreSQL，请明确如何启动与连接

### 3) 修正未迁移场景下的 `init_db()` 后续行为

当前 `database.py` 在检测到未迁移后仍会继续查询 `users` 表，这可能在空库下直接报错。

要求：

- 若未检测到迁移，不应继续访问依赖已建表的业务表
- 应只打印清晰警告并安全返回，或采用同等安全策略

### 4) 报告必须按真实验证结果书写

禁止再出现：

- 未跑 `upgrade/downgrade` 却勾选通过
- 一边写“全部验证”，一边又说“需要部署前补充验证”

---

## 四、验证命令

至少执行以下命令，并在报告中附**完整原始输出**：

```bash
cd apps/api
..\..\.venv\Scripts\alembic.exe upgrade head
..\..\.venv\Scripts\alembic.exe downgrade base
..\..\.venv\Scripts\alembic.exe upgrade head
..\..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

如果需要先设置环境变量或启动本地 PostgreSQL，也必须把完整前置命令写进报告。

---

## 五、通过条件（全部满足才算通过）

- [ ] `apps/api/alembic/versions/` 下至少有 1 个 migration 文件
- [ ] `alembic upgrade head` 实际执行成功
- [ ] `alembic downgrade base` 实际执行成功
- [ ] 二次 `alembic upgrade head` 实际执行成功
- [ ] 生产启动流程不再自动 `create_all`
- [ ] 未迁移场景下 `init_db()` 不会继续访问业务表
- [ ] 测试环境仍可正常初始化数据库
- [ ] 全量测试通过（不得新增 failed）
- [ ] 未越界推进到 Phase-3 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T71-R-<timestamp>-p2-t24-alembic-execution-closure-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. Alembic 执行链路是如何修复的
4. `init_db()` 未迁移场景如何安全返回
5. baseline migration 文件名与覆盖内容
6. 实际执行命令
7. `upgrade head` / `downgrade base` / 再次 `upgrade head` 的完整原始输出
8. 全量测试输出
9. 未验证部分
10. 风险与限制
11. 是否建议重新提交 Task 2.4 验收

---

## 七、明确禁止

- 不得再用 `history` / `--version` 代替迁移执行验证
- 不得把未验证项写成已通过
- 不得让未迁移场景继续访问业务表
- 不得提前进入 Phase-3
