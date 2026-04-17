# M7-T24 任务单：P1-T10 预测 vs 实际与残差分析

任务编号: M7-T24  
时间戳: 20260407-085126  
所属计划: P1-S4 / P1-T10  
前置任务: M7-T23（已停点，Redis 运行时证据阻断已如实记录）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T10 验收标准）
- [ ] docs/tasks/M7/M7-T20-20260401-100809-p1-t09-concurrent-training-and-queue-visibility.md
- [ ] docs/tasks/M7/M7-T21-R-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure-report.md
- [ ] docs/tasks/M7/M7-T22-R-20260401-121329-m7-t21-audit-fixes-report-presence-and-runtime-test-stability-report.md
- [ ] docs/tasks/M7/M7-T23-R-20260401-143438-redis-runtime-evidence-environment-blocked-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

当前 P1-S1 至 P1-S3 的核心链路已经形成：

1. 数据质量评分、特征工程、预处理与多表 Join 已具备真实实现。
2. 训练参数校验、Early Stopping、并发训练与队列可视化已落地。
3. 结果页目前已具备基础指标、训练历史与特征重要性展示，但尚未补齐 P1-T10 要求的“预测 vs 实际”和“残差分析”能力。

本轮任务目标是把实验结果从“能看指标”推进到“能定位误差结构”。重点不是新增训练能力，而是补齐结果分析维度，使用户能判断模型是否存在系统性偏差、异常点聚集和残差分布异常。

---

## 二、任务目标

1. 后端提供预测值、真实值、残差数据的统一返回结构。
2. 结果页新增至少 3 类可视化：
   - 预测 vs 实际散点图
   - 残差分布图（直方图）
   - 残差趋势图或残差与预测值关系图
3. 明确残差定义并保持前后端一致：`residual = actual - predicted` 或 `predicted - actual`，必须唯一且文档一致。
4. 当结果工件缺少逐样本预测数据时，接口必须给出诚实、可读的降级返回，禁止伪造图表。
5. 提供最小真实验证与自动化测试证据，证明图表数据可被正确读取、返回与展示。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/routers/results.py
- apps/api/app/schemas/**（仅限结果分析相关 schema）
- apps/api/app/services/**（仅限结果工件读取、结果分析聚合、残差计算）
- apps/api/app/models/**（仅当结果读取必须补充字段且不引入范围外变更）
- apps/api/tests/**（新增或修复结果分析相关测试）
- apps/web/src/lib/api.ts
- apps/web/src/pages/ExperimentDetailPage.tsx
- apps/web/src/components/**（仅限结果分析图表组件）
- apps/web/src/types/**（如已有类型定义需补齐结果分析字段）
- docs/tasks/M7/M7-T24-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis.md
- docs/tasks/M7/M7-T24-R-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md（若已有任务映射表需同步）

### 3.2 禁止修改

- 训练调度、并发槽位、Redis 队列治理逻辑
- 数据集上传、特征工程、预处理、Join 业务逻辑
- P1-T11 Benchmark 模式
- P1-T12 及后续任务（标签、模型版本、认证、导出扩展）
- 大规模 UI 重构或样式翻新
- 未经批准的数据库迁移

---

## 四、详细交付要求

### 4.1 后端结果分析接口

必须补齐结果分析数据接口，可选方式：

1. 在现有结果详情接口中新增 analysis 字段。
2. 或新增专用结果分析接口，但必须说明与现有结果接口的边界。

至少应返回：

- `actual_values`
- `predicted_values`
- `residual_values`
- `sample_count`
- `residual_summary`（如 mean、std、min、max、p50、p95）

若前端图表需要结构化点位，也可采用：

- `prediction_scatter_points: [{ actual, predicted }]`
- `residual_histogram_bins: [{ bin_start, bin_end, count }]`
- `residual_scatter_points: [{ predicted, residual }]` 或 `[{ index, residual }]`

要求：

1. 字段命名在 router、schema、前端类型、页面逻辑保持一致。
2. 残差定义必须在接口文档、代码实现、页面文案中完全一致。
3. 不允许前端自行“猜测”残差方向。

### 4.2 工件读取与降级策略

必须先核实现有训练产物中是否存在逐样本预测结果。

分两种情况处理：

1. 若已有真实预测工件：直接读取并返回真实分析数据。
2. 若当前训练结果只保存聚合指标、不保存逐样本预测：
   - 必须在接口中返回明确的 `analysis_unavailable_reason`
   - 前端展示“当前实验缺少逐样本预测工件，无法生成该图表”
   - 不得用 mock 数据、占位数组、随机值冒充分析能力完成

只有在真实数据链路打通时，才能宣称 P1-T10 完成；否则只能如实汇报“部分完成/受现有工件结构限制”。

### 4.3 前端结果页展示

在实验详情页补齐结果分析区域，至少包含：

1. 预测 vs 实际散点图
2. 残差分布图
3. 残差摘要卡片（样本数、均值、标准差、极值）

要求：

1. 图表标题与指标含义可读。
2. 数据缺失时展示诚实降级态，而不是空白报错。
3. 不得破坏当前已有指标、训练历史、特征重要性模块。
4. 移动端至少保证不出现明显布局错乱。

### 4.4 最小图表语义要求

必须满足以下语义：

1. 预测 vs 实际图中，坐标轴名称清晰。
2. 残差图与残差摘要使用同一残差定义。
3. 若存在异常值，图表不应直接崩溃或 NaN 渲染失败。
4. 若样本量过大，可做前端采样或后端限量，但必须在实现或汇报中说明策略。

---

## 五、多角色协同执行要求（强制）

1. `Results-Agent`：梳理结果工件结构、定义残差数据契约。
2. `API-Agent`：实现结果分析接口与 schema，对齐错误返回。
3. `Frontend-Agent`：完成实验详情页分析图表与降级态展示。
4. `QA-Agent`：补齐后端测试、前端门禁、最小集成验证。
5. `Reviewer-Agent`：检查范围边界、残差定义一致性、证据真实性。

允许执行者自行一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端结果分析测试（必须）

至少提供一条结果分析相关测试，验证：

1. 返回字段完整。
2. 残差计算正确。
3. 数据缺失时返回明确降级原因。

示例命令：

```bash
python -m pytest apps/api/tests/ -k "result or residual or prediction" -v
```

### 6.2 前端门禁（必须）

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
```

### 6.3 最小人工或脚本验证（必须）

至少提供一项实际验证，证明实验详情页或结果接口可以拿到分析数据或正确显示降级态。可选其一：

```bash
python apps/api/scripts/e2e_validation.py --output json --timeout 120
```

或

```bash
python -m pytest apps/api/tests/ -k "experiment detail or results" -v
```

或提供明确的本地接口调用/页面访问证据。

### 6.4 回归检查（必须）

```bash
python -m pytest apps/api/tests/ --tb=short
cd apps/web && npx tsc --noEmit
```

若全量回归因既有问题未通过，必须在汇报中区分：

1. 既有失败
2. 本次新增失败
3. 本次已修复失败

---

## 七、完成判定

以下条件全部满足才可宣称完成：

- [ ] 后端存在可复用的结果分析返回结构
- [ ] 预测 vs 实际散点图可展示真实数据或诚实降级态
- [ ] 残差分布图可展示真实数据或诚实降级态
- [ ] 残差摘要卡可见且数值来源明确
- [ ] 残差定义在前后端与文档中完全一致
- [ ] 后端结果分析测试已执行并通过或如实报告失败
- [ ] 前端 typecheck 已执行
- [ ] 前端 build 已执行并如实报告结果
- [ ] 至少提供 1 条真实运行或最小集成证据
- [ ] 未越界推进 P1-T11 或后续任务

---

## 八、Copilot 审核重点

1. 是否真的基于实验结果工件生成分析数据，而非前端临时拼装假数据。
2. 残差方向是否唯一、明确且全链路一致。
3. 数据缺失时是否诚实降级，而不是隐藏问题。
4. 图表引入是否破坏现有实验详情页稳定性。
5. 汇报是否明确区分“真实完成”和“受工件结构限制未完成”的部分。

---

## 九、风险提示

1. 若当前训练产物未保存逐样本预测，P1-T10 可能被结果工件结构阻断。
2. 大样本量散点图可能影响浏览器性能，需要明确采样或聚合策略。
3. 残差口径若前后端不一致，会直接导致图表误导结论。
4. 若结果接口返回 NaN/Infinity，前端图表可能出现渲染异常，需要显式处理。

---

## 十、统一汇报要求

汇报必须为统一证据报告，至少包含：

1. 已完成任务编号
2. 分角色产出说明（Results/API/Frontend/QA/Reviewer）
3. 修改文件清单
4. 实际执行命令
5. 实际输出结果
6. 已验证部分
7. 未验证部分
8. 风险与限制
9. 是否建议进入下一任务

不得只给摘要，不得只给“已完成”结论。

---

## 十一、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T24-R-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis-report.md`

执行完成后必须按该命名提交统一证据汇报。

---

## 十二、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T11 Benchmark 模式或 P1-S5 任务。