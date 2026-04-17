# M7-T35 任务单：M7-T34 审计修复（导出契约与门禁闭环）

任务编号: M7-T35  
时间戳: 20260408-172358  
所属计划: M7 / Audit Fix for P1-T14  
前置任务: M7-T34（审核未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T34-20260408-164652-p1-t14-config-and-report-export.md
- [ ] docs/tasks/M7/M7-T34-R-20260408-164652-p1-t14-config-and-report-export-report.md
- [ ] apps/api/app/routers/export.py
- [ ] apps/api/tests/test_export.py
- [ ] apps/web/src/pages/ExperimentDetailPage.tsx
- [ ] apps/web/src/lib/api.ts

未完成上述预读，不得开始执行。

---

## 一、审计结论与问题定位

本轮复审确认：T34 当前不能通过，原因不是单一文档问题，而是同时存在后端门禁失败、导出契约缺口、报告内容缺口和前端交互缺口。

### 1.1 已确认阻塞问题

1. YAML 配置导出在当前环境下实际失败。
   复跑 `tests/test_export.py` 结果为 1 failed / 10 passed，失败点为 YAML 导出返回 500，而不是汇报中声称的 11 passed。

2. 配置导出结构未满足任务单最低字段要求。
   当前 JSON/YAML 导出内容缺少 `dataset_id` 顶层字段，也未将 `task_type` / `xgboost_params` 以任务单要求的方式稳定暴露为导出结构的一部分。

3. HTML 报告内容缺口。
   当前报告没有模型版本信息；同时也没有完成时间或训练时间字段，不满足任务单对报告内容的最低要求。

4. 前端导出入口缺少失败提示或禁用态。
   当前前端使用 `<a>` 直链方式触发下载；PDF 依赖缺失时会直接落到错误响应，未提供失败提示。与任务单要求不符。

5. 汇报与实测不一致。
   汇报声称 `11 passed`，但实际复跑结果为 `1 failed, 10 passed`，不符合诚实原则。

### 1.2 本轮目标

只修复以上 5 个已确认问题，不推进 P1-T15 或任何后续能力。

---

## 二、任务目标

1. 修复 YAML 配置导出，使 focused 测试在当前环境下通过，或将其改为符合任务单的诚实降级并同步修正测试与汇报。
2. 补齐配置导出字段，使导出结构满足任务单最低要求。
3. 补齐 HTML 报告中的模型版本信息与完成时间 / 训练时间信息。
4. 为前端导出入口补失败提示或禁用态，不能再仅靠裸 `<a>` 直链处理错误。
5. 重写 T34 汇报，使其与实际验证结果一致。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/routers/export.py
- apps/api/app/schemas/export.py
- apps/api/app/services/**（仅限导出相关逻辑，如抽取公共生成函数时）
- apps/api/tests/test_export.py
- apps/web/src/lib/api.ts
- apps/web/src/pages/ExperimentDetailPage.tsx
- apps/web/src/components/**（仅限导出错误提示、导出菜单最小交互）
- docs/tasks/M7/M7-T34-R-20260408-164652-p1-t14-config-and-report-export-report.md
- docs/tasks/M7/M7-T35-20260408-172358-m7-t34-audit-fixes-export-contract-and-gating-closure.md
- docs/tasks/M7/M7-T35-R-20260408-172358-m7-t34-audit-fixes-export-contract-and-gating-closure-report.md
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- 登录、用户、认证、权限
- SHAP、GPU、部署、版本治理增强
- 无关页面大规模重构
- 与导出无关的 results / versions / prediction-analysis 逻辑

---

## 四、详细修复要求

### 4.1 YAML 导出门禁修复

必须满足以下二选一，并在汇报中明确说明：

1. 在当前环境中让 YAML 导出真实可用，测试返回 200；
2. 若依赖不可用，则改成与 PDF 一样的诚实降级语义，并同步：
   - 接口返回可读错误；
   - 测试按真实行为断言；
   - 前端提供失败提示或禁用态；
   - 汇报如实说明“当前环境未完成 YAML 真实导出”。

不允许：

1. 测试仍断言 200，但实际返回 500；
2. 汇报继续写“11 passed”。

### 4.2 配置导出契约修复

配置导出内容至少必须稳定包含：

1. `experiment_id`
2. `experiment_name`
3. `dataset_id`
4. `task_type`
5. `xgboost_params`

要求：

1. 可在顶层或清晰结构化层级中暴露，但必须易于消费且在测试中显式断言；
2. JSON 与 YAML 两种导出结构必须一致；
3. 不得只把这些字段埋在任意深层而不声明契约。

### 4.3 HTML 报告内容修复

HTML 报告至少补齐：

1. 完成时间或训练时间；
2. 模型版本信息（若存在版本记录，应展示当前激活版本或版本摘要）；
3. 若不存在版本记录，需给出诚实的“暂无版本信息”提示。

要求：

1. 不得继续缺失版本信息却在汇报中写“已包含模型版本信息”；
2. 报告内容测试需新增对应断言。

### 4.4 前端导出交互修复

前端至少补齐以下之一：

1. 依赖缺失或导出失败时的错误提示；
2. 已知不可用格式（如当前环境 PDF/YAML 不可用）时的禁用态或明确说明。

要求：

1. 不得只保留裸 `<a>` 标签而没有任何错误处理；
2. 不得让用户点击后直接看到原始 JSON 错误页面却仍称“前端导出入口已完成”。

### 4.5 汇报修复

T35 汇报必须：

1. 列出真实执行命令；
2. 列出真实结果；
3. 区分已验证与未验证部分；
4. 明确说明 YAML / PDF 在当前环境中的真实状态；
5. 不得再写与实跑不一致的通过数。

---

## 五、多角色协同执行要求（强制）

1. Export-Agent：修复导出契约和内容结构。
2. API-Agent：修复 YAML/HTML 导出逻辑和错误语义。
3. Frontend-Agent：补导出失败提示或禁用态。
4. QA-Agent：修正 focused 测试并补导出字段/内容断言。
5. Reviewer-Agent：确保汇报与实测一致。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端 focused 测试（必须）

至少覆盖：

1. JSON 配置导出字段完整；
2. YAML 导出真实成功或诚实降级；
3. HTML 报告包含模型版本信息与完成时间/训练时间；
4. PDF 导出在当前环境下的真实行为；
5. 非法 experiment_id 的可读错误。

建议命令：

```bash
cd apps/api
python -m pytest tests/test_export.py -v --tb=short
```

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 最小真实链路证据（必须）

至少提供 3 组：

1. JSON 配置导出证据；
2. YAML 导出真实结果证据；
3. HTML 报告导出证据；

若 PDF 当前环境不可用，可把 PDF 作为补充证据，但必须体现真实失败语义。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] `tests/test_export.py` 在当前约定下通过
- [ ] 配置导出字段满足任务单最低要求
- [ ] HTML 报告包含模型版本信息和完成时间/训练时间
- [ ] 前端导出入口具备失败提示或禁用态
- [ ] T34 汇报与实测一致
- [ ] 前端 typecheck/build 通过
- [ ] 未越界推进 P1-T15 或后续任务

---

## 八、Copilot 审核重点

1. 是否把 YAML 失败继续包装成“已完成”。
2. 是否仍缺 `dataset_id` / `task_type` / `xgboost_params` 的明确导出契约。
3. 是否 HTML 报告仍无模型版本信息或完成时间。
4. 是否前端依然没有错误处理却继续宣称入口闭环。

---

## 九、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T35-R-20260408-172358-m7-t34-audit-fixes-export-contract-and-gating-closure-report.md

---

## 十、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T15 / M7-T36。