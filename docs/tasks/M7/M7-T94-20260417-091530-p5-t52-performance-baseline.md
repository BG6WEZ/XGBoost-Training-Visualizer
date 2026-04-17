# M7-T94 — Phase-5 / Task 5.2 性能基线测试

> 任务编号：M7-T94  
> 阶段：Phase-5 / Task 5.2  
> 前置：M7-T93（Task 5.1 验收通过）  
> 时间戳：20260417-091530

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T93-AUDIT-SUMMARY-20260417-091530.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.2`

---

## 一、本轮目标

进入 `Phase-5 / Task 5.2 — 性能基线测试`。本轮目标不是优化性能，也不是继续修业务功能，而是基于当前已经通过 `Task 5.1` 的 Docker 全栈环境，产出一份**真实、可复现、可比较**的性能基线报告。

本轮必须回答三个问题：

1. 当前关键端点的 P95 延迟分别是多少
2. 当前基线下是否出现 `5xx` 错误
3. 哪些端点满足计划门槛，哪些未满足

---

## 二、允许修改的范围文件

- `scripts/benchmark.py`（新增）
- 如确有必要，可补充与性能测试直接相关的最小辅助文件
- 本轮新增报告文件：`docs/tasks/M7/M7-T94-R-<timestamp>-p5-t52-performance-baseline-report.md`

禁止越界到：

- Task 5.3 或后续任务
- 与性能测试无关的业务逻辑重构
- 为了“跑出好看结果”而临时改宽验收口径

---

## 三、基线测试对象

必须覆盖以下 5 个端点，并按总计划中的并发目标执行：

| 端点 | 方法 | 并发数 | 目标 P95 |
|------|------|--------|-----------|
| `/health` | `GET` | 50 | `< 50ms` |
| `/api/auth/login` | `POST` | 10 | `< 500ms` |
| `/api/datasets/` | `GET` | 20 | `< 200ms` |
| `/api/experiments/` | `GET` | 20 | `< 200ms` |
| `/api/datasets/upload`（1MB CSV） | `POST` | 5 | `< 3s` |

---

## 四、必须完成的最小工作

### 1) 保持 Docker 全栈运行并确认就绪

在性能测试前，必须先确认：

- Docker 全栈仍在运行
- `http://localhost:8000/ready` 返回 `200`

至少提交：

```bash
docker compose -f docker/docker-compose.yml ps
```

以及 `/ready` 的检查结果。

### 2) 实现性能测试脚本

必须新增：

```bash
scripts/benchmark.py
```

要求：

- 使用 Python 实现，优先 `httpx`
- 能独立运行
- 支持对指定端点执行并发请求
- 输出每个端点的：
  - 总请求数
  - 成功数
  - 失败数
  - 错误率
  - 平均延迟
  - P95 延迟
  - 最大延迟
- 最终给出整体汇总

### 3) 准备登录态与测试数据

你必须为以下端点准备真实可用的测试前提：

- `POST /api/auth/login`
- `GET /api/datasets/`
- `GET /api/experiments/`
- `POST /api/datasets/upload`

要求：

- 不允许用伪造响应
- 不允许跳过认证直接写“性能结果”
- 上传测试必须使用真实约 `1MB` CSV 文件

### 4) 执行基线测试

至少执行一次完整基线：

```bash
python scripts/benchmark.py --base-url http://localhost:8000
```

如果第一次执行失败，可以修复后重跑，但报告必须明确区分：

- 初次执行
- 中间失败
- 最终验收依据

### 5) 统计 `5xx` 与异常

报告必须单独列出：

- 是否出现 `5xx`
- 是否出现连接超时 / 读超时 / 认证失败
- 哪些异常属于环境噪声，哪些属于真实性能问题

### 6) 输出端点级结论

每个端点都必须单独判断：

- 是否满足目标 P95
- 是否存在 5xx
- 是否建议后续优化

不能只给一份混合平均值报告。

---

## 五、通过条件（全部满足才算通过）

- [ ] 已新增 `scripts/benchmark.py`
- [ ] 基于真实运行中的 Docker 全栈执行性能测试
- [ ] 覆盖 5 个指定端点
- [ ] 报告给出每个端点的 P95 延迟
- [ ] 报告明确说明是否出现 `5xx`
- [ ] 所有端点满足计划中的 P95 目标
- [ ] 正式报告文件与本轮编号一致
- [ ] 未越界推进到 Task 5.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T94-R-<timestamp>-p5-t52-performance-baseline-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 性能测试前的环境状态
4. 基准脚本实现说明
5. 5 个端点的测试参数
6. 5 个端点的结果表（含 P95）
7. 是否出现 `5xx` / 超时 / 认证异常
8. 已验证通过项
9. 未验证部分
10. 风险与限制
11. 是否建议提交 Task 5.2 验收

---

## 七、明确禁止

- 不得只测单个端点后声称“性能基线已完成”
- 不得省略 `P95`，只给平均值
- 不得在出现 `5xx` 时仍写“全部满足基线”
- 不得用本地开发模式替代 Docker 全栈结果
- 不得直接跳到 Task 5.3
