# M4-T07 任务指令：模型类型检测修复 & README 门禁等级固化

**任务编号**: M4-T07  
**发布时间**: 2026-03-28 21:22:56  
**前置任务**: M4-T06（汇报已审核，本任务修复 M4-T06 遗留的 2 处实质性缺陷）  
**预期汇报文件名**: `M4-T07-R-20260328-212256-model-type-detection-and-readme-gate-report.md`

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 读取本任务单全文

---

## 一、任务背景与挂起缺陷说明

M4-T06 已审核，发现 2 处实质性缺陷：

### 缺陷 1：model_type 输出仍为 `unknown`（核心任务目标未达成）

**根因**：`apps/api/scripts/e2e_validation.py` 第 374 行仅做：
```python
model_type = model_data.get("model_type", "unknown")
```

但实际模型文件为 XGBoost 原生 JSON 格式，顶层只有 `learner` 和 `version` 两个字段，**没有 `model_type` 键**。因此无论如何执行，`model_type` 永远返回 `"unknown"`。

**实测模型文件顶层结构**：
```python
# 执行命令后返回：
['learner', 'version']
```

**目标**：让 e2e 最终输出中 `model_validation.model_type` 不再是 `unknown`（应为 `xgboost`），`validation_level` 从 `partial` 升为 `full`。

### 缺陷 2：README 门禁等级章节未实际写入

M4-T06 汇报声称"README 新增门禁等级与判定标准章节"，但实测验证该内容不存在。`README.md` 中无 Worker 状态说明、无模型校验语义、无门禁等级表格。

---

## 二、任务目标

### 任务 1：修复 model_type 检测逻辑（必须实测验证）

**允许的修复策略（二选一）**：

**策略 A（推荐）：在 e2e_validation.py 中增加 XGBoost 原生格式识别**

在 `apps/api/scripts/e2e_validation.py` 中，将 model_type 检测逻辑改为：

```python
# 检测 XGBoost 原生 JSON 格式（有 learner + version 字段）
if "learner" in model_data and "version" in model_data:
    model_type = "xgboost"
    model_format = "json"
elif "model_type" in model_data:
    model_type = model_data["model_type"]
    model_format = model_data.get("format", "json")
else:
    model_type = "unknown"
    model_format = "unknown"
```

同时提取 `has_feature_names` 和 `has_target`：

```python
# XGBoost native 格式中，feature_names 在 learner.feature_names 路径
learner = model_data.get("learner", {})
has_feature_names = bool(learner.get("feature_names", []))
has_target = "objective" in learner.get("learner_model_param", {})
```

**策略 B（备选）：在 Worker 保存模型时写入元数据包装**

在 `apps/worker` 的模型保存逻辑中，将原生 XGBoost JSON 内容包在元数据结构中：
```json
{
  "model_type": "xgboost",
  "format": "json",
  "version": "1.0",
  "saved_at": "...",
  "model_data": { ...原始 XGBoost JSON... }
}
```

此策略影响面更大（需同步修改所有读取模型的逻辑），**不建议使用**。

**验收标准（任务 1）**：
- `pnpm test:e2e:results:json` 输出中 `model_validation.model_type` 为 `xgboost`
- `model_validation.validation_level` 为 `full`
- `model_validation.has_feature_names` 为 `true`（如 XGBoost 模型包含特征名）
- 所有原有回归测试（合计 28 项 + 7 项）仍然通过

### 任务 2：写入 README 门禁等级章节（必须实测验证文本存在）

在 `README.md` 中，**找到"端到端验收"相关章节**，在其后补充以下内容（精确写入）：

```markdown
### 门禁等级与判定标准

端到端验收（`pnpm test:e2e:results:json`）按以下三级判定：

| 等级 | 条件 | 说明 |
|------|------|------|
| **通过** | `success=true`，`model_validation.model_type != "unknown"`，`validation_level="full"` | 生产环境可部署 |
| **降级通过** | `success=true`，Worker 状态 `not_available`（API 服务刚启动未重启） | 可部署，需重启 API 服务激活 Worker 探活 |
| **失败** | `success=false`，核心步骤（split/create/train/result）任一失败 | 禁止部署，需修复后重测 |

#### Worker 状态说明

Worker 状态由 `/api/training/status` 端点提供，字段含义：
- `worker_status: healthy` — Redis 已连接，队列正常
- `worker_status: degraded` — Redis 已连接，队列积压或有异常
- `worker_status: unavailable` — Redis 未连接或端点未加载（需重启 API 服务）

#### 模型校验语义

模型通过 XGBoost 原生 JSON 格式存储（顶层字段：`learner`, `version`）：
- `validation_level: full` — 检测到 XGBoost 原生格式，完整校验通过
- `validation_level: partial` — 模型内容合法 JSON，但未识别具体格式
```

**验收标准（任务 2）**：
- 使用命令 `Select-String README.md -Pattern "门禁等级"` 有匹配行
- 使用命令 `Select-String README.md -Pattern "validation_level"` 有匹配行

---

## 三、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| **backend-expert** | 修改 `e2e_validation.py` 的 model_type 检测逻辑 |
| **qa-engineer** | 更新 `test_observability_regression.py` 中断言 model_type 和 validation_level（如测试依赖旧值需同步更新）；运行全量回归 |
| **tech-writer** | 按规范写入 README 门禁等级章节 |
| **tech-lead** | 整合验证，输出完整证据 |

---

## 四、必须提供的实测证据

汇报中**必须包含实际命令输出**（非示意代码块），具体要求：

1. **`pnpm test:e2e:results:json` 完整 JSON 输出**，其中 `model_validation` 字段必须显示：
   ```
   "model_type": "xgboost",
   "validation_level": "full"
   ```

2. **`python -m pytest tests/test_observability_regression.py -v --tb=short` 输出**，确认仍 7 passed

3. **`python -m pytest tests/test_results_contract.py tests/test_e2e_validation_regression.py tests/test_workspace_consistency.py --tb=short` 输出**，确认仍 28 passed

4. **`Select-String README.md -Pattern "门禁等级"` 的 PowerShell 输出截图或文本**（有行号）

---

## 五、禁止事项

- 禁止在汇报中用"截图示意"或 mock 数据替代真实输出
- 禁止修改 `test_observability_regression.py` 中的断言使其匹配旧值 `unknown`（需同步修改断言为 `xgboost`）
- 禁止伪造 e2e JSON 输出（汇报中的 JSON 必须来自真实运行）
- 禁止在 README 中只添加注释而非实际内容

---

## 六、完成判定

满足以下全部条件，本任务才算完成：

- [ ] `pnpm test:e2e:results:json` 真实输出 `model_type: xgboost`
- [ ] 全量回归测试（28 + 7 = 35 项）全部通过
- [ ] `Select-String README.md -Pattern "门禁等级"` 有匹配
- [ ] 汇报中包含上述所有实测命令输出
