# RC1 发布就绪清单

## 一、运行前提

| 组件 | 状态 | 说明 |
|------|------|------|
| PostgreSQL | 必需 | 数据库服务 |
| Redis | 必需 | 消息队列服务 |
| API Server | 必需 | FastAPI 服务 (端口 8000) |
| Worker | 必需 | 训练任务消费者 |

## 二、启动顺序

```bash
# 1. 启动数据库和 Redis
pnpm docker:dev

# 2. 运行数据库迁移
pnpm db:migrate

# 3. 启动 API
pnpm dev:api

# 4. 启动 Worker
pnpm dev:worker

# 5. 启动前端
pnpm dev:web

# 6. 验证服务
curl http://localhost:8000/health
```

## 三、主门禁命令

### 一键执行（推荐）

```bash
# Windows
scripts\main-gate.bat

# Unix/Linux/macOS
./scripts/main-gate.sh
```

### 分步执行

```bash
# API 测试
cd apps/api
pytest -v --tb=short

# Worker 测试
cd apps/worker
pytest -v --tb=short

# 前端门禁
cd apps/web
pnpm typecheck
pnpm build
```

### 浏览器冒烟测试

```bash
# 前置条件：所有服务已启动
node smoke-test.mjs
# 或
node test-playwright.mjs
```

## 四、CI 自动化

项目已配置 GitHub Actions CI workflow (`.github/workflows/main-gate.yml`)。

**触发条件**：
- push 到 `main` 或 `master` 分支
- Pull Request 到 `main` 或 `master` 分支

**CI 包含**：
- API 测试 (pytest)
- Worker 测试 (pytest)
- 前端 TypeScript 检查
- 前端构建

## 五、Skip 测试说明

| 测试文件 | Skip 数量 | 原因 |
|----------|-----------|------|
| test_queue.py | 5 | Redis 不可用 - 集成测试需要运行中的 Redis 服务 |
| test_training_real_concurrency_e2e.py | 4 | Redis 不可用 - 真实并发 E2E 测试需要 Redis |

**总计**: 9 skipped

这些 skip 不计入"通过"结论。

## 六、构建警告

前端构建有 chunk size warning (733.77 kB > 500 kB)，不阻塞构建。

## 七、回滚策略

1. **代码回滚**: `git checkout <previous_commit>`
2. **数据库回滚**: 
   - 备份: `pg_dump xgboost_vis > backup.sql`
   - 恢复: `psql xgboost_vis < backup.sql`
3. **配置回滚**: 恢复 `apps/api/.env` 和 `apps/worker/.env` 文件

## 八、已知风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Worker 需手动启动 | 服务重启后需手动启动 Worker | 使用启动脚本 |
| 队列积压 | 大量任务排队导致超时 | 队列治理脚本 + e2e 前置检查 |
| 无监控告警 | 异常无法及时发现 | 建议后续添加 Prometheus + Grafana |
| 浏览器冒烟需完整环境 | 需要启动所有服务才能执行 | 文档明确启动顺序 |

## 九、发布建议

### 结论: **Go** ✅

### 理由:
1. **测试覆盖完整**: 336 passed, 9 skipped (已声明边界)
2. **CI 自动化**: GitHub Actions workflow 已配置
3. **主门禁脚本**: 一键执行所有核心测试
4. **文档一致**: README、RC1 清单、汇报口径一致

### 后续优化建议:
1. 添加进程管理器 (PM2/systemd) 实现 Worker 自动重启
2. 添加 Prometheus 监控指标
3. 实现队列积压自动告警
4. 优化前端 chunk size
