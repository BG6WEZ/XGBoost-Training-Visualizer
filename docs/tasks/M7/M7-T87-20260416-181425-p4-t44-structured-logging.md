# M7-T87 — Phase-4 / Task 4.4 结构化日志

> 任务编号：M7-T87  
> 阶段：Phase-4 / Task 4.4  
> 前置：M7-T86（Task 4.3 验收通过）  
> 时间戳：20260416-181425

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T86-AUDIT-SUMMARY-20260416-181425.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.4`

---

## 一、本轮目标

进入 `Phase-4 / Task 4.4 — 结构化日志`，目标是让 API 与 Worker 在生产环境输出可被日志系统解析的结构化 JSON 日志，并在 API 请求链路中补充 `request_id`。

---

## 二、允许修改的范围文件

- `apps/api/app/main.py`
- `apps/worker/app/main.py`
- `apps/api/app/logging_config.py`（新增）
- 如确有必要，可补充极少量与本轮测试直接相关的测试文件
- 本轮新增报告文件：`docs/tasks/M7/M7-T87-R-<timestamp>-p4-t44-structured-logging-report.md`

禁止越界到：

- 业务路由逻辑大改
- 前端改动
- Task 5.1 或后续任务

---

## 三、必须完成的最小工作

### 1) 新增统一日志配置模块

新增：

- `apps/api/app/logging_config.py`

要求：

- 支持 `LOG_FORMAT=text|json`
- 默认 `text`
- `json` 时输出合法 JSON
- `text` 时保持本地开发可读性

### 2) JSON 日志至少包含以下字段

生产日志（`LOG_FORMAT=json`）至少包含：

- `timestamp`
- `level`
- `message`
- `module`
- `request_id`（API 端请求日志）

若存在额外字段，可以附加，但不得缺上述核心字段。

### 3) API 增加 request_id 中间件

要求：

- 优先复用请求头 `X-Request-ID`
- 若请求头不存在，则自动生成
- 每个 API 请求有唯一 `request_id`
- 日志里能带上该字段

若响应头也能回写 `X-Request-ID`，建议一起完成。

### 4) API 与 Worker 都接入新日志配置

要求：

- `apps/api/app/main.py` 使用统一日志配置
- `apps/worker/app/main.py` 使用统一日志配置

### 5) 必须完成验证

至少完成以下验证：

1. `LOG_FORMAT=json` 时输出一条合法 JSON 日志
2. JSON 日志包含必需字段
3. API 请求能生成 / 透传 `request_id`

若可以快速验证，建议补做：

- `LOG_FORMAT=text` 时输出人类可读日志
- Worker 启动日志验证

---

## 四、通过条件（全部满足才算通过）

- [ ] 已新增 `apps/api/app/logging_config.py`
- [ ] `LOG_FORMAT=json` 时日志为合法 JSON
- [ ] JSON 日志包含 `timestamp`、`level`、`message`、`module`、`request_id`
- [ ] 每个 API 请求有唯一 `request_id`
- [ ] API 与 Worker 都接入新日志配置
- [ ] 全量测试通过
- [ ] 产出与本轮编号一致的 `M7-T87-R-...` 报告
- [ ] 未越界推进到 Phase-5 或后续任务

---

## 五、汇报要求

完成后提交：

- `M7-T87-R-<timestamp>-p4-t44-structured-logging-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. `logging_config.py` 的职责
4. `LOG_FORMAT` 如何切换
5. `request_id` 如何生成 / 透传
6. 实际验证命令
7. JSON 日志样例
8. text 日志样例（若已验证）
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 4.4 验收

---

## 六、明确禁止

- 不得只改 API 不改 Worker
- 不得输出伪 JSON 或不稳定 JSON
- 不得缺少 `request_id`
- 不得提前进入 Phase-5
