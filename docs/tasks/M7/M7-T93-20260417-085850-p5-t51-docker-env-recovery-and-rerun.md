# M7-T93 — Phase-5 / Task 5.1 再收口（Docker 环境恢复与全栈复测）

> 任务编号：M7-T93  
> 阶段：Phase-5 / Task 5.1 Re-open  
> 前置：M7-T92（环境未恢复，未完成最终复测）  
> 时间戳：20260417-085850

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T91-AUDIT-SUMMARY-20260416-201059.md`
- [ ] 阅读 `docs/tasks/M7/M7-T92-20260416-201059-p5-t51-docker-host-browser-routing-and-smoke-closure.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.1`

---

## 一、本轮目标

本轮**不得进入 Task 5.2**。只允许继续收口 **Task 5.1 Docker 全栈构建与启动验证**，本轮重点不是新增功能，而是恢复验证环境并完成一次**干净、可复现、可验收**的 Docker 全栈复测。

---

## 二、允许修改的范围文件

- `docker/docker-compose.yml`
- 如确有必要，可补充与 Docker 全栈联通直接相关的最小配置修正
- 本轮新增报告文件：`docs/tasks/M7/M7-T93-R-<timestamp>-p5-t51-docker-env-recovery-and-rerun-report.md`

禁止越界到：

- Task 5.2 或后续任务
- 与 Docker 全栈启动无关的业务逻辑重构

---

## 三、上一轮已知阻断

你必须先解决以下环境与验证阻断：

1. **Docker Desktop / Docker Daemon 已停止**
   - 当前无法继续做容器级复测

2. **宿主机 8000 端口存在冲突风险**
   - 先前出现本地进程抢占 `8000`，导致测试请求打到错误进程

3. **API 冒烟测试仍未达 `exit code 0`**
   - Docker 内部验证仍有训练轮询超时

4. **Playwright 通过率尚未达到 `>= 80%`**
   - 需要在 Docker 环境恢复后重新验证

---

## 四、必须完成的最小工作

### 1) 恢复 Docker 环境

要求：

- 重启 Docker Desktop / Docker Daemon
- 确认 Docker CLI 可正常工作

至少验证：

```bash
docker version
docker info
```

### 2) 清理宿主机端口冲突

重点检查：

- `8000`
- `3000`
- 如有必要也检查 `5432`、`6379`、`9000`、`9001`

要求：

- 在启动 Docker 全栈前，确认不会有本地 API 进程抢占 `8000`
- 报告中记录处理方式

### 3) 重新启动 Docker 全栈

必须执行：

```bash
docker compose -f docker/docker-compose.yml up -d
```

并提交：

- `docker compose ps`

要求：

- 目标仍是 `6 / 6 healthy/running`

### 4) 重新轮询 `/ready`

要求：

- 轮询 `http://localhost:8000/ready`
- 直到返回 `200`

### 5) 重新执行 API 冒烟测试

必须执行：

```bash
python scripts/smoke-test-api.py --api-url http://localhost:8000
```

要求：

- 最终必须 `exit code 0`
- 若训练仍超时，需要先定位是 Worker 时序、队列残留还是 Docker 资源问题，再修正后重跑

### 6) 重新执行浏览器 E2E 冒烟

必须执行：

```bash
npx playwright test --config=apps/web/playwright.config.ts
```

要求：

- 最终必须 `>= 80% passed`
- 若未达到阈值，必须记录失败用例与根因

### 7) 检查关键日志

至少检查：

- `api`
- `worker`
- `frontend`

要求：

- 无 `error` 级别日志
- `warning` 可接受，但必须如实记录

### 8) 最终报告必须明确“最终验收依据是哪一次执行”

如果本轮中做过多次尝试，报告必须区分：

- 环境恢复尝试
- 中间失败尝试
- 最终成功尝试

---

## 五、通过条件（全部满足才算通过）

- [ ] Docker Daemon 已恢复并可正常工作
- [ ] 宿主机端口冲突已排除
- [ ] `docker compose up -d` 后 6 个容器全部 `healthy/running`
- [ ] `/ready` 返回 `200`
- [ ] API 冒烟测试 exit code `0`
- [ ] 浏览器 E2E 测试 `>= 80% passed`
- [ ] 无 `error` 级别日志
- [ ] 产出与本轮编号一致的 `M7-T93-R-...` 报告
- [ ] 未越界推进到 Task 5.2 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T93-R-<timestamp>-p5-t51-docker-env-recovery-and-rerun-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. Docker 恢复方式
4. 端口冲突排查与处理结果
5. `docker compose ps` 结果
6. `/ready` 检查结果
7. API 冒烟测试结果
8. Playwright 冒烟结果
9. 日志检查结果
10. 已验证通过项
11. 未验证部分
12. 风险与限制
13. 是否建议提交 Task 5.1 验收

---

## 七、明确禁止

- 不得在 Docker Daemon 未恢复时宣称完成 Docker 全栈验证
- 不得在端口冲突未排除时提交新的主机侧测试结论
- 不得在 API 冒烟非 `0` 时写“Task 5.1 已通过”
- 不得在 E2E 通过率 < `80%` 时写“浏览器冒烟已通过”
- 不得提前进入 Task 5.2
