# M7-T05 任务单：M7-T03 审核修复与证据闭环

任务编号: M7-T05  
时间戳: 20260330-113500  
前置任务: M7-T03（审核结果：部分通过）  
优先级: 最高（阻断 M7-T04）

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T03-20260330-112000-p1-t01-feature-engineering-backend-foundation.md
- [ ] docs/reports/M7-T03-R-20260330-112000-p1-t01-feature-engineering-backend-foundation-report.md

---

## 一、审核结论摘要

M7-T03 当前判定为“部分通过”，存在阻断项，暂不允许进入 M7-T04。

阻断原因：

1. 特征工程请求契约未实现有效约束校验，无法满足“非法配置返回 422 且指出具体字段”的要求。
2. 汇报未提交真实 API -> Worker -> 任务状态 -> 结果落盘的完整链路证据。
3. 汇报文件落点与任务单约定不一致（任务单要求 `docs/tasks/M7/...-report.md`，实际提交到 `docs/reports/...`）。

---

## 二、任务目标

本任务仅做 M7-T03 的闭环修复，不做 P1-T02 功能开发。

目标：

1. 修复请求契约校验缺口。
2. 补齐真实闭环执行证据。
3. 修复文档命名与归档一致性。
4. 输出可审计的通过/失败证据包。

---

## 三、必须修复项（全部必做）

### 任务 3.1：实现特征工程配置的严格校验

要求至少覆盖：

- `time_features.features` 仅允许 `hour`、`dayofweek`、`month`、`is_weekend`
- `lag_features.lags` 必须为正整数列表（禁止 0、负数、非整数）
- `rolling_features.windows` 必须为正整数列表（禁止 0、负数、非整数）
- 当启用某类特征时，对应 `column/columns` 必须提供且非空

验收标准：

- 非法请求返回 422
- 错误信息中可定位到字段（如 `time_features.features`）

### 任务 3.2：补齐真实闭环证据

必须提供一次完整链路证据（真实运行，不接受仅单测）：

1. 提交特征工程任务请求（含请求体）
2. 返回 `task_id`
3. 轮询任务状态直到 `completed`
4. 输出 `async_tasks.result` 中的路径与字段摘要
5. 证明输出文件在磁盘或存储中真实存在

证据必须包含：

- 请求参数
- `task_id`
- 状态变化（queued -> running -> completed）
- 输出文件路径
- 新增特征列表（或数量变化）

### 任务 3.3：补齐失败场景证据

至少提交 2 条失败请求示例（真实响应）：

1. 非法时间特征名（如 `day_of_week`）
2. 非法窗口值（如 `0` 或负数）

验收标准：

- 均返回 422
- 响应错误定位到具体字段

### 任务 3.4：修正文档归档路径一致性

将 M7-T03 汇报按任务单约定补档到：

- `docs/tasks/M7/M7-T03-R-20260330-112000-p1-t01-feature-engineering-backend-foundation-report.md`

说明：

- `docs/reports/` 下原文件可保留为历史副本，但必须说明“正式归档路径”
- 以任务单约定路径为审核依据

---

## 四、范围边界

### 4.1 允许修改

- `apps/api/app/schemas/dataset.py`
- `apps/api/app/routers/datasets.py`（如需补显式校验）
- `apps/api/tests/test_new_endpoints.py`
- `apps/api/tests/` 新增最小负向测试文件（如需要）
- `docs/tasks/M7/` 下对应汇报文件

### 4.2 禁止修改

- 不得提前实现 P1-T02 功能（缺失值策略、编码策略）
- 不得修改无关业务逻辑以掩盖测试失败
- 不得改写历史任务目标

---

## 五、必须提供的实测证据

### 5.1 自动化测试

至少执行并贴出完整输出：

```bash
cd apps/api
python -m pytest tests/test_new_endpoints.py --tb=short
```

若新增专用测试文件，必须一并执行。

### 5.2 真实接口验证

至少贴出以下证据（可用 curl 或等价工具）：

```bash
POST /api/datasets/{id}/feature-engineering
GET  /api/datasets/tasks/{task_id}
```

并附：

- 成功链路 1 条
- 失败链路 2 条（422）

---

## 六、完成判定

以下全部满足才算完成：

- [ ] 契约校验达到 422 约束要求
- [ ] 成功链路证据完整
- [ ] 失败链路证据完整
- [ ] 汇报归档路径符合任务单约定
- [ ] Copilot 复核通过

---

## 七、下一任务准入条件

仅当 M7-T05 审核通过，才允许进入：

- `docs/tasks/M7/M7-T04-20260330-112500-p1-t02-preprocessing-strategies-and-schema-alignment.md`

---

## 八、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T05-R-20260330-113500-m7-t03-audit-fixes-and-evidence-closure-report.md`

Trae 完成后按该命名提交。