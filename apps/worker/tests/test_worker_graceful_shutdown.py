"""Worker graceful shutdown tests - Task 3.1 (M7-T72)

Test coverage:
- test_worker_graceful_shutdown (对应任务要求 #8)
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.main import TrainingWorker


class TestWorkerGracefulShutdown:
    """测试: test_worker_graceful_shutdown
    
    核心验证点: Worker 收到停止信号后优雅退出
    """

    @pytest.mark.asyncio
    async def test_worker_graceful_shutdown(self):
        """验证 Worker 收到停止信号后优雅退出"""
        worker = TrainingWorker()
        worker.running = True

        # 模拟停止信号
        worker.stop()

        # 验证 running 标志被设置为 False
        assert worker.running is False, "Worker should set running=False when stopped"

    @pytest.mark.asyncio
    async def test_worker_stops_running_loop_on_signal(self):
        """验证 Worker running 标志控制主循环退出"""
        worker = TrainingWorker()
        worker.running = True

        # 验证初始状态
        assert worker.running is True, "Worker should be running initially"

        # 发送停止信号
        worker.stop()

        # 验证停止后 running 为 False
        assert worker.running is False, "Worker should stop running after stop() call"

    @pytest.mark.asyncio
    async def test_worker_disconnect_closes_connections(self):
        """验证 Worker 断开连接时正确关闭资源"""
        worker = TrainingWorker()

        # Mock Redis 连接
        mock_redis = MagicMock()
        mock_redis.close = AsyncMock()
        worker.redis = mock_redis

        # Mock DB 引擎
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()
        worker.db_engine = mock_engine

        # 调用断开连接
        await worker.disconnect()

        # 验证连接被关闭
        mock_redis.close.assert_called_once()
        mock_engine.dispose.assert_called_once()