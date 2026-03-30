# M6-T04 任务单：RC1 最终发布闸门与交付收口

任务编号: M6-T04  
时间戳: 20260329-215608  
前置任务: M6-T03（已通过）  
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

## 二、任务目标

在 M6-T03 基础上，完成 RC1 最终收口，产出可交付、可复核、可回滚的发布包证据。

### 目标 2.1：发布闸门复核脚本化

新增脚本: scripts/rc1_final_gate.ps1

脚本应串行执行并输出统一结果：
- docker compose -f docker/docker-compose.prod.yml up -d
- Start-Sleep 25
- docker compose -f docker/docker-compose.prod.yml ps
- curl.exe 检查:
  - http://localhost:8000/health
  - http://localhost:8000/api/training/status
  - http://localhost:3000（HTTP 200）
- Get-Content package.json | Select-String '"version"'
- docker logs docker-worker-1 | Select-Object -Last 20
- docker compose -f docker/docker-compose.prod.yml down -v

要求：
- 脚本末尾输出 FINAL_GATE=PASS 或 FINAL_GATE=FAIL
- 任一关键检查失败时，最终必须 FAIL

### 目标 2.2：发布说明补全（不改映射）

更新 docs/release/RC1_DEPLOYMENT_GUIDE.md，新增“最终闸门执行”小节：
- 给出一条命令执行脚本
- 给出预期通过条件
- 给出失败时的最小回滚步骤

### 目标 2.3：根 README 追加 RC1 验收入口

在 README.md 新增 RC1 最终验收入口：
- 脚本路径
- 一键验收命令
- 成功判定标识 FINAL_GATE=PASS

---

## 三、验收标准（必须全部通过）

1. 脚本存在并可执行
- scripts/rc1_final_gate.ps1 存在
- 在项目根执行后可完整跑完

2. 服务与接口
- docker compose ps 显示 6 服务 Up
- /health 返回 healthy
- /api/training/status 返回 worker healthy
- localhost:3000 返回 HTTP 200

3. 版本一致性
- package.json 显示 version 为 1.0.0-rc1

4. Worker 稳定性
- worker 日志末尾无 Traceback 和 IndexError

5. 清理收口
- down -v 返回 EXIT_CODE=0

6. 文档同步
- docs/release/RC1_DEPLOYMENT_GUIDE.md 已补“最终闸门执行”
- README.md 已补 RC1 验收入口

---

## 四、汇报要求

汇报文件路径：

docs/tasks/M6/M6-T04-R-20260329-215608-rc1-final-gate-and-handover-report.md

汇报必须包含：

1. 脚本完整执行输出（含 FINAL_GATE=PASS/FAIL）
2. docker compose ps 输出
3. 三个 curl.exe 检查结果
4. package.json 版本检查输出
5. worker 最后 20 行日志
6. down -v 的 EXIT_CODE=0 证据
7. 修改文件清单
8. 未解决风险（如有）

---

## 五、角色分工建议

- DevOps（Trae）: 编写并执行 rc1_final_gate.ps1
- Backend（Trae）: 校验 worker 稳定性证据
- Docs（Trae）: 更新部署指南与 README
- QA（Copilot）: 独立复核并给出通过/不通过结论
