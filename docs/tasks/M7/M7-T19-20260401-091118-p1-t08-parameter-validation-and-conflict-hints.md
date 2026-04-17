# M7-T19 任务单：P1-T08 参数校验与冲突提示（前后端双重校验）

任务编号: M7-T19  
时间戳: 20260401-091118  
所属计划: P1-S3 / P1-T08  
前置任务: M7-T18（已完成）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T08 验收标准）
- [ ] docs/tasks/M7/M7-T18-20260331-180428-p1-t07-early-stopping-and-param-templates.md
- [ ] docs/tasks/M7/M7-T18-R-20260331-180428-p1-t07-early-stopping-and-param-templates-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

M7-T18 已完成 early stopping 生效与参数模板回填，但训练参数输入目前仍缺少完整的“前后端双重校验 + 冲突提示”，存在以下风险：

1. 前端可提交语义冲突参数（例如过小学习率配合过低迭代轮数）。
2. 后端虽有基础范围校验，但缺少组合规则校验与可读冲突提示。
3. 错误提示粒度不够，用户无法快速定位具体字段与冲突原因。

P1-T08 的目标是让非法参数在提交前和提交时都被阻断，并返回可执行的修复建议。

---

## 二、任务目标

1. 前端实现参数级 + 组合级校验，阻断明显非法或高风险冲突配置。
2. 后端实现参数组合冲突规则校验，保证 API 层不可绕过。
3. 统一错误结构：明确字段、规则、当前值、建议值区间。
4. 负向测试不少于 8 条，覆盖单字段越界与组合冲突。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/schemas/experiment.py
- apps/api/app/routers/experiments.py
- apps/api/app/services/**（如抽出参数校验服务）
- apps/api/tests/**（新增参数冲突测试）
- apps/web/src/pages/ExperimentsPage.tsx
- apps/web/src/lib/api.ts
- apps/web/src/components/**（如新增参数校验提示组件）
- docs/tasks/M7/M7-T19-20260401-091118-p1-t08-parameter-validation-and-conflict-hints.md
- docs/tasks/M7/M7-T19-R-20260401-091118-p1-t08-parameter-validation-and-conflict-hints-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/worker/**（本任务不改训练执行逻辑）
- 数据库模型与迁移（apps/api/app/models/**, apps/api/migrations/**）
- 与实验参数无关的页面与业务模块
- 提前实现 P1-T09 并发训练与队列可视化

---

## 四、详细交付要求

### 4.1 后端：组合规则校验与统一错误结构

在后端新增或增强参数规则校验（建议独立 `parameter_validation.py`），至少覆盖：

1. 学习率与迭代轮数冲突
- 规则示例：`learning_rate <= 0.02` 且 `n_estimators < 150` 判定为高风险欠拟合配置

2. 深度与正则/子采样冲突
- 规则示例：`max_depth >= 10` 且 `subsample >= 0.95` 且 `colsample_bytree >= 0.95` 判定为高风险过拟合配置

3. early_stopping_rounds 约束
- 规则示例：`early_stopping_rounds >= n_estimators` 判定为无效配置

4. min_child_weight 与 max_depth 组合建议
- 规则示例：高深度时 min_child_weight 过低给出警告或阻断（按规则定义）

错误响应必须可读，建议结构：
```json
{
  "error_code": "PARAM_CONFLICT",
  "message": "训练参数存在冲突",
  "field_errors": [
    {
      "fields": ["learning_rate", "n_estimators"],
      "rule": "LOW_LR_LOW_ESTIMATORS",
      "current": {"learning_rate": 0.01, "n_estimators": 80},
      "suggestion": "将 n_estimators 提高到 >=150，或将 learning_rate 提升到 >=0.05"
    }
  ]
}
```

### 4.2 前端：提交前阻断与冲突提示

在实验创建页实现：

1. 输入即校验（轻量）
- 单字段越界实时提示（例如 learning_rate > 1）

2. 提交前组合校验（强阻断）
- 命中组合冲突时阻止提交，并展示可读冲突列表

3. 服务端错误映射
- 若后端返回 `field_errors`，前端要定位到对应字段并高亮提示

4. 模板联动后再次校验
- 用户应用模板后仍需跑一遍组合校验，避免模板修改后未触发校验

### 4.3 规则配置可维护

规则不要写死在页面散落逻辑中，必须做到：

- 前端规则集中管理（可在 util 或 hook）
- 后端规则集中管理（可在 service）
- 前后端规则命名一致（如 `LOW_LR_LOW_ESTIMATORS`）

---

## 五、多角色协同执行要求（强制）

1. `API-Validation-Agent`：后端规则设计、422 错误结构、接口契约。
2. `Frontend-Validation-Agent`：前端实时校验、提交阻断、字段高亮提示。
3. `Rule-Governance-Agent`：前后端规则命名一致性与文档同步。
4. `QA-Agent`：负向测试与冲突场景覆盖，证据采集。
5. `Reviewer-Agent`：范围检查、回归风险、验收逐条勾核。

---

## 六、必须提供的实测证据

### 6.1 后端负向测试（至少 8 条）

必须新增并执行参数冲突测试，至少覆盖：

1. learning_rate 越界（>1 或 <0.001）
2. n_estimators 越界（<10）
3. early_stopping_rounds >= n_estimators
4. 低学习率 + 低轮数冲突
5. 高深度 + 高采样冲突
6. 无效字段类型（字符串传数值字段）
7. 模板参数被手动篡改后的冲突
8. 合法配置通过（对照组）

命令建议：
```bash
python -m pytest apps/api/tests/test_training_param_validation.py -q
```

### 6.2 前端门禁

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
```

### 6.3 后端回归

```bash
python -m pytest apps/api/tests/ -q
```

### 6.4 真实链路证据（必须）

至少提供 2 组失败 + 1 组成功链路：

1. 失败链路 A：前端提交前即被阻断（无请求发出）。
2. 失败链路 B：绕过前端直接调 API 被 422 拒绝，返回 field_errors。
3. 成功链路：合法参数提交成功，实验创建并进入排队/运行状态。

---

## 七、完成判定

以下条件全部满足才可宣称完成：

- [ ] 前端实现单字段与组合参数校验
- [ ] 前端能阻断非法提交并提示具体冲突
- [ ] 后端实现组合规则校验且不可绕过
- [ ] 后端返回统一错误结构（含 fields/rule/suggestion）
- [ ] 负向测试 >= 8 条且通过
- [ ] 前端 typecheck/build 通过
- [ ] 后端回归通过或明确声明既有失败项
- [ ] 提供 2 失败 + 1 成功真实链路证据
- [ ] 汇报按模板提交并区分已验证/未验证
- [ ] 未越界推进 P1-T09

---

## 八、Copilot 审核重点

1. 冲突规则是否只做前端提示而后端未阻断（不允许）。
2. 错误响应是否能定位具体字段而非笼统报错。
3. 前后端规则命名是否一致，避免“前端通过/后端拒绝”语义错位。
4. 负向测试数量是否达到 8 条且真实执行。
5. 是否把既有失败回归测试错误写成“全部通过”。

---

## 九、风险提示

1. 规则过严会误伤正常配置，需提供明确建议值而非一刀切。
2. 前后端规则不一致会引发体验割裂，必须统一命名与含义。
3. 错误信息如果不含字段定位，将严重影响可修复性。

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T19-R-20260401-091118-p1-t08-parameter-validation-and-conflict-hints-report.md`

执行完成后必须按该命名提交统一证据汇报。

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 M7-T20 / P1-T09。
