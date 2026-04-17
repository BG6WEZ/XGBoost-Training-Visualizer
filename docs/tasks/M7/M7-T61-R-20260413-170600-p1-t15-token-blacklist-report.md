# M7-T61 汇报：Task 1.5 Token 黑名单（简化版 Redis）

任务编号: M7-T61 (对应 LAUNCH_DEVELOPMENT_PLAN Task 1.5)  
时间戳: 20260413-170600  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-1 Task 1.5  
前置任务: M7-T60（路由级强制改密防绕过，已验收）

---

## 一、已完成任务

### 1. TokenBlacklist 类（含 Redis 降级）

**实现内容：**
- `apps/api/app/services/auth.py` 中新增 `TokenBlacklist` 类
- `_try_init_redis()`: 尝试连接 Redis，失败则记录 warning 并降级
- `revoke_token()`: 将 JTI 写入 Redis，TTL = token 剩余有效期
- `is_token_revoked()`: 检查 JTI 是否在黑名单中
- 全局实例 `token_blacklist`

### 2. create_access_token() 自动注入 JTI

**修改内容：**
- `create_access_token()` 中自动注入 `jti` claim（使用 `uuid4()`）

### 3. revoke_token() 函数

**新增内容：**
- 解析 JWT，提取 JTI 和 exp
- 调用 `token_blacklist.revoke_token()` 写入黑名单
- 容错处理：格式错误、过期 token 均不报错

### 4. get_current_user() 增加黑名单检查

**修改内容：**
- `apps/api/app/routers/auth.py` 中 `get_current_user()` 解码 token 后检查 JTI 是否在黑名单
- 若在黑名单，返回 401 "Token 已被吊销，请重新登录"

### 5. logout 端点调用 revoke_token

**修改内容：**
- `POST /api/auth/logout` 现在调用 `revoke_token()` 吊销当前 token
- 吊销失败不影响登出流程（容错设计）

### 6. 4 个单元测试

| 测试 | 状态 |
|------|------|
| `test_create_access_token_includes_jti` | ✅ PASSED |
| `test_logout_revokes_token` | ✅ PASSED |
| `test_logout_without_redis_degrades_gracefully` | ✅ PASSED |
| `test_revoked_token_rejected` | ✅ PASSED |

---

## 二、修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/api/app/services/auth.py` | 新增 TokenBlacklist 类、revoke_token 函数、修改 create_access_token 注入 JTI |
| `apps/api/app/routers/auth.py` | 修改 get_current_user 增加黑名单检查、修改 logout 端点调用 revoke_token |
| `apps/api/tests/test_auth.py` | 新增 TestTokenBlacklist 类（4 个测试） |

---

## 三、实际验证

### 新增测试

**命令：**
```bash
cd apps/api
python -m pytest tests/test_auth.py::TestTokenBlacklist -v
```

**结果：**
```
4 passed in 7.08s
```

### 全量后端测试

**命令：**
```bash
cd apps/api
python -m pytest tests/ -q --tb=short
```

**结果：**
```
349 passed, 9 skipped, 1 warning in 130.70s
```

**对比基线：** 345 passed → 349 passed（新增 4 个测试），0 failed

---

## 四、通过条件检查

- [x] JTI 自动注入（create_access_token 中自动注入）
- [x] logout 端点新增（POST /api/auth/logout 可调用，返回 {"message": "登出成功"}）
- [x] 黑名单检查（get_current_user 中检查 JTI 是否在黑名单）
- [x] Redis 降级（Redis 不可用时，logout 和 login 仍正常工作）
- [x] 测试 1 通过：test_create_access_token_includes_jti
- [x] 测试 2 通过：test_logout_revokes_token
- [x] 测试 3 通过：test_logout_without_redis_degrades_gracefully
- [x] 测试 4 通过：test_revoked_token_rejected
- [x] 全量测试通过（349 passed, 0 failed）
- [x] 未越界推进（未修改 CORS、密码强度等无关内容）

---

## 五、风险与限制

1. **Redis 依赖**
   - 若 Redis 配置不正确或宕机，黑名单检查自动降级为无检查
   - 测试环境中使用 Mock Redis 验证了黑名单逻辑
   - 生产环境必须配置 Redis 告警

2. **TTL 精度**
   - 黑名单 TTL 计算基于 Unix timestamp，精度为秒
   - Token 过期后 Redis 自动清理黑名单项

3. **仅登出端点吊销**
   - 当前仅 logout 时吊销 token
   - 改密、重置密码等场景未吊销旧 token（可在后续任务中补充）

---

## 六、是否建议继续下一任务

**建议继续**

**原因：**
1. 所有通过条件已验证（10/10 勾选）
2. 全量测试无回归（349 passed, 0 failed）
3. 未越界推进后续任务
4. 风险与限制已如实记录