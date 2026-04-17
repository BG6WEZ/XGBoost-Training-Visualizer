# M7-T56 汇报：Task 1.1 统一密钥管理，移除所有硬编码 Secret

任务编号: M7-T56  
时间戳: 20260413-110000  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-1 Task 1.1  
前置任务: M7-T55（审核通过后，进入上线开发计划执行）

---

## 已完成任务

### 1. config.py — 密钥默认值改空 + 启动校验

**实现内容：**
- `JWT_SECRET` 默认值从 `"your-super-secret-jwt-key-change-in-production"` 改为 `""`
- `DATABASE_URL` 默认值从 `"postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis"` 改为 `""`
- 新增 `model_post_init()` 方法，启动时校验这两个变量非空，否则抛出 `ValueError`

**修改文件：** `apps/api/app/config.py`

---

### 2. auth.py — 移除硬编码 SECRET_KEY 和条件分支

**实现内容：**
- 删除 `SECRET_KEY = os.getenv("SECRET_KEY", "xgboost-visualizer-secret-key-2026")` 硬编码
- 移除 `BCRYPT_AVAILABLE` / `JOSE_AVAILABLE` 条件分支和 SHA256 fallback 逻辑
- `bcrypt` 和 `python-jose` 设为必须依赖（import 失败即启动失败）
- `create_access_token()` / `decode_access_token()` 统一从 `config.settings.JWT_SECRET` 读取
- 修复 `datetime.utcnow()` 废弃警告，改用 `datetime.now(timezone.utc)`

**修改文件：** `apps/api/app/services/auth.py`

---

### 3. conftest.py — 测试环境适配

**实现内容：**
- 添加 `JWT_SECRET` 测试环境变量 `os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-32chars")`

**修改文件：** `apps/api/tests/conftest.py`

---

### 4. test_auth.py — 新增启动校验测试

**实现内容：**
- `test_missing_jwt_secret_raises`：未设 JWT_SECRET 时启动应抛出 `ValueError`
- `test_missing_database_url_raises`：未设 DATABASE_URL 时启动应抛出 `ValueError`

**修改文件：** `apps/api/tests/test_auth.py`

---

### 5. .env.example — 完整版环境变量模板

**实现内容：**
- 重写 `.env.example` 文件，包含 15+ 环境变量，分类注释清晰
- 分类：必须配置、存储配置、MinIO、可选配置、开发环境相关

**修改文件：** `.env.example`

---

## 修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/api/app/config.py` | JWT_SECRET/DATABASE_URL 默认值改空，增加 model_post_init 校验 |
| `apps/api/app/services/auth.py` | 删除硬编码 SECRET_KEY，移除条件分支，统一从 config 读取 |
| `apps/api/tests/conftest.py` | 添加 JWT_SECRET 测试环境变量 |
| `apps/api/tests/test_auth.py` | 新增 TestJwtSecretValidation 类（2 个测试） |
| `.env.example` | 重写为完整版，包含 15+ 环境变量且有分类注释 |

---

## 实际验证

### 新增测试

**命令：**
```bash
cd apps/api
python -m pytest tests/test_auth.py::TestJwtSecretValidation -v
```

**结果：**
```
tests/test_auth.py::TestJwtSecretValidation::test_missing_jwt_secret_raises PASSED [ 50%]
tests/test_auth.py::TestJwtSecretValidation::test_missing_database_url_raises PASSED [100%]

=============================== 2 passed in 1.84s ================================
```

### 全量后端测试

**命令：**
```bash
cd apps/api
python -m pytest tests/ -q --tb=short
```

**结果：**
```
338 passed, 9 skipped, 1 warning in 129.79s (0:02:09)
```

**对比基线：** 基线 336 passed，新增 2 个测试，338 passed，0 failed

---

## 未验证部分

1. **不带 .env 启动 API 的 crash 行为**
   - 测试使用 monkeypatch 模拟环境变量缺失，未在实际不带 .env 文件的 Production 环境中验证
   - 预期行为：启动时抛出 `ValueError: JWT_SECRET must be set via environment variable or .env file`

---

## 风险与限制

1. **bcrypt 和 python-jose 设为必须依赖**
   - 如果未安装，API 启动时会直接报错（这是期望行为）
   - 已通过 `pip install bcrypt passlib python-jose[cryptography]` 安装

2. **代码行数变化**
   - `auth.py` 净减少约 40% 代码（移除 fallback 逻辑）

---

## 通过条件检查

- [x] `SECRET_KEY` 在 `auth.py` 中不再存在硬编码值
- [x] `config.py` 中 `JWT_SECRET` 默认值为空且有启动校验
- [x] `.env.example` 文件包含 12+ 个环境变量定义（实际 15+ 个）
- [x] 现有 338 个测试全部通过（基线 336 + 新增 2）

---

## 是否建议继续下一任务

**建议继续**

**原因：**
1. 所有通过条件已勾选
2. 全量测试无回归（338 passed, 0 failed）
3. 未越界推进 Task 1.2 或后续任务
4. 风险与限制已如实记录，可供后续参考