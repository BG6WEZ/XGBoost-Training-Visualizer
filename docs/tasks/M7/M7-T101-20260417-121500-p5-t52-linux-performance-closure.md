# M7-T101 — Phase-5 / Task 5.2 再收口（Linux 性能目标达标闭环）

> 任务编号：M7-T101  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T100（Linux runner 已成功跑出完整 benchmark 输出，但仅 1/5 端点达标）  
> 时间戳：20260417-121500

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T100-R-20260417-121000-p5-t52-linux-runner-schema-init-and-benchmark-rerun-report.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.2`
- [ ] 查看 Run `24554310231`（Linux benchmark #2）的完整日志

---

## 一、本轮目标

本轮**不得进入 Task 5.3**。只允许继续收口 `Task 5.2`。

当前已确认：

- Linux runner 可稳定执行 benchmark
- schema 初始化阻断已解除
- 当前真实问题是性能未达标，而非环境不可复现

因此本轮目标是：

1. 针对 Linux 输出中 4 个未达标端点做真实性能优化
2. 重新触发 Linux benchmark
3. 把结果推到 `5/5` 全部达标

---

## 二、上一轮基线（Linux runner）

来自 run `24554310231`：

| 端点 | P95(ms) | 目标(ms) | 状态 |
|------|---------|----------|------|
| `/health` | 2392.38 | `< 50` | FAIL |
| `/api/auth/login` | 6911.86 | `< 500` | FAIL |
| `/api/datasets/` | 666.97 | `< 200` | FAIL |
| `/api/experiments/` | 568.58 | `< 200` | FAIL |
| `/api/datasets/upload` | 2839.09 | `< 3000` | PASS |

补充：

- 5xx：`0`
- 成功率：`100%`
- 失败原因：达标门槛未满足（脚本退出码 1）

---

## 三、允许修改的范围文件

- `scripts/benchmark.py`（仅限统计准确性或测试前置改进，不得改宽验收口径）
- `apps/api/app/routers/health.py`
- `apps/api/app/routers/auth.py`
- `apps/api/app/routers/datasets.py`
- `apps/api/app/routers/experiments.py`
- `apps/api/app/services/auth.py`
- `apps/api/app/database.py`
- `apps/api/app/main.py`
- `.github/workflows/benchmark-linux.yml`
- `docker/docker-compose.yml`
- 本轮新增报告：`docs/tasks/M7/M7-T101-R-<timestamp>-p5-t52-linux-performance-closure-report.md`

禁止越界到：

- Task 5.3 或后续任务
- 修改 `Task 5.2` 的目标阈值
- 降低 benchmark 并发参数来“伪达标”

---

## 四、必须完成的最小工作

### 1) 逐端点定位性能瓶颈（必须有证据）

至少对以下 4 个端点提交定位依据：

- `/health`（当前 P95 远高于目标）
- `/api/auth/login`
- `/api/datasets/`
- `/api/experiments/`

定位依据必须来自真实日志、代码路径或可复现压测观测，不能只写“猜测”。

### 2) 实施真实性能优化

优化方向可包括但不限于：

- `uvicorn` worker 与 DB pool 配置协同
- 登录路径的密码校验与查询开销
- 列表接口 ORM 查询 / 序列化开销
- 健康检查路径中的不必要阻塞

要求：

- 不降低安全语义
- 不删除关键校验
- 不通过 mock 或跳过逻辑制造“通过”

### 3) 重新触发 Linux benchmark

必须在 GitHub Actions `ubuntu-latest` 上触发：

- `.github/workflows/benchmark-linux.yml`

并提交：

- 新 run URL
- 新 run ID
- 最终状态（success / failed）

### 4) 提交完整 benchmark 结果

若运行成功：

- 提交 5 端点结果表（P95、目标、是否达标）
- 提交 5xx、成功率、退出码

若仍失败：

- 提交失败步骤、原始错误
- 对比 `24554310231` 的变化
- 明确指出当前仍未达标的端点和差距

### 5) 保持 Task 5.2 原始口径

必须沿用：

| 端点 | 并发数 | 目标 P95 |
|------|--------|----------|
| `GET /health` | 50 | `< 50ms` |
| `POST /api/auth/login` | 10 | `< 500ms` |
| `GET /api/datasets/` | 20 | `< 200ms` |
| `GET /api/experiments/` | 20 | `< 200ms` |
| `POST /api/datasets/upload` (1MB CSV) | 5 | `< 3s` |

---

## 五、通过条件（全部满足才算通过）

- [ ] 已提交 4 个未达标端点的瓶颈定位证据
- [ ] 已实施并说明对应优化项
- [ ] 已重新触发 Linux benchmark（新 run 证据齐全）
- [ ] 5 个端点全部满足 P95 目标
- [ ] 无 5xx 错误
- [ ] benchmark 退出码为 0
- [ ] 正式报告文件与本轮编号一致
- [ ] 未越界推进到 Task 5.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T101-R-<timestamp>-p5-t52-linux-performance-closure-report.md`

汇报必须包含：

1. 已完成任务编号
2. 瓶颈定位证据
3. 修改文件清单
4. 优化项与收益映射
5. 新 run URL / run ID / 最终状态
6. benchmark 原始输出
7. 5 端点结果表
8. 5xx / 成功率 / 退出码
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 5.2 验收

---

## 七、明确禁止

- 不得把“跑通 workflow”表述成“性能达标”
- 不得用降低并发方式换取达标
- 不得改动目标阈值或脚本通过语义
- 不得提前进入 Task 5.3
