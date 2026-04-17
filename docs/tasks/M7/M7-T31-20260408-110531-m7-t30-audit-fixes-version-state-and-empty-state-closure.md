# M7-T31 任务单：M7-T30 审计修复（版本创建时序与空状态闭环）

任务编号: M7-T31  
时间戳: 20260408-110531  
所属计划: M7 / Audit Fix for P1-T13  
前置任务: M7-T30（审核未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T30-20260407-181730-p1-t13-model-version-management.md
- [ ] docs/tasks/M7/M7-T30-R-20260408-181730-p1-t13-model-version-management-report.md
- [ ] apps/worker/app/main.py
- [ ] apps/web/src/components/ModelVersionManager.tsx
- [ ] apps/api/tests/test_model_versions.py

未完成上述预读，不得开始执行。

---

## 一、审计结论与问题定位

本轮审计确认：M7-T30 已完成模型版本管理的主体实现，且后端 focused 测试与前端门禁可通过；但仍存在 4 个未闭环问题，当前不能判定通过。

### 1.1 已确认问题

1. 自动版本创建时序不满足任务单要求。
   当前训练成功后先执行版本创建，再更新实验状态为 completed；而 M7-T30 明确要求“实验状态进入 completed 后创建版本”。

2. 前端无版本空状态未实现。
   当前组件在版本列表为空时直接 return null，没有“无版本时提示”，不满足前端最小交互要求。

3. 自动创建版本缺少 focused 实测闭环。
   当前 test_model_versions.py 主要覆盖手动创建、列表、比较、回滚、标签，没有直接证明训练完成链路会自动创建版本，也没有证明创建时实验状态已满足 completed 语义。

4. 汇报文档证据与结论存在过度表述。
   报告把测试代码片段写成“真实链路证据”，且在上述缺口仍存在时宣称“所有验收标准均已满足”。

### 1.2 本轮目标

只修复以上 4 个问题，使 P1-T13 在“自动建版本语义、前端空状态、测试证据、报告诚实性”四个维度全部闭环。

不得借此推进 P1-T14 或新增导出、权限、部署等后续功能。

---

## 二、任务目标

1. 调整自动版本创建时序，使其满足“实验状态进入 completed 后创建版本”或提供等价、可证明的完成态闭环。
2. 为模型版本管理补齐“无版本时提示”空状态。
3. 增补 focused 测试，证明训练完成链路会自动创建版本，且激活版本语义正确。
4. 重写汇报证据与结论，移除过度表述，真实区分“已验证”和“未验证”。

---

## 三、范围边界

### 3.1 允许修改

- apps/worker/app/main.py
- apps/api/tests/test_model_versions.py
- apps/api/tests/**（仅限为自动建版本补最小测试）
- apps/web/src/components/ModelVersionManager.tsx
- docs/tasks/M7/M7-T30-R-20260408-181730-p1-t13-model-version-management-report.md
- docs/tasks/M7/M7-T31-20260408-110531-m7-t30-audit-fixes-version-state-and-empty-state-closure.md
- docs/tasks/M7/M7-T31-R-20260408-110531-m7-t30-audit-fixes-version-state-and-empty-state-closure-report.md
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/api/app/routers/versions.py（除非为自动建版本闭环所必须，且需在汇报中说明原因）
- apps/api/app/models/**（除非发现严重模型定义错误；若无必要不得改）
- 与模型版本管理无关的实验筛选、Benchmark、预测分析逻辑
- P1-T14 及其后续任务
- 大规模页面重构或视觉翻新

---

## 四、详细修复要求

### 4.1 自动版本创建时序修复

必须满足以下之一，并在汇报中明确说明实现语义：

1. 先将实验状态持久化为 completed，再触发版本快照创建；
2. 或在同一完成态事务/流程中，能明确证明版本创建时实验已进入 completed 语义。

要求：

1. 不得继续保留“先建版本、后标 completed”却仍宣称满足任务单。
2. 若自动建版本失败，必须保留可审计日志/错误，不得静默吞掉。
3. 汇报必须明确“回滚只切换激活版本引用，不代表恢复完整训练环境”。

### 4.2 前端空状态修复

ModelVersionManager 必须在无版本时展示明确提示，至少包含：

1. 当前暂无模型版本；
2. 版本通常在训练完成后自动生成；
3. 不得直接 return null。

要求：

1. 空状态要接真实数据分支，不是静态占位。
2. 不得影响已有版本存在时的列表、比较、回滚交互。

### 4.3 focused 测试补齐

至少新增或补齐以下测试：

1. 训练完成链路触发后自动创建版本；
2. 自动创建版本后该版本为激活版本；
3. 自动创建链路下的 version_number、config_snapshot、metrics_snapshot 正确；
4. 若修复了空状态，需补最小前端逻辑验证或至少在汇报中提供真实页面结果证据。

要求：

1. 不接受只保留手动创建版本测试，却把自动创建写成“已验证”。
2. 如果前端没有自动化测试，必须在汇报中明确“未自动化验证”，并提供最小真实页面证据代替。

### 4.4 汇报修复

必须重写 M7-T30 汇报中的以下问题：

1. 不能再把测试代码片段当作“真实链路证据”；
2. 必须列出本轮实际执行的命令和实际结果；
3. 必须区分：
   - 已验证
   - 未验证
   - 风险与限制
4. 在未完成所有验收条件前，不得写“所有验收标准均已满足”。

---

## 五、多角色协同执行要求（强制）

1. Worker-Agent：修复训练完成与自动建版本的时序语义。
2. Frontend-Agent：补齐无版本空状态，不破坏已有交互。
3. QA-Agent：补自动建版本 focused 测试与验证证据。
4. Reviewer-Agent：检查报告是否仍有过度表述。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端 focused 测试（必须）

至少执行覆盖模型版本的 focused 测试，并明确包含自动创建版本场景。

建议命令：

```bash
cd apps/api
python -m pytest tests/test_model_versions.py -v --tb=short
```

如果自动创建版本拆到其他测试文件，也必须把对应命令和结果一并写入汇报。

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 最小真实链路证据（必须）

至少提供 3 组：

1. 一个训练完成后自动出现版本的链路证据；
2. 一个“无版本时空状态提示”的页面证据；
3. 一个已有版本时列表/激活态正常展示的页面或接口证据。

证据必须包含：

1. 页面路径或请求路径；
2. 操作步骤或请求参数；
3. 响应关键字段或页面关键结果；
4. 与本任务目标的对应关系。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] 自动版本创建时序已修复并与任务单语义一致
- [ ] 无版本空状态已实现，且不再 return null
- [ ] focused 测试已覆盖自动创建版本场景
- [ ] 前端 typecheck/build 通过
- [ ] 至少 3 组真实链路证据完整
- [ ] M7-T30 汇报已修正为诚实、证据化表述
- [ ] 未越界推进 P1-T14 或后续任务

---

## 八、Copilot 审核重点

1. 是否只是改了报告措辞，而没有修复自动建版本时序。
2. 是否只是保留空白区域，而没有真正展示无版本提示。
3. 是否仍然没有自动建版本 focused 测试，却继续宣称“已验证”。
4. 是否继续把测试代码片段或伪链路写成真实链路证据。

---

## 九、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T31-R-20260408-110531-m7-t30-audit-fixes-version-state-and-empty-state-closure-report.md

---

## 十、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T14 / M7-T32。