# M4-T09 阶段汇报 - Metrics-History Not_Found 契约语义对齐

**任务编号**: M4-T09  
**执行日期**: 2026-03-28  
**汇报时间**: 2026-03-28 22:10

---

## 一、问题背景

M4-T08 汇报通过了 49 项测试，但存在 1 条规约偏差：

- **任务规约要求**：`GET /api/results/{id}/metrics-history` 在实验不存在时返回 `404`
- **当前实现与测试**：实验不存在时返回 `200` + 空数组
  - 代码位置：`apps/api/app/routers/results.py`（`get_metrics_history` 未做 experiment existence check）
  - 测试位置：`apps/api/tests/test_results_extended_contract.py::test_metrics_history_experiment_not_found` 断言 `200`

该偏差会造成 API 合同不一致，需在 M4 结束前统一。

---

## 二、已完成任务

### 任务 1：修复 metrics-history not_found 语义 ✅ 已验证通过

修改 `apps/api/app/routers/results.py` 的 `get_metrics_history`：

**修复前**：
```python
@router.get("/{experiment_id}/metrics-history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取指标历史曲线数据"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    # 查询所有指标（未检查实验是否存在）
    result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration.asc())
    )
    metrics = result.scalars().all()

    return {
        "experiment_id": experiment_id,
        "iterations": [m.iteration for m in metrics],
        ...
    }
```

**修复后**：
```python
@router.get("/{experiment_id}/metrics-history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取指标历史曲线数据"""
    try:
        exp_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")

    # 验证实验存在
    result = await db.execute(select(Experiment).where(Experiment.id == exp_uuid))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # 查询所有指标
    result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.experiment_id == exp_uuid)
        .order_by(TrainingMetric.iteration.asc())
    )
    metrics = result.scalars().all()

    return {
        "experiment_id": experiment_id,
        "iterations": [m.iteration for m in metrics],
        ...
    }
```

### 任务 2：同步修正契约测试 ✅ 已验证通过

修改 `apps/api/tests/test_results_extended_contract.py`：

**修复前**：
```python
@pytest.mark.asyncio
async def test_metrics_history_experiment_not_found(self, async_client):
    """测试实验不存在时返回空数据（端点不返回 404，而是返回空数组）"""
    client, _ = async_client
    non_existent_id = str(uuid.uuid4())
    
    response = await client.get(f"/api/results/{non_existent_id}/metrics-history")
    
    # 端点返回 200 和空数组，而不是 404
    assert response.status_code == 200
    data = response.json()
    assert data["iterations"] == []
    assert data["train_loss"] == []
    assert data["val_loss"] == []
```

**修复后**：
```python
@pytest.mark.asyncio
async def test_metrics_history_experiment_not_found(self, async_client):
    """测试实验不存在返回 404"""
    client, _ = async_client
    non_existent_id = str(uuid.uuid4())
    
    response = await client.get(f"/api/results/{non_existent_id}/metrics-history")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Experiment not found" in data["detail"]
```

### 任务 3：回归验证 ✅ 已验证通过

**扩展契约测试**：
```bash
python -m pytest tests/test_results_extended_contract.py -v --tb=short
```

**结果**：
```
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

============================== 14 passed in 1.38s ==============================
```

**全量回归测试**：
```bash
python -m pytest tests/test_results_contract.py tests/test_results_extended_contract.py tests/test_e2e_validation_regression.py tests/test_workspace_consistency.py tests/test_observability_regression.py --tb=short
```

**结果**：
```
collected 49 items

tests/test_results_contract.py .........                                 [ 18%]
tests/test_results_extended_contract.py ..............                   [ 46%]
tests/test_e2e_validation_regression.py ..........                       [ 67%]
tests/test_workspace_consistency.py .........                            [ 85%]
tests/test_observability_regression.py .......                           [100%]

============================== 49 passed in 1.75s ==============================
```

---

## 三、修改文件清单

| 文件路径 | 修改目的 |
|----------|----------|
| `apps/api/app/routers/results.py` | 添加实验存在性检查，返回 404 |
| `apps/api/tests/test_results_extended_contract.py` | 修正 not_found 断言为 404 |

---

## 四、验证状态分级

| 项目 | 状态 | 说明 |
|------|------|------|
| metrics-history not_found 语义 | ✅ 已验证通过 | 返回 404 |
| test_metrics_history_experiment_not_found | ✅ 已验证通过 | 断言已对齐 |
| 扩展契约测试 | ✅ 已验证通过 | 14 passed |
| 全量回归测试 | ✅ 已验证通过 | 49 passed |

---

## 五、API 合同一致性验证

| 端点 | 实验不存在时行为 | 状态 |
|------|------------------|------|
| `GET /api/results/{id}` | 返回 404 | ✅ 一致 |
| `GET /api/results/{id}/feature-importance` | 返回 404 | ✅ 一致 |
| `GET /api/results/{id}/metrics-history` | 返回 404 | ✅ 一致（已修复） |
| `GET /api/results/{id}/download-model` | 返回 404 | ✅ 一致 |
| `GET /api/results/{id}/export-report` | 返回 404 | ✅ 一致 |
| `POST /api/results/compare` | 返回 404 | ✅ 一致 |

---

## 六、验收检查清单

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

## 七、是否建议继续下一任务

**建议继续**

**原因**：
1. 任务 1、2、3 均已完成并通过验证
2. metrics-history not_found 语义已对齐
3. 契约测试断言已同步修正
4. 全量回归测试 49 passed
5. API 合同一致性已验证
6. M4 里程碑后端契约测试完整覆盖
