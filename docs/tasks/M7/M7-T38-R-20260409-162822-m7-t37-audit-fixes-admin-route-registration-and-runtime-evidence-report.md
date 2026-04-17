# M7-T38 汇报：M7-T37 审计修复（管理员路由注册与运行态证据）

任务编号: M7-T38  
时间戳: 20260409-162822  
所属计划: M7 / Audit Fix for P1-T15  
前置任务: M7-T37（审核未通过）

---

## 已完成任务

### 1. 注册 /admin/users 路由

**问题：** `AdminUsersPage` 已创建但未在路由中注册。

**修复：** 在 `router.tsx` 中添加 `/admin/users` 路由，并创建 `AdminRoute` 组件进行管理员权限校验。

**修改文件：** `apps/web/src/router.tsx`

**新增内容：**
```typescript
import { AdminUsersPage } from './pages/AdminUsersPage'

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, isAdmin } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!isAdmin) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">需要管理员权限才能访问此页面</p>
      </div>
    )
  }

  return <>{children}</>
}

// 路由注册
<Route
  path="/admin/users"
  element={
    <AdminRoute>
      <AdminUsersPage />
    </AdminRoute>
  }
/>
```

---

### 2. 添加导航入口

**问题：** 管理员用户管理页面缺少导航入口。

**修复：** 在 `AppLayout.tsx` 中添加管理员导航区域和用户管理入口。

**修改文件：** `apps/web/src/components/layout/AppLayout.tsx`

**新增内容：**
```typescript
import { Users, LogOut } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

// 管理员导航项
const adminNavItems = [
  { path: '/admin/users', label: '用户管理', icon: Users },
]

// 侧边栏管理员区域
{isAdmin && (
  <>
    <div className="pt-4 pb-2">
      <span className="px-3 text-xs font-semibold text-gray-400 uppercase">
        管理员
      </span>
    </div>
    {adminNavItems.map((item) => (
      <Link key={item.path} to={item.path} ...>
        <Icon className="w-5 h-5" />
        <span>{item.label}</span>
      </Link>
    ))}
  </>
)}

// 顶部栏用户信息和登出按钮
<div className="flex items-center space-x-4">
  <div className="text-sm text-gray-600">
    <span className="font-medium">{user?.username}</span>
    <span className="mx-2 text-gray-300">|</span>
    <span className={`px-2 py-0.5 rounded text-xs ${
      isAdmin ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'
    }`}>
      {isAdmin ? '管理员' : '用户'}
    </span>
  </div>
  <button onClick={logout} ...>
    <LogOut className="w-4 h-4" />
    <span>登出</span>
  </button>
</div>
```

---

## 修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/web/src/router.tsx` | 注册 `/admin/users` 路由，添加 `AdminRoute` 组件 |
| `apps/web/src/components/layout/AppLayout.tsx` | 添加管理员导航入口、用户信息显示、登出按钮 |

---

## 实际验证

### 后端测试

**命令：**
```bash
cd apps/api
python -m pytest tests/test_auth.py -v --tb=short
```

**结果：**
```
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

============================= 17 passed in 2.11s ==============================
```

### 前端门禁

**命令：**
```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

**结果：**
- TypeScript 检查：通过（无错误）
- Build：成功（`✓ built in 6.64s`）

---

## 已验证证据（T38 范围）

### 证据 1：路由注册

**文件：** `apps/web/src/router.tsx`

**路由配置：**
```typescript
<Route
  path="/admin/users"
  element={
    <AdminRoute>
      <AdminUsersPage />
    </AdminRoute>
  }
/>
```

**权限校验：**
- `AdminRoute` 组件检查 `isAdmin` 状态
- 非管理员访问时显示"需要管理员权限才能访问此页面"

---

### 证据 2：导航入口

**文件：** `apps/web/src/components/layout/AppLayout.tsx`

**管理员导航区域：**
- 管理员可见"用户管理"导航项
- 导航项位于侧边栏底部，有"管理员"分组标题

**顶部栏用户信息：**
- 显示当前用户名
- 显示用户角色标签（管理员/用户）
- 登出按钮

---

### 证据 3：页面访问路径设计

**设计路径：**
1. 登录页面 `/login` → 输入 admin/admin123
2. 登录成功后跳转到首页 `/`
3. 侧边栏显示"管理员"区域和"用户管理"入口
4. 点击"用户管理" → 跳转到 `/admin/users`
5. 显示用户管理页面（用户列表、创建用户、禁用/启用、重置密码）

---

### 证据 4：前端 Build 输出

**Build 结果：**
```
✓ 2347 modules transformed.
dist/index.html                   0.82 kB │ gzip:   0.08 kB
dist/assets/index-DiwrgTda.js   733.77 kB │ gzip: 202.21 kB
✓ built in 6.64s
```

---

## 未验证部分

1. **浏览器真实运行态**
  - 本报告只验证了代码接线、focused 测试和前端门禁。
  - 未在真实浏览器中验证页面跳转和管理员链路。
  - localStorage 持久登录行为未验证。

2. **管理员页面交互**
   - 未验证创建用户弹窗的打开/关闭
   - 未验证禁用/启用用户的实时更新
   - 未验证重置密码的完整流程

3. **说明**
  - 上述浏览器运行态证据已在后续 T39 补齐。
  - 因此本报告不再把静态访问路径说明写成“真实运行态证据”。

---

## 风险与限制

1. **简化认证模式**
   - 当前使用简化认证，Token 无刷新机制
   - 过期后需要重新登录

2. **Fallback 安全性**
   - 当 bcrypt/jose 不可用时，使用 fallback 方案
   - Fallback 方案安全性较低

---

## 是否建议继续下一任务

**不建议继续**

**原因：**
1. T38 确实完成了路由注册、管理员导航入口和前端权限分流。
2. 但 T38 任务单要求的浏览器运行态证据在本报告范围内并未交付。
3. 因此 T38 不能单独作为放行依据，后续运行态证据与报告一致性修复已转入 T39。
