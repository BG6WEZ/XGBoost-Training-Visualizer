# M7-T33 任务单：M7-T32 审计修复（worker 测试必须绑定真实实现）

任务编号: M7-T33  
时间戳: 20260408-162408  
所属计划: M7 / Audit Fix for P1-T13  
前置任务: M7-T32（审核未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T32-20260408-144135-m7-t31-audit-fixes-worker-evidence-and-report-template-closure.md
- [ ] docs/tasks/M7/M7-T32-R-20260408-144135-m7-t31-audit-fixes-worker-evidence-and-report-template-closure-report.md
- [ ] apps/worker/app/main.py
- [ ] apps/api/tests/test_worker_auto_version.py

未完成上述预读，不得开始执行。

---

## 一、审计结论与问题定位

本轮复审确认：

1. T30 / T31 / T32 三份汇报的模板结构已经基本补齐；
2. 后端与前端门禁均可通过；
3. 但新增的 `apps/api/tests/test_worker_auto_version.py` 仍未真正绑定生产实现，当前不能作为“worker 自动建版本已验证”的有效证据。

### 1.1 唯一阻塞项

当前 `test_worker_auto_version.py` 在测试文件内部重新定义了一份 `_create_model_version`，而不是直接调用 `apps/worker/app/main.py` 中 `TrainingWorker._create_model_version` 的真实实现。

这意味着：

1. 测试验证的是“复制出来的一段近似逻辑”；
2. 不是生产代码本身；
3. 因而不能作为“真实 worker 自动建版本已验证”的审计证据。

本轮只修复这一个问题，不再扩展任何新功能。

---

## 二、任务目标

1. 将 worker 自动建版本测试改为直接绑定生产实现。
2. 测试必须明确验证 `apps/worker/app/main.py` 中 `TrainingWorker._create_model_version` 的真实行为。
3. 汇报中必须明确说明测试边界：
   - 是否只测 worker 内部方法；
   - 是否未覆盖 Redis 队列消费与完整训练链路。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/tests/test_worker_auto_version.py
- apps/worker/app/main.py（仅限为了提升可测试性做最小改动）
- docs/tasks/M7/M7-T32-R-20260408-144135-m7-t31-audit-fixes-worker-evidence-and-report-template-closure-report.md
- docs/tasks/M7/M7-T33-20260408-162408-m7-t32-audit-fixes-bind-worker-tests-to-production-implementation.md
- docs/tasks/M7/M7-T33-R-20260408-162408-m7-t32-audit-fixes-bind-worker-tests-to-production-implementation-report.md
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/api/app/routers/versions.py
- apps/web/src/**
- apps/api/app/models/**
- P1-T14 及后续任务
- 与模型版本管理无关的任何逻辑

---

## 四、详细修复要求

### 4.1 测试必须绑定真实生产实现

必须满足以下要求：

1. 测试中直接导入并调用 `TrainingWorker` 或其真实 `_create_model_version` 实现；
2. 不得在测试文件中复制一份 `_create_model_version` 作为替代；
3. 若需要构造最小 `db_session_maker` / worker 实例，可使用 mock 或最小测试支架，但核心待测逻辑必须来自生产代码。

允许的形式示例：

1. 实例化 `TrainingWorker`，注入测试数据库 session maker，再直接调用真实 `_create_model_version`；
2. 或通过真实 `save_training_result` / `process_training_task` 的最小可控路径触发版本创建。

不允许的形式：

1. 在测试文件内重新实现同名方法；
2. 复制生产逻辑后测复制版；
3. 把“结构相似”表述成“测试了真实 worker”。

### 4.2 测试覆盖要求

至少保留或补齐以下场景：

1. completed 状态下可创建版本；
2. 非 completed 状态下不创建版本；
3. 版本号递增；
4. 快照完整性；
5. 激活版本语义正确（如适用）。

### 4.3 汇报要求

M7-T33 汇报中必须明确写出：

1. 这次测试是否直接绑定 `TrainingWorker._create_model_version`；
2. 测试中 mock 了什么；
3. 没有 mock 什么；
4. 仍未覆盖哪些真实链路。

不得继续写“worker 自动建版本已验证”而不说明验证边界。

---

## 五、多角色协同执行要求（强制）

1. Worker-Agent：评估如何在最小改动下让真实 worker 实现可测试。
2. QA-Agent：将测试从“复制逻辑”改为“绑定真实实现”。
3. Reviewer-Agent：检查汇报措辞是否仍夸大测试覆盖面。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 worker focused 测试（必须）

至少执行一次新的 worker focused 测试文件，并证明它直接绑定真实实现。

建议命令：

```bash
cd apps/api
python -m pytest tests/test_worker_auto_version.py -v --tb=short
```

### 6.2 回归验证（建议）

```bash
cd apps/api
python -m pytest tests/test_model_versions.py -v --tb=short

cd apps/web
npx tsc --noEmit
pnpm build
```

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] `test_worker_auto_version.py` 已直接绑定生产实现
- [ ] 不再存在测试文件内复制版 `_create_model_version`
- [ ] worker focused 测试通过
- [ ] 汇报明确说明 mock 边界与未验证范围
- [ ] 未越界推进 P1-T14 或后续任务

---

## 八、Copilot 审核重点

1. 是否仍在测试文件里复制 worker 逻辑。
2. 是否虽然导入了 worker，但真正断言的仍不是生产方法结果。
3. 是否继续把“测试真实实现”写得比实际覆盖范围更大。

---

## 九、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T33-R-20260408-162408-m7-t32-audit-fixes-bind-worker-tests-to-production-implementation-report.md

---

## 十、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T14 / M7-T34。