# M7-T36 任务单：P1-T15 登录与用户管理（简化版）

任务编号: M7-T36  
时间戳: 20260409-092707  
所属计划: P1-S6 / P1-T15  
前置任务: M7-T35（已验收通过，P1-T14 导出闭环完成）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T15 条目）
- [ ] docs/tasks/M7/M7-T34-R-20260408-164652-p1-t14-config-and-report-export-report.md
- [ ] docs/tasks/M7/M7-T35-R-20260408-172358-m7-t34-audit-fixes-export-contract-and-gating-closure-report.md
- [ ] docs/specification/PROJECT_FUNCTIONAL_SPECIFICATION.md（重点阅读“模块八：用户管理（简化版）”与 6.1/6.2 API 设计）
- [ ] docs/design/references/PAGE_DESIGN_SPECIFICATIONS.md（重点阅读“登录页面”）

未完成上述预读，不得开始执行。

---

## 一、任务背景

P1-T14 已完成配置/报告导出闭环，当前系统已经具备：

1. 数据集、实验、结果分析、Benchmark、标签筛选、模型版本与导出能力。
2. 前后端已有相对完整的业务主链路，但仍处于“默认单团队、无登录隔离”的状态。
3. `PROJECT_FUNCTIONAL_SPECIFICATION` 已明确 P1-T15 采用**简化版用户管理**：管理员统一配置账号，无公开注册流程。

本轮目标不是做完整 IAM 或 OAuth，而是补齐最小可用的登录认证与管理员用户管理闭环，使系统具备基础账号边界和管理入口。

---

## 二、任务目标

1. 提供用户名/密码登录能力。
2. 提供当前用户信息接口与退出登录能力。
3. 提供管理员用户管理能力：查看用户、创建用户、禁用/启用账号、管理员重置密码。
4. 前端提供真实登录页与管理员用户管理页，不得只做静态页面。
5. 权限边界至少区分管理员与普通用户；管理员接口不可被普通用户访问。
6. 提供 focused 测试和真实链路证据，证明登录、用户创建、禁用、密码重置可用。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/models/**（仅限用户、认证、角色、状态相关模型）
- apps/api/app/schemas/**（仅限 auth/user 相关 schema）
- apps/api/app/routers/**（仅限 `/api/auth/**` 与 `/api/admin/users/**`）
- apps/api/app/services/**（仅限认证、密码哈希、用户管理、权限校验）
- apps/api/app/main.py（仅限注册认证/用户管理路由与中间件接入）
- apps/api/migrations/**（仅当落地用户表或字段必须新增迁移时允许）
- apps/api/tests/**（新增或修复认证/用户管理相关测试）
- apps/web/src/lib/api.ts
- apps/web/src/pages/**（仅限登录页、管理员用户管理页、最小路由守卫接入）
- apps/web/src/components/**（仅限登录表单、用户列表、创建用户对话框、重置密码确认等最小组件）
- docs/tasks/M7/M7-T36-20260409-092707-p1-t15-login-and-user-management-simplified.md
- docs/tasks/M7/M7-T36-R-20260409-092707-p1-t15-login-and-user-management-simplified-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- OAuth、SSO、第三方登录
- 公开注册、邮箱验证码、复杂权限系统
- 与认证无关的数据集/训练/结果/导出/版本管理逻辑
- P1-T16 及后续技术债、SHAP、GPU、部署增强
- 无关页面大规模重构或视觉翻新

---

## 四、详细交付要求

### 4.1 认证能力

至少补齐以下接口或等价实现：

1. `POST /api/auth/login`
2. `POST /api/auth/logout`
3. `GET /api/auth/me`
4. `POST /api/auth/change-password`

要求：

1. 登录必须校验用户名/密码，错误时返回可读错误，不得泄露敏感信息。
2. 登录成功后必须建立可持续的认证状态。
3. 认证状态可采用 session/cookie 或 token，但必须前后端一致，且在汇报中明确说明。
4. 禁用用户不得登录。

### 4.2 用户数据模型与权限语义

至少包含：

1. 用户名
2. 密码哈希
3. 角色（管理员 / 普通用户）
4. 启用状态
5. 创建时间

要求：

1. 不得存储明文密码。
2. 至少存在 2 类角色：`admin`、`user` 或等价语义。
3. 管理员接口必须有服务端权限校验，不能只靠前端隐藏按钮。

### 4.3 管理员用户管理能力

至少补齐以下接口或等价实现：

1. `GET /api/admin/users`
2. `POST /api/admin/users`
3. `PUT /api/admin/users/:id`
4. `DELETE /api/admin/users/:id` 或等价禁用接口
5. `POST /api/admin/users/:id/reset-password`

要求：

1. 创建用户时支持角色与启用状态设置。
2. 禁用用户后登录被阻断。
3. 管理员重置密码后，新密码链路可被 focused 验证。
4. 不要求实现复杂审计日志，但至少要保证返回结果与状态变更可复核。

### 4.4 前端页面与交互

至少补齐：

1. 登录页面 `/login`
2. 管理员用户管理页面 `/admin/users`
3. 登录失败错误提示
4. 登录中加载态
5. 管理员创建用户对话框
6. 禁用/启用与重置密码的最小确认交互

要求：

1. 不得只做静态 UI，必须接真实后端。
2. 普通用户不应看到管理员用户管理入口。
3. 当前用户信息应能驱动最小导航或权限显示。
4. 不得破坏现有业务主页面路由进入。

### 4.5 范围约束与诚实边界

本轮明确**不做**：

1. OAuth 登录
2. 公开注册
3. 邮件找回密码
4. 细粒度资源级 RBAC
5. 多租户隔离

汇报中必须明确写出上述未做项，避免将“简化版登录”表述为“完整认证系统”。

---

## 五、多角色协同执行要求（强制）

1. `Auth-Agent`：认证状态方案、密码哈希、登录/退出/me/change-password 设计。
2. `Admin-User-Agent`：管理员用户 CRUD、禁用/重置密码、角色边界。
3. `Frontend-Agent`：登录页、管理员用户管理页、最小路由守卫与状态反馈。
4. `QA-Agent`：focused 测试、权限负向测试、真实链路证据采集。
5. `Reviewer-Agent`：检查是否误把简化版认证写成完整认证系统，检查服务端权限是否真实生效。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端 focused 测试（必须）

至少覆盖：

1. 用户名密码登录成功
2. 错误密码登录失败
3. 禁用用户登录失败
4. `GET /api/auth/me` 返回当前用户信息
5. 管理员可创建用户
6. 普通用户访问管理员接口被拒绝
7. 管理员可禁用用户
8. 管理员可重置密码
9. 修改密码链路可用

建议命令：

```bash
cd apps/api
python -m pytest tests/ -k "auth or user or admin" -v --tb=short
```

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 最小真实链路证据（必须）

至少提供 3 组：

1. 登录成功链路：登录请求、认证状态建立、`/api/auth/me` 返回当前用户。
2. 管理员创建用户链路：创建后用户列表可见。
3. 禁用或重置密码链路：状态变化或新密码生效可复核。

证据必须包含：

1. 页面路径或请求路径
2. 请求参数或操作步骤
3. 响应关键字段或页面结果
4. 与任务目标的对应关系

### 6.4 未验证边界（必须）

若未验证浏览器刷新后的持久登录、跨标签页登出同步、生产部署安全头等，必须明确写入“未验证部分”，不得包装成已完成。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] 用户名/密码登录可用
- [ ] `login/logout/me/change-password` 闭环可用
- [ ] 管理员用户管理能力可用
- [ ] 禁用用户不可登录
- [ ] 普通用户不可访问管理员接口
- [ ] 前端登录页与管理员用户管理页接入真实后端
- [ ] 后端 focused 测试已执行
- [ ] 前端 typecheck/build 通过
- [ ] 至少 3 组真实链路证据完整
- [ ] 未越界推进 P1-T16 或后续任务

---

## 八、Copilot 审核重点

1. 是否只有前端登录页，没有真实服务端认证状态。
2. 是否只有前端隐藏管理员按钮，没有服务端权限校验。
3. 是否存储明文密码或将测试密码直接写入持久层。
4. 是否把简化版登录、管理员配号系统表述成完整认证平台。
5. 是否前端页面做了，但管理员创建/禁用/重置密码未真实打通。

---

## 九、风险提示

1. 认证状态方案若设计不清，后续路由守卫和管理员权限会反复返工。
2. 若用户模型与现有实验归属关系未处理，本轮可能只能先完成认证与用户管理，不做“用户只看自己实验”的严格隔离。
3. 密码重置若没有明确返回和操作约束，容易在汇报中夸大安全性，必须诚实说明边界。

---

## 十、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T36-R-20260409-092707-p1-t15-login-and-user-management-simplified-report.md

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T16 / M7-T37。