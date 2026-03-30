# XGBoost Training Worker

## 依赖安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python -m app.main
```

## 环境变量

- `DATABASE_URL`: PostgreSQL 连接字符串
- `REDIS_URL`: Redis 连接字符串
- `MINIO_ENDPOINT`: MinIO 端点
- `WORKSPACE_DIR`: 工作目录