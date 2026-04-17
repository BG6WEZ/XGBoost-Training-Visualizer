# M7-T37 任务单：M7-T36 审计修复（管理员用户界面与用户路由契约闭环）

任务编号: M7-T37  
时间戳: 20260409-142258  
所属计划: M7 / Audit Fix for P1-T15  
前置任务: M7-T36（审核未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T36-20260409-092707-p1-t15-login-and-user-management-simplified.md
- [ ] docs/tasks/M7/M7-T36-R-20260409-092707-p1-t15-login-and-user-management-simplified-report.md
- [ ] docs/specification/PROJECT_FUNCTIONAL_SPECIFICATION.md（重点阅读“模块八：用户管理（简化版）”与 6.1/6.2 API 设计）
- [ ] docs/design/references/PAGE_DESIGN_SPECIFICATIONS.md（重点阅读“登录页面”）

未完成上述预读，不得开始执行。

---

## 一、当前审核结论（必须先承认问题）

M7-T36 当前**不能判定为通过**。后端认证能力和 focused 测试已基本落地，但任务单要求的“管理员用户管理前端闭环”和“用户管理接口契约口径”尚未完成，且汇报结论与事实不一致。

### 阻断问题 1：管理员用户管理页未实现

任务单 M7-T36 第 4.4 明确要求前端至少补齐：

1. 登录页面 `/login`
2. 管理员用户管理页面 `/admin/users`
3. 管理员创建用户对话框
4. 禁用/启用与重置密码的最小确认交互

审计结果：

1. 路由文件当前只存在 `/login` 路由，未发现 `/admin/users` 路由。
2. 工作区内未发现管理员用户管理页面文件。
3. 汇报文档自己也明确写了“当前只实现了登录页面，未实现用户管理界面”。

因此，前端管理员用户管理闭环未完成。

### 阻断问题 2：用户管理接口路径与任务单契约不一致

任务单 M7-T36 的管理员接口要求为：

1. `GET /api/admin/users`
2. `POST /api/admin/users`
3. `PUT /api/admin/users/:id`
4. `DELETE /api/admin/users/:id` 或等价禁用接口
5. `POST /api/admin/users/:id/reset-password`

审计结果：

1. 当前实现使用的是 `/api/users` 前缀，而不是 `/api/admin/users`。
2. 前端 `usersApi`、后端路由和汇报证据都使用 `/api/users`。
3. 汇报未明确说明这是“等价实现”以及为何偏离任务单契约。

这意味着 schema/router/types/docs 的契约口径没有按任务单闭环。

### 阻断问题 3：汇报结论与未验证/未完成事实冲突

当前汇报同时出现以下冲突：

1. 结论区写“所有任务目标已完成”；
2. 但“未验证部分”与“风险与限制”中明确承认管理员用户管理界面未实现；
3. 仍建议继续下一任务。

这违反了诚实原则与文档一致性原则。

---

## 二、本轮修复目标

本轮**只修复 M7-T36 的审计阻断项**，不推进 P1-T16，不扩展复杂权限、OAuth、注册或多租户。

目标：

1. 实现管理员用户管理页 `/admin/users`。
2. 打通创建用户、查看用户、禁用/启用、重置密码的前端最小闭环。
3. 将用户管理接口契约对齐到 `/api/admin/users/**`，或做极小兼容迁移并在汇报中说明。
4. 重写 M7-T36 汇报，使其与实际实现、验证结果、未验证边界完全一致。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/routers/users.py
- apps/api/app/schemas/**（仅限用户管理相关 schema 的最小契约修正）
- apps/api/app/main.py
- apps/api/tests/**（仅限 auth/user/admin 相关测试）
- apps/web/src/lib/api.ts
- apps/web/src/router.tsx
- apps/web/src/pages/**（仅限管理员用户管理页）
- apps/web/src/components/**（仅限用户列表、创建用户对话框、禁用/启用、重置密码最小交互）
- apps/web/src/contexts/AuthContext.tsx（仅限为管理员页面接入所需的最小状态修正）
- docs/tasks/M7/M7-T36-R-20260409-092707-p1-t15-login-and-user-management-simplified-report.md
- docs/tasks/M7/M7-T37-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure.md
- docs/tasks/M7/M7-T37-R-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- OAuth、SSO、第三方登录
- 公开注册、邮箱验证码、复杂权限系统
- 与认证无关的数据集/训练/结果/导出/版本管理逻辑
- P1-T16 及后续技术债、SHAP、GPU、部署增强
- 无关页面大规模重构或视觉翻新

---

## 四、必须完成的修复项

### 4.1 管理员用户管理页闭环

必须新增并打通：

1. `/admin/users` 页面路由
2. 用户列表展示
3. 创建用户对话框或表单
4. 禁用/启用用户交互
5. 重置密码交互

要求：

1. 必须接真实后端，不得只做静态页面。
2. 普通用户不可进入该页面。
3. 管理员页面至少能完成一条“创建后列表可见”和一条“禁用/重置成功”的真实链路。

### 4.2 用户管理路由契约对齐

必须将管理员用户管理接口口径与任务单对齐到 `/api/admin/users/**`，至少包括：

1. 列表
2. 创建
3. 更新/禁用
4. 重置密码

可接受方案：

1. 直接改为 `/api/admin/users/**`；
2. 保留旧路径兼容，但新增规范路径，并在汇报中明确兼容策略。

不接受：

1. 继续只保留 `/api/users/**` 且不说明偏差；
2. 只改文档不改实现；
3. 只改前端路径导致后端测试或旧调用失效而不补证据。

### 4.3 focused 测试补齐

至少覆盖：

1. 管理员访问 `/api/admin/users` 成功
2. 普通用户访问 `/api/admin/users` 被拒绝
3. 创建用户成功
4. 禁用用户后状态变化正确
5. 重置密码成功

若保留旧路径兼容，也必须说明哪组测试覆盖新路径，哪组是兼容验证。

### 4.4 汇报修复

M7-T37 汇报必须：

1. 不再写“所有任务目标已完成”除非管理员页面和管理员接口契约都已闭环；
2. 明确列出真实执行命令和真实结果；
3. 区分已验证 / 未验证 / 风险与限制；
4. 不得再把“只实现登录页”包装成 P1-T15 已完成。

---

## 五、多角色协同执行要求（强制）

1. `Auth-Agent`：保持现有登录态和权限守卫不回退。
2. `Admin-User-Agent`：管理员用户管理接口契约对齐与权限校验。
3. `Frontend-Agent`：管理员用户管理页、创建/禁用/重置密码最小交互。
4. `QA-Agent`：focused 测试、前端门禁、真实链路证据采集。
5. `Reviewer-Agent`：检查汇报是否仍存在“未完成写成已完成”的问题。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端 focused 测试（必须）

建议命令：

```bash
cd apps/api
python -m pytest tests/ -k "auth or user or admin" -v --tb=short
```

必须明确体现新契约 `/api/admin/users/**` 已被覆盖。

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 最小真实链路证据（必须）

至少提供 3 组：

1. 管理员登录并访问 `/admin/users` 页面成功。
2. 创建用户后列表可见。
3. 禁用或重置密码链路成功。

每组证据必须包含：

1. 页面路径或请求路径
2. 请求参数或操作步骤
3. 响应关键字段或页面结果
4. 与任务目标的对应关系

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] `/admin/users` 页面已实现并接真实后端
- [ ] 管理员用户管理最小交互闭环可用
- [ ] `/api/admin/users/**` 契约已落地或有明确兼容说明
- [ ] 普通用户不可访问管理员页面和管理员接口
- [ ] 后端 focused 测试已执行
- [ ] 前端 typecheck/build 通过
- [ ] 至少 3 组真实链路证据完整
- [ ] M7-T36 汇报已修正且不再过度表述
- [ ] 未越界推进 P1-T16 或后续任务

---

## 八、Copilot 审核重点

1. 是否只是补了管理员页面 UI，但没有真实创建/禁用/重置链路。
2. 是否只在前端做了 `/admin/users` 页面，而后端仍未对齐 `/api/admin/users/**`。
3. 是否服务端权限仍只靠前端隐藏按钮。
4. 是否汇报继续把“部分认证能力”写成“P1-T15 全闭环完成”。

---

## 九、风险提示

1. 路由契约从 `/api/users` 迁移到 `/api/admin/users` 时，若兼容处理不清晰，容易引入前后端不一致。
2. 当前若未处理用户与实验归属关系，本轮仍只能完成认证与管理员管理，不代表资源级隔离完成。
3. 若管理员页面只做最小交互，后续仍可能需要补搜索、分页、批量操作，但这些不属于本轮范围。

---

## 十、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T37-R-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure-report.md

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T16 / M7-T38。