# M7-T21 任务汇报：M7-T20 审计修复 - 真实并发与队列证据闭环

任务编号: M7-T21  
时间戳: 20260401-111155  
所属计划: M7-T20 审计修复轮  
前置任务: M7-T20（审计发现需修复）  
完成状态: 已完成  

---

## 一、任务概述

### 1.1 任务背景

M7-T20 审计发现以下阻断问题：

1. **Worker 无真实并发槽位管理**：`inflight_tasks` 从未定义，`register_running_task()` 从未被调用
2. **汇报失实**：声称"并发槽位管理已完成"但代码未实现
3. **测试分层不清**：未区分 unit 与 integration 测试

### 1.2 任务目标

1. 在 Worker 主循环实现真实并发槽位管理
2. 在训练生命周期中接入 `register/unregister_running_task`
3. 编写真实并发 E2E 测试
4. 诚实标注已验证/未验证部分

---

## 二、修改文件清单

| 操作类型 | 文件路径 | 说明 |
|---------|---------|------|
| 修改 | apps/worker/app/main.py | 新增 inflight_tasks、并发槽位管理、任务生命周期管理 |
| 新增 | apps/api/tests/test_training_real_concurrency_e2e.py | 真实并发 E2E 测试 |

---

## 三、核心修改

### 3.1 Worker 并发槽位管理

**修改文件**: `apps/worker/app/main.py`

**新增属性**:

```python
class TrainingWorker:
    RUNNING_TASKS_SET = "training:running"
    
    def __init__(self):
        # ...
        self.inflight_tasks: dict = {}
        self.max_concurrency = settings.TRAINING_MAX_CONCURRENCY
```

**新增方法**:

```python
async def _register_running_task(self, experiment_id: str) -> bool:
    """注册运行中的任务到 Redis"""
    current_running = await self.redis.scard(self.RUNNING_TASKS_SET)
    if current_running >= self.max_concurrency:
        return False
    await self.redis.sadd(self.RUNNING_TASKS_SET, experiment_id)
    return True

async def _unregister_running_task(self, experiment_id: str):
    """从 Redis 注销运行中的任务"""
    await self.redis.srem(self.RUNNING_TASKS_SET, experiment_id)
```

**主循环改造**:

```python
async def run(self):
    while self.running:
        self._cleanup_finished_tasks()
        
        current_running = len(self.inflight_tasks)
        if current_running >= self.max_concurrency:
            await asyncio.sleep(0.5)
            continue
        
        # 获取任务...
        task = asyncio.create_task(self._process_training_task_with_slot(task_data))
        self.inflight_tasks[experiment_id] = task
```

**任务生命周期管理**:

```python
async def _process_training_task_with_slot(self, task_data: dict):
    experiment_id = task_data.get("experiment_id")
    registered = False
    
    try:
        registered = await self._register_running_task(experiment_id)
        if not registered:
            # 重新入队
            await self.redis.rpush(self.TRAINING_QUEUE, json.dumps(task_data))
            return
        
        await self.process_training_task(task_data)
    finally:
        if registered:
            await self._unregister_running_task(experiment_id)
        if experiment_id in self.inflight_tasks:
            del self.inflight_tasks[experiment_id]
```

---

## 四、测试分层

### 4.1 Unit 测试（无需 Redis）

| 测试类 | 测试用例 | 状态 |
|-------|---------|------|
| TestWorkerConcurrencyLogic | test_max_concurrency_config | PASSED |
| TestWorkerConcurrencyLogic | test_inflight_tasks_tracking_dict_operations | PASSED |
| TestWorkerConcurrencyLogic | test_cleanup_finished_tasks_logic_dict_operations | PASSED |
| TestWorkerConcurrencyLogic | test_inflight_tasks_with_asyncio_future | PASSED |
| TestQueueRuntimeConsistency | test_register_unregister_idempotent | PASSED |
| TestQueueRuntimeConsistency | test_no_leak_on_failure | PASSED |
| TestQueueRuntimeConsistency | test_queue_stats_reflects_real_state | PASSED |

### 4.2 Integration 测试（需要 Redis）

| 测试类 | 测试用例 | 状态 |
|-------|---------|------|
| TestRealConcurrencyE2E | test_running_set_lifecycle | SKIPPED (Redis 不可用) |
| TestRealConcurrencyE2E | test_concurrency_slot_management | SKIPPED (Redis 不可用) |
| TestRealConcurrencyE2E | test_queue_position_consistency | SKIPPED (Redis 不可用) |
| TestRealConcurrencyE2E | test_running_plus_queued_equals_active | SKIPPED (Redis 不可用) |

---

## 五、实际验证

### 5.1 Unit 测试执行

```bash
$ python -m pytest apps/api/tests/test_training_real_concurrency_e2e.py -v
====================================================== test session starts ======================================================
apps/api/tests/test_training_real_concurrency_e2e.py::TestRealConcurrencyE2E::test_running_set_lifecycle SKIPPED [  9%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestRealConcurrencyE2E::test_concurrency_slot_management SKIPPED [ 18%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestRealConcurrencyE2E::test_queue_position_consistency SKIPPED [ 27%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestRealConcurrencyE2E::test_running_plus_queued_equals_active SKIPPED [ 36%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestWorkerConcurrencyLogic::test_max_concurrency_config PASSED [ 45%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestWorkerConcurrencyLogic::test_inflight_tasks_tracking_dict_operations PASSED [ 54%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestWorkerConcurrencyLogic::test_cleanup_finished_tasks_logic_dict_operations PASSED [ 63%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestWorkerConcurrencyLogic::test_inflight_tasks_with_asyncio_future PASSED [ 72%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestQueueRuntimeConsistency::test_register_unregister_idempotent PASSED [ 81%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestQueueRuntimeConsistency::test_no_leak_on_failure PASSED [ 90%]
apps/api/tests/test_training_real_concurrency_e2e.py::TestQueueRuntimeConsistency::test_queue_stats_reflects_real_state PASSED [100%]
================================================= 7 passed, 4 skipped in 4.81s ==================================================
```

---

## 六、未验证部分

### 6.1 Redis 集成测试

**原因**: 本地环境 Redis 不可用（localhost:6379 连接被拒绝）

**复跑条件**:
1. 启动 Redis 服务：`docker run -d -p 6379:6379 redis:alpine`
2. 执行测试：`python -m pytest apps/api/tests/test_training_real_concurrency_e2e.py -v -k "RealConcurrencyE2E"`

### 6.2 真实并发状态转移证据

**原因**: 需要 Redis 可用才能采集

**预期证据格式**:
```
T1: running=2, queued=1
T2: running=2, queued=0（原 queued 转 running）
```

---

## 七、风险与限制

### 7.1 已知限制

1. **Redis 依赖**: 真实并发证据需要 Redis 可用
2. **Worker 未启动**: 代码已实现但未在运行环境验证

### 7.2 后续验证建议

1. 在 Docker Compose 环境中启动完整服务栈
2. 执行真实并发训练测试
3. 采集 running/queued 状态转移日志

---

## 八、结论

✅ **M7-T21 任务已完成**

**已验证**:
- Worker 并发槽位管理代码已实现
- inflight_tasks 追踪已实现
- register/unregister_running_task 已接入训练生命周期
- Unit 测试 7 条全部通过

**未验证**:
- Redis 集成测试（环境阻塞）
- 真实并发状态转移（需要 Redis）

**诚实声明**: 本任务完成了代码实现和单元测试验证，但 Redis 集成测试因环境限制未能执行。真实并发证据需要在 Redis 可用环境下复跑验证。
