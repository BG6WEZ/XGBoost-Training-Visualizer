# M5-T02 任务汇报：E2E 门禁稳定性与训练队列清理

**任务编号**: M5-T02  
**执行时间**: 2026-03-29  
**汇报文件名**: `M5-T02-R-20260329-172233-e2e-gate-stability-and-queue-drain-report.md`

---

## 一、任务完成状态

| 任务项 | 状态 | 说明 |
|--------|------|------|
| 任务1：定位并修复 e2e 超时根因 | ✅ 完成 | 根因：队列积压+Worker未运行 |
| 任务2：恢复 e2e 门禁通过 | ✅ 完成 | 连续两次 success=true |
| 任务3：补充回归保护 | ✅ 完成 | 新增 8 项测试 |

---

## 二、根因分析

### 2.1 问题现象

M5-T01 汇报中 e2e 测试连续失败：
- 第一次复测：`success=false`，错误 `Training did not complete within 120 seconds`，`queue_position=2`
- 第二次复测：`success=false`，错误同上，`queue_position=3`

### 2.2 根因定位

通过检查队列状态发现：

```
队列状态: {'worker_status': 'healthy', 'redis_status': 'connected', 'queue_length': 3, 'active_experiments': 0}

排队/运行中的实验: 3
  - a5b57a90-8dbe-42a2-8bd1-9d3af08ba87f: queued - E2E Validation Experiment 2026-03-29T17:20:19
  - 83ea4017-f80d-4928-80f8-47c89c6420ba: queued - E2E Validation Experiment 2026-03-29T17:18:03
  - 6c8a4b1e-ed3f-467c-a555-01273a5eaea7: queued - E2E Validation Experiment 2026-03-29T17:15:37
```

**根因**：
1. **队列积压**：3 个 queued 状态的实验在队列中等待
2. **Worker 未运行**：`active_experiments=0` 说明没有 Worker 在消费队列
3. **新任务排队**：新提交的 e2e 测试任务被排在队列末尾，等待超时

---

## 三、修复措施

### 3.1 启动 Worker 消费积压

```bash
cd apps/worker && python -m app.main
```

Worker 启动后立即开始消费积压任务，队列清空。

### 3.2 新增队列健康前置检查

修改 [e2e_validation.py](file:///c:/Users/wangd/project/XGBoost%20Training%20Visualizer/apps/api/scripts/e2e_validation.py#L333-L353)：

```python
# 队列健康前置检查
worker_status = service_status.get("worker", {})
queue_length = worker_status.get("queue_length", 0)
if queue_length > 0:
    results.steps["queue_check"] = {"queue_length": queue_length, "status": "waiting"}
    max_wait = 60
    wait_start = datetime.now()
    while queue_length > 0:
        elapsed = (datetime.now() - wait_start).total_seconds()
        if elapsed > max_wait:
            results.success = False
            results.error = f"Queue not empty after {max_wait}s, queue_length={queue_length}"
            return results
        await asyncio.sleep(3)
        status_resp = await client.get(f"{api_url}/api/training/status")
        if status_resp.status_code == 200:
            queue_length = status_resp.json().get("queue_length", 0)
    results.steps["queue_check"] = {"status": "cleared", "wait_seconds": ...}
```

---

## 四、实测证据

### 4.1 第一次 e2e 测试

```json
{
  "success": true,
  "experiment_id": "2989c038-fa74-4d51-8b4f-ce65eb4de7b0",
  "steps": {
    "service_check": {
      "api": {"status": "healthy", "version": "1.0.0"},
      "worker": {"status": "healthy", "queue_length": 0}
    },
    "start_training": {"status": "success", "queue_position": 0},
    "model_validation": {"status": "success", "model_type": "xgboost"}
  },
  "duration_seconds": 3.580056
}
```

### 4.2 第二次 e2e 测试

```json
{
  "success": true,
  "experiment_id": "22e3e92b-f71d-48e4-b1ae-6407f465dcd9",
  "steps": {
    "service_check": {
      "api": {"status": "healthy", "version": "1.0.0"},
      "worker": {"status": "healthy", "queue_length": 0}
    },
    "start_training": {"status": "success", "queue_position": 0},
    "model_validation": {"status": "success", "model_type": "xgboost"}
  },
  "duration_seconds": 3.483782
}
```

### 4.3 新增回归测试

```
============================= test session starts =============================
tests/test_queue_health_check.py::TestE2EResultsModel::test_success_parsing PASSED
tests/test_queue_health_check.py::TestE2EResultsModel::test_failure_parsing PASSED
tests/test_queue_health_check.py::TestE2EResultsModel::test_to_dict PASSED
tests/test_queue_health_check.py::TestQueueWaitLogic::test_queue_empty_no_wait PASSED
tests/test_queue_health_check.py::TestQueueWaitLogic::test_queue_has_items_needs_wait PASSED
tests/test_queue_health_check.py::TestQueueWaitLogic::test_queue_timeout_threshold PASSED
tests/test_queue_health_check.py::TestTimeoutConfiguration::test_default_timeout_is_reasonable PASSED
tests/test_queue_health_check.py::TestTimeoutConfiguration::test_timeout_can_be_configured PASSED
============================== 8 passed in 0.28s ==============================
```

### 4.4 回归测试验证

```
tests/test_e2e_validation_regression.py::TestHealthCheckEndpoints::test_health_endpoint_path PASSED
tests/test_e2e_validation_regression.py::TestHealthCheckEndpoints::test_ready_endpoint_path PASSED
tests/test_e2e_validation_regression.py::TestStatusCodeChecks::test_create_experiment_accepts_200 PASSED
tests/test_e2e_validation_regression.py::TestStatusCodeChecks::test_create_experiment_accepts_201 PASSED
tests/test_e2e_validation_regression.py::TestTargetColumnSelection::test_selects_column_without_missing_values PASSED
tests/test_e2e_validation_regression.py::TestErrorOutput::test_e2e_results_to_dict PASSED
tests/test_e2e_validation_regression.py::TestErrorOutput::test_e2e_results_failure PASSED
tests/test_e2e_validation_regression.py::TestDatasetSelection::test_prefers_demo_test_dataset PASSED
tests/test_e2e_validation_regression.py::TestDatasetSelection::test_prefers_smoke_test_dataset PASSED
tests/test_e2e_validation_regression.py::TestDatasetSelection::test_demo_test_has_priority_over_smoke_test PASSED
============================= 10 passed in 0.18s ==============================
```

---

## 五、完成判定检查

- [x] 已定位并说明 e2e 超时根因
- [x] 连续两次 `pnpm test:e2e:results:json` 均 `success=true`
- [x] 新增至少 1 个回归测试并通过
- [x] 汇报证据与实测输出一致

---

## 六、结论

M5-T02 任务全部完成。

**根因**：队列积压 3 个 queued 实验，但 Worker 未运行导致无人消费，新任务排队等待超时。

**修复**：
1. 启动 Worker 消费积压
2. 在 e2e_validation.py 中新增队列健康前置检查，最多等待 60 秒队列清空

**验证**：
- 连续两次 e2e 测试均 success=true，耗时约 3.5 秒
- 新增 8 项回归测试全部通过
- 原有 10 项回归测试全部通过
