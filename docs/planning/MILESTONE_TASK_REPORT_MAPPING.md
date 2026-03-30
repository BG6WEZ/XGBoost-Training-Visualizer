# 里程碑任务-汇报映射表

更新时间：2026-03-28

## 命名规则（自本轮起执行）

- 任务单：M{里程碑}-T{两位序号}-{时间戳}-{短标题}.md
- 汇报单：M{里程碑}-T{两位序号}-R-{时间戳}-{短标题}-report.md

说明：为保持历史可追溯，现阶段先做“映射”，暂不批量重命名旧文件。

## 历史任务映射（旧编号 -> 里程碑编号）

| 里程碑编号 | 旧任务单 | 对应汇报单 | 状态 |
|---|---|---|---|
| M2-T01 | docs/tasks/TASK-001/TASK-001-下一轮任务指令.md | docs/reports/2026-03-27-task-001-frontend-e2e-data-quality-gate.md | 已完成 |
| M3-T01 | docs/tasks/TASK-002/TASK-002-2026-03-27-任务指令.md | docs/reports/20260327-230950-task-002-browser-e2e-workspace-governance.md | 已完成 |
| M3-T02 | docs/tasks/TASK-003/TASK-003-20260327-230851-任务指令.md | docs/reports/20260327-232731-task-003-workspace-unification-guard.md | 已完成 |
| M3-T03 | docs/tasks/TASK-004/TASK-004-20260328-091828-任务指令.md | docs/reports/20260328-101820-task-004-workspace-e2e-closure.md | 已完成 |
| M3-T04 | docs/tasks/TASK-005/TASK-005-20260328-111029-任务指令.md | docs/reports/20260328-111029-task-005-training-success-closure.md | 已完成 |
| M4-T01 | docs/tasks/TASK-006/TASK-006-20260328-120712-任务指令.md | docs/reports/20260328-120712-task-006-model-api-and-venv-closure.md | 已完成 |
| M4-T02 | docs/tasks/TASK-007/TASK-007-20260328-135643-任务指令.md | docs/reports/task-007-20260328-doc-and-test-baseline-alignment.md | 已完成 |
| M4-T03 | docs/tasks/TASK-008/TASK-008-20260328-141008-任务指令.md | 待生成（等待 TASK-008 汇报） | 等待反馈 |
| M4-T04 | docs/tasks/M4/M4-T04-20260328-163352-任务指令.md | 待生成（等待 M4-T04 汇报） | 等待反馈 |
| M4-T05 | docs/tasks/M4/M4-T05-20260328-170549-任务指令.md | docs/reports/M4-T05-R-20260328-170549-e2e-logic-fix-and-success-closure-report.md | 已完成 |
| M4-T06 | docs/tasks/M4/M4-T06-20260328-174320-任务指令.md | docs/reports/M4-T06-R-20260328-174320-observability-and-gate-semantics-report.md | 部分通过（2 处缺陷移至 M4-T07） |
| M4-T07 | docs/tasks/M4/M4-T07-20260328-212256-model-type-detection-and-readme-gate.md | docs/reports/M4-T07-R-20260328-212256-model-type-detection-and-readme-gate.md | 已完成 |
| M4-T08 | docs/tasks/M4/M4-T08-20260328-213749-results-api-full-contract-coverage.md | docs/reports/M4-T08-R-20260328-213749-results-api-full-contract-coverage-report.md | 部分通过（1 处规约偏差移至 M4-T09） |
| M4-T09 | docs/tasks/M4/M4-T09-20260328-215210-metrics-history-not-found-contract-alignment.md | docs/reports/M4-T09-R-20260328-215210-metrics-history-not-found-contract-alignment-report.md | 已完成 |
| M4-T10 | docs/tasks/M4/M4-T10-20260328-221621-warning-free-regression-and-m4-closure.md | docs/reports/M4-T10-R-20260328-221621-warning-free-regression-and-m4-closure-report.md | 已完成 |
| M5-T01 | docs/tasks/M5/M5-T01-20260329-074310-m1-evidence-backfill-and-mvp-acceptance.md | docs/tasks/M5/M5-T01-R-20260329-074310-m1-evidence-backfill-and-mvp-acceptance-report.md | 部分通过（e2e success 条件未达标，移至 M5-T02） |
| M5-T02 | docs/tasks/M5/M5-T02-20260329-172233-e2e-gate-stability-and-queue-drain.md | docs/tasks/M5/M5-T02-R-20260329-172233-e2e-gate-stability-and-queue-drain-report.md | 已完成 |
| M5-T03 | docs/tasks/M5/M5-T03-20260329-174719-mvp-final-acceptance-and-rc-baseline.md | docs/tasks/M5/M5-T03-R-20260329-174719-mvp-final-acceptance-and-rc-baseline-report.md | 已完成 |
| M5-T04 | docs/tasks/M5/M5-T04-20260329-180305-rc1-release-readiness-and-ops-hardening.md | docs/tasks/M5/M5-T04-R-20260329-180305-rc1-release-readiness-and-ops-hardening-report.md | 已完成 |

| M6-T01 | docs/tasks/M6/M6-T01-20260329-182500-rc1-release-git-docker-deploy.md | docs/tasks/M6/M6-T01-R-20260329-182500-rc1-release-git-docker-deploy-report.md | 部分通过（Compose 冒烟与发布物对齐未完成，移至 M6-T02） |
| M6-T02 | docs/tasks/M6/M6-T02-20260329-195244-docker-smoke-closure-and-release-artifacts-alignment.md | docs/tasks/M6/M6-T02-R-20260329-195244-docker-smoke-closure-and-release-artifacts-alignment-report.md | 部分通过（前端 HTTP 200 ✅、API healthy ✅；worker 崩溃 ❌、package.json 版本未更新 ❌，移至 M6-T03） |
| M6-T03 | docs/tasks/M6/M6-T03-20260329-210708-worker-config-and-version-alignment.md | 待生成（等待 M6-T03 汇报） | 等待反馈 |

## 预任务阶段汇报（无独立任务单）

| 建议归档编号 | 汇报单 | 说明 |
|---|---|---|
| M2-PRE-R01 | docs/reports/2026-03-26-task1-2-router-split-contract.md | 早期路由与契约阶段汇报 |
| M2-PRE-R02 | docs/reports/2026-03-26-task3-4-assets-smoke.md | 早期资产冒烟阶段汇报 |
| M2-PRE-R03 | docs/reports/2026-03-27-e2e-verification-quality-closure.md | 早期 E2E 与质量收口汇报 |

## 当前项目位置

- 当前推进到：M6（RC1 正式发布阶段）
- 当前活动任务：M6-T03
- 当前等待项：M6-T03 汇报反馈
