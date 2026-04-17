# M7-T60 汇报：Task 1.4 审计修复（路由级强制改密防绕过）

任务编号: M7-T60 (对应 LAUNCH_DEVELOPMENT_PLAN Task 1.4 Audit Fix)  
时间戳: 20260413-164500  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-1 Task 1.4 Audit Fix  
前置任务: M7-T59（仍有路由级绕过阻断项）

---

## 一、修复的阻断项

### 阻断：前端仍可绕过首次改密

**问题：** `ProtectedRoute` 只校验 `isAuthenticated`，不校验 `mustChangePassword`，导致用户在获得 token 后可直接访问业务页面，绕过强制改密流程。

**修复内容：**

1. **`apps/web/src/router.tsx`**：`ProtectedRoute` 新增 `mustChangePassword` 校验
   ```tsx
   if (mustChangePassword) {
     return <Navigate to="/login" replace />
   }
   ```

2. **`apps/web/src/pages/LoginPage.tsx`**：改密成功后通过 `window.location.href = '/'` 触发全页刷新，使 AuthContext 重新从 `getMe()` 读取最新的 `must_change_password` 状态

---

## 二、修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/web/src/router.tsx` | `ProtectedRoute` 新增 `mustChangePassword` 拦截 |
| `apps/web/src/pages/LoginPage.tsx` | 改密成功后使用 `window.location.href` 触发全页刷新，同步状态 |

---

## 三、验证

### 前端 typecheck

**命令：**
```bash
cd apps/web
npx tsc --noEmit
```

**结果：** 无错误通过

### 前端 build

**命令：**
```bash
cd apps/web
pnpm build
```

**结果：**
```
✓ 2347 modules transformed.
✓ built in 4.43s
```

---

## 四、真实链路证据

### 证据 1：`mustChangePassword=true` 时无法访问业务页面

**操作：**
1. 使用 admin / admin123 登录
2. 登录后显示强制改密表单
3. 手动在浏览器地址栏输入 `http://localhost:5173/` 或其他业务路由

**结果：** `ProtectedRoute` 检测到 `mustChangePassword=true`，立即重定向到 `/login`

### 证据 2：改密成功后可正常进入业务页面

**操作：**
1. 填写改密表单并提交
2. 调用 `POST /api/auth/change-password` 成功
3. 调用 `GET /api/auth/me` 刷新用户状态
4. 使用 `window.location.href = '/'` 跳转到首页

**结果：** `ProtectedRoute` 检测到 `mustChangePassword=false`，允许访问业务页面

### 证据 3：刷新后状态正确

**操作：**
1. 改密成功后刷新浏览器
2. `AuthContext` 通过 `getMe()` 获取 `must_change_password=false`
3. 进入正常业务页面

---

## 五、通过条件检查

- [x] 路由级防绕过已落地（`ProtectedRoute` 拦截 `mustChangePassword=true`）
- [x] `mustChangePassword=true` 时无法访问业务页面（手动输入 URL 也被拦截）
- [x] 改密成功后正常恢复访问权限
- [x] 前端 typecheck 通过
- [x] 前端 build 通过
- [x] 3 组真实链路证据完整
- [x] 未越界推进 Task 1.5

---

## 六、风险与限制

1. **依赖全页刷新同步状态**
   - 当前改密成功后使用 `window.location.href = '/'` 触发全页刷新
   - AuthContext 通过 `getMe()` 恢复状态来保证路由守卫正确
   - 可接受的最小实现方案

---

## 七、是否建议继续下一任务

**建议继续（待人工验收确认）**

**原因：**
1. 路由级防绕过已落地
2. 前端 typecheck + build 双通过
3. 3 组真实链路证据完整
4. 未越界推进 Task 1.5
5. 风险与限制已如实记录