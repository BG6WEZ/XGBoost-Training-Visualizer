# M7-T95 — Phase-5 / Task 5.2 再收口（性能目标达标闭环）

> 任务编号：M7-T95  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T94（已建立性能基线，但 5 / 5 端点 P95 全未达标）  
> 时间戳：20260417-092530

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T94-AUDIT-SUMMARY-20260417-092530.md`
- [ ] 阅读 `docs/tasks/M7/M7-T94-R-20260417-092200-p5-t52-performance-baseline-report.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.2`

---

## 一、本轮目标

本轮**不得进入 Task 5.3**。只允许继续收口 `Task 5.2 性能基线测试`。

注意：

- `T94` 已经完成了“基线测量”
- 但 `Task 5.2` 的真正通过条件不是“测出来”，而是“测出来且全部达标”

因此本轮目标是：

1. 针对当前 5 个端点的高延迟瓶颈做真实优化
2. 在 Docker 全栈环境下重新执行性能基线
3. 让所有端点同时满足计划中的 P95 目标

---

## 二、上一轮阻断事实

以下数据来自 `M7-T94-R`，你必须以此为优化起点：

| 端点 | 当前 P95 | 目标 P95 | 差距 |
|------|-----------|-----------|------|
| `/health` | `2251.78ms` | `< 50ms` | 极大 |
| `/api/auth/login` | `21779.15ms` | `< 500ms` | 极大 |
| `/api/datasets/` | `942.16ms` | `< 200ms` | 明显超标 |
| `/api/experiments/` | `758.84ms` | `< 200ms` | 明显超标 |
| `/api/datasets/upload` | `5411.11ms` | `< 3000ms` | 超标 |

同时已确认：

- `5xx = 0`
- 成功率 `100%`

说明当前主要矛盾不是稳定性，而是**性能目标严重不达标**。

---

## 三、允许修改的范围文件

- `scripts/benchmark.py`
- `apps/api/app/main.py`
- `apps/api/app/routers/health.py`
- `apps/api/app/routers/auth.py`
- `apps/api/app/routers/datasets.py`
- `apps/api/app/routers/experiments.py`
- `apps/api/app/services/auth.py`
- `apps/api/app/database.py`
- `docker/docker-compose.yml`
- 如确有必要，可补充与性能闭环直接相关的最小配置修正
- 本轮新增报告文件：`docs/tasks/M7/M7-T95-R-<timestamp>-p5-t52-performance-target-closure-report.md`

禁止越界到：

- Task 5.3 或后续任务
- 与性能闭环无关的功能开发
- 通过降低并发、降低请求数、放宽目标值来“伪达标”

---

## 四、必须完成的最小工作

### 1) 先定位 5 个端点的主要瓶颈

你必须逐个分析并记录瓶颈来源，至少覆盖：

- `/health` 为什么在 50 并发下远高于 `50ms`
- `/api/auth/login` 的 bcrypt / CPU / 线程池 / worker 数是否为主瓶颈
- `/api/datasets/` 与 `/api/experiments/` 的数据库查询、序列化、连接池是否为主瓶颈
- `/api/datasets/upload` 的文件写入、CSV 解析、元数据提取是否为主瓶颈

要求：

- 报告中必须写明“定位依据”
- 不允许直接跳到“我猜测是某某原因”

### 2) 做真实性能优化

允许但不限于以下方向：

- API 进程 / worker 配置优化
- 连接池配置优化
- bcrypt 计算路径优化，但不得破坏安全语义
- 列表接口查询与序列化优化
- 上传链路中的同步阻塞路径优化
- 健康检查路径上的不必要中间件 / 开销清理

注意：

- 不得删除安全检查来换取性能
- 不得为了基准通过而改弱业务语义
- 不得通过 mock / fake response 冒充真实性能

### 3) 继续使用真实 Docker 全栈执行

必须在 Docker 全栈运行状态下执行：

```bash
docker compose -f docker/docker-compose.yml ps
python scripts/benchmark.py --base-url http://localhost:8000
```

要求：

- 报告中提交真实命令
- 若中间执行多次，必须区分“中间尝试”和“最终验收依据”

### 4) 基准脚本本身不得回避验收条件

`scripts/benchmark.py` 允许改进，但不得通过以下方式造假：

- 降低端点并发数
- 降低每并发槽请求数且不在报告中说明
- 修改目标阈值
- 把未达标结果仍返回 `exit code 0`

如需改脚本，只允许：

- 提升统计准确性
- 提升输出可读性
- 修复真实 bug

### 5) 报告必须提交“优化前 vs 优化后”对比

至少包含：

- `T94` 基线值
- 本轮最终值
- 是否达标
- 优化点与对应收益

不能只给最终一组数字。

---

## 五、通过条件（全部满足才算通过）

- [ ] 当前 5 个端点全部满足计划中的 P95 目标
- [ ] 全程无 `5xx` 错误
- [ ] `scripts/benchmark.py` 最终执行返回 `exit code 0`
- [ ] 报告包含优化前后对比
- [ ] 报告明确写出最终验收依据是哪一次执行
- [ ] 正式报告文件与本轮编号一致
- [ ] 未越界推进到 Task 5.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T95-R-<timestamp>-p5-t52-performance-target-closure-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 性能瓶颈定位结果
4. 实施的优化项
5. Docker 全栈运行状态
6. 最终 benchmark 命令与退出码
7. 5 个端点“优化前 vs 优化后”对比表
8. 是否出现 `5xx` / 超时 / 认证异常
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 5.2 验收

---

## 七、明确禁止

- 不得把“基线已建立”表述成“Task 5.2 已通过”
- 不得在 5 / 5 端点未达标时提交验收
- 不得通过放宽阈值、降低并发或改退出码来规避失败
- 不得提前进入 Task 5.3
