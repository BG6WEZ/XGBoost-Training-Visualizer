# M7-T96 — Phase-5 / Task 5.2 再收口（原生 Linux 复核或诚实收缩）

> 任务编号：M7-T96  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T95（已完成真实性能优化，但当前仅 1 / 5 端点达标，且 WSL2 环境归因尚未闭环）  
> 时间戳：20260417-100730

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T95-AUDIT-SUMMARY-20260417-100730.md`
- [ ] 阅读 `docs/tasks/M7/M7-T95-R-20260417-100449-p5-t52-performance-target-closure-report.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.2`

---

## 一、本轮目标

本轮**不得进入 Task 5.3**。只允许继续收口 `Task 5.2`。

当前状态已经很明确：

- 应用层已做出一轮真实性能优化
- 结果从 `0 / 5` 达标提升到 `1 / 5`
- 但仍未满足 `Task 5.2` 的计划门槛
- 当前报告把主要原因归因为 `WSL2`

因此本轮唯一合理目标是：

1. 用**原生 Linux 环境**复核 benchmark 结果
2. 验证“未达标主因是 WSL2 环境”这一判断是否成立
3. 基于复核结果，决定 `Task 5.2` 是通过还是继续失败

---

## 二、上一轮阻断事实

来自 `M7-T95-R` 的最终数据：

| 端点 | 当前 P95 | 目标 P95 | 结果 |
|------|-----------|-----------|------|
| `/health` | `2270ms` | `< 50ms` | FAIL |
| `/api/auth/login` | `4384ms` | `< 500ms` | FAIL |
| `/api/datasets/` | `717ms` | `< 200ms` | FAIL |
| `/api/experiments/` | `607ms` | `< 200ms` | FAIL |
| `/api/datasets/upload` | `1896ms` | `< 3000ms` | PASS |

同时成立：

- `5xx = 0`
- 成功率 `100%`
- `benchmark.py` 退出码 `1`

这意味着：

- 当前 `Task 5.2` 仍然不能通过
- 但阻断点已经集中到“目标线未达到 + 环境归因未闭环”

---

## 三、允许修改的范围文件

- `scripts/benchmark.py`
- 与 Linux benchmark 执行直接相关的最小辅助脚本或配置
- 本轮新增报告文件：`docs/tasks/M7/M7-T96-R-<timestamp>-p5-t52-native-linux-benchmark-validation-or-honest-scope-down-report.md`

禁止越界到：

- Task 5.3 或后续任务
- 与 benchmark 复核无关的业务逻辑重构
- 通过放宽阈值、降低并发、修改目标值来规避失败

---

## 四、必须完成的最小工作

### 1) 在原生 Linux 环境执行同口径 benchmark

你必须想办法在**原生 Linux** 环境执行同一套 benchmark。可接受方式包括：

- Linux 物理机
- Linux 云主机
- Linux CI runner
- 其他明确可证明为原生 Linux 的执行环境

不接受：

- Windows 宿主机 + Docker Desktop + WSL2 再跑一遍冒充 Linux 复核

### 2) 复用相同口径，不得修改目标线

必须继续沿用 `Task 5.2` 的原始要求：

| 端点 | 并发数 | 目标 P95 |
|------|--------|-----------|
| `GET /health` | 50 | `< 50ms` |
| `POST /api/auth/login` | 10 | `< 500ms` |
| `GET /api/datasets/` | 20 | `< 200ms` |
| `GET /api/experiments/` | 20 | `< 200ms` |
| `POST /api/datasets/upload` (1MB CSV) | 5 | `< 3s` |

要求：

- 不得改低并发
- 不得改高目标值
- 不得改脚本退出码语义

### 3) 提交环境证明

报告必须提交足以证明“这是原生 Linux”的证据，例如：

- `uname -a`
- `/etc/os-release`
- CI runner 类型
- Docker Engine 所在环境说明

### 4) 提交 WSL2 vs Linux 对照结果

至少需要一张对照表：

- `T95`（WSL2）结果
- `T96`（Linux）结果
- 差值
- 是否达标

### 5) 诚实给出最终结论

本轮只允许两种结论：

#### 结论 A：Linux 复核后全部达标

若原生 Linux 复核结果满足：

- 5 个端点全部满足 P95 目标
- 无 `5xx`
- benchmark 退出码 `0`

则可据此申请 `Task 5.2` 通过，并明确写明：

- 当前计划门槛是在原生 Linux 环境下成立
- WSL2 结果仅作为开发机参考，不作为最终验收依据

#### 结论 B：Linux 复核后仍未全部达标，或无法取得 Linux 复核证据

若出现以下任一情况：

- Linux 复核后仍未全部达标
- 无法取得原生 Linux 环境
- 环境证据不足

则必须诚实结论：

- `Task 5.2` 仍不通过
- 当前不能把“WSL2 是主因”写成已证实结论

---

## 五、通过条件（全部满足才算通过）

- [ ] 已提交原生 Linux 环境证明
- [ ] 已在原生 Linux 环境执行同口径 benchmark
- [ ] 5 个端点全部满足计划中的 P95 目标
- [ ] 无 `5xx` 错误
- [ ] `scripts/benchmark.py` 最终执行返回 `exit code 0`
- [ ] 报告包含 WSL2 vs Linux 对照
- [ ] 正式报告文件与本轮编号一致
- [ ] 未越界推进到 Task 5.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T96-R-<timestamp>-p5-t52-native-linux-benchmark-validation-or-honest-scope-down-report.md`

汇报必须包含：

1. 已完成任务编号
2. Linux 环境证明
3. benchmark 执行命令与退出码
4. 5 个端点的 Linux 结果表
5. `T95 (WSL2)` vs `T96 (Linux)` 对照表
6. 是否出现 `5xx` / 超时 / 认证异常
7. 已验证通过项
8. 未验证部分
9. 风险与限制
10. 是否建议提交 Task 5.2 验收

---

## 七、明确禁止

- 不得把“猜测 WSL2 是主因”写成“已经证实”
- 不得在没有 Linux 环境证明时提交 Linux 结论
- 不得通过修改 benchmark 口径来制造通过
- 不得提前进入 Task 5.3
