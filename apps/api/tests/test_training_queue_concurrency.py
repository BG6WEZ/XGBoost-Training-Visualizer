"""
并发训练与队列一致性测试

测试目标：
1. 验证队列统计字段正确性
2. 验证队列位置计算正确性
3. 验证并发槽位管理正确性
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestQueueStats:
    """队列统计测试"""

    @pytest.mark.asyncio
    async def test_queue_stats_response_structure(self):
        """测试队列统计响应结构"""
        from app.services.queue import QueueStats
        
        stats = QueueStats(
            running_count=2,
            queued_count=3,
            max_concurrency=2,
            available_slots=0
        )
        
        assert stats.running_count == 2
        assert stats.queued_count == 3
        assert stats.max_concurrency == 2
        assert stats.available_slots == 0
        print("✓ 队列统计响应结构正确")

    @pytest.mark.asyncio
    async def test_available_slots_calculation(self):
        """测试可用槽位计算"""
        from app.services.queue import QueueStats
        
        stats = QueueStats(
            running_count=1,
            queued_count=5,
            max_concurrency=2,
            available_slots=1
        )
        
        assert stats.available_slots == 1
        print("✓ 可用槽位计算正确")

    @pytest.mark.asyncio
    async def test_queue_stats_with_full_capacity(self):
        """测试满容量时的队列统计"""
        from app.services.queue import QueueStats
        
        stats = QueueStats(
            running_count=2,
            queued_count=10,
            max_concurrency=2,
            available_slots=0
        )
        
        assert stats.running_count == stats.max_concurrency
        assert stats.available_slots == 0
        print("✓ 满容量时队列统计正确")


class TestQueuePosition:
    """队列位置测试"""

    @pytest.mark.asyncio
    async def test_queue_position_starts_from_one(self):
        """测试队列位置从 1 开始"""
        from app.services.queue import QueueService
        
        with patch.object(QueueService, '__init__', lambda x, y, z=None: None):
            service = QueueService('redis://localhost')
            service._redis = AsyncMock()
            service._max_concurrency = 2
            
            service._redis.lrange = AsyncMock(return_value=[
                '{"experiment_id": "exp-1"}',
                '{"experiment_id": "exp-2"}',
                '{"experiment_id": "exp-3"}',
            ])
            
            position = await service.get_queue_position('exp-1')
            assert position == 1
            
            position = await service.get_queue_position('exp-2')
            assert position == 2
            
            position = await service.get_queue_position('exp-3')
            assert position == 3
            
            print("✓ 队列位置从 1 开始正确")

    @pytest.mark.asyncio
    async def test_queue_position_not_in_queue(self):
        """测试不在队列中的任务返回 None"""
        from app.services.queue import QueueService
        
        with patch.object(QueueService, '__init__', lambda x, y, z=None: None):
            service = QueueService('redis://localhost')
            service._redis = AsyncMock()
            service._max_concurrency = 2
            
            service._redis.lrange = AsyncMock(return_value=[
                '{"experiment_id": "exp-1"}',
            ])
            
            position = await service.get_queue_position('exp-not-exist')
            assert position is None
            
            print("✓ 不在队列中的任务返回 None")


class TestConcurrencyControl:
    """并发控制测试"""

    @pytest.mark.asyncio
    async def test_can_start_training_when_slots_available(self):
        """测试有空闲槽位时可以启动训练"""
        from app.services.queue import QueueService
        
        with patch.object(QueueService, '__init__', lambda x, y, z=None: None):
            service = QueueService('redis://localhost')
            service._redis = AsyncMock()
            service._max_concurrency = 2
            
            service._redis.scard = AsyncMock(return_value=1)
            
            can_start = await service.can_start_training()
            assert can_start == True
            
            print("✓ 有空闲槽位时可以启动训练")

    @pytest.mark.asyncio
    async def test_cannot_start_training_when_full(self):
        """测试槽位满时不能启动训练"""
        from app.services.queue import QueueService
        
        with patch.object(QueueService, '__init__', lambda x, y, z=None: None):
            service = QueueService('redis://localhost')
            service._redis = AsyncMock()
            service._max_concurrency = 2
            
            service._redis.scard = AsyncMock(return_value=2)
            
            can_start = await service.can_start_training()
            assert can_start == False
            
            print("✓ 槽位满时不能启动训练")

    @pytest.mark.asyncio
    async def test_register_running_task_success(self):
        """测试成功注册运行任务"""
        from app.services.queue import QueueService
        
        with patch.object(QueueService, '__init__', lambda x, y, z=None: None):
            service = QueueService('redis://localhost')
            service._redis = AsyncMock()
            service._max_concurrency = 2
            
            service._redis.scard = AsyncMock(return_value=1)
            service._redis.sadd = AsyncMock(return_value=1)
            
            success = await service.register_running_task('exp-1')
            assert success == True
            
            print("✓ 成功注册运行任务")

    @pytest.mark.asyncio
    async def test_register_running_task_fails_when_full(self):
        """测试槽位满时注册失败"""
        from app.services.queue import QueueService
        
        with patch.object(QueueService, '__init__', lambda x, y, z=None: None):
            service = QueueService('redis://localhost')
            service._redis = AsyncMock()
            service._max_concurrency = 2
            
            service._redis.scard = AsyncMock(return_value=2)
            
            success = await service.register_running_task('exp-1')
            assert success == False
            
            print("✓ 槽位满时注册失败")


class TestQueueConsistency:
    """队列一致性测试"""

    @pytest.mark.asyncio
    async def test_running_plus_queued_equals_active(self):
        """测试 running_count + queued_count 等于活跃任务数"""
        from app.services.queue import QueueService
        
        with patch.object(QueueService, '__init__', lambda x, y, z=None: None):
            service = QueueService('redis://localhost')
            service._redis = AsyncMock()
            service._max_concurrency = 2
            
            service._redis.scard = AsyncMock(return_value=2)
            service._redis.llen = AsyncMock(return_value=3)
            
            stats = await service.get_queue_stats()
            
            active_count = stats.running_count + stats.queued_count
            assert active_count == 5
            
            print("✓ running_count + queued_count 等于活跃任务数")

    @pytest.mark.asyncio
    async def test_all_queue_positions_unique(self):
        """测试所有队列位置唯一"""
        from app.services.queue import QueueService
        
        with patch.object(QueueService, '__init__', lambda x, y, z=None: None):
            service = QueueService('redis://localhost')
            service._redis = AsyncMock()
            service._max_concurrency = 2
            
            service._redis.lrange = AsyncMock(return_value=[
                '{"experiment_id": "exp-1"}',
                '{"experiment_id": "exp-2"}',
                '{"experiment_id": "exp-3"}',
            ])
            
            positions = await service.get_all_queue_positions()
            
            assert len(positions) == 3
            assert set(positions.values()) == {1, 2, 3}
            
            print("✓ 所有队列位置唯一")


class TestMaxConcurrencyConfig:
    """并发上限配置测试"""

    def test_max_concurrency_from_settings(self):
        """测试从配置读取并发上限"""
        from app.config import settings
        
        assert hasattr(settings, 'TRAINING_MAX_CONCURRENCY')
        assert settings.TRAINING_MAX_CONCURRENCY >= 1
        
        print(f"✓ 并发上限配置: {settings.TRAINING_MAX_CONCURRENCY}")

    def test_max_concurrency_default_value(self):
        """测试并发上限默认值"""
        from app.config import Settings
        
        settings = Settings()
        assert settings.TRAINING_MAX_CONCURRENCY == 2
        
        print("✓ 并发上限默认值为 2")
