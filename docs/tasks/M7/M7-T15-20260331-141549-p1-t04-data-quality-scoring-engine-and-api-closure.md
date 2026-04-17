# M7-T15 任务单：P1-T04 数据质量评分引擎与 API 闭环

任务编号: M7-T15  
时间戳: 20260331-141549  
所属计划: P1-S2（数据质量与多表融合）  
前置任务: M7-T14（已完成）  
优先级: 最高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T14-R-20260331-140904-mainline-stability-hardening-and-governance-closure-report.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T04 验收标准）

未完成上述预读，不得开始执行。

---

## 一、任务目标

在现有 DataQualityValidator 已具备“是否可训练”校验能力的基础上，补齐 P1-T04 要求的“可量化评分能力”，形成可被前端消费的数据质量评分接口，输出以下核心结果：

1. 四维评分：完整性、准确性、一致性、分布（0-100）。
2. 总分（0-100）。
3. 问题列表（errors/warnings）与修复建议（actionable suggestions）。
4. 数据统计摘要（可用于后续质量报告页面）。

本任务只做后端评分引擎与 API 闭环，不包含前端质量报告页面（该部分留给下一任务 M7-T16 / P1-T05）。

---

## 二、范围边界

### 2.1 允许修改

- apps/api/app/services/data_quality_validator.py
- apps/api/app/schemas/dataset.py
- apps/api/app/routers/datasets.py
- apps/api/tests/test_data_quality.py
- apps/api/tests/test_datasets_router.py（若不存在则新增最小接口测试文件）
- docs/tasks/M7/M7-T15-20260331-141549-p1-t04-data-quality-scoring-engine-and-api-closure.md
- docs/tasks/M7/M7-T15-R-20260331-141549-p1-t04-data-quality-scoring-engine-and-api-closure-report.md（执行完成后生成）

### 2.2 禁止修改

- 前端页面文件（apps/web/**）
- 训练执行链路文件（apps/worker/**）
- 数据库模型与迁移（apps/api/app/models/**, apps/api/migrations/**）
- 与本任务无关的治理文档

---

## 三、需求定义（必须全部满足）

### 3.1 评分维度定义（可复核）

在 data quality 校验结果基础上新增评分结构，至少包含：

- completeness_score：基于缺失率、空列占比、有效样本占比。
- accuracy_score：基于目标列非法值（NaN/Inf/不可解析）与关键字段可解析率。
- consistency_score：基于时间列解析一致性、重复记录比例、关键列类型一致性。
- distribution_score：基于极端值比例、偏态/离散异常提示（允许简化实现，但规则必须可解释）。
- overall_score：按固定权重汇总（权重需在代码中显式定义并写入返回结果）。

说明：若当前数据不足以支持某子项，必须返回“not_applicable”或明确降级规则，禁止静默跳过。

### 3.2 API 能力

在数据集路由中新增质量评分接口（挂在 dataset 维度下）：

- 建议路径：`GET /api/datasets/{dataset_id}/quality-score`
- 返回结构至少包含：
  - dataset_id
  - overall_score
  - dimension_scores（4 维）
  - errors
  - warnings
  - recommendations
  - stats
  - evaluated_at

错误语义要求：

- 数据集不存在：404
- 数据文件缺失或不可读：422（附可读错误码与信息）
- 内部异常：500（保留可追踪日志）

### 3.3 可观测性与可解释性

- 日志中必须可定位：数据集 ID、主文件路径、评分阶段、主要扣分项。
- 推荐建议必须与错误/警告可对应，禁止泛化文案。

---

## 四、双AI协同执行要求（强制）

采用多角色并行协同，允许自组织，但输出必须包含明确责任归属：

1. `Backend-Agent`：实现评分引擎与 API，确保契约稳定。
2. `QA-Agent`：补齐单测/接口测试，执行失败场景与边界值验证。
3. `Governance-Agent`：检查任务范围、文档一致性、证据完备性。
4. `Reviewer-Agent`：做最终合并审查，给出通过/驳回结论。

若由单人串行执行，也必须在汇报中按上述角色视角分段说明“谁负责了什么”。

---

## 五、验收标准

以下全部满足才可宣称完成：

1. API 能返回四维评分 + 总分 + 问题清单 + 修复建议。
2. 至少覆盖 4 类场景：
   - 正常数据（高分）
   - 高缺失率数据（完整性低分）
   - 目标列非法值数据（准确性低分/报错）
   - 时间列解析差数据（一致性低分）
3. 分数范围严格在 [0, 100]。
4. 评分权重与计算规则在代码中可见、在汇报中可说明。
5. 不破坏现有数据注册与训练主链路。

---

## 六、最小验证命令（必须真实执行）

- `python -m pytest apps/api/tests/test_data_quality.py -q`
- `python -m pytest apps/api/tests/test_datasets_router.py -q`（或新增的对应接口测试）
- `python -m pytest apps/api/tests/ --tb=short -k "quality or dataset"`

若无法执行，必须在汇报中标注“未验证”并说明阻塞原因。

---

## 七、交付物要求

1. 代码变更（仅限范围内文件）。
2. 任务汇报：
   - docs/tasks/M7/M7-T15-R-20260331-141549-p1-t04-data-quality-scoring-engine-and-api-closure-report.md
3. 汇报必须为统一证据报告，不得只给摘要，必须至少包含：
   - 已完成项
   - 修改文件清单
   - 实际执行命令
   - 实际输出结果
   - 未验证项
   - 风险与限制

---

## 八、风险提示

1. 评分规则若定义过于复杂，容易与当前代码基线冲突；优先采用“可解释的最小可用规则”。
2. 大文件全量扫描可能引发性能问题；允许采样，但采样策略必须明确可追溯。
3. 不得将“质量校验通过”与“模型效果好”混为一谈。

---

## 九、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 M7-T16。
