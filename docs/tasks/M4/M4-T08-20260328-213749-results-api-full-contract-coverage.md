# M4-T08 任务指令：Results API 完整契约测试覆盖

**任务编号**: M4-T08  
**发布时间**: 2026-03-28 21:37:49  
**前置任务**: M4-T07（已审核通过）  
**预期汇报文件名**: `M4-T08-R-20260328-213749-results-api-full-contract-coverage-report.md`

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 读取本任务单全文

---

## 一、任务背景

当前里程碑评估：

- M0 ✅ M2 ✅ M3 ✅ M4（进行中）
- M4 完成标准（来自 `docs/planning/DEVELOPMENT_PLAN.md`）：
  - "能查看单次结果" — ✅ 已验证（`/api/results/{id}`）
  - "能对比两次以上实验" — ❌ `/api/results/compare` 端点存在但**无测试覆盖**

`apps/api/app/routers/results.py` 共实现 6 个端点：

| 端点 | 状态 |
|------|------|
| `GET /api/results/{id}` | ✅ 有契约测试（9 项，test_results_contract.py） |
| `GET /api/results/{id}/download-model` | ✅ 有 e2e 验证 |
| `GET /api/results/{id}/feature-importance` | ❌ **无测试** |
| `GET /api/results/{id}/metrics-history` | ❌ **无测试** |
| `POST /api/results/compare` | ❌ **无测试** |
| `GET /api/results/{id}/export-report` | ❌ **无测试** |

本任务目标：补全以上 4 个端点的契约测试，完成 M4 后端完整覆盖。

---

## 二、端点规约（实现已存在，请阅读源码确认后编写测试）

源文件：`apps/api/app/routers/results.py`

### 2.1 GET /api/results/{id}/feature-importance

- 参数：`top_n`（默认 20）
- 成功返回 `200`：`experiment_id`, `total_features`, `total_importance`, `features[]`
  - `features[]` 每项：`feature_name`, `importance`, `importance_pct`, `rank`
- 实验不存在返回 `404`
- 无效 UUID 返回 `400`

### 2.2 GET /api/results/{id}/metrics-history

- 成功返回 `200`：`experiment_id`, `iterations[]`, `train_loss[]`, `val_loss[]`, `train_metric[]`, `val_metric[]`
- 实验不存在返回 `404`
- 无效 UUID 返回 `400`

### 2.3 POST /api/results/compare

- Body：`List[str]`（实验 ID 列表）
- 成功返回 `200`：`experiments[]`, `best_val_rmse`, `comparison.best_experiment`
- 少于 2 个实验 ID 返回 `400`（`"At least 2 experiments required for comparison"`）
- 超过 4 个实验 ID 返回 `400`（`"Maximum 4 experiments can be compared at once"`）
- 任意 ID 无效格式返回 `400`

### 2.4 GET /api/results/{id}/export-report

- 参数：`format`（`json` 或 `csv`）
- JSON 格式成功返回 `200`：结构化报告（`experiment_id`, `experiment_name`, `metrics[]`, `feature_importance[]`, `model` 等）
- 实验不存在返回 `404`

---

## 三、任务内容

### 任务 1：新增契约测试文件

创建 `apps/api/tests/test_results_extended_contract.py`，覆盖以下测试场景（最少 12 项测试用例，参考 test_results_contract.py 写法风格）：

**feature-importance 端点（至少 3 项）：**
- 成功路径：返回 200 + 正确字段结构
- 404：实验不存在
- 400：无效 UUID

**metrics-history 端点（至少 3 项）：**
- 成功路径：返回 200 + 正确数组结构
- 404：实验不存在
- 400：无效 UUID

**compare 端点（至少 4 项）：**
- 成功路径：2 个有效实验 ID
- 400：只传 1 个 ID（少于 2）
- 400：传 5 个 ID（超过 4）
- 400：包含无效 UUID 格式

**export-report 端点（至少 2 项）：**
- JSON 格式成功路径
- 404：实验不存在

### 任务 2：运行全量回归（必须 47 项全部通过）

执行命令：
```
python -m pytest tests/test_results_contract.py tests/test_results_extended_contract.py tests/test_e2e_validation_regression.py tests/test_workspace_consistency.py tests/test_observability_regression.py --tb=short
```

预期通过数：原有 35 项 + 新增 ≥12 项 = 至少 47 项

---

## 四、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| **backend-expert** | 阅读 results.py，理解各端点返回结构 |
| **qa-engineer** | 编写 test_results_extended_contract.py（参照 test_results_contract.py 风格） |
| **tech-lead** | 运行全量回归，整合证据输出汇报 |

---

## 五、必须提供的实测证据

汇报中**必须包含以下实际命令输出**：

1. **全量 pytest 运行输出**，显示每个测试文件的通过数、总通过数 ≥47
2. **新增测试文件中，每个测试类名和方法名清单**（`-v` 输出）

---

## 六、禁止事项

- 禁止修改现有 `test_results_contract.py` 中已有的 9 项测试
- 禁止用 `@pytest.mark.skip` 跳过测试使数量达标
- 禁止仅测试 happy path，每个端点必须有 error case 覆盖
- 禁止实现占位 mock 而非真实断言（必须 assert 具体字段）

---

## 七、完成判定

满足以下全部条件：

- [ ] `test_results_extended_contract.py` 文件存在，≥12 个测试用例
- [ ] 全量测试运行通过 ≥47 项，0 fail，0 error
- [ ] 汇报中包含 `-v` 测试列表和 summary 行
