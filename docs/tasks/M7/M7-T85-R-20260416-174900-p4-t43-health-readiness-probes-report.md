# M7-T85-R — Phase-4 / Task 4.3 健康检查与就绪探针完善报告

> 任务编号：M7-T85-R  
> 阶段：Phase-4 / Task 4.3  
> 前置：M7-T84（Task 4.2 验收通过）  
> 时间戳：2026-04-16 17:49:00  
> 执行人：AI Coding Agent

---

## 一、已完成任务编号

- **M7-T85**：Phase-4 / Task 4.3 — 健康检查与就绪探针完善

---

## 二、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `apps/api/app/routers/health.py` | 重写 | 规范 liveness / readiness 语义，新增 `/health/details` |
| `apps/api/tests/test_health.py` | 新增 | 健康检查端点测试 |

---

## 三、`/health` 如何改为 liveness

**修改内容**：

- 移除了对数据库、存储、Redis 等外部依赖的检查
- 仅返回应用运行状态、服务名和时间戳

**响应示例**：
```json
{
  "status": "ok",
  "service": "xgboost-vis-api",
  "timestamp": "2026-04-16T09:49:00.000Z"
}
```

**语义**：
- Docker healthcheck 使用 `/health`
- 容器编排系统可通过此端点判断容器是否存活

---

## 四、`/ready` 如何返回各组件状态

**检查项**：

| 组件 | 状态 | 说明 |
|------|------|------|
| database | 关键 | 不可降级，失败时返回 503 |
| storage | 关键 | 不可降级，失败时返回 503 |
| redis | 非关键 | 可降级为 warning，不阻塞就绪状态 |

**就绪时响应 (200)**：
```json
{
  "status": "ready",
  "timestamp": "...",
  "checks": {
    "database": {"status": "ok", "message": "Connected"},
    "storage": {"status": "ok", "message": "...", "type": "..."},
    "redis": {"status": "ok", "message": "Connected"}
  }
}
```

**未就绪时响应 (503)**：
```json
{
  "status": "not_ready",
  "timestamp": "...",
  "checks": {
    "database": {"status": "error", "message": "..."},
    "storage": {"status": "error", "message": "..."},
    "redis": {"status": "warning", "message": "..."}
  }
}
```

**语义**：
- K8s readiness probe 使用 `/ready`
- 关键依赖不可用时返回 503，流量不应被路由

---

## 五、`/health/details` 的权限控制方式

**权限控制**：

- 使用 `get_current_admin` 依赖
- 需要有效的 JWT token
- 需要用户角色为 `admin`
- 非管理员返回 403 Forbidden

**返回内容**：

- 数据库版本、连接状态
- Redis 版本、内存使用、连接状态
- 存储服务类型、工作目录、健康状态
- 应用版本、服务名

**响应示例**：
```json
{
  "status": "ok",
  "timestamp": "...",
  "service": "xgboost-vis-api",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "ok", "message": "Connected", "version": "SQLite 3.x"},
    "redis": {"status": "ok", "message": "Connected", "version": "7.x", "memory_used": "1M"},
    "storage": {"status": "ok", "message": "OK", "type": "minio", "workspace": "/workspace"}
  }
}
```

---

## 六、实际执行的测试命令

```bash
cd apps/api
python -m pytest tests/test_health.py -v
```

---

## 七、测试结果

```
tests/test_health.py::TestLivenessCheck::test_liveness_always_ok PASSED
tests/test_health.py::TestLivenessCheck::test_liveness_no_db_dependency PASSED
tests/test_health.py::TestReadinessCheck::test_readiness_checks_db PASSED
tests/test_health.py::TestReadinessCheck::test_readiness_returns_200_or_503 PASSED
tests/test_health.py::TestReadinessCheck::test_readiness_returns_503_when_db_unhealthy PASSED
tests/test_health.py::TestHealthDetails::test_details_requires_admin PASSED
tests/test_health.py::TestHealthDetails::test_details_returns_403_for_non_admin PASSED
tests/test_health.py::TestHealthDetails::test_details_returns_200_for_admin PASSED
tests/test_health.py::TestHealthDetails::test_details_returns_component_status PASSED
tests/test_health.py::TestProbeSemantics::test_health_is_liveness PASSED
tests/test_health.py::TestProbeSemantics::test_ready_is_readiness PASSED

11 passed in 2.91s
```

---

## 八、已验证通过项

- [x] `/health` 不依赖任何外部服务
- [x] `/ready` 返回各组件状态（database, storage, redis）
- [x] `/health/details` 已实现且仅管理员可访问
- [x] 相关测试通过（11 个测试全部通过）
- [x] 产出与本轮编号一致的 `M7-T85-R-20260416-174900-p4-t43-health-readiness-probes-report.md`
- [x] 未越界推进到 Task 4.4 或后续任务

---

## 九、未验证部分

| 步骤 | 状态 | 说明 |
|------|------|------|
| K8s readiness probe 配置 | ⚠️ 未验证 | 仓库中暂无 K8s manifests，仅明确了语义映射 |
| Docker healthcheck 配置 | ⚠️ 未验证 | 仅实现 API 端点，Dockerfile/Compose 中的探针配置需在后续任务中完善 |

---

## 十、风险与限制

1. **Redis 类型提示**：`redis.asyncio` 的 `ping()` 方法在不同版本中返回值类型不一致，代码使用了 try/except 兼容
2. **端到端验证**：仅在 SQLite 内存数据库环境中测试，未在生产环境中验证
3. **探针超时配置**：API 端点已实现，但容器探针的 timeout/period 配置需在生产部署时完善

---

## 十一、建议

### 建议提交 Task 4.3 验收

**理由**：

1. `/health` 已改为纯 liveness 检查，不依赖任何外部服务
2. `/ready` 已实现 database、storage、redis 三项检查，支持 Redis 降级
3. `/health/details` 已实现且复用现有 `get_current_admin` 权限控制
4. 11 个测试全部通过，覆盖 liveness、readiness、admin 权限、探针语义
5. 已产出正式报告

**建议在提交验收前人工确认**：

- 确认 Docker Compose 中的 healthcheck 配置引用 `/health`
- 确认 K8s manifests 中的 readiness probe 引用 `/ready`