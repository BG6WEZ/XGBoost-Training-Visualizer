# M7-T82 — Phase-4 / Task 4.1 再收口（部署验证与报告补齐）

> 任务编号：M7-T82  
> 阶段：Phase-4 / Task 4.1 Re-open  
> 前置：M7-T81（审计不通过）  
> 时间戳：20260416-163120

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T81-AUDIT-SUMMARY-20260416-163120.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.1`

---

## 一、本轮目标

本轮**不得进入 Task 4.2**。只允许继续收口 **Task 4.1 生产环境配置模板**，重点补齐两类缺口：

1. **正式完成报告**
2. **按部署文档成功启动的验证证据**

---

## 二、允许修改的范围文件

- `.env.example`
- `docker/.env.example`
- `docs/release/DEPLOYMENT_GUIDE.md`
- 本轮新增报告文件：`docs/tasks/M7/M7-T82-R-<timestamp>-p4-t41-deployment-verification-and-report.md`

禁止越界到：

- Task 4.2 的 Nginx 配置
- API / Worker / Frontend 业务逻辑
- 部署脚本大改

---

## 三、上一轮未通过的核心问题

你必须逐项消除以下问题：

1. **缺少 `M7-T81-R` / 本轮正式报告**
   - 当前没有与任务编号一致的完成报告

2. **缺少部署验证证据**
   - 当前只有模板和文档
   - 没有“按部署文档操作能成功启动”的命令、输出、状态检查

3. **文档与验证边界不清**
   - 需要明确哪些步骤已验证
   - 哪些步骤仍只是文档说明

---

## 四、必须完成的最小工作

### 1) 产出正式报告文件

必须新增：

- `M7-T82-R-<timestamp>-p4-t41-deployment-verification-and-report.md`

要求：

- 不得只口头汇报
- 不得继续缺少与任务编号一致的正式报告

### 2) 至少做一次最小部署验证

至少完成以下一组最小验证：

1. 按文档准备环境变量文件
2. 按文档执行启动命令
3. 检查 `docker compose ps` 或等价状态输出
4. 执行健康检查命令

可接受的验证粒度：

- 若全量生产模式启动成本高，可做最小可行验证
- 但必须提供真实命令与真实输出

### 3) 报告中必须附验证证据

至少包含：

- 实际执行命令
- 服务状态输出摘要
- 健康检查结果
- 若失败，失败原因与阻断点

### 4) 明确区分“已验证”与“仅文档说明”

报告中必须明确标注：

- 已验证通过的步骤
- 仅在文档中说明、但本轮未实际执行的步骤

### 5) 若发现文档与实际不符，必须顺手修正

如果在验证过程中发现：

- 命令路径不对
- 端口不对
- 脚本名不对
- 初始化步骤不对

则必须同步修正文档，再汇报最终版本。

---

## 五、通过条件（全部满足才算通过）

- [ ] `.env.example` 保持完整且带注释
- [ ] `docker/.env.example` 保持适用于 Docker 场景
- [ ] `docs/release/DEPLOYMENT_GUIDE.md` 已与仓库现实对齐
- [ ] 至少完成一次按部署文档的最小启动验证
- [ ] 报告附实际执行命令与验证结果
- [ ] 产出与本轮编号一致的 `M7-T82-R-...` 报告
- [ ] 未越界推进到 Task 4.2 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T82-R-<timestamp>-p4-t41-deployment-verification-and-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 实际执行的部署验证步骤
4. 实际执行命令
5. 服务状态结果
6. 健康检查结果
7. 已验证通过项
8. 未验证部分
9. 风险与限制
10. 是否建议提交 Task 4.1 验收

---

## 七、明确禁止

- 不得只写文档而不提供验证证据
- 不得缺少正式报告文件
- 不得提前进入 Task 4.2
