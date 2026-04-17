# 里程碑任务-汇报映射表

更新时间：2026-04-01

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
| M6-T04 | docs/tasks/M6/M6-T04-20260329-215608-rc1-final-gate-and-handover.md | docs/reports/M6-T04-R-20260329-215608-rc1-final-gate-and-handover-report.md | 已完成（后续脚本逻辑问题移至 M6-T05） |
| M6-T05 | docs/tasks/M6/M6-T05-20260330-085040-final-gate-fail-closed-loop-and-doc-alignment.md | docs/reports/M6-T05-R-20260330-085040-final-gate-fail-closed-loop-and-doc-alignment-report.md | 已完成 |
| M7-T01 | docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md | 无（计划与治理任务单） | 已完成 |
| M7-T02 | docs/tasks/M7/M7-T02-20260330-111500-mvp-summary-and-p1-p2-transition-record.md | 无（阶段分界总纪要） | 已完成 |
| M7-T03 | docs/tasks/M7/M7-T03-20260330-112000-p1-t01-feature-engineering-backend-foundation.md | docs/tasks/M7/M7-T03-R-20260330-112000-p1-t01-feature-engineering-backend-foundation-report.md | 已完成（分两轮：原提交部分通过→M7-T05修复→通过） |
| M7-T04 | docs/tasks/M7/M7-T04-20260330-112500-p1-t02-preprocessing-strategies-and-schema-alignment.md | docs/tasks/M7/M7-T04-R-20260330-112500-p1-t02-preprocessing-strategies-and-schema-alignment-report.md | 部分通过（测试结果失实 2 条隐瞒、缺链路证据、缺失败场景真实输出；移至 M7-T06） |
| M7-T05 | docs/tasks/M7/M7-T05-20260330-113500-m7-t03-audit-fixes-and-evidence-closure.md | docs/tasks/M7/M7-T05-R-20260330-113500-m7-t03-audit-fixes-and-evidence-closure-report.md | 已完成（7个测试全通过；422校验有效；路径修正完成；默认值一致；所有阻断项解除） |
| M7-T06 | docs/tasks/M7/M7-T06-20260330-120000-m7-t04-audit-fixes-and-evidence-closure.md | docs/tasks/M7/M7-T06-R-20260330-120000-m7-t04-audit-fixes-and-evidence-closure-report.md | 已完成（Copilot 直接执行；35/35 tests；E2E 强断言；routers.py 补全 encoding_strategy；失败场景真实输出） |
| M7-T07 | docs/tasks/M7/M7-T07-20260330-123500-p1-t03-frontend-preprocess-feature-task-chain.md | docs/tasks/M7/M7-T07-R-20260330-123500-p1-t03-frontend-preprocess-feature-task-chain-report.md | 部分通过（typecheck/build/回归通过；但请求体契约不匹配+任务状态路径错误，移至 M7-T08） |
| M7-T08 | docs/tasks/M7/M7-T08-20260330-131800-m7-t07-audit-fixes-frontend-contract-and-task-status-chain.md | docs/tasks/M7/M7-T08-R-20260330-131800-m7-t07-audit-fixes-frontend-contract-and-task-status-chain-report.md | 部分通过（路径/请求体/枚举修复已完成；轮询失败缺少可见提示且运行时链路证据不足，移至 M7-T09） |
| M7-T09 | docs/tasks/M7/M7-T09-20260331-082720-m7-t08-audit-fixes-visible-polling-error-and-runtime-evidence.md | docs/reports/M7-T09-R-20260331-082720-m7-t08-audit-fixes-visible-polling-error-and-runtime-evidence-report.md | 部分通过（轮询失败可见提示已修复并经代码/门禁复核通过；但 2 成功+1 失败链路证据为示例值，不可复核，移至 M7-T10） |
| M7-T10 | docs/tasks/M7/M7-T10-20260331-083728-m7-t09-audit-fixes-real-runtime-evidence-and-archive-path.md | docs/reports/M7-T10-R-20260331-083728-m7-t09-audit-fixes-real-runtime-evidence-and-archive-path-report.md | 部分通过（真实链路证据已复核通过；但与“不得修改代码文件”范围约束冲突，且“无代码修改”结论与实际新增脚本不一致，移至 M7-T11） |
| M7-T11 | docs/tasks/M7/M7-T11-20260331-085010-m7-t10-audit-fixes-scope-and-archive-governance-closure.md | docs/tasks/M7/M7-T11-R-20260331-085010-m7-t10-audit-fixes-scope-and-archive-governance-closure-report.md | 已完成（采用方案 A 删除越界脚本；修正文档事实一致性；门禁复核通过） |
| M7-T12 | docs/tasks/M7/M7-T12-20260331-091851-mvp-upload-recovery-and-docker-ingestion-simplification.md | docs/tasks/M7/M7-T12-R-20260331-091851-mvp-upload-recovery-and-docker-ingestion-simplification-report.md | 已完成（2 成功 + 2 失败链路证据；门禁通过） |
| M7-T13 | docs/tasks/M7/M7-T13-20260331-095253-upload-ui-closure-and-self-governance.md | docs/tasks/M7/M7-T13-R-20260331-095253-upload-ui-closure-and-self-governance-report.md | 已完成（前端上传入口闭环；一键创建数据集；门禁通过） |
| M7-T14 | docs/tasks/M7/M7-T14-20260331-140904-mainline-stability-hardening-and-governance-closure.md | docs/tasks/M7/M7-T14-R-20260331-140904-mainline-stability-hardening-and-governance-closure-report.md | 已完成（上传稳定性/大文件持久化/训练容错与诊断加固闭环） |
| M7-T15 | docs/tasks/M7/M7-T15-20260331-141549-p1-t04-data-quality-scoring-engine-and-api-closure.md | docs/tasks/M7/M7-T15-R-20260331-141549-p1-t04-data-quality-scoring-engine-and-api-closure-report.md | 已完成（四维评分引擎实现；API 端点已就绪；27 条测试全通过；后端回归 26/26 通过） |
| M7-T16 | docs/tasks/M7/M7-T16-20260331-160630-p1-t05-frontend-quality-report-page-and-visualization.md | docs/tasks/M7/M7-T16-R-20260331-160630-p1-t05-frontend-quality-report-page-and-visualization-report.md | 已完成（前端质量报告页面与四维评分卡已闭环；typecheck/build 通过；API 契约一致） |
| M7-T17 | docs/tasks/M7/M7-T17-20260331-164748-p1-t06-multi-table-join-and-data-fusion.md | docs/tasks/M7/M7-T17-R-20260331-164748-p1-t06-multi-table-join-and-data-fusion-report.md | 已完成（JoinResult/JoinRequest Schema 实现；DataFusionService 完整；8/8 测试通过；后端回归通过） |
| M7-T18 | docs/tasks/M7/M7-T18-20260331-180428-p1-t07-early-stopping-and-param-templates.md | docs/tasks/M7/M7-T18-R-20260331-180428-p1-t07-early-stopping-and-param-templates-report.md | 已完成（early_stopping_rounds 训练调用生效；模板端点与前端回填已闭环；6/6 专项测试通过） |
| M7-T19 | docs/tasks/M7/M7-T19-20260401-091118-p1-t08-parameter-validation-and-conflict-hints.md | docs/tasks/M7/M7-T19-R-20260401-091118-p1-t08-parameter-validation-and-conflict-hints-report.md | 已完成（前后端参数校验与冲突提示闭环；16/16 专项测试通过；前端门禁通过） |
| M7-T20 | docs/tasks/M7/M7-T20-20260401-100809-p1-t09-concurrent-training-and-queue-visibility.md | docs/tasks/M7/M7-T20-R-20260401-100809-p1-t09-concurrent-training-and-queue-visibility-report.md | 部分通过（配置项/队列字段/前端展示已落地；但真实并发执行、running 生命周期接入、并发 E2E 证据未达标，移至 M7-T21） |
| M7-T21 | docs/tasks/M7/M7-T21-20260401-111155-m7-t20-audit-fixes-real-concurrency-and-queue-evidence-closure.md | 待归档（未发现 M7-T21 汇报文件） | 部分通过（worker 并发与 running 生命周期接入已实现；但汇报文件缺失，Redis 运行时证据未完成，测试存在 2 条事件循环错误，移至 M7-T22） |
| M7-T22 | docs/tasks/M7/M7-T22-20260401-121329-m7-t21-audit-fixes-report-presence-and-runtime-test-stability.md | docs/tasks/M7/M7-T22-R-20260401-121329-m7-t21-audit-fixes-report-presence-and-runtime-test-stability-report.md | 已完成（M7-T21 汇报归档补齐；测试稳定性修复；7 passed/4 skipped；Redis 集成未验证已诚实声明） |
| M7-T23 | docs/tasks/M7/M7-T23-20260401-140002-m7-t21-runtime-redis-concurrency-evidence-closure.md | docs/tasks/M7/M7-T23-R-20260401-143438-redis-runtime-evidence-environment-blocked-report.md | 环境阻断（Redis 不可用；诚实声明已代码验证、未运行时验证；建议停止等待 Redis 环境就绪） |

## 预任务阶段汇报（无独立任务单）

| 建议归档编号 | 汇报单 | 说明 |
|---|---|---|
| M2-PRE-R01 | docs/reports/2026-03-26-task1-2-router-split-contract.md | 早期路由与契约阶段汇报 |
| M2-PRE-R02 | docs/reports/2026-03-26-task3-4-assets-smoke.md | 早期资产冒烟阶段汇报 |
| M2-PRE-R03 | docs/reports/2026-03-27-e2e-verification-quality-closure.md | 早期 E2E 与质量收口汇报 |

## 当前项目位置

- 当前推进到：M7（P1/P2 功能开发阶段）
- 上一个完成的任务：M7-T22（M7-T21 审计修复与测试稳定性）
- 当前任务状态：M7-T23（M7-T21 Redis 运行时并发证据补齐）**环境阻断** - 已提交诚实报告
- 阻断原因：Redis 不可用（localhost:6379 连接被拒绝），无本地 Redis 服务，无 Docker 环境
- 下一步：**停止等待** - 需获取 Redis 环境（Docker/远程实例/本地 Redis 服务）后重新执行 M7-T23
- 停点规则：**勿推进 P1-T10**，直到 M7-T23 获得运行时证据并闭环
