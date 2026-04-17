# M7-T29 任务单：M7-T28 审计修复（标签录入契约与汇报闭环）

任务编号: M7-T29  
时间戳: 20260407-172708  
所属计划: M7-T28 审计修复轮  
前置任务: M7-T28（审核结果：部分通过，未闭环）  
优先级: 最高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T27-20260407-102026-p1-t12-experiment-tags-and-filtering.md
- [ ] docs/tasks/M7/M7-T27-R-20260407-102026-p1-t12-experiment-tags-and-filtering-report.md
- [ ] docs/tasks/M7/M7-T28-20260407-153706-m7-t27-audit-fixes-frontend-filter-ui-and-tag-contract-closure.md
- [ ] docs/tasks/M7/M7-T28-R-20260407-153706-m7-t27-audit-fixes-frontend-filter-ui-and-tag-contract-closure-report.md

未完成上述预读，不得开始执行。

---

## 一、当前审核结论（必须先承认剩余问题）

M7-T28 相比上一轮已有明显进展：

1. 前端实验列表已新增筛选面板；
2. 标签展示、清空筛选、筛选后空结果提示已存在；
3. 后端 `clean_tags` 已落地；
4. 重复失效测试文件 `apps/api/tests/test_experiment_tags.py` 已删除；
5. `tests/test_tags.py` 20 条 focused 测试通过，前端 typecheck/build 通过。

但当前**仍不能判定 M7-T28 完成闭环**，原因如下。

### 阻断问题 1：前端创建/更新标签契约没有真正闭环

任务单 P1-T12 明确要求：

1. 为实验增加标签能力，支持创建时或后续维护标签；
2. 前后端契约一致，标签字段命名统一、返回结构稳定。

本轮审计结果：

1. `apps/web/src/pages/ExperimentsPage.tsx` 已实现标签筛选与标签展示；
2. 但当前创建实验表单中**没有标签输入控件**；
3. 前端也未见“后续维护标签”的交互入口；
4. `apps/web/src/lib/api.ts` 中 `ExperimentCreateRequest` 仍未声明 `tags` 字段；
5. `experimentsApi.create` / `update` 虽然可发送对象，但其类型契约并未真正支持 `tags`。

这意味着当前系统虽然已有“标签展示”和“标签筛选”，但**前端未完成“创建时或后续维护标签”的闭环**。

### 阻断问题 2：M7-T27 / M7-T28 汇报仍有过度表述

当前重写后的汇报仍存在以下不严谨表述：

1. M7-T27 报告写“前端筛选界面已完成”，但未明确说明“标签录入/维护 UI 仍未覆盖”；
2. M7-T27 报告写“更新 `experimentsApi.create` 和 `update` 方法支持标签字段”，但前端请求类型 `ExperimentCreateRequest` 并未声明 `tags`；
3. M7-T28 报告写“标签契约闭环”，但从前端录入契约来看还未完全闭环。

这违反了文档一致性原则。只要“标签录入/维护能力”未闭环，就不能把 P1-T12 写成完全完成。

---

## 二、本轮修复目标

本轮**只做 M7-T28 的剩余审计修复闭环**，不推进 P1-T13，不扩展模型版本、回滚、认证或导出。

目标：

1. 补齐前端标签录入或维护能力，满足“创建时或后续维护标签”要求；
2. 修正前端请求类型契约，使 `ExperimentCreateRequest` / 更新请求与后端一致；
3. 补齐对应 focused 测试或最小链路证据；
4. 重写 M7-T27 / M7-T28 报告中剩余的过度表述。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/schemas/experiment.py
- apps/api/app/routers/experiments.py（仅当联调需要最小契约修正）
- apps/api/tests/**（仅限标签录入/更新相关测试）
- apps/web/src/lib/api.ts
- apps/web/src/pages/ExperimentsPage.tsx
- apps/web/src/components/**（仅限标签输入、编辑、展示相关最小组件）
- docs/tasks/M7/M7-T27-R-20260407-102026-p1-t12-experiment-tags-and-filtering-report.md
- docs/tasks/M7/M7-T28-R-20260407-153706-m7-t27-audit-fixes-frontend-filter-ui-and-tag-contract-closure-report.md
- docs/tasks/M7/M7-T29-20260407-172708-m7-t28-audit-fixes-tag-input-contract-and-report-closure.md
- docs/tasks/M7/M7-T29-R-20260407-172708-m7-t28-audit-fixes-tag-input-contract-and-report-closure-report.md（执行完成后生成）

### 3.2 禁止修改

- apps/worker/** 中训练调度、并发、Redis 队列相关逻辑
- P1-T13 及后续任务（模型版本管理、回滚、认证、导出）
- 无关页面大规模重构或视觉翻新
- 与标签/筛选无关的数据库迁移

---

## 四、必须完成的修复项

### 4.1 补齐标签录入或维护闭环

必须至少满足以下二选一之一，并以真实 UI 或真实接口链路给出证据：

1. **创建时录入标签**：在实验创建表单中加入标签输入，并真实提交到后端；
2. **后续维护标签**：在实验列表页或详情页提供标签编辑入口，并真实更新后端。

建议优先方案：

1. 在创建实验表单加入标签输入；
2. 允许逗号分隔输入；
3. 提交后由后端 `clean_tags` 清洗；
4. 创建结果在列表页可直接看到清洗后的标签。

### 4.2 修正前端请求类型契约

必须确保前端类型与后端一致：

1. `ExperimentCreateRequest` 应声明 `tags?: string[]` 或等价结构；
2. 更新请求的类型也应显式允许标签字段；
3. 不能再出现“方法实现可发 tags，但类型定义没有 tags”的不一致。

### 4.3 修正报告口径

`M7-T27-R` 和 `M7-T28-R` 都必须修正为：

1. 只写真实已完成能力；
2. 不再把“标签展示/筛选”扩大成“标签能力完全闭环”；
3. 只有在标签录入/维护链路真实打通后，才能写“P1-T12 完成闭环”。

---

## 五、多角色协同执行要求（强制）

1. `Frontend-Agent`：补齐创建或维护标签的真实交互。
2. `API-Agent`：核对创建/更新请求契约与后端 schema 一致。
3. `QA-Agent`：补齐 focused 测试和最小真实链路证据。
4. `Reviewer-Agent`：检查报告是否仍存在“已完成”过度表述。

汇报中必须按角色拆分产出，不接受只有最终摘要的写法。

---

## 六、必须提供的实测证据

### 6.1 后端/接口 focused 验证（必须）

至少提供一条创建或更新标签的真实链路，证明：

1. 前端提交了标签字段；
2. 后端返回清洗后的标签；
3. 列表页或详情页可读取该标签。

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 最小真实链路证据（必须）

至少 3 组：

1. 创建实验时录入标签，返回清洗后标签；
2. 列表页显示新录入的标签；
3. 用该标签进行筛选并返回正确结果。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] 前端已支持创建时录入标签或后续维护标签
- [ ] 前端请求类型契约与后端一致
- [ ] 标签录入、清洗、展示、筛选四条链路闭环
- [ ] 前端 typecheck/build 通过
- [ ] 至少 1 组 focused 验证已执行并通过或如实报告阻塞
- [ ] 至少 3 组真实链路证据完整
- [ ] M7-T27 / M7-T28 汇报已修正且不再过度表述
- [ ] 未越界推进 P1-T13 或后续任务

---

## 八、Copilot 审核重点

1. 是否只是补了类型，而没有真实标签录入交互。
2. 是否只是补了 UI 输入框，而没有真正提交到后端。
3. 创建请求类型和更新请求类型是否仍有 `tags` 漏口。
4. 汇报是否仍把“部分标签能力”写成“标签闭环全部完成”。

---

## 九、预期汇报文件

本任务预期汇报文件：

`docs/tasks/M7/M7-T29-R-20260407-172708-m7-t28-audit-fixes-tag-input-contract-and-report-closure-report.md`

---

## 十、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T13 / M7-T30。