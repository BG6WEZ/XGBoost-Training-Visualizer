# M7-T03 任务单：P1-T01 特征工程后端基础能力落地

任务编号: M7-T03  
时间戳: 20260330-112000  
所属计划: P1-S1 / P1-T01  
前置任务: M7-T01（P1/P2 计划已发布）、M7-T02（阶段分界总纪要已补齐）  
优先级: 最高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md
- [ ] docs/tasks/M7/M7-T02-20260330-111500-mvp-summary-and-p1-p2-transition-record.md

未完成上述预读，不得开始编码。

---

## 一、任务背景

MVP 已完成数据资产、实验、训练、结果对比主链路，但自动化特征工程仍未落地。目前代码中虽然已经存在：

- `async_tasks` 表
- `preprocessing` / `feature_engineering` 队列
- worker 内 `run_feature_engineering_task()` 骨架

但尚未形成可被前端与 API 稳定调用、可落盘、可验证的后端特征工程能力。

本任务要求先完成后端基础能力，不做前端页面，不提前做 P1-T02 的缺失值处理与编码策略扩展。

---

## 二、任务目标

完成可执行的“时间特征 + 滞后特征 + 滚动统计特征”后端能力，打通以下闭环：

1. API 接受特征工程任务请求。
2. API 校验请求并入队。
3. Worker 正确消费并生成特征工程结果文件。
4. 结果文件写入 `workspace/` 对应工件目录。
5. `async_tasks.result` 记录输出路径、字段变化、执行摘要。
6. API 可查询任务状态与最终结果。

---

## 三、范围边界

### 3.1 本任务允许修改的范围

- `apps/api/app/routers/datasets.py`
- `apps/api/app/schemas/` 下与数据集任务相关的 schema 文件
- `apps/api/app/models/`（仅在确有必要时补充字段；如无必要则不要动表结构）
- `apps/api/app/services/` 下与任务入队、校验、结果组织相关代码
- `apps/worker/app/tasks/training.py`
- `apps/worker/app/main.py`
- `apps/api/tests/` 与本任务直接相关的测试文件
- 必要的最小文档同步（仅限已存在文档的事实更新）

### 3.2 本任务明确禁止修改的范围

- 不得提前实现前端页面
- 不得提前实现缺失值处理、编码转换、多表 Join
- 不得修改 `docs/planning/MILESTONE_TASK_REPORT_MAPPING.md` 以外的历史映射关系
- 不得引入无关重构、无关依赖、无关目录清理
- 不得把占位返回值包装成已完成能力

---

## 四、详细交付要求

### 任务 4.1：定义并收敛特征工程请求契约

要求新增或完善 Feature Engineering 请求结构，至少支持：

- 时间列名称
- 时间特征开关：`hour`、`dayofweek`、`month`、`is_weekend`
- lag 特征列表：`[1, 6, 12, 24]`
- rolling 窗口列表：`[3, 6, 24]`
- rolling 指标至少支持：`mean`、`min`、`max`、`std`

验收标准：

- 非法配置返回 422
- 响应错误信息中必须指出具体非法字段或非法组合

### 任务 4.2：实现 Worker 特征生成能力

要求在 worker 中完成真实数据处理逻辑，而不是伪实现：

- 时间特征从指定时间列提取
- lag 特征基于目标列或指定数值列生成
- rolling 统计基于顺序数据生成
- 输出文件必须能被后续训练或人工检查直接读取

验收标准：

- 至少生成以下字段类型：时间字段、lag 字段、rolling 字段
- 输出文件物理落盘
- `async_tasks.result` 中包含：输出文件名、完整路径、生成字段列表、原始列数、输出列数

### 任务 4.3：打通 API-Worker-Storage 闭环

要求：

- API 提交任务后，数据库中可见 `queued -> running -> completed/failed`
- worker 任务失败时，错误原因进入 `async_tasks.error_message`
- 成功时，API 查询任务状态能看到结果摘要

验收标准：

- 至少完成 1 次真实任务闭环
- 失败场景有可读错误消息

---

## 五、实现约束

1. 优先复用现有 `async_tasks`、队列、storage 适配层，不要新造平行机制。
2. 结果文件路径必须与当前 `workspace/` 工件体系一致。
3. schema、router、worker、测试、文档描述必须一致。
4. 若现有 `run_feature_engineering_task()` 只是骨架，必须明确补成真实实现。
5. 若需要新增字段，必须说明为什么现有 JSON 结果字段不够，而不是直接扩表。

---

## 六、建议协作分工（Trae 内部自组织或按角色执行）

- Backend/API 角色：定义请求契约、入队校验、状态查询返回
- Worker 角色：实现真实特征生成逻辑与结果摘要
- QA 角色：补单测、集成测试、失败场景测试，整理命令输出
- Reviewer 角色：核对 schema/router/worker/test/docs 一致性

如果 Trae 不拆角色，也必须在汇报里说明由谁完成了上述职责。

---

## 七、必须提供的实测证据

### 7.1 自动化测试

至少执行并贴出真实输出：

```bash
cd apps/api
python -m pytest tests/test_new_endpoints.py tests/test_data_quality.py --tb=short
```

如果你新增了专用测试文件，也必须把新增测试文件一起执行并贴出 summary。

### 7.2 最小集成验证

至少完成一次 API -> Worker -> 结果落盘闭环验证，并贴出：

```bash
# 示例要求，不限定具体命令形式，但必须有等价证据
curl /api/datasets/{id}/feature-engineering
curl /api/datasets/tasks/{task_id}
```

证据必须包含：

- 任务 ID
- 最终状态 `completed`
- 输出文件路径
- 生成字段列表或字段数量变化

### 7.3 必须区分未验证项

若没有真实跑通 worker 消费链路，不得写“功能完成”，只能写“代码已改但未验证”。

---

## 八、完成判定

以下条件全部满足才算完成：

- [ ] Feature engineering 请求契约已稳定
- [ ] Worker 真实生成时间/lag/rolling 特征
- [ ] 输出文件已成功落盘并可追踪
- [ ] API / worker / async task 状态链路打通
- [ ] 至少完成 1 次真实闭环验证
- [ ] 测试结果已贴出并区分通过/失败/未运行
- [ ] 汇报中明确风险与限制

---

## 九、Copilot 审核重点

GitHub Copilot 审核时重点检查：

1. 是否是真实特征工程而不是占位实现
2. 请求契约是否与 API 响应、测试完全一致
3. 输出文件是否真实落盘、而不是只写数据库结果
4. 失败场景是否可定位
5. 是否越界做了 P1-T02 或前端页面

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T03-R-20260330-112000-p1-t01-feature-engineering-backend-foundation-report.md`

Trae 完成后必须按该命名提交汇报。