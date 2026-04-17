# M7-T69 — Task 2.3 补收口（Compose Warning 闭环）

> 任务编号：M7-T69  
> 阶段：Phase-2 / Task 2.3 Re-open  
> 前置：M7-T68（审计不通过）  
> 时间戳：20260415-103222

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T68-AUDIT-SUMMARY-20260415-103222.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 2.3`

---

## 一、本轮目标

本轮**不得进入 Task 2.4**。只允许继续收口 **Task 2.3 Docker Compose 清理**，补齐上一轮未完成的“Compose 无 warning”要求。

---

## 二、允许修改的范围文件

- `docker/docker-compose.yml`
- `docker/docker-compose.prod.yml`
- `docker/docker-compose.dev.yml`
- `docker/.env.example`
- 如确有必要，可新增与 compose 验证直接相关的模板文件，但必须放在 `docker/` 内

禁止越界到：

- API 代码
- Worker 代码
- 前端代码
- Alembic
- 认证逻辑

---

## 三、必须完成的最小工作

### 1) 保持上一轮已完成项不退化

以下已完成项不得回退：

- 三个 compose 文件均无 `version:`
- `prod` compose 使用环境变量注入敏感值
- `prod` 长期服务包含 `restart: unless-stopped`
- `docker/.env.example` 不包含真实密钥

### 2) 关闭 `docker-compose.yml config` 的变量 warning

当前阻断点是：

- `docker compose -f docker/docker-compose.yml config`

会出现多条：

- `The "<VAR>" variable is not set. Defaulting to a blank string.`

你必须修复这一点，允许的方式包括但不限于：

1. 为 `docker/docker-compose.yml` 中引用的变量提供安全的默认值；
2. 为基础 compose 增加与验证命令匹配的 env 模板机制；
3. 调整 compose 结构，使当前验证命令在仓库默认状态下无 warning。

注意：

- 不能用真实密钥填充默认值
- 不能仅在报告里忽略 warning
- 不能把“没有 `version is obsolete`”偷换成“没有 warning”

### 3) 建议顺手修正 `prod` 健康检查参数化

非强制，但建议检查：

- `docker/docker-compose.prod.yml` 中 `pg_isready -U xgboost -d xgboost_vis`

若你能在不增加复杂度的前提下改为与环境变量一致，会更稳妥。

---

## 四、验证命令

必须重新执行以下命令，并在报告中附**完整原始输出**：

```bash
docker compose -f docker/docker-compose.yml config
docker compose -f docker/docker-compose.dev.yml config
docker compose -f docker/docker-compose.prod.yml --env-file docker/.env.example config
```

通过标准：

- 三条命令都退出 `0`
- 输出中不出现 warning

---

## 五、通过条件（全部满足才算通过）

- [ ] 三个 compose 文件均无 `version:` 行
- [ ] `prod` compose 中无硬编码密码/密钥
- [ ] `docker/.env.example` 已创建且变量齐全
- [ ] `prod` compose 中长期服务含 `restart: unless-stopped`
- [ ] 三条 `docker compose ... config` 命令可执行
- [ ] 三条命令输出均无 warning
- [ ] 未越界推进到 Task 2.4 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T69-R-<timestamp>-p2-t23-compose-warning-closure-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 如何关闭 `docker-compose.yml` 的变量 warning
4. `docker/.env.example` 或其他模板文件的关键变量清单
5. 是否顺手修正了 `prod` 健康检查
6. 实际执行命令
7. 三条命令的完整原始输出
8. 未验证部分
9. 风险与限制
10. 是否建议重新提交 Task 2.3 验收

---

## 七、明确禁止

- 不得在模板文件中写入真实密钥
- 不得把 warning 解释成“可忽略即算通过”
- 不得省略命令原始输出
- 不得提前进入 Task 2.4
