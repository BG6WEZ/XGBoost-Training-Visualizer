# M7-T68 — Task 2.3 Docker Compose 清理

> 任务编号：M7-T68  
> 阶段：Phase-2 / Task 2.3  
> 前置：M7-T67（Task 2.2 已通过）  
> 时间戳：20260415-101208

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T67-AUDIT-SUMMARY-20260415-101208.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 2.3`

---

## 一、本轮目标

进入 `Task 2.3 — Docker Compose 清理`，目标是把当前三套 compose 文件收敛到较新的 Compose 规范，并消除生产配置中的硬编码凭据。

---

## 二、允许修改的范围文件

- `docker/docker-compose.yml`
- `docker/docker-compose.prod.yml`
- `docker/docker-compose.dev.yml`
- `docker/.env.example`

如确有必要，可补充极少量与本任务直接相关的说明，但不得越界改动应用代码。

禁止越界到：

- API 代码
- Worker 代码
- 前端代码
- Alembic
- 认证逻辑

---

## 三、具体要求

### 1) 移除所有 compose 文件中的 `version`

以下文件都不得再包含 `version:` 顶层字段：

- `docker/docker-compose.yml`
- `docker/docker-compose.prod.yml`
- `docker/docker-compose.dev.yml`

### 2) `prod` compose 改为环境变量注入凭据

在 `docker/docker-compose.prod.yml` 中：

- 所有数据库密码、JWT secret、MinIO 密钥、默认管理员密码等敏感信息，都必须改为 `${VAR_NAME}` 引用
- 不得保留默认值
- 不得保留明文硬编码凭据

### 3) 新增 `docker/.env.example`

创建：

- `docker/.env.example`

要求：

- 列出 `prod` compose 需要的全部关键变量
- 变量名清晰
- 可为空占位，但不得放入真实密钥

至少应覆盖：

- 数据库连接相关
- Redis 相关
- JWT 相关
- MinIO 相关
- 默认管理员相关

### 4) `prod` compose 增加重启策略

在 `docker/docker-compose.prod.yml` 中，为长期运行服务增加：

```yaml
restart: unless-stopped
```

---

## 四、验证要求

至少完成以下命令验证，并在报告中附实际输出：

```bash
docker compose -f docker/docker-compose.yml config
docker compose -f docker/docker-compose.dev.yml config
docker compose -f docker/docker-compose.prod.yml --env-file docker/.env.example config
```

要求：

- 不出现 `version is obsolete` 或同类 warning
- `prod` compose 可成功解析

---

## 五、通过条件（全部满足才算通过）

- [ ] 三个 compose 文件均无 `version:` 行
- [ ] `prod` compose 中无硬编码密码/密钥
- [ ] `docker/.env.example` 已创建且变量齐全
- [ ] `prod` compose 中长期服务含 `restart: unless-stopped`
- [ ] 三条 `docker compose ... config` 命令可执行
- [ ] 无 Compose 配置 warning
- [ ] 未越界推进到 Task 2.4 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T68-R-<timestamp>-p2-t23-docker-compose-cleanup-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 哪些 `version:` 被移除
4. `prod` compose 中替换掉了哪些硬编码凭据
5. `docker/.env.example` 包含的关键变量清单
6. 实际执行命令
7. 实际输出原文
8. 未验证部分
9. 风险与限制
10. 是否建议进入 Task 2.4

---

## 七、明确禁止

- 不得在 `.env.example` 写入真实密钥
- 不得在 `prod` compose 保留硬编码密码
- 不得跳过 `docker compose config` 验证
- 不得提前进入 Task 2.4
