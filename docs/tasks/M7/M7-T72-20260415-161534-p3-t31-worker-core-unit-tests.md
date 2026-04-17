# M7-T72 — Phase-3 / Task 3.1 Worker 核心路径单元测试

> 任务编号：M7-T72  
> 阶段：Phase-3 / Task 3.1  
> 前置：M7-T71（Task 2.4 已通过）  
> 时间戳：20260415-161534

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T71-AUDIT-SUMMARY-20260415-161534.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 3.1`

---

## 一、本轮目标

进入 `Phase-3 / Task 3.1 — Worker 核心路径单元测试`，目标是为 Worker 关键执行链路补上自动化回归，确保训练与任务执行逻辑在无外部服务依赖下可验证。

---

## 二、允许修改的范围文件

- `apps/worker/tests/`（新增或扩展）
- 如确有必要，可修改 `apps/worker/` 下与测试隔离、依赖注入、mock 友好性直接相关的少量代码

禁止越界到：

- 前端代码
- API 业务逻辑
- Docker / Alembic / 认证
- 与 Worker 测试无关的重构

---

## 三、必须完成的最小工作

### 1) 新增或补齐以下测试

至少覆盖以下 8 项：

1. `test_training_task.py::test_xgboost_trainer_loads_csv`
2. `test_training_task.py::test_xgboost_trainer_runs_training`
3. `test_training_task.py::test_xgboost_trainer_early_stopping`
4. `test_training_task.py::test_xgboost_trainer_invalid_target_column`
5. `test_training_task.py::test_xgboost_trainer_saves_metrics`
6. `test_preprocessing_task.py::test_preprocessing_runs_successfully`
7. `test_feature_engineering_task.py::test_feature_engineering_runs`
8. `test_worker_main.py::test_worker_graceful_shutdown`

如果现有文件名不同，可以调整，但报告中必须明确“实际测试文件/测试名”与任务要求的对应关系。

### 2) 测试必须可脱离外部服务运行

要求：

- 使用临时目录
- 使用内存 SQLite
- mock Redis / 外部依赖
- 不依赖 Docker / PostgreSQL / Redis / MinIO 实际运行

### 3) 优先做高价值断言

避免只测“函数能调用”。至少验证：

- 训练器能正确读取 CSV
- 训练后确实生成 model 文件
- early stopping 真的触发并提前终止
- 目标列不存在时返回明确错误
- metrics 列表非空
- 预处理/特征工程任务有可验证产物或状态
- Worker 收到停止信号后优雅退出

### 4) 若为测试补点做了少量代码调整

要求：

- 必须是为可测性服务的最小改动
- 不得顺手做与测试无关的大重构
- 报告中明确写出“为什么必须改代码”

---

## 四、验证命令

至少执行以下命令，并在报告中附完整输出：

```bash
cd apps/worker
..\..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

如果你将测试拆成多个文件单独执行，也请在报告中附上对应命令。

---

## 五、通过条件（全部满足才算通过）

- [ ] 新增测试不少于 8 个
- [ ] 覆盖训练 / 预处理 / 特征工程 / Worker 退出四类核心路径
- [ ] `pytest apps/worker/tests/ -q` 全部 passed
- [ ] 测试不依赖 Docker / PostgreSQL / Redis 实际运行
- [ ] 未越界推进到 Task 3.2 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T72-R-<timestamp>-p3-t31-worker-core-unit-tests-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 新增测试清单
4. 每个测试覆盖的核心验证点
5. 是否为可测性改动了生产代码；若有，说明原因
6. 实际执行命令
7. 实际输出原文
8. 未验证部分
9. 风险与限制
10. 是否建议进入 Task 3.2

---

## 七、明确禁止

- 不得用大量 mock 把核心逻辑全绕开
- 不得新增低价值“仅调用即通过”测试
- 不得依赖外部服务才能跑通
- 不得提前进入 Task 3.2
