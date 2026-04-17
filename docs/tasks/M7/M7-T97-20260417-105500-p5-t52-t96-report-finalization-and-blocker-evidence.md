# M7-T97 — Phase-5 / Task 5.2 再收口（T96 正式报告补齐与阻断证据固化）

> 任务编号：M7-T97  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T96（诚实结论方向正确，但 `M7-T96-R` 正式报告文件缺失）  
> 时间戳：20260417-105500

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T96-AUDIT-SUMMARY-20260417-105500.md`
- [ ] 阅读 `docs/tasks/M7/M7-T96-20260417-100730-p5-t52-native-linux-benchmark-validation-or-honest-scope-down.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.2`

---

## 一、本轮目标

本轮**不得进入 Task 5.3**。只允许继续收口 `Task 5.2`，并且本轮重点不是再做新的性能优化，而是把 `T96` 已得出的诚实结论与环境阻断证据，按正式报告格式完整固化。

当前阻断点只有一个核心事实：

- `M7-T96-R-...` 正式报告文件不存在

因此本轮目标是：

1. 产出与 `T96` 编号一致的正式报告
2. 把环境排查证据完整落盘
3. 明确写出本轮采用的是 `结论 B`
4. 明确 `Task 5.2` 仍不通过

---

## 二、允许修改的范围文件

- 本轮新增报告文件：`docs/tasks/M7/M7-T96-R-<timestamp>-p5-t52-native-linux-benchmark-validation-or-honest-scope-down-report.md`
- 如确有必要，可补充极少量与证据整理直接相关的说明文件

禁止越界到：

- Task 5.3 或后续任务
- 与报告固化无关的代码重构
- 重新包装 `Task 5.2` 为“已通过”

---

## 三、必须完成的最小工作

### 1) 产出 `M7-T96-R` 正式报告

必须在仓库中新增：

- `docs/tasks/M7/M7-T96-R-<timestamp>-p5-t52-native-linux-benchmark-validation-or-honest-scope-down-report.md`

注意：

- 必须是 `T96-R`
- 不能继续只在聊天里汇报
- 不能用 `T95-R` 或其他旧报告替代

### 2) 把环境排查证据完整写入报告

报告必须逐项固化你已汇报的环境排查事实，至少包括：

- Windows 宿主机不是 Linux
- `docker-desktop` WSL distro 无法提供可用 shell
- Docker 容器内内核仍为 `microsoft-standard-WSL2`
- GitHub Actions / Linux CI 路径为何未能取得有效复核证据

要求：

- 尽量附命令或原始输出片段
- 若某项只有现象没有命令，也必须写清“证据形式”和限制

### 3) 明确写出本轮采用 `结论 B`

报告必须明确声明：

- **本轮结论：B**
- **无法取得原生 Linux 环境复核证据**
- **当前不能把“WSL2 是主因”写成已证实结论**

### 4) 保持 Task 5.2 的诚实结论

报告必须明确写出：

- `Task 5.2` 仍不通过
- 不得进入 `Task 5.3`

不能再出现：

- “虽然无 Linux 证据，但建议提交 Task 5.2 验收”

这种与任务单冲突的表述。

### 5) 补齐可追溯结构

报告至少要包含：

1. 已完成任务编号
2. 环境排查范围
3. 各环境状态与结论
4. 取得 / 未取得的证据
5. 本轮采用的结论类型（A / B）
6. 对 `Task 5.2` 的最终判断
7. 风险与限制
8. 是否建议提交 `Task 5.2` 验收

---

## 四、通过条件（全部满足才算通过）

- [ ] 已产出 `M7-T96-R-...` 正式报告文件
- [ ] 报告完整记录环境排查证据
- [ ] 报告明确采用 `结论 B`
- [ ] 报告明确写出 `Task 5.2` 仍不通过
- [ ] 报告未越界推进到 `Task 5.3`
- [ ] 正式报告与本轮编号一致

---

## 五、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T96-R-<timestamp>-p5-t52-native-linux-benchmark-validation-or-honest-scope-down-report.md`

汇报必须包含：

1. 已完成任务编号
2. 环境排查范围
3. Windows / WSL2 / Docker / CI 各自状态
4. 环境证据与限制
5. 本轮结论（A 或 B）
6. 对 `Task 5.2` 的最终判断
7. 风险与限制
8. 是否建议提交 Task 5.2 验收

---

## 六、明确禁止

- 不得继续只做聊天汇报而不落正式报告
- 不得把口头结论当作正式交付物
- 不得在没有 `M7-T96-R` 的情况下宣称 `T96` 已验收
- 不得提前进入 `Task 5.3`
