# M7-T98 — Phase-5 / Task 5.2 再收口（恢复网络路径并执行 Linux Runner Benchmark）

> 任务编号：M7-T98  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T97（`T96-R` 已补齐并诚实固化阻断，但尚无原生 Linux benchmark 结果）  
> 时间戳：20260417-105900

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T97-AUDIT-SUMMARY-20260417-105900.md`
- [ ] 阅读 `docs/tasks/M7/M7-T96-R-20260417-105255-p5-t52-native-linux-benchmark-validation-or-honest-scope-down-report.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.2`

---

## 一、本轮目标

本轮**不得进入 Task 5.3**。只允许继续收口 `Task 5.2`。

当前事实已经明确：

- `benchmark-linux.yml` 已创建
- `T96-R` 已诚实说明：本地无法取得原生 Linux 复核证据
- 当前阻断点已从“报告缺失”转为“缺少 Linux runner 的真实 benchmark 结果”

因此本轮唯一目标是：

1. 恢复到 GitHub 的网络连通性
2. 触发 `ubuntu-latest` runner 执行 Linux benchmark
3. 取得原生 Linux 结果并据此继续判断 `Task 5.2`

---

## 二、允许修改的范围文件

- `.github/workflows/benchmark-linux.yml`
- 如确有必要，可修改与 GitHub Actions benchmark 直接相关的最小辅助文件
- 本轮新增报告文件：`docs/tasks/M7/M7-T98-R-<timestamp>-p5-t52-network-path-restoration-and-linux-runner-benchmark-report.md`

禁止越界到：

- Task 5.3 或后续任务
- 与 Linux benchmark 执行无关的业务逻辑修改
- 通过修改 benchmark 阈值、并发数或退出码来制造“通过”

---

## 三、必须完成的最小工作

### 1) 排查并恢复 GitHub 网络路径

你必须先解决：

- 当前对 `github.com:443` 的连接失败

至少要提交以下排查结果之一：

- 代理配置检查结果
- DNS / TLS / 443 连接检查结果
- 如果修复成功，给出成功推送的证据
- 如果仍失败，明确失败点是否在本机、代理、公司网络或 GitHub 访问策略

### 2) 成功推送当前代码

要求：

- 将包含 `.github/workflows/benchmark-linux.yml` 的当前代码推送到远端仓库
- 提交可核验的推送成功证据

### 3) 在 GitHub Actions `ubuntu-latest` 上执行 benchmark

必须执行：

- 触发 `.github/workflows/benchmark-linux.yml`

并提交：

- workflow 链接或运行编号
- `uname -a`
- `/etc/os-release`
- benchmark 输出
- 最终退出码

### 4) 保持 benchmark 口径不变

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
- 修改 `benchmark.py` 的通过语义

### 5) 给出 Linux 结果后的诚实结论

本轮只允许两种结果：

#### 情况 A：Linux runner 上 5 / 5 全部达标

则可以据此申请：

- `Task 5.2` 通过

#### 情况 B：Linux runner 上仍未全部达标，或 workflow 仍无法成功执行

则必须诚实写明：

- `Task 5.2` 仍不通过

---

## 四、通过条件（全部满足才算通过）

- [ ] GitHub 网络路径已恢复或失败点已被明确定位
- [ ] 当前代码已成功推送到远端
- [ ] `ubuntu-latest` runner 已执行 `.github/workflows/benchmark-linux.yml`
- [ ] 已取得原生 Linux benchmark 结果
- [ ] benchmark 口径与 `Task 5.2` 保持一致
- [ ] 已根据 Linux 结果诚实给出最终判断
- [ ] 正式报告文件与本轮编号一致
- [ ] 未越界推进到 Task 5.3 或后续任务

---

## 五、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T98-R-<timestamp>-p5-t52-network-path-restoration-and-linux-runner-benchmark-report.md`

汇报必须包含：

1. 已完成任务编号
2. GitHub 网络排查结果
3. 推送结果
4. GitHub Actions 运行信息
5. Linux 环境证明
6. benchmark 输出与退出码
7. 5 个端点结果表
8. 是否出现 `5xx` / 超时 / 认证异常
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 5.2 验收

---

## 六、明确禁止

- 不得继续停留在“怀疑 WSL2 是主因”而不去取得 Linux 结果
- 不得在 workflow 未真正执行时提交 Linux benchmark 结论
- 不得修改 benchmark 口径来规避失败
- 不得提前进入 Task 5.3
