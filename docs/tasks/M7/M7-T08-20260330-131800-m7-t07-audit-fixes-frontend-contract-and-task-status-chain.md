# M7-T08 任务单：M7-T07 审核修复（前端契约与任务状态链路）

任务编号: M7-T08  
时间戳: 20260330-131800  
所属计划: P1-S1 / M7-T07 修复  
前置任务: M7-T07（审核结果：部分通过）  
优先级: 最高（阻断 M7-T09）

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T07-20260330-123500-p1-t03-frontend-preprocess-feature-task-chain.md
- [ ] docs/tasks/M7/M7-T07-R-20260330-123500-p1-t03-frontend-preprocess-feature-task-chain-report.md

未完成预读，不得开始开发。

---

## 一、审核结论摘要

M7-T07 判定为“部分通过”，前端构建与后端回归测试可通过，但存在 2 个阻断项，导致真实页面链路不可用：

1. **任务状态查询接口路径错误（阻断）**  
   前端使用 `/api/tasks/{task_id}`，后端实际为 `/api/datasets/tasks/{task_id}`，会导致状态轮询 404。

2. **任务提交请求体与后端契约不一致（阻断）**  
   前端提交体缺少 `dataset_id` + `config` 包装层，且策略枚举值使用旧值（如 `mean`、`label`、`day`），与后端当前枚举不匹配，实际会触发 422。

说明：`typecheck/build` 通过不代表运行时链路正确，必须以真实请求响应为准。

---

## 二、本任务目标

仅做 M7-T07 修复闭环，不做新功能扩展：

1. 修复前端 API 路径与请求体契约。
2. 修复前端默认值与可选值，确保与后端枚举一致。
3. 提供两条真实链路证据（preprocess / feature-engineering）及失败场景证据。
4. 保持现有页面功能不回退。

---

## 三、详细修复要求

### 修复 3.1：任务状态接口路径对齐

修改 `apps/web/src/lib/api.ts`：

- `getTask` 路径从：`/api/tasks/{task_id}`
- 改为：`/api/datasets/tasks/{task_id}`

验收：任务提交后，页面状态轮询不再因 404 中断。

### 修复 3.2：请求体结构与契约对齐

后端接口要求（已存在，不可改后端绕过）：

- `POST /api/datasets/{dataset_id}/preprocess` body 必须为：

```json
{
  "dataset_id": "<id>",
  "config": {
    "missing_value_strategy": "forward_fill|mean_fill|drop_rows",
    "encoding_strategy": "one_hot|label_encoding",
    "target_columns": ["..."]
  }
}
```

- `POST /api/datasets/{dataset_id}/feature-engineering` body 必须为：

```json
{
  "dataset_id": "<id>",
  "config": {
    "time_features": {"enabled": true, "column": "...", "features": ["hour|dayofweek|month|is_weekend"]},
    "lag_features": {"enabled": true, "columns": ["..."], "lags": [1,6,12,24]},
    "rolling_features": {"enabled": true, "columns": ["..."], "windows": [3,6,24]}
  }
}
```

要求：

- 前端类型定义和实际提交结构必须一致。
- 不得再提交裸 `config`。
- `dataset_id` 必须与 URL 参数一致。

### 修复 3.3：枚举值与默认值对齐

前端必须对齐后端枚举：

- 缺失值策略：`forward_fill` / `mean_fill` / `drop_rows`
- 编码策略：`one_hot` / `label_encoding`
- 时间特征：`hour` / `dayofweek` / `month` / `is_weekend`

要求：

- 页面下拉和默认值均不得出现后端不支持值（如 `mean`、`drop`、`label`、`day`、`week`、`year`、`quarter`）。
- 移除 `as any` 类型绕过写法。

### 修复 3.4：错误反馈与轮询稳定性

要求：

- 轮询失败（4xx/5xx）要有可见提示，不得仅 `console.error`。
- 任务提交失败需显示后端具体错误信息（字段级 detail）。
- 成功态显示关键摘要字段（至少 task_id + status + result 中一个稳定字段）。

---

## 四、范围边界

### 4.1 允许修改

- `apps/web/src/lib/api.ts`
- `apps/web/src/pages/DatasetDetailPage.tsx`
- `apps/web/src/components/` 下与任务表单/状态展示直接相关组件（若新增）
- 必要的前端类型定义

### 4.2 禁止修改

- 不得修改后端 router/schema/worker 以迁就前端错误请求
- 不得改动无关页面
- 不得引入新依赖来规避当前问题

---

## 五、协作要求（必须体现多角色协同）

需在汇报中明确以下角色产出（可由同一人承担多角色，但必须标注）：

- Frontend 角色：页面与交互修复
- Contract 角色：请求/响应契约对齐
- QA 角色：命令执行与证据采集
- Reviewer 角色：范围检查与验收项核对

---

## 六、必须提供的实测证据

### 6.1 前端质量门禁

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
```

### 6.2 后端回归

```bash
python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -v --tb=short
```

### 6.3 真实链路证据（必须）

至少提供 2 组真实链路，且每组都包含“请求体 + 响应体关键字段”：

1. preprocess 成功链路：请求 -> task_id -> 状态轮询到 completed/running
2. feature-engineering 成功链路：请求 -> task_id -> 状态轮询到 completed/running

并提供 1 组失败链路：

- 例如提交非法枚举值，返回 422，错误定位到具体字段

证据可用浏览器 Network 摘录或命令行调用结果，但必须包含真实字段值。

---

## 七、完成判定

以下全部满足才算完成：

- [ ] `getTask` 路径已与后端一致（`/api/datasets/tasks/{task_id}`）
- [ ] preprocess/feature-engineering 请求体与后端契约完全一致
- [ ] 前端枚举值与默认值全部对齐后端
- [ ] 轮询错误和提交错误均有可见反馈
- [ ] typecheck 与 build 通过
- [ ] 后端回归结果已如实贴出
- [ ] 2 条成功链路 + 1 条失败链路证据完整

---

## 八、Copilot 审核重点

1. 真实请求是否命中正确路径与正确 body 结构。
2. 是否消除 `any` 绕过与旧枚举值残留。
3. 报告中的链路证据是否可复核。
4. 是否出现越界修改后端代码。

---

## 九、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T08-R-20260330-131800-m7-t07-audit-fixes-frontend-contract-and-task-status-chain-report.md`

Trae 完成后必须按该命名提交汇报。
