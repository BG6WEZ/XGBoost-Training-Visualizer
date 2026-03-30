# M5-T03 任务指令：MVP 最终验收与发布候选基线

**任务编号**: M5-T03  
**发布时间**: 2026-03-29 17:47:19  
**前置任务**: M5-T02（已审核通过）  
**预期汇报文件名**: `M5-T03-R-20260329-174719-mvp-final-acceptance-and-rc-baseline-report.md`

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 读取本任务单全文

---

## 一、任务背景

当前已完成：

- M4 结果与对比能力收口
- M1 证据补强（目录型资产与多 CSV 逻辑数据集）
- e2e 门禁稳定性恢复（连续两次 success=true）

下一步目标：形成可交付的 MVP 发布候选（RC）基线与最终验收包。

---

## 二、任务目标

### 任务 1：一键验收脚本化（RC smoke）

新增一个统一脚本（建议 `apps/api/scripts/rc_smoke.py` 或等价路径），串联以下检查：

1. 服务健康检查（API/readiness/worker）
2. M1 资产链路最小验证（目录资产扫描 + 多文件数据集存在）
3. 结果链路验证（执行一次 `e2e_validation.py --output json`）
4. 输出统一 JSON 报告（包含每个检查项 status 与 error）

验收标准：脚本支持退出码语义（全部通过返回 0，否则非 0）。

### 任务 2：发布候选回归基线

执行并贴出真实输出：

```bash
python -m pytest tests/test_results_contract.py tests/test_results_extended_contract.py tests/test_e2e_validation_regression.py tests/test_workspace_consistency.py tests/test_observability_regression.py tests/test_queue_health_check.py --tb=short
pnpm test:e2e:results:json
python scripts/rc_smoke.py
```

验收标准：
- pytest 全部通过（>=57 项）
- e2e `success=true`
- rc_smoke 脚本 `success=true`

### 任务 3：最终验收文档对齐

在汇报中提供“发布候选基线摘要表”：

- 代码基线（关键文件）
- 测试基线（通过数、耗时）
- 运行基线（e2e 与 rc_smoke）
- 已知风险（若有）
- 发布建议（Go / No-Go）

---

## 三、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| backend-expert | 实现 rc_smoke 编排脚本与退出码语义 |
| qa-engineer | 执行全量回归、e2e、smoke 并收集原始输出 |
| release-manager | 整理 RC 基线摘要与发布建议 |

---

## 四、必须提供的实测证据

1. pytest 命令完整 summary 输出（包含通过数）
2. `pnpm test:e2e:results:json` 完整 JSON 输出
3. `python scripts/rc_smoke.py` 完整 JSON 输出
4. Go/No-Go 结论与理由

---

## 五、禁止事项

- 禁止省略任一验收命令输出
- 禁止将历史结果当作本次结果复用
- 禁止以手工描述替代 rc_smoke 脚本输出

---

## 六、完成判定

以下条件全部满足才算完成：

- [ ] rc_smoke 编排脚本可运行且输出结构化结果
- [ ] pytest 全量回归通过（>=57）
- [ ] e2e success=true
- [ ] rc_smoke success=true
- [ ] 汇报含 Go/No-Go 结论
