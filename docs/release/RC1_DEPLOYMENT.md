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
docker-compose -f docker-compose.prod.yml up -d
```

### 方式二：手动启动

```bash
# 1. 启动基础设施
docker run -d --name postgres -e POSTGRES_USER=xgboost -e POSTGRES_PASSWORD=xgboost123 -e POSTGRES_DB=xgboost_vis -p 5432:5432 postgres:15-alpine

docker run -d --name redis -p 6379:6379 redis:7-alpine

docker run -d --name minio -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"

# 2. 启动应用服务
docker run -d --name api -p 8000:8000 --env-file .env xgboost-vis-api:rc1

docker run -d --name worker --env-file .env xgboost-vis-worker:rc1

docker run -d --name web -p 3000:3000 xgboost-vis-web:rc1
```

## 三、环境变量

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

## 四、健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# 就绪检查
curl http://localhost:8000/ready

# Worker 状态
curl http://localhost:8000/api/training/status
```

## 五、服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Web | 3000 | 前端界面 |
| API | 8000 | 后端 API |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 消息队列 |
| MinIO API | 9000 | 对象存储 API |
| MinIO Console | 9001 | 对象存储控制台 |

## 六、数据持久化

| 卷 | 说明 |
|------|------|
| postgres-data | 数据库数据 |
| redis-data | Redis 数据 |
| minio-data | 对象存储数据 |
| workspace-data | 工作区数据 |

## 七、回滚策略

```bash
# 回滚到上一版本
docker-compose -f docker-compose.prod.yml down
docker tag xgboost-vis-api:rc1 xgboost-vis-api:backup
docker pull xgboost-vis-api:previous
docker-compose -f docker-compose.prod.yml up -d
```

## 八、已知限制

1. Worker 需要手动启动（无自动重启机制）
2. 无监控告警（建议后续添加 Prometheus）
3. 队列积压需要手动处理（使用 queue_governance.py）
