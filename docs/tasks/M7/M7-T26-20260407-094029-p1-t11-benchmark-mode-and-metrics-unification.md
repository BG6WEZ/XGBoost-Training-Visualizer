# M7-T26 任务单：P1-T11 Benchmark 模式与指标统一输出

任务编号: M7-T26  
时间戳: 20260407-094029  
所属计划: P1-S4 / P1-T11  
前置任务: M7-T25（已审核通过）  
优先级: 高  

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T11 验收标准）
- [ ] docs/tasks/M7/M7-T24-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis.md
- [ ] docs/tasks/M7/M7-T24-R-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis-report.md
- [ ] docs/tasks/M7/M7-T25-R-20260407-092723-m7-t24-audit-fixes-backend-degradation-and-evidence-closure-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

P1-T10 已完成预测分析与残差分析闭环，当前结果页已经能展示单实验的误差结构。但 P1-S4 仍缺少另一项关键能力：

1. 不同数据集或不同实验之间的指标输出口径尚未统一。
2. 当前结果返回中已有 RMSE、MAE、R² 等字段，但缺少明确的 Benchmark 模式约束，无法保证跨数据集对比时结构稳定。
3. P1-T11 要求形成统一 Benchmark 输出，使不同数据集在结果结构和指标口径上可比较、可复核。

本轮任务只做 Benchmark 模式与统一指标输出闭环，不扩展模型管理、认证或导出能力。

---

## 二、任务目标

1. 在后端定义统一 Benchmark 指标输出结构。
2. 支持至少输出以下指标：`RMSE`、`MAE`、`MAPE`、`R2`。
3. 为结果接口补齐 Benchmark 相关字段，使不同数据集的实验结果结构一致。
4. 如当前训练结果缺少某指标计算前提，必须给出诚实降级或明确说明，不得伪造数值。
5. 提供最小自动化测试和真实接口验证证据，证明指标结构可复用、可对比。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/routers/results.py
- apps/api/app/schemas/results.py
- apps/api/app/services/**（仅限结果聚合、指标计算、benchmark 结构整理）
- apps/api/tests/**（新增或修复 benchmark/metrics 相关测试）
- apps/web/src/lib/api.ts
- apps/web/src/pages/ExperimentDetailPage.tsx（仅当结果结构调整需要前端最小联调）
- apps/web/src/pages/ComparePage.tsx（仅当 benchmark 字段需要最小接入）
- apps/web/src/components/**（仅限 benchmark 指标展示所需最小组件）
- docs/tasks/M7/M7-T26-20260407-094029-p1-t11-benchmark-mode-and-metrics-unification.md
- docs/tasks/M7/M7-T26-R-20260407-094029-p1-t11-benchmark-mode-and-metrics-unification-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/worker/** 中与训练调度、并发、Redis 队列相关逻辑
- P1-T12 及后续任务（标签、模型版本、认证、导出）
- 无关页面重构或大规模 UI 翻新
- 数据库迁移
- 引入新的 benchmark 数据集治理流程（本轮只做结果输出模式，不做数据管理扩展）

---

## 四、详细交付要求

### 4.1 统一 Benchmark 指标结构

后端必须定义统一的 benchmark 指标结构，至少包含：

- `benchmark_mode` 或等价标志字段
- `metrics.rmse`
- `metrics.mae`
- `metrics.mape`
- `metrics.r2`
- 指标的可用性说明（如某指标不可算时的处理方式）

要求：

1. 字段命名在 schema、router、前端类型定义中保持一致。
2. 不同数据集返回的结构必须一致。
3. 如果 MAPE 因真实值含 0 或不可计算而不可用，必须：
   - 明确返回 `null` 或等价可空值；
   - 同时给出原因说明字段或可读语义；
   - 不得填 0 冒充有效结果。

### 4.2 结果接口接入

必须在现有结果接口上补齐 benchmark 相关输出，可接受方式：

1. 在现有 `GET /api/results/{experiment_id}` 中补充 benchmark 字段；
2. 或新增专用 benchmark 结果接口，但必须说明与原结果接口边界。

若选择新增接口，必须同时保证前端消费路径清晰，不得造成双套口径并存。

### 4.3 指标计算规则明确化

必须明确各指标的计算口径：

1. `RMSE`
2. `MAE`
3. `MAPE`
4. `R2`

要求：

1. 计算逻辑在代码中可见、可审计。
2. 汇报中必须说明各指标来源。
3. 若当前系统已有部分指标来自模型持久化结果、部分来自训练阶段，需要说明统一来源策略。

### 4.4 前端最小联调

如果结果结构发生变化，前端需要做最小联调，至少满足：

1. 实验详情页或对比页不因新字段崩溃。
2. Benchmark 指标在页面上可读或可忽略降级，但不能白屏。
3. 不得因为接入 benchmark 字段而破坏当前 P1-T10 结果分析展示。

---

## 五、多角色协同执行要求（强制）

1. `Metrics-Agent`：定义统一 benchmark 指标结构与计算口径。
2. `API-Agent`：实现后端 schema/router/结果聚合逻辑。
3. `Frontend-Agent`：完成前端最小联调，确保结果页和对比页消费稳定。
4. `QA-Agent`：补齐自动化测试与真实接口验证证据。
5. `Reviewer-Agent`：检查范围边界、结果口径一致性、证据真实性。

汇报中必须按角色拆分产出，不接受只有最终摘要的写法。

---

## 六、必须提供的实测证据

### 6.1 后端 Benchmark 测试（必须）

至少提供一组 benchmark/metrics 相关测试，验证：

1. 返回结构完整；
2. 四个指标字段口径一致；
3. 不可计算指标的降级逻辑正确；
4. 不同实验结果结构一致。

建议命令：

```bash
cd apps/api
python -m pytest tests/ -k "benchmark or metrics or results" -v --tb=short
```

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 最小真实链路证据（必须）

至少 2 组：

1. 成功链路：实验结果返回统一 benchmark 指标结构；
2. 降级链路：某指标不可计算时，返回可读降级而非伪造数值。

证据必须包含：

1. 请求路径；
2. 响应关键字段；
3. 与任务目标的对应关系。

### 6.4 最小回归说明（必须）

若未执行全量回归，必须在汇报中明确：

- 未执行哪些；
- 为什么未执行；
- 当前验证覆盖范围。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] 后端已定义统一 benchmark 指标结构
- [ ] `RMSE/MAE/MAPE/R2` 四个指标在结果结构中可用或诚实降级
- [ ] 指标计算口径在代码与汇报中可说明
- [ ] 不同实验结果结构一致
- [ ] 前端 typecheck/build 通过
- [ ] 至少 1 组后端测试已执行并通过或如实报告阻塞
- [ ] 至少 2 组真实链路证据完整
- [ ] 未越界推进 P1-T12 或后续任务

---

## 八、Copilot 审核重点

1. 是否只是改了文档或前端展示，而后端结果结构并未真正统一。
2. MAPE 不可计算场景是否被诚实处理，而不是填默认值掩盖问题。
3. Benchmark 指标口径是否与当前结果页已有指标冲突。
4. 是否因为结构调整破坏了 P1-T10 的预测分析展示。
5. 汇报是否提供真实接口和测试证据，而不是仅给结论。

---

## 九、风险提示

1. 若已有指标来源分散，统一口径时可能暴露历史结果结构不一致问题。
2. MAPE 对真实值为 0 的样本敏感，必须明确定义降级处理。
3. 若前端直接假定所有指标永远存在，接入可空字段时可能触发运行时错误。

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T26-R-20260407-094029-p1-t11-benchmark-mode-and-metrics-unification-report.md`

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-S5 / M7-T27。