# M7-T100 — Phase-5 / Task 5.2 再收口（Linux Runner Schema 初始化与 Benchmark 重跑）

> 任务编号：M7-T100  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T99（已成功触发 GitHub Actions Linux runner，但 benchmark 在 schema 未就绪时失败）  
> 时间戳：20260417-114600

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T99-R-20260417-113500-p5-t52-user-side-linux-benchmark-execution-handoff-report.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.2`
- [ ] 查看 GitHub Actions 运行：`https://github.com/BG6WEZ/XGBoost-Training-Visualizer/actions/runs/24552029858`

---

## 一、本轮目标

本轮**不得进入 Task 5.3**。只允许继续收口 `Task 5.2`。

当前已确认的真实状态：

- GitHub Actions `ubuntu-latest` runner 已成功触发
- Linux runner 不是阻断点
- 当前阻断点已经收敛为：
  - benchmark 执行前数据库 schema / 初始化步骤未完成
  - 导致 `Run benchmark` 步骤访问 `/api/experiments/` 时报错
  - 页面可见错误线索指向 SQLAlchemy `f405`

因此本轮唯一目标是：

1. 在 Linux runner workflow 中补齐数据库迁移 / 初始化前置步骤
2. 重新触发 `benchmark-linux.yml`
3. 取得一份真正完成的 Linux benchmark 结果
4. 再据此继续判断 `Task 5.2`

---

## 二、上一轮失败事实

来自 GitHub Actions run：

- Run URL: `https://github.com/BG6WEZ/XGBoost-Training-Visualizer/actions/runs/24552029858`
- Run ID: `24552029858`
- Workflow: `Performance Benchmark (Linux)`
- 关联提交：`699361a`
- 最终状态：`failed`

失败位置：

- Job: `Performance Benchmark on Ubuntu`
- Step: `Run benchmark`
- Command:

```bash
python scripts/benchmark.py --base-url http://localhost:8000
```

当前可见根因：

- Docker Compose 已启动服务
- 但 benchmark 运行前数据库表尚未准备好
- `/api/experiments/` 链路在 schema 缺失时失败

---

## 三、允许修改的范围文件

- `.github/workflows/benchmark-linux.yml`
- 与 Linux benchmark 前置初始化直接相关的最小脚本 / 配置
- 如确有必要，可调整 Docker Compose 启动后的等待 / 健康检查 / 初始化顺序
- 本轮新增报告文件：`docs/tasks/M7/M7-T100-R-<timestamp>-p5-t52-linux-runner-schema-init-and-benchmark-rerun-report.md`

禁止越界到：

- Task 5.3 或后续任务
- 与 benchmark 初始化无关的业务功能开发
- 修改 `benchmark.py` 的目标阈值、并发数或通过语义

---

## 四、必须完成的最小工作

### 1) 明确 schema 未就绪的真实原因

你必须先定位到底缺了什么前置动作，至少回答：

- 是缺 Alembic migration
- 还是缺 `Base.metadata.create_all`
- 还是缺 admin / seed / workspace 初始化
- 还是 API readiness 与 schema readiness 语义不一致

要求：

- 在报告中写出定位依据
- 不允许只写“怀疑是 migration 问题”

### 2) 在 Linux workflow 中补齐前置初始化

你必须让 `.github/workflows/benchmark-linux.yml` 在执行 benchmark 前完成 schema 准备。

允许的手段包括但不限于：

- 执行 Alembic migration
- 显式运行初始化脚本
- 在 API 启动前完成 DB schema 创建
- 增加对 schema ready 的等待与验证

要求：

- 必须是真实修复，不得靠重试掩盖
- 不得把 benchmark 的失败接口从统计中移除

### 3) 重新触发 Linux benchmark

修复后必须再次在 GitHub Actions `ubuntu-latest` 上执行：

- `.github/workflows/benchmark-linux.yml`

报告必须提供：

- 新 run URL
- 新 run ID
- 最终状态

### 4) 提交 benchmark 完整结果

若运行成功，必须提交：

- benchmark 原始输出
- 退出码
- 5 个端点结果表
- 是否出现 `5xx` / 超时 / 认证异常

若运行仍失败，必须提交：

- 新的失败步骤
- 原始错误信息
- 与 `24552029858` 的差异

### 5) 保持 `Task 5.2` 原始口径不变

仍然必须使用：

| 端点 | 并发数 | 目标 P95 |
|------|--------|-----------|
| `GET /health` | 50 | `< 50ms` |
| `POST /api/auth/login` | 10 | `< 500ms` |
| `GET /api/datasets/` | 20 | `< 200ms` |
| `GET /api/experiments/` | 20 | `< 200ms` |
| `POST /api/datasets/upload` (1MB CSV) | 5 | `< 3s` |

不得：

- 改低并发
- 改高目标值
- 修改脚本退出码语义

---

## 五、通过条件（全部满足才算通过）

- [ ] 已明确定位 Linux runner 失败的 schema / 初始化根因
- [ ] 已在 workflow 中补齐 schema / 初始化前置步骤
- [ ] 已重新触发 GitHub Actions Linux benchmark
- [ ] 已提交新的 run URL / run ID / 最终状态
- [ ] 若 benchmark 成功，已提交完整结果与退出码
- [ ] 若 benchmark 失败，已提交新的失败证据与差异分析
- [ ] 正式报告文件与本轮编号一致
- [ ] 未越界推进到 Task 5.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T100-R-<timestamp>-p5-t52-linux-runner-schema-init-and-benchmark-rerun-report.md`

汇报必须包含：

1. 已完成任务编号
2. 失败根因定位
3. 修改文件清单
4. workflow 初始化修复说明
5. 新的 GitHub Actions run 信息
6. benchmark 原始输出或失败日志
7. 5 个端点结果表（若已成功跑完）
8. 是否出现 `5xx` / 超时 / 认证异常
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 5.2 验收

---

## 七、明确禁止

- 不得把“workflow 已触发”表述成“benchmark 已成功”
- 不得在 schema 未就绪的情况下再次空跑并声称已复现即可
- 不得通过降低 benchmark 口径来规避失败
- 不得提前进入 Task 5.3
