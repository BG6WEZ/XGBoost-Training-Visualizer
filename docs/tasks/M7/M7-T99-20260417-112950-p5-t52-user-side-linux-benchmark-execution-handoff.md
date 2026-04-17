# M7-T99 — Phase-5 / Task 5.2 再收口（用户侧 Linux Benchmark 执行交接）

> 任务编号：M7-T99  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T98（网络阻断已被定位，但本机仍无法完成 push 与 Linux runner 执行）  
> 时间戳：20260417-112950

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T98-AUDIT-SUMMARY-20260417-112950.md`
- [ ] 阅读 `docs/tasks/M7/M7-T98-R-20260417-112727-p5-t52-network-path-restoration-and-linux-runner-benchmark-report.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.2`

---

## 一、本轮目标

本轮**不得进入 Task 5.3**。只允许继续收口 `Task 5.2`。

当前已经确认：

- 本机环境无法完成 `git push`
- GitHub Actions 因代码未推送而无法执行
- Linux benchmark 结果仍缺失

因此本轮目标不再是继续本机调网络，而是把执行动作转移到**网络通畅且具备 GitHub 推送能力的环境**，完成 Linux runner benchmark 的真实执行。

---

## 二、允许修改的范围文件

- 如确有必要，可补充极少量与 GitHub Actions 执行直接相关的说明文件
- 本轮新增报告文件：`docs/tasks/M7/M7-T99-R-<timestamp>-p5-t52-user-side-linux-benchmark-execution-handoff-report.md`

禁止越界到：

- Task 5.3 或后续任务
- 修改 benchmark 阈值、并发数或退出码语义
- 再次把“没有 Linux 结果”包装为“Task 5.2 可验收”

---

## 三、必须完成的最小工作

### 1) 在网络通畅环境完成推送

必须在可访问 GitHub 的环境中执行：

```bash
git push origin master
```

要求：

- 报告中附推送成功证据
- 若默认分支不是 `master`，必须如实记录实际分支名

### 2) 手动触发 GitHub Actions workflow

必须在 GitHub 仓库页面触发：

- `.github/workflows/benchmark-linux.yml`

要求：

- 记录 workflow 运行编号或链接
- 记录触发时间

### 3) 提交 Linux runner 环境证据

必须提交：

- `uname -a`
- `/etc/os-release`
- runner 类型（`ubuntu-latest`）

### 4) 提交 benchmark 原始结果

必须提交：

- `python scripts/benchmark.py --base-url http://localhost:8000` 的输出
- 最终退出码
- 5 个端点的结果表
- 是否存在 `5xx` / 超时 / 认证异常

### 5) 诚实给出 `Task 5.2` 结论

只允许两种结论：

#### 情况 A：Linux runner 上 5 / 5 全部达标

则可以申请：

- `Task 5.2` 通过

#### 情况 B：Linux runner 上仍未全部达标

则必须明确：

- `Task 5.2` 仍不通过

---

## 四、通过条件（全部满足才算通过）

- [ ] 已在网络通畅环境完成代码推送
- [ ] 已手动触发 `benchmark-linux.yml`
- [ ] 已提交 Linux runner 环境证据
- [ ] 已提交 benchmark 原始输出与退出码
- [ ] 已按 `Task 5.2` 原始口径给出 5 个端点结果
- [ ] 已基于 Linux 结果诚实给出最终判断
- [ ] 正式报告文件与本轮编号一致
- [ ] 未越界推进到 Task 5.3 或后续任务

---

## 五、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T99-R-<timestamp>-p5-t52-user-side-linux-benchmark-execution-handoff-report.md`

汇报必须包含：

1. 已完成任务编号
2. 推送环境说明
3. `git push` 结果
4. GitHub Actions 运行信息
5. Linux runner 环境证明
6. benchmark 输出与退出码
7. 5 个端点结果表
8. 是否出现 `5xx` / 超时 / 认证异常
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 5.2 验收

---

## 六、明确禁止

- 不得继续只汇报“网络不通”而不转移到可执行环境
- 不得在 workflow 未执行时提交 Linux benchmark 结论
- 不得修改 benchmark 口径来规避失败
- 不得提前进入 Task 5.3
