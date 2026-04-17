# M7-T90 — Phase-4 / Task 4.4 再收口（真全量测试或诚实收缩结论）

> 任务编号：M7-T90  
> 阶段：Phase-4 / Task 4.4 Re-open  
> 前置：M7-T89（审计不通过）  
> 时间戳：20260416-185200

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T89-AUDIT-SUMMARY-20260416-185200.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.4`

---

## 一、本轮目标

本轮**不得进入 Phase-5**。只允许继续收口 **Task 4.4 结构化日志**，当前唯一核心问题是：

- 需要拿到**真正不带排除项的全量测试通过证据**
- 或诚实承认当前做不到，并停止宣称“全量测试通过”

---

## 二、允许修改的范围文件

- `apps/api/app/logging_config.py`
- `apps/api/app/main.py`
- `apps/worker/app/logging_config.py`
- `apps/worker/app/main.py`
- 如确有必要，可补充少量与测试直接相关的修复
- 本轮新增报告文件：`docs/tasks/M7/M7-T90-R-<timestamp>-p4-t44-true-full-test-run-or-honest-scope-down-report.md`

禁止越界到：

- Phase-5 或后续任务
- 与当前测试收口无关的大范围业务改动

---

## 三、上一轮未通过的核心问题

你必须逐项消除以下问题：

1. **测试命令带有 `--ignore`**
   - 当前不是完整的全量测试

2. **报告把“排除部分测试后的通过”写成“真正的全量测试通过”**
   - 这一表述与计划要求不一致

---

## 四、必须完成的最小工作

### 1) 优先尝试真正的全量测试

首选方案：

```bash
cd apps/api
python -m pytest tests/ -v
```

要求：

- 不带 `--ignore`
- 不跳过关键测试
- 提交真实命令与真实输出

### 2) 若全量测试失败，必须如实修复或如实汇报

你可以：

- 修复失败测试后重新执行
- 或如实写明当前仍未达到“全量测试通过”

但不得：

- 再用 `--ignore`
- 再把子集通过写成“全量通过”

### 3) 保持当前已完成项不回退

本轮不能把已完成的能力弄丢：

- request_id 稳定注入普通子 logger
- JSON 合法输出
- Worker 最小日志验证

### 4) 报告必须精确描述验证范围

报告中必须明确：

- 全量测试是否真的执行
- 若执行，执行了哪些命令
- 若未执行成功，失败点是什么

### 5) 只有在真正满足条件时，才能写“建议提交 Task 4.4 验收”

若本轮仍不是不带排除项的全量测试通过，则：

- 不得建议提交 `Task 4.4` 验收

---

## 五、通过条件（全部满足才算通过）

- [ ] `request_id` 稳定注入到普通子 logger 的日志中
- [ ] `LOG_FORMAT=json` 时业务日志为合法 JSON 且包含 `request_id`
- [ ] API 与 Worker 都接入新日志配置
- [ ] 已提交 Worker 最小日志验证证据
- [ ] 已提交**不带排除项**的真正全量测试通过证据
- [ ] 产出与本轮编号一致的 `M7-T90-R-...` 报告
- [ ] 未越界推进到 Phase-5 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T90-R-<timestamp>-p4-t44-true-full-test-run-or-honest-scope-down-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 全量测试执行命令
4. 全量测试结果
5. 若有失败，失败项与修复情况
6. Worker 最小验证方式
7. Worker 日志真实样例
8. API 日志真实样例
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 4.4 验收

---

## 七、明确禁止

- 不得继续用 `--ignore` 后再写“全量测试通过”
- 不得用“之前任务已验证过”替代当前通过条件
- 不得提前进入 Phase-5
