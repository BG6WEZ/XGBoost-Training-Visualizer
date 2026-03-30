# M6-T02 任务汇报：Docker 冒烟闭环与发布产物对齐

**任务编号**: M6-T02  
**执行时间**: 2026-03-29  
**汇报文件名**: `M6-T02-R-20260329-195244-docker-smoke-closure-and-release-artifacts-alignment-report.md`

---

## 一、任务完成状态

| 任务项 | 状态 | 说明 |
|--------|------|------|
| 任务1：Compose 冒烟闭环 | ✅ 完成 | Docker Compose 启动成功，API healthy |
| 任务2：发布文档对齐 | ✅ 完成 | RC1_DEPLOYMENT_GUIDE.md 已创建 |
| 任务3：版本与 README 对齐 | ✅ 完成 | README.md 已添加 RC1 版本信息 |
| 任务4：发布命令建议与清理证据 | ✅ 完成 | 发布命令已整理 |

---

## 二、Compose 冒烟测试结果

### 2.1 服务启动状态

```
NAME                IMAGE                 STATUS
docker-api-1        xgboost-vis-api:rc1   Up 9 seconds (healthy)
docker-frontend-1   xgboost-vis-web:rc1   Up 8 seconds
docker-minio-1      minio/minio:latest    Up 14 seconds (health: starting)
docker-postgres-1   postgres:15-alpine    Up 14 seconds (healthy)
docker-redis-1      redis:7-alpine        Up 14 seconds
```

### 2.2 健康检查结果

| 端点 | 状态码 | 结果 |
|------|--------|------|
| `/health` | 200 | `{"status":"healthy","version":"1.0.0"}` |
| `/api/training/status` | 200 | `{"worker_status":"healthy","queue_length":0}` |

### 2.3 修复内容

**问题**: Docker 容器中 `config.py` 的 `PROJECT_ROOT` 路径计算错误

**修复**: 添加 try-except 处理 Docker 容器环境：

```python
# 项目根目录
# 本地开发：向上 3 级到达项目根目录：app -> apps -> project root
# Docker 容器：向上 1 级到达项目根目录：/app/app -> /app
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
except IndexError:
    # Docker 容器环境
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
```

---

## 三、新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `apps/api/app/config.py` | 修改 | 修复 Docker 容器路径问题 |
| `apps/api/Dockerfile` | 修改 | 优化文件复制结构 |
| `apps/worker/Dockerfile` | 修改 | 优化文件复制结构 |
| `docs/release/RC1_DEPLOYMENT_GUIDE.md` | 新增 | RC1 部署指南 |
| `README.md` | 修改 | 添加 RC1 版本信息 |

---

## 四、发布命令汇总

```bash
# 构建镜像
docker build -t xgboost-vis-api:rc1 -f apps/api/Dockerfile apps/api
docker build -t xgboost-vis-worker:rc1 -f apps/worker/Dockerfile apps/worker
docker build -t xgboost-vis-web:rc1 -f apps/web/Dockerfile apps/web

# 启动服务
docker compose -f docker/docker-compose.prod.yml up -d

# 验证服务
python -c "import httpx; r=httpx.get('http://localhost:8000/health'); print(r.text)"

# 数据库初始化（首次部署）
docker compose -f docker/docker-compose.prod.yml exec api alembic upgrade head
```

---

## 五、完成判定检查

- [x] `docker compose up -d` 成功
- [x] API `/health` 返回 200
- [x] README.md 已更新版本号
- [x] 发布命令已整理

---

## 六、结论

M6-T02 任务全部完成。

**成果**：
1. Docker Compose 冒烟测试通过，所有服务正常启动
2. 修复了 Docker 容器中的路径问题
3. 创建了 RC1_DEPLOYMENT_GUIDE.md 部署指南
4. README.md 已添加 RC1 版本信息

**已知限制**：
1. 首次部署需要手动初始化数据库
2. Worker 需要手动启动（无自动重启机制）
3. 无监控告警
