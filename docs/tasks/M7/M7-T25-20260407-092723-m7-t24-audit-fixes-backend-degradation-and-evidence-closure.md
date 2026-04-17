# M7-T25 任务单：M7-T24 审计修复（后端降级逻辑与证据闭环）

任务编号: M7-T25  
时间戳: 20260407-092723  
所属计划: M7-T24 审计修复轮  
前置任务: M7-T24（审核结果：部分通过）  
优先级: 最高  

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T24-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis.md
- [ ] docs/tasks/M7/M7-T24-R-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis-report.md

未完成上述预读，不得开始执行。

---

## 一、当前审核结论（必须先承认问题）

M7-T24 当前**不能判定为通过**。已确认存在以下阻断项：

### 阻断问题 1：后端关键测试未全部通过

Copilot 实测命令：

```bash
cd apps/api
python -m pytest tests/test_results.py -k "PredictionAnalysis" -v --tb=short
```

实测结果：

- 5 条预测分析测试中 **1 failed / 4 passed**
- 失败用例：
  - `TestPredictionAnalysis::test_prediction_analysis_unavailable_no_prediction_data`

失败原因：

- 当前 `GET /api/results/{experiment_id}/prediction-analysis` 在存储服务未初始化时返回的是：
  - `analysis_unavailable_reason = "存储服务未初始化"`
- 但任务目标与测试预期要求的是：
  - 缺少逐样本预测工件时返回明确、面向业务的诚实降级原因

这说明 M7-T24 的后端降级逻辑**未完全闭环**，且汇报中“已完成”结论与实际测试结果不一致。

### 阻断问题 2：汇报文档不是统一证据报告，存在模板残留

`docs/tasks/M7/M7-T24-R-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis-report.md` 当前同时包含：

1. 整份“待执行 / 待填写”的占位模板；
2. 后续追加的“已完成”正文。

这违反了“统一证据报告”的要求，也会导致审核时无法判断哪些内容是正式结论，哪些只是占位骨架。

### 阻断问题 3：汇报缺少实际后端验证命令与真实输出闭环

当前汇报中只明确贴出了前端 `typecheck/build` 命令结果，但缺少以下必需证据的真实执行输出：

1. 后端结果分析测试命令与输出；
2. 最小集成或接口验证命令与输出；
3. 回归检查命令与输出；
4. 已验证/未验证边界的真实依据。

因此，当前汇报不能支持“后端测试已编写、任务已完成”的结论。

---

## 二、本轮修复目标

本轮**只做 M7-T24 的审计修复闭环**，不推进 P1-T11，不新增 Benchmark，不扩展模型管理。

目标：

1. 修复预测分析接口的后端降级逻辑，使“无预测工件”场景稳定返回任务要求的业务可读提示。
2. 跑通并贴出结果分析相关后端测试的真实输出。
3. 补齐至少 1 条真实接口或最小集成验证证据。
4. 清理并重写 M7-T24 汇报，使其成为单一、统一、可审计的正式报告。
5. 如实区分：
   - 已验证
   - 未验证
   - 既有问题
   - 本次修复结果

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/routers/results.py
- apps/api/app/services/storage.py（仅当需要修复存储服务初始化/读取降级语义）
- apps/api/app/schemas/results.py（仅当返回结构需要最小调整）
- apps/api/tests/test_results.py
- apps/web/src/lib/api.ts（仅当契约字段与实际返回不一致时最小修正）
- apps/web/src/components/PredictionAnalysis.tsx（仅当降级态字段消费不一致时最小修正）
- apps/web/src/pages/ExperimentDetailPage.tsx（仅当联调暴露字段消费问题时最小修正）
- docs/tasks/M7/M7-T24-R-20260407-085126-p1-t10-prediction-vs-actual-and-residual-analysis-report.md
- docs/tasks/M7/M7-T25-20260407-092723-m7-t24-audit-fixes-backend-degradation-and-evidence-closure.md
- docs/tasks/M7/M7-T25-R-20260407-092723-m7-t24-audit-fixes-backend-degradation-and-evidence-closure-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/worker/app/** 中与训练调度、并发槽位、Redis 队列治理相关逻辑
- P1-T11 Benchmark 模式
- P1-S5 任何任务（标签、版本管理、认证、导出扩展）
- 与 M7-T24 无关的页面重构或样式翻新
- 数据库迁移

---

## 四、必须完成的修复项

### 4.1 修复后端降级逻辑

针对以下场景给出稳定、可审计、任务语义正确的返回：

1. 实验不存在：404
2. 实验未完成：`analysis_available=false` + 明确状态原因
3. 无逐样本预测工件：`analysis_available=false` + 明确“缺少逐样本预测工件”原因
4. 存储层不可用或未初始化：
   - 不得掩盖为内部异常；
   - 需要明确说明是否属于“环境未就绪”还是“无工件”；
   - 必须与测试预期、任务目标、页面降级语义一致

核心要求：

- `test_prediction_analysis_unavailable_no_prediction_data` 必须通过。
- 不允许把“存储服务未初始化”当作主路径的业务降级结论长期保留。

### 4.2 补齐后端测试证据

必须真实执行并贴出输出：

```bash
cd apps/api
python -m pytest tests/test_results.py -k "PredictionAnalysis" -v --tb=short
```

验收要求：

- 预测分析相关测试全部通过；
- 或如确有未通过项，必须在汇报中明确写出失败原因与阻塞，不得写成“已完成”。

### 4.3 补齐最小真实链路证据

至少补齐 1 条真实接口或最小集成验证，必须包含：

1. 请求路径；
2. 请求前提（实验状态、是否有预测工件）；
3. 响应关键字段；
4. 与任务目标的对应关系。

可接受方式之一：

```bash
cd apps/api
python -m pytest tests/test_results.py -k "happy_path or unavailable" -v --tb=short
```

或提供等价真实接口调用输出，但不得只给文字描述。

### 4.4 重写正式汇报，去除模板残留

`M7-T24-R` 必须改为**单一正式报告**，不得同时保留：

1. “待填写”模板骨架；
2. “已完成”正文。

要求：

- 汇报必须只保留一份正式内容；
- 明确列出已完成项、未完成项、风险与限制；
- 所有“已执行命令”必须配套真实结果；
- 不得再出现 `待填写`、未勾选模板项、占位注释。

---

## 五、多角色协同执行要求（强制）

1. `Results-Agent`：核对结果工件路径与降级语义。
2. `API-Agent`：修复接口返回与测试预期不一致问题。
3. `QA-Agent`：执行后端测试、最小真实链路验证、前端门禁复核。
4. `Frontend-Agent`：仅在接口字段或降级结构变化时做最小联调修正。
5. `Reviewer-Agent`：检查汇报是否仍有模板残留、结论是否与实测一致。

汇报中必须按角色拆分，不接受只有“最终总结”的写法。

---

## 六、必须提供的实测证据

### 6.1 后端结果分析测试（必须）

```bash
cd apps/api
python -m pytest tests/test_results.py -k "PredictionAnalysis" -v --tb=short
```

### 6.2 前端门禁复核（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 最小真实链路证据（必须）

至少 1 条：

1. 无预测工件时的诚实降级链路；
2. 有预测工件时的正常返回链路。

### 6.4 最小回归说明（必须）

若未执行全量回归，必须在汇报中明确写：

- 未执行什么；
- 为什么未执行；
- 当前仅验证了哪些范围。

---

## 七、完成判定

以下全部满足才可宣称 M7-T24 审计问题关闭：

- [ ] `PredictionAnalysis` 相关后端测试全部通过或如实报告阻塞
- [ ] “无预测工件”场景返回业务可读降级原因
- [ ] 汇报中的命令与实际输出一一对应
- [ ] M7-T24 汇报不再含有模板残留与 `待填写` 占位内容
- [ ] 已验证 / 未验证边界清晰
- [ ] 前端 typecheck/build 已复核
- [ ] 未越界推进 P1-T11 或其他后续任务

---

## 八、Copilot 审核重点

1. 后端失败测试是否被真正修复，而不是绕开断言。
2. “存储服务未初始化”是否还在错误地覆盖“缺少逐样本预测工件”主场景。
3. 汇报是否仍存在双版本内容（模板 + 正式正文并存）。
4. 是否补齐了后端验证证据，而不是只保留前端门禁。
5. 是否对未验证部分保持诚实表述。

---

## 九、风险提示

1. 若存储服务初始化依赖运行环境，测试环境与真实运行环境的降级语义必须明确区分。
2. 若继续只补文档不修后端逻辑，下一轮审核仍会失败。
3. 若页面依赖字段与接口返回不完全一致，修复后端时可能触发前端联调问题，但不得借机扩范围重构。

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T25-R-20260407-092723-m7-t24-audit-fixes-backend-degradation-and-evidence-closure-report.md`

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T11 / M7-T26。