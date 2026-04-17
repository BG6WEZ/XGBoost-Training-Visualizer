# M7-T20 任务单：P1-T09 并发训练与队列可视化

任务编号: M7-T20  
时间戳: 20260401-100809  
所属计划: P1-S3 / P1-T09  
前置任务: M7-T19（已完成）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T09 验收标准）
- [ ] docs/tasks/M7/M7-T19-20260401-091118-p1-t08-parameter-validation-and-conflict-hints.md
- [ ] docs/tasks/M7/M7-T19-R-20260401-091118-p1-t08-parameter-validation-and-conflict-hints-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

目前实验训练链路以“单任务可运行”为主，缺少可证明的并发能力和队列可观测性。P1-T09 目标要求：

1. 支持至少 2 个训练任务并发执行。
2. 在前端可观察排队状态与队列长度变化。
3. 队列与运行状态字段语义一致且可复核。

这轮任务应解决“看起来能提交任务，但无法判断系统并发吞吐和排队行为”的问题。

---

## 二、任务目标

1. 后端明确并发上限配置（例如 worker 并发槽位）。
2. 实验状态流转可区分：queued / running / completed / failed。
3. 新增队列观测接口或在现有接口补齐队列字段（queue_position、running_count、queued_count）。
4. 前端展示任务排队与并发运行状态（至少列表可见）。
5. 提供并发 E2E 证据与队列长度一致性证据。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/routers/experiments.py
- apps/api/app/schemas/experiment.py
- apps/api/app/services/**（如实验调度/队列统计服务）
- apps/worker/app/**（仅限并发槽位与状态上报相关）
- apps/api/tests/**（新增并发与队列测试）
- apps/web/src/lib/api.ts
- apps/web/src/pages/ExperimentsPage.tsx
- apps/web/src/components/**（如新增队列状态组件）
- docs/tasks/M7/M7-T20-20260401-100809-p1-t09-concurrent-training-and-queue-visibility.md
- docs/tasks/M7/M7-T20-R-20260401-100809-p1-t09-concurrent-training-and-queue-visibility-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- 数据集上传、预处理、特征工程业务逻辑
- 与队列可视化无关的页面重构
- 数据库迁移（除非证明为阻断且先报批）
- 提前实现 P1-T10 结果分析图表

---

## 四、详细交付要求

### 4.1 并发上限配置

明确并发上限配置来源并在代码中可见：

- 允许通过环境变量配置（例如 `TRAINING_MAX_CONCURRENCY`）。
- 当并发槽位满时，新任务进入 queued，而不是直接失败。
- 状态流转必须可追踪：`pending -> queued -> running -> completed/failed`。

### 4.2 队列可观测字段

为实验列表或任务状态接口补齐至少以下字段：

- `queue_position`：当前排队位置（running 状态为 0 或 null）。
- `running_count`：当前运行中的训练任务数。
- `queued_count`：当前排队中的训练任务数。
- `max_concurrency`：并发上限。

要求字段命名在 schema/router/types/docs 保持一致。

### 4.3 前端队列可视化

在实验页补齐队列可视信息：

1. 显示每个任务的当前状态与排队序号。
2. 页面顶部显示并发摘要：运行中/排队中/上限。
3. 状态轮询可刷新排队位置变化。

### 4.4 状态语义一致性

必须定义并执行一致语义：

- running：实际占用训练槽位的任务。
- queued：已入队但未开始执行。
- queue_position：仅 queued 有意义，且最小值为 1。

禁止出现：
- queued 任务无 queue_position。
- running 任务仍显示 queue_position > 0。
- 前端状态词与后端枚举不一致。

---

## 五、多角色协同执行要求（强制）

1. `Scheduler-Agent`：并发调度、队列统计、状态语义。
2. `Worker-Agent`：并发执行与状态上报正确性。
3. `API-Agent`：接口契约与返回字段一致性。
4. `Frontend-Agent`：队列可视组件与轮询展示。
5. `QA-Agent`：并发 E2E、一致性验证、回归测试。
6. `Reviewer-Agent`：范围控制、证据完整性、验收结论。

汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 并发场景 E2E（必须）

至少发起 3 个训练任务，要求：

1. 至少 2 个任务同时处于 running。
2. 第 3 个任务进入 queued。
3. 当 running 任务完成后，queued 任务自动转为 running。

可使用脚本或测试命令，示例：

```bash
python -m pytest apps/api/tests/test_training_queue_concurrency.py -v
```

### 6.2 队列长度一致性测试（必须）

验证 `running_count + queued_count` 与当前活跃任务总数一致。

```bash
python -m pytest apps/api/tests/test_queue_consistency.py -v
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

若有既有失败项，必须在汇报中明确“既有问题/本次新增问题”分界。

---

## 七、完成判定

以下条件全部满足才可宣称完成：

- [ ] 并发上限配置可见且生效
- [ ] 至少 2 个任务并发 running
- [ ] 队列任务可观测（位置、数量、状态）
- [ ] queue_position/running_count/queued_count 字段在 API 与前端均可见
- [ ] 状态语义一致（queued/running 无冲突）
- [ ] 并发 E2E 通过
- [ ] 队列长度一致性测试通过
- [ ] 前端 typecheck/build 通过
- [ ] 后端回归已执行并如实报告
- [ ] 提供 2 成功 + 1 队列转运行真实链路证据
- [ ] 未越界推进 P1-T10

---

## 八、Copilot 审核重点

1. 是否真实并发（时间重叠）而非串行快速完成伪并发。
2. 队列位置是否动态变化且有证据。
3. 统计字段是否与真实状态一致。
4. 前后端状态词与字段是否完全一致。
5. 汇报是否如实披露回归失败项。

---

## 九、风险提示

1. 并发提升可能放大资源争用（CPU/RAM），需限制上限并可配置。
2. 队列状态若更新不及时，前端可能显示抖动，需要节流与轮询策略。
3. 若使用外部队列中间件，状态源必须单一，避免前后端读到不同真相。

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T20-R-20260401-100809-p1-t09-concurrent-training-and-queue-visibility-report.md`

执行完成后必须按该命名提交统一证据汇报。

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 M7-T21 / P1-T10。
