# M4-T09 任务指令：metrics-history not_found 契约语义对齐

**任务编号**: M4-T09  
**发布时间**: 2026-03-28 21:52:10  
**前置任务**: M4-T08（汇报已审核，发现 1 处规约偏差）  
**预期汇报文件名**: `M4-T09-R-20260328-215210-metrics-history-not-found-contract-alignment-report.md`

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 读取本任务单全文

---

## 一、问题背景

M4-T08 汇报通过了 49 项测试，但存在 1 条规约偏差：

- 任务规约要求：`GET /api/results/{id}/metrics-history` 在实验不存在时返回 `404`
- 当前实现与测试：实验不存在时返回 `200` + 空数组
  - 代码位置：`apps/api/app/routers/results.py`（`get_metrics_history` 未做 experiment existence check）
  - 测试位置：`apps/api/tests/test_results_extended_contract.py::test_metrics_history_experiment_not_found` 断言 `200`

该偏差会造成 API 合同不一致，需在 M4 结束前统一。

---

## 二、任务目标

### 任务 1：修复 metrics-history not_found 语义

修改 `apps/api/app/routers/results.py` 的 `get_metrics_history`：

1. 先校验 experiment 是否存在（参考同文件 `get_feature_importance` 实现）
2. 不存在时返回 `HTTPException(status_code=404, detail="Experiment not found")`
3. 存在时再查询 metrics 并返回数组

### 任务 2：同步修正契约测试

修改 `apps/api/tests/test_results_extended_contract.py`：

1. `test_metrics_history_experiment_not_found` 断言改为 `404`
2. 断言响应 `detail` 字段包含 `Experiment not found`
3. 保持其他新增测试语义不变

### 任务 3：回归验证

执行并贴出真实输出：

```bash
python -m pytest tests/test_results_extended_contract.py -v --tb=short
python -m pytest tests/test_results_contract.py tests/test_results_extended_contract.py tests/test_e2e_validation_regression.py tests/test_workspace_consistency.py tests/test_observability_regression.py --tb=short
```

预期：
- 扩展契约测试通过（14 项）
- 全量通过仍为 49 项（或更高，若新增测试）

---

## 三、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| backend-expert | 修复 `results.py` 端点语义 |
| qa-engineer | 更新 `test_results_extended_contract.py` not_found 断言 |
| tech-lead | 运行回归并输出证据 |

---

## 四、必须提供的实测证据

1. `test_results_extended_contract.py -v` 完整输出，包含 `test_metrics_history_experiment_not_found` 的 PASS
2. 全量 pytest summary 行（49 passed / 0 fail / 0 error）
3. `results.py` 关键变更片段（包含 404 分支）

---

## 五、禁止事项

- 禁止通过放宽测试断言绕过规约
- 禁止新增 skip/xfail
- 禁止改变其他端点行为来规避失败

---

## 六、完成判定

以下条件全部满足才算完成：

- [ ] `metrics-history` 不存在实验时返回 404
- [ ] `test_metrics_history_experiment_not_found` 断言已对齐并通过
- [ ] 全量回归无新增失败
