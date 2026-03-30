# XGBoost 训练可视化工具 - 联调冒烟测试手册

## 概述

本文档提供可执行的联调冒烟测试步骤，用于验证系统各组件的集成是否正常工作。

**目标读者**：开发人员、测试人员、运维人员

**前置条件**：
- Docker 和 Docker Compose 已安装
- Python 3.11+ 已安装（用于本地开发）
- Node.js 18+ 和 pnpm 已安装（用于前端开发）

---

## 1. 环境准备

### 1.1 环境变量配置

复制环境变量模板并配置：

```bash
cp .env.example .env
```

关键配置项：

> **说明**：以下配置与 Docker Compose 开发环境（`docker/docker-compose.dev.yml`）默认账号密码一致。
> 如使用本地自装的 PostgreSQL，请按实际配置调整。

```bash
# 数据库（Docker Compose 默认：xgboost / xgboost123）
DATABASE_URL=postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis

# Redis
REDIS_URL=redis://localhost:6379/0

# 存储模式：local 或 minio
STORAGE_TYPE=local
WORKSPACE_DIR=./workspace

# MinIO 配置（仅 STORAGE_TYPE=minio 时需要）
# MINIO_ENDPOINT=localhost:9000
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
# MINIO_BUCKET=xgboost-vis
# MINIO_SECURE=false
```

### 1.2 启动基础设施

#### 方式一：Docker Compose（推荐）

```bash
# 启动 PostgreSQL + Redis（开发环境）
docker compose -f docker/docker-compose.dev.yml up -d postgres redis

# 可选：启动 MinIO（对象存储模式）
docker compose -f docker/docker-compose.dev.yml up -d minio
```

#### 方式二：本地安装

```bash
# PostgreSQL
pg_ctl -D /usr/local/var/postgres start

# Redis
redis-server /usr/local/etc/redis.conf
```

### 1.3 验证基础设施

```bash
# PostgreSQL（Docker Compose 默认用户：xgboost）
psql -h localhost -U xgboost -d xgboost_vis -c "SELECT 1"

# Redis
redis-cli ping
# 应返回 PONG

# MinIO（如果启用）
curl http://localhost:9000/minio/health/live
```

---

## 2. 启动服务

### 2.1 启动 API 服务

```bash
cd apps/api

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（首次运行）
# 注意：需要手动创建数据库或使用迁移脚本
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证 API 启动：

```bash
curl http://localhost:8000/health
# 应返回 {"status": "healthy", ...}
```

### 2.2 启动 Worker 服务

```bash
cd apps/worker

# 安装依赖
pip install -r requirements.txt

# 启动 Worker
python -m app.main
```

验证 Worker 启动：
- 查看日志输出 `Worker started, waiting for tasks...`

### 2.3 启动前端（可选）

```bash
cd apps/web

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

验证前端启动：
- 访问 http://localhost:3000

---

## 3. 冒烟测试步骤

### 3.1 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/health

# 就绪检查（含数据库、存储、Redis）
curl http://localhost:8000/ready

# 存活检查
curl http://localhost:8000/live
```

**预期结果**：所有检查返回 HTTP 200

### 3.2 创建数据集

**接口**：`POST /api/datasets/`

**请求格式**：JSON（非 multipart 上传）

```bash
# 准备测试数据文件
mkdir -p ./dataset
cat > ./dataset/test.csv << EOF
id,value,target
1,10.5,1.2
2,20.3,0.8
3,15.8,1.5
4,8.2,0.6
5,12.1,1.1
EOF

# 创建数据集（JSON 请求）
curl -X POST http://localhost:8000/api/datasets/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Dataset",
    "description": "Smoke test dataset",
    "target_column": "target",
    "files": [
      {
        "file_path": "./dataset/test.csv",
        "file_name": "test.csv",
        "role": "primary",
        "row_count": 5,
        "column_count": 3,
        "file_size": 60
      }
    ]
  }'
```

**预期结果**：
- HTTP 200
- 返回数据集 ID

记录数据集 ID：
```bash
DATASET_ID="<返回的数据集ID>"
```

### 3.3 查询数据集

**接口**：`GET /api/datasets/{dataset_id}`

```bash
curl http://localhost:8000/api/datasets/$DATASET_ID
```

**预期结果**：
- HTTP 200
- 返回数据集详情，包含 `name`, `total_row_count`, `files` 等字段

### 3.4 创建实验

**接口**：`POST /api/experiments/`

**请求格式**：config 必须包含 `xgboost_params` 子对象

```bash
curl -X POST http://localhost:8000/api/experiments/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test Experiment",
    "description": "Integration test experiment",
    "dataset_id": "'$DATASET_ID'",
    "config": {
      "task_type": "regression",
      "test_size": 0.2,
      "random_seed": 42,
      "xgboost_params": {
        "n_estimators": 10,
        "max_depth": 3,
        "learning_rate": 0.1
      }
    }
  }'
```

**预期结果**：
- HTTP 200
- 返回实验 ID

记录实验 ID：
```bash
EXPERIMENT_ID="<返回的实验ID>"
```

### 3.5 启动训练

**接口**：`POST /api/experiments/{experiment_id}/start`

```bash
curl -X POST http://localhost:8000/api/experiments/$EXPERIMENT_ID/start
```

**预期结果**：
- HTTP 200
- 返回 `{"status": "queued", "experiment_id": "...", ...}`

### 3.6 查询训练状态

**接口**：`GET /api/training/{experiment_id}/status`

```bash
# 等待几秒让 Worker 消费任务
sleep 5

curl http://localhost:8000/api/training/$EXPERIMENT_ID/status
```

**预期结果**：
- HTTP 200
- 状态可能是 `running` 或 `completed`

持续查询直到状态变为 `completed` 或 `failed`：

```bash
# 循环查询
for i in {1..30}; do
  STATUS=$(curl -s http://localhost:8000/api/training/$EXPERIMENT_ID/status | jq -r '.status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" ]]; then
    break
  fi
  sleep 2
done
```

### 3.7 查询实验结果

**接口**：`GET /api/results/{experiment_id}`

```bash
curl http://localhost:8000/api/results/$EXPERIMENT_ID
```

**预期结果**：
- HTTP 200
- 返回实验结果，包含 `metrics`, `feature_importance`, `model` 等字段

### 3.8 下载模型

**接口**：`GET /api/results/{experiment_id}/download-model`

```bash
curl -O -J http://localhost:8000/api/results/$EXPERIMENT_ID/download-model
```

**预期结果**：
- HTTP 200
- 下载文件 `model_{EXPERIMENT_ID}.json`

验证模型文件：

```bash
# 检查文件是否为有效 JSON
python -c "import json; json.load(open('model_${EXPERIMENT_ID}.json'))"
```

### 3.9 查询特征重要性

**接口**：`GET /api/results/{experiment_id}/feature-importance`

```bash
curl "http://localhost:8000/api/results/$EXPERIMENT_ID/feature-importance?top_n=10"
```

**预期结果**：
- HTTP 200
- 返回特征重要性列表

### 3.10 查询指标历史

**接口**：`GET /api/results/{experiment_id}/metrics-history`

```bash
curl http://localhost:8000/api/results/$EXPERIMENT_ID/metrics-history
```

**预期结果**：
- HTTP 200
- 返回训练过程中的损失曲线数据

---

## 4. 异步任务测试

### 4.1 预处理任务

**接口**：`POST /api/datasets/{dataset_id}/preprocess`

**请求体结构**：
```json
{
  "dataset_id": "uuid",
  "config": {
    "missing_value_strategy": "mean",
    "remove_duplicates": true,
    "handle_outliers": false
  }
}
```

```bash
curl -X POST http://localhost:8000/api/datasets/$DATASET_ID/preprocess \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "'$DATASET_ID'",
    "config": {
      "missing_value_strategy": "mean",
      "remove_duplicates": true,
      "handle_outliers": false
    }
  }'
```

**预期结果**：
- HTTP 200
- 返回任务 ID

记录任务 ID：
```bash
TASK_ID="<返回的任务ID>"
```

### 4.2 查询异步任务状态

**接口**：`GET /api/datasets/tasks/{task_id}`

```bash
curl http://localhost:8000/api/datasets/tasks/$TASK_ID
```

**预期结果**：
- HTTP 200
- 返回任务状态和结果，包含 `status`, `config`, `result` 等字段

---

## 5. 存储模式切换测试

### 5.1 Local 存储模式

默认模式，数据存储在 `WORKSPACE_DIR` 目录下。

验证存储：
```bash
# 检查模型文件
ls -la ./workspace/models/

# 检查预处理输出
ls -la ./workspace/preprocessing/
```

### 5.2 MinIO 存储模式

**前置条件**：MinIO 服务已启动

修改 `.env`：
```bash
STORAGE_TYPE=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=xgboost-vis
MINIO_SECURE=false
```

重启 API 和 Worker 服务后重新执行冒烟测试。

验证 MinIO 存储：
```bash
# 使用 MinIO Client (mc)
mc alias set local http://localhost:9000 minioadmin minioadmin
mc ls local/xgboost-vis/models/
```

---

## 6. 已知限制

| 限制 | 说明 | 影响 |
|------|------|------|
| 单 Worker 实例 | 当前仅支持单 Worker 实例 | 无法水平扩展 |
| 无 WebSocket | 训练进度通过轮询获取 | 实时性受限 |
| 无认证授权 | API 无身份验证 | 仅限内网部署 |
| 无暂停/恢复 | 训练任务不支持暂停 | 无法中断后继续 |
| 文件格式限制 | 仅支持 CSV 格式数据集 | 不支持 Parquet 等 |

---

## 7. 故障排查

### 7.1 API 启动失败

```bash
# 检查端口占用
lsof -i :8000

# 检查数据库连接
psql $DATABASE_URL -c "SELECT 1"

# 检查 Redis 连接
redis-cli -u $REDIS_URL ping
```

### 7.2 Worker 无法消费任务

```bash
# 检查 Redis 队列
redis-cli -u $REDIS_URL LLEN training:queue

# 检查 Worker 日志
# 确认输出 "Worker started, waiting for tasks..."
```

### 7.3 训练失败

```bash
# 查询实验错误信息
curl http://localhost:8000/api/experiments/$EXPERIMENT_ID

# 检查 Worker 日志中的错误堆栈
```

### 7.4 模型下载失败

```bash
# 检查模型记录
curl http://localhost:8000/api/results/$EXPERIMENT_ID

# 检查存储
# Local 模式
ls -la ./workspace/models/$EXPERIMENT_ID/

# MinIO 模式
mc ls local/xgboost-vis/models/$EXPERIMENT_ID/
```

---

## 8. 快速验证脚本

### 8.1 Linux/macOS Bash 示例

> **注意**：以下脚本仅适用于 Linux/macOS 环境，Windows PowerShell 请参见 8.2 节。

```bash
#!/bin/bash
# 此脚本仅适用于 Linux/macOS

set -e

API_URL="http://localhost:8000"

echo "=== 1. 健康检查 ==="
curl -s $API_URL/health | jq .

echo "=== 2. 创建数据集 ==="
DATASET_RESPONSE=$(curl -s -X POST $API_URL/api/datasets/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test Dataset",
    "description": "Smoke test",
    "target_column": "target",
    "files": [
      {
        "file_path": "./dataset/test.csv",
        "file_name": "test.csv",
        "role": "primary",
        "row_count": 5,
        "column_count": 3,
        "file_size": 60
      }
    ]
  }')
DATASET_ID=$(echo $DATASET_RESPONSE | jq -r '.id')
echo "Dataset ID: $DATASET_ID"

echo "=== 3. 创建实验 ==="
EXP_RESPONSE=$(curl -s -X POST $API_URL/api/experiments/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test",
    "dataset_id": "'$DATASET_ID'",
    "config": {
      "task_type": "regression",
      "test_size": 0.2,
      "xgboost_params": {
        "n_estimators": 10,
        "max_depth": 3
      }
    }
  }')
EXPERIMENT_ID=$(echo $EXP_RESPONSE | jq -r '.id')
echo "Experiment ID: $EXPERIMENT_ID"

echo "=== 4. 启动训练 ==="
curl -s -X POST $API_URL/api/experiments/$EXPERIMENT_ID/start | jq .

echo "=== 5. 等待训练完成 ==="
for i in {1..30}; do
  STATUS=$(curl -s $API_URL/api/training/$EXPERIMENT_ID/status | jq -r '.status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" ]]; then
    break
  fi
  sleep 2
done

echo "=== 6. 查询结果 ==="
curl -s $API_URL/api/results/$EXPERIMENT_ID | jq .

echo "=== 7. 下载模型 ==="
curl -s -o model_$EXPERIMENT_ID.json $API_URL/api/results/$EXPERIMENT_ID/download-model
ls -la model_$EXPERIMENT_ID.json

echo "=== 冒烟测试完成 ==="
```

### 8.2 Windows PowerShell 示例

```powershell
# Windows PowerShell 冒烟测试脚本

$ApiUrl = "http://localhost:8000"

Write-Host "=== 1. 健康检查 ==="
Invoke-RestMethod -Uri "$ApiUrl/health" | ConvertTo-Json

Write-Host "=== 2. 创建数据集 ==="
$datasetBody = @{
    name = "Smoke Test Dataset"
    description = "Smoke test"
    target_column = "target"
    files = @(
        @{
            file_path = "./dataset/test.csv"
            file_name = "test.csv"
            role = "primary"
            row_count = 5
            column_count = 3
            file_size = 60
        }
    )
} | ConvertTo-Json -Depth 3

$datasetResponse = Invoke-RestMethod -Uri "$ApiUrl/api/datasets/" -Method POST -ContentType "application/json" -Body $datasetBody
$datasetId = $datasetResponse.id
Write-Host "Dataset ID: $datasetId"

Write-Host "=== 3. 创建实验 ==="
$expBody = @{
    name = "Smoke Test"
    dataset_id = $datasetId
    config = @{
        task_type = "regression"
        test_size = 0.2
        xgboost_params = @{
            n_estimators = 10
            max_depth = 3
        }
    }
} | ConvertTo-Json -Depth 3

$expResponse = Invoke-RestMethod -Uri "$ApiUrl/api/experiments/" -Method POST -ContentType "application/json" -Body $expBody
$experimentId = $expResponse.id
Write-Host "Experiment ID: $experimentId"

Write-Host "=== 4. 启动训练 ==="
Invoke-RestMethod -Uri "$ApiUrl/api/experiments/$experimentId/start" -Method POST | ConvertTo-Json

Write-Host "=== 5. 等待训练完成 ==="
for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Seconds 2
    $statusResponse = Invoke-RestMethod -Uri "$ApiUrl/api/training/$experimentId/status"
    $status = $statusResponse.status
    Write-Host "Status: $status"
    if ($status -in @("completed", "failed")) {
        break
    }
}

Write-Host "=== 6. 查询结果 ==="
Invoke-RestMethod -Uri "$ApiUrl/api/results/$experimentId" | ConvertTo-Json -Depth 5

Write-Host "=== 7. 下载模型 ==="
Invoke-WebRequest -Uri "$ApiUrl/api/results/$experimentId/download-model" -OutFile "model_$experimentId.json"
Get-Item "model_$experimentId.json"

Write-Host "=== 冒烟测试完成 ==="
```

---

## 附录：API 端点速查表

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 基础健康检查 |
| `/ready` | GET | 就绪检查（含 DB、存储、Redis） |
| `/live` | GET | 存活检查 |
| `/api/datasets/` | POST | 创建数据集（JSON） |
| `/api/datasets/{id}` | GET | 获取数据集详情 |
| `/api/datasets/{id}/preprocess` | POST | 触发预处理任务 |
| `/api/datasets/tasks/{task_id}` | GET | 查询异步任务状态 |
| `/api/experiments/` | POST | 创建实验 |
| `/api/experiments/{id}` | GET | 获取实验详情 |
| `/api/experiments/{id}/start` | POST | 启动训练 |
| `/api/experiments/{id}/stop` | POST | 停止训练 |
| `/api/training/{id}/status` | GET | 查询训练状态 |
| `/api/results/{id}` | GET | 获取实验结果 |
| `/api/results/{id}/download-model` | GET | 下载模型 |
| `/api/results/compare` | POST | 对比多个实验 |
| `/api/results/{id}/export-report` | GET | 导出报告 |

---

**文档版本**：2.1
**创建日期**：2026-03-26
**更新日期**：2026-03-26
**状态**：已核对代码一致性

### 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 2.1 | 2026-03-26 | 修正数据库连接信息与 .env.example、docker-compose.dev.yml 一致；添加 Docker Compose 默认账号说明 |
| 2.0 | 2026-03-26 | 修正所有接口路径、请求格式与当前 API 一致；补充 Windows PowerShell 脚本 |
| 1.0 | 2026-03-26 | 初版 |