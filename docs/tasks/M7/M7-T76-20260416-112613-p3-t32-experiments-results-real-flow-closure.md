# M7-T76 — Phase-3 / Task 3.2 再收口（实验/结果真实主路径闭环）

> 任务编号：M7-T76  
> 阶段：Phase-3 / Task 3.2 Re-open  
> 前置：M7-T75（审计不通过）  
> 时间戳：20260416-112613

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T75-AUDIT-SUMMARY-20260416-112613.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 3.2`

---

## 一、本轮目标

本轮**不得进入 Task 3.3**。只允许继续收口 **Task 3.2 前端 E2E 测试（Playwright）**，重点补齐 `experiments.spec.ts` 与 `results.spec.ts` 的真实业务主路径，并纠正报告与截图证据不一致问题。

---

## 二、允许修改的范围文件

- `apps/web/package.json`
- `apps/web/playwright.config.ts`
- `apps/web/e2e/`
- 如确有必要，可补充少量仅服务于 E2E 稳定性的前端选择器属性
- 本轮新增报告文件：`docs/tasks/M7/M7-T76-R-<timestamp>-p3-t32-experiments-results-real-flow-closure-report.md`

禁止越界到：

- API / Worker 业务逻辑
- Docker / Alembic / 认证后端实现
- 与 E2E 稳定性无关的前端大重构

---

## 三、上一轮未通过的核心问题

你必须逐项消除以下问题：

1. **`experiments.spec.ts` 仍保留静默跳过逻辑**
   - 当前仍有 `if (await tableElement.isVisible(...).catch(() => false)) { ... }`

2. **`results.spec.ts` 仍保留静默跳过逻辑**
   - 当前仍有 `isVisible(...).catch(() => false)` + 条件点击模式

3. **实验主路径仍未落地**
   - 仍未做到真实创建实验
   - 仍未做到真实提交训练任务
   - 仍未做到列表中出现新实验的强断言

4. **结果主路径仍未落地**
   - 仍未绑定真实实验结果做断言
   - 仍未做到对比页多实验选择的真实状态变化验证

5. **截图证据与报告不一致**
   - 报告写 `TC8-upload-success.png`
   - 实际目录里是 `TC8-upload-attempt.png`

6. **报告表述超前**
   - 不得再写“所有审计问题已解决”，除非代码与证据都已对齐

---

## 四、必须完成的最小工作

### 1) 删除实验与结果测试中的所有静默跳过逻辑

本轮必须确保以下模式在 `experiments.spec.ts` / `results.spec.ts` 中不再存在：

- `if (await locator.isVisible(...).catch(() => false))`
- `const ok = await locator.isVisible(...).catch(() => false); if (ok) { ... }`
- “关键元素不存在时直接结束测试”

要求：

- 关键元素不存在时必须失败
- 不能通过条件分支绕过核心动作

### 2) 实验流程必须落成真实主路径

至少完成以下链路：

1. 准备一个真实可用的数据集
2. 打开实验创建页面
3. 实际填写创建实验所需字段
4. 实际提交创建
5. 在实验列表中验证新实验出现
6. 实际触发训练提交
7. 对提交成功状态或任务状态变化做真实断言

禁止：

- 只验证按钮可见
- 只验证表单存在
- 只验证“表格如果存在就检查，否则跳过”

### 3) 结果流程必须绑定真实实验结果

至少完成以下链路：

1. 基于前面真实创建并提交过训练的实验
2. 打开实验详情或结果页
3. 对指标、状态字段、图表或结果区块做真实断言
4. 在对比页中选中多个实验
5. 断言对比状态变化或对比结果区块发生变化

禁止：

- 直接 `goto('/assets/1/quality')` / `goto('/compare')` 后只断言 `body` 可见
- 找不到实验链接时无失败退出
- 只截图不验证结果内容

### 4) 截图证据必须与报告逐项一致

要求：

- 报告列出的截图文件名，必须全部真实存在
- 若截图数量不是 20 张，报告必须如实写明
- 不得再出现“报告写成功截图、目录却只有 attempt 截图”的情况

### 5) 报告必须诚实对齐当前事实

本轮报告必须明确区分：

- 已验证通过
- 未验证
- 因环境/后端限制无法验证

禁止：

- 在未完成真实实验创建/训练/结果断言时写“全部问题已解决”
- 用“页面可访问”包装成“业务主路径已验证”

### 6) 必须真实执行 Playwright，并附本轮原始输出

至少执行：

```bash
cd apps/web
npx playwright test
```

要求：

- 报告中附本轮完整原始输出
- 输出必须对应当前代码
- 若仍有失败，必须诚实记录，不能写“已完成”

---

## 五、通过条件（全部满足才算通过）

- [ ] `npx playwright test` 全部 passed
- [ ] E2E 用例数不少于 10 个
- [ ] 覆盖登录 / 数据资产 / 实验 / 结果查看四类流程
- [ ] `experiments.spec.ts` 与 `results.spec.ts` 中不存在静默跳过式通过逻辑
- [ ] 实验流程达到“真实创建 + 列表出现 + 提交训练 + 真实断言”
- [ ] 结果流程达到“真实结果页断言 + 对比状态变化断言”
- [ ] 截图证据实际生成并与报告逐项一致
- [ ] `test:e2e` 脚本仍保持可用
- [ ] 产出与本轮编号一致的 `M7-T76-R-...` 报告
- [ ] 未越界推进到 Task 3.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T76-R-<timestamp>-p3-t32-experiments-results-real-flow-closure-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 实验与结果流程的数据准备策略
4. 删除了哪些静默跳过逻辑
5. 实验创建 / 训练提交 / 结果验证 / 对比验证分别如何落地
6. 实际执行命令
7. `npx playwright test` 完整原始输出
8. 实际截图输出路径与截图文件示例
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议重新提交 Task 3.2 验收

---

## 七、明确禁止

- 不得继续保留 `catch(() => false)` 式关键路径跳过逻辑
- 不得把“页面可见”描述成“实验/结果真实主路径完成”
- 不得让截图目录与报告文件名不一致
- 不得用报告文字掩盖代码和证据缺口
- 不得提前进入 Task 3.3
