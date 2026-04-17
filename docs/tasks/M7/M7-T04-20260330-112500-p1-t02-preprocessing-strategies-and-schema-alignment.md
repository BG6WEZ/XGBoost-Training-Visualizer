# M7-T04 任务单：P1-T02 预处理策略与契约对齐

任务编号: M7-T04  
时间戳: 20260330-112500  
所属计划: P1-S1 / P1-T02  
前置任务: M7-T03 审核通过后方可开始  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md
- [ ] docs/tasks/M7/M7-T03-20260330-112000-p1-t01-feature-engineering-backend-foundation.md

若 M7-T03 未经 Copilot 审核通过，不得启动本任务。

---

## 一、任务背景

在 P1-T01 中，项目将具备特征工程后端基础能力；但训练前仍缺少稳定的预处理策略能力。当前需要补齐：

- 缺失值处理策略
- 基础编码策略
- 契约与输出 schema 对齐

本任务的目标是把“预处理”从抽象任务类型变成可执行、可验证、可追踪的真实能力，并保证与后续训练链路兼容。

---

## 二、任务目标

完成以下闭环：

1. API 接受预处理任务请求。
2. API 校验缺失值和编码策略配置。
3. Worker 执行真实预处理逻辑并输出文件。
4. 输出 schema 与结果摘要可被 API 返回。
5. 预处理结果可作为后续训练或特征工程输入。

---

## 三、范围边界

### 3.1 本任务允许修改的范围

- `apps/api/app/routers/datasets.py`
- `apps/api/app/schemas/` 下预处理相关请求/响应
- `apps/api/app/services/` 下任务校验与结果组织逻辑
- `apps/worker/app/tasks/training.py`
- `apps/worker/app/main.py`
- `apps/api/tests/` 下与预处理相关测试
- 必要的已有文档事实同步

### 3.2 本任务明确禁止修改的范围

- 不得提前实现前端预处理页面
- 不得提前实现多表 Join、质量评分、模型版本
- 不得引入与本任务无关的新存储机制
- 不得修改无关测试让其“看起来通过”

---

## 四、详细交付要求

### 任务 4.1：缺失值处理策略落地

至少支持以下策略：

- `forward_fill`
- `mean_fill`
- `drop_rows`

要求：

- 仅对允许的数据类型执行对应策略
- 非法列类型必须报错
- 必须记录哪些列被处理、处理前后缺失值数量

验收标准：

- 处理结果进入 `async_tasks.result`
- 返回结果包含策略名、处理列清单、统计摘要

### 任务 4.2：基础编码策略落地

至少支持：

- `one_hot`
- `label_encoding`

要求：

- 自动识别目标编码列是否为分类列
- 对高基数列如需限制，必须明确报错或限制说明
- 输出字段变化必须进入结果摘要

验收标准：

- 编码后的输出文件真实存在
- 原始列数与输出列数变化可解释

### 任务 4.3：契约与 schema 对齐

要求：

- API 请求 schema、响应 schema、worker 结果 JSON、测试断言一致
- 错误场景返回字段必须稳定，不能随意变形

验收标准：

- 至少补 1 组合同测试
- 至少补 1 组失败场景测试

---

## 五、实现约束

1. 优先复用 `run_preprocessing_task()` 入口，不要再新建一套预处理执行路径。
2. 输出文件命名与存储路径必须与现有 storage 体系一致。
3. 不允许将“已支持策略”写在文档里，但代码中只是 TODO。
4. 对任何自动推断行为，必须在结果里留下可追溯摘要。

---

## 六、建议协作分工（Trae 内部自组织或按角色执行）

- Backend/API 角色：请求契约、参数校验、响应结构
- Worker 角色：缺失值处理与编码逻辑
- QA 角色：参数化测试、负向场景、链路验证
- Reviewer 角色：检查 schema/router/worker/tests 一致性

---

## 七、必须提供的实测证据

### 7.1 自动化测试

至少执行并贴出真实输出：

```bash
cd apps/api
python -m pytest tests/test_new_endpoints.py tests/test_workspace_consistency.py --tb=short
```

若新增专用测试文件，必须将新增测试文件一起执行。

### 7.2 真实链路验证

至少完成一次预处理任务真实验证，证据必须包含：

- 请求配置
- 任务 ID
- 最终状态
- 输出文件路径
- 处理摘要（如缺失值变化、编码列变化）

### 7.3 失败场景验证

至少提供 1 条失败案例，例如：

- 非法编码列
- 对非数值列执行均值填充
- 不支持的策略名

并贴出实际错误输出。

---

## 八、完成判定

以下条件全部满足才算完成：

- [ ] 缺失值处理策略真实可用
- [ ] 基础编码策略真实可用
- [ ] API / worker / result schema 已对齐
- [ ] 至少 1 条成功链路与 1 条失败链路已验证
- [ ] 输出文件与摘要均可追踪
- [ ] 汇报中区分已验证与未验证部分

---

## 九、Copilot 审核重点

GitHub Copilot 审核时重点检查：

1. 预处理是否是真实执行，而不是只更新任务状态
2. 编码与缺失值策略是否会破坏下游训练兼容性
3. response schema 是否稳定、可测试
4. 是否越界做了前端页面或质量评分

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T04-R-20260330-112500-p1-t02-preprocessing-strategies-and-schema-alignment-report.md`

Trae 完成后必须按该命名提交汇报。