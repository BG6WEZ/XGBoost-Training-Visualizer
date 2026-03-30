# RC1 发布就绪清单

## 一、运行前提

| 组件 | 状态 | 说明 |
|------|------|------|
| PostgreSQL | 必需 | 数据库服务 |
| Redis | 必需 | 鶈息队列服务 |
| API Server | 必需 | FastAPI 服务 (端口 8000) |
| Worker | 必需 | 训练任务消费者 |

## 二、启动顺序

```bash
# 1. 启动数据库
# PostgreSQL 应已运行

# 2. 启动 Redis
# Redis 应已运行

# 3. 启动 API
cd apps/api
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. 启动 Worker
# Windows:
scripts\start-local-worker.bat

# Unix:
./scripts/start-local-worker.sh

# 5. 验证服务
python scripts/check_worker_health.py
```

## 三、最小验收命令

```bash
# 1. 回归测试
python -m pytest tests/test_queue_health_check.py tests/test_e2e_validation_regression.py --tb=short

# 2. E2E 验证
python scripts/e2e_validation.py --output json --timeout 120

# 3. RC Smoke
python scripts/rc_smoke.py

# 4. 队列治理
python scripts/queue_governance.py
```

## 四、回滚策略

1. **代码回滚**: `git checkout <previous_commit>`
2. **数据库回滚**: 
   - 备份: `pg_dump xgboost_vis > backup.sql`
   - 恢复: `psql xgboost_vis < backup.sql`
3. **配置回滚**: 恢复 `apps/api/.env` 和 `apps/worker/.env` 文件

## 五、已知风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Worker 需手动启动 | 服务重启后需手动启动 Worker | 使用启动脚本 |
| 队列积压 | 大量任务排队导致超时 | 队列治理脚本 + e2e 前置检查 |
| 无监控告警 | 异常无法及时发现 | 建议后续添加 Prometheus + Grafana |

## 六、发布建议

### 结论: **Go** ✅

### 理由:
1. **测试覆盖完整**: 18 项回归测试全部通过
2. **E2E 链路稳定**: success=true, 耗时 3.48s
3. **RC Smoke 通过**: success=true, 所有检查项通过
4. **运维工具完备**: Worker 启动脚本 + 队列治理脚本

### 后续优化建议:
1. 添加进程管理器 (PM2/systemd) 实现 Worker 自动重启
2. 添加 Prometheus 监控指标
3. 实现队列积压自动告警
