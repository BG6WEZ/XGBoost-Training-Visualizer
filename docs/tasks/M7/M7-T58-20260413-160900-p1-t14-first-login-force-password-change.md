# M7-T58 任务单：P1-T14 首次登录强制改密与默认密码标记

任务编号: M7-T58  
时间戳: 20260413-160900  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-1 Task 1.4  
前置任务: M7-T56（已验收通过）、M7-T57（已验收通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/planning/LAUNCH_DEVELOPMENT_PLAN.md（重点阅读 Task 1.4 条目）
- [ ] docs/tasks/M7/M7-T56-20260413-110000-p1-t11-unified-secret-management.md
- [ ] docs/tasks/M7/M7-T56-1.1-fix-VERIFICATION.md
- [ ] docs/tasks/M7/M7-T57-20260413-155400-p1-t12-storage-path-traversal-protection.md

未完成上述预读，不得开始执行。

---

## 一、当前审核结论

M7-T56 与 M7-T57 的 focused 验证已通过，当前可以进入 Task 1.4。

当前放行依据：

1. Task 1.1 focused 测试复验通过：`TestJwtSecretValidation` 2 passed。
2. Task 1.2 focused 测试复验通过：`TestPathTraversalProtection` 4 passed。
3. 当前仓库中尚未发现 `must_change_password` 相关实现，说明 Task 1.4 尚未被提前推进。

因此，本轮允许继续执行 **Task 1.4 — 首次登录强制改密 + 默认密码标记**。

---

## 二、本轮目标

只完成 LAUNCH_DEVELOPMENT_PLAN 中的 Task 1.4，不得顺手推进 Task 1.5 Token 黑名单。

本轮目标：

1. 在用户模型中增加 `must_change_password` 字段。
2. 默认管理员账号初始化时标记 `must_change_password=True`。
3. 登录接口返回该字段，前端据此进入首次改密流程。
4. 用户改密成功后清除该标记。
5. 补齐最小后后端测试与前端联动验证证据。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/models/models.py
- apps/api/app/database.py
- apps/api/app/routers/auth.py
- apps/api/app/schemas/**（仅限 auth/user 响应字段最小同步）
- apps/api/tests/test_auth.py
- apps/api/tests/conftest.py（仅当 mock user/fixture 需要适配新字段时）
- apps/api/migrations/**（新增本轮 SQL 迁移）
- apps/web/src/pages/LoginPage.tsx
- apps/web/src/contexts/AuthContext.tsx（仅当登录后状态流转需要最小适配时）
- apps/web/src/lib/api.ts（仅当 auth 响应类型需要同步时）
- docs/tasks/M7/M7-T58-20260413-160900-p1-t14-first-login-force-password-change.md
- docs/tasks/M7/M7-T58-R-20260413-160900-p1-t14-first-login-force-password-change-report.md（完成后生成）

### 3.2 禁止修改

- Token 黑名单 / Redis 吊销逻辑
- 新增复杂密码策略、密码强度评分、邮件通知、找回密码
- 与认证无关的数据集、训练、结果、导出、部署逻辑
- 前端无关页面的大规模重构
- 任意超出 Task 1.4 的权限系统改造

---

## 四、必须完成的实现项

### 4.1 用户模型与默认管理员标记

必须完成：

1. `User` 模型新增 `must_change_password: bool` 字段，默认 `False`。
2. 数据库初始化默认管理员时设置 `must_change_password=True`。
3. 若数据库迁移由 SQL 文件管理，必须新增对应迁移文件。

### 4.2 登录响应返回改密标记

必须完成：

1. 登录 API 响应增加 `must_change_password` 字段。
2. 相关 schema / response type / 前端类型同步。
3. 不得只在后端内部计算而不返回给前端。

### 4.3 改密后清除标记

必须完成：

1. 改密接口成功后将当前用户的 `must_change_password` 设置为 `False`。
2. 再次登录时返回值应体现标记已清除。
3. 不得只修改内存对象而不持久化。

### 4.4 前端首次改密最小闭环

必须完成：

1. 登录后若返回 `must_change_password=true`，前端必须进入强制改密流程。
2. 可以采用弹窗、页面态提示或内联表单，但必须阻止用户把首次登录当作正常完成。
3. 改密成功后，前端状态需恢复到正常登录完成态。

不接受：

1. 只显示提示文案但允许用户跳过。
2. 只有后端字段，没有前端联动。
3. 只做前端假逻辑，不调用真实改密接口。

---

## 五、测试与验证要求

### 5.1 后端 focused 测试（必须）

至少新增并通过：

1. `test_admin_must_change_password_on_first_login`
2. `test_change_password_clears_flag`

如果现有 fixture 或 mock user 缺少新字段，必须最小同步适配。

### 5.2 建议执行命令

```bash
cd apps/api
python -m pytest tests/test_auth.py -v --tb=short
```

如前端有类型或构建受影响，至少执行：

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 5.3 最小链路证据（必须）

汇报中至少给出以下 2 组真实结果：

1. 默认 admin 首次登录返回 `must_change_password: true`
2. admin 修改密码成功后再次登录返回 `must_change_password: false`

证据必须包含：

1. 请求路径或页面路径
2. 输入参数或操作步骤
3. 关键响应字段或页面结果
4. 与本轮目标的对应关系

---

## 六、通过条件

- [ ] `User` 模型已新增 `must_change_password` 字段且默认值正确
- [ ] 默认 admin 初始化为 `must_change_password: true`
- [ ] 登录 API 返回 `must_change_password` 字段
- [ ] 改密成功后会清除该标记
- [ ] 后端 focused 测试已执行并通过
- [ ] 若前端类型/构建受影响，已完成最小门禁验证
- [ ] 至少 2 组真实链路证据完整
- [ ] 未越界推进 Task 1.5 或其他后续任务

---

## 七、多角色协作要求（强制）

1. `Backend-Agent`：模型、初始化、路由、schema、迁移与测试闭环。
2. `Frontend-Agent`：登录后首次改密联动与最小交互闭环。
3. `QA-Agent`：focused 测试、真实链路证据、已验证/未验证边界整理。
4. `Reviewer-Agent`：检查是否把“已加字段”误写成“完整安全体系已完成”。

允许单执行者分角色完成，但汇报必须按角色拆分产出与证据。

---

## 八、汇报要求

完成后必须生成：

`docs/tasks/M7/M7-T58-R-20260413-160900-p1-t14-first-login-force-password-change-report.md`

汇报至少包含：

1. 已完成任务
2. 修改文件
3. 实际验证命令
4. 实际结果
5. 未验证部分
6. 风险与限制
7. 是否建议继续下一任务

---

## 九、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 Task 1.5。