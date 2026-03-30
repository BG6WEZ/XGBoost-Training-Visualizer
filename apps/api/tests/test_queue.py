"""队列服务测试"""
import pytest
import pytest_asyncio
import os
import redis.asyncio as aioredis

# 设置测试环境
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["MINIO_ENDPOINT"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
os.environ["MINIO_SECRET_KEY"] = "minioadmin"
os.environ["DEBUG"] = "true"

from app.services.queue import QueueService, TrainingTask


async def check_redis_available():
    """检查 Redis 是否可用"""
    try:
        client = await aioredis.from_url("redis://localhost:6379/15")
        await client.ping()
        await client.close()
        return True
    except Exception:
        return False


class TestQueueService:
    """队列服务测试"""

    @pytest_asyncio.fixture
    async def queue_service(self):
        """创建队列服务"""
        # 跳过测试如果 Redis 不可用
        if not await check_redis_available():
            pytest.skip("Redis not available")

        service = QueueService("redis://localhost:6379/15")
        try:
            await service.connect()
            yield service
        finally:
            # 清理队列
            try:
                await service.redis.delete(QueueService.TRAINING_QUEUE)
            except Exception:
                pass
            await service.disconnect()

    @pytest.mark.asyncio
    async def test_enqueue_training(self, queue_service):
        """测试入队训练任务"""
        task = TrainingTask(
            experiment_id="test-exp-001",
            dataset_id="test-dataset-001",
            config={"task_type": "regression"}
        )

        task_id = await queue_service.enqueue_training(task)
        assert task_id == "test-exp-001"

        # 检查队列长度
        length = await queue_service.get_queue_length()
        assert length == 1

    @pytest.mark.asyncio
    async def test_dequeue_training(self, queue_service):
        """测试出队训练任务"""
        task = TrainingTask(
            experiment_id="test-exp-002",
            dataset_id="test-dataset-002",
            subset_id="test-subset-001",
            config={"task_type": "classification"}
        )

        await queue_service.enqueue_training(task)

        # 出队
        dequeued = await queue_service.dequeue_training(timeout=1)
        assert dequeued is not None
        assert dequeued.experiment_id == "test-exp-002"
        assert dequeued.dataset_id == "test-dataset-002"
        assert dequeued.subset_id == "test-subset-001"
        assert dequeued.config["task_type"] == "classification"

    @pytest.mark.asyncio
    async def test_queue_fifo_order(self, queue_service):
        """测试队列 FIFO 顺序"""
        for i in range(3):
            task = TrainingTask(
                experiment_id=f"exp-{i}",
                dataset_id=f"dataset-{i}",
                config={}
            )
            await queue_service.enqueue_training(task)

        # 出队应该按顺序
        for i in range(3):
            task = await queue_service.dequeue_training(timeout=1)
            assert task.experiment_id == f"exp-{i}"

    @pytest.mark.asyncio
    async def test_progress_storage(self, queue_service):
        """测试进度存储"""
        experiment_id = "test-exp-progress"
        progress = {
            "iteration": 50,
            "total": 100,
            "train_loss": 0.5,
            "val_loss": 0.6
        }

        await queue_service.set_experiment_progress(experiment_id, progress)

        retrieved = await queue_service.get_experiment_progress(experiment_id)
        assert retrieved == progress

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, queue_service):
        """测试空队列出队"""
        # 空队列，短超时
        result = await queue_service.dequeue_training(timeout=1)
        assert result is None


class TestTrainingTask:
    """训练任务模型测试"""

    def test_create_task(self):
        """测试创建训练任务"""
        task = TrainingTask(
            experiment_id="exp-001",
            dataset_id="dataset-001",
            config={"task_type": "regression", "xgboost_params": {"n_estimators": 100}}
        )

        assert task.experiment_id == "exp-001"
        assert task.dataset_id == "dataset-001"
        assert task.subset_id is None
        assert task.config["task_type"] == "regression"

    def test_create_task_with_subset(self):
        """测试创建带子集的训练任务"""
        task = TrainingTask(
            experiment_id="exp-002",
            dataset_id="dataset-001",
            subset_id="subset-001",
            config={}
        )

        assert task.subset_id == "subset-001"

    def test_task_serialization(self):
        """测试任务序列化"""
        task = TrainingTask(
            experiment_id="exp-003",
            dataset_id="dataset-003",
            config={"xgboost_params": {"lambda": 1.5}}
        )

        data = task.model_dump()
        assert data["experiment_id"] == "exp-003"
        assert data["config"]["xgboost_params"]["lambda"] == 1.5


class TestTaskVersionRaceProtection:
    """任务版本号竞态保护测试"""

    def test_version_key_format(self):
        """测试版本号键格式"""
        from app.services.queue import QueueService

        expected_prefix = "task:version:"
        assert QueueService.TASK_VERSION_PREFIX == expected_prefix

    @pytest.mark.asyncio
    async def test_version_increments_on_stop(self):
        """测试停止时版本号递增"""
        # 使用 mock Redis 测试版本号递增逻辑
        from unittest.mock import AsyncMock, MagicMock
        import json

        # 创建 mock Redis
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="1")  # 当前版本为 1
        mock_redis.incr = AsyncMock(return_value=2)  # 递增后版本为 2
        mock_redis.set = AsyncMock()
        mock_redis.rpush = AsyncMock()

        # 创建队列服务并注入 mock Redis
        queue = QueueService("redis://localhost:6379")
        queue._redis = mock_redis

        # 测试版本号递增
        new_version = await queue.increment_task_version("test-exp-001")

        # 验证返回新版本号
        assert new_version == 2

        # 验证 incr 被正确调用
        mock_redis.incr.assert_called_once_with("task:version:test-exp-001")


class TestQueueBehaviorWithoutRedis:
    """不依赖 Redis 的队列行为测试"""

    @pytest.mark.asyncio
    async def test_enqueue_dequeue_with_mock_redis(self):
        """
        测试完整的入队和出队流程（使用 mock Redis）
        
        验证：
        1. 入队时版本号正确绑定到 payload
        2. 出队时能正确解析任务
        3. FIFO 顺序正确
        """
        from unittest.mock import AsyncMock, MagicMock
        import json

        # 创建 mock Redis
        mock_redis = MagicMock()
        
        # 模拟队列数据
        queue_data = []
        
        async def mock_rpush(key, value):
            queue_data.append(value)
        
        async def mock_blpop(key, timeout=0):
            if queue_data:
                return (key, queue_data.pop(0))
            return None
        
        async def mock_llen(key):
            return len(queue_data)
        
        async def mock_get(key):
            # 模拟版本号存储
            return "1"
        
        async def mock_set(key, value, ex=None):
            pass
        
        mock_redis.rpush = AsyncMock(side_effect=mock_rpush)
        mock_redis.blpop = AsyncMock(side_effect=mock_blpop)
        mock_redis.llen = AsyncMock(side_effect=mock_llen)
        mock_redis.get = AsyncMock(side_effect=mock_get)
        mock_redis.set = AsyncMock(side_effect=mock_set)

        # 创建队列服务
        queue = QueueService("redis://localhost:6379")
        queue._redis = mock_redis

        # 测试 1: 入队任务
        task1 = TrainingTask(
            experiment_id="exp-001",
            dataset_id="dataset-001",
            config={"task_type": "regression"}
        )
        task_id1 = await queue.enqueue_training(task1)
        assert task_id1 == "exp-001"
        assert len(queue_data) == 1

        # 验证 payload 包含版本号
        payload1 = json.loads(queue_data[0])
        assert payload1["experiment_id"] == "exp-001"
        assert "task_version" in payload1
        assert payload1["task_version"] == 1

        # 测试 2: 再入队一个任务
        task2 = TrainingTask(
            experiment_id="exp-002",
            dataset_id="dataset-002",
            config={"task_type": "classification"}
        )
        await queue.enqueue_training(task2)
        assert len(queue_data) == 2

        # 测试 3: 出队验证 FIFO
        dequeued1 = await queue.dequeue_training(timeout=1)
        assert dequeued1 is not None
        assert dequeued1.experiment_id == "exp-001"
        assert dequeued1.task_version == 1

        dequeued2 = await queue.dequeue_training(timeout=1)
        assert dequeued2 is not None
        assert dequeued2.experiment_id == "exp-002"

        # 测试 4: 空队列出队返回 None
        dequeued3 = await queue.dequeue_training(timeout=1)
        assert dequeued3 is None

    @pytest.mark.asyncio
    async def test_remove_from_queue_with_mock_redis(self):
        """
        测试从队列中移除指定任务（使用 mock Redis）
        
        验证：
        1. 能正确移除指定实验的任务
        2. 其他任务保持不变
        3. 返回正确的移除状态
        """
        from unittest.mock import AsyncMock, MagicMock
        import json

        # 创建 mock Redis
        mock_redis = MagicMock()
        
        # 模拟队列数据
        queue_data = [
            json.dumps({"experiment_id": "exp-001", "dataset_id": "dataset-001", "config": {}}),
            json.dumps({"experiment_id": "exp-002", "dataset_id": "dataset-002", "config": {}}),
            json.dumps({"experiment_id": "exp-003", "dataset_id": "dataset-003", "config": {}}),
        ]
        
        async def mock_llen(key):
            return len(queue_data)
        
        async def mock_lrange(key, start, end):
            return queue_data.copy()
        
        async def mock_delete(key):
            queue_data.clear()
        
        async def mock_rpush(key, value):
            queue_data.append(value)
        
        mock_redis.llen = AsyncMock(side_effect=mock_llen)
        mock_redis.lrange = AsyncMock(side_effect=mock_lrange)
        mock_redis.delete = AsyncMock(side_effect=mock_delete)
        mock_redis.rpush = AsyncMock(side_effect=mock_rpush)

        # 创建队列服务
        queue = QueueService("redis://localhost:6379")
        queue._redis = mock_redis

        # 测试移除中间的任务
        removed = await queue.remove_from_queue("exp-002")
        assert removed is True
        
        # 验证队列中只剩 2 个任务
        assert len(queue_data) == 2
        
        # 验证剩余任务
        remaining_ids = [json.loads(task)["experiment_id"] for task in queue_data]
        assert "exp-001" in remaining_ids
        assert "exp-003" in remaining_ids
        assert "exp-002" not in remaining_ids

        # 测试移除不存在的任务
        removed = await queue.remove_from_queue("exp-999")
        assert removed is False

    @pytest.mark.asyncio
    async def test_progress_storage_with_mock_redis(self):
        """
        测试进度存储和读取（使用 mock Redis）
        
        验证：
        1. 进度能正确存储
        2. 进度能正确读取
        3. 数据格式正确
        """
        from unittest.mock import AsyncMock, MagicMock
        import json

        # 创建 mock Redis
        mock_redis = MagicMock()
        storage = {}
        
        async def mock_set(key, value, ex=None):
            storage[key] = value
        
        async def mock_get(key):
            return storage.get(key)
        
        mock_redis.set = AsyncMock(side_effect=mock_set)
        mock_redis.get = AsyncMock(side_effect=mock_get)

        # 创建队列服务
        queue = QueueService("redis://localhost:6379")
        queue._redis = mock_redis

        # 测试存储进度
        progress = {
            "iteration": 50,
            "total": 100,
            "train_loss": 0.5,
            "val_loss": 0.6
        }
        await queue.set_experiment_progress("exp-001", progress)

        # 测试读取进度
        retrieved = await queue.get_experiment_progress("exp-001")
        assert retrieved == progress

        # 测试读取不存在的进度
        not_found = await queue.get_experiment_progress("exp-999")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_task_cancellation_race_condition(self):
        """
        测试任务取消的竞态条件（核心测试）
        
        场景：
        1. 任务入队（版本 1）
        2. 用户停止任务（版本递增到 2）
        3. Worker 消费任务时检测到版本不匹配
        4. 任务被正确拒绝
        
        这是队列系统最重要的竞态保护测试
        """
        from unittest.mock import AsyncMock, MagicMock
        import json

        # 创建 mock Redis
        mock_redis = MagicMock()
        version_storage = {"task:version:exp-001": "1"}
        
        async def mock_get(key):
            return version_storage.get(key)
        
        async def mock_set(key, value, ex=None):
            version_storage[key] = value
        
        async def mock_incr(key):
            current = int(version_storage.get(key, "0"))
            new_value = current + 1
            version_storage[key] = str(new_value)
            return new_value
        
        async def mock_rpush(key, value):
            pass
        
        mock_redis.get = AsyncMock(side_effect=mock_get)
        mock_redis.set = AsyncMock(side_effect=mock_set)
        mock_redis.incr = AsyncMock(side_effect=mock_incr)
        mock_redis.rpush = AsyncMock(side_effect=mock_rpush)

        # 创建队列服务
        queue = QueueService("redis://localhost:6379")
        queue._redis = mock_redis

        # 步骤 1: 任务入队（版本 1）
        task = TrainingTask(
            experiment_id="exp-001",
            dataset_id="dataset-001",
            config={"task_type": "regression"}
        )
        await queue.enqueue_training(task)

        # 验证入队时版本号为 1
        assert version_storage["task:version:exp-001"] == "1"

        # 步骤 2: 用户停止任务（版本递增到 2）
        new_version = await queue.increment_task_version("exp-001")
        assert new_version == 2
        assert version_storage["task:version:exp-001"] == "2"

        # 步骤 3: Worker 检查任务是否被取消
        # 使用旧版本号（1）检查，应该返回 True（已取消）
        is_cancelled = await queue.check_task_cancelled("exp-001", expected_version=1)
        assert is_cancelled is True, "任务版本 1 应该被判定为已取消"

        # 步骤 4: 如果重新入队，应该使用新版本号（2）
        await queue.enqueue_training(task)
        # 版本号应该仍然是 2（因为已经存在）
        current_version = await queue.get_task_version("exp-001")
        assert current_version == 2

        # 使用新版本号检查，应该返回 False（有效）
        is_cancelled_new = await queue.check_task_cancelled("exp-001", expected_version=2)
        assert is_cancelled_new is False, "任务版本 2 应该被判定为有效"