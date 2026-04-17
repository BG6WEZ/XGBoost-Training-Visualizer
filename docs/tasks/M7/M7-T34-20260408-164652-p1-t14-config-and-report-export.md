# M7-T34 任务单：P1-T14 配置/报告导出

任务编号: M7-T34  
时间戳: 20260408-164652  
所属计划: P1-S5 / P1-T14  
前置任务: M7-T33（审核通过后，P1-T13 闭环完成）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T14）
- [ ] docs/specification/PROJECT_FUNCTIONAL_SPECIFICATION.md（重点阅读“模型导出 / 训练报告 / 配置导出”）
- [ ] docs/architecture/TECHNICAL_ARCHITECTURE.md（重点阅读 `/api/results/{id}/export-report`）
- [ ] docs/design/UI_DESIGN_SPECIFICATION.md（重点阅读结果页导出入口相关设计）
- [ ] docs/tasks/M7/M7-T30-R-20260408-181730-p1-t13-model-version-management-report.md
- [ ] docs/tasks/M7/M7-T33-R-20260408-162408-m7-t32-audit-fixes-bind-worker-tests-to-production-implementation-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

P1-T13 模型版本管理完成后，P1-S5 的下一项是 P1-T14 配置/报告导出。

根据 roadmap 与规格文档，本轮目标是补齐两类导出能力：

1. 配置导出：支持将实验训练配置导出为 JSON / YAML；
2. 报告导出：支持导出训练报告，至少提供 HTML 或 PDF 中的一种真实可打开格式，另一种能力可做诚实降级但不得虚报完成。

本轮只做配置导出与训练报告导出，不推进认证、权限、SHAP、GPU、更多报表模板等后续任务。

---

## 二、任务目标

1. 提供实验配置导出接口，至少支持 JSON 与 YAML。
2. 提供训练报告导出接口，至少支持 HTML；若 PDF 也完成，可一并交付。
3. 前端结果页或实验详情页提供真实导出入口，不得仅保留静态按钮。
4. 导出文件可打开、字段完整、文件名和内容语义清晰。
5. 汇报必须提供真实导出证据，而不是仅展示字符串或 mock 片段。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/routers/**（仅限配置/报告导出相关接口）
- apps/api/app/schemas/**（仅限导出响应结构）
- apps/api/app/services/**（仅限配置序列化、报告生成）
- apps/api/tests/**（新增或修复导出相关测试）
- apps/web/src/lib/api.ts
- apps/web/src/pages/**（仅限实验详情页/结果页的导出入口）
- apps/web/src/components/**（仅限导出按钮、导出状态提示等最小组件）
- workspace/ 或 apps/api/workspace/ 下导出目录处理（仅限必要最小接入）
- docs/tasks/M7/M7-T34-20260408-164652-p1-t14-config-and-report-export.md
- docs/tasks/M7/M7-T34-R-20260408-164652-p1-t14-config-and-report-export-report.md
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- 登录、用户、认证、权限控制
- SHAP 分析、GPU、部署、版本治理增强
- 无关页面大规模重构或视觉翻新
- 未说明的大范围存储架构重写

---

## 四、详细交付要求

### 4.1 配置导出

至少支持：

1. 导出实验配置为 JSON；
2. 导出实验配置为 YAML；
3. 导出内容至少包含：
   - experiment_id
   - experiment_name
   - dataset_id
   - task_type
   - xgboost_params
   - 其他训练配置字段（若存在）

要求：

1. 字段命名必须与当前实验配置契约一致；
2. 不得导出不存在或历史残留字段；
3. 文件内容应可被常见工具直接打开；
4. YAML 若未引入外部依赖，需说明生成策略与限制。

### 4.2 训练报告导出

至少支持：

1. HTML 训练报告导出；
2. 报告包含至少以下信息：
   - 实验基本信息
   - 训练配置摘要
   - 关键指标（RMSE / R2 / MAE 中已有项）
   - 训练时间或完成时间
   - 模型版本信息（若存在）

如果实现 PDF：

1. 必须提供真实可打开文件证据；
2. 若只是 HTML 包装或浏览器打印方案，需如实说明语义边界。

要求：

1. 不接受返回纯 JSON 却命名为 report；
2. 不接受空白 HTML / 占位模板；
3. 不接受只给下载路由但未生成真实文件或响应内容。

### 4.3 前端导出入口

至少补齐：

1. 配置导出入口；
2. 报告导出入口；
3. 失败提示或禁用态；
4. 与真实后端接口对接。

要求：

1. 不得只保留静态按钮；
2. 不得破坏现有下载模型、版本管理、预测分析链路；
3. 若导出需要 query 参数或格式选择，前后端契约必须一致。

---

## 五、多角色协同执行要求（强制）

1. Export-Agent：设计配置与报告导出的文件结构、格式与命名。
2. API-Agent：实现导出接口、序列化和报告生成逻辑。
3. Frontend-Agent：实现真实导出入口、状态反馈与错误提示。
4. QA-Agent：提供文件结构校验与最小真实导出证据。
5. Reviewer-Agent：检查是否存在“伪导出”或过度表述。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端 focused 测试（必须）

至少覆盖：

1. JSON 配置导出结构正确；
2. YAML 配置导出结构正确；
3. HTML 或 PDF 报告导出返回可读内容；
4. 非法 experiment_id 或无结果实验的可读错误；
5. 导出响应头或文件命名符合预期。

建议命令：

```bash
cd apps/api
python -m pytest tests/ -k "export or report or config" -v --tb=short
```

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 最小真实链路证据（必须）

至少提供 3 组：

1. JSON 配置导出成功证据；
2. YAML 配置导出成功证据；
3. HTML 或 PDF 报告导出成功证据；

每组证据必须包含：

1. 页面路径或请求路径；
2. 请求参数或操作步骤；
3. 响应头、文件名、关键内容摘要；
4. 与任务目标的对应关系。

### 6.4 未验证边界（必须）

若未验证浏览器真实下载、PDF 打印兼容性、跨平台打开效果等，必须明确写入“未验证部分”，不得包装成已完成。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] JSON 配置导出可用
- [ ] YAML 配置导出可用
- [ ] HTML 或 PDF 报告导出可用
- [ ] 导出文件可打开且字段完整
- [ ] 前端导出入口接入真实后端
- [ ] 后端 focused 测试已执行
- [ ] 前端 typecheck/build 通过
- [ ] 至少 3 组真实导出证据完整
- [ ] 未越界推进 P1-T15 或后续任务

---

## 八、Copilot 审核重点

1. 是否只是返回字符串/JSON，却宣称“报告导出已完成”。
2. 是否按钮存在但没有真实调用后端。
3. YAML / HTML / PDF 的 MIME 类型、文件名和内容是否匹配。
4. 是否把浏览器未验证、PDF 未真实打开的内容写成已验证通过。

---

## 九、风险提示

1. PDF 若依赖额外渲染库，可能带来环境依赖问题；若未引入，需诚实降级。
2. 导出内容如果直接绑定现有结果结构，后续结果 schema 变化会影响导出稳定性。
3. 若导出文件路径与工作区路径管理不清晰，可能出现覆盖或清理不一致问题。

---

## 十、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T34-R-20260408-164652-p1-t14-config-and-report-export-report.md

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T15 / M7-T35。