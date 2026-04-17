# M7-T37 汇报：M7-T36 审计修复（管理员 UI 与路由契约闭环）

任务编号: M7-T37  
时间戳: 20260409-142258  
所属计划: M7 / Audit Fix for P1-T15  
前置任务: M7-T36（审核未通过）

---

## 已完成任务

### 1. 用户管理接口契约对齐

**问题：** 用户管理接口使用 `/api/users/**` 路径，未明确表示管理员专用。

**修复：** 将所有用户管理接口路径改为 `/api/admin/users/**`。

**修改文件：** `apps/api/app/routers/users.py`

**修改内容：**
```python
# 修复前
@router.get("/users", response_model=UserListResponse)
@router.post("/users", response_model=UserResponse)
@router.get("/users/{user_id}", response_model=UserResponse)
@router.patch("/users/{user_id}", response_model=UserResponse)
@router.post("/users/{user_id}/reset-password")
@router.post("/users/generate-password")

# 修复后
@router.get("/admin/users", response_model=UserListResponse)
@router.post("/admin/users", response_model=UserResponse)
@router.get("/admin/users/{user_id}", response_model=UserResponse)
@router.patch("/admin/users/{user_id}", response_model=UserResponse)
@router.post("/admin/users/{user_id}/reset-password")
@router.post("/admin/users/generate-password")
```

---

### 2. 前端 API 路径更新

**问题：** 前端 `usersApi` 使用旧路径 `/api/users/**`。

**修复：** 更新 `usersApi` 使用新路径 `/api/admin/users/**`。

**修改文件：** `apps/web/src/lib/api.ts`

**修改内容：**
```typescript
// 修复前
export const usersApi = {
  list: () => apiClient<UserListResponse>('/api/users'),
  get: (userId: string) => apiClient<UserResponse>(`/api/users/${userId}`),
  create: (data: UserCreateRequest) => apiClient<UserResponse>('/api/users', {...}),
  update: (userId: string, data: UserUpdateRequest) => apiClient<UserResponse>(`/api/users/${userId}`, {...}),
  resetPassword: (userId: string, data: PasswordResetRequest) => apiClient<{ message: string }>(`/api/users/${userId}/reset-password`, {...}),
  generatePassword: () => apiClient<{ password: string }>('/api/users/generate-password', {...}),
}

// 修复后
export const usersApi = {
  list: () => apiClient<UserListResponse>('/api/admin/users'),
  get: (userId: string) => apiClient<UserResponse>(`/api/admin/users/${userId}`),
  create: (data: UserCreateRequest) => apiClient<UserResponse>('/api/admin/users', {...}),
  update: (userId: string, data: UserUpdateRequest) => apiClient<UserResponse>(`/api/admin/users/${userId}`, {...}),
  resetPassword: (userId: string, data: PasswordResetRequest) => apiClient<{ message: string }>(`/api/admin/users/${userId}/reset-password`, {...}),
  generatePassword: () => apiClient<{ password: string }>('/api/admin/users/generate-password', {...}),
}
```

---

### 3. 管理员用户管理页面

**问题：** 缺少管理员用户管理前端界面。

**修复：** 创建 `AdminUsersPage.tsx` 页面，实现最小交互闭环。

**修改文件：** `apps/web/src/pages/AdminUsersPage.tsx`（新建）

**实现功能：**
- 用户列表展示（用户名、角色、状态、创建时间、最后登录）
- 创建用户弹窗（用户名、密码、角色选择）
- 禁用/启用用户按钮
- 重置密码弹窗（支持随机密码生成）
- 权限校验（非管理员显示权限提示）

---

### 4. 测试文件更新

**问题：** 测试使用旧路径 `/api/users/**`。

**修复：** 更新测试使用新路径 `/api/admin/users/**`。

**修改文件：** `apps/api/tests/test_auth.py`

**修改内容：**
```python
# 修复前
response = await client.get("/api/users", headers={...})
response = await client.post("/api/users", headers={...}, json={...})
response = await client.patch(f"/api/users/{normal_user.id}", headers={...}, json={...})
response = await client.post(f"/api/users/{normal_user.id}/reset-password", headers={...}, json={...})
response = await client.post("/api/users/generate-password", headers={...})

# 修复后
response = await client.get("/api/admin/users", headers={...})
response = await client.post("/api/admin/users", headers={...}, json={...})
response = await client.patch(f"/api/admin/users/{normal_user.id}", headers={...}, json={...})
response = await client.post(f"/api/admin/users/{normal_user.id}/reset-password", headers={...}, json={...})
response = await client.post("/api/admin/users/generate-password", headers={...})
```

---

## 修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/api/app/routers/users.py` | 路由路径改为 `/admin/users/**` |
| `apps/web/src/lib/api.ts` | 更新 `usersApi` 路径 |
| `apps/web/src/pages/AdminUsersPage.tsx` | 新建管理员用户管理页面 |
| `apps/api/tests/test_auth.py` | 更新测试路径 |

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

============================= 17 passed in 5.31s ==============================
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
- Build：成功（`✓ built in 5.55s`）

---

## 已验证证据（T37 范围）

### 证据 1：用户管理接口契约

**接口路径：** `/api/admin/users/**`

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/admin/users` | 获取用户列表 |
| POST | `/api/admin/users` | 创建用户 |
| GET | `/api/admin/users/{user_id}` | 获取用户详情 |
| PATCH | `/api/admin/users/{user_id}` | 更新用户状态/角色 |
| POST | `/api/admin/users/{user_id}/reset-password` | 重置用户密码 |
| POST | `/api/admin/users/generate-password` | 生成随机密码 |

**契约验证：** ✅ 所有接口使用 `/api/admin/users/**` 前缀，明确表示管理员专用

---

### 证据 2：管理员获取用户列表

**请求：** `GET /api/admin/users`

**请求头：**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应：**
```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "admin",
      "role": "admin",
      "status": "active",
      "created_at": "2026-04-09T09:30:00",
      "last_login_at": "2026-04-09T10:00:00"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "username": "researcher",
      "role": "user",
      "status": "active",
      "created_at": "2026-04-09T10:05:00",
      "last_login_at": null
    }
  ],
  "total": 2
}
```

---

### 证据 3：管理员创建用户

**请求：** `POST /api/admin/users`

**请求头：**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**请求体：**
```json
{
  "username": "newuser",
  "password": "randompass123",
  "role": "user"
}
```

**响应：**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "username": "newuser",
  "role": "user",
  "status": "active",
  "created_at": "2026-04-09T10:10:00",
  "last_login_at": null
}
```

---

### 证据 4：前端管理员用户管理页面组件

**实现功能：**
- 用户列表表格展示
- 创建用户弹窗（用户名、密码、角色选择）
- 禁用/启用用户按钮
- 重置密码弹窗（支持随机密码生成）
- 权限校验（非管理员显示权限提示）

---

## 未验证部分

1. **浏览器真实交互**
  - 本报告只验证了 API 契约、页面组件和 focused 测试。
  - 未在真实浏览器中验证用户管理页面交互。

2. **页面可达性与导航闭环**
  - T37 本身只完成页面组件创建，未提供 `/admin/users` 真实可达证据。
  - 路由注册、导航入口和页面运行态证据已在后续 T38/T39 继续闭环。

---

## 风险与限制

1. **T37 不是独立放行版本**
  - T37 解决了管理员用户管理 API 契约和页面组件缺口。
  - 但管理员页面真实可达性和浏览器运行态证据不在本报告验证范围内。

2. **当前仓库事实已前进**
  - 当前代码中 `/admin/users` 路由和管理员导航入口已在后续 T38 落地。
  - 因此本报告不再把“路由未注册”当作当前代码事实，而是把它视为 T37 当时尚未闭环的后续项。

---

## 是否建议继续下一任务

**不建议继续**

**原因：**
1. T37 只完成了管理员接口契约对齐、测试路径修正和页面组件实现。
2. `/admin/users` 的路由注册、导航入口和真实运行态证据在本报告内都没有闭环。
3. 因此 T37 不能作为 P1-T15 的独立验收通过依据，后续修复已转入 T38/T39。
