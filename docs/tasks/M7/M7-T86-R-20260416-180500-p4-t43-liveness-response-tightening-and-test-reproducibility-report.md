# M7-T86-R — Phase-4 / Task 4.3 再收口（Liveness 收敛与测试可复现）报告

> 任务编号：M7-T86-R  
> 阶段：Phase-4 / Task 4.3 Re-open  
> 前置：M7-T85（审计不通过）  
> 时间戳：2026-04-16 18:05:00  
> 执行人：AI Coding Agent

---

## 一、已完成任务编号

- **M7-T86**：Phase-4 / Task 4.3 再收口（Liveness 收敛与测试可复现）

---

## 二、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `apps/api/app/routers/health.py` | 修改 | `/health` 严格收敛为 `{"status": "ok"}` |
| `apps/api/tests/test_health.py` | 修改 | 更新断言以匹配最小返回体 |

---

## 三、`/health` 最终返回体

**修改前**：
```json
{
  "status": "ok",
  "service": "xgboost-vis-api",
  "timestamp": "..."
}
```

**修改后（最终）**：
```json
{"status": "ok"}
```

**代码**：
```python
@router.get("/health")
async def liveness_check() -> dict[str, str]:
    return {"status": "ok"}
```

- 不附加 `service` 字段
- 不附加 `timestamp` 字段
- 不检查任何外部依赖

---

## 四、`/ready` 与 `/health/details` 的最终行为

### `/ready`

- 检查 database、storage、redis
- database/storage 为关键依赖，失败时返回 503
- redis 为可选依赖，失败时降级为 warning，不阻塞就绪状态
- 就绪时返回 200，包含各组件状态

### `/health/details`

- 复用现有 `get_current_admin` 依赖进行权限控制
- 非认证用户返回 401
- 非管理员用户返回 403
- 管理员返回 200，包含数据库版本、Redis 信息、存储详情等

---

## 五、测试运行环境说明

### 环境前提

| 项目 | 值 |
|------|-----|
| 操作系统 | Windows 11 |
| Python 版本 | Python 3.14.3 |
| Python 路径 | `C:\Users\wangd\project\XGBoost Training Visualizer\.venv\Scripts\python.exe` |
| 虚拟环境 | `.venv`（项目根目录下的虚拟环境） |
| 虚拟环境激活 | 测试时直接使用 `.venv\Scripts\python.exe`，无需手动激活 |
| 依赖安装方式 | 项目依赖已安装在 `.venv` 中（通过 `pip install` 或 `uv sync`） |

### 关键依赖版本

- pytest: 9.0.2
- pytest-asyncio: 1.3.0
- httpx: （用于 AsyncClient 测试）
- SQLAlchemy: （用于 AsyncSession）
- FastAPI: （用于 ASGITransport）

### 测试运行前提条件

1. `.venv` 虚拟环境存在且包含项目依赖
2. 测试使用 SQLite 内存数据库（`sqlite+aiosqlite:///:memory:`），无需外部数据库
3. 环境变量通过 `conftest.py` 自动设置
4. JWT_SECRET 在 `conftest.py` 中设置为测试值

---

## 六、依赖安装 / 激活方式

```bash
# 方式一：如果虚拟环境已存在
cd "C:\Users\wangd\project\XGBoost Training Visualizer"
.venv\Scripts\python.exe -m pytest apps/api/tests/test_health.py -v

# 方式二：激活虚拟环境后运行
cd "C:\Users\wangd\project\XGBoost Training Visualizer"
.venv\Scripts\activate
cd apps/api
python -m pytest tests/test_health.py -v
```

---

## 七、实际执行的测试命令

```bash
cd apps/api
python -m pytest tests/test_health.py -v
```

---

## 八、完整测试结果

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\wangd\project\XGBoost Training Visualizer\apps\api
configfile: pytest.ini
plugins: anyio-4.13.0, asyncio-1.3.0, cov-7.1.0
asyncio: mode=Mode.AUTO

tests/test_health.py::TestLivenessCheck::test_liveness_always_ok PASSED  [  9%]
tests/test_health.py::TestLivenessCheck::test_liveness_no_db_dependency PASSED [ 18%]
tests/test_health.py::TestReadinessCheck::test_readiness_checks_db PASSED [ 27%]
tests/test_health.py::TestReadinessCheck::test_readiness_returns_200_or_503 PASSED [ 36%]
tests/test_health.py::TestReadinessCheck::test_readiness_returns_503_when_db_unhealthy PASSED [ 45%]
tests/test_health.py::TestHealthDetails::test_details_requires_admin PASSED [ 54%]
tests/test_health.py::TestHealthDetails::test_details_returns_403_for_non_admin PASSED [ 63%]
tests/test_health.py::TestHealthDetails::test_details_returns_200_for_admin PASSED [ 72%]
tests/test_health.py::TestHealthDetails::test_details_returns_component_status PASSED [ 81%]
tests/test_health.py::TestProbeSemantics::test_health_is_liveness PASSED [ 90%]
tests/test_health.py::TestProbeSemantics::test_ready_is_readiness PASSED [100%]

============================= 11 passed in 2.55s ==============================
```

---

## 九、已验证通过项

- [x] `/health` 仅返回 `{"status": "ok"}`
- [x] `/health` 不依赖数据库或其他外部服务（`test_liveness_no_db_dependency`）
- [x] `/ready` 返回各组件状态（database, storage, redis）
- [x] `/ready` 在关键依赖失败时返回 503
- [x] `/health/details` 已实现且仅管理员可访问
- [x] `tests/test_health.py` 在可说明、可复现的环境中通过（11/11 passed）
- [x] 报告明确测试运行环境与依赖前提
- [x] 产出与本轮编号一致的 `M7-T86-R-20260416-180500-p4-t43-liveness-response-tightening-and-test-reproducibility-report.md`
- [x] 未越界推进到 Task 4.4 或后续任务

---

## 十、未验证部分

| 步骤 | 状态 | 说明 |
|------|------|------|
| K8s readiness probe 配置 | ⚠️ 未验证 | 仓库中暂无 K8s manifests，仅明确了语义映射 |
| Docker healthcheck 配置 | ⚠️ 未验证 | 仅实现 API 端点，Dockerfile/Compose 中的探针配置需在后续任务中完善 |
| 生产环境端到端测试 | ⚠️ 未验证 | 仅在 SQLite 内存数据库环境中测试 |

---

## 十一、风险与限制

1. **Redis 类型提示**：`redis.asyncio` 的 `ping()` 方法在不同版本中返回值类型不一致，代码使用了 try/except 兼容
2. **测试环境隔离**：测试使用 SQLite 内存数据库，与生产环境的 PostgreSQL 可能行为有差异
3. **探针超时配置**：API 端点已实现，但容器探针的 timeout/period 配置需在生产部署时完善

---

## 十二、建议

### 建议提交 Task 4.3 验收

**理由**：

1. `/health` 已严格收敛为 `{"status": "ok"}`，不附加任何额外字段
2. `/ready` 已实现 database、storage、redis 三项检查，支持 Redis 降级
3. `/health/details` 已实现且复用现有 `get_current_admin` 权限控制
4. 11 个测试在可复现环境中全部通过（Python 3.14.3, `.venv` 虚拟环境）
5. 报告已清楚说明测试运行环境、依赖前提、实际执行命令和完整输出
6. 已产出正式报告

**建议在提交验收前人工确认**：

- 确认 Docker Compose 中的 healthcheck 配置引用 `/health`
- 确认 K8s manifests 中的 readiness probe 引用 `/ready`