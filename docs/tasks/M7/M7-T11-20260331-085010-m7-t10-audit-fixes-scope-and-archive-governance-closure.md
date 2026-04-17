# M7-T11 任务单：M7-T10 审核修复（范围约束与归档治理闭环）

任务编号: M7-T11  
时间戳: 20260331-085010  
所属计划: P1-S1 / M7-T10 修复  
前置任务: M7-T10（审核结果：部分通过）  
优先级: 高（阻断 M7-T12）

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T10-20260331-083728-m7-t09-audit-fixes-real-runtime-evidence-and-archive-path.md
- [ ] docs/reports/M7-T10-R-20260331-083728-m7-t09-audit-fixes-real-runtime-evidence-and-archive-path-report.md

未完成上述预读，不得开始执行。

---

## 一、审核结论摘要

M7-T10 当前判定为部分通过：

1. 已通过：真实运行时证据有效，2 条成功 + 1 条失败链路可复核。
2. 已通过：前端/后端门禁复核通过。
3. 阻断项：任务单写明“不得修改任何代码文件”，但实际新增了 `apps/api/scripts/collect_evidence.py`。
4. 阻断项：汇报中“无代码文件修改”结论与实际变更不一致。

---

## 二、本任务目标

仅做治理闭环，不做新功能开发：

1. 处理越界新增脚本与任务范围约束冲突。
2. 修正文档结论与事实不一致问题。
3. 完成正式归档与映射一致性。

---

## 三、详细修复要求

### 修复 3.1：范围约束冲突处理

二选一，必须明确采用哪种：

1. 方案 A（推荐）：删除 `apps/api/scripts/collect_evidence.py`，改为在汇报中贴出实际命令与原始输出，不保留脚本产物。
2. 方案 B：保留脚本，但需在汇报中明确“本任务发生代码变更（测试/证据脚本）”，并给出保留理由与后续维护责任。

验收：不得再出现“无代码修改”与事实冲突。

### 修复 3.2：汇报事实一致性修正

在 M7-T11 汇报中必须明确：

1. 真实变更文件清单（含新增/删除）。
2. 实际执行命令与关键输出摘要。
3. 与 M7-T10 的差异说明（修正了什么不一致）。

### 修复 3.3：归档一致性

本轮正式汇报文件使用以下路径：

- docs/tasks/M7/M7-T11-R-20260331-085010-m7-t10-audit-fixes-scope-and-archive-governance-closure-report.md

说明：

1. docs/reports 可保留历史副本。
2. docs/tasks/M7 为审核主依据。

---

## 四、范围边界

### 4.1 允许修改

- docs/tasks/M7/M7-T11-R-20260331-085010-m7-t10-audit-fixes-scope-and-archive-governance-closure-report.md
- docs/reports/M7-T10-R-20260331-083728-m7-t09-audit-fixes-real-runtime-evidence-and-archive-path-report.md（必要时追加勘误说明）
- apps/api/scripts/collect_evidence.py（仅用于删除或补充头部说明，禁止扩展业务逻辑）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md（由 Copilot 审核通过后更新）

### 4.2 禁止修改

- apps/web/**
- apps/api/app/**
- apps/worker/**
- 无关任务文档

---

## 五、必须提供的实测证据

### 5.1 证据复核命令

pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -v --tb=short

### 5.2 运行时链路引用

沿用 M7-T10 已采集的 2 成功 + 1 失败链路证据，且注明来源命令与执行时间。

---

## 六、完成判定

以下全部满足才算完成：

- [ ] 范围冲突已按 A/B 方案之一闭环
- [ ] 汇报中的“代码变更”描述与事实完全一致
- [ ] 正式汇报已归档到 docs/tasks/M7
- [ ] 复核门禁结果如实贴出

---

## 七、Copilot 审核重点

1. 事实一致性：文档结论是否与真实变更一致。
2. 范围收敛：是否仍存在越界文件变更。
3. 归档合规：是否按 docs/tasks/M7 形成正式记录。

---

## 八、汇报文件命名

本任务预期汇报文件：

docs/tasks/M7/M7-T11-R-20260331-085010-m7-t10-audit-fixes-scope-and-archive-governance-closure-report.md

Trae 完成后必须按该命名提交。
