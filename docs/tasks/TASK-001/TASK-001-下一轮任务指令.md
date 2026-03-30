# TASK-001 下一轮任务指令（前端真实交互验证 + 数据质量门禁）

## 任务时间信息

- 任务编号：TASK-001
- 发布时间：2026-03-27
- 生效时间：立即生效
- 执行窗口：2026-03-27 至 2026-03-28
- 汇报截止：2026-03-28 18:00（本地时间）

## 零、开始前必须先做

1. 先阅读并遵守以下规则文件：
- `C:\Users\wangd\project\XGBoost Training Visualizer\docs\collaboraion\CLAUDE_WORK_RULES.md`
- `C:\Users\wangd\project\XGBoost Training Visualizer\docs\collaboraion\CLAUDE_REPORT_TEMPLATE.md`
- `C:\Users\wangd\project\XGBoost Training Visualizer\docs\collaboraion\CLAUDE_ACCEPTANCE_CHECKLIST.md`

2. 再阅读你上一轮汇报文件：
- `C:\Users\wangd\project\XGBoost Training Visualizer\docs\reports\2026-03-27-e2e-verification-quality-closure.md`

3. 先回复你本轮将调用哪些内部智能体、各自负责什么，再开始执行。

4. 最终仍由你统一汇报，不能只给摘要，必须给证据。

---

## 一、本轮目标

在不扩展产品范围的前提下，补齐上一轮未闭环风险，确保“可见交互链路”和“数据入口质量门禁”都可验证。

---

## 二、可用内部智能体（按需调用）

- AI ML工程师 / ai-ml-engineer
- 安全工程师 / security-engineer
- 数据工程师 / data-engineer
- UI/Ux设计师 / uiux-designer
- 产品经理 / product-manager-cn
- DevOps / devops-architect
- 测试工程师 / qa-engineer
- 后端专家 / backend-expert
- 前端专家 / senior-frontend-developer
- 架构师 / system-architect
- 技术负责人 / tech-lead-architect

建议最小协作分工（可调整）：
- devops-architect：安装并确认浏览器验证运行环境
- senior-frontend-developer：执行前端真实页面交互链路
- backend-expert + data-engineer：实现并验证数据质量门禁
- qa-engineer：补齐自动化测试与结果分级
- tech-lead-architect：最终一致性检查与风险复核

---

## 三、本轮任务范围（仅以下 2 项）

### 任务 1：前端真实浏览器交互 E2E 补验收

目标：
- 将“前端仅 API 验证”升级为“真实浏览器交互验证”。

必须完成：
1. 安装并验证浏览器测试运行环境（如 Playwright 所需浏览器）。
2. 通过真实浏览器完成以下链路并保留证据：
   - 扫描资产
   - 登记数据集
   - 发起切分
   - 创建实验
   - 启动实验
   - 查看训练状态与结果页面
3. 每一步必须同时给出：
   - 页面操作证据（截图或关键日志）
   - 对应后端接口响应证据（状态码/响应体关键字段）

验收标准：
- 至少 1 条完整链路从页面操作走通到结果可见。
- 明确列出“已验证页面”和“仍未验证页面”。
- 失败步骤必须包含可复现原因，不可只写“失败”。

---

### 任务 2：数据登记质量门禁（最小可用版）

目标：
- 在数据集登记入口增加质量防线，优先拦截导致训练直接失败的明显问题。

必须完成：
1. 在登记/或登记前检查流程中加入最小质量校验（至少覆盖）：
   - 目标列全空或有效样本过少
   - 目标列存在 NaN/Inf
   - 时间列无法解析（若任务依赖时间列）
2. 对失败场景返回明确可读错误，不得吞异常。
3. 补充最小自动化测试，至少覆盖：
   - 正常样本可通过
   - NaN/Inf 被拒绝
   - 时间列不可解析被拒绝（如适用）

验收标准：
- 对问题数据可稳定拒绝并返回可读错误信息。
- 对正常数据不引入回归。
- 测试结果明确区分：通过 / 跳过 / 未运行 / 失败。

---

## 四、范围限制

- 只允许执行本文件定义的 2 个任务。
- 不得提前开发下一阶段功能（如新算法平台、权限系统、在线预测服务等）。
- 不得将“未实际验证”写成“已验证通过”。

---

## 五、交付物要求

1. 阶段汇报文档（必须落盘）：
- 路径：`C:\Users\wangd\project\XGBoost Training Visualizer\docs\reports\`
- 文件名建议：`2026-03-27-task-001-frontend-e2e-data-quality-gate.md`

2. 汇报内容必须包含：
- 已完成任务编号
- 修改文件清单（逐项说明目的）
- 实际执行命令
- 实际结果与关键证据
- 未验证部分
- 风险与限制
- 是否建议继续下一任务

3. 提交前必须附上并勾选验收清单（引用）：
- `C:\Users\wangd\project\XGBoost Training Visualizer\docs\collaboraion\CLAUDE_ACCEPTANCE_CHECKLIST.md`

---

## 六、完成后的停点要求

- 本轮完成后必须暂停，等待人工验收。
- 未经确认不得继续下发或执行 TASK-002。
