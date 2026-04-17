# M7-T07 任务单：P1-T03 前端预处理/特征工程任务链路接入

任务编号: M7-T07  
时间戳: 20260330-123500  
所属计划: P1-S1 / P1-T03  
前置任务: M7-T06 已审核通过后方可开始  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md
- [ ] docs/tasks/M7/M7-T06-R-20260330-120000-m7-t04-audit-fixes-and-evidence-closure-report.md

未完成预读，不得开始开发。

---

## 一、任务背景

M7-T03（特征工程后端）与 M7-T04/M7-T06（预处理能力与证据闭环）已完成并通过审核，但前端尚未提供完整操作入口，导致用户无法在数据集详情页完成以下闭环：

1. 配置并触发预处理任务。
2. 配置并触发特征工程任务。
3. 查询任务状态并看到结果摘要。

本任务用于打通数据集页面到异步任务状态的前端链路，形成可操作、可验证、可演示的 P1-T03 成果。

---

## 二、任务目标

完成以下端到端前端链路：

1. 在数据集详情页提供“预处理”和“特征工程”两个可用入口。
2. 前端调用现有 API：
   - `POST /api/datasets/{dataset_id}/preprocess`
   - `POST /api/datasets/{dataset_id}/feature-engineering`
   - `GET /api/datasets/tasks/{task_id}`
3. 提交后展示 `task_id`，并轮询任务状态（`queued/running/completed/failed`）。
4. 对成功和失败结果均给出清晰反馈（禁止静默失败）。

---

## 三、范围边界

### 3.1 允许修改

- `apps/web/src/lib/api.ts`
- `apps/web/src/pages/DatasetDetailPage.tsx`
- `apps/web/src/components/` 下新增或修改与任务表单/状态展示相关组件
- `apps/web/src/router.tsx`（仅当页面路由必须调整）
- 必要的类型定义与轻量工具函数

### 3.2 明确禁止

- 不得改动后端业务逻辑（router/worker）
- 不得扩展到多表 Join、质量评分、模型管理等后续任务
- 不得为“通过构建”删除现有页面功能
- 不得更改任务单范围外 UI 视觉体系

---

## 四、详细交付要求

### 4.1 API 客户端与类型契约补齐

在 `api.ts` 中补齐前端调用所需类型和方法，至少包含：

- 预处理请求类型（含 `missing_value_strategy`、`encoding_strategy`、`target_columns` 等）
- 特征工程请求类型（time/lag/rolling）
- 任务触发响应类型（含 `task_id`、`status`）
- 任务状态查询响应类型（含 `id`、`task_type`、`status`、`result`、`error_message`）

验收：页面调用不使用 `any` 拼接临时对象；关键字段均有类型约束。

### 4.2 数据集详情页接入两类任务入口

在 `DatasetDetailPage.tsx` 中新增两个操作区：

1. 预处理任务区
2. 特征工程任务区

每个区至少包含：

- 核心参数输入（不要求覆盖所有高级参数）
- 提交按钮
- 提交中禁用态与 loading 状态
- 提交成功后显示 `task_id`

验收：两个按钮都能真实触发 API 请求，返回结果可见。

### 4.3 任务状态轮询与结果反馈

要求：

- 以 `task_id` 为键轮询 `GET /api/datasets/tasks/{task_id}`
- 在 UI 展示状态流转（queued -> running -> completed/failed）
- `completed` 时显示结果摘要（如输出路径或摘要字段）
- `failed` 时展示可读错误信息（`error_message` 或后端 detail）

验收：必须有状态轮询逻辑，且非一次性“提交成功即完成”的伪状态。

### 4.4 错误处理与输入约束

要求：

- 对必填字段缺失给出前端阻断提示
- 对后端 4xx/5xx 错误展示明确文案
- 不得吞掉异常（例如 `catch` 后无提示）

验收：至少 1 个无效输入场景 + 1 个后端返回错误场景在汇报中有证据。

---

## 五、协作与执行方式（必须体现多角色协同）

本任务必须采用“内部多角色协同”执行并在汇报中明确分工，可按下列角色自组织：

- Frontend 角色：页面交互、状态渲染、表单约束
- Contract 角色：对齐 `api.ts` 与后端字段契约
- QA 角色：执行 typecheck/build/接口冒烟并记录证据
- Reviewer 角色：审查越界修改、校验验收项逐条闭环

要求：汇报中必须给出角色-产出映射，不接受“单段总结式汇报”。

---

## 六、必须提供的实测证据

### 6.1 前端质量门禁

在项目根目录执行并贴出真实输出：

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
```

### 6.2 后端契约回归（防止前端接入破坏现有能力）

```bash
python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -v --tb=short
```

要求：如测试未执行，必须标注“未验证”与阻塞原因，不得写“默认通过”。

### 6.3 真实链路证据（必须）

至少提供 2 组真实链路（每组都要有输入与输出）：

1. 预处理链路：提交参数 -> 返回 task_id -> 状态变化 -> 最终结果/错误
2. 特征工程链路：提交参数 -> 返回 task_id -> 状态变化 -> 最终结果/错误

证据可为：命令行调用输出、浏览器网络记录摘录、页面状态截图文字化说明（需包含关键字段值）。

---

## 七、完成判定

以下条件全部满足才算完成：

- [ ] 数据集详情页可触发预处理任务并展示 task_id
- [ ] 数据集详情页可触发特征工程任务并展示 task_id
- [ ] 两类任务均实现任务状态轮询（非伪完成）
- [ ] 成功/失败场景都有明确反馈文案
- [ ] 前端 typecheck 与 build 通过
- [ ] 后端回归测试结果如实记录
- [ ] 汇报体现多角色协同与统一证据闭环

---

## 八、Copilot 审核重点

1. 是否真实调用既有后端接口，而非本地 mock 自嗨。
2. 状态轮询是否可靠，是否处理 failed 分支。
3. API 字段与后端契约是否一致（尤其 `task_id`、`task_type`、`status`）。
4. 是否出现范围漂移（越界改后端、越界改其他页面）。
5. 汇报是否提供统一证据而非口头结论。

---

## 九、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T07-R-20260330-123500-p1-t03-frontend-preprocess-feature-task-chain-report.md`

Trae 完成后必须按该命名提交汇报。
