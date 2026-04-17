# M7-T40 任务单：P1-T16 技术债清理与主测试集绿灯基线

任务编号: M7-T40  
时间戳: 20260409-174925  
所属计划: P1-S6 / P1-T16  
前置任务: M7-T39（已完成，P1-T15 简化登录与管理员用户管理闭环完成）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T16 条目）
- [ ] docs/tasks/M7/M7-T36-20260409-092707-p1-t15-login-and-user-management-simplified.md
- [ ] docs/tasks/M7/M7-T36-R-20260409-092707-p1-t15-login-and-user-management-simplified-report.md
- [ ] docs/tasks/M7/M7-T39-20260409-165811-m7-t38-audit-fixes-browser-runtime-evidence-and-report-consistency.md
- [ ] docs/tasks/M7/M7-T39-R-20260409-165811-m7-t38-audit-fixes-browser-runtime-evidence-and-report-consistency-report.md
- [ ] README.md（重点阅读测试/启动脚本与环境说明）
- [ ] package.json（重点阅读现有 test/typecheck/build 脚本）

未完成上述预读，不得开始执行。

---

## 一、任务背景

P1-T15 已在 T36 到 T39 连续闭环，当前系统已经具备：

1. 登录、当前用户信息、退出登录、修改密码能力。
2. 管理员用户查看、创建、禁用、重置密码能力。
3. 浏览器运行态证据、后端 focused 测试、前端 typecheck/build 证据。

但根据 P1-T16 原始定义，当前还缺少一个面向全仓库的“技术债清理”收口轮次，目标不是继续新增业务功能，而是把现有实现中的测试债、路径一致性、接口契约偏差、文档与脚本漂移统一清干净，形成可以被复核的“主测试集全绿”基线。

本轮必须坚持诚实原则：

1. 不得通过删除失败测试、无理由 skip、降低断言强度来包装通过。
2. 不得把局部通过写成全量通过。
3. 若存在环境阻断，必须明确标注阻断范围和实际失败输出。

---

## 二、任务目标

1. 盘点并修复当前主测试集中的真实失败项。
2. 修复代码、脚本、文档中的路径不一致与接口契约不一致问题。
3. 清理会误导验证结论的临时实现、散落脚本或失效说明。
4. 形成一套可复核的主测试集验证结果：后端、worker、前端、关键浏览器冒烟。
5. 在不推进新功能的前提下，把 P1-T16 收敛到“主测试集全绿（允许已声明 skip）”的可验收状态。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/**
- apps/worker/**
- apps/web/**
- scripts/**
- package.json
- apps/web/package.json
- apps/api/pytest.ini
- apps/worker/requirements.txt
- 根目录测试与冒烟脚本（仅限与当前主测试集/验证链路直接相关的文件）
- README.md（仅限同步实际脚本、路径、运行方式）
- docs/planning/**（仅限同步测试命令、任务映射、事实性描述）
- docs/tasks/M7/M7-T40-20260409-174925-p1-t16-tech-debt-cleanup-and-main-test-green.md
- docs/tasks/M7/M7-T40-R-20260409-174925-p1-t16-tech-debt-cleanup-and-main-test-green-report.md（执行完成后生成）

### 3.2 禁止修改

- P2 功能开发（SHAP、迁移学习、监控、checkpoint 等）
- 新增 OAuth、SSO、公开注册、复杂 RBAC、多租户
- 与“修复现有失败/不一致”无关的新业务能力
- 纯视觉翻新、大规模页面重构
- 通过删除测试、改写需求、弱化断言来规避失败

---

## 四、详细交付要求

### 4.1 主测试集盘点与修复

必须先真实执行当前主测试集，再决定修复范围。至少盘点：

1. `apps/api` 全量 pytest
2. `apps/worker` 全量 pytest
3. 前端 typecheck/build
4. 至少 1 组关键浏览器冒烟

要求：

1. 每一个失败项都必须定位到真实根因，不得只在测试里绕过。
2. 如果失败来自过时测试，必须同时证明生产实现/契约的当前真实边界。
3. 如果失败来自生产代码，优先修生产代码，再最小同步测试。
4. 如果存在历史上已声明 skip 的测试，必须在汇报中单列说明，不得计入“通过”。

### 4.2 路径一致性与脚本清理

至少检查并修正以下类型问题：

1. README、package 脚本、测试脚本、文档中的路径与当前仓库结构不一致。
2. 根目录与子应用目录下重复、失效或误导性的测试入口。
3. 运行说明中把旧脚本、旧目录、旧端口写成当前事实。

要求：

1. 只保留对当前仓库真实可执行的命令说明。
2. 若保留临时脚本，必须说明用途与边界；若无必要，应归位或清理。

### 4.3 接口契约与测试契约对齐

至少检查并修正以下类型问题：

1. schema/model/router/types/tests/docs 对同一字段命名不一致。
2. 测试仍在断言旧路径、旧字段、旧状态机。
3. 浏览器冒烟脚本与真实页面交互/接口路径不一致。

要求：

1. 任何契约修正都必须是全链路同步，而不是单点修补。
2. 不得把“当前实现如此”当成无需修正文档的理由。

### 4.4 关键浏览器冒烟

本轮不是新增 E2E 需求，但必须保留至少 1 组关键浏览器冒烟作为主测试集的一部分。可接受范围：

1. 登录 -> 首页 -> 管理员用户页 -> 退出登录
2. 或一个等价的当前主链路浏览器冒烟

要求：

1. 脚本必须连接真实页面与真实 API。
2. 若使用现有 Playwright 脚本，必须先验证脚本仍然与当前实现一致。
3. 若环境阻断，必须给出启动命令、失败输出和阻断原因。

### 4.5 文档同步

完成后必须同步：

1. T40 汇报文档
2. 任何被本轮修正事实影响到的 README / planning / task 映射说明
3. 对已验证和未验证边界的诚实说明

---

## 五、多角色协同执行要求（强制）

1. `Backend-Agent`：处理 API pytest 失败、schema/router/model/test 契约对齐。
2. `Worker-Agent`：处理 worker pytest 失败、任务执行链路与测试夹具对齐。
3. `Frontend-Agent`：处理前端 typecheck/build 问题、浏览器冒烟脚本与实际页面一致性。
4. `QA-Agent`：执行主测试集，记录失败清单、复测结果、已声明 skip、环境阻断。
5. `Docs-Agent`：同步 README、planning、任务映射和汇报口径，防止旧路径和旧脚本残留。
6. `Reviewer-Agent`：确认没有通过删测试、降断言、扩大未验证区来伪造“全绿”。

允许执行者一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 后端全量 pytest（必须）

建议命令：

```bash
cd apps/api
pytest -v --tb=short
```

### 6.2 Worker 全量 pytest（必须）

建议命令：

```bash
cd apps/worker
pytest -v --tb=short
```

### 6.3 前端门禁（必须）

```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

### 6.4 关键浏览器冒烟（必须）

可接受命令示例：

```bash
cd <repo-root>
node test-playwright.mjs
```

或等价的当前有效 Playwright 冒烟脚本。

### 6.5 汇报中必须呈现

1. 首次执行主测试集时的失败清单。
2. 每类失败项的根因与修复策略。
3. 修复后的复测结果。
4. 已声明 skip / 未运行 / 环境阻断项的单列说明。

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] `apps/api` 全量 pytest 已执行并达到全绿或仅保留已声明 skip
- [ ] `apps/worker` 全量 pytest 已执行并达到全绿或仅保留已声明 skip
- [ ] 前端 `tsc --noEmit` 与 `pnpm build` 通过
- [ ] 至少 1 组关键浏览器冒烟已执行
- [ ] 已修复真实失败项，而不是通过删测/弱化断言规避
- [ ] 路径一致性问题已同步到代码、脚本与文档
- [ ] 接口契约不一致已完成全链路同步
- [ ] 汇报中区分“通过 / 跳过 / 未运行 / 运行失败”
- [ ] 未越界推进 P2 或其他新功能任务

---

## 八、Copilot 审核重点

1. 是否把 focused 测试通过包装成主测试集全绿。
2. 是否通过删除测试、改 skip、降低断言强度规避失败。
3. 是否只修测试不修生产代码根因。
4. 是否 README、脚本、文档仍保留旧路径、旧命令、旧端口、旧契约。
5. 是否把环境阻断项偷偷排除后仍写成“全量通过”。

---

## 九、风险提示

1. 全量 pytest 可能暴露历史遗留问题，修复过程中必须严格控范围，避免顺手推进新功能。
2. 当前仓库存在多入口测试脚本与多层文档说明，若不统一，后续每轮都会重复出现“代码与文档不一致”的治理问题。
3. 若浏览器冒烟依赖本地 API/Web/Redis 等环境，必须先固定启动方式，否则容易再次出现“脚本存在但不可复核”的问题。

---

## 十、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T40-R-20260409-174925-p1-t16-tech-debt-cleanup-and-main-test-green-report.md

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 P2 或新的 M7-T41。