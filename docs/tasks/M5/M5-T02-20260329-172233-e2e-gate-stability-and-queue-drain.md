# M5-T02 任务指令：E2E 门禁稳定性与训练队列清理

**任务编号**: M5-T02  
**发布时间**: 2026-03-29 17:22:33  
**前置任务**: M5-T01（已审核，业务证据通过但 e2e 验收项未达标）  
**预期汇报文件名**: `M5-T02-R-20260329-172233-e2e-gate-stability-and-queue-drain-report.md`

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 读取本任务单全文

---

## 一、问题背景

M5-T01 汇报中勾选了“最新 e2e 输出 success=true”，但审核复测结果为连续失败：

- 第一次复测：`success=false`，错误 `Training did not complete within 120 seconds`，`queue_position=2`
- 第二次复测：`success=false`，错误同上，`queue_position=3`

说明当前 e2e 门禁不稳定，受训练队列积压影响，尚不满足 MVP 验收闭环要求。

---

## 二、任务目标

### 任务 1：定位并修复 e2e 超时根因

围绕以下方向排查并给出可复现修复：

1. 训练队列是否存在历史任务积压（queued/running 状态长期不收敛）
2. e2e 脚本等待策略是否与实际队列行为不匹配（固定 120 秒过短）
3. 是否缺少“前置队列清理/任务隔离”机制，导致验证任务被排队

允许修复策略（可组合）：

- 在 e2e 脚本中增加队列健康前置检查（如 queue_length 门槛）
- 增加训练等待超时参数可配置化并在脚本中合理设定
- 增加用于测试环境的 stale 任务清理步骤
- 为 e2e 使用独立测试数据集和低成本训练参数，缩短收敛时间

### 任务 2：恢复 e2e 门禁通过

必须连续执行两次以下命令，且两次都成功：

```bash
pnpm test:e2e:results:json
```

验收要求：

- 两次输出均满足 `success=true`
- 不出现 `Training did not complete within 120 seconds`
- 输出中 `experiment_id` 均有效

### 任务 3：补充回归保护

新增至少 1 个自动化测试，覆盖你本次修复的关键逻辑（例如超时策略、队列前置检查或状态判定逻辑），避免再次回归。

---

## 三、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| backend-expert | 定位队列积压与训练状态流转问题 |
| qa-engineer | 设计并验证连续两次 e2e success=true |
| reliability-engineer | 增加回归保护测试，防止超时回归 |
| tech-lead | 汇总证据并形成可审计结论 |

---

## 四、必须提供的实测证据

1. 两次 `pnpm test:e2e:results:json` 的完整原始输出（含 success 字段）
2. 若做了队列清理，提供清理前后队列长度或任务状态对比证据
3. 新增自动化测试的执行输出（测试名 + PASS）
4. 全量关键回归命令输出（至少包含：
   - `python -m pytest tests/test_e2e_validation_regression.py --tb=short`
   - 你新增测试文件）

---

## 五、禁止事项

- 禁止在汇报中用历史成功结果替代本次实测结果
- 禁止仅通过延长超时掩盖真实队列问题而不解释根因
- 禁止跳过“连续两次 success=true”要求
- 禁止将未来计划写成已完成事实

---

## 六、完成判定

以下条件全部满足才算完成：

- [ ] 已定位并说明 e2e 超时根因
- [ ] 连续两次 `pnpm test:e2e:results:json` 均 `success=true`
- [ ] 新增至少 1 个回归测试并通过
- [ ] 汇报证据与实测输出一致
