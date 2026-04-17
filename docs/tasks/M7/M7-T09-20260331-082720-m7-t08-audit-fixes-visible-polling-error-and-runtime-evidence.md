# M7-T09 任务单：M7-T08 审核修复（可见轮询错误与真实运行时证据）

任务编号: M7-T09  
时间戳: 20260331-082720  
所属计划: P1-S1 / M7-T08 修复  
前置任务: M7-T08（审核结果：部分通过）  
优先级: 最高（阻断 M7-T10）

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T08-20260330-131800-m7-t07-audit-fixes-frontend-contract-and-task-status-chain.md
- [ ] docs/tasks/M7/M7-T08-R-20260330-131800-m7-t07-audit-fixes-frontend-contract-and-task-status-chain-report.md

未完成上述预读，不得开始开发。

---

## 一、审核结论摘要

M7-T08 当前判定为部分通过。以下项目已通过：

1. getTask 路径已修正为 /api/datasets/tasks/{task_id}
2. preprocess 与 feature-engineering 的请求体结构已包含 dataset_id + config
3. 枚举值与默认值已对齐后端
4. 前端 typecheck/build 通过，后端回归 26/26 通过

仍有阻断项：

1. 轮询失败仅 console.error，未向用户提供可见错误提示
2. 汇报宣称已有 2 条成功链路 + 1 条失败链路完整证据，但文档内未贴真实请求/响应字段证据

---

## 二、本任务目标

仅做 M7-T08 审核修复闭环，不做新功能扩展：

1. 补齐轮询失败场景的可见反馈（不能只写日志）
2. 补齐真实运行时证据，确保结论可复核
3. 保持现有契约对齐成果不回退

---

## 三、详细修复要求

### 修复 3.1：轮询错误可见反馈

修改前端任务轮询逻辑（预处理与特征工程两条链路），要求：

1. 当 getTask 返回 4xx/5xx/网络异常时，页面必须展示可见错误信息
2. 错误文案必须包含后端 detail 或 HTTP 状态关键信息
3. 出现错误后应停止当前轮询，避免持续刷错
4. 不得只在控制台输出

验收标准：

- 预处理轮询错误有页面可见提示
- 特征工程轮询错误有页面可见提示
- 控制台可保留日志，但不能替代 UI 提示

### 修复 3.2：真实链路证据补齐（必须）

汇报中必须贴出可复核证据，至少包括：

1. preprocess 成功链路 1 条
2. feature-engineering 成功链路 1 条
3. 失败链路 1 条（非法枚举触发 422）

每条链路必须包含：

1. 请求 URL
2. 请求体关键字段（至少 dataset_id 与 config 关键字段）
3. 响应体关键字段（至少 task_id、status；失败场景含 detail 字段）
4. 状态轮询结果（成功链路至少到 running 或 completed）

证据可选来源：

1. 浏览器 Network 摘录（文字化）
2. 命令行 curl/Invoke-RestMethod 输出
3. 自动化 E2E 脚本输出

禁止仅写“已验证通过”而不贴字段值。

### 修复 3.3：回归与范围控制

要求：

1. 不得改后端 router/schema/worker 来迁就前端
2. 不得改动无关页面
3. 仅修复 M7-T08 剩余阻断项

---

## 四、范围边界

### 4.1 允许修改

- apps/web/src/pages/DatasetDetailPage.tsx
- apps/web/src/lib/api.ts（仅在错误信息结构化提取确有必要时）
- docs/tasks/M7/M7-T09-R-20260331-082720-m7-t08-audit-fixes-visible-polling-error-and-runtime-evidence-report.md

### 4.2 禁止修改

- apps/api/**（后端代码）
- apps/worker/**
- 与本任务无关的前端页面与组件

---

## 五、协作要求（必须体现多角色协同）

汇报中必须明确角色产出（可一人多角色，但必须逐项标注）：

- Frontend 角色：轮询错误提示与状态处理修复
- Contract 角色：确认请求与响应字段证据完整性
- QA 角色：执行命令与采集链路证据
- Reviewer 角色：范围检查与验收项核对

---

## 六、必须提供的实测证据

### 6.1 前端质量门禁

在项目根目录执行并贴出输出：

pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build

### 6.2 后端回归（防止误伤）

python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -v --tb=short

### 6.3 运行时链路证据（必须）

至少 2 条成功 + 1 条失败，且字段完整，包含：

- 请求 URL
- 请求体关键字段
- 响应关键字段
- 轮询状态结果或失败 detail

---

## 七、完成判定

以下全部满足才算完成：

- [ ] 预处理与特征工程轮询失败均有页面可见提示
- [ ] 轮询失败后可停止继续刷错
- [ ] 2 条成功链路 + 1 条失败链路证据字段完整可复核
- [ ] typecheck 与 build 通过
- [ ] 后端回归结果如实贴出
- [ ] 无后端越界修改

---

## 八、Copilot 审核重点

1. 是否仍存在仅 console.error 无 UI 提示的分支
2. 链路证据是否包含真实字段值，而非结论性描述
3. 是否出现范围漂移或后端越界改动

---

## 九、汇报文件命名

本任务预期汇报文件：

docs/tasks/M7/M7-T09-R-20260331-082720-m7-t08-audit-fixes-visible-polling-error-and-runtime-evidence-report.md

Trae 完成后必须按该命名提交汇报。
