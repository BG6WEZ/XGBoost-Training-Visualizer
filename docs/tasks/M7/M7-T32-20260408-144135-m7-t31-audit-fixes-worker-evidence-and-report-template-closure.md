# M7-T32 任务单：M7-T31 审计修复（worker 自动建版本证据与汇报模板闭环）

任务编号: M7-T32  
时间戳: 20260408-144135  
所属计划: M7 / Audit Fix for P1-T13  
前置任务: M7-T31（审核未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T30-20260407-181730-p1-t13-model-version-management.md
- [ ] docs/tasks/M7/M7-T30-R-20260408-181730-p1-t13-model-version-management-report.md
- [ ] docs/tasks/M7/M7-T31-20260408-110531-m7-t30-audit-fixes-version-state-and-empty-state-closure.md
- [ ] docs/tasks/M7/M7-T31-R-20260408-110531-audit-fixes-report.md
- [ ] apps/worker/app/main.py
- [ ] apps/api/tests/test_model_versions.py
- [ ] apps/web/src/components/ModelVersionManager.tsx

未完成上述预读，不得开始执行。

---

## 一、审计结论与问题定位

本轮复审确认：

1. worker 时序修复已实际落地；
2. 前端无版本空状态已实际落地；
3. 后端 19 项测试与前端门禁可通过；
4. 但 T31 仍未完成“真实证明 worker 自动建版本”与“汇报模板闭环”这两项硬要求，因此当前仍不能判定 P1-T13 审核通过。

### 1.1 本轮未闭环问题

1. 所谓“自动创建版本 focused 测试”仍然主要是对 `/api/versions` 手动创建接口的调用，未直接覆盖 worker 训练完成链路。
2. T30 / T31 汇报仍未按模板提供：
   - 修改文件清单的完整目的说明
   - 实际执行命令
   - 实际结果
   - 未验证部分
   - 风险与限制
   - 是否建议继续下一任务
3. T31 所谓“真实链路证据”仍然主要是代码片段和静态流程说明，不是实际运行后的链路结果。

### 1.2 本轮目标

只修复以上两类问题：

1. 补 worker 自动建版本的 focused 真实测试/最小集成验证；
2. 将 T30/T31 汇报改写为符合模板、诚实且证据化的审计文档。

不得借此推进 P1-T14 或新增模型版本增强功能。

---

## 二、任务目标

1. 增加至少一组直接覆盖 worker 训练完成后自动创建版本的 focused 测试或最小集成验证。
2. 证明该链路下版本创建发生在 completed 语义之后，而不是仅证明手动创建接口可用。
3. 重写 T30 与 T31 汇报，使其完全符合阶段汇报模板。
4. 在汇报中明确区分已验证、未验证、风险与限制，不得继续使用代码片段冒充真实链路证据。

---

## 三、范围边界

### 3.1 允许修改

- apps/worker/app/main.py（仅当为补充可测试性所必需）
- apps/api/tests/test_model_versions.py
- apps/api/tests/**（仅限新增与 worker 自动建版本相关的 focused 测试）
- docs/tasks/M7/M7-T30-R-20260408-181730-p1-t13-model-version-management-report.md
- docs/tasks/M7/M7-T31-R-20260408-110531-audit-fixes-report.md
- docs/tasks/M7/M7-T32-20260408-144135-m7-t31-audit-fixes-worker-evidence-and-report-template-closure.md
- docs/tasks/M7/M7-T32-R-20260408-144135-m7-t31-audit-fixes-worker-evidence-and-report-template-closure-report.md
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/api/app/routers/versions.py（除非发现 worker 自动建版本闭环必须依赖接口修复，并需在汇报中说明）
- apps/web/src/components/ModelVersionManager.tsx（空状态已闭环，本轮非重点，除非发现回归）
- apps/api/app/models/**（无必要不得修改）
- P1-T14 及后续任务
- 导出、权限、部署、模型治理增强等后续能力

---

## 四、详细修复要求

### 4.1 worker 自动建版本证据闭环

必须满足以下至少一项，并优先选择自动化测试：

1. 新增 focused 测试，直接调用 worker 的训练完成保存链路，证明：
   - 训练结果保存后；
   - 实验状态更新为 completed；
   - 自动创建版本；
   - 且该版本为 active。
2. 若难以完整自动化，可做最小集成验证，但必须给出真实命令、操作步骤、输入、输出与关键字段。

要求：

1. 不接受仅通过 `client.post('/api/versions')` 的手动创建接口来证明“自动创建版本已验证”。
2. 测试名、汇报文字和证据必须明确区分：
   - 手动创建版本
   - 自动创建版本
3. 若只验证了 worker 内部函数而非完整训练队列链路，必须如实写明边界。

### 4.2 汇报模板闭环

T30 与 T31 汇报必须包含并明确拆分以下章节：

1. 已完成任务
2. 修改文件
3. 实际验证
4. 未验证部分
5. 风险与限制
6. 是否建议继续下一任务

要求：

1. “实际验证”必须列出真实执行命令和真实结果，不能只写“通过”。
2. “未验证部分”不能为空；如果确实全部验证，也要明确说明哪些高级链路仍未做全量回归。
3. “风险与限制”必须诚实列出当前仍存在的边界，例如未验证完整 worker+queue+UI 的端到端链路。
4. 不得再用代码摘录、函数流程图、静态片段替代真实链路证据。

### 4.3 真实链路证据要求

至少提供 3 组，其中必须包含：

1. worker 自动建版本的真实测试或最小集成证据；
2. 前端空状态的真实页面或组件结果证据；
3. 已有版本时版本列表/激活态/回滚之一的真实接口或页面结果证据。

证据必须包含：

1. 执行命令或操作步骤；
2. 输入参数；
3. 输出关键字段；
4. 与任务目标的对应关系。

---

## 五、多角色协同执行要求（强制）

1. Worker-Agent：补 worker 自动建版本可验证性与语义证明。
2. QA-Agent：设计 focused 测试或最小集成验证，明确自动链路与手动链路边界。
3. Reviewer-Agent：重写 T30/T31 汇报，确保满足模板与诚实原则。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端 focused 验证（必须）

至少执行一次明确覆盖 worker 自动建版本场景的 focused 验证。

建议命令示例：

```bash
cd apps/api
python -m pytest tests/test_model_versions.py -v --tb=short
```

如果自动建版本验证被拆到其他测试文件，也必须把对应命令与结果写入汇报。

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 汇报证据（必须）

T30 与 T31 两份汇报都必须按模板完整重写或补齐，不得只局部修改标题。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] 已有直接覆盖 worker 自动建版本的 focused 证据
- [ ] 自动链路与手动链路边界表述清晰
- [ ] T30 汇报已符合模板并包含真实执行命令/结果
- [ ] T31 汇报已符合模板并包含真实执行命令/结果
- [ ] 两份汇报均包含未验证部分与风险限制
- [ ] 前端 typecheck/build 通过
- [ ] 未越界推进 P1-T14 或后续任务

---

## 八、Copilot 审核重点

1. 是否仍拿手动创建接口测试冒充 worker 自动建版本验证。
2. 是否仍然没有“实际执行命令”和“实际结果”章节。
3. 是否继续把静态代码片段描述成真实链路证据。
4. 是否在未列清未验证边界时继续宣称“任务完成”。

---

## 九、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T32-R-20260408-144135-m7-t31-audit-fixes-worker-evidence-and-report-template-closure-report.md

---

## 十、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T14 / M7-T33。