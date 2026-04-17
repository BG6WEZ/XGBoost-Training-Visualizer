# M7-T60 任务单：P1-T14 审计修复（路由级强制改密防绕过）

任务编号: M7-T60  
时间戳: 20260413-164500  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-1 Task 1.4 Audit Fix  
前置任务: M7-T59（审核未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/planning/LAUNCH_DEVELOPMENT_PLAN.md（重点阅读 Task 1.4 / Task 1.5）
- [ ] docs/tasks/M7/M7-T58-20260413-160900-p1-t14-first-login-force-password-change.md
- [ ] docs/tasks/M7/M7-T59-20260413-162300-p1-t14-audit-fix-first-login-password-change-closure.md
- [ ] docs/tasks/M7/M7-T59-R-20260413-163500-p1-t14-audit-fix-report.md

未完成上述预读，不得开始执行。

---

## 一、当前审核结论（必须先承认问题）

M7-T59 仍不能判定为通过，当前不得进入 Task 1.5。

### 阻断问题：前端仍可绕过首次改密

当前实现虽然在登录页内显示强制改密表单，但路由层并未拦截 `must_change_password=true` 用户访问受保护页面。

审计事实：

1. [LoginPage.tsx](apps/web/src/pages/LoginPage.tsx#L23) 在登录后根据返回值决定是否显示改密表单；
2. [AuthContext.tsx](apps/web/src/contexts/AuthContext.tsx#L31) 会通过 `getMe()` 恢复用户；
3. 但 [router.tsx](apps/web/src/router.tsx#L13) 的 `ProtectedRoute` 仅检查 `isAuthenticated`，未检查 `mustChangePassword`；
4. 因此用户在 token 已建立后，仍可直接访问 `/`、`/assets/:id`、`/experiments` 等受保护页面，从而绕过“必须先改密”。

---

## 二、本轮修复目标

本轮只修复“路由级强制改密防绕过”这一阻断项，不推进 Task 1.5，不扩展密码强度策略。

本轮目标：

1. 在路由保护层强制拦截 `mustChangePassword=true` 用户访问业务页面。
2. 仅允许其停留在改密流程页面（或登录页强制改密态）。
3. 改密成功后才恢复正常路由访问权限。

---

## 三、范围边界

### 3.1 允许修改

- apps/web/src/router.tsx
- apps/web/src/pages/LoginPage.tsx
- apps/web/src/contexts/AuthContext.tsx
- apps/web/src/lib/api.ts（仅当类型字段需最小同步）
- apps/web/src/app/**（仅当最小路由承载页需要）
- docs/tasks/M7/M7-T60-20260413-164500-p1-t14-audit-fix-route-level-must-change-password-guard.md
- docs/tasks/M7/M7-T60-R-20260413-164500-p1-t14-audit-fix-route-level-must-change-password-guard-report.md（完成后生成）

### 3.2 禁止修改

- 后端 Token 黑名单 / Redis 吊销逻辑（Task 1.5）
- 密码强度策略、邮箱流程、找回密码
- 与认证无关业务模块
- 大规模 UI 重构

---

## 四、必须完成的修复项

### 4.1 路由级防绕过（强制）

必须满足：

1. 当 `mustChangePassword=true` 时，用户不能访问业务受保护路由；
2. 用户只能进入强制改密流程载体；
3. 手动输入 URL 不得绕过。

### 4.2 改密完成后的状态切换

必须满足：

1. 改密成功后，前端状态与路由守卫同步解除限制；
2. 刷新后通过 `getMe()` 获取 `must_change_password=false` 时，用户可正常进入业务页面。

### 4.3 负向证据（必须）

至少提供 1 组负向证据：

1. `mustChangePassword=true` 的用户尝试访问 `/` 或其他业务页面，被强制留在改密流程；
2. 不允许仅凭文案说明，需要真实路径跳转或页面结果证据。

---

## 五、验证要求

### 5.1 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 5.2 后端回归（建议）

```bash
cd apps/api
python -m pytest tests/test_auth.py::TestMustChangePassword -v
python -m pytest tests/ -q --tb=short
```

### 5.3 真实链路证据（必须）

至少提供 3 组：

1. 首次登录进入强制改密流程；
2. 直接访问业务路由被拦截（负向证据）；
3. 改密成功后可进入业务路由。

---

## 六、完成判定

以下全部满足才可宣称完成并进入 Task 1.5：

- [ ] 路由级防绕过已落地
- [ ] `mustChangePassword=true` 时无法访问业务页面
- [ ] 改密成功后正常恢复访问
- [ ] 前端 typecheck/build 通过
- [ ] 至少 1 组负向证据 + 2 组正向证据完整
- [ ] 未越界推进 Task 1.5

---

## 七、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 Task 1.5。
