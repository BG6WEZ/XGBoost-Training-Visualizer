# XGBoost Training Visualizer — 上线开发计划

> 版本：v1.0  
> 基线日期：2026-04-13  
> 目标：从当前 MVP 状态推进到可部署上线  
> 使用方式：AI Coding Agent 按 Phase → Task 顺序逐条执行，每个 Task 独立可验证

---

## 〇、现状基线

| 指标 | 当前值 |
|------|--------|
| API 后端 | 32 文件 / 9,363 行，10 个 Router 全部注册 |
| Worker | 6 文件 / 1,875 行，训练/预处理/特征工程三队列 |
| 前端 | 21 文件 / 6,043 行，8 页面 + 认证守卫 |
| 后端测试 | 29 文件 / 336 passed / 0 failed |
| Worker 测试 | 1 文件 / 4 passed |
| 前端测试 | **无** |
| TypeScript 编译 | 0 errors |
| Docker 配置 | dev / prod / 全栈三套 compose |
| 数据库迁移 | 4 个 SQL 手动迁移文件 + `create_all` |

**已完成的功能**：数据资产扫描/上传/多文件数据集、质量检查、多表 Join、特征工程、训练队列、并发控制、实验管理（标签/过滤/模板）、结果分析（RMSE/MAE/MAPE/R²/残差）、实验对比、模型版本管理、配置导出(JSON/YAML/HTML/PDF)、用户认证(JWT)、管理后台。

**未完成的关键缺陷**：JWT 密钥硬编码、默认凭据裸露、存储路径穿越、登出空实现、前端零测试、Worker 测试极薄、无 CI/CD。

---

## 一、Phase 定义与依赖关系

```
Phase-1 安全加固 (P0 阻塞上线)
    ↓
Phase-2 稳定性 & 缺陷修复 (P0)
    ↓
Phase-3 测试补全 (P0)
    ↓
Phase-4 部署就绪化 (P1)
    ↓
Phase-5 集成验收 (P1)
```

Phase-1 ~ Phase-3 为**上线阻塞项**，必须全部完成。  
Phase-4 ~ Phase-5 为**上线推荐项**，可在灰度期迭代。

---

## 二、Phase-1：安全加固

> 目标：消除 OWASP Top 10 中的硬编码密钥、默认凭据、路径穿越风险

### Task 1.1 — 统一密钥管理，移除所有硬编码 Secret

**范围文件**：
- `apps/api/app/config.py`
- `apps/api/app/services/auth.py`
- `apps/api/app/database.py`
- `docker/docker-compose.yml`
- `docker/docker-compose.prod.yml`

**具体要求**：
1. `config.py` 中 `JWT_SECRET` 默认值改为空字符串 `""`，启动时若为空则 raise `ValueError("JWT_SECRET must be set")`
2. `services/auth.py` 中删除独立的 `SECRET_KEY` 常量，统一从 `config.settings.JWT_SECRET` 读取
3. 所有 `create_access_token()` / `decode_access_token()` 使用同一个 key
4. 在项目根目录创建 `.env.example` 文件列出所有需要配置的环境变量（含注释）
5. `.gitignore` 中确保 `.env` 被忽略

**测试要求**：
- 运行现有后端测试：`pytest tests/ -q`，336 passed 无新增 failure
- 新增测试 `test_auth.py::test_missing_jwt_secret_raises`：未设 JWT_SECRET 时启动报错
- 手动验证：不带 `.env` 启动 API 应 crash 并输出明确错误信息

**通过条件**：
- [ ] `SECRET_KEY` 在 `auth.py` 中不再存在硬编码值
- [ ] `config.py` 中 `JWT_SECRET` 默认值为空且有启动校验
- [ ] `.env.example` 文件包含 12+ 个环境变量定义
- [ ] 现有 336 个测试全部通过

---

### Task 1.2 — 存储路径穿越防护

**范围文件**：
- `apps/api/app/services/storage.py` → `LocalStorageAdapter._get_full_path()`
- `apps/worker/app/storage.py`（同步修复）

**具体要求**：
1. `_get_full_path()` 中对 `object_key` 做 `os.path.normpath()` 后检查结果是否仍在 `self.base_path` 内
2. 如果 `../` 导致路径逃逸，raise `ValueError("Path traversal detected")`
3. 同样的逻辑应用到所有 `save()` / `read()` / `delete()` / `exists()` 调用链

**测试要求**：
- 新增 `tests/test_storage.py::test_path_traversal_blocked`：传入 `../../etc/passwd` 类 key，断言 `ValueError`
- 新增 `tests/test_storage.py::test_normal_path_allowed`：传入 `models/exp1/model.json`，断言正常

**通过条件**：
- [ ] `_get_full_path()` 包含 `os.path.commonpath` 或 `str.startswith()` 校验
- [ ] 两个新增测试 passed
- [ ] 全量测试无回归

---

### Task 1.3 — 强制 bcrypt，移除 SHA256 Fallback

**范围文件**：
- `apps/api/app/services/auth.py`
- `apps/api/requirements.txt`

**具体要求**：
1. 移除 `BCRYPT_AVAILABLE` 条件分支和 SHA256 fallback 逻辑
2. 直接 `import bcrypt`，顶层导入（import 失败即启动失败，这是期望行为）
3. `requirements.txt` 中确认 `passlib[bcrypt]` 或 `bcrypt` 已列出
4. 同样移除 `JOSE_AVAILABLE` 条件分支，`python-jose` 设为必须依赖

**测试要求**：
- 现有 `test_auth.py` 全部通过
- 验证：`hash_password("test")` 返回值以 `$2b$` 开头

**通过条件**：
- [ ] `auth.py` 中无 `if BCRYPT_AVAILABLE` / `if JOSE_AVAILABLE` 分支
- [ ] 代码行数减少 30+ 行
- [ ] 全量测试通过

---

### Task 1.4 — 首次登录强制改密 + 默认密码标记

**范围文件**：
- `apps/api/app/models/models.py` → `User` 表增加 `must_change_password: bool` 字段
- `apps/api/app/database.py` → 默认 admin 创建时 `must_change_password=True`
- `apps/api/app/routers/auth.py` → login 返回 `must_change_password` 字段
- `apps/web/src/pages/LoginPage.tsx` → 登录后若 `must_change_password` 跳转改密
- `apps/api/migrations/005_add_must_change_password.sql`

**具体要求**：
1. `User` 模型新增 `must_change_password` Boolean 字段，默认 `False`
2. `init_db()` 创建默认 admin 时设 `must_change_password=True`
3. 登录 API 响应增加 `must_change_password` 字段
4. 改密 API 成功后将 `must_change_password` 设为 `False`
5. 前端 `LoginPage` 检测到 `must_change_password=true` 时弹出改密对话框
6. 新增 SQL 迁移文件

**测试要求**：
- 新增 `test_auth.py::test_admin_must_change_password_on_first_login`
- 新增 `test_auth.py::test_change_password_clears_flag`
- 现有测试 conftest 中的 mock user 需要适配新字段

**通过条件**：
- [ ] 默认 admin 登录后 API 返回 `must_change_password: true`
- [ ] 改密后再次登录返回 `must_change_password: false`
- [ ] 全量测试通过

---

### Task 1.5 — Token 黑名单（简化版 Redis）

**范围文件**：
- `apps/api/app/services/auth.py` → 新增 `revoke_token()` / `is_token_revoked()`
- `apps/api/app/routers/auth.py` → logout 端点调用 `revoke_token()`
- `apps/api/app/routers/auth.py` → `get_current_user()` 增加吊销检查

**具体要求**：
1. logout 时将当前 token 的 JTI (JWT ID) 写入 Redis，TTL = token 剩余有效期
2. `get_current_user()` 解码 token 后检查 JTI 是否在黑名单
3. `create_access_token()` 自动注入 `jti` claim（`uuid4`）
4. 如果 Redis 不可用，降级为"不检查黑名单"（记录 warning log），不影响正常使用

**测试要求**：
- 新增 `test_auth.py::test_logout_revokes_token`：登出后用同 token 请求 `/auth/me` 返回 401
- 新增 `test_auth.py::test_logout_without_redis_degrades_gracefully`

**通过条件**：
- [ ] logout 后同 token 无法再请求受保护端点
- [ ] Redis 宕机时 login/logout 不报错
- [ ] 全量测试通过

---

## 三、Phase-2：稳定性 & 缺陷修复

> 目标：修复已知的性能和健壮性问题

### Task 2.1 — 大文件上传异步行计数

**范围文件**：
- `apps/api/app/routers/datasets.py` → `upload_file()` 端点

**具体要求**：
1. 将 `sum(1 for _ in open(file_path))` 替换为 `aiofiles` 异步行计数
2. 对大文件（>100MB）采用采样估算（读前 10000 行 + 文件大小推算）

**测试要求**：
- 现有 `test_datasets.py` 通过
- 新增 `test_datasets.py::test_upload_large_csv_does_not_block`：上传 >50MB 文件的超时测试

**通过条件**：
- [ ] `upload_file()` 中无同步 `open()` 调用
- [ ] 全量测试通过

---

### Task 2.2 — CORS 配置生产化

**范围文件**：
- `apps/api/app/config.py`
- `apps/api/app/main.py`

**具体要求**：
1. `CORS_ORIGINS` 默认值改为 `["http://localhost:3000"]`（仅开发）
2. 生产环境通过环境变量 `CORS_ORIGINS` 注入实际域名（逗号分隔字符串 → List 解析）
3. `allow_methods` 从 `["*"]` 改为 `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`
4. `allow_headers` 从 `["*"]` 改为 `["Content-Type", "Authorization", "Accept"]`

**测试要求**：
- 新增 `test_cors.py::test_cors_origins_from_env`
- 验证 `OPTIONS` 预检请求返回正确的 `Access-Control-Allow-Origin`

**通过条件**：
- [ ] `allow_methods` 和 `allow_headers` 均为显式列表
- [ ] 环境变量可覆盖 CORS 源
- [ ] 全量测试通过

---

### Task 2.3 — Docker Compose 清理

**范围文件**：
- `docker/docker-compose.yml`
- `docker/docker-compose.prod.yml`
- `docker/docker-compose.dev.yml`

**具体要求**：
1. 移除所有文件中的 `version: '3.8'`
2. prod compose 中所有凭据改为 `${VAR_NAME}` 环境变量引用（不写入默认值）
3. 创建 `docker/.env.example` 列出 prod 需要的所有变量
4. prod compose 增加 `restart: unless-stopped` 策略

**测试要求**：
- `docker compose -f docker/docker-compose.yml config` 无 warning
- `docker compose -f docker/docker-compose.prod.yml --env-file docker/.env.example config` 可解析

**通过条件**：
- [ ] 三个 compose 文件均无 `version:` 行
- [ ] prod compose 中无硬编码密码
- [ ] `docker compose config` 无 warning

---

### Task 2.4 — 数据库迁移正规化（Alembic）

**范围文件**：
- `apps/api/alembic.ini`（新增）
- `apps/api/alembic/`（新增目录）
- `apps/api/app/database.py` → 移除 `create_all`，改为 startup 检查
- `apps/api/migrations/` → 现有 SQL 作为 baseline

**具体要求**：
1. 初始化 Alembic（`alembic init alembic`），配置 async engine
2. 创建 baseline migration 对应现有 4 个 SQL 文件的最终 schema
3. `database.py` 的 `init_db()` 改为：检查 `alembic_version` 表是否存在，若不存在打印警告提示运行迁移
4. 保留 `create_all` 仅用于测试环境（`conftest.py`）
5. `start-local.bat` / `start-local.sh` 中增加 `alembic upgrade head` 步骤

**测试要求**：
- `alembic upgrade head` 在空数据库上可执行成功
- `alembic downgrade base` 可回滚
- 现有 336 个测试通过（测试 conftest 仍用 `create_all`）

**通过条件**：
- [ ] `alembic/versions/` 下至少有 1 个 migration 文件
- [ ] 生产启动流程不再自动 `create_all`
- [ ] 全量测试通过

---

## 四、Phase-3：测试补全

> 目标：确保核心路径有自动化回归保障

### Task 3.1 — Worker 核心路径单元测试

**范围文件**：
- `apps/worker/tests/`（新增/扩展）

**具体要求**：
新增以下测试：
1. `test_training_task.py::test_xgboost_trainer_loads_csv` — 给定有效 CSV，XGBoostTrainer 正确加载数据
2. `test_training_task.py::test_xgboost_trainer_runs_training` — 给定小数据集，训练完成并产出 model 文件
3. `test_training_task.py::test_xgboost_trainer_early_stopping` — 开启早停时正确终止
4. `test_training_task.py::test_xgboost_trainer_invalid_target_column` — 目标列不存在时报错
5. `test_training_task.py::test_xgboost_trainer_saves_metrics` — 训练后 metrics 列表非空
6. `test_preprocessing_task.py::test_preprocessing_runs_successfully` — 预处理任务正常执行
7. `test_feature_engineering_task.py::test_feature_engineering_runs` — 特征工程任务正常执行
8. `test_worker_main.py::test_worker_graceful_shutdown` — 收到停止信号后优雅退出

**测试要求**：
- 所有测试使用临时目录 + 内存 SQLite + mock Redis
- 不依赖外部服务

**通过条件**：
- [ ] 新增测试 ≥ 8 个
- [ ] `pytest apps/worker/tests/ -q` 全部 passed
- [ ] 无需 Docker/PostgreSQL/Redis 即可运行

---

### Task 3.2 — 前端 E2E 测试（Playwright）

**范围文件**：
- `apps/web/package.json` → 新增 `@playwright/test` devDependency
- `apps/web/playwright.config.ts`（新增）
- `apps/web/e2e/`（新增目录）

**具体要求**：
新增 Playwright E2E 测试覆盖以下核心流程：

1. **登录流程** `e2e/auth.spec.ts`
   - 正确用户名密码可登录
   - 错误密码显示错误提示
   - 登出后重定向到登录页

2. **数据资产流程** `e2e/assets.spec.ts`
   - 数据资产扫描按钮可点击，返回结果
   - 上传 CSV 文件成功
   - 注册数据集成功并跳转详情

3. **实验流程** `e2e/experiments.spec.ts`
   - 创建实验（选择数据集、模板、参数）
   - 实验列表显示新创建的实验
   - 提交训练任务

4. **结果查看** `e2e/results.spec.ts`
   - 已完成实验的结果页可正常加载
   - 指标数据可见
   - 实验对比页可选择多个实验

**配置要求**：
- `playwright.config.ts` 设置 `baseURL` 从环境变量读取
- `package.json` 新增 script：`"test:e2e": "playwright test"`
- 使用 `webServer` 配置自动启动 vite dev server

**测试要求**：
- 需要后端服务运行（describe 中有 beforeAll 检查 API 可达）
- 每个测试截图保存到 `e2e/screenshots/`

**通过条件**：
- [ ] `npx playwright test` 在本地启动全栈后全部 passed
- [ ] 至少 10 个 E2E 测试用例
- [ ] 截图证据自动生成

---

### Task 3.3 — API 集成冒烟测试脚本

**范围文件**：
- `scripts/smoke-test-api.py`（新增）

**具体要求**：
创建一个端到端 API 冒烟测试脚本（Python + httpx），覆盖：

```
1. POST /api/auth/login → 获取 token
2. GET /api/assets/scan → 扫描资产
3. POST /api/datasets/upload → 上传测试 CSV
4. POST /api/datasets/ → 创建数据集
5. GET /api/datasets/{id} → 获取详情
6. POST /api/experiments/ → 创建实验
7. POST /api/training/submit → 提交训练
8. GET /api/training/status → 查看队列
9. (轮询等待训练完成)
10. GET /api/results/{id} → 获取结果
11. GET /api/results/{id}/feature-importance → 特征重要性
12. POST /api/results/compare → 对比实验
13. POST /api/auth/logout → 登出
```

**测试要求**：
- 脚本可独立运行：`python scripts/smoke-test-api.py --api-url http://localhost:8000`
- 每步输出 PASS/FAIL + 耗时
- 退出码：0 = 全通过，1 = 有失败

**通过条件**：
- [ ] 本地全栈启动后 `python scripts/smoke-test-api.py` 返回 exit code 0
- [ ] 覆盖 ≥ 10 个 API 端点
- [ ] 总耗时 < 120 秒（含训练等待）

---

## 五、Phase-4：部署就绪化

> 目标：具备一键部署能力

### Task 4.1 — 生产环境配置模板

**范围文件**：
- `.env.example`（项目根目录，完整版）
- `docker/.env.example`（Docker 专用）
- `docs/release/DEPLOYMENT_GUIDE.md`（更新）

**具体要求**：
1. 创建完整的 `.env.example`，包含所有环境变量：
   ```
   # === 必须配置 ===
   JWT_SECRET=          # 至少 32 字符的随机字符串
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   REDIS_URL=redis://host:6379/0
   ADMIN_DEFAULT_PASSWORD=  # 首次启动的默认管理员密码

   # === 存储配置 ===
   STORAGE_TYPE=local   # local 或 minio
   WORKSPACE_DIR=/app/workspace
   
   # === MinIO (当 STORAGE_TYPE=minio 时必须) ===
   MINIO_ENDPOINT=
   MINIO_ACCESS_KEY=
   MINIO_SECRET_KEY=
   MINIO_BUCKET=xgboost-vis
   MINIO_SECURE=false
   
   # === 可选配置 ===
   CORS_ORIGINS=https://your-domain.com
   MAX_CONCURRENT_TRAININGS=3
   LOG_LEVEL=INFO
   ```

2. 更新部署文档，包含：
   - 部署前置条件（Docker 20+、16GB RAM 等）
   - 一键启动命令
   - 首次登录步骤
   - 健康检查验证步骤

**通过条件**：
- [ ] `.env.example` 包含所有必须变量且有注释
- [ ] 按部署文档操作能成功启动

---

### Task 4.2 — Nginx 反向代理生产配置

**范围文件**：
- `apps/web/nginx.conf`

**具体要求**：
1. 增加安全响应头：
   ```nginx
   add_header X-Frame-Options "SAMEORIGIN" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-XSS-Protection "1; mode=block" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   ```
2. API 代理增加超时配置：`proxy_read_timeout 300s`（训练提交可能较慢）
3. 文件上传大小限制：`client_max_body_size 500M`
4. 静态资源缓存：js/css 文件 `Cache-Control: public, max-age=31536000, immutable`

**测试要求**：
- Docker build 前端镜像成功
- `curl -I http://localhost:3000/` 返回安全头

**通过条件**：
- [ ] 4 个安全头均出现在响应中
- [ ] 大文件上传不被 Nginx 拦截
- [ ] 静态资源有缓存头

---

### Task 4.3 — 健康检查与就绪探针完善

**范围文件**：
- `apps/api/app/routers/health.py`

**具体要求**：
1. `/health` — 存活探针（liveness），仅返回 `{"status": "ok"}`，不检查依赖
2. `/ready` — 就绪探针（readiness），检查：
   - 数据库连接可用
   - Redis 连接可用（可选降级）
   - 存储服务可写
3. 增加 `/health/details` 管理端点（仅管理员可访问），返回各组件详细状态
4. Docker healthcheck 使用 `/health`，K8s readiness 使用 `/ready`

**测试要求**：
- `test_health.py::test_liveness_always_ok`
- `test_health.py::test_readiness_checks_db`
- `test_health.py::test_details_requires_admin`

**通过条件**：
- [ ] `/health` 不依赖任何外部服务
- [ ] `/ready` 返回各组件状态
- [ ] 全量测试通过

---

### Task 4.4 — 结构化日志

**范围文件**：
- `apps/api/app/main.py`
- `apps/worker/app/main.py`
- 新增 `apps/api/app/logging_config.py`

**具体要求**：
1. 配置 JSON 格式日志输出（生产环境）
2. 每条日志包含：timestamp, level, message, module, request_id（API 端）
3. 开发环境保持人类可读格式
4. 通过 `LOG_FORMAT` 环境变量切换：`json` | `text`（默认 `text`）
5. API 请求增加 request_id 中间件（使用 `X-Request-ID` header 或自动生成）

**测试要求**：
- 验证 `LOG_FORMAT=json` 时日志输出为合法 JSON

**通过条件**：
- [ ] 生产日志可被 ELK/Loki 等日志系统解析
- [ ] 每个 API 请求有唯一 request_id
- [ ] 全量测试通过

---

## 六、Phase-5：集成验收

> 目标：全链路验证，确认可上线

### Task 5.1 — Docker 全栈构建 & 启动验证

**具体操作**：
```bash
# 1. 构建所有镜像
docker compose -f docker/docker-compose.yml build

# 2. 启动全栈
docker compose -f docker/docker-compose.yml up -d

# 3. 等待就绪
# 轮询 http://localhost:8000/ready 直到返回 200

# 4. 执行 API 冒烟测试
python scripts/smoke-test-api.py --api-url http://localhost:8000

# 5. 执行浏览器冒烟测试
npx playwright test --config=apps/web/playwright.config.ts

# 6. 检查容器健康
docker compose -f docker/docker-compose.yml ps
```

**通过条件**：
- [ ] 6 个容器全部 healthy/running
- [ ] API 冒烟测试 exit code 0
- [ ] 浏览器 E2E 测试 ≥ 80% passed
- [ ] 无 error 级别日志（warning 可接受）

---

### Task 5.2 — 性能基线测试

**范围文件**：
- `scripts/benchmark.py`（新增）

**具体要求**：
用 `httpx` 或 `locust` 对以下端点做基本性能测试：

| 端点 | 并发数 | 目标 P95 延迟 |
|------|--------|---------------|
| `GET /health` | 50 | < 50ms |
| `POST /api/auth/login` | 10 | < 500ms |
| `GET /api/datasets/` | 20 | < 200ms |
| `GET /api/experiments/` | 20 | < 200ms |
| `POST /api/datasets/upload` (1MB CSV) | 5 | < 3s |

**通过条件**：
- [ ] 所有端点满足 P95 目标
- [ ] 无 5xx 错误
- [ ] 输出性能基线报告

---

### Task 5.3 — 安全检查清单最终确认

**逐项验证**：

| # | 检查项 | 验证方法 |
|---|--------|----------|
| 1 | 无硬编码密钥 | `grep -r "secret\|password\|key" apps/ --include="*.py" \| grep -v test \| grep -v ".pyc"` 人工审阅 |
| 2 | 默认 admin 强制改密 | 登录 admin/admin123 后 API 返回 `must_change_password: true` |
| 3 | JWT 可吊销 | 登出 → 用旧 token 请求 → 401 |
| 4 | 路径穿越阻止 | `curl -X POST .../upload` 带 `../../../etc/passwd` 文件名 → 拒绝 |
| 5 | SQL 注入阻止 | 全部使用 ORM（已确认，无 raw SQL） |
| 6 | CORS 收紧 | `OPTIONS` 请求仅允许配置的 origin |
| 7 | 安全响应头 | `curl -I` 检查 4 个安全头 |
| 8 | 非 root 运行 | Docker 内 `whoami` 返回 `appuser` |

**通过条件**：
- [ ] 8/8 检查项全部通过

---

## 七、执行优先级与时间预估

| Phase | 任务数 | 优先级 | 上线阻塞 |
|-------|--------|--------|----------|
| Phase-1 安全加固 | 5 | P0 | ✅ 是 |
| Phase-2 稳定性修复 | 4 | P0 | ✅ 是 |
| Phase-3 测试补全 | 3 | P0 | ✅ 是 |
| Phase-4 部署就绪 | 4 | P1 | ⚠️ 建议 |
| Phase-5 集成验收 | 3 | P1 | ⚠️ 建议 |
| **合计** | **19 个任务** | | |

**建议执行顺序**：严格按 Phase 1 → 2 → 3 → 4 → 5，Phase 内可并行。

---

## 八、AI Coding Agent 执行规范

### 每个 Task 的执行流程

```
1. 阅读 Task 描述，理解范围文件和具体要求
2. 阅读范围文件的当前内容
3. 实现代码变更
4. 运行指定的测试命令
5. 若测试失败 → 修复 → 重新测试（最多 3 轮）
6. 运行全量后端测试确认无回归：pytest apps/api/tests/ -q
7. 逐条检查"通过条件"清单
8. 输出 Task 完成报告：
   - 修改的文件列表
   - 新增/删除/修改行数
   - 测试结果截图/输出
   - 通过条件逐项 ✅/❌
```

### 禁止事项

- ❌ 不得修改不在"范围文件"内的代码（除非测试 conftest 需要适配）
- ❌ 不得添加与 Task 无关的"改进"
- ❌ 不得跳过测试直接提交
- ❌ 不得在测试中使用 `@pytest.mark.skip` 绕过失败
- ❌ 不得引入新的硬编码密钥或凭据

### 回归保护红线

- 后端测试基线：**336 passed**（只允许增加，不允许减少）
- Worker 测试基线：**4 passed**
- TypeScript 编译：**0 errors**
