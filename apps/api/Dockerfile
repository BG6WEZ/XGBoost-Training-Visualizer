FROM python:3.11-slim-bookworm

WORKDIR /app

# 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（保留 uvloop/httptools 的高性能路径）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码到 /app/app（保持与本地开发一致的路径结构）
COPY app/ /app/app/
COPY alembic.ini /app/
COPY alembic/ /app/alembic/
COPY migrations/ /app/migrations/
COPY scripts/ /app/scripts/

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app && mkdir -p /app/workspace/uploads && chown -R appuser:appuser /app/workspace
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Performance optimization (M7-T101-v14):
# - Workers = 8 to improve CPU-bound login throughput now that startup races are fixed
# - Re-enable uvloop + httptools for the hot benchmark paths
# - Disable access log to remove per-request logging overhead during benchmark
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8", "--backlog", "4096", "--loop", "uvloop", "--http", "httptools", "--no-access-log"]
