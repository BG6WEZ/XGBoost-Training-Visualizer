# RC1 部署指南

## 一、镜像清单

| 镜像 | 大小 | 说明 |
|------|------|------|
| xgboost-vis-api:rc1 | 592MB | FastAPI 后端服务 |
| xgboost-vis-worker:rc1 | 567MB | 训练任务消费者 |
| xgboost-vis-web:rc1 | 26.2MB | React 前端服务 |

## 二、快速启动

### 方式一：Docker Compose（推荐）

```bash
cd docker
docker compose -f docker-compose.prod.yml up -d
```

### 方式二：手动启动

参见 RC1_DEPLOYMENT.md

## 三、服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Web | 3000 | 前端界面 |
| API | 8000 | 后端 API |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 消息队列 |
| MinIO API | 9000 | 对象存储 API |
| MinIO Console | 9001 | 对象存储控制台 |

## 四、健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# 就绪检查
curl http://localhost:8000/ready

# Worker 状态
curl http://localhost:8000/api/training/status
```

## 五、数据库初始化

首次部署需要初始化数据库：

```bash
# 进入 API 容器
docker compose -f docker/docker-compose.prod.yml exec api bash

# 运行迁移
alembic upgrade head
```

## 六、环境变量

### API / Worker 共用

```env
DATABASE_URL=postgresql://xgboost:xgboost123@postgres:5432/xgboost_vis
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=xgboost-vis
MINIO_SECURE=false
WORKSPACE_DIR=/app/workspace
```

## 七、数据持久化

| 卷 | 说明 |
|------|------|
| postgres-data | 数据库数据 |
| redis-data | Redis 数据 |
| minio-data | 对象存储数据 |
| workspace-data | 工作区数据 |

## 八、回滚策略

```bash
# 停止服务
docker compose -f docker/docker-compose.prod.yml down

# 回滚镜像
docker tag xgboost-vis-api:rc1 xgboost-vis-api:backup
docker pull xgboost-vis-api:previous

# 重启服务
docker compose -f docker/docker-compose.prod.yml up -d
```

## 九、已知限制

1. Worker 需要手动启动（无自动重启机制）
2. 无监控告警（建议后续添加 Prometheus）
3. 队列积压需要手动处理（使用 queue_governance.py）

## 十、发布命令

```bash
# 构建镜像
docker build -t xgboost-vis-api:rc1 -f apps/api/Dockerfile apps/api
docker build -t xgboost-vis-worker:rc1 -f apps/worker/Dockerfile apps/worker
docker build -t xgboost-vis-web:rc1 -f apps/web/Dockerfile apps/web

# 启动服务
docker compose -f docker/docker-compose.prod.yml up -d

# 验证服务
python -c "import httpx; r=httpx.get('http://localhost:8000/health'); print(r.text)"
```

## 十一、验收脚本

使用 RC1 最终闸门复核脚本进行完整验收：

```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts/rc1_final_gate.ps1

# 输出 FINAL_GATE=PASS 表示验收通过
# 输出 FINAL_GATE=FAIL 表示验收失败
```

## 十二、常见问题

### Q1: Docker 不可用

**症状**: `FINAL_GATE=FAIL`, `Docker: NOT AVAILABLE`

**解决方案**:
1. 确保 Docker Desktop 已启动
2. 检查 Docker 服务状态: `docker info`
3. 重启 Docker Desktop

### Q2: API 健康检查失败

**症状**: `API health: FAIL`

**解决方案**:
1. 检查 API 容器日志: `docker logs docker-api-1`
2. 检查数据库连接: `docker compose -f docker/docker-compose.prod.yml exec api curl http://postgres:5432`
3. 检查环境变量配置

### Q3: Worker 无法启动

**症状**: `Worker status: FAIL`

**解决方案**:
1. 检查 Worker 容器日志: `docker logs docker-worker-1`
2. 检查 Redis 连接: `docker compose -f docker/docker-compose.prod.yml exec worker curl http://redis:6379`
3. 检查缺少依赖: `docker compose -f docker/docker-compose.prod.yml exec worker pip list`
