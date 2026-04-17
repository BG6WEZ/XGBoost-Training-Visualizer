# M7-T58 汇报：Task 1.4 首次登录强制改密与默认密码标记

任务编号: M7-T58 (对应 LAUNCH_DEVELOPMENT_PLAN Task 1.4)  
时间戳: 20260413-160900  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-1 Task 1.4  
前置任务: M7-T56（Task 1.1 统一密钥管理）、M7-T57（Task 1.2 存储路径穿越防护）

---

## 已完成任务

### 1. 用户模型增加 must_change_password 字段

**实现内容：**
- `apps/api/app/models/models.py` 中 `User` 模型新增 `must_change_password = Column(Boolean, default=False)` 字段
- 默认值为 `False`，仅默认管理员账号初始化为 `True`

**修改文件：** `apps/api/app/models/models.py`

---

### 2. 默认管理员初始化标记

**实现内容：**
- `apps/api/app/database.py` 中 `init_db()` 创建默认 admin 时设置 `must_change_password=True`
- 确保首次启动系统时，默认 admin 必须修改密码

**修改文件：** `apps/api/app/database.py`

---

### 3. 登录响应返回改密标记

**实现内容：**
- `apps/api/app/schemas/auth.py` 中 `UserResponse` 增加 `must_change_password: bool = False` 字段
- `apps/api/app/routers/auth.py` 中登录接口返回该字段

**修改文件：** 
- `apps/api/app/schemas/auth.py`
- `apps/api/app/routers/auth.py`

---

### 4. 改密后清除标记

**实现内容：**
- `apps/api/app/routers/auth.py` 中 `change_password` 接口成功后将 `must_change_password` 设置为 `False`
- 确保改密后再次登录返回 `must_change_password=false`

**修改文件：** `apps/api/app/routers/auth.py`

---

### 5. 后端 focused 测试

**实现内容：**
- `test_admin_must_change_password_on_first_login`：默认 admin 首次登录返回 `must_change_password=true`
- `test_normal_user_no_must_change_password`：普通用户登录返回 `must_change_password=false`
- `test_change_password_clears_flag`：改密成功后再次登录返回 `must_change_password=false`

**修改文件：** `apps/api/tests/test_auth.py`

---

## 修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/api/app/models/models.py` | `User` 模型新增 `must_change_password` 字段 |
| `apps/api/app/database.py` | 默认 admin 初始化时设置 `must_change_password=True` |
| `apps/api/app/schemas/auth.py` | `UserResponse` 增加 `must_change_password` 字段 |
| `apps/api/app/routers/auth.py` | 登录响应返回该字段，改密接口清除该标记 |
| `apps/api/tests/test_auth.py` | 新增 `TestMustChangePassword` 类（3 个测试），admin_user fixture 增加字段 |

---

## 实际验证

### 新增测试

**命令：**
```bash
cd apps/api
python -m pytest tests/test_auth.py::TestMustChangePassword -v
```

**结果：**
```
tests/test_auth.py::TestMustChangePassword::test_admin_must_change_password_on_first_login PASSED [ 33%]
tests/test_auth.py::TestMustChangePassword::test_normal_user_no_must_change_password PASSED [ 66%]
tests/test_auth.py::TestMustChangePassword::test_change_password_clears_flag PASSED [100%]

======================= 3 passed in 3.12s =======================
```

### 全量后端测试回归验证

**命令：**
```bash
cd apps/api
python -m pytest tests/ -q --tb=short
```

**结果：**
```
345 passed, 9 skipped, 1 warning in 124.87s (0:02:04)
```

**对比基线：** 基线 336 passed → Task 1.1 后 338 → Task 1.2 后 342 → 当前 345 passed（新增 3 个测试），0 failed

---

## 真实链路证据

### 证据 1：默认 admin 首次登录

**请求：** `POST /api/auth/login`
**请求体：**
```json
{"username": "admin", "password": "admin123"}
```
**响应关键字段：**
```json
{
  "user": {
    "username": "admin",
    "must_change_password": true
  }
}
```
**对应目标：** 默认 admin 首次登录返回 `must_change_password=true`

### 证据 2：改密成功后再次登录

**操作：**
1. 使用首次登录的 token 调用 `POST /api/auth/change-password`
2. 改密成功后，使用新密码重新登录

**响应关键字段：**
```json
{
  "user": {
    "username": "admin",
    "must_change_password": false
  }
}
```
**对应目标：** 改密成功后再次登录返回 `must_change_password=false`

---

## 通过条件检查

- [x] `User` 模型已新增 `must_change_password` 字段且默认值正确（`False`）
- [x] 默认 admin 初始化为 `must_change_password: true`
- [x] 登录 API 返回 `must_change_password` 字段
- [x] 改密成功后会清除该标记
- [x] 后端 focused 测试已执行并通过（3 passed）
- [x] 全量测试无回归（345 passed, 0 failed）
- [x] 2 组真实链路证据完整
- [x] 未越界推进 Task 1.5

---

## 未验证部分

1. **前端首次改密最小闭环**
   - 后端接口和字段已完成，前端 LoginPage 和 AuthContext 需要适配
   - 建议在实际浏览器环境中验证登录→强制改密→正常使用的完整流程

---

## 风险与限制

1. **仅后端实现**
   - 当前仅完成后端接口和字段，前端联动（弹窗/页面态/内联表单）需要前端 Agent 适配
   - 用户通过 API 可以直接调用接口，不受前端限制

2. **无密码强度校验**
   - 改密接口不校验新密码强度，建议在后续任务中增加密码策略

---

## 是否建议继续下一任务

**建议继续**

**原因：**
1. 所有通过条件已验证（7/7 勾选）
2. 全量测试无回归（345 passed, 0 failed）
3. 未越界推进 Task 1.5 或其他后续任务
4. 风险与限制已如实记录
5. 前端联动部分可在后续任务中补充