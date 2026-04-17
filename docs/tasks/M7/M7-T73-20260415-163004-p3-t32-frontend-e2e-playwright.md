# M7-T73 — Phase-3 / Task 3.2 前端 E2E 测试（Playwright）

> 任务编号：M7-T73  
> 阶段：Phase-3 / Task 3.2  
> 前置：M7-T72（Task 3.1 已通过）  
> 时间戳：20260415-163004

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T72-AUDIT-SUMMARY-20260415-163004.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 3.2`

---

## 一、本轮目标

进入 `Phase-3 / Task 3.2 — 前端 E2E 测试（Playwright）`，目标是为前端关键用户流程建立可重复执行的端到端回归测试。

---

## 二、允许修改的范围文件

- `apps/web/package.json`
- `apps/web/playwright.config.ts`（新增）
- `apps/web/e2e/`（新增目录及测试文件）
- 如确有必要，可补充少量与 E2E 测试稳定性直接相关的前端选择器属性或测试辅助代码

禁止越界到：

- API 业务逻辑
- Worker 业务逻辑
- Docker / Alembic / 认证后端实现
- 与 E2E 测试无关的前端大重构

---

## 三、必须完成的最小工作

### 1) Playwright 基础配置

要求：

- 在 `apps/web/package.json` 中新增 `@playwright/test` devDependency
- 新增脚本：
  - `"test:e2e": "playwright test"`
- 新增 `apps/web/playwright.config.ts`

配置要求：

- `baseURL` 从环境变量读取
- 使用 `webServer` 自动启动 Vite dev server
- 截图输出保存到 `e2e/screenshots/` 或等效可追踪目录

### 2) 登录流程测试

新增：

- `apps/web/e2e/auth.spec.ts`

至少覆盖：

1. 正确用户名密码可登录
2. 错误密码显示错误提示
3. 登出后重定向到登录页

### 3) 数据资产流程测试

新增：

- `apps/web/e2e/assets.spec.ts`

至少覆盖：

1. 数据资产扫描按钮可点击并返回结果
2. 上传 CSV 文件成功
3. 注册数据集成功并跳转详情

### 4) 实验流程测试

新增：

- `apps/web/e2e/experiments.spec.ts`

至少覆盖：

1. 创建实验（选择数据集、模板、参数）
2. 实验列表显示新创建的实验
3. 提交训练任务

### 5) 结果查看测试

新增：

- `apps/web/e2e/results.spec.ts`

至少覆盖：

1. 已完成实验结果页可正常加载
2. 指标数据可见
3. 实验对比页可选择多个实验

### 6) 测试用例数量

要求：

- 总 E2E 用例数不少于 10 个

### 7) 稳定性要求

可以为了测试稳定性补充少量 `data-testid` 或其他选择器支持，但要求：

- 改动尽量小
- 仅为 E2E 稳定性服务
- 报告中必须写明新增了哪些测试选择器

---

## 四、验证要求

至少执行以下命令，并在报告中附完整输出：

```bash
cd apps/web
npx playwright test
```

如果需要先启动后端服务，必须在报告中明确说明前置启动方式。  
如果使用了额外环境变量，也必须写清楚。

---

## 五、通过条件（全部满足才算通过）

- [ ] `npx playwright test` 全部 passed
- [ ] E2E 用例数不少于 10 个
- [ ] 覆盖登录 / 数据资产 / 实验 / 结果查看四类流程
- [ ] 截图证据自动生成
- [ ] `test:e2e` 脚本已加入 `package.json`
- [ ] 未越界推进到 Task 3.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T73-R-<timestamp>-p3-t32-frontend-e2e-playwright-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. Playwright 配置说明
4. 新增测试文件与测试用例清单
5. 总用例数量
6. 是否新增了前端测试选择器；若有，列出位置
7. 后端/前端前置启动方式
8. 实际执行命令
9. 实际输出原文
10. 截图输出路径
11. 未验证部分
12. 风险与限制
13. 是否建议进入 Task 3.3

---

## 七、明确禁止

- 不得只搭 Playwright 框架而不写实质用例
- 不得少于 10 个 E2E 用例
- 不得跳过截图证据
- 不得提前进入 Task 3.3
