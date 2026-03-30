# M4-T10 阶段汇报 - 无告警回归与 M4 收口确认

**任务编号**: M4-T10  
**执行日期**: 2026-03-28  
**汇报时间**: 2026-03-28 22:25

---

## 一、任务背景

M4-T09 已修复 `metrics-history` 的 404 契约语义，并通过：
- `tests/test_results_extended_contract.py`：14 passed
- 全量回归：49 passed

但在全量回归输出中仍出现非阻断告警：
- `PytestUnhandledThreadExceptionWarning`
- 根因堆栈指向 `aiosqlite` 连接线程在事件循环关闭后回调（`Event loop is closed`）

这类告警会影响 CI 稳定性与质量门禁可信度，需在 M4 正式收口前清理。

---

## 二、已完成任务

### 任务 1：清理 aiosqlite 线程告警 ✅ 已验证通过

**问题定位**：
- `apps/api/tests/test_results_extended_contract.py` 中 `async_client` fixture 创建了 `engine` 但没有在 teardown 时 dispose

**修复方案**：
在 fixture teardown 时显式调用 `await engine.dispose()`

**修复前**：
```python
@pytest_asyncio.fixture
async def async_client():
    """创建异步测试客户端"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    # ... 创建客户端 ...
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session
    
    app.dependency_overrides.clear()
    # 缺少 engine.dispose()
```

**修复后**：
```python
@pytest_asyncio.fixture
async def async_client():
    """创建异步测试客户端"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    # ... 创建客户端 ...
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session
    
    app.dependency_overrides.clear()
    
    # 显式关闭 engine 以避免 aiosqlite 线程告警
    await engine.dispose()
```

### 任务 2：验证告警清零 ✅ 已验证通过

**命令 1**：
```bash
python -m pytest tests/test_results_extended_contract.py -v --tb=short
```

**结果**：
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0
rootdir: c:\Users\wangd\project\XGBoost Training Visualizer\apps\api
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.0.0, html-4.2.0, metadata-3.1.1     
asyncio: mode=Mode.AUTO, debug=False
collected 14 items                                                             

tests/test_results_extended_contract.py::TestFeatureImportanceEndpoint::test_feature_importance_invalid_uuid_format PASSED [  7%]
tests/test_results_extended_contract.py::TestFeatureImportanceEndpoint::test_feature_importance_experiment_not_found PASSED [ 14%]
tests/test_results_extended_contract.py::TestFeatureImportanceEndpoint::test_feature_importance_success PASSED [ 21%]
tests/test_results_extended_contract.py::TestMetricsHistoryEndpoint::test_metrics_history_invalid_uuid_format PASSED [ 28%]
tests/test_results_extended_contract.py::TestMetricsHistoryEndpoint::test_metrics_history_experiment_not_found PASSED [ 35%]
tests/test_results_extended_contract.py::TestMetricsHistoryEndpoint::test_metrics_history_success PASSED [ 42%]
tests/test_results_extended_contract.py::TestCompareExperimentsEndpoint::test_compare_less_than_2_experiments PASSED [ 50%]
tests/test_results_extended_contract.py::TestCompareExperimentsEndpoint::test_compare_more_than_4_experiments PASSED [ 57%]
tests/test_results_extended_contract.py::TestCompareExperimentsEndpoint::test_compare_invalid_uuid_format PASSED [ 64%]
tests/test_results_extended_contract.py::TestCompareExperimentsEndpoint::test_compare_success PASSED [ 71%]
tests/test_results_extended_contract.py::TestExportReportEndpoint::test_export_report_invalid_uuid_format PASSED [ 78%]
tests/test_results_extended_contract.py::TestExportReportEndpoint::test_export_report_experiment_not_found PASSED [ 85%]
tests/test_results_extended_contract.py::TestExportReportEndpoint::test_export_report_json_success PASSED [ 92%]
tests/test_results_extended_contract.py::TestExportReportEndpoint::test_export_report_csv_format PASSED [100%]

============================= 14 passed in 1.46s ==============================
```

**告警检查**：
- ✅ 无 `PytestUnhandledThreadExceptionWarning`
- ✅ 无 `RuntimeError: Event loop is closed`

**命令 2**：
```bash
python -m pytest tests/test_results_contract.py tests/test_results_extended_contract.py tests/test_e2e_validation_regression.py tests/test_workspace_consistency.py tests/test_observability_regression.py --tb=short
```

**结果**：
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0
rootdir: c:\Users\wangd\project\XGBoost Training Visualizer\apps\api
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.0.0, html-4.2.0, metadata-3.1.1     
asyncio: mode=Mode.AUTO, debug=False
collected 49 items                                                             

tests/test_results_contract.py::TestResultsContract::test_get_results_invalid_id_format PASSED [  2%]
tests/test_results_contract.py::TestResultsContract::test_get_results_not_found PASSED [  4%]
tests/test_results_contract.py::TestResultsContract::test_get_results_success_with_model PASSED [  6%]
tests/test_results_contract.py::TestResultsContract::test_get_results_success_without_model PASSED [  8%]
tests/test_results_contract.py::TestDownloadModelContract::test_download_model_invalid_id_format PASSED [ 10%]
tests/test_results_contract.py::TestDownloadModelContract::test_download_model_experiment_not_found PASSED [ 12%]
tests/test_results_contract.py::TestDownloadModelContract::test_download_model_no_model_record PASSED [ 14%]
tests/test_results_contract.py::TestDownloadModelContract::test_download_model_file_not_found PASSED [ 16%]
tests/test_results_contract.py::TestDownloadModelContract::test_download_model_success PASSED [ 18%]
tests/test_results_extended_contract.py::TestFeatureImportanceEndpoint::test_feature_importance_invalid_uuid_format PASSED [ 20%]
tests/test_results_extended_contract.py::TestFeatureImportanceEndpoint::test_feature_importance_experiment_not_found PASSED [ 22%]
tests/test_results_extended_contract.py::TestFeatureImportanceEndpoint::test_feature_importance_success PASSED [ 24%]
tests/test_results_extended_contract.py::TestMetricsHistoryEndpoint::test_metrics_history_invalid_uuid_format PASSED [ 26%]
tests/test_results_extended_contract.py::TestMetricsHistoryEndpoint::test_metrics_history_experiment_not_found PASSED [ 28%]
tests/test_results_extended_contract.py::TestMetricsHistoryEndpoint::test_metrics_history_success PASSED [ 30%]
tests/test_results_extended_contract.py::TestCompareExperimentsEndpoint::test_compare_less_than_2_experiments PASSED [ 32%]
tests/test_results_extended_contract.py::TestCompareExperimentsEndpoint::test_compare_more_than_4_experiments PASSED [ 34%]
tests/test_results_extended_contract.py::TestCompareExperimentsEndpoint::test_compare_invalid_uuid_format PASSED [ 36%]
tests/test_results_extended_contract.py::TestCompareExperimentsEndpoint::test_compare_success PASSED [ 38%]
tests/test_results_extended_contract.py::TestExportReportEndpoint::test_export_report_invalid_uuid_format PASSED [ 40%]
tests/test_results_extended_contract.py::TestExportReportEndpoint::test_export_report_experiment_not_found PASSED [ 42%]
tests/test_results_extended_contract.py::TestExportReportEndpoint::test_export_report_json_success PASSED [ 44%]
tests/test_results_extended_contract.py::TestExportReportEndpoint::test_export_report_csv_format PASSED [ 46%]
tests/test_e2e_validation_regression.py::TestHealthCheckEndpoints::test_health_endpoint_path PASSED [ 48%]
tests/test_e2e_validation_regression.py::TestHealthCheckEndpoints::test_ready_endpoint_path PASSED [ 51%]
tests/test_e2e_validation_regression.py::TestStatusCodeChecks::test_create_experiment_accepts_200 PASSED [ 53%]
tests/test_e2e_validation_regression.py::TestStatusCodeChecks::test_create_experiment_accepts_201 PASSED [ 55%]
tests/test_e2e_validation_regression.py::TestTargetColumnSelection::test_selects_column_without_missing_values PASSED [ 57%]
tests/test_e2e_validation_regression.py::TestErrorOutput::test_e2e_results_to_dict PASSED [ 59%]
tests/test_e2e_validation_regression.py::TestErrorOutput::test_e2e_results_failure PASSED [ 61%]
tests/test_e2e_validation_regression.py::TestDatasetSelection::test_prefers_demo_test_dataset PASSED [ 63%]
tests/test_e2e_validation_regression.py::TestDatasetSelection::test_prefers_smoke_test_dataset PASSED [ 65%]
tests/test_e2e_validation_regression.py::TestDatasetSelection::test_demo_test_has_priority_over_smoke_test PASSED [ 67%]
tests/test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_config_consistency PASSED [ 69%]
tests/test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_is_absolute_path PASSED [ 71%]
tests/test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_points_to_project_root_workspace PASSED [ 73%]
tests/test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_not_empty PASSED [ 75%]
tests/test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_path_format_valid PASSED [ 77%]
tests/test_workspace_consistency.py::TestWorkspaceConsistency::test_workspace_dir_exists_or_creatable PASSED [ 79%]
tests/test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_api_workspace_is_absolute PASSED [ 81%]
tests/test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_worker_workspace_is_absolute PASSED [ 83%]
tests/test_workspace_consistency.py::TestWorkspaceAbsolutePathValidation::test_both_services_have_identical_workspace_path PASSED [ 85%]
tests/test_observability_regression.py::TestWorkerStatusEndpoint::test_worker_status_endpoint_returns_correct_format PASSED [ 87%]
tests/test_observability_regression.py::TestWorkerStatusEndpoint::test_worker_status_healthy_when_redis_connected PASSED [ 89%]
tests/test_observability_regression.py::TestWorkerStatusEndpoint::test_worker_status_unavailable_when_redis_disconnected PASSED [ 91%]
tests/test_observability_regression.py::TestModelValidationSemantics::test_model_validation_includes_all_fields PASSED [ 93%]
tests/test_observability_regression.py::TestModelValidationSemantics::test_model_validation_partial_for_unknown_type PASSED [ 95%]
tests/test_observability_regression.py::TestWorkerStatusInServiceCheck::test_service_check_includes_worker_status PASSED [ 97%]
tests/test_observability_regression.py::TestWorkerStatusInServiceCheck::test_service_check_worker_unavailable PASSED [100%]

============================= 49 passed in 1.74s ==============================
```

**告警检查**：
- ✅ 无 `PytestUnhandledThreadExceptionWarning`
- ✅ 无 `RuntimeError: Event loop is closed`

### 任务 3：M4 收口核对 ✅ 已验证通过

#### M4 完成标准 1："能查看单次结果"

**证据指针**：

| 接口 | 测试文件 | 测试用例 |
|------|----------|----------|
| `GET /api/results/{id}` | `tests/test_results_contract.py` | `test_get_results_success_with_model` |
| `GET /api/results/{id}` | `tests/test_results_contract.py` | `test_get_results_success_without_model` |
| `GET /api/results/{id}/feature-importance` | `tests/test_results_extended_contract.py` | `test_feature_importance_success` |
| `GET /api/results/{id}/metrics-history` | `tests/test_results_extended_contract.py` | `test_metrics_history_success` |
| `GET /api/results/{id}/download-model` | `tests/test_results_contract.py` | `test_download_model_success` |
| `GET /api/results/{id}/export-report` | `tests/test_results_extended_contract.py` | `test_export_report_json_success` |

#### M4 完成标准 2："能对比两次以上实验"

**证据指针**：

| 接口 | 测试文件 | 测试用例 |
|------|----------|----------|
| `POST /api/results/compare` | `tests/test_results_extended_contract.py` | `test_compare_success` |
| `POST /api/results/compare` | `tests/test_results_extended_contract.py` | `test_compare_less_than_2_experiments` |
| `POST /api/results/compare` | `tests/test_results_extended_contract.py` | `test_compare_more_than_4_experiments` |
| `POST /api/results/compare` | `tests/test_results_extended_contract.py` | `test_compare_invalid_uuid_format` |

---

## 三、修改文件清单

| 文件路径 | 修改目的 |
|----------|----------|
| `apps/api/tests/test_results_extended_contract.py` | 添加 `await engine.dispose()` 清理 aiosqlite 线程告警 |

---

## 四、验收检查清单

- [x] 全量回归仍 49 passed（或更高）
- [x] 无 `PytestUnhandledThreadExceptionWarning`
- [x] 无 `Event loop is closed`
- [x] 汇报包含 M4 收口证据指针
- [x] 只修改了当前任务范围内的内容
- [x] 代码不只是占位实现
- [x] schema/model/router/types/docs 已同步
- [x] 没有残留明显错误字段或旧结构
- [x] 至少做了 1 次实际验证
- [x] 汇报中区分了已验证和未验证部分
- [x] 测试若有跳过，已明确说明原因
- [x] 文档没有把未来方案写成当前现状
- [x] 没有擅自推进后续任务
- [x] 已准备好等待人工验收

---

## 五、M4 里程碑完成确认

| M4 完成标准 | 状态 | 证据 |
|-------------|------|------|
| "能查看单次结果" | ✅ 已验证通过 | 6 个契约测试用例覆盖 |
| "能对比两次以上实验" | ✅ 已验证通过 | 4 个契约测试用例覆盖 |

**M4 里程碑已正式收口。**

---

## 六、是否建议继续下一任务

**建议继续**

**原因**：
1. 任务 1、2、3 均已完成并通过验证
2. 全量回归测试 49 passed，无告警
3. M4 收口证据指针已完整提供
4. 项目处于可运行状态
5. M4 里程碑已正式收口，可进入下一阶段
