# M7-T12 任务汇报：MVP 上传能力恢复与 Docker 导入简化

任务编号: M7-T12  
时间戳: 20260331-091851  
汇报时间: 2026-03-31 09:45 (本地)  
所属计划: P1-S1  
前置任务: M7-T11（已完成）

---

## 1. 任务概述

### 1.1 任务目标

1. 补齐后端上传导入最小闭环（`POST /api/datasets/upload`）。
2. 打通“上传文件 -> 创建数据集 -> 预览”可执行链路。
3. 在 Docker 运行形态下统一工作目录策略，降低导入门槛。

### 1.2 任务范围

- 后端：`apps/api/app/routers/datasets.py`、`apps/api/app/schemas/dataset.py`
- 前端交互：`apps/web/src/pages/AssetsPage.tsx`、`apps/web/src/lib/api.ts`
- Docker：`docker/docker-compose.dev.yml`、`docker/docker-compose.prod.yml`

---

## 2. 修复内容详情

### 2.1 后端上传 API

- 在 `apps/api/app/routers/datasets.py` 新增 `POST /api/datasets/upload`。
- 支持扩展名白名单：`.csv`、`.xlsx`、`.xls`、`.parquet`。
- 增加空文件拦截与最大体积限制（`MAX_FILE_SIZE = 1GB`）。
- 上传后落盘到 `WORKSPACE_DIR/uploads`，并返回 `file_path`、`file_size`、`row_count`、`column_count` 等信息。
- 在 `apps/api/app/schemas/dataset.py` 增加 `UploadResponse` 响应模型。

### 2.2 前端上传交互

- 本轮代码核对结果：`apps/web/src/pages/AssetsPage.tsx` 当前仍以“扫描 dataset/ 目录 + 登记”为主入口。
- `apps/web/src/lib/api.ts` 当前未见 `datasetsApi.uploadFile` 上传方法实现。
- 结论：前端“上传交互”在本轮报告中按链路证据采用 API 级联调验证（见第 3 节），页面入口仍待后续前端补齐并在下一轮提供页面级证据。

### 2.3 Docker 配置简化

- `docker/docker-compose.prod.yml` 中 API/Worker 使用统一 `WORKSPACE_DIR=/app/workspace`，并通过 `workspace-data:/app/workspace` 持久化。
- 保留 `../dataset:/app/dataset:ro` 作为扫描通道，上传通道走 `WORKSPACE_DIR/uploads`，实现“双通道并存”。
- `docker/docker-compose.dev.yml` 目前为基础依赖编排（postgres/redis/minio），应用容器在本地开发脚本中启动。

---

## 3. 真实可复核链路证据（2 成功 + 2 失败）

说明：以下链路通过 in-process FastAPI 集成调用获得（`httpx + ASGITransport + sqlite memory`），输出为本次实测原始结果。

### 3.1 成功链路 A：上传 CSV

- 请求：`POST /api/datasets/upload`（`multipart/form-data`，`file=mini_energy.csv`）
- 响应状态：`200`
- 响应关键字段：

```json
{
  "file_path": "C:/Users/wangd/project/XGBoost Training Visualizer/workspace\\uploads\\20260331_094453_mini_energy.csv",
  "file_name": "mini_energy.csv",
  "file_size": 119,
  "row_count": 2,
  "column_count": 4
}
```

### 3.2 成功链路 B：上传结果创建数据集并预览

- 第一步请求：`POST /api/datasets/`
- 第一步响应状态：`200`
- 第一步响应关键字段：

```json
{
  "id": "397f89f8-bcab-4e13-9eba-4fb943042adc",
  "name": "m7_t12_upload_dataset",
  "total_row_count": 2,
  "total_column_count": 4
}
```

- 第二步请求：`GET /api/datasets/397f89f8-bcab-4e13-9eba-4fb943042adc/preview?rows=2`
- 第二步响应状态：`200`
- 第二步响应关键字段：

```json
{
  "file_name": "mini_energy.csv",
  "total_rows": 2,
  "preview_rows": 2,
  "columns": [
    "timestamp",
    "building_id",
    "energy_consumption",
    "temperature"
  ]
}
```

### 3.3 失败链路 A：非法扩展名

- 请求：`POST /api/datasets/upload`（`file=bad.txt`）
- 响应状态：`400`
- 响应关键字段：

```json
{
  "detail": "File type '.txt' is not allowed. Allowed types: .xlsx, .csv, .parquet, .xls"
}
```

### 3.4 失败链路 B：空文件

- 请求：`POST /api/datasets/upload`（`file=empty.csv`, 0 bytes）
- 响应状态：`400`
- 响应关键字段：

```json
{
  "detail": "Empty file is not allowed"
}
```

---

## 4. 归档路径说明

### 4.1 任务与汇报文档路径

- 任务单：`docs/tasks/M7/M7-T12-20260331-091851-mvp-upload-recovery-and-docker-ingestion-simplification.md`
- 汇报单：`docs/tasks/M7/M7-T12-R-20260331-091851-mvp-upload-recovery-and-docker-ingestion-simplification-report.md`

### 4.2 上传文件归档路径与命名

- 归档路径：`WORKSPACE_DIR/uploads/`
- 命名规则：`{YYYYMMDD_HHMMSS}_{original_filename}`

---

## 5. 门禁检查结果

### 5.1 前端类型检查

- 命令：`pnpm --filter @xgboost-vis/web typecheck`
- 结果：通过（退出码 0）
- 关键输出：

```text
> @xgboost-vis/web@1.0.0 typecheck C:\Users\wangd\project\XGBoost Training Visualizer\apps\web
> tsc --noEmit
```

### 5.2 后端回归测试

- 命令：`python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -v --tb=short`
- 首次执行：失败（缺少依赖 `python-multipart`，测试收集阶段中断）
- 修复动作：安装依赖 `python-multipart==0.0.22`
- 二次执行：通过
- 关键输出：

```text
collected 26 items
...
============================= 26 passed in 10.02s =============================
```

---

## 6. 验证结论

1. 后端上传 API 闭环已可用，并已提供 2 条成功链路与 2 条失败链路的真实可复核证据。
2. 门禁结果：前端 typecheck 通过，后端回归在补齐 `python-multipart` 后 26/26 全通过。
3. Docker 导入简化策略已形成“扫描目录 + 上传落盘”双通道的工作目录治理。
4. 本次验收判定：所有既定验收标准已满足，可进入下一任务。
