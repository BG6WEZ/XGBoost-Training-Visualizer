# M7-T88 — Phase-4 / Task 4.4 再收口（request_id 注入与测试证据补齐）

> 任务编号：M7-T88  
> 阶段：Phase-4 / Task 4.4 Re-open  
> 前置：M7-T87（审计不通过）  
> 时间戳：20260416-182618

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T87-AUDIT-SUMMARY-20260416-182618.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.4`

---

## 一、本轮目标

本轮**不得进入 Phase-5**。只允许继续收口 **Task 4.4 结构化日志**，重点补齐两类缺口：

1. **让 `request_id` 稳定进入普通子 logger 的日志**
2. **补齐“全量测试通过”的真实证据**

---

## 二、允许修改的范围文件

- `apps/api/app/logging_config.py`
- `apps/api/app/main.py`
- `apps/worker/app/logging_config.py`
- `apps/worker/app/main.py`
- 如确有必要，可补充与本轮验证直接相关的测试文件
- 本轮新增报告文件：`docs/tasks/M7/M7-T88-R-<timestamp>-p4-t44-request-id-log-injection-and-test-evidence-report.md`

禁止越界到：

- 业务路由大改
- Phase-5 或后续任务

---

## 三、上一轮未通过的核心问题

你必须逐项消除以下问题：

1. **`request_id` 未稳定注入到普通子 logger**
   - 当前运行时复测中，`demo.child` 输出的 JSON 日志没有 `request_id`

2. **报告与运行时事实不一致**
   - 报告写有 `request_id`
   - 真实输出没有 `request_id`

3. **缺少“全量测试通过”证据**
   - 原计划明确要求全量测试通过
   - 上一轮报告没有给出对应命令与输出

---

## 四、必须完成的最小工作

### 1) 修正 request_id 注入机制

目标：

- 让普通子 logger（例如 `logging.getLogger("demo.child")`）输出的日志也包含 `request_id`

可接受方向：

- 将 filter 挂到 handler 而不是仅挂 root logger
- 或采用等价方式，确保所有经过 handler 的记录都能注入 `request_id`

要求：

- `LOG_FORMAT=json` 时，业务日志必须真正出现 `request_id`
- `LOG_FORMAT=text` 时，业务日志也应能显示 `request_id`

### 2) 重新提交与运行时事实一致的日志样例

报告中的样例必须来自真实运行结果，不得手写虚构。

至少提供：

- 一条 JSON 业务日志，包含 `request_id`
- 一条 text 业务日志，包含 `request_id`（若已验证）

### 3) 补做 request_id 运行时验证

至少验证以下之一：

#### 方案 A：最小脚本验证

- 设置 `request_id_ctx`
- 用普通子 logger 记录日志
- 验证输出中真的有 `request_id`

#### 方案 B：HTTP 请求验证

- 启动 API
- 发送带或不带 `X-Request-ID` 的请求
- 验证响应头与日志中的 `request_id`

要求：

- 不能只看代码结构
- 必须有真实命令与真实输出

### 4) 补齐“全量测试通过”证据

若声称满足原计划中的“全量测试通过”，则必须提交：

- 实际执行命令
- 测试输出摘要或完整输出

若本轮不做全量测试，则必须诚实说明，并**不得**写“已满足全量测试通过”。

你可以选择：

- 真正执行全量测试并提交证据
- 或在报告中如实标记该条件未完成，但这将影响是否能通过

### 5) Worker 端至少补一个最小验证

由于本轮要求 API 与 Worker 都接入日志配置，至少补一个最小 Worker 验证：

- `LOG_FORMAT=json` 启动日志样例
- 或 `setup_logging()` 后的最小脚本日志样例

---

## 五、通过条件（全部满足才算通过）

- [ ] `request_id` 稳定注入到普通子 logger 的日志中
- [ ] `LOG_FORMAT=json` 时业务日志为合法 JSON 且包含 `request_id`
- [ ] API 与 Worker 都接入新日志配置
- [ ] 至少一类 request_id 运行时验证已完成
- [ ] “全量测试通过”已提交真实证据
- [ ] 产出与本轮编号一致的 `M7-T88-R-...` 报告
- [ ] 未越界推进到 Phase-5 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T88-R-<timestamp>-p4-t44-request-id-log-injection-and-test-evidence-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. request_id 注入机制如何修正
4. JSON 日志真实样例
5. text 日志真实样例（若已验证）
6. Worker 最小验证方式
7. 全量测试执行命令
8. 全量测试结果
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 4.4 验收

---

## 七、明确禁止

- 不得继续提交与运行时事实不一致的日志样例
- 不得只改代码结构而不做运行时验证
- 不得在没有证据时写“全量测试通过”
- 不得提前进入 Phase-5
