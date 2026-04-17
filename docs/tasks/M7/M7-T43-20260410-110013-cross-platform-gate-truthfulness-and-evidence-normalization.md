# M7-T43 任务单：跨平台门禁真实性与证据命名规范收口

任务编号: M7-T43  
时间戳: 20260410-110013  
所属计划: M7 收口轮次 / RC1 发布前治理  
前置任务: M7-T42（已提交汇报，待复核）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T42-20260410-100021-gate-proof-and-report-integrity-closure.md
- [ ] docs/tasks/M7/M7-T42-R-20260410-100021-gate-proof-and-report-integrity-closure-report.md
- [ ] docs/tasks/M7/M7-T41-R-20260410-083606-release-gate-automation-and-honest-smoke-closure-report.md
- [ ] scripts/main-gate.bat
- [ ] scripts/main-gate.sh
- [ ] README.md
- [ ] docs/release/RC1_RELEASE_CHECKLIST.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

对 T42 汇报与仓库状态复核后，确认以下事实：

1. Windows 本地主门禁已经真实可运行：
   - `scripts/main-gate.bat` 当前可跑通
   - 实测结果仍为 `336 passed, 9 skipped`、`4 passed`、Web typecheck/build 通过
   - summary 已显式输出 `Passed / Skipped / Failed`
2. T42 仍未达到“可直接判定为完成”的严格标准：
   - 汇报明确仍存在 `CI 远端运行` 未验证项
   - 汇报明确浏览器冒烟仍受环境阻断
   - 但最终结论仍写为 `✅ 完成`，与任务单完成标准冲突
3. T42 还存在两个实质性治理缺口：
   - 证据文件 `docs/tasks/M7/evidence/t42/main-gate-output.md` 未带时间戳，不满足 T42 自身对证据命名的要求
   - `scripts/main-gate.sh` 的 API 测试结果判断依赖 `tee` 管道后的 `$?`，存在脚本误判通过的风险；同时 `grep -oP` 也带来跨环境兼容性风险

本轮任务不新增功能，不做新门禁扩展，只收口“结论口径、证据命名、Unix 脚本真实性”三件事。

---

## 二、任务目标

1. 修正 T42 汇报结论，使其与“未验证项”和任务单完成标准严格一致。
2. 将本轮证据文件改为带轮次和时间戳的规范命名，并同步所有引用位置。
3. 修复 `scripts/main-gate.sh` 的成功判定逻辑，避免 API pytest 失败时被 `tee` 掩盖成通过。
4. 在可能情况下补做一次 Unix 侧最小验证；若当前环境无法执行，必须诚实给出阻断说明。

---

## 三、范围边界

### 3.1 允许修改

- `scripts/main-gate.sh`
- `scripts/main-gate.bat`（仅在需要对齐口径时最小修改）
- `docs/tasks/M7/M7-T42-R-20260410-100021-gate-proof-and-report-integrity-closure-report.md`
- `docs/tasks/M7/evidence/t42/**`
- `README.md`（仅当证据路径或脚本口径需同步）
- `docs/release/RC1_RELEASE_CHECKLIST.md`（仅当证据路径或脚本口径需同步）

### 3.2 禁止修改

- 新增业务功能
- 扩大浏览器冒烟范围
- 新增 CI 能力范围之外的流水线工程
- 通过删改测试或增加 skip 制造通过
- 无关的大规模重构

---

## 四、详细交付要求

### 4.1 T42 汇报结论纠偏

必须根据 T42 任务单完成标准重新判断结论：

1. 若仍存在关键未验证项，则不得写 `✅ 完成`
2. 必须在 `已完成并已验证 / 已完成但未独立验证 / 未完成或不在本轮范围` 三层中保持一致
3. `最终结论`、`未验证部分`、`风险与限制` 三处口径必须完全对齐

### 4.2 证据文件命名规范化

必须将 T42 门禁证据文件改成带轮次和时间戳的文件名，例如：

`docs/tasks/M7/evidence/t42/t42-main-gate-output-YYYYMMDD-HHMMSS.md`

要求：

1. 文件必须保留本轮真实输出内容
2. 汇报内所有路径引用必须同步更新
3. 若保留旧文件，必须明确说明其状态；更推荐直接规范化并避免重复歧义

### 4.3 Unix 主门禁脚本真实性修复

必须修复 `scripts/main-gate.sh` 的以下问题：

1. API pytest 的退出码不能被 `tee` 掩盖
2. 不得依赖脆弱或不必要的 GNU-only 正则能力，除非明确说明环境前提
3. summary 必须继续正确输出 `Passed / Skipped / Failed`

至少应明确处理：

1. `set -o pipefail` 或等价手段
2. pytest 退出码捕获方式
3. skipped 数量提取失败时的兜底逻辑

### 4.4 验证要求

至少完成以下之一：

1. 在可用 Unix shell 环境中真实执行 `scripts/main-gate.sh`
2. 若当前工作机无法执行 Unix 脚本，则给出真实阻断，并补最小静态推演说明为何修复后逻辑正确

注意：

1. Windows 已验证通过，不可替代 Unix 侧验证结论
2. 不允许把“理论正确”写成“已验证通过”

---

## 五、协作要求

本任务必须采用内部多代理协作方式完成，至少覆盖以下角色：

1. `QA-Agent`：复核 T42 汇报结论、核对证据路径、执行或评估 Unix 验证。
2. `Shell-Agent`：修复 `scripts/main-gate.sh` 的退出码与 skipped 统计逻辑。
3. `Docs-Agent`：同步 T42 汇报及相关路径引用。
4. `Reviewer-Agent`：专门检查“是否再次过度宣称完成”。

若实际由单代理执行，必须在汇报中显式说明职责拆分。

---

## 六、执行要求

1. 先证伪风险，再改脚本，再验证，再改汇报。
2. 所有“已验证”结论都必须有对应证据。
3. 所有“未验证”项都必须有明确阻断原因。
4. 不得再出现“结论已完成，但正文承认关键未验证项”的自相矛盾。

---

## 七、预期交付物

1. 修正后的 `scripts/main-gate.sh`
2. 如有必要，对齐后的 `scripts/main-gate.bat`
3. 规范命名后的 T42 主门禁证据文件
4. 修订后的 T42 汇报
5. 本轮统一汇报文档：

   `docs/tasks/M7/M7-T43-R-20260410-110013-cross-platform-gate-truthfulness-and-evidence-normalization-report.md`

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

1. `✅ 完成`
2. `⚠️ 部分完成`
3. `❌ 未完成`

---

## 九、验收清单

- [ ] T42 汇报结论已与未验证项严格一致
- [ ] T42 证据文件已改为带轮次和时间戳的规范命名
- [ ] 汇报中的证据路径引用已全部同步
- [ ] `scripts/main-gate.sh` 不再因 `tee` 掩盖 pytest 失败退出码
- [ ] `scripts/main-gate.sh` 仍能正确输出 `Passed / Skipped / Failed`
- [ ] 若 Unix 未实际执行，已明确写明阻断原因且未过度宣称
- [ ] 未新增业务范围或越界开发

---

## 十、风险提示

1. 当前工作环境若缺少可用 Bash，Unix 侧只能做到静态修复和受限验证，必须诚实说明。
2. skipped 统计若过度依赖输出格式，后续 pytest 文案变化可能导致脚本脆弱；应尽量保持提取逻辑简单清晰。
3. 证据文件重命名后若引用未同步，会再次造成验收混乱。

---

## 十一、完成后动作

完成后必须停点等待人工验收。未经确认，不得推进新的 M7-T44。