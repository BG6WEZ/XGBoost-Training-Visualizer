# M7-T92 — Phase-5 / Task 5.1 再收口（Docker 宿主机浏览器路由与冒烟闭环）

> 任务编号：M7-T92  
> 阶段：Phase-5 / Task 5.1 Re-open  
> 前置：M7-T91（审计不通过）  
> 时间戳：20260416-201059

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T91-AUDIT-SUMMARY-20260416-201059.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 5.1`

---

## 一、本轮目标

本轮**不得进入 Task 5.2**。只允许继续收口 **Task 5.1 Docker 全栈构建与启动验证**，重点解决两类阻断：

1. **Docker 场景下宿主机浏览器无法解析 `api` 内部域名**
2. **API 冒烟测试未达到 exit code `0`**

---

## 二、允许修改的范围文件

- `docker/docker-compose.yml`
- 如确有必要，可补充与 Docker 场景前后端联通直接相关的最小配置修正
- 本轮新增报告文件：`docs/tasks/M7/M7-T92-R-<timestamp>-p5-t51-docker-host-browser-routing-and-smoke-closure-report.md`

禁止越界到：

- Task 5.2 或后续任务
- 与 Docker 全栈联通无关的业务逻辑重构

---

## 三、上一轮未通过的核心问题

你必须逐项消除以下问题：

1. **API 冒烟测试不是成功态**
   - 当前 12 / 13 passed
   - 训练步骤超时

2. **Playwright 通过率远低于 80%**
   - 当前主要因 `VITE_API_URL=http://api:8000` 只适用于容器内，不适用于宿主机浏览器

---

## 四、必须完成的最小工作

### 1) 修正宿主机浏览器访问前端时的 API 地址

目标：

- 宿主机浏览器打开 `http://localhost:3000` 时，前端能访问到正确的 API 地址

可接受方向：

- 将前端构建时 API 地址指向宿主机可访问地址
- 或采用可同时兼容 Docker 内部与宿主机访问的方案

要求：

- 不得再让浏览器请求打到 `http://api:8000`
- 必须有真实浏览器层验证结果

### 2) 让 Playwright 冒烟达到至少 80% 通过

要求：

- 重新执行：

```bash
npx playwright test --config=apps/web/playwright.config.ts
```

- 通过率必须达到 `>= 80%`

### 3) 让 API 冒烟达到 exit code 0

要求：

- 重新执行：

```bash
python scripts/smoke-test-api.py --api-url http://localhost:8000
```

- 最终必须 `exit code 0`

若训练步骤仍容易超时，可在不违背真实链路前提下调整：

- 训练超时窗口
- 轮询等待策略
- Docker 场景下的 Worker 准备时序

### 4) 重新检查容器状态与日志

必须重新提交：

- `docker compose ps`
- 关键服务日志检查结论

要求：

- 容器仍为 6 / 6 healthy/running
- 无 `error` 级别日志

### 5) 报告必须以最终结果为准

要求：

- 明确写本轮最终验收依据是哪一次执行
- 若做过多次尝试，必须区分失败尝试与最终成功尝试

---

## 五、通过条件（全部满足才算通过）

- [ ] `docker compose build` 成功
- [ ] 全栈成功启动
- [ ] `/ready` 返回 `200`
- [ ] API 冒烟测试 exit code `0`
- [ ] 浏览器 E2E 测试 ≥ `80%` passed
- [ ] `docker compose ps` 显示 6 个容器全部 `healthy/running`
- [ ] 无 `error` 级别日志
- [ ] 产出与本轮编号一致的 `M7-T92-R-...` 报告
- [ ] 未越界推进到 Task 5.2 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T92-R-<timestamp>-p5-t51-docker-host-browser-routing-and-smoke-closure-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. Docker 场景下前端 API 地址如何修正
4. API 冒烟测试结果
5. Playwright 冒烟结果
6. `docker compose ps` 结果
7. 日志检查结果
8. 已验证通过项
9. 未验证部分
10. 风险与限制
11. 是否建议提交 Task 5.1 验收

---

## 七、明确禁止

- 不得继续保留宿主机浏览器无法解析 `api` 的前端配置
- 不得在 API 冒烟非 `0` 时写“Task 5.1 已通过”
- 不得在 E2E 通过率 < 80% 时写“浏览器冒烟已通过”
- 不得提前进入 Task 5.2
