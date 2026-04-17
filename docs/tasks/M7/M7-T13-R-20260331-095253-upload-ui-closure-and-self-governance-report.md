# M7-T13 任务汇报：上传导入前端闭环与自执行治理收口

任务编号: M7-T13  
时间戳: 20260331-095253  
所属计划: P1-S1 / MVP 导入体验补齐  
前置任务: M7-T12  
完成状态: 已完成

---

## 一、任务概述

本任务针对 M7-T12 遗留的前端缺口进行闭环：后端上传 API 已可用，但页面未提供上传入口。通过本轮改造，资产页已形成“上传导入（推荐）+ 扫描登记（批量）+ 已登记数据集”三入口，用户可完成上传并直接创建数据集。

---

## 二、修复内容详情

### 2.1 前端 API 契约补齐

修改文件：`apps/web/src/lib/api.ts`

新增内容：

1. `datasetsApi.uploadFile(file)`，使用 `multipart/form-data` 调用 `/api/datasets/upload`。
2. 新增上传响应类型：`UploadResponse`、`UploadColumnInfo`。
3. 保持原有 `datasetsApi.create` 契约不变，上传后复用创建数据集接口。

### 2.2 资产页上传闭环实现

修改文件：`apps/web/src/pages/AssetsPage.tsx`

新增能力：

1. 页签扩展为：`upload` / `scan` / `registered`。
2. 上传导入页支持文件选择与上传触发。
3. 上传成功后回显文件信息、列信息，并自动推荐时间列/目标列候选。
4. 提供数据集名称、描述、时间列、目标列输入。
5. 一键创建数据集并刷新列表，创建成功后自动切换到已登记页签。
6. 上传错误和创建错误均提供可见提示。
7. 扫描页增加场景说明，明确“上传导入优先用于临时文件”。

### 2.3 范围控制

- 未修改后端业务代码。
- 未修改训练与结果分析相关模块。
- 仅在允许范围内完成前端闭环补齐。

---

## 三、真实可复核链路证据

### 3.1 成功链路 A：上传 CSV

请求：`POST /api/datasets/upload`（multipart/form-data）  
响应状态：`200`

响应关键字段：

```json
{
  "file_path": "C:/Users/wangd/project/XGBoost Training Visualizer/workspace\\uploads\\20260331_095432_mini_energy.csv",
  "file_name": "mini_energy.csv",
  "file_size": 119,
  "row_count": 2,
  "column_count": 4
}
```

### 3.2 成功链路 B：创建数据集并预览

第一步请求：`POST /api/datasets/`  
第一步响应状态：`200`

第一步响应关键字段：

```json
{
  "id": "5ec03dd7-6782-41fb-b477-13dd6e7a570f",
  "name": "m7_t13_upload_dataset",
  "total_row_count": 2,
  "total_column_count": 4
}
```

第二步请求：`GET /api/datasets/5ec03dd7-6782-41fb-b477-13dd6e7a570f/preview?rows=2`  
第二步响应状态：`200`

第二步响应关键字段：

```json
{
  "file_name": "mini_energy.csv",
  "total_rows": 2,
  "preview_rows": 2,
  "columns": ["timestamp", "building_id", "energy_consumption", "temperature"]
}
```

### 3.3 失败链路 A：非法扩展名

请求：`POST /api/datasets/upload`（`bad.txt`）  
响应状态：`400`

```json
{
  "detail": "File type '.txt' is not allowed. Allowed types: .csv, .xlsx, .xls, .parquet"
}
```

### 3.4 失败链路 B：空文件

请求：`POST /api/datasets/upload`（`empty.csv`，0 bytes）  
响应状态：`400`

```json
{
  "detail": "Empty file is not allowed"
}
```

---

## 四、归档路径说明

1. 任务单：`docs/tasks/M7/M7-T13-20260331-095253-upload-ui-closure-and-self-governance.md`
2. 汇报单：`docs/tasks/M7/M7-T13-R-20260331-095253-upload-ui-closure-and-self-governance-report.md`
3. 代码变更：`apps/web/src/lib/api.ts`、`apps/web/src/pages/AssetsPage.tsx`

---

## 五、门禁检查结果

### 5.1 前端类型检查

命令：`pnpm --filter @xgboost-vis/web typecheck`  
结果：通过

关键输出：

```text
> @xgboost-vis/web@1.0.0 typecheck C:\Users\wangd\project\XGBoost Training Visualizer\apps\web
> tsc --noEmit
```

### 5.2 前端构建

命令：`pnpm --filter @xgboost-vis/web build`  
结果：通过

关键输出：

```text
vite v5.4.21 building for production...
✓ built in 6.47s
```

### 5.3 后端回归

命令：`python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -v --tb=short`  
结果：通过

关键输出：

```text
collected 26 items
...
============================= 26 passed in 10.00s =============================
```

---

## 六、验证结论

1. 上传导入前端闭环已完成，页面可执行“上传 -> 创建数据集”。
2. 扫描登记能力保留，双通道场景已在页面文案中区分。
3. 门禁全部通过，且提供了 2 成功 + 2 失败链路的真实可复核证据。
4. 任务-代码-报告-映射文件闭环已形成，可进入下一任务。
