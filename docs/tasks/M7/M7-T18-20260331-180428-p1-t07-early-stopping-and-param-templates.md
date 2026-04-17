# M7-T18 任务单：P1-T07 Early Stopping 真实生效 + 参数模板前后端闭环

任务编号: M7-T18  
时间戳: 20260331-180428  
所属计划: P1-S3 / P1-T07  
前置任务: M7-T17（已完成）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T07 验收标准）
- [ ] docs/tasks/M7/M7-T17-20260331-164748-p1-t06-multi-table-join-and-data-fusion.md
- [ ] docs/tasks/M7/M7-T17-R-20260331-164748-p1-t06-multi-table-join-and-data-fusion-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

### 1.1 Early Stopping 现状（审核发现的重要缺陷）

代码审查发现 `apps/api/app/schemas/experiment.py` 中虽然定义了 `early_stopping_rounds` 字段（第 49 行），但 `apps/worker/app/tasks/training.py` 的 `xgb.train()` 调用中**未传入 `early_stopping_rounds` 参数**，导致早停功能实际未生效。

当前训练调用：
```python
self.model = xgb.train(
    params,
    dtrain,
    num_boost_round=n_estimators,
    evals=[(dtrain, 'train'), (dval, 'val')],
    evals_result=evals_result,
    callbacks=[progress_callback],
    verbose_eval=False
)
# 注意：early_stopping_rounds 从未被传入，字段定义是空摆设
```

### 1.2 参数模板现状

前端训练创建页面目前需要用户手动填写所有 XGBoost 参数，没有预设模板辅助选择，对新用户不友好。

---

## 二、任务目标

1. **修复 Early Stopping**：让 `early_stopping_rounds` 从 Schema → API → Worker 全链路真实生效，训练过程中可提前终止并记录 `best_iteration`。
2. **新增三套参数模板**：保守（conservative）、平衡（balanced）、激进（aggressive），前后端联动，选模板后参数自动回填。
3. **前端接入**：实验创建页面支持模板选择，选择后参数表单联动回填，支持手动覆盖。

---

## 三、范围边界

### 3.1 允许修改

**后端（Worker）**:
- apps/worker/app/tasks/training.py（让 early_stopping_rounds 真实传入 xgb.train 或使用 xgboost callbacks）

**后端（API）**:
- apps/api/app/schemas/experiment.py（确认 early_stopping_rounds 定义无误，确保 best_iteration 能返回训练结果）
- apps/api/app/routers/experiments.py（确认参数正确传入 worker）
- apps/api/app/schemas/results.py（如需新增 best_iteration 在结果响应中）

**前端**:
- apps/web/src/lib/api.ts（新增参数模板类型定义）
- apps/web/src/pages/ExperimentsPage.tsx 或创建实验的相关页面（新增模板选择器，联动回填参数）
- apps/web/src/components/**（可选：模板选择组件）

**其他**:
- apps/api/tests/（新增 early stopping 相关测试）
- docs/tasks/M7/M7-T18-20260331-180428-p1-t07-early-stopping-and-param-templates.md
- docs/tasks/M7/M7-T18-R-20260331-180428-p1-t07-early-stopping-and-param-templates-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- 数据库模型与迁移（apps/api/app/models/**, apps/api/migrations/**）
- 无关的前端页面或业务逻辑
- 提前实现 P1-T08（参数校验）或其他后续任务

---

## 四、详细交付要求

### 4.1 Early Stopping 后端修复（worker）

修改 `apps/worker/app/tasks/training.py`，让 `early_stopping_rounds` 配置真实生效。

要求：
- 读取 `training_config.get('early_stopping_rounds')` 或对应字段。
- 若值为正整数，则在 `xgb.train()` 时传入 `early_stopping_rounds` 参数（XGBoost 原生支持）。
- 训练结束后从 `model.best_iteration` 获取实际停止轮次，并在结果中返回。
- 若值为 None/0，则不启用早停，保持原有行为。

**验证方法**：通过构造一个训练集，配置 `early_stopping_rounds=5`，人为使 val_loss 不再下降，确认训练提前终止、返回 `best_iteration`。

参考 XGBoost 原生早停使用方式：
```python
self.model = xgb.train(
    params,
    dtrain,
    num_boost_round=n_estimators,
    evals=[(dtrain, 'train'), (dval, 'val')],
    early_stopping_rounds=early_stopping_rounds,  # 新增
    evals_result=evals_result,
    callbacks=[progress_callback],
    verbose_eval=False
)
best_iteration = self.model.best_iteration  # XGBoost 原生属性
```

### 4.2 三套参数模板定义（后端或共享配置）

在后端（建议放在 `apps/api/app/schemas/experiment.py` 或独立 `templates.py`）定义三套标准模板，可通过 API 返回：

| 参数 | conservative（保守） | balanced（平衡） | aggressive（激进） |
|------|---------------------|-----------------|-------------------|
| learning_rate | 0.01 | 0.1 | 0.3 |
| max_depth | 3 | 6 | 9 |
| n_estimators | 500 | 100 | 50 |
| subsample | 0.8 | 1.0 | 1.0 |
| colsample_bytree | 0.8 | 1.0 | 1.0 |
| early_stopping_rounds | 20 | 10 | 5 |
| 说明 | 适合小数据、防过拟合 | 通用默认值 | 快速探索 |

建议新增只读端点供前端拉取：`GET /api/experiments/param-templates`

响应示例：
```json
{
  "templates": {
    "conservative": { "learning_rate": 0.01, ... },
    "balanced":     { "learning_rate": 0.1,  ... },
    "aggressive":   { "learning_rate": 0.3,  ... }
  }
}
```

### 4.3 前端模板选择与参数回填

在实验创建/配置页面中，找到训练参数配置区，新增：

1. **模板选择器**：提供"保守 / 平衡 / 激进"三个选项。
2. **联动回填**：选择模板后，对应参数值自动填入对应表单项。
3. **手动覆盖**：用户可在回填后继续手动修改任意参数。
4. **模板标注**：回填后参数旁可有轻量标注（如"来自平衡模板"），不强制要求。

要求：
- 选模板后参数值确实变更，不是只展示说明文字。
- 模板值来源于后端 API 或静态常量，两种方式均可，但必须与后端定义保持一致。
- 不得删除或覆盖用户已有的参数配置（首次进入或显式点击"应用模板"时才触发回填）。

### 4.4 best_iteration 在结果中返回

确认 Worker 训练完成后，`best_iteration` 能返回并在实验结果中可查询。

检查 `apps/api/app/schemas/results.py` 中 `ExperimentResult` 是否包含 `best_iteration` 字段；若无则新增：
```python
best_iteration: Optional[int] = None
```

---

## 五、多角色协同执行要求（强制）

1. `Worker-Agent`：修复 Early Stopping 传参，确保 best_iteration 正确返回。
2. `API-Agent`：确认 Schema 完整、参数模板端点实现、best_iteration 返回链路。
3. `Frontend-Agent`：模板选择器 UI + 参数联动回填逻辑。
4. `QA-Agent`：测试早停是否真实触发（构造收敛失速的训练场景），前端回填正确性。
5. `Reviewer-Agent`：范围漂移检查、文档一致性、验收标准闭环。

汇报中必须按角色拆分职责说明。

---

## 六、必须提供的实测证据

### 6.1 Early Stopping 真实生效证据（必须，核心审核点）

构造一个能触发早停的最小场景（方式不限：单测、集成测试、手动 API 调用）：

- 设置 `n_estimators=200`，`early_stopping_rounds=5`
- 使用会过拟合的训练集（训练集拟合好、验证集提前停止改善）
- **证明训练提前于 200 步停止**，且返回 `best_iteration`

证据形式可为：
```bash
python -m pytest apps/api/tests/test_early_stopping.py -v
```

或等价的集成测试输出，**必须包含** `best_iteration` 的实际值。

### 6.2 参数模板端点证据

```bash
# 验证 API 端点返回三套模板
curl http://localhost:8000/api/experiments/param-templates
# 或等价的构造 requests 调用 / 测试输出
```

### 6.3 前端门禁命令

必须执行并在汇报中贴出真实输出：

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
```

### 6.4 后端回归测试

```bash
python -m pytest apps/api/tests/ -q --ignore=apps/api/tests/test_early_stopping.py
```

确认未破坏现有链路。

### 6.5 真实链路证据（必须）

至少提供以下 3 类：

1. **Early stopping 触发链路**：训练提前终止，best_iteration < n_estimators。
2. **参数模板回填链路**：前端选择"保守"模板后，learning_rate 变为 0.01，n_estimators 变为 500。
3. **训练结果链路**：完整训练后 best_iteration 字段出现在结果 API 响应中。

---

## 七、完成判定

以下条件全部满足才可宣称完成：

- [ ] Worker 中 early_stopping_rounds 参数真实传入 xgb.train()
- [ ] 训练提前终止时 best_iteration 可正确返回
- [ ] 三套参数模板已定义，值与上表一致
- [ ] GET /api/experiments/param-templates 端点可用（或等价静态配置）
- [ ] 前端模板选择后参数确实联动回填
- [ ] 手动覆盖不受模板干扰
- [ ] Early stopping 集成测试通过（证明提前终止发生）
- [ ] 后端回归测试全部通过，不破坏现有链路
- [ ] typecheck 与 build 通过
- [ ] 三类真实链路证据完整
- [ ] 汇报按统一格式与多角色分工提交
- [ ] 未越界推进 P1-T08 或其他后续任务

---

## 八、Copilot 审核重点

1. **核心审核**：Early Stopping 是否真实传入 XGBoost 训练调用，还是字段有定义但调用处静默忽略。
2. best_iteration 返回值是否来自 XGBoost 原生属性 `model.best_iteration`，还是自己维护的近似值。
3. 参数模板是否前后端完全一致（前端回填的值与后端定义的模板值相同）。
4. 前端模板联动是否真实修改表单状态，还是只更新展示文字。
5. 是否越界修改了数据库迁移或其他无关模块。

---

## 九、风险提示

1. **XGBoost 版本差异**：`early_stopping_rounds` 参数的行为在不同版本有细微差异，确认当前项目使用的 xgboost 版本，按对应文档实现。
2. **early stopping 与 evals 参数关系**：XGBoost 原生 early stopping 需要指定 `evals` 中的 metric 监控目标（通常为 `val`），确认当前 evals 配置与早停 metric 匹配。
3. **前端回填时机**：注意避免在用户正在编辑某字段时强制回填，建议只在显式点击"应用模板"时触发。

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T18-R-20260331-180428-p1-t07-early-stopping-and-param-templates-report.md`

执行完成后必须按该命名提交统一证据汇报。

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 M7-T19 / P1-T08。
