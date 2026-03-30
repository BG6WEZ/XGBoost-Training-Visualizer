# M6-T01 任务指令：RC1 正式发布 — Git Tag、Docker 构建验证与部署文档

**任务编号**: M6-T01  
**发布时间**: 2026-03-29 18:25:00  
**前置任务**: M5-T04（已审核通过，RC1 就绪）  
**预期汇报文件名**: `M6-T01-R-20260329-182500-rc1-release-git-docker-deploy-report.md`

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 读取本任务单全文

---

## 一、任务背景

M5 已关闭，RC1 就绪。当前仓库只有一个初始 commit（`88beaee Initial commit`）。Docker 基础设施（Dockerfile × 3 + docker-compose.yml + docker-compose.dev.yml）已存在但从未验证过实际构建。本轮目标是将代码推到"可构建、可部署、可回溯"的正式 RC1 状态。

---

## 二、任务目标

### 任务 1：Docker 镜像构建验证

逐一构建三个服务镜像并确认无构建错误：

```bash
docker build -t xgboost-vis-api:rc1 -f apps/api/Dockerfile apps/api
docker build -t xgboost-vis-web:rc1 -f apps/web/Dockerfile apps/web
docker build -t xgboost-vis-worker:rc1 -f apps/worker/Dockerfile apps/worker
```

若构建失败，修复 Dockerfile 或依赖文件后重试。

验收标准：
- 三个镜像均构建成功（无 error 退出）
- 输出 `docker images` 可见三个 `rc1` 标签镜像

### 任务 2：Docker Compose 冒烟启动

使用已有 `docker/docker-compose.yml` 启动全栈：

```bash
cd docker
docker compose up -d
```

- 等待所有服务 healthy/started
- 验证 API 健康端点：`curl http://localhost:8000/health`
- 验证前端可访问：`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000`
- 验证 Worker 接入：`curl http://localhost:8000/api/training/status`

验收标准：
- `docker compose ps` 显示所有容器 Up 状态
- API `/health` 返回 `{"status":"healthy"}`
- 前端返回 HTTP 200
- Worker 状态可见

完成后清理：`docker compose down -v`

### 任务 3：RC1 部署文档

在 `docs/release/` 下创建 `RC1_DEPLOYMENT_GUIDE.md`，包含：

1. **系统需求**（Docker 版本、最低硬件）
2. **快速启动**（docker compose 一键方式）
3. **本地开发模式**（docker-compose.dev.yml + 本地服务启动）
4. **环境变量说明**（所有 ENV 逐项）
5. **健康检查端点说明**
6. **首次使用流程**（启动 → 扫描资产 → 创建实验 → 训练 → 查看结果）
7. **常见问题排查**

验收标准：按文档操作可完成首次使用流程。

### 任务 4：版本标记

确认以上全部通过后：

1. 在 `package.json`（根）中确认 version 字段为 `"1.0.0-rc1"`
2. 创建 README 中增加"快速启动"章节（如已有则更新）
3. 给出建议的 git tag 命令（不要实际执行 `git tag`/`git push`，只输出命令）

验收标准：版本号已更新、README 含快速启动、tag 命令已给出。

---

## 三、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| devops-engineer | Dockerfile 修复与镜像构建 |
| qa-engineer | Compose 冒烟与端点验证 |
| tech-writer | 部署文档与 README |

---

## 四、必须提供的实测证据

1. 三个 `docker build` 命令完整输出摘要（尤其 final 行）
2. `docker images | grep xgboost-vis` 输出
3. `docker compose ps` 输出
4. API `/health` curl 输出
5. 前端 HTTP 状态码
6. Worker 状态 curl 输出
7. `docker compose down -v` 清理确认
8. 建议的 git tag 命令文本

---

## 五、禁止事项

- 禁止跳过 Docker 构建直接声称成功
- 禁止实际执行 `git tag` 或 `git push`（仅输出命令建议）
- 禁止删除现有 Dockerfile 重写（只允许增量修复）
- 禁止复用历史输出

---

## 六、完成判定

以下条件全部满足才算完成：

- [ ] 三个 Docker 镜像构建成功
- [ ] Docker Compose 全栈冒烟通过
- [ ] RC1_DEPLOYMENT_GUIDE.md 已创建且内容完整
- [ ] package.json version 已更新为 1.0.0-rc1
- [ ] README 含快速启动章节
- [ ] 汇报含 git tag 命令建议
