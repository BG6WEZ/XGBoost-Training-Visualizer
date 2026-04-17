# M7-T22 任务单：M7-T21 审计修复（汇报归档缺失 + 运行时并发证据与测试稳定性）

任务编号: M7-T22  
时间戳: 20260401-121329  
所属计划: M7-T21 审计修复轮  
前置任务: M7-T21（未通过，需补证据）  
优先级: 最高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T21-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure.md
- [ ] docs/planning/MILESTONE_TASK_REPORT_MAPPING.md（查看当前状态）

未完成上述预读，不得开始执行。

---

## 一、当前阻断结论（必须先修）

M7-T21 当前不能验收通过，阻断项如下：

1. 汇报文件未归档到约定路径
- 期望文件：
  - docs/tasks/M7/M7-T21-R-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure-report.md
- 审计检索结果：当前工作区不存在该文件。

2. 并发 E2E 无法在本地环境跑通
- `python -m pytest apps/api/tests/test_training_real_concurrency_e2e.py -q`
- 本地报错：Redis 连接拒绝（localhost:6379 不可达），无法形成可复核的真实并发证据。

3. 非 Redis 分支仍有测试代码缺陷
- 命令：
  - python -m pytest apps/api/tests/test_training_real_concurrency_e2e.py -q -k "not TestRealConcurrencyE2E"
- 结果：2 failed，错误为无事件循环下直接创建 `asyncio.Future()`。
- 说明：测试代码本身不稳定，影响证据可信度。

---

## 二、本轮修复目标

1. 补齐并归档 M7-T21 汇报文档到约定路径。
2. 修复并发测试代码稳定性，避免“无事件循环”错误。
3. 在可运行 Redis 的条件下提供真实并发链路证据。
4. 若环境无 Redis，明确给出“未验证”并提供替代方案与阻塞说明。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/tests/test_training_real_concurrency_e2e.py
- apps/api/tests/**（如拆分 runtime/integration 测试文件）
- apps/worker/app/main.py（仅当测试暴露真实并发链路问题时修复）
- docs/tasks/M7/M7-T21-R-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure-report.md（补归档）
- docs/tasks/M7/M7-T22-20260401-121329-m7-t21-audit-fixes-report-presence-and-runtime-test-stability.md
- docs/tasks/M7/M7-T22-R-20260401-121329-m7-t21-audit-fixes-report-presence-and-runtime-test-stability-report.md（完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- P1-T10 功能开发（图表/结果分析）
- 与并发队列无关的页面或接口
- 数据库迁移（除非先报批）

---

## 四、必须完成的修复项

### 4.1 汇报归档修复

- 将 M7-T21 汇报文档实际落盘到任务单指定路径。
- 汇报中必须包含：
  - 已完成项
  - 修改文件清单
  - 实际执行命令
  - 实际输出
  - 未验证项
  - 风险与限制

### 4.2 测试稳定性修复

修复 `test_training_real_concurrency_e2e.py` 的事件循环问题，避免同步测试直接 `asyncio.Future()` 抛错。

可接受修复方式：
- 使用 `asyncio.get_running_loop().create_future()` 且测试标记为 `@pytest.mark.asyncio`。
- 或在同步测试中改用普通占位对象，不依赖 event loop。

### 4.3 真实并发证据分层

将测试分为两层并明确标注：

1. `unit`（无需 Redis）：校验并发逻辑与状态机语义。
2. `integration/e2e`（依赖 Redis）：校验真实 running/queued 转移。

要求：
- 若 Redis 不可用，integration 测试应 skip 并在汇报写明阻塞。
- 不得把 unit 结果写成“真实并发 E2E 通过”。

### 4.4 证据真实性约束

必须给出至少一条真实状态时间序列样本（可来自测试日志）：

- T1: running=2, queued=1
- T2: running=2, queued=0（原 queued 转 running）

如果环境做不到，必须在“未验证部分”明确声明并给出下一步执行条件。

---

## 五、多角色协同执行要求（强制）

1. `QA-Agent`：修复测试稳定性，跑通可跑部分。
2. `Runtime-Agent`：负责 Redis 条件下并发证据采集。
3. `Governance-Agent`：核对汇报文件是否真实存在并匹配命名。
4. `Reviewer-Agent`：区分“真实 E2E 通过”与“环境阻塞未验证”。

---

## 六、必须提供的实测证据

### 6.1 测试稳定性

```bash
python -m pytest apps/api/tests/test_training_real_concurrency_e2e.py -q -k "not integration"
```

要求：不得出现“无事件循环”类错误。

### 6.2 Redis 集成（如环境可用）

```bash
python -m pytest apps/api/tests/test_training_real_concurrency_e2e.py -q -k "integration or RealConcurrencyE2E"
```

若 Redis 不可用：
- 输出连接失败证据
- 汇报标注“未验证”
- 给出在 Docker/本地 Redis 下的复跑命令

### 6.3 前端门禁（若涉及前端改动）

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
```

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] M7-T21 汇报文件已存在并可读
- [ ] 并发测试文件无事件循环基础错误
- [ ] unit 与 integration 证据分层清晰
- [ ] 未将 unit 结果冒充 E2E 结果
- [ ] Redis 不可用场景已如实标注未验证
- [ ] 若 Redis 可用，给出真实 running/queued 转移证据
- [ ] 映射表状态与事实一致

---

## 八、Copilot 审核重点

1. 文件是否真正存在（不是“口头已生成”）。
2. 测试是否稳定可复现（无环境外基础错误）。
3. 报告是否诚实区分“已验证/未验证”。
4. 是否仍存在把 mock 或 unit 结果写成 E2E 通过的情况。

---

## 九、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T22-R-20260401-121329-m7-t21-audit-fixes-report-presence-and-runtime-test-stability-report.md`

---

## 十、停点要求

本任务完成后停点，等待人工验收；未经确认不得推进 P1-T10 / M7-T23。
