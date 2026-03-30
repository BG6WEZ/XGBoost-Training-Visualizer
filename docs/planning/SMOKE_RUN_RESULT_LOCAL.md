# 本地冒烟联调结果报告

## 概述

**测试日期**：2026-03-26
**测试时间**：13:12 - 13:31
**测试环境**：Windows 11 Pro, Python 3.14.3
**存储模式**：local storage

---

## 环境准备

### 基础设施启动

```bash
# 启动 PostgreSQL 和 Redis
docker compose -f docker/docker-compose.dev.yml up -d postgres redis
```

**结果**：✅ 成功
- PostgreSQL: healthy, 端口 5432
- Redis: running, 端口 6379

### API 启动

```bash
cd apps/api
WORKSPACE_DIR="c:/Users/wangd/project/XGBoost Training Visualizer/workspace" \
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**结果**：✅ 成功
- 服务地址：http://localhost:8000
- 健康检查：`{"status": "healthy"}`

### Worker 启动

```bash
cd apps/worker
WORKSPACE_DIR="c:/Users/wangd/project/XGBoost Training Visualizer/workspace" \
  python -m app.main
```

**结果**：✅ 成功
- 日志输出：`Worker started, waiting for tasks...`

---

## 测试步骤与结果

### 步骤 1：健康检查

**请求**：
```bash
curl -s http://localhost:8000/health
```

**响应**：
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "service": "xgboost-vis-api",
    "timestamp": "2026-03-26T05:12:27.726923"
}
```

**结果**：✅ 成功

---

### 步骤 2：创建数据集

**请求**：
```bash
curl -X POST http://localhost:8000/api/datasets/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test Dataset Final",
    "description": "Final smoke test dataset",
    "target_column": "target",
    "files": [{
      "file_path": "c:/Users/wangd/project/XGBoost Training Visualizer/dataset/test.csv",
      "file_name": "test.csv",
      "role": "primary",
      "row_count": 10,
      "column_count": 3,
      "file_size": 150
    }]
  }'
```

**响应**：
```json
{
    "id": "532ec87d-2a38-42fc-9786-667f8e95f256",
    "name": "Smoke Test Dataset Final",
    "target_column": "target",
    "total_row_count": 10,
    "total_column_count": 3,
    "files": [...]
}
```

**结果**：✅ 成功
- Dataset ID: `532ec87d-2a38-42fc-9786-667f8e95f256`

---

### 步骤 3：创建实验

**请求**：
```bash
curl -X POST http://localhost:8000/api/experiments/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Final Smoke Test",
    "dataset_id": "532ec87d-2a38-42fc-9786-667f8e95f256",
    "config": {
      "task_type": "regression",
      "test_size": 0.2,
      "xgboost_params": {
        "n_estimators": 10,
        "max_depth": 3,
        "learning_rate": 0.1
      }
    }
  }'
```

**响应**：
```json
{
    "id": "7dc81097-ed11-492b-823d-9e22e1a832dc",
    "name": "Final Smoke Test",
    "status": "pending"
}
```

**结果**：✅ 成功
- Experiment ID: `7dc81097-ed11-492b-823d-9e22e1a832dc`

---

### 步骤 4：启动训练

**请求**：
```bash
curl -X POST http://localhost:8000/api/experiments/7dc81097-ed11-492b-823d-9e22e1a832dc/start
```

**响应**：
```json
{
    "status": "queued",
    "experiment_id": "7dc81097-ed11-492b-823d-9e22e1a832dc",
    "message": "Experiment has been queued for training"
}
```

**结果**：✅ 成功

---

### 步骤 5：等待训练完成

**轮询命令**：
```bash
for i in {1..30}; do
  curl -s http://localhost:8000/api/training/{exp_id}/status
  sleep 2
done
```

**状态变化**：
```
[1] Status: running
[2] Status: running
[3] Status: running
[4] Status: running
[5] Status: completed
```

**结果**：✅ 成功
- 训练时间：约 7.5 秒

---

### 步骤 6：查询训练状态

**请求**：
```bash
curl http://localhost:8000/api/training/7dc81097-ed11-492b-823d-9e22e1a832dc/status
```

**响应**：
```json
{
    "experiment_id": "7dc81097-ed11-492b-823d-9e22e1a832dc",
    "status": "completed",
    "progress": 100.0,
    "started_at": "2026-03-26T05:12:29.438330",
    "finished_at": "2026-03-26T05:12:37.022520",
    "error_message": null
}
```

**结果**：✅ 成功

---

### 步骤 7：查询实验结果

**请求**：
```bash
curl http://localhost:8000/api/results/7dc81097-ed11-492b-823d-9e22e1a832dc
```

**响应**：
```json
{
    "experiment_id": "7dc81097-ed11-492b-823d-9e22e1a832dc",
    "experiment_name": "Final Smoke Test",
    "status": "completed",
    "metrics": {
        "train_rmse": 0.182,
        "val_rmse": 0.365,
        "r2": -12.29,
        "mae": null
    },
    "feature_importance": [
        {"feature_name": "value", "importance": 0.144, "rank": 1},
        {"feature_name": "id", "importance": 0.046, "rank": 2}
    ],
    "model": {
        "id": "b8390d61-cbef-4f07-b54e-dba726b67d67",
        "format": "json",
        "file_size": 7585,
        "storage_type": "local",
        "object_key": "models/7dc81097-ed11-492b-823d-9e22e1a832dc/model.json"
    },
    "training_time_seconds": 7.58
}
```

**结果**：✅ 成功

---

### 步骤 8：下载模型

**请求**：
```bash
curl -o model_final.json http://localhost:8000/api/results/7dc81097-ed11-492b-823d-9e22e1a832dc/download-model
```

**文件验证**：
```
-rw-r--r-- 1 wangd 197609 7585 Mar 26 13:31 model_final.json
Model version: [3, 2, 0]
Learner: gbtree
```

**结果**：✅ 成功
- 文件大小：7585 bytes
- 格式：XGBoost JSON model

---

### 步骤 9：触发预处理任务

**请求**：
```bash
curl -X POST http://localhost:8000/api/datasets/532ec87d-2a38-42fc-9786-667f8e95f256/preprocess \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "532ec87d-2a38-42fc-9786-667f8e95f256",
    "config": {
      "missing_value_strategy": "mean",
      "remove_duplicates": true,
      "handle_outliers": false
    }
  }'
```

**响应**：
```json
{
    "task_id": "dbc763ad-cb75-4f16-a917-53ed94f4b592",
    "dataset_id": "532ec87d-2a38-42fc-9786-667f8e95f256",
    "status": "queued",
    "message": "Preprocessing task has been queued"
}
```

**结果**：✅ 成功

---

### 步骤 10：查询异步任务状态

**请求**：
```bash
curl http://localhost:8000/api/datasets/tasks/dbc763ad-cb75-4f16-a917-53ed94f4b592
```

**响应**：
```json
{
    "id": "dbc763ad-cb75-4f16-a917-53ed94f4b592",
    "task_type": "preprocessing",
    "dataset_id": "532ec87d-2a38-42fc-9786-667f8e95f256",
    "status": "completed",
    "error_message": null,
    "config": {
        "missing_value_strategy": "mean",
        "remove_duplicates": true,
        "handle_outliers": false
    },
    "result": {
        "original_shape": [10, 3],
        "processed_shape": [10, 3],
        "storage_type": "local",
        "object_key": "preprocessing/532ec87d.../processed.csv",
        "file_size": 136
    }
}
```

**结果**：✅ 成功

---

## 测试总结

| 步骤 | 描述 | 结果 |
|------|------|------|
| 1 | 健康检查 | ✅ 成功 |
| 2 | 创建数据集 | ✅ 成功 |
| 3 | 创建实验 | ✅ 成功 |
| 4 | 启动训练 | ✅ 成功 |
| 5 | 等待训练完成 | ✅ 成功 |
| 6 | 查询训练状态 | ✅ 成功 |
| 7 | 查询实验结果 | ✅ 成功 |
| 8 | 下载模型 | ✅ 成功 |
| 9 | 触发预处理任务 | ✅ 成功 |
| 10 | 查询异步任务状态 | ✅ 成功 |

**总体结果**：✅ 所有步骤通过

---

## 修复的问题

在冒烟测试过程中发现并修复了以下后端阻塞问题：

### 1. Worker Windows 兼容性问题

**问题**：`add_signal_handler` 在 Windows 上不可用

**修复文件**：`apps/worker/app/main.py`

**修复内容**：
```python
# 添加 Windows 平台检测
if sys.platform != "win32":
    loop.add_signal_handler(sig, signal_handler)
else:
    # Windows: 直接运行，通过 Ctrl+C 终止
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
```

### 2. XGBoost 3.x 回调兼容性问题

**问题**：XGBoost 3.x 要求回调必须是 `TrainingCallback` 实例

**修复文件**：`apps/worker/app/tasks/training.py`

**修复内容**：
```python
# 使用 TrainingCallback 类代替函数回调
class ProgressCallback(xgb.callback.TrainingCallback):
    def after_iteration(self, model, epoch, evals_log):
        # 记录指标
        ...
```

### 3. Worker Model 类字段缺失

**问题**：Worker 的 Model 类缺少 `storage_type` 和 `object_key` 字段

**修复文件**：`apps/worker/app/models.py`

**修复内容**：
```python
class Model(Base):
    storage_type = Column(String(20), default="local")
    object_key = Column(String(500), nullable=True)
    # ...
```

---

## 已知限制

| 限制 | 说明 |
|------|------|
| WORKSPACE_DIR 需要统一 | API 和 Worker 必须使用相同的绝对 WORKSPACE_DIR 路径 |
| scikit-learn 安装问题 | Python 3.14 与某些包版本不兼容 |
| 单 Worker 实例 | 当前仅支持单 Worker 实例 |
| 无 WebSocket | 训练进度通过轮询获取 |

---

## 未验证项

| 项目 | 原因 |
|------|------|
| MinIO 存储模式 | 本次测试仅验证 local storage 模式 |
| 特征工程任务 | 时间限制，仅验证预处理任务 |
| 数据集切分 | 未在本次测试范围内 |
| 实验对比 | 未在本次测试范围内 |
| 报告导出 | 未在本次测试范围内 |

---

## 风险与限制

1. **Python 版本兼容性**：Python 3.14 是较新版本，部分科学计算包可能存在兼容性问题
2. **工作目录配置**：API 和 Worker 需要显式设置相同的 `WORKSPACE_DIR` 环境变量
3. **Windows 信号处理**：Worker 在 Windows 上不支持优雅关闭，需要 Ctrl+C

---

**报告版本**：1.0
**创建日期**：2026-03-26
**测试人员**：Claude (Automated)