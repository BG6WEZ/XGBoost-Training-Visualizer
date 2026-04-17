# M7-T89 — Phase-4 / Task 4.4 再收口（全量测试证据与 Worker 日志核查）

> 任务编号：M7-T89  
> 阶段：Phase-4 / Task 4.4 Re-open  
> 前置：M7-T88（审计不通过）  
> 时间戳：20260416-183842

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T88-AUDIT-SUMMARY-20260416-183842.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.4`

---

## 一、本轮目标

本轮**不得进入 Phase-5**。只允许继续收口 **Task 4.4 结构化日志**，重点补齐两类证据：

1. **真正的全量测试通过证据**
2. **Worker 侧最小日志验证证据**

---

## 二、允许修改的范围文件

- `apps/api/app/logging_config.py`
- `apps/api/app/main.py`
- `apps/worker/app/logging_config.py`
- `apps/worker/app/main.py`
- 如确有必要，可补充少量与验证直接相关的测试或说明
- 本轮新增报告文件：`docs/tasks/M7/M7-T89-R-<timestamp>-p4-t44-full-test-evidence-and-worker-log-check-report.md`

禁止越界到：

- 业务路由大改
- Phase-5 或后续任务

---

## 三、上一轮未通过的核心问题

你必须逐项消除以下问题：

1. **“全量测试通过”证据不成立**
   - 上一轮实际只执行了 `tests/test_health.py`
   - 但报告写成了“全量测试通过”

2. **Worker 端缺少最小运行验证**
   - 报告中仍写未执行

---

## 四、必须完成的最小工作

### 1) 对“全量测试通过”做真实收口

你必须二选一：

#### 方案 A：真正执行全量测试

- 运行项目当前约定的 API 全量测试集合
- 提交真实命令与真实输出

#### 方案 B：诚实收缩结论

- 如果当前无法完成全量测试，就不要再写“全量测试通过”
- 报告中必须把这条明确标记为未完成 / 未验证

注意：

- 若选择方案 B，本轮通常仍难以通过 `Task 4.4`
- 因为原计划通过条件明确包含“全量测试通过”

### 2) 提交 Worker 最小日志验证

至少完成以下一种：

#### 方案 A：最小脚本验证

- 在 Worker 代码路径下调用 `setup_logging()`
- 输出一条 `LOG_FORMAT=json` 日志
- 提供真实输出

#### 方案 B：Worker 启动日志验证

- 在可运行环境中启动 Worker
- 抓取一条启动日志
- 证明 Worker 端日志配置已接入

### 3) 报告必须精确描述验证范围

报告中必须明确：

- 哪些是 API 端已验证
- 哪些是 Worker 端已验证
- 哪些测试是全量
- 哪些测试只是专项

禁止再出现：

- 用单文件测试通过替代“全量测试通过”

### 4) 如仍保留日志样例，必须来自真实运行

要求：

- JSON 样例来自真实输出
- text 样例来自真实输出
- Worker 样例来自真实输出

---

## 五、通过条件（全部满足才算通过）

- [ ] `request_id` 稳定注入到普通子 logger 的日志中
- [ ] `LOG_FORMAT=json` 时业务日志为合法 JSON 且包含 `request_id`
- [ ] API 与 Worker 都接入新日志配置
- [ ] 已提交 Worker 最小日志验证证据
- [ ] 已提交真正的全量测试通过证据
- [ ] 产出与本轮编号一致的 `M7-T89-R-...` 报告
- [ ] 未越界推进到 Phase-5 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T89-R-<timestamp>-p4-t44-full-test-evidence-and-worker-log-check-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 全量测试执行命令
4. 全量测试结果
5. Worker 最小验证方式
6. Worker 日志真实样例
7. API 日志真实样例
8. 已验证通过项
9. 未验证部分
10. 风险与限制
11. 是否建议提交 Task 4.4 验收

---

## 七、明确禁止

- 不得再把 `tests/test_health.py` 通过写成“全量测试通过”
- 不得继续让 Worker 端保持完全未验证
- 不得提前进入 Phase-5
