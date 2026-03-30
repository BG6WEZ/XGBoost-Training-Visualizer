# M5-T04 任务指令：RC1 发布就绪与运维加固

**任务编号**: M5-T04  
**发布时间**: 2026-03-29 18:03:05  
**前置任务**: M5-T03（已审核通过）  
**预期汇报文件名**: `M5-T04-R-20260329-180305-rc1-release-readiness-and-ops-hardening-report.md`

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 读取本任务单全文

---

## 一、任务背景

M5-T03 已确认 MVP RC 基线可通过（57 测试通过、e2e success=true、rc_smoke success=true）。当前已知风险仍包括：

- Worker 需手工启动
- 队列积压缺乏自动治理策略

本轮目标是将上述风险收敛到“可发布可运维”的 RC1 状态。

---

## 二、任务目标

### 任务 1：Worker 自启动与存活守护

实现并提交一套本地可复用的 Worker 启动与守护方案（Windows + Unix 至少一侧可直接运行，另一侧给出等价说明）：

1. 提供启动脚本（例如 `start-local-worker.bat` / `start-local-worker.sh`）
2. 提供健康检查命令（确认 worker 在线与队列消费）
3. 在文档中给出“服务重启后最少步骤”

验收标准：重启后按文档执行，`/api/training/status` 可见 `worker_status=healthy`。

### 任务 2：队列治理最小策略

实现一个最小可执行的“队列积压处理机制”（脚本或命令化流程均可），包含：

1. 队列长度观测
2. 超阈值处理策略（例如阻断新训练、告警、人工清理命令）
3. e2e 前置检查联动说明

验收标准：可演示“队列有积压时的处理路径”，并有明确退出码或结果输出。

### 任务 3：RC1 发布就绪清单

产出发布就绪清单并给出结论：

- 运行前提（API/DB/Redis/Worker）
- 启动顺序
- 最小验收命令（pytest + e2e + rc_smoke）
- 回滚策略（最小版）
- 最终建议（Go / No-Go）

---

## 三、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| backend-expert | Worker 启动守护与队列治理脚本 |
| qa-engineer | 场景回放与回归验证（含积压场景） |
| devops-release | 发布清单、回滚步骤与 Go/No-Go 判定 |

---

## 四、必须提供的实测证据

1. Worker 启动/重启后状态验证输出（含 `worker_status`）
2. 队列治理策略演示输出（积压前后对比）
3. 最小验收命令输出：

```bash
python -m pytest tests/test_queue_health_check.py tests/test_e2e_validation_regression.py --tb=short
pnpm test:e2e:results:json
python scripts/rc_smoke.py
```

4. RC1 发布就绪清单（含回滚策略）

---

## 五、禁止事项

- 禁止仅提供文字描述而无实测输出
- 禁止复用历史命令输出冒充本轮结果
- 禁止省略队列积压场景演示

---

## 六、完成判定

以下条件全部满足才算完成：

- [ ] Worker 自启动/守护方案可执行
- [ ] 队列治理最小策略可演示
- [ ] 最小验收命令全部通过
- [ ] 汇报包含 RC1 Go/No-Go 结论与回滚策略
