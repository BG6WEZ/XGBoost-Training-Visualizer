# M7-T39 汇报：M7-T38 审计修复（浏览器运行态证据与汇报一致性闭环）

任务编号: M7-T39  
时间戳: 20260409-165811  
所属计划: M7 / Audit Fix for P1-T15  
前置任务: M7-T38（审核未通过）

---

## 已完成任务

### 1. 浏览器运行态证据脚本

**实现内容：**
- 将根目录下 `test-playwright.mjs` 改为 T39 专用浏览器证据脚本。
- 脚本使用 Playwright 启动 Edge channel；若不可用则回退到默认 Chromium。
- 运行时自动保存截图和结构化 JSON 结果到 `docs/tasks/M7/evidence/t39/`。

**修改文件：** `test-playwright.mjs`

---

### 2. 管理员浏览器链路闭环

**已验证：**
- 管理员登录成功。
- 管理员通过侧边栏进入 `/admin/users`。
- 管理员创建普通用户成功，且列表中出现新用户。
- 管理员禁用用户成功，且列表状态更新为“禁用”。
- 管理员重置密码成功，且重置密码弹窗关闭。

**证据落盘：**
- `docs/tasks/M7/evidence/t39/01-admin-home.png`
- `docs/tasks/M7/evidence/t39/02-admin-users-page.png`
- `docs/tasks/M7/evidence/t39/03-create-user-modal.png`
- `docs/tasks/M7/evidence/t39/04-user-created-row.png`
- `docs/tasks/M7/evidence/t39/06-user-disabled-row.png`
- `docs/tasks/M7/evidence/t39/07-reset-password-modal.png`
- `docs/tasks/M7/evidence/t39/08-reset-password-complete.png`
- `docs/tasks/M7/evidence/t39/t39-playwright-results.json`

---

### 3. 普通用户负向访问证据

**已验证：**
- 用管理员创建的普通用户登录后，直接访问 `/admin/users`。
- 页面显示“需要管理员权限才能访问此页面”。

**证据落盘：**
- `docs/tasks/M7/evidence/t39/05-normal-user-blocked.png`
- `docs/tasks/M7/evidence/t39/t39-playwright-results.json`

---

### 4. 汇报一致性修复

**修复内容：**
- 修正 `M7-T37-R`，删除将“路由未注册”继续描述为当前代码事实的表述。
- 修正 `M7-T38-R`，不再把静态路径说明写成真实运行态证据，也不再提前给出放行结论。
- 新增 `M7-T39-R` 统一证据报告，集中记录本轮真实浏览器链路、focused 测试和前端门禁结果。

**修改文件：**
- `docs/tasks/M7/M7-T37-R-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure-report.md`
- `docs/tasks/M7/M7-T38-R-20260409-162822-m7-t37-audit-fixes-admin-route-registration-and-runtime-evidence-report.md`
- `docs/tasks/M7/M7-T39-R-20260409-165811-m7-t38-audit-fixes-browser-runtime-evidence-and-report-consistency-report.md`

---

## 修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `test-playwright.mjs` | 新增 T39 浏览器证据脚本，自动采集管理员/普通用户运行态证据 |
| `docs/tasks/M7/M7-T37-R-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure-report.md` | 修正过时路由事实和放行结论 |
| `docs/tasks/M7/M7-T38-R-20260409-162822-m7-t37-audit-fixes-admin-route-registration-and-runtime-evidence-report.md` | 修正证据边界与放行结论 |
| `docs/tasks/M7/M7-T39-R-20260409-165811-m7-t38-audit-fixes-browser-runtime-evidence-and-report-consistency-report.md` | 新增本轮统一证据汇报 |

---

## 实际验证

### 1. 浏览器运行态验证

**命令：**
```bash
cd <repo-root>
node test-playwright.mjs
```

**结果：**
```json
{
  "reportPath": "C:\\Users\\wangd\\project\\XGBoost Training Visualizer\\docs\\tasks\\M7\\evidence\\t39\\t39-playwright-results.json",
  "evidenceCount": 5
}
```

**说明：**
- 本轮运行态链路真实执行成功。
- 结果 JSON 中记录了 5 组结构化证据和 8 张截图路径。

### 2. 后端 focused 测试

**命令：**
```bash
cd apps/api
python -m pytest tests/test_auth.py -v --tb=short
```

**结果：**
```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\wangd\project\XGBoost Training Visualizer\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\wangd\project\XGBoost Training Visualizer\apps\api
configfile: pytest.ini
plugins: anyio-4.13.0, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 17 items

tests/test_auth.py::TestLogin::test_login_success PASSED                 [  5%]
tests/test_auth.py::TestLogin::test_login_wrong_password PASSED          [ 11%]
tests/test_auth.py::TestLogin::test_login_user_not_found PASSED          [ 17%]
tests/test_auth.py::TestLogin::test_login_disabled_user PASSED           [ 23%]
tests/test_auth.py::TestAuthMe::test_get_me_success PASSED               [ 29%]
tests/test_auth.py::TestAuthMe::test_get_me_no_token PASSED              [ 35%]
tests/test_auth.py::TestChangePassword::test_change_password_success PASSED [ 41%]
tests/test_auth.py::TestChangePassword::test_change_password_wrong_old PASSED [ 47%]
tests/test_auth.py::TestUserManagement::test_list_users_as_admin PASSED  [ 52%]
tests/test_auth.py::TestUserManagement::test_list_users_as_normal_user PASSED [ 58%]
tests/test_auth.py::TestUserManagement::test_create_user_success PASSED  [ 64%]
tests/test_auth.py::TestUserManagement::test_create_user_duplicate_username PASSED [ 70%]
tests/test_auth.py::TestUserManagement::test_disable_user PASSED         [ 76%]
tests/test_auth.py::TestUserManagement::test_cannot_disable_self PASSED  [ 82%]
tests/test_auth.py::TestUserManagement::test_reset_password PASSED       [ 88%]
tests/test_auth.py::TestUserManagement::test_generate_password PASSED    [ 94%]
tests/test_auth.py::TestLogout::test_logout_success PASSED               [100%]

============================= 17 passed in 1.43s ==============================
```

### 3. 前端门禁

**命令：**
```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

**结果：**
```text
> @xgboost-vis/web@1.0.0 build C:\Users\wangd\project\XGBoost Training Visualizer\apps\web
> tsc -b && vite build

vite v5.4.21 building for production...
✓ 2347 modules transformed.
dist/index.html                   0.82 kB │ gzip:   0.46 kB
dist/assets/index-BI8bOWKs.css   27.17 kB │ gzip:   5.15 kB
dist/assets/index-CXiekmd5.js   733.77 kB │ gzip: 202.21 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 6.35s
```

**说明：**
- `npx tsc --noEmit` 无错误输出。
- `pnpm build` 成功，仅有非阻断的 chunk size warning。

---

## 真实链路证据

### 证据 1：管理员登录并进入 `/admin/users`

**页面路径：** `/login` -> `/` -> `/admin/users`

**操作步骤：**
1. 使用管理员账号 `admin / admin123` 登录。
2. 在侧边栏点击“用户管理”。
3. 页面跳转到 `/admin/users` 并显示“用户管理”标题与用户列表。

**页面结果：**
- 页面显示用户列表与“创建用户”按钮。
- 截图文件：
  - `docs/tasks/M7/evidence/t39/01-admin-home.png`
  - `docs/tasks/M7/evidence/t39/02-admin-users-page.png`

**对应任务目标：**
- 证明管理员页面真实可达。

### 证据 2：管理员创建用户后列表可见

**页面路径：** `/admin/users`

**操作步骤：**
1. 点击“创建用户”。
2. 输入：
   - 用户名：`t39_user_1775725817917`
   - 密码：`T39User123!`
   - 角色：`user`
3. 提交创建。

**关键响应：**
```json
{
  "id": "f9fb9f12-4bfe-4471-ab7d-774740c408a0",
  "username": "t39_user_1775725817917",
  "role": "user",
  "status": "active",
  "created_at": "2026-04-09T09:10:20.724026",
  "last_login_at": null
}
```

**页面结果：**
- 用户列表出现新建用户行。
- 截图文件：
  - `docs/tasks/M7/evidence/t39/03-create-user-modal.png`
  - `docs/tasks/M7/evidence/t39/04-user-created-row.png`

**对应任务目标：**
- 证明创建用户链路真实打通。

### 证据 3：管理员禁用用户后页面状态更新

**页面路径：** `/admin/users`

**操作步骤：**
1. 管理员返回用户列表。
2. 点击新用户行的“禁用用户”按钮。

**关键响应：**
```json
{
  "id": "f9fb9f12-4bfe-4471-ab7d-774740c408a0",
  "username": "t39_user_1775725817917",
  "role": "user",
  "status": "disabled",
  "created_at": "2026-04-09T09:10:20.724026",
  "last_login_at": "2026-04-09T09:10:21.527693"
}
```

**页面结果：**
- 列表中的状态标签更新为“禁用”。
- 截图文件：
  - `docs/tasks/M7/evidence/t39/06-user-disabled-row.png`

**对应任务目标：**
- 证明禁用链路真实打通。

### 证据 4：管理员重置密码成功

**页面路径：** `/admin/users`

**操作步骤：**
1. 点击同一用户行的“重置密码”。
2. 在弹窗中输入新密码：`T39Reset456!`。
3. 提交重置。

**关键响应：**
```json
{
  "message": "密码重置成功"
}
```

**页面结果：**
- 重置密码弹窗关闭，页面保持可操作。
- 截图文件：
  - `docs/tasks/M7/evidence/t39/07-reset-password-modal.png`
  - `docs/tasks/M7/evidence/t39/08-reset-password-complete.png`

**对应任务目标：**
- 证明重置密码链路真实打通。

### 证据 5：普通用户访问管理员页面被拦截

**页面路径：** `/login` -> `/` -> `/admin/users`

**操作步骤：**
1. 使用新建普通用户 `t39_user_1775725817917 / T39User123!` 登录。
2. 直接访问 `/admin/users`。

**页面结果：**
- 页面显示“需要管理员权限才能访问此页面”。
- 截图文件：
  - `docs/tasks/M7/evidence/t39/05-normal-user-blocked.png`

**对应任务目标：**
- 证明普通用户不能正常访问管理员页面。

---

## 未验证部分

1. **浏览器刷新后的登录持久性**
   - 本轮未单独验证刷新页面后 `localStorage` 恢复登录态是否稳定。

2. **禁用后再次登录失败的浏览器链路**
   - 后端 focused 测试已覆盖禁用用户登录失败。
   - 但本轮未在浏览器里补跑“禁用后重新登录”的完整 UI 链路。

3. **跨标签页登出同步**
   - 未验证多标签页间的登出同步行为。

4. **完整生产部署安全性**
   - 本轮只验证简化版登录与管理员管理链路。
   - 未验证 HTTPS、CSRF、安全头或生产环境令牌治理。

---

## 风险与限制

1. **本轮使用本地 SQLite 运行时库**
   - 为了稳定采集浏览器证据，本轮 API 以独立 SQLite 文件启动。
   - 这不影响管理员链路本身，但不能替代生产数据库环境验证。

2. **简化认证边界仍然存在**
   - 当前仅完成“用户名密码登录 + 管理员用户管理”的简化版闭环。
   - 不代表资源级隔离、多租户、完整后台系统已完成。

3. **前端仅验证了核心管理动作**
   - 本轮已验证访问、创建、禁用、重置密码。
   - 未扩展分页、搜索、批量操作等后台增强能力。

---

## 是否建议继续下一任务

**建议继续**

**原因：**
1. `/admin/users` 已通过真实浏览器验证可访问。
2. 管理员创建用户、禁用用户、重置密码链路都已完成真实浏览器验证。
3. 普通用户访问管理员页面已完成负向验证。
4. 后端 focused 测试 17 项通过。
5. 前端 typecheck/build 通过。
6. T37/T38 报告中的过时事实与过早结论已修正。

---

## 结论

本轮 T39 已完成 T38 剩余阻断项，P1-T15 在“简化版登录与管理员用户管理”范围内可判定闭环完成。后续若继续推进，应进入 P1-T16 或新的独立任务，不应再回到 T37/T38 的旧结论口径。