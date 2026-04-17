# 生产部署指南

## 一、环境要求

### 1.1 系统要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Docker | 24.0+ | 26.0+ |
| Docker Compose | 2.20+ | 2.26+ |
| 内存 | 4GB | 8GB+ |
| CPU | 2核 | 4核+ |
| 磁盘 | 20GB | 50GB+ |

### 1.2 网络要求

| 端口 | 协议 | 说明 |
|------|------|------|
| 3000 | TCP | Web 前端 |
| 8000 | TCP | API 后端 |
| 5432 | TCP | PostgreSQL（可选外部访问） |
| 9000 | TCP | MinIO API（可选外部访问） |
| 9001 | TCP | MinIO Console（可选外部访问） |

## 二、快速开始

### 2.1 克隆项目

```bash
git clone https://github.com/BG6WEZ/XGBoost-Training-Visualizer.git
cd XGBoost-Training-Visualizer
```

### 2.2 配置环境变量

```bash
# 复制环境变量模板
cp docker/.env.example docker/.env

# 编辑 .env 文件，修改所有必填项
# 特别注意以下安全相关变量：
# - POSTGRES_PASSWORD
# - MINIO_ROOT_PASSWORD
# - MINIO_SECRET_KEY
# - JWT_SECRET (使用 python -c "import secrets; print(secrets.token_hex(32))" 生成)
# - ADMIN_DEFAULT_PASSWORD
```

### 2.3 启动服务

```bash
cd docker

# 启动所有服务
docker compose -f docker-compose.prod.yml --env-file .env up -d

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

### 2.4 初始化数据库

```bash
# 进入 API 容器
docker compose -f docker-compose.prod.yml exec api bash

# 运行数据库迁移
alembic upgrade head

# 创建管理员账户（如需要）
python -m app.scripts.create_admin

# 退出容器
exit
```

### 2.5 验证部署

```bash
# 检查 API 健康状态
curl http://localhost:8000/health

# 检查 API 就绪状态
curl http://localhost:8000/ready

# 访问前端界面
# 浏览器打开: http://localhost:3000
```

## 三、环境变量详解

### 3.1 数据库配置

| 变量 | 说明 | 示例值 | 必填 |
|------|------|--------|------|
| POSTGRES_USER | 数据库用户名 | xgboost | 是 |
| POSTGRES_PASSWORD | 数据库密码 | secure-password | 是 |
| POSTGRES_DB | 数据库名称 | xgboost_vis | 是 |
| DATABASE_URL | 完整数据库连接字符串 | postgresql://xgboost:pass@postgres:5432/xgboost_vis | 是 |

### 3.2 Redis 配置

| 变量 | 说明 | 示例值 | 必填 |
|------|------|--------|------|
| REDIS_PASSWORD | Redis 密码 | secure-redis-pass | 是 |
| REDIS_URL | Redis 连接字符串 | redis://:pass@redis:6379/0 | 是 |

### 3.3 MinIO 对象存储配置

| 变量 | 说明 | 示例值 | 必填 |
|------|------|--------|------|
| MINIO_ROOT_USER | MinIO 根用户 | minioadmin | 是 |
| MINIO_ROOT_PASSWORD | MinIO 根密码 | secure-minio-pass | 是 |
| MINIO_ACCESS_KEY | MinIO 访问密钥 | minioadmin | 是 |
| MINIO_SECRET_KEY | MinIO 密钥 | secure-secret-key | 是 |
| MINIO_ENDPOINT | MinIO 端点 | minio:9000 | 是 |
| MINIO_BUCKET | MinIO 桶名 | xgboost-vis | 是 |
| MINIO_SECURE | 是否使用 HTTPS | false | 是 |

### 3.4 安全配置

| 变量 | 说明 | 示例值 | 必填 |
|------|------|--------|------|
| JWT_SECRET | JWT 签名密钥（至少32字符） | random-32-char-secret | 是 |
| ADMIN_DEFAULT_PASSWORD | 默认管理员密码 | admin123 | 是 |

### 3.5 应用配置

| 变量 | 说明 | 示例值 | 默认值 |
|------|------|--------|--------|
| WORKSPACE_DIR | 工作目录路径 | /app/workspace | /app/workspace |
| VITE_API_URL | API 地址 | http://api:8000 | http://api:8000 |
| CORS_ORIGINS | CORS 允许的源（逗号分隔） | http://localhost:3000 | http://localhost:3000 |
| STORAGE_TYPE | 存储类型 | local/minio | minio |
| MAX_CONCURRENT_TRAININGS | 最大并发训练数 | 3 | 3 |
| TRAINING_MAX_CONCURRENCY | Worker 并发槽位数 | 2 | 2 |
| JWT_EXPIRE_HOURS | JWT 过期时间（小时） | 24 | 24 |
| TRAINING_TIMEOUT_MINUTES | 训练超时时间（分钟） | 120 | 120 |
| MAX_FILE_SIZE_MB | 最大上传文件大小（MB） | 1024 | 1024 |
| LOG_LEVEL | 日志级别 | DEBUG/INFO/WARNING/ERROR | INFO |
| LOG_FORMAT | 日志格式 | text/json | text |
| DEBUG | 调试模式 | true/false | false |

## 四、数据持久化

### 4.1 Docker Volumes

| 卷名 | 挂载点 | 说明 |
|------|--------|------|
| postgres-data | /var/lib/postgresql/data | PostgreSQL 数据 |
| redis-data | /data | Redis 数据 |
| minio-data | /data | MinIO 数据 |
| workspace-data | /app/workspace | 工作区数据 |

### 4.2 数据备份

```bash
# 备份 PostgreSQL 数据
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U xgboost xgboost_vis > backup.sql

# 备份 MinIO 数据
docker run --rm -v docker_minio-data:/data -v $(pwd):/backup alpine tar czf /backup/minio-backup.tar.gz -C /data .

# 恢复 PostgreSQL
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T postgres psql -U xgboost -d xgboost_vis
```

## 五、服务管理

### 5.1 查看日志

```bash
# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f worker
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f postgres
docker compose -f docker-compose.prod.yml logs -f redis
docker compose -f docker-compose.prod.yml logs -f minio
```

### 5.2 重启服务

```bash
# 重启所有服务
docker compose -f docker-compose.prod.yml restart

# 重启单个服务
docker compose -f docker-compose.prod.yml restart api
docker compose -f docker-compose.prod.yml restart worker
```

### 5.3 停止服务

```bash
# 停止服务但保留数据
docker compose -f docker-compose.prod.yml down

# 停止服务并删除数据卷（危险操作！）
docker compose -f docker-compose.prod.yml down -v
```

## 六、部署模式

### 6.1 开发环境

```bash
cd docker

# 启动开发环境（仅基础设施）
docker compose -f docker-compose.dev.yml up -d

# 在本地运行 API
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 在本地运行前端
cd apps/web
pnpm install
pnpm dev

# 在本地运行 Worker
cd apps/worker
python main.py
```

### 6.2 生产环境

使用 docker-compose.prod.yml 完整部署所有服务。

## 七、安全建议

### 7.1 密码策略

1. 所有密码至少 16 字符
2. 使用随机字符串作为 JWT_SECRET
3. 定期更换数据库和 Redis 密码
4. 不要在 .env 文件中使用默认密码

### 7.2 网络安全

1. 生产环境使用 HTTPS 反向代理（Nginx/Caddy）
2. 限制 PostgreSQL 端口外部访问
3. 限制 MinIO 端口外部访问

### 7.3 Nginx 反向代理示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 八、故障排查

### 8.1 常见问题

#### Q1: API 启动失败

**症状**: 容器启动后立即退出

**排查步骤**:
```bash
# 查看容器日志
docker compose -f docker-compose.prod.yml logs api

# 检查环境变量
docker compose -f docker-compose.prod.yml exec api env

# 检查数据库连接
docker compose -f docker-compose.prod.yml exec api python -c "from app.database import engine; print('DB OK')"
```

#### Q2: Worker 无法连接

**症状**: 训练任务无法启动或卡住

**排查步骤**:
```bash
# 检查 Redis 连接
docker compose -f docker-compose.prod.yml logs worker

# 检查 Worker 状态
curl http://localhost:8000/api/training/status
```

#### Q3: CORS 错误

**症状**: 前端请求被拒绝

**解决方案**:
在 .env 中添加正确的源：
```
CORS_ORIGINS=http://your-domain.com,http://localhost:3000
```

### 8.2 日志级别调整

```bash
# 临时调整日志级别
LOG_LEVEL=DEBUG docker compose -f docker-compose.prod.yml up -d

# 或使用 JSON 格式日志
LOG_FORMAT=json docker compose -f docker-compose.prod.yml up -d
```

## 九、升级部署

### 9.1 更新代码

```bash
git pull origin main
```

### 9.2 重新构建镜像

```bash
docker compose -f docker-compose.prod.yml build --no-cache
```

### 9.3 滚动升级

```bash
# 停止旧服务
docker compose -f docker-compose.prod.yml down

# 启动新服务
docker compose -f docker-compose.prod.yml --env-file .env up -d

# 运行数据库迁移
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## 十、架构概览

```
┌─────────────────────────────────────────────┐
│                  Docker Network              │
│                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │  Front  │───▶│   API   │───▶│ Worker  │ │
│  │  (3000) │    │  (8000) │    │         │ │
│  └─────────┘    └────┬────┘    └────┬────┘ │
│                      │              │       │
│            ┌─────────▼──────────────▼─────┐ │
│            │          PostgreSQL          │ │
│            │           (5432)             │ │
│            └──────────────────────────────┘ │
│                      │                      │
│            ┌─────────▼──────────────┐       │
│            │        Redis           │       │
│            │        (6379)          │       │
│            └────────────────────────┘       │
│                      │                      │
│            ┌─────────▼──────────────┐       │
│            │        MinIO           │       │
│            │     (9000/9001)        │       │
│            └────────────────────────┘       │
│                                             │
└─────────────────────────────────────────────┘
```

## 十一、服务依赖关系

| 服务 | 依赖 | 说明 |
|------|------|------|
| api | postgres, redis, minio | 必须等待所有依赖就绪 |
| worker | postgres, redis, minio | 必须等待所有依赖就绪 |
| frontend | api | 依赖 API 提供服务 |
| postgres | 无 | 基础设施服务 |
| redis | 无 | 基础设施服务 |
| minio | 无 | 基础设施服务 |