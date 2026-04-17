# M7-T23 任务单：M7-T21 运行时 Redis 并发证据补齐闭环

任务编号: M7-T23  
时间戳: 20260401-140002  
所属计划: M7-T21 运行时证据补齐轮  
前置任务: M7-T22（已完成，保留未验证项）  
优先级: 最高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T21-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure.md
- [ ] docs/tasks/M7/M7-T21-R-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure-report.md
- [ ] docs/tasks/M7/M7-T22-R-20260401-121329-m7-t21-audit-fixes-report-presence-and-runtime-test-stability-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

M7-T22 已完成以下修复：

1. M7-T21 汇报文档补齐归档。
2. 并发测试稳定性修复（无事件循环错误）。
3. unit/integration 测试分层清晰。

但仍保留关键未验证项：

- Redis 集成并发证据尚未在运行环境完成。
- 真实状态迁移时间序列（T1/T2）尚未落盘证据。

本任务只做“运行时证据补齐”，不做新功能扩展。

---

## 二、任务目标

1. 在 Redis 可用环境中执行真实并发链路验证。
2. 采集并提交可复核时间序列证据：
   - T1: running=2, queued=1
   - T2: running=2, queued=0（queued 自动转 running）
3. 验证 running 集合在成功/失败/取消后无泄漏。
4. 关闭 M7-T21 的未验证项，形成完整闭环。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/tests/test_training_real_concurrency_e2e.py（仅当运行时验证暴露测试脚本问题）
- apps/api/tests/**（可新增 runtime 证据采集脚本）
- apps/worker/app/main.py（仅当运行时验证发现并发生命周期 bug）
- docs/tasks/M7/M7-T23-20260401-140002-m7-t21-runtime-redis-concurrency-evidence-closure.md
- docs/tasks/M7/M7-T23-R-20260401-140002-m7-t21-runtime-redis-concurrency-evidence-closure-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- P1-T10 功能开发（图表/残差分析）
- 无关前端页面与样式
- 数据库迁移（除非先报批）
- 参数校验、模板、Join 等已完成功能

---

## 四、执行要求（必须按顺序）

### 4.1 启动 Redis 运行环境

任选其一：

1. Docker 本地 Redis
```bash
docker run -d --name xgbv-redis -p 6379:6379 redis:alpine
```

2. 已有 Redis 服务（确保 REDIS_URL 可连通）

验证连接：
```bash
python - << 'PY'
import redis
r = redis.Redis.from_url('redis://localhost:6379/15')
print('PING=', r.ping())
PY
```

### 4.2 运行真实并发测试

```bash
python -m pytest apps/api/tests/test_training_real_concurrency_e2e.py -v -k "RealConcurrencyE2E"
```

要求：
- 不得 skip。
- 不得用 mock 替代 Redis。

### 4.3 采集状态时间序列证据

至少提交 2 个时间点的运行时快照，必须包含：

- timestamp
- running_count
- queued_count
- max_concurrency
- queue_positions

格式示例：
```json
{
  "time": "2026-04-01T14:12:30Z",
  "running_count": 2,
  "queued_count": 1,
  "max_concurrency": 2,
  "queue_positions": {"exp-c": 1}
}
```

以及：
```json
{
  "time": "2026-04-01T14:13:02Z",
  "running_count": 2,
  "queued_count": 0,
  "max_concurrency": 2,
  "queue_positions": {}
}
```

### 4.4 running 集合泄漏检查

在任务完成后检查：

- `training:running` 是否清空或符合实际运行数。
- 失败任务后是否正确释放。

可使用：
```bash
python - << 'PY'
import redis
r = redis.Redis.from_url('redis://localhost:6379/15', decode_responses=True)
print('running=', r.smembers('training:running'))
print('queued_len=', r.llen('training:queue'))
PY
```

---

## 五、多角色协同执行要求（强制）

1. `Runtime-Agent`：Redis 环境准备与真实并发链路执行。
2. `QA-Agent`：并发 E2E、状态序列、泄漏检查证据采集。
3. `Worker-Agent`：若运行时发现槽位注册/释放异常，负责修复。
4. `Governance-Agent`：检查汇报对“已验证/未验证”表述是否诚实。
5. `Reviewer-Agent`：判定是否关闭 M7-T21 未验证项。

---

## 六、必须提供的实测证据

### 6.1 Redis 可用性

- PING 成功输出。

### 6.2 真实并发 E2E

- `RealConcurrencyE2E` 测试执行输出（非 skip）。

### 6.3 状态时间序列

- 至少 T1/T2 两个时间点 JSON 或等价日志。

### 6.4 泄漏检查

- 训练结束后 `training:running` 检查输出。

### 6.5 回归检查（最小）

```bash
python -m pytest apps/api/tests/test_training_queue_concurrency.py -q
```

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] Redis 环境可连通并有证据
- [ ] RealConcurrencyE2E 实际执行（非 skip）
- [ ] 提供 T1/T2 状态迁移证据
- [ ] 证明 queued 可自动转 running
- [ ] running 集合无泄漏
- [ ] 汇报中未验证项归零或明确残留阻塞
- [ ] 映射表状态同步更新

---

## 八、Copilot 审核重点

1. 是否真正执行了 Redis 集成测试（非 skip/非 mock）。
2. 证据是否包含时间点与状态字段，能复核转移过程。
3. running 集合是否存在泄漏。
4. 汇报是否继续保持诚实声明。

---

## 九、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T23-R-20260401-140002-m7-t21-runtime-redis-concurrency-evidence-closure-report.md`

---

## 十、停点要求

本任务完成后停点，等待人工验收。未经确认不得推进 P1-T10 / M7-T24。
