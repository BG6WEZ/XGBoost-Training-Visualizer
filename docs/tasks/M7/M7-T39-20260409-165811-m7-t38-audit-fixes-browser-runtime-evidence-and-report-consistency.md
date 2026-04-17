# M7-T39 任务单：M7-T38 审计修复（浏览器运行态证据与汇报一致性闭环）

任务编号: M7-T39  
时间戳: 20260409-165811  
所属计划: M7 / Audit Fix for P1-T15  
前置任务: M7-T38（审核未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T36-20260409-092707-p1-t15-login-and-user-management-simplified.md
- [ ] docs/tasks/M7/M7-T36-R-20260409-092707-p1-t15-login-and-user-management-simplified-report.md
- [ ] docs/tasks/M7/M7-T37-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure.md
- [ ] docs/tasks/M7/M7-T37-R-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure-report.md
- [ ] docs/tasks/M7/M7-T38-20260409-162822-m7-t37-audit-fixes-admin-route-registration-and-runtime-evidence.md
- [ ] docs/tasks/M7/M7-T38-R-20260409-162822-m7-t37-audit-fixes-admin-route-registration-and-runtime-evidence-report.md

未完成上述预读，不得开始执行。

---

## 一、当前审核结论（必须先承认剩余问题）

M7-T38 相比上一轮已有实质修复，当前已可确认：

1. `/admin/users` 路由已注册。
2. `AdminRoute` 已存在，管理员/普通用户已做前端权限分流。
3. `AppLayout` 已增加管理员导航入口。
4. 后端 focused 测试通过。
5. 前端 typecheck/build 通过。

但当前**仍不能判定 P1-T15 闭环完成**，原因如下。

### 阻断问题 1：T38 任务要求的 3 组运行态证据仍未交付

T38 任务单明确要求至少提供：

1. 管理员登录后访问 `/admin/users` 成功；
2. 创建用户后页面列表刷新可见；
3. 禁用或重置密码交互成功。

当前 T38 汇报在“未验证部分”中明确承认：

1. 未做真实浏览器运行态验证；
2. 未验证创建用户弹窗完整交互；
3. 未验证禁用/启用实时更新；
4. 未验证重置密码完整流程。

这意味着：

1. 当前只有代码、测试和构建证据；
2. 没有满足任务单要求的页面运行态证据；
3. 不能把“可编译 + 路由已接线”写成“页面闭环已验证”。

### 阻断问题 2：T37 汇报未按 T38 要求同步修正

T38 任务单明确要求：

1. 重写 T37 汇报；
2. 使其与实际可访问性和已验证边界一致。

当前实际情况：

1. T37 汇报仍保留“未在路由中注册”“需要后续添加 `/admin/users` 路由”等陈述；
2. 这些内容已经与当前代码状态不一致；
3. 文档事实未同步，违反文档一致性原则。

### 阻断问题 3：T38 汇报结论仍然早于证据

当前 T38 汇报给出“建议继续”的放行结论，但其自身又明确写出：

1. 浏览器真实运行态未验证；
2. 管理员页面核心交互未验证。

在任务单已明确要求“至少 3 组真实运行态链路证据”的前提下，这一结论不能成立。

---

## 二、本轮修复目标

本轮**只修复 M7-T38 的剩余证据与文档问题**，不推进 P1-T16，不扩展复杂权限、资源隔离、分页搜索或系统设置。

目标：

1. 提供 `/admin/users` 的真实浏览器运行态证据。
2. 补齐创建用户、禁用/启用或重置密码的真实页面交互证据。
3. 修正 T37 汇报，使其与当前代码事实一致。
4. 修正 T38 汇报，使其只对已验证内容作结论。

---

## 三、范围边界

### 3.1 允许修改

- apps/web/src/**（仅当浏览器实测暴露真实阻断缺陷时做最小修复）
- apps/api/tests/**（仅当需要补最小运行态配套脚本或断言时）
- playwright-test.js
- test-playwright.js
- test-playwright.mjs
- docs/tasks/M7/M7-T37-R-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure-report.md
- docs/tasks/M7/M7-T38-R-20260409-162822-m7-t37-audit-fixes-admin-route-registration-and-runtime-evidence-report.md
- docs/tasks/M7/M7-T39-20260409-165811-m7-t38-audit-fixes-browser-runtime-evidence-and-report-consistency.md
- docs/tasks/M7/M7-T39-R-20260409-165811-m7-t38-audit-fixes-browser-runtime-evidence-and-report-consistency-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/api/app/routers/users.py（当前接口契约已对齐，除非浏览器联调暴露真实阻断）
- OAuth、SSO、第三方登录
- 公开注册、邮箱验证码、复杂权限系统
- 与认证无关的数据集/训练/结果/导出/版本管理逻辑
- P1-T16 及后续技术债、SHAP、GPU、部署增强
- 无关页面大规模重构或视觉翻新

---

## 四、必须完成的修复项

### 4.1 真实浏览器运行态证据

必须至少提供 3 组真实页面链路证据，优先使用 Playwright + 已安装系统浏览器（如 Edge channel）；若环境不支持，必须诚实阻断并停点。

至少包括：

1. 管理员登录成功并进入 `/admin/users` 页面；
2. 创建用户后页面列表出现新用户；
3. 以下二选一：
   - 禁用/启用用户后页面状态变化可见；
   - 重置密码成功并有页面或接口结果可见。

每组证据必须包含：

1. 页面路径；
2. 操作步骤；
3. 输入值；
4. 页面结果、接口结果或截图/日志摘要；
5. 与任务目标的对应关系。

### 4.2 权限负向证据

除上述 3 组证据外，至少补 1 组负向证据，证明普通用户不能正常进入管理员页面或不能完成管理员操作。

可接受形式：

1. 普通用户访问 `/admin/users` 时显示权限提示；
2. 或普通用户访问对应管理员接口被拒绝，并与页面结果形成闭环说明。

### 4.3 汇报修复

必须同步修复以下文档：

1. `M7-T37-R`：删除已失效的“路由未注册”表述，改为与当前代码事实一致；
2. `M7-T38-R`：仅在真实运行态证据补齐后才可写“建议继续”；否则必须明确写“当前不建议继续”；
3. `M7-T39-R`：按统一证据报告输出，不得再用静态说明替代运行态结果。

### 4.4 环境阻断时的诚实处理

如果浏览器运行态验证因环境问题无法完成，必须：

1. 真实记录阻断原因；
2. 提供已执行命令与失败结果；
3. 明确说明当前轮不能通过；
4. 不得用代码静态检查替代浏览器证据。

---

## 五、多角色协同执行要求（强制）

1. `Frontend-Agent`：确认路由、导航与页面交互在真实浏览器下可达。
2. `QA-Agent`：执行浏览器运行态验证，采集成功链路与负向链路证据。
3. `Auth-Agent`：确保登录态与管理员权限判断在浏览器链路中不回退。
4. `Reviewer-Agent`：修正 T37/T38 汇报中过时或过度表述内容。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端 focused 测试（必须）

建议命令：

```bash
cd apps/api
python -m pytest tests/test_auth.py -v --tb=short
```

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 浏览器运行态证据（必须）

建议优先命令或等价方案：

```bash
node playwright-test.js
```

或基于现有 Playwright 脚本补充本轮管理员链路验证。

至少提交：

1. 管理员登录并进入 `/admin/users` 的真实证据；
2. 创建用户的真实证据；
3. 禁用/启用或重置密码的真实证据；
4. 普通用户负向访问证据。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] `/admin/users` 页面已通过真实浏览器验证为可访问
- [ ] 管理员创建用户链路已通过真实浏览器验证
- [ ] 禁用/启用或重置密码链路已通过真实浏览器验证
- [ ] 普通用户不可正常完成管理员页面/管理员接口访问
- [ ] 后端 focused 测试已执行
- [ ] 前端 typecheck/build 通过
- [ ] T37 汇报已与当前代码事实对齐
- [ ] T38 汇报已与真实验证边界对齐
- [ ] 至少 4 组真实链路证据完整
- [ ] 未越界推进 P1-T16 或后续任务

---

## 八、Copilot 审核重点

1. 是否继续用“路由已注册 + build 通过”替代浏览器运行态证据。
2. 是否浏览器里只能打开页面，但创建/禁用/重置交互没有真实结果。
3. 是否普通用户仍可到达管理员页面而未形成明确负向结果。
4. 是否 T37/T38 汇报仍保留过时事实或过早放行结论。

---

## 九、风险提示

1. 如果浏览器验证依赖本地 API/Web 联调环境，启动脚本与测试账户准备必须清晰，否则容易再次出现“代码在位但证据不足”。
2. 当前即便本轮通过，也只代表“简化版登录与管理员管理”闭环，不代表资源级隔离、多租户或完整后台系统已完成。

---

## 十、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T39-R-20260409-165811-m7-t38-audit-fixes-browser-runtime-evidence-and-report-consistency-report.md

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T16 / M7-T40。