# M7-T59 任务单：P1-T14 审计修复（首次登录改密闭环补齐）

任务编号: M7-T59  
时间戳: 20260413-162300  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-1 Task 1.4 Audit Fix  
前置任务: M7-T58（审核未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/planning/LAUNCH_DEVELOPMENT_PLAN.md（重点阅读 Task 1.4 / Task 1.5）
- [ ] docs/tasks/M7/M7-T58-20260413-160900-p1-t14-first-login-force-password-change.md
- [ ] docs/tasks/M7/M7-T58-R-20260413-160900-p1-t14-first-login-force-password-change-report.md

未完成上述预读，不得开始执行。

---

## 一、当前审核结论（必须先承认问题）

M7-T58 当前**不能判定为通过**，因此不得直接进入 Task 1.5。

### 阻断问题 1：数据库迁移未落地

Task 1.4 任务单明确要求：

1. 若数据库迁移由 SQL 文件管理，必须新增对应迁移文件。

当前审计结果：

1. `User` 模型已新增 `must_change_password` 字段；
2. 但 `apps/api/migrations/` 目录当前仍停在 `004_add_model_versions.sql`；
3. 未发现与 `must_change_password` 相关的新增 SQL 迁移文件。

这意味着：

1. 测试环境依赖 `Base.metadata.create_all()` 可以通过；
2. 真实已有数据库不会自动获得该字段；
3. 本轮不能宣称数据库层已闭环。

### 阻断问题 2：`/api/auth/me` 契约未同步

Task 1.4 要求 schema / response type / 前端类型最小同步。

当前审计结果：

1. 登录接口已返回 `must_change_password`；
2. 但 `GET /api/auth/me` 的 `UserResponse` 构造未传入该字段；
3. 由于 schema 中该字段默认值为 `False`，接口会把真实值静默覆盖成 `false`。

这意味着：

1. 登录响应与 `me` 响应对同一用户状态给出不同结果；
2. `schema/router` 契约未真正闭环；
3. 前端刷新后依赖 `getMe()` 时会丢失首次改密标记。

### 阻断问题 3：前端首次改密最小闭环未实现

Task 1.4 任务单的 4.4 明确要求前端必须进入强制改密流程，且不得允许用户跳过。

当前审计结果：

1. `LoginPage.tsx` 登录成功后直接 `navigate('/')`；
2. `AuthContext.tsx` 只保存登录返回的 user，不处理首次改密流程；
3. 前端代码中未发现 `must_change_password` 联动实现；
4. 当前汇报也明确写了“前端 LoginPage 和 AuthContext 联动需要适配”。

因此，Task 1.4 的“前端首次改密最小闭环”仍未完成。

---

## 二、本轮修复目标

本轮**只修复 M7-T58 的审计阻断项**，不推进 Task 1.5，不扩展 Token 黑名单、密码强度策略、找回密码或其他认证增强。

本轮目标：

1. 补齐 `must_change_password` 的数据库迁移文件。
2. 修复 `/api/auth/me` 与登录响应的字段契约不一致。
3. 打通前端首次登录强制改密最小闭环。
4. 重写 M7-T58 汇报，使其与真实实现和验证边界完全一致。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/models/models.py（仅当字段定义需最小补正时）
- apps/api/app/database.py（仅当默认管理员初始化逻辑需最小补正时）
- apps/api/app/routers/auth.py
- apps/api/app/schemas/auth.py
- apps/api/tests/test_auth.py
- apps/api/tests/conftest.py（仅当 fixture 需最小同步）
- apps/api/migrations/**（新增 Task 1.4 对应 SQL 迁移）
- apps/web/src/pages/LoginPage.tsx
- apps/web/src/contexts/AuthContext.tsx
- apps/web/src/lib/api.ts
- docs/tasks/M7/M7-T58-R-20260413-160900-p1-t14-first-login-force-password-change-report.md
- docs/tasks/M7/M7-T59-20260413-162300-p1-t14-audit-fix-first-login-password-change-closure.md
- docs/tasks/M7/M7-T59-R-20260413-162300-p1-t14-audit-fix-first-login-password-change-closure-report.md（完成后生成）

### 3.2 禁止修改

- Task 1.5 Token 黑名单 / Redis 吊销逻辑
- 新增复杂密码策略、邮箱验证、忘记密码、密码强度评分
- 与认证无关的数据集、训练、结果、导出、部署逻辑
- 无关页面大规模重构
- 任意超出 Task 1.4 审计修复范围的扩展开发

---

## 四、必须完成的修复项

### 4.1 数据库迁移闭环

必须完成：

1. 为 `must_change_password` 新增 SQL 迁移文件；
2. 迁移内容至少覆盖：新增字段、默认值、对已有数据的兼容处理；
3. 汇报中必须明确迁移文件路径。

不接受：

1. 只改 ORM 模型，不补迁移；
2. 只在汇报里写“需要迁移”，但仓库无实际文件。

### 4.2 `/api/auth/me` 契约修复

必须完成：

1. `GET /api/auth/me` 返回真实的 `must_change_password` 值；
2. 登录响应与 `me` 响应对同一用户字段保持一致；
3. 如有需要，补最小测试覆盖该接口行为。

### 4.3 前端首次改密最小闭环

必须完成：

1. 登录返回 `must_change_password=true` 时，前端不能直接把用户送入正常首页使用态；
2. 前端必须进入强制改密流程；
3. 改密成功后才进入正常登录完成态；
4. 刷新后若 `getMe()` 仍返回 `must_change_password=true`，前端状态不能丢失该约束。

可接受实现：

1. 登录页弹出强制改密表单；
2. 登录页进入必须完成的改密态；
3. 等价的最小内联闭环。

不接受：

1. 只显示提示，不阻止用户继续；
2. 登录后直接 `navigate('/')`；
3. 只存字段，不驱动真实改密接口。

---

## 五、测试与验证要求

### 5.1 后端验证（必须）

至少包含：

1. `TestMustChangePassword` focused 测试继续通过；
2. `/api/auth/me` 返回真实 `must_change_password` 的验证；
3. 全量后端测试回归验证。

建议命令：

```bash
cd apps/api
python -m pytest tests/test_auth.py -v --tb=short
python -m pytest tests/ -q --tb=short
```

### 5.2 前端验证（必须）

至少执行：

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

若有条件，补最小浏览器或页面级真实链路证据。

### 5.3 真实链路证据（必须）

至少给出以下 3 组：

1. 默认 admin 首次登录后前端进入强制改密流程；
2. `/api/auth/me` 返回 `must_change_password=true` 的真实证据；
3. 改密成功后再次登录或刷新会话返回 `must_change_password=false`。

---

## 六、完成判定

以下全部满足才可宣称完成：

- [ ] 已新增并落地 Task 1.4 对应 SQL 迁移文件
- [ ] `/api/auth/me` 与登录响应对 `must_change_password` 契约一致
- [ ] 前端首次改密最小闭环可用且不能跳过
- [ ] 后端 focused 测试已执行并通过
- [ ] 全量后端测试无回归
- [ ] 前端 typecheck/build 通过
- [ ] 至少 3 组真实链路证据完整
- [ ] M7-T58 汇报已修正且不再过度表述
- [ ] 未越界推进 Task 1.5

---

## 七、多角色协作要求（强制）

1. `Backend-Agent`：迁移、接口契约、后端测试闭环。
2. `Frontend-Agent`：首次登录强制改密最小交互与状态流转闭环。
3. `QA-Agent`：focused 测试、全量回归、真实链路证据整理。
4. `Reviewer-Agent`：检查是否仍把“后端字段已加”误写成“Task 1.4 完成”。

允许单执行者分角色完成，但汇报必须按角色拆分产出与证据。

---

## 八、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 Task 1.5。
