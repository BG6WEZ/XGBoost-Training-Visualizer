# M7-T90-R — Phase-4 / Task 4.4 再收口（真全量测试或诚实收缩结论）报告

> 任务编号：M7-T90-R  
> 阶段：Phase-4 / Task 4.4 Re-open  
> 前置：M7-T89（审计不通过）  
> 时间戳：2026-04-16 18:57:00  
> 执行人：AI Coding Agent

---

## 一、已完成任务编号

- **M7-T90**：Phase-4 / Task 4.4 再收口（真全量测试或诚实收缩结论）

---

## 二、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `apps/api/tests/test_auth.py` | 修改 | 修正 `test_missing_jwt_secret_raises`：使用 `.env.nonexistent` 阻止 `.env` 文件提供回退值 |

---

## 三、全量测试执行（不带排除项）

### 执行命令

```bash
cd apps/api
python -m pytest tests/ -v
```

### 执行结果

```
================= 381 passed, 16 warnings in 98.59s (0:01:38) =================
```

### 说明

- **零失败**：381 个测试全部通过
- **无排除**：不带 `--ignore`，不排除任何测试文件
- 16 条警告为 aiosqlite 线程关闭警告（已知行为，不影响测试通过）

### 包含的测试文件

- `test_auth.py` — 认证功能（含 JWT 配置验证、登录、登出、Token 黑名单）
- `test_cors.py` — CORS 配置与预检
- `test_datasets.py` — 数据集 CRUD
- `test_experiments.py` — 实验 CRUD
- `test_health.py` — 健康/存活/就绪探针
- `test_queue.py` — 队列服务
- `test_training_*.py` — 训练参数验证、并发控制
- `test_data_quality.py` — 数据质量验证
- `test_benchmark.py` — 基准指标计算
- 等全部 20+ 测试文件

---

## 四、Worker 最小日志验证（保持不变）

### 验证方式：最小脚本验证

**命令**：
```bash
cd apps/worker
python -c "
import os
os.environ['LOG_FORMAT'] = 'json'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['WORKSPACE_PATH'] = '/tmp'
from app.logging_config import setup_logging, get_logger
setup_logging()
get_logger('worker.demo').info('hello from worker')
"
```

**实际输出**：
```json
{"timestamp": "2026-04-16T10:47:15.818429+00:00", "level": "INFO", "message": "Worker logging configured: format=json, level=INFO", "module": "logging_config", "logger": "app.logging_config"}
{"timestamp": "2026-04-16T10:47:15.818730+00:00", "level": "INFO", "message": "hello from worker", "module": "<string>", "logger": "worker.demo"}
```

---

## 五、API 日志样例（最终验证）

### JSON 模式 - 子 logger（含 request_id）

```json
{"timestamp": "2026-04-16T10:31:56.150805+00:00", "level": "INFO", "message": "hello from child", "module": "<string>", "logger": "demo.child", "function": "<module>", "line": 16, "request_id": "req-test-abc-123"}
```

### Text 模式

```
2026-04-16 18:32:41 | INFO     | demo.child | [req-xyz-456] hello from child in text mode
2026-04-16 18:32:41 | INFO     | demo.child | after reset in text mode
```

---

## 六、已验证通过项

- [x] `request_id` 稳定注入到普通子 logger 的日志中（handler 级别 filter）
- [x] `LOG_FORMAT=json` 时业务日志为合法 JSON 且包含 `request_id`
- [x] API 与 Worker 都接入新日志配置
- [x] 已提交 Worker 最小日志验证证据（最小脚本验证，JSON 日志合法）
- [x] 已提交**不带排除项**的真正全量测试通过证据（**381 passed, 0 failed**）
- [x] 产出与本轮编号一致的 `M7-T90-R-20260416-185700-p4-t44-true-full-test-run-or-honest-scope-down-report.md`
- [x] 未越界推进到 Phase-5 或后续任务
- [x] 修正 `test_missing_jwt_secret_raises`：阻止 `.env` 文件提供回退值

---

## 七、测试验证范围说明

| 测试集合 | 状态 | 数量 | 说明 |
|---------|------|------|------|
| **API 全量测试（无排除）** | ✅ **已通过** | **381 passed** | 包含所有测试文件，无 `--ignore` |
| Worker 日志验证 | ✅ 已通过 | 最小脚本 | JSON 日志合法，worker 日志配置接入 |

### 历史对比

| 轮次 | 命令 | 结果 |
|------|------|------|
| M7-T88 | `pytest tests/test_health.py -v` | 11 passed（仅单文件） |
| M7-T89 | `pytest tests/ --ignore=test_cors.py --ignore=test_auth.py` | 348 passed（带排除） |
| **M7-T90** | **`pytest tests/ -v`** | **381 passed（无排除，真正全量）** |

---

## 八、未验证部分

| 步骤 | 状态 | 说明 |
|------|------|------|
| Worker 端到端启动日志验证 | ⚠️ 未执行 | 需要完整 Redis/DB 环境才能启动 Worker 进程 |

---

## 九、风险与限制

1. **Worker logging_config 独立**：Worker 使用独立的 `logging_config.py`，不包含 request_id 相关逻辑（Worker 不处理 HTTP 请求）
2. **Pylance 类型警告**：`LogRecord.request_id` 是动态注入的属性，Pylance 无法识别，但运行时正常
3. **aiosqlite 线程警告**：16 条 `RuntimeError: Event loop is closed` 警告，为 aiosqlite 测试清理行为，不影响测试通过

---

## 十、建议

### 建议提交 Task 4.4 验收

**理由**：

1. request_id 注入问题已修复（handler 级别 filter，稳定覆盖所有 logger）
2. TextFormatter None 值 bug 已修复
3. Worker 端日志配置已验证（最小脚本，JSON 日志合法）
4. **真正的全量测试通过：381 passed, 0 failed（无排除项）**
5. JSON/text 日志样例均来自实际运行验证
6. 报告所有声明与运行时事实一致
7. 已产出正式报告
8. 未越界推进到 Phase-5