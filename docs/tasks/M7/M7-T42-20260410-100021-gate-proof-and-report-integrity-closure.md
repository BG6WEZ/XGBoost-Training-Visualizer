# M7-T42 任务单：门禁留痕与汇报口径完整性闭环

任务编号: M7-T42  
时间戳: 20260410-100021  
所属计划: M7 收口轮次 / RC1 发布前治理  
前置任务: M7-T41（已提交汇报，待复核）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T41-20260410-083606-release-gate-automation-and-honest-smoke-closure.md
- [ ] docs/tasks/M7/M7-T41-R-20260410-083606-release-gate-automation-and-honest-smoke-closure-report.md
- [ ] .github/workflows/main-gate.yml
- [ ] scripts/main-gate.bat
- [ ] scripts/main-gate.sh
- [ ] README.md
- [ ] docs/release/RC1_RELEASE_CHECKLIST.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

对 M7-T41 汇报与仓库现状的复核结果如下：

1. T41 已经完成了实质性推进：
   - 新增 GitHub Actions workflow：`.github/workflows/main-gate.yml`
   - 新增本地主门禁脚本：`scripts/main-gate.bat`、`scripts/main-gate.sh`
   - README 与 RC1 检查清单已同步门禁、skip、chunk warning 说明
   - T40 汇报中的关键失实表述已被纠正
2. 当前仓库状态已经具备较强发布基线：
   - 本地实际复核 `scripts/main-gate.bat` 可跑通
   - `apps/api`：`336 passed, 9 skipped`
   - `apps/worker`：`4 passed`
   - `apps/web`：`pnpm typecheck`、`pnpm build` 通过
3. 但 T41 仍未完全收口，主要问题已从“有没有做”转为“证据是否完整、口径是否准确”：
   - 汇报仍写成“任务完成”，但同时承认 CI 未验证，完成口径偏满
   - T41 任务单明确要求门禁输出区分 `passed / skipped / failed`，但当前脚本 summary 只输出 `Passed / Failed`
   - T41 汇报缺少足够直接的本轮主门禁实际执行留痕，导致第三方复核成本偏高

本轮不再扩展功能范围，只完成“证据闭环 + 口径闭环 + summary 闭环”，把 RC1 发布门禁变成真正可交接、可复核、可追责的最终版本。

---

## 二、任务目标

1. 修正门禁脚本 summary，让结果显式区分 `passed / skipped / failed`。
2. 为本地主门禁补齐本轮真实执行留痕，保证第三方无需猜测即可复核。
3. 纠正 T41 汇报中的完成口径，使“已验证 / 未验证 / 不在本轮范围”边界清楚。
4. 在不新增业务功能的前提下，形成可验收的 RC1 门禁最终文档包。

---

## 三、范围边界

### 3.1 允许修改

- `scripts/main-gate.bat`
- `scripts/main-gate.sh`
- `.github/workflows/main-gate.yml`
- `README.md`
- `docs/release/RC1_RELEASE_CHECKLIST.md`
- `docs/tasks/M7/M7-T41-R-20260410-083606-release-gate-automation-and-honest-smoke-closure-report.md`
- `docs/tasks/M7/M7-T42-20260410-100021-gate-proof-and-report-integrity-closure.md`
- `docs/tasks/M7/evidence/**`（仅限新增本轮门禁执行证据）

### 3.2 禁止修改

- 新增 P2 功能
- 修改业务功能范围或交互范围
- 通过新增 skip、删除测试、放宽断言来换取门禁通过
- 无关的大规模重构
- 用历史截图或旧日志伪装成本轮执行证据

---

## 四、详细交付要求

### 4.1 主门禁 summary 语义修正

必须修改本地主门禁脚本，使最终 summary 至少显式输出：

1. `Passed`
2. `Skipped`
3. `Failed`

要求：

1. `Skipped` 不能只是预留变量，必须出现在 summary 输出中。
2. 若某一步自身无法精确统计 skip 数，至少要在统一 summary 中明确写出“本轮总 skip 数来自 API pytest 结果”或等价真实口径。
3. 不得把 skipped 计入 passed。
4. Windows 与 Unix 脚本口径必须一致。

### 4.2 本轮真实执行留痕

必须补齐一次本轮真实主门禁执行的证据，至少包括：

1. 实际执行命令
2. 关键输出摘要
3. 最终 summary
4. 产物保存位置
5. 若有 warning，必须原样记录而非省略

证据可以采用以下任一或组合方式：

1. 汇报内直接粘贴关键输出片段
2. 单独 evidence 文件保存原始日志，再在汇报中链接/引用
3. 截图加文本摘要，但文本摘要不可缺失

要求：

1. 证据必须是本轮新生成，文件名带当前轮次和时间戳。
2. 禁止仅写“已执行，通过”而无输出。
3. 若执行环境与 T41 不同，必须说明差异。

### 4.3 T41 汇报口径纠偏

必须修正 T41 汇报，使其明确分层：

1. 已完成并已验证
2. 已完成但未独立验证
3. 未完成 / 不在本轮验证范围

至少要处理以下口径问题：

1. `CI 未验证` 与 `任务完成` 的表述冲突
2. 本地门禁是否已真实执行，证据是否足以支撑“已验证”
3. 浏览器冒烟、CI、主门禁三者的验证边界

要求：

1. 如果 GitHub 上的 Actions 没有真实运行记录，不得写成“CI 已验证通过”。
2. 如果本地主门禁已实际跑通，可以写“本地主门禁已验证通过”，但要附证据。
3. 最终结论允许写“部分完成”或“完成但保留未验证项”，不得为了好看强行写满分口径。

### 4.4 文档一致性收口

README、RC1 checklist、T41 汇报三处口径必须一致回答以下问题：

1. 当前主门禁包含哪些步骤
2. 当前 skip 总数是多少，是否计入通过
3. CI 是“已配置”还是“已验证”
4. 浏览器冒烟当前属于“已验证”还是“需完整环境后再执行”
5. 前端 chunk warning 是否阻塞发布

---

## 五、协作要求

本任务必须采用内部多代理协作方式完成，至少覆盖以下角色：

1. `QA-Agent`：复跑门禁、整理输出证据、核对 skip / warning 口径。
2. `DevOps-Agent`：修正主门禁脚本 summary 与 workflow 说明。
3. `Docs-Agent`：同步 README、RC1 checklist、T41 汇报的一致口径。
4. `Reviewer-Agent`：按验收清单做最终交叉复核，专门检查“是否过度宣称”。

若实际由单代理执行，必须在汇报中显式说明如何完成上述角色职责拆分，不得省略协作视角。

---

## 六、执行要求

1. 先复核，再修改，再复跑，再出汇报，不得倒序。
2. 每一项“已完成”都必须有对应证据。
3. 每一项“未验证”都必须有明确阻断说明。
4. 不得把 T41 中已经纠正过的历史事实再次写回错误状态。

---

## 七、预期交付物

1. 修正后的 `scripts/main-gate.bat`
2. 修正后的 `scripts/main-gate.sh`
3. 如有必要，同步更新 `.github/workflows/main-gate.yml`
4. 本轮新增的门禁执行证据文件
5. 修订后的 T41 汇报
6. 本轮统一汇报文档：

   `docs/tasks/M7/M7-T42-R-20260410-100021-gate-proof-and-report-integrity-closure-report.md`

---

## 八、汇报要求

汇报必须严格包含以下栏目，缺一不可：

1. 已完成任务
2. 修改文件清单
3. 实际执行命令
4. 实际结果
5. 证据文件路径
6. 未验证部分
7. 风险与限制
8. 多代理分工说明
9. 最终结论

最终结论只能三选一：

1. `✅ 完成`：仅当本轮要求全部满足且无关键未验证项
2. `⚠️ 部分完成`：主体完成，但仍有明确未验证边界
3. `❌ 未完成`：关键要求未达成

---

## 九、验收清单

- [ ] `scripts/main-gate.bat` summary 已显式输出 passed / skipped / failed
- [ ] `scripts/main-gate.sh` summary 已显式输出 passed / skipped / failed
- [ ] 至少 1 次本轮真实主门禁执行证据已留档
- [ ] T41 汇报已修正“完成 / 未验证”口径冲突
- [ ] README、RC1 checklist、T41 汇报三处口径一致
- [ ] 未把 skipped 计入 passed
- [ ] 未把“已配置 CI”写成“已验证 CI”
- [ ] 汇报包含统一证据与多代理分工说明

---

## 十、风险提示

1. GitHub Actions 是否真正触发，若当前无法在远端执行，仍可能保留未验证项；这不阻止本轮完成，但必须诚实标注。
2. 不同平台 shell 行为可能导致批处理与 shell 脚本输出不一致，必须实际复核而不是只看源码。
3. 若 evidence 文件命名或路径再次不规范，会削弱后续验收效率。

---

## 十一、完成后动作

完成后必须停止继续开发，提交汇报并等待人工验收。未经确认，不得推进新的 M7-T43。