# M7-T91 — Phase-5 / Task 5.1 Docker 全栈构建与启动验证

> 任务编号：M7-T91  
> 阶段：Phase-5 / Task 5.1  
> 前置：M7-T90（Task 4.4 验收通过）  
> 时间戳：20260416-190040

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T90-AUDIT-SUMMARY-20260416-190040.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.1`

---

## 一、本轮目标

进入 `Phase-5 / Task 5.1 — Docker 全栈构建与启动验证`，目标是验证当前项目能够通过 Docker Compose 构建、启动，并完成 API 与浏览器层的最小端到端冒烟。

---

## 二、允许修改的范围文件

- `docker/docker-compose.yml`
- 如确有必要，可补充与全栈启动直接相关的最小配置修正
- 本轮新增报告文件：`docs/tasks/M7/M7-T91-R-<timestamp>-p5-t51-docker-full-stack-validation-report.md`

禁止越界到：

- Phase-5 的后续任务（性能基线、安全清单等）
- 与全栈启动无关的业务重构

---

## 三、必须完成的最小工作

### 1) 构建所有镜像

必须执行：

```bash
docker compose -f docker/docker-compose.yml build
```

要求：

- 报告中附真实命令
- 若构建失败，必须记录失败点与修复情况

### 2) 启动全栈

必须执行：

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 3) 等待 API 就绪

要求：

- 轮询 `http://localhost:8000/ready`
- 直到返回 `200`

### 4) 执行 API 冒烟测试

必须执行：

```bash
python scripts/smoke-test-api.py --api-url http://localhost:8000
```

要求：

- exit code = `0`

### 5) 执行浏览器 E2E 冒烟

必须执行：

```bash
npx playwright test --config=apps/web/playwright.config.ts
```

要求：

- 至少 `80%` passed
- 若少于该阈值，必须记录失败用例与原因

### 6) 检查容器健康状态

必须执行：

```bash
docker compose -f docker/docker-compose.yml ps
```

要求：

- 核对容器状态
- 目标是 `6` 个容器全部 `healthy/running`

### 7) 检查错误日志

要求：

- 检查关键容器日志
- 确认无 `error` 级别日志
- `warning` 可接受，但需如实记录

---

## 四、通过条件（全部满足才算通过）

- [ ] `docker compose build` 成功
- [ ] 全栈成功启动
- [ ] `/ready` 返回 `200`
- [ ] API 冒烟测试 exit code `0`
- [ ] 浏览器 E2E 测试 ≥ `80%` passed
- [ ] `docker compose ps` 显示 6 个容器全部 `healthy/running`
- [ ] 无 `error` 级别日志
- [ ] 产出与本轮编号一致的 `M7-T91-R-...` 报告

---

## 五、汇报要求

完成后提交：

- `M7-T91-R-<timestamp>-p5-t51-docker-full-stack-validation-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 镜像构建命令与结果
4. 启动命令与结果
5. `/ready` 检查结果
6. API 冒烟测试结果
7. Playwright 冒烟结果
8. `docker compose ps` 结果
9. 日志检查结果
10. 已验证通过项
11. 未验证部分
12. 风险与限制
13. 是否建议提交 Task 5.1 验收

---

## 六、明确禁止

- 不得跳过 Docker 实际构建与启动
- 不得只依赖本地开发模式结果冒充 Docker 全栈结果
- 不得提前推进到 Phase-5 后续任务
