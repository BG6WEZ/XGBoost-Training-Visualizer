# M7-T38 任务单：M7-T37 审计修复（管理员路由注册与运行态证据闭环）

任务编号: M7-T38  
时间戳: 20260409-162822  
所属计划: M7 / Audit Fix for P1-T15  
前置任务: M7-T37（审核未通过）  
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

未完成上述预读，不得开始执行。

---

## 一、当前审核结论（必须先承认剩余问题）

M7-T37 相比上一轮已有实质进展：

1. 后端用户管理接口已对齐到 `/api/admin/users/**`。
2. focused 测试已覆盖新接口路径并通过。
3. `AdminUsersPage.tsx` 页面文件已存在。
4. 前端 typecheck/build 通过。

但当前**仍不能判定 P1-T15 闭环完成**，原因如下。

### 阻断问题 1：管理员页面未真正可达

T37 汇报自己已明确写出：

1. `AdminUsersPage` 已创建；
2. 但“未在路由中注册”；
3. 因而 `/admin/users` 页面实际不可访问。

这意味着：

1. 管理员用户管理页并未形成真实前端闭环；
2. 任务单要求的 `/admin/users` 页面仍未完成；
3. “页面已实现”只能算部分完成，不能算已交付可用。

### 阻断问题 2：真实链路证据不足

T37 要求至少提供：

1. 管理员登录并访问 `/admin/users` 页面成功；
2. 创建用户后列表可见；
3. 禁用或重置密码链路成功。

当前汇报中的前端部分仍主要是静态说明：

1. 没有证明 `/admin/users` 实际可达；
2. 没有提供页面运行态结果；
3. 由于路由未注册，所谓页面链路证据实际上无法成立。

### 阻断问题 3：汇报结论仍过早

T37 汇报在“未验证部分”和“风险与限制”中明确承认：

1. 路由未注册；
2. 导航入口缺失；

但仍给出“建议继续”的放行结论。当前不满足“管理员页面真实可用”的完成判定。

---

## 二、本轮修复目标

本轮**只修复 M7-T37 的剩余阻断项**，不推进 P1-T16，不扩展复杂权限、资源隔离、搜索分页或系统设置。

目标：

1. 将 `AdminUsersPage` 真实注册到 `/admin/users` 路由。
2. 补齐最小访问入口或最小跳转路径，使管理员能实际进入该页面。
3. 提供真实页面运行态证据，证明页面可访问且交互能打通后端。
4. 重写 T37 汇报，使其与实际可访问性和已验证边界一致。

---

## 三、范围边界

### 3.1 允许修改

- apps/web/src/router.tsx
- apps/web/src/pages/AdminUsersPage.tsx
- apps/web/src/components/**（仅限管理员页面所需最小交互抽取）
- apps/web/src/contexts/AuthContext.tsx（仅限管理员导航/权限显示所需最小修正）
- apps/web/src/app/App.tsx（仅限管理员入口或布局最小接入）
- apps/web/src/lib/api.ts（仅限管理员页面联调所需最小修正）
- apps/api/tests/**（仅当需要补页面联调相关最小接口验证时）
- docs/tasks/M7/M7-T37-R-20260409-142258-m7-t36-audit-fixes-admin-ui-and-user-route-contract-closure-report.md
- docs/tasks/M7/M7-T38-20260409-162822-m7-t37-audit-fixes-admin-route-registration-and-runtime-evidence.md
- docs/tasks/M7/M7-T38-R-20260409-162822-m7-t37-audit-fixes-admin-route-registration-and-runtime-evidence-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- apps/api/app/routers/users.py（当前接口路径已对齐，除非发现阻断缺陷）
- OAuth、SSO、第三方登录
- 公开注册、邮箱验证码、复杂权限系统
- 与认证无关的数据集/训练/结果/导出/版本管理逻辑
- P1-T16 及后续技术债、SHAP、GPU、部署增强
- 无关页面大规模重构或视觉翻新

---

## 四、必须完成的修复项

### 4.1 路由注册闭环

必须完成：

1. 注册 `/admin/users` 路由；
2. 该路由受认证保护；
3. 管理员可访问；
4. 普通用户不可访问，至少返回前端权限提示或跳转。

不接受：

1. 页面文件存在但仍未挂路由；
2. 只在汇报中写“已创建页面”，但运行态仍不可达。

### 4.2 最小入口或跳转路径

至少完成以下之一：

1. 在现有页面中增加管理员入口；
2. 或明确提供可直接访问的真实路径，并保证受保护路由可到达。

要求：

1. 管理员需要能实际进入页面，而不是只靠开发者手输不存在的路由。
2. 若暂不做完整导航，也必须在汇报中明确说明“当前使用直接路径访问”，并给出真实证据。

### 4.3 运行态证据补齐

至少提供 3 组真实链路证据：

1. 管理员登录后访问 `/admin/users` 成功。
2. 创建用户后页面列表刷新可见。
3. 禁用或重置密码交互成功。

证据必须包含：

1. 页面路径或操作步骤；
2. 请求参数或表单输入；
3. 页面结果或关键响应；
4. 与任务目标的对应关系。

如果无法做浏览器级真实页面验证，必须至少做最小集成验证并诚实说明缺口；不能把静态页面截图思维替代运行态结果。

### 4.4 汇报修复

M7-T38 汇报必须：

1. 不再把“页面文件存在”写成“页面闭环完成”；
2. 明确列出真实执行命令和真实结果；
3. 区分已验证 / 未验证 / 风险与限制；
4. 仅在 `/admin/users` 真正可达并完成最小交互后，才可给出继续下一任务建议。

---

## 五、多角色协同执行要求（强制）

1. `Frontend-Agent`：路由注册、管理员页面可达性、最小入口/跳转闭环。
2. `Auth-Agent`：保持认证保护与管理员权限判断不回退。
3. `QA-Agent`：补运行态证据、前端门禁和必要的最小集成验证。
4. `Reviewer-Agent`：检查汇报是否仍存在“文件已创建就算完成”的过度表述。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端 focused 测试（必须）

建议命令：

```bash
cd apps/api
python -m pytest tests/ -k "auth or user or admin" -v --tb=short
```

### 6.2 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.3 页面运行态证据（必须）

至少提供 3 组：

1. `/admin/users` 实际可访问。
2. 创建用户后页面结果变化可见。
3. 禁用/重置密码后的页面或接口结果可见。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] `/admin/users` 路由已注册且真实可达
- [ ] 管理员用户管理页面最小交互闭环可用
- [ ] 管理员可访问，普通用户不可访问
- [ ] 后端 focused 测试已执行
- [ ] 前端 typecheck/build 通过
- [ ] 至少 3 组真实运行态链路证据完整
- [ ] M7-T37 汇报已修正且不再过度表述
- [ ] 未越界推进 P1-T16 或后续任务

---

## 八、Copilot 审核重点

1. 是否只是补了路由而没有真实交互验证。
2. 是否管理员页面可见但普通用户仍可进入。
3. 是否继续用静态说明替代运行态证据。
4. 是否在页面仍不可达时继续宣称 P1-T15 已闭环。

---

## 九、风险提示

1. 若只做直达路由、不补导航入口，后续仍可能有可用性欠缺，但本轮可接受前提是运行态证据完整。
2. 当前若未处理用户与实验归属关系，本轮仍只完成认证与管理员管理，不代表资源级隔离完成。
3. 管理员页面目前若无分页、搜索、批量操作，不构成本轮阻断，但必须避免在汇报中夸大为完整后台系统。

---

## 十、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T38-R-20260409-162822-m7-t37-audit-fixes-admin-route-registration-and-runtime-evidence-report.md

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P1-T16 / M7-T39。