# M7-T06 任务汇报：M7-T04 审核修复与证据闭环

任务编号: M7-T06  
时间戳: 20260330-120000  
所属计划: P1-S1 / M7-T04 修复  
前置任务: M7-T04（审核结果：部分通过）  
执行者: GitHub Copilot（直接执行修复）  
汇报时间: 2026-03-30

---

## 一、修复背景

M7-T04 审核发现 3 个阻断项：

| # | 阻断项 | 严重级别 |
|---|--------|---------|
| 1 | 测试结果失实：报告声称 31 passed，实际 2 failed 29 passed（WORKSPACE_DIR 不一致） | 🔴 阻断 |
| 2 | 缺少真实 API 链路证据（无 task_id 强断言、无状态轮询验证） | 🔴 阻断 |
| 3 | 失败场景仅文字描述，无实际命令输出 | 🔴 阻断 |

---

## 二、修复内容

### 修复 2.1：WORKSPACE_DIR 路径不一致

**根因分析**：

Trae 从 `apps/api/` 子目录运行 pytest，导致 `test_workspace_consistency.py` 动态加载 Worker config 时文件路径与预期不同，Worker 的 `Path(__file__).resolve().parents[3]` 在测试环境下解析到 `C:\Users\wangd\project\` 而非 `C:\Users\wangd\project\XGBoost Training Visualizer\`。

**解决方案**：从项目根目录运行所有 pytest 命令（`cd` 到工程根而非 `apps/api`），API 与 Worker 的 `config.py` 逻辑完全对称，无需修改代码。

**正确运行方式**：
```bash
cd "c:\Users\wangd\project\XGBoost Training Visualizer"
python -m pytest apps/api/tests/test_workspace_consistency.py -v
```

**验证结果（Copilot 独立复现）**：
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0
collected 9 items

apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_config_consistency PASSED [ 11%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_is_absolute_path PASSED [ 22%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_points_to_project_root_workspace PASSED [ 33%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_not_empty PASSED [ 44%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_path_format_valid PASSED [ 55%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_exists_or_creatable PASSED [ 66%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_api_workspace_is_absolute PASSED [ 77%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_worker_workspace_is_absolute PASSED [ 88%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_both_services_have_identical_workspace_path PASSED [100%]

============================== 9 passed in 0.16s ==============================
```

✅ **9/9 通过，0 failed**

---

### 修复 2.2：真实 API 链路证据

**修改文件**: `apps/api/tests/test_preprocessing.py`

**修复内容**：
1. 将旧 E2E 测试中允许 404 通过的**弱断言**替换为**强断言**
2. 修正状态查询路径：`/api/tasks/{task_id}` → `/api/datasets/tasks/{task_id}`
3. 增加 `task_type == "preprocessing"` 类型断言

**修改后关键断言**：
```python
# 触发预处理 → 验证 task_id
preprocess_response = await client.post(f"/api/datasets/{dataset_id}/preprocess", json={...})
assert preprocess_response.status_code == 200
task_id = preprocess_response.json()["task_id"]
assert task_id is not None
assert preprocess_response.json()["status"] == "queued"

# 验证任务状态可查询（强断言，不再允许 404 通过）
status_response = await client.get(f"/api/datasets/tasks/{task_id}")
assert status_response.status_code == 200
status_data = status_response.json()
assert status_data["id"] == task_id
assert status_data["status"] in ["queued", "running", "completed"]
assert status_data["task_type"] == "preprocessing"
```

**同步修复** (`apps/api/app/routers/datasets.py`)：  
`preprocess_dataset` 端点的 `task_config` 中补上之前缺失的：
- `encoding_strategy`
- `target_columns`

**验证**：
```
python -m pytest apps/api/tests/test_preprocessing.py -v --tb=short

apps\api\tests\test_preprocessing.py::TestPreprocessingValidation::test_preprocessing_valid_config PASSED [ 25%]
apps\api\tests\test_preprocessing.py::TestPreprocessingValidation::test_preprocessing_invalid_missing_value_strategy PASSED [ 50%]
apps\api\tests\test_preprocessing.py::TestPreprocessingValidation::test_preprocessing_invalid_encoding_strategy PASSED [ 75%]
apps\api\tests\test_preprocessing.py::TestPreprocessingEndToEnd::test_preprocessing_end_to_end PASSED [100%]

============================== 4 passed in 1.27s ==============================
```

✅ **4/4 通过，E2E 链路测试含 task_id 强断言**

---

### 修复 2.3：失败场景真实命令输出

**执行命令**：
```bash
cd apps/api
python -c "
from app.schemas.dataset import PreprocessingConfig
from pydantic import ValidationError

print('--- 场景 1: 无效的缺失值处理策略 ---')
try:
    PreprocessingConfig(missing_value_strategy='invalid_strategy')
except ValidationError as e:
    print(str(e))

print('--- 场景 2: 无效的编码策略 ---')
try:
    PreprocessingConfig(encoding_strategy='bad_encoding')
except ValidationError as e:
    print(str(e))
"
```

**实际输出**：
```
--- 场景 1: 无效的缺失值处理策略 ---
1 validation error for PreprocessingConfig
missing_value_strategy
  Input should be 'forward_fill', 'mean_fill' or 'drop_rows' [type=enum, input_value='invalid_strategy', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/enum

--- 场景 2: 无效的编码策略 ---
1 validation error for PreprocessingConfig
encoding_strategy
  Input should be 'one_hot' or 'label_encoding' [type=enum, input_value='bad_encoding', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/enum
```

✅ **字段级错误定位精确，枚举约束有效**

---

## 三、修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `apps/api/tests/test_preprocessing.py` | 状态查询路径修正；弱断言替换为强断言；增加 task_type 断言 |
| `apps/api/app/routers/datasets.py` | `task_config` 补上 `encoding_strategy` 和 `target_columns` |

---

## 四、完整测试结果（Copilot 独立执行）

```
python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_workspace_consistency.py apps/api/tests/test_preprocessing.py --tb=short -v

============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0 -- C:\Python314\python.exe
rootdir: C:\Users\wangd\project\XGBoost Training Visualizer\apps\api
configfile: pytest.ini
collected 35 items

apps\api\tests\test_new_endpoints.py::TestPreprocessingEndpoints::test_preprocess_dataset PASSED [  2%]
apps\api\tests\test_new_endpoints.py::TestPreprocessingEndpoints::test_preprocess_dataset_not_found PASSED [  5%]
apps\api\tests\test_new_endpoints.py::TestFeatureEngineeringEndpoints::test_feature_engineering_dataset PASSED [  8%]
apps\api\tests\test_new_endpoints.py::TestDatasetSplitEndpoint::test_split_dataset PASSED [ 11%]
apps\api\tests\test_new_endpoints.py::TestHealthEndpoints::test_health_endpoint PASSED [ 14%]
apps\api\tests\test_new_endpoints.py::TestHealthEndpoints::test_live_endpoint PASSED [ 17%]
apps\api\tests\test_new_endpoints.py::TestStopExperimentLogic::test_stop_queued_experiment PASSED [ 20%]
apps\api\tests\test_new_endpoints.py::TestStopExperimentLogic::test_version_bound_to_payload PASSED [ 22%]
apps\api\tests\test_new_endpoints.py::TestStopExperimentLogic::test_training_task_model_has_version_field PASSED [ 25%]
apps\api\tests\test_new_endpoints.py::TestLambdaFieldSerialization::test_lambda_field_in_config PASSED [ 28%]
apps\api\tests\test_new_endpoints.py::TestReadyEndpoint::test_ready_endpoint_all_services PASSED [ 31%]
apps\api\tests\test_new_endpoints.py::TestReadyEndpoint::test_ready_endpoint_returns_checks PASSED [ 34%]
apps\api\tests\test_new_endpoints.py::TestDownloadModelEndpoint::test_download_model_not_found PASSED [ 37%]
apps\api\tests\test_new_endpoints.py::TestDownloadModelEndpoint::test_download_model_invalid_id PASSED [ 40%]
apps\api\tests\test_new_endpoints.py::TestDownloadModelEndpoint::test_download_model_no_model PASSED [ 42%]
apps\api\tests\test_new_endpoints.py::TestExportReportEndpoint::test_export_report_not_found PASSED [ 45%]
apps\api\tests\test_new_endpoints.py::TestExportReportEndpoint::test_export_report_invalid_id PASSED [ 48%]
apps\api\tests\test_new_endpoints.py::TestExportReportEndpoint::test_export_report_json_format PASSED [ 51%]
apps\api\tests\test_new_endpoints.py::TestExportReportEndpoint::test_export_report_csv_format PASSED [ 54%]
apps\api\tests\test_new_endpoints.py::TestAsyncTaskPersistence::test_preprocessing_task_creates_db_record PASSED [ 57%]
apps\api\tests\test_new_endpoints.py::TestAsyncTaskPersistence::test_feature_engineering_task_creates_db_record PASSED [ 60%]
apps\api\tests\test_new_endpoints.py::TestAsyncTaskPersistence::test_list_dataset_tasks PASSED [ 62%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_config_consistency PASSED [ 65%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_is_absolute_path PASSED [ 68%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_points_to_project_root_workspace PASSED [ 71%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_not_empty PASSED [ 74%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_path_format_valid PASSED [ 77%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_exists_or_creatable PASSED [ 80%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_api_workspace_is_absolute PASSED [ 82%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_worker_workspace_is_absolute PASSED [ 85%]
apps\api\tests\test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_both_services_have_identical_workspace_path PASSED [ 88%]
apps\api\tests\test_preprocessing.py::TestPreprocessingValidation::test_preprocessing_valid_config PASSED [ 91%]
apps\api\tests\test_preprocessing.py::TestPreprocessingValidation::test_preprocessing_invalid_missing_value_strategy PASSED [ 94%]
apps\api\tests\test_preprocessing.py::TestPreprocessingValidation::test_preprocessing_invalid_encoding_strategy PASSED [ 97%]
apps\api\tests\test_preprocessing.py::TestPreprocessingEndToEnd::test_preprocessing_end_to_end PASSED [100%]

============================= 35 passed in 10.18s =============================
```

---

## 五、完成判定清单

- [x] `test_workspace_consistency.py` 全部通过（9/9，0 failed）
- [x] `test_new_endpoints.py` + `test_workspace_consistency.py` 合计通过 ≥ 31（实际 31/31，0 failed）
- [x] `test_preprocessing.py` 包含 E2E 链路测试，含 task_id 强断言（4/4 通过）
- [x] 失败场景有真实命令输出（见 §2.3，enm 枚举拒绝字段级定位精确）
- [x] 汇报如实标注所有测试结果（总计 **35 passed, 0 failed**）
