# M7-T41 任务单：发布门禁自动化与真实冒烟闭环

任务编号: M7-T41  
时间戳: 20260410-083606  
所属计划: M7 收口轮次 / RC1 发布前治理  
前置任务: M7-T40（已提交汇报，待复核）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T40-20260409-174925-p1-t16-tech-debt-cleanup-and-main-test-green.md
- [ ] docs/tasks/M7/M7-T40-R-20260409-p1-t16-tech-debt-cleanup-and-main-test-green-report.md
- [ ] README.md
- [ ] docs/release/RC1_RELEASE_CHECKLIST.md
- [ ] package.json
- [ ] apps/web/package.json

未完成上述预读，不得开始执行。

---

## 一、任务背景

对 M7-T40 汇报与仓库当前状态的复核结果显示：

1. 主测试集当前确实为绿灯：
   - `apps/api`：`336 passed, 9 skipped`
   - `apps/worker`：`4 passed`
   - `apps/web`：`pnpm typecheck`、`pnpm build` 通过
2. 但 T40 汇报仍存在若干不可忽略的不一致与治理缺口：
   - 汇报文件名与任务单预期文件名不一致。
   - 汇报声称已删除 `apps/api/tests/test_feature_engineering_validation.py`，但该文件实际仍存在，且当前测试通过。
   - T40 要求“至少 1 组关键浏览器冒烟已执行”，但汇报实际复用了 T39 历史证据，不满足“本轮真实执行”的严格口径。
   - 汇报结构未完全按模板显式列出“修改文件清单 / 实际执行命令 / 未验证部分 / 风险与限制”。
3. 项目整体质量仍存在发布前缺口：
   - 当前仓库未发现 CI workflow，主门禁尚未自动化。
   - 9 个 skip 主要依赖 Redis / 集成环境，缺少统一的启动与解释机制。
   - 前端 build 有 chunk size warning，虽然不阻塞，但应纳入发布门禁说明。

因此，本轮任务不是新增业务功能，而是把“人工绿灯”提升为“可复核、可自动执行、口径诚实”的发布门禁基线。

---

## 二、任务目标

1. 让主测试集与关键浏览器冒烟具备一键复核能力。
2. 修复 T40 汇报中的事实不一致、命名不一致和模板缺项。
3. 将 skip、环境依赖、启动顺序、门禁脚本统一成明确且诚实的发布前说明。
4. 建立最小 CI 或等价自动化门禁，避免后续再靠手工口头声明“全绿”。
5. 在不推进 P2 和新业务功能的前提下，完成 RC1 前最后一轮质量治理闭环。

---

## 三、范围边界

### 3.1 允许修改

- `.github/workflows/**`（如需新增 CI）
- `package.json`
- `README.md`
- `docs/release/RC1_RELEASE_CHECKLIST.md`
- `docs/planning/**`（仅限同步真实测试/门禁说明）
- `docs/tasks/M7/M7-T40-R-20260409-p1-t16-tech-debt-cleanup-and-main-test-green-report.md`
- `docs/tasks/M7/M7-T41-20260410-083606-release-gate-automation-and-honest-smoke-closure.md`
- 与门禁自动化直接相关的根目录脚本
- `smoke-test.mjs`、`test-playwright.mjs` 或其等价当前有效脚本
- 必要的少量 API / Web / Worker 代码与测试，但仅限修复门禁链路与真实运行问题

### 3.2 禁止修改

- P2 功能开发
- 新增业务页面、训练能力、权限模型、监控系统等功能性扩展
- 纯视觉改版
- 通过删除测试、扩大 skip、降低断言强度伪造通过
- 无关的大规模重构

---

## 四、详细交付要求

### 4.1 T40 汇报纠偏

必须复核并修正 T40 汇报中的事实性问题，至少包括：

1. 汇报文件名与任务单预期文件名不一致的问题。
2. “已删除文件”与仓库实际状态不一致的问题。
3. 补齐模板要求：
   - 已完成任务
   - 修改文件
   - 实际验证命令
   - 实际结果
   - 未验证部分
   - 风险与限制
4. 对“浏览器冒烟”必须明确区分：
   - 本轮真实执行
   - 复用历史证据
   - 因环境阻断未执行

要求：

1. 不得改写历史事实；若 T40 当时未执行，则必须诚实修正文案。
2. 不得把“可运行”写成“已验证”。

### 4.2 关键浏览器冒烟真实闭环

必须让关键浏览器冒烟在当前仓库具备真实执行路径，至少覆盖：

1. 登录页可访问
2. 管理员登录成功
3. 管理员用户页可访问
4. 至少一个主链路页面可访问（数据集页或实验页）

要求：

1. 脚本必须连接真实页面与真实 API。
2. 必须给出明确的启动前提：PostgreSQL / Redis / API / Worker / Web。
3. 若当前环境无法完整执行，必须给出真实失败输出和阻断点，不得再复用旧截图代替本轮运行。
4. 若现有脚本可用，则修正其文档与入口；若现有脚本不可用，则只做最小修复，不得扩展为大型 E2E 工程。

### 4.3 主门禁自动化

至少实现以下二选一之一，优先 A：

1. A 方案：新增最小 CI workflow，自动执行
   - API pytest
   - Worker pytest
   - Web typecheck
   - Web build
2. B 方案：新增统一本地门禁脚本，并在 README / 发布清单中明确一键执行方式

若选择 A 方案，要求：

1. workflow 名称清晰，触发条件最小可用。
2. 不要求在 CI 内启动完整浏览器运行态，但必须说明 smoke 的本地执行方式。

若选择 B 方案，要求：

1. 一条命令可串起当前主门禁。
2. 输出中必须清楚区分 passed / skipped / failed。

### 4.4 Skip 与环境依赖治理

必须梳理当前 9 个 skip 的真实原因，并在文档中显式列出：

1. 哪些 skip 依赖 Redis
2. 哪些 skip 依赖 workspace 权限或本地目录权限
3. 哪些属于集成环境测试，不应计入纯单元门禁

要求：

1. 不要求本轮消灭全部 skip。
2. 但必须把 skip 变成“可解释的已声明边界”，而不是隐性灰区。

### 4.5 文档一致性收口

至少同步以下事实：

1. 当前推荐启动顺序
2. 当前主门禁命令
3. 当前浏览器冒烟脚本入口
4. 构建 warning 的现状与影响边界
5. CI 是否存在、覆盖到什么程度

要求：

1. README、RC1 清单、任务汇报三者口径必须一致。
2. 不得保留“旧脚本名/旧路径/旧文件名”作为当前事实。

---

## 五、多角色协同执行要求（强制）

1. `QA-Agent`：复跑主门禁、整理 skip 与环境阻断、确认 smoke 是否真实执行。
2. `Docs-Agent`：修正 T40 汇报、README、RC1 清单和下一轮汇报口径。
3. `Frontend-Agent`：处理浏览器冒烟脚本与页面入口一致性，评估 build warning。
4. `Backend-Agent`：处理 smoke/API 启动链路与 Redis 依赖说明，必要时修最小根因。
5. `DevOps-Agent`：落 CI workflow 或统一本地 gate 脚本。
6. `Reviewer-Agent`：检查是否再次出现“历史证据冒充本轮验证”的问题。

允许一人分角色完成，但汇报必须按角色拆分产出与证据。

---

## 六、必须提供的实测证据

### 6.1 当前主门禁结果（必须）

```bash
cd apps/api
pytest

cd apps/worker
pytest

cd apps/web
pnpm typecheck
pnpm build
```

### 6.2 关键浏览器冒烟（必须）

必须真实执行以下之一：

```bash
node smoke-test.mjs
```

或

```bash
node test-playwright.mjs
```

或等价当前有效脚本。

### 6.3 自动化门禁证据（必须）

1. CI workflow 文件或统一 gate 脚本内容。
2. 实际执行输出或截图。

### 6.4 汇报中必须明确区分

1. 通过
2. 跳过
3. 未运行
4. 运行失败
5. 环境阻断

---

## 七、完成判定

以下全部满足才可宣称完成：

- [ ] T40 汇报中的事实不一致已纠正
- [ ] T40 汇报已补齐模板关键字段
- [ ] 关键浏览器冒烟已在本轮真实执行，或已给出真实阻断证据
- [ ] 主门禁已有 CI workflow 或统一 gate 脚本
- [ ] README / RC1 清单 / 汇报口径一致
- [ ] 已单列说明 skip 的真实原因和环境边界
- [ ] 未越界推进 P2 或新业务功能

---

## 八、Copilot 审核重点

1. 是否再次把历史截图或旧 JSON 当成本轮真实执行证据。
2. 是否修文档而不修事实。
3. 是否只增加 CI 文档说明，却没有可执行脚本或 workflow。
4. 是否把 skip 继续隐藏在“全绿”表述里。
5. 是否因为追求自动化而顺手扩大了功能范围。

---

## 九、风险提示

1. 浏览器冒烟依赖完整本地环境，若环境不稳，最容易再次出现“脚本存在但不可复核”。
2. CI 若引入数据库/Redis 依赖，复杂度会上升；本轮应坚持最小可用，不做重量级流水线工程。
3. 文档纠偏涉及历史汇报，必须诚实修改，不得用模糊措辞掩盖前一轮未真实执行的部分。

---

## 十、预期汇报文件

本任务预期汇报文件：

docs/tasks/M7/M7-T41-R-20260410-083606-release-gate-automation-and-honest-smoke-closure-report.md

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得继续推进新的 M7-T42。