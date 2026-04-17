# M7-T21 任务单：M7-T20 审计修复与真实并发/队列证据闭环

任务编号: M7-T21  
时间戳: 20260401-111155  
所属计划: M7-T20 审计修复轮  
前置任务: M7-T20（未通过，需修复）  
优先级: 最高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T20-20260401-100809-p1-t09-concurrent-training-and-queue-visibility.md
- [ ] docs/tasks/M7/M7-T20-R-20260401-100809-p1-t09-concurrent-training-and-queue-visibility-report.md

未完成上述预读，不得开始执行。

---

## 一、当前审计结论（必须先承认问题）

M7-T20 **不能判定为通过**。当前实现存在以下阻断问题：

### 阻断问题 1：并发训练未真正接入执行链路

`apps/worker/app/main.py` 当前主循环是单 worker 串行 `blpop -> await process_training_task()`，未形成多任务并发执行。仅增加 `TRAINING_MAX_CONCURRENCY` 配置与队列工具方法，**不等于真实并发生效**。

### 阻断问题 2：running 集合未接入真实生命周期

`apps/api/app/services/queue.py` 中虽然定义了：
- `register_running_task()`
- `unregister_running_task()`
- `RUNNING_TASKS_SET = "training:running"`

但审计发现这些方法**没有被 worker 训练主链路实际调用**，导致：
- `running_count` 统计不可信
- `available_slots` 不可信
- `queue/stats` 端点并不能反映真实运行状态

### 阻断问题 3：所谓“并发 E2E”其实只是 mocked 单元测试

当前 `apps/api/tests/test_training_queue_concurrency.py` 主要通过：
- patch `QueueService.__init__`
- `AsyncMock` 模拟 Redis

它验证的是工具函数逻辑，不是“至少 2 个任务并发 running + 第 3 个 queued + 自动转运行”的真实链路，**与任务单要求不符**。

因此，M7-T20 当前结论应为：
- **部分通过**：配置项、队列字段、前端展示基础已实现
- **未通过**：真实并发执行与真实队列证据未达标

---

## 二、本轮修复目标

本轮不是推进 P1-T10，而是只修 M7-T20 审计阻断项，形成真实闭环：

1. 让训练 worker 或调度层支持**真实并发槽位**。
2. 让 running/queued 状态与 Redis 统计**来自真实执行链路**。
3. 提供**真实并发 E2E 证据**，而非 mocked queue 单测冒充。
4. 修正汇报文档中“并发 E2E 已通过”的失实表述。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/config.py
- apps/api/app/services/queue.py
- apps/api/app/routers/experiments.py
- apps/api/app/schemas/experiment.py
- apps/worker/app/main.py
- apps/api/tests/**（新增真实并发/队列链路测试）
- apps/web/src/lib/api.ts
- apps/web/src/pages/ExperimentsPage.tsx
- docs/tasks/M7/M7-T20-R-20260401-100809-p1-t09-concurrent-training-and-queue-visibility-report.md（修正文档事实）
- docs/tasks/M7/M7-T21-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure.md
- docs/tasks/M7/M7-T21-R-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure-report.md（完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- 结果分析图表（P1-T10）
- 无关页面视觉重构
- 数据库迁移（除非先证明为阻断）
- 数据上传、预处理、特征工程业务逻辑

---

## 四、必须完成的修复项

### 4.1 真实并发执行能力

需要在 worker/调度层实现真实并发，而不是单循环串行。可接受方案包括但不限于：

#### 方案 A：Worker 内部并发槽位
- worker 维护一个 in-flight tasks 集合
- 当运行中任务数 < `TRAINING_MAX_CONCURRENCY` 时，继续拉取新训练任务
- 使用 `asyncio.create_task()` 或等价机制并发执行训练
- 任务结束后自动释放槽位

#### 方案 B：多 worker + 统一运行集约束
- 多 worker 并发消费队列
- 每次启动训练前必须原子注册 `training:running`
- 注册失败则任务重新排队或等待

无论采用哪种方案，都必须满足：
- 至少 2 个任务真正同时处于 running
- 第 3 个任务进入 queued
- 其中一个 running 完成后，第 3 个自动转 running

### 4.2 running 集合真实接入生命周期

必须把以下动作接入真实训练链路：

- 任务开始前：`register_running_task(experiment_id)`
- 任务结束后：`unregister_running_task(experiment_id)`
- 异常失败时：也必须释放 running 槽位
- cancelled/跳过场景：不得泄漏 running 状态

### 4.3 队列统计真实性

`/api/experiments/queue/stats` 与前端摘要必须反映真实状态，而不是工具层假数据：

- `running_count` 来自真实 running set
- `queued_count` 来自真实 waiting queue
- `queue_position` 必须与当前排队顺序一致
- running 任务 `queue_position` 必须为 null/None

### 4.4 测试与证据回归

必须新增或替换当前 mocked 单测，补齐**真实链路**验证：

1. 真实并发测试：至少 3 个训练任务
2. 真实队列转移测试：1 个 queued 自动转 running
3. 真实统计一致性测试：running + queued 与活跃任务数一致

---

## 五、多角色协同执行要求（强制）

1. `Scheduler-Agent`：并发模型设计与状态语义落地。
2. `Worker-Agent`：worker 生命周期中 running slot 注册/释放。
3. `API-Agent`：队列统计与实验列表接口真实性校验。
4. `Frontend-Agent`：前端展示与真实状态联调，不得展示伪并发。
5. `QA-Agent`：真实并发 E2E、状态迁移、统计一致性测试。
6. `Reviewer-Agent`：核对失实表述是否被修正，决定是否允许进入下一任务。

---

## 六、必须提供的实测证据

### 6.1 真实并发 E2E（必须）

至少提交 3 个训练任务，并记录全过程：

- 时刻 T1：2 个任务 running，1 个任务 queued
- 时刻 T2：其中 1 个完成后，queued 任务转为 running

证据必须包含：
- 实验 ID
- 每次状态采样的时间点
- running_count / queued_count / queue_position

可接受形式：
```bash
python -m pytest apps/api/tests/test_training_real_concurrency_e2e.py -v
```
或等价真实脚本输出。

### 6.2 队列一致性测试（真实，不接受纯 mock）

```bash
python -m pytest apps/api/tests/test_queue_runtime_consistency.py -v
```

### 6.3 前端门禁

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
```

### 6.4 后端回归

```bash
python -m pytest apps/api/tests/ -q
```

若仍有既有失败项，必须明确列出，不得写“全部通过”。

---

## 七、完成判定

以下全部满足才可宣称 M7-T20 审计问题已关闭：

- [ ] 至少 2 个训练任务真实并发 running
- [ ] 第 3 个任务真实进入 queued
- [ ] queued 任务可自动转 running
- [ ] running_count / queued_count / queue_position 与真实状态一致
- [ ] running 集合在成功/失败/取消场景都不泄漏
- [ ] mocked queue 单测不再冒充并发 E2E 证据
- [ ] 前端展示与 API 状态一致
- [ ] typecheck/build 通过
- [ ] 后端回归结果如实报告
- [ ] 已修正文档中失实“并发 E2E 已通过”表述

---

## 八、Copilot 审核重点

1. 是否真正实现并发，而非串行 worker + 队列统计伪装。
2. `register_running_task` / `unregister_running_task` 是否接入真实生命周期。
3. 真实 E2E 证据是否包含状态时间序列，而不是静态截图或 mock 输出。
4. 汇报是否修正了 M7-T20 中不实结论。
5. 是否仍然存在 `running_count` 永远不变或不可信的问题。

---

## 九、风险提示

1. 并发实现不当可能引入竞态和 running set 泄漏。
2. 若 Redis 状态更新非原子，queue_position 与 running_count 可能短时失真。
3. 若用 sleep 伪造并发证据，将视为未完成。

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T21-R-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure-report.md`

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T10 / M7-T22。
