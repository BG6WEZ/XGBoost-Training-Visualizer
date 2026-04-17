# M7-T85 — Phase-4 / Task 4.3 健康检查与就绪探针完善

> 任务编号：M7-T85  
> 阶段：Phase-4 / Task 4.3  
> 前置：M7-T84（Task 4.2 验收通过）  
> 时间戳：20260416-173120

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T84-AUDIT-SUMMARY-20260416-173120.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.3`

---

## 一、本轮目标

进入 `Phase-4 / Task 4.3 — 健康检查与就绪探针完善`，目标是规范 API 的 liveness / readiness 语义，并补充管理端详细状态端点。

---

## 二、允许修改的范围文件

- `apps/api/app/routers/health.py`
- 如确有必要，可补充与本轮测试直接相关的测试文件
- 本轮新增报告文件：`docs/tasks/M7/M7-T85-R-<timestamp>-p4-t43-health-readiness-probes-report.md`

禁止越界到：

- 其他业务路由大改
- 日志系统改造（属于 Task 4.4）
- Task 4.4 或后续任务

---

## 三、必须完成的最小工作

### 1) 规范 `/health` 为 liveness

要求：

- `/health` 仅返回简单存活状态
- 不检查数据库、Redis、存储等外部依赖
- 目标响应应接近：

```json
{"status": "ok"}
```

可附最少量额外字段，但不得依赖外部服务状态。

### 2) 规范 `/ready` 为 readiness

要求：

- 检查数据库连接可用
- 检查存储服务可写 / 可用
- 检查 Redis 连接（允许降级为 warning）
- 返回各组件状态明细

要求：

- 当关键依赖不可用时，应返回非 ready 状态
- Redis 可降级，但数据库与存储不可降级

### 3) 新增 `/health/details`

要求：

- 作为管理端详细状态端点
- 返回各组件详细状态
- **仅管理员可访问**

若项目已有认证依赖与管理员判断逻辑，需复用现有实现，不得自造一套权限体系。

### 4) 对齐容器探针语义

要求：

- Docker healthcheck 使用 `/health`
- K8s readiness 使用 `/ready`

本轮至少在报告中明确说明这一语义映射；若仓库中已有相关配置可顺手引用，但不强制越界改其它文件。

### 5) 必须完成测试

至少满足计划要求中的测试：

- `test_health.py::test_liveness_always_ok`
- `test_health.py::test_readiness_checks_db`
- `test_health.py::test_details_requires_admin`

如果当前不存在对应测试文件或测试名，需要补齐到等价覆盖。

---

## 四、通过条件（全部满足才算通过）

- [ ] `/health` 不依赖任何外部服务
- [ ] `/ready` 返回各组件状态
- [ ] `/health/details` 已实现且仅管理员可访问
- [ ] 相关测试通过
- [ ] 产出与本轮编号一致的 `M7-T85-R-...` 报告
- [ ] 未越界推进到 Task 4.4 或后续任务

---

## 五、汇报要求

完成后提交：

- `M7-T85-R-<timestamp>-p4-t43-health-readiness-probes-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. `/health` 如何改为 liveness
4. `/ready` 如何返回各组件状态
5. `/health/details` 的权限控制方式
6. 实际执行的测试命令
7. 测试结果
8. 已验证通过项
9. 未验证部分
10. 风险与限制
11. 是否建议提交 Task 4.3 验收

---

## 六、明确禁止

- 不得让 `/health` 继续依赖数据库或其它外部服务
- 不得让 `/health/details` 无权限保护直接暴露
- 不得提前进入 Task 4.4
