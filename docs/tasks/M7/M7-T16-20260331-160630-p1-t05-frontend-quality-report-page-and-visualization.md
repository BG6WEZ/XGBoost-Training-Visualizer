# M7-T16 任务单：P1-T05 前端质量报告页面与可视化闭环

任务编号: M7-T16  
时间戳: 20260331-160630  
所属计划: P1-S2 / P1-T05  
前置任务: M7-T15（已完成）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T05 验收标准）
- [ ] docs/tasks/M7/M7-T15-20260331-141549-p1-t04-data-quality-scoring-engine-and-api-closure.md
- [ ] docs/tasks/M7/M7-T15-R-20260331-141549-p1-t04-data-quality-scoring-engine-and-api-closure-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

M7-T15 已完成数据质量评分引擎与后端 API 闭环，当前系统已经可以返回 `overall_score`、四维评分、问题清单、修复建议与统计摘要，但前端仍缺少可视化承接页面，用户无法在 UI 中直接查看质量结论，也无法基于质量问题继续决策。

本任务用于补齐 P1-T05 的前端消费层，形成“后端评分 API -> 前端质量报告页 -> 问题与建议可视呈现”的闭环。

---

## 二、任务目标

完成一个可实际访问、可联调、可验证的数据质量报告页面，至少实现以下能力：

1. 新增质量报告页面路由，支持按数据集 ID 查看质量评分结果。
2. 页面展示总分与四维评分卡。
3. 页面展示 errors / warnings / recommendations / stats。
4. 页面具备 loading / empty / error 三类状态处理。
5. 页面至少提供一个从现有数据集相关页面进入质量报告页的可见入口。

---

## 三、范围边界

### 3.1 允许修改

- apps/web/src/lib/api.ts
- apps/web/src/pages/**（仅限质量报告页及必要的入口页面）
- apps/web/src/components/**（仅限质量评分展示相关组件）
- apps/web/src/router.tsx
- apps/web/src/types/**（如项目当前结构需要）
- apps/web/src/styles/**（仅限质量报告页样式，若现有结构需要）
- docs/tasks/M7/M7-T16-20260331-160630-p1-t05-frontend-quality-report-page-and-visualization.md
- docs/tasks/M7/M7-T16-R-20260331-160630-p1-t05-frontend-quality-report-page-and-visualization-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/api/app/**
- apps/api/tests/**
- apps/worker/**
- 数据库模型、迁移、训练链路
- 与质量报告无关的前端页面大范围重构
- 提前实现 P1-T06 多表 Join 或任何后续任务

---

## 四、详细交付要求

### 4.1 前端 API 契约接入

在前端 API 客户端中补齐质量评分读取方法与类型定义，至少覆盖：

- `getDatasetQualityScore(datasetId)` 或等价命名
- `overall_score`
- `dimension_scores.completeness`
- `dimension_scores.accuracy`
- `dimension_scores.consistency`
- `dimension_scores.distribution`
- `errors`
- `warnings`
- `recommendations`
- `stats`
- `evaluated_at`
- `weights`

要求：

- 不允许使用 `any` 拼接临时对象蒙混过关。
- 字段名必须与后端实际返回契约一致。
- 若后端字段存在可空或缺省情况，前端必须显式处理。

### 4.2 质量报告页面实现

新增或接入质量报告页面，建议路径之一：

- `/data/:datasetId/quality`
- `/datasets/:datasetId/quality`

要求页面至少包含以下区块：

1. **总分区**
   - 显示 overall score
   - 显示 evaluated_at
   - 明确分数含义范围为 0-100

2. **四维评分卡区**
   - completeness
   - accuracy
   - consistency
   - distribution
   - 每项至少展示名称、数值、必要的简短说明

3. **问题清单区**
   - errors 与 warnings 分开展示或清晰区分
   - 每项展示 code、message、severity（如接口提供）

4. **建议区**
   - recommendations 逐条展示
   - 不得静默隐藏空数组，应给出“暂无建议”之类可读状态

5. **统计摘要区**
   - total_rows
   - total_columns
   - 关键缺失率 / 极端值率等后端已提供字段
   - 字段不存在时要优雅降级，不得直接报错白屏

### 4.3 状态管理与错误处理

必须处理以下状态：

- 首次进入页面时的 loading 状态
- 数据为空或部分字段缺失时的 empty/degraded 状态
- 接口 404 时的可读提示
- 接口 422/500 时的错误提示
- 网络异常或超时时的错误提示与重试入口

禁止：

- 页面白屏
- `catch` 后只打日志不提示用户
- 用假数据默认填满 UI 冒充成功状态

### 4.4 页面入口与导航闭环

必须至少补齐 1 个真实入口，使用户可从现有业务页面进入质量报告页。建议优先从以下位置之一接入：

- 数据集详情页
- 资产页中的数据集操作区

要求：

- 入口文案明确可理解，例如“查看质量报告”
- 数据集 ID 传递正确
- 页面跳转后可直接加载对应数据集结果

### 4.5 视觉与可读性要求

本任务不是做“好看截图”，而是做“可读决策页”，因此至少满足：

- 总分与四维分区层级清晰
- 错误、警告、建议语义分组明显
- 桌面端与常见笔记本宽度下不出现主要内容遮挡
- 不得引入与现有项目视觉语言明显冲突的重设计

---

## 五、多角色协同执行要求（强制）

本任务必须采用内部多角色协同并在汇报中明确责任归属；可由同一执行者串行承担多个角色，但汇报必须拆分视角：

1. `Frontend-Agent`：页面结构、交互状态、入口接入、视觉可读性。
2. `Contract-Agent`：API 类型定义与字段契约对齐。
3. `QA-Agent`：执行 typecheck/build/接口联调验证，提供真实输出证据。
4. `Reviewer-Agent`：检查范围漂移、文档一致性、验收项逐条闭环。

不接受“只写一个最终总结段落”的汇报方式。

---

## 六、必须提供的实测证据

### 6.1 前端门禁命令

必须执行并在汇报中贴出真实输出：

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
```

### 6.2 后端接口可用性复核

至少执行 1 组真实接口验证，证明前端消费的质量评分接口可用。可采用以下任一方式：

```bash
python -m pytest apps/api/tests/test_data_quality.py -q
```

或提供等价的真实接口请求/响应证据，但必须包含关键字段值，禁止只写“接口可用”。

### 6.3 页面真实链路证据（必须）

至少提供以下 3 类真实证据：

1. 成功链路：从入口页跳转到质量报告页并加载成功。
2. 降级链路：当 recommendations 为空或 stats 缺字段时，页面仍正常显示。
3. 失败链路：接口异常或指定数据集不存在时，页面展示可读错误。

证据形式可为：

- 浏览器页面文字化截图说明
- 网络请求摘录
- 控制台/测试输出
- Playwright 或等价工具输出

但必须是真实执行结果，不得使用示例值冒充实测证据。

---

## 七、完成判定

以下条件全部满足才可宣称完成：

- [ ] 前端已接入质量评分 API，字段契约无明显漂移
- [ ] 质量报告页面可按数据集 ID 访问
- [ ] 总分、四维评分、问题、建议、统计信息均可展示
- [ ] loading / empty / error 三类状态已覆盖
- [ ] 至少一个真实页面入口已打通
- [ ] typecheck 与 build 通过
- [ ] 至少 1 组接口证据 + 3 类页面链路证据完整
- [ ] 汇报已按统一证据格式归档
- [ ] 未越界推进 P1-T06 或其他后续任务

---

## 八、Copilot 审核重点

1. 是否真实消费 M7-T15 的后端契约，而不是本地 mock 自嗨。
2. 页面在缺字段、空数组、异常响应时是否仍可读且不白屏。
3. 是否只做质量报告页闭环，而未越界改动无关页面或后端逻辑。
4. 入口跳转是否真实可用，是否把 datasetId 正确传递到目标页。
5. 汇报是否提供真实联调证据，而不是纯静态页面说明。

---

## 九、风险提示

1. 若前端直接假设所有 stats 字段恒定存在，运行时容易崩溃；必须做容错降级。
2. 若只做 mock 展示而未联调真实接口，将不计入通过结论。
3. 若质量报告页入口挂在错误页面或路由不稳定，会导致闭环不成立。
4. 本任务不包含多表 Join、质量历史对比、评分趋势图，禁止借机扩范围。

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T16-R-20260331-160630-p1-t05-frontend-quality-report-page-and-visualization-report.md`

执行完成后必须按该命名提交统一证据汇报。

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 M7-T17 / P1-T06。
