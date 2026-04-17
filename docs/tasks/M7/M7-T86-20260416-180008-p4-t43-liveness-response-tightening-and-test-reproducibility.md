# M7-T86 — Phase-4 / Task 4.3 再收口（Liveness 收敛与测试可复现）

> 任务编号：M7-T86  
> 阶段：Phase-4 / Task 4.3 Re-open  
> 前置：M7-T85（审计不通过）  
> 时间戳：20260416-180008

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T85-AUDIT-SUMMARY-20260416-180008.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.3`

---

## 一、本轮目标

本轮**不得进入 Task 4.4**。只允许继续收口 **Task 4.3 健康检查与就绪探针完善**，重点修复两类问题：

1. **`/health` 返回体未严格收敛**
2. **测试结果缺少当前环境下的可复现性证据**

---

## 二、允许修改的范围文件

- `apps/api/app/routers/health.py`
- `apps/api/tests/test_health.py`
- 如确有必要，可补充极少量与测试环境说明直接相关的文档
- 本轮新增报告文件：`docs/tasks/M7/M7-T86-R-<timestamp>-p4-t43-liveness-response-tightening-and-test-reproducibility-report.md`

禁止越界到：

- 其他业务路由大改
- 日志系统改造（属于 Task 4.4）
- Task 4.4 或后续任务

---

## 三、上一轮未通过的核心问题

你必须逐项消除以下问题：

1. **`/health` 未严格满足原计划要求**
   - 原计划要求：仅返回 `{"status": "ok"}`
   - 当前仍返回额外字段 `service`、`timestamp`

2. **测试结果在当前环境不可复现**
   - 报告声称 11 个测试通过
   - 当前实际执行在收集阶段即因缺依赖失败

3. **报告未清楚说明测试运行环境**
   - 未交代依赖前提
   - 未说明使用的 Python 环境 / 虚拟环境

---

## 四、必须完成的最小工作

### 1) 将 `/health` 严格收敛为最小 liveness 响应

要求：

- `/health` 仅返回：

```json
{"status": "ok"}
```

- 不附加 `service`
- 不附加 `timestamp`
- 不检查任何外部依赖

### 2) 调整测试以匹配最终语义

要求：

- `test_health.py` 中与 `/health` 相关断言需匹配最终最小返回体
- 仍要证明 `/health` 不依赖数据库或其他外部服务

### 3) 确保测试在当前可复现环境中可执行

你必须明确采用以下一种方式：

#### 方案 A：补齐本项目 API 测试运行依赖

- 让当前环境满足 `tests/test_health.py` 的导入与执行要求
- 重新运行测试并给出真实输出

#### 方案 B：明确使用受控虚拟环境

- 明确激活方式
- 明确依赖安装方式
- 在该环境中运行测试并提交真实输出

要求：

- 不得只写“测试通过”而无环境说明
- 不得再出现当前环境下无法导入的情况却仍宣称已完成

### 4) 报告必须明确测试运行环境

至少写清：

- Python 版本
- 是否使用虚拟环境
- 依赖安装方式
- 实际测试命令

### 5) 必须提交真实测试输出

至少提交：

```bash
cd apps/api
python -m pytest tests/test_health.py -v
```

要求：

- 报告中附真实输出
- 输出必须来自可复现环境
- 若使用虚拟环境，命令前置步骤必须写清楚

---

## 五、通过条件（全部满足才算通过）

- [ ] `/health` 仅返回 `{"status": "ok"}`
- [ ] `/ready` 返回各组件状态
- [ ] `/health/details` 已实现且仅管理员可访问
- [ ] `tests/test_health.py` 在可说明、可复现的环境中通过
- [ ] 报告明确测试运行环境与依赖前提
- [ ] 产出与本轮编号一致的 `M7-T86-R-...` 报告
- [ ] 未越界推进到 Task 4.4 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T86-R-<timestamp>-p4-t43-liveness-response-tightening-and-test-reproducibility-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. `/health` 最终返回体
4. `/ready` 与 `/health/details` 的最终行为
5. 测试运行环境说明
6. 依赖安装 / 激活方式
7. 实际执行的测试命令
8. 完整测试结果
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 4.3 验收

---

## 七、明确禁止

- 不得让 `/health` 继续返回额外字段
- 不得继续提交在当前环境不可复现的“测试已通过”结论
- 不得提前进入 Task 4.4
