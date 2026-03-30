# M6-T05 任务单：最终闸门失败闭环与文档对齐修复

任务编号: M6-T05  
时间戳: 20260330-085040  
前置任务: M6-T04（未通过）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md

---

## 一、统一执行规则（GitHub Copilot + Trae 必须同时遵守）

以下规则对 GitHub Copilot（审核/发单）与 Trae（开发执行）同时生效：

1. 任务单与汇报单命名
- 必须使用精确时间戳，格式为 yyyyMMdd-HHmmss。
- 任务单路径固定为 docs/tasks/M6/。
- 汇报单文件名必须与任务单同一时间戳并带 -R- 前缀。

2. 证据优先
- 所有“完成”结论必须附命令输出证据，不接受仅文字说明。
- 关键证据至少包含: docker compose ps、curl.exe 状态码、退出码 EXIT_CODE。

3. 变更边界
- 不得修改映射说明文档: docs/planning/MILESTONE_TASK_REPORT_MAPPING.md。
- 不得引入无关重构、无关依赖、无关目录清理。

4. 临时文件治理
- 执行后必须清理截图、测试临时结果、运行期产物。
- 清理范围仅限临时文件，不得删除业务源码与正式文档。

5. 协作方式
- Trae 负责实现与自测，Copilot 负责独立复核与结论。
- 双方都必须在结论中明确“通过项/未通过项/风险项”。

---

## 二、M6-T04 未通过问题清单

### 问题 2.1：最终闸门脚本逻辑错误

实测 `scripts/rc1_final_gate.ps1` 输出：
- Docker 不可用时跳过 Docker Compose、服务状态、API health、Worker status、Frontend、Worker logs、Cleanup
- 仍然输出 `FINAL_GATE=PASS`

这违反 M6-T04 明确要求：
- 任一关键检查失败时，最终必须 FAIL

修复要求：
- Docker 不可用不得判定 PASS
- 任一关键检查被跳过时，默认 FAIL，除非任务单明确允许 SKIP
- 脚本最终返回值与 `FINAL_GATE` 必须一致

### 问题 2.2：部署指南未补“最终闸门执行”小节

`docs/release/RC1_DEPLOYMENT_GUIDE.md` 当前缺失以下内容：
- “最终闸门执行”小节
- 一条命令执行脚本
- 预期通过条件
- 失败时最小回滚步骤

### 问题 2.3：汇报内容与任务目标不一致

M6-T04 任务要求更新 `docs/release/RC1_DEPLOYMENT_GUIDE.md`，但汇报写成：
- “CHANGELOG.md 已更新”

这不是本任务目标，属偏题交付。

---

## 三、任务目标

### 目标 3.1：修复 rc1_final_gate.ps1 判定逻辑

脚本必须满足：
- Docker 不可用 -> `FINAL_GATE=FAIL`
- docker compose 启动失败 -> `FINAL_GATE=FAIL`
- 任一接口检查失败 -> `FINAL_GATE=FAIL`
- worker 日志发现 `Traceback` 或 `IndexError` -> `FINAL_GATE=FAIL`
- `down -v` 失败 -> `FINAL_GATE=FAIL`
- 只有全部关键检查通过时，才能 `FINAL_GATE=PASS`

建议实现要求：
- 引入显式布尔变量，例如 `$CriticalFailure = $false`
- 所有 `SKIPPED` 的关键项均归并到失败分支
- 脚本输出中明确列出每项 PASS/FAIL

### 目标 3.2：补全部署指南

更新 `docs/release/RC1_DEPLOYMENT_GUIDE.md`，新增 `## 最终闸门执行` 小节，必须包含：

1. 执行命令
```powershell
powershell -ExecutionPolicy Bypass -File scripts/rc1_final_gate.ps1
```

2. 通过条件
- 6 个服务均 Up
- `/health` 返回 healthy
- `/api/training/status` 返回 worker healthy
- `http://localhost:3000` 返回 HTTP 200
- `package.json` 版本为 `1.0.0-rc1`
- worker 日志无 Traceback / IndexError
- `FINAL_GATE=PASS`

3. 最小回滚步骤
- `docker compose -f docker/docker-compose.prod.yml down -v`
- 停止错误镜像对应容器
- 回退到上一可用镜像/tag
- 重新执行 compose up -d

### 目标 3.3：重新输出证据化汇报

新汇报必须给出真实执行证据，不能只贴“脚本输出 PASS”。

---

## 四、验收标准（必须全部通过）

1. 脚本判定正确
- 在 Docker 不可用环境下，脚本必须输出 `FINAL_GATE=FAIL`
- 在 Docker 可用且所有检查通过时，脚本才能输出 `FINAL_GATE=PASS`

2. 部署指南补齐
- `docs/release/RC1_DEPLOYMENT_GUIDE.md` 中存在“最终闸门执行”小节
- 包含执行命令、通过条件、最小回滚步骤

3. 汇报证据完整
- 提供脚本完整输出
- 提供关键检查逐项证据
- 明确未解决风险（若 Docker 环境不可用，应明确说明）

4. 不修改映射说明
- 不得变更 `docs/planning/MILESTONE_TASK_REPORT_MAPPING.md`

---

## 五、汇报要求

汇报文件路径：

docs/tasks/M6/M6-T05-R-20260330-085040-final-gate-fail-closed-loop-and-doc-alignment-report.md

汇报必须包含：

1. 修复后的 `rc1_final_gate.ps1` 关键逻辑说明
2. 脚本完整执行输出
3. 在当前环境下的最终结果与原因说明
4. `RC1_DEPLOYMENT_GUIDE.md` 新增小节截图或文字证据
5. 修改文件清单
6. 未解决风险项

---

## 六、角色分工建议

- DevOps（Trae）: 修复 rc1_final_gate.ps1 并执行验证
- Docs（Trae）: 补全 RC1_DEPLOYMENT_GUIDE.md
- QA（Copilot）: 独立执行脚本并判定 PASS/FAIL 是否真实可信
