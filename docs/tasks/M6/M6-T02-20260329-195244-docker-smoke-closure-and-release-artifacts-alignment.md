# M6-T02 任务指令：Docker 冒烟闭环与发布物对齐修复

任务编号: M6-T02  
发布时间: 2026-03-29 19:52:44  
前置任务: M6-T01（审核结论：部分通过）  
预期汇报文件名: M6-T02-R-20260329-195244-docker-smoke-closure-and-release-artifacts-alignment-report.md

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] 读取 docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] 读取 docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] 读取本任务单全文

---

## 一、问题背景（来自 M6-T01 审核）

以下项目未满足原验收要求：

1. Docker Compose 冒烟不通过：前端 localhost:3000 不可达
2. 发布文档文件名不符合要求：应为 docs/release/RC1_DEPLOYMENT_GUIDE.md
3. 根版本号未更新为 1.0.0-rc1（当前仍为 1.0.0）
4. 汇报缺少建议 git tag 命令
5. 清理步骤 docker compose down -v 缺失可验证证据

---

## 二、任务目标

### 任务 1：Compose 冒烟闭环

使用 docker/docker-compose.prod.yml 完成一次完整冒烟：

- docker compose -f docker/docker-compose.prod.yml up -d
- docker compose -f docker/docker-compose.prod.yml ps
- curl.exe -s http://localhost:8000/health
- curl.exe -s -o NUL -w "%{http_code}" http://localhost:3000
- curl.exe -s http://localhost:8000/api/training/status

验收标准：

- compose ps 显示 frontend/api/worker/postgres/redis/minio 均为 Up
- /health 返回 healthy
- 前端 HTTP 状态码为 200
- 训练状态接口返回 worker_status

### 任务 2：发布文档对齐

新增或重命名到目标文件：docs/release/RC1_DEPLOYMENT_GUIDE.md，内容至少包含：

- 系统需求
- 快速启动
- 环境变量
- 健康检查
- 首次使用流程
- 排障

验收标准：目标文件存在且可读。

### 任务 3：版本与 README 对齐

- 将根 package.json version 更新为 1.0.0-rc1
- 在 README.md 明确 RC1 的 Docker 快速启动步骤（如已有相关段落，补齐即可）

验收标准：

- package.json 中 version 精确为 1.0.0-rc1
- README 中含 RC1 Docker 快速启动步骤

### 任务 4：发布命令建议与清理证据

- 在汇报中提供建议命令（仅文本，不执行）：
  - git tag -a v1.0.0-rc1 -m "RC1 release"
  - git push origin v1.0.0-rc1
- 冒烟结束后执行并提供证据：
  - docker compose -f docker/docker-compose.prod.yml down -v

验收标准：

- 汇报含上述两条 git tag 建议命令
- down -v 执行证据完整

---

## 三、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| devops-engineer | Compose 冒烟闭环与清理证据 |
| backend-expert | API/Worker 健康联动验证 |
| tech-writer | RC1_DEPLOYMENT_GUIDE 与 README 对齐 |
| release-manager | 版本号更新与 tag 命令建议整理 |

---

## 四、必须提供的实测证据

1. docker compose ps 全量输出
2. /health 输出
3. 前端 HTTP 状态码输出（必须是 200）
4. /api/training/status 输出
5. package.json 版本号截图或文本片段
6. RC1_DEPLOYMENT_GUIDE.md 文件路径与关键段落
7. docker compose down -v 输出
8. git tag 建议命令文本

---

## 五、禁止事项

- 禁止省略前端 3000 可达性证据
- 禁止只说“已完成”但不给命令输出
- 禁止执行真实 git tag/push

---

## 六、完成判定

以下条件全部满足才算完成：

- [ ] Compose 冒烟完整通过（含前端 200）
- [ ] RC1_DEPLOYMENT_GUIDE.md 已落地
- [ ] package.json version 已更新为 1.0.0-rc1
- [ ] README 含 RC1 Docker 快速启动步骤
- [ ] down -v 清理证据完整
- [ ] 汇报含建议 git tag 命令
