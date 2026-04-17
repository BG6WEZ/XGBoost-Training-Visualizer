"""Redis 队列服务"""
import json
import redis.asyncio as redis
from typing import Optional, Any, Dict, List
from pydantic import BaseModel

from app.config import settings


class TrainingTask(BaseModel):
    """训练任务"""
    experiment_id: str
    dataset_id: str
    subset_id: Optional[str] = None
    config: dict
    task_version: int = 0  # 入队时的版本号，用于竞态保护


class QueueStats(BaseModel):
    """队列统计"""
    running_count: int
    queued_count: int
    max_concurrency: int
    available_slots: int


class QueueService:
    """Redis 队列服务"""

    TRAINING_QUEUE = "training:queue"
    EXPERIMENT_STATUS_CHANNEL = "experiment:status"
    TASK_VERSION_PREFIX = "task:version:"  # 任务版本号，用于竞态保护
    RUNNING_TASKS_SET = "training:running"  # 正在运行的任务集合
    QUEUE_POSITION_PREFIX = "queue:position:"  # 队列位置前缀

    def __init__(self, redis_url: str, max_concurrency: int = None):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._max_concurrency = max_concurrency or settings.TRAINING_MAX_CONCURRENCY

    async def connect(self):
        """连接 Redis"""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def disconnect(self):
        """断开连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    @property
    def redis(self) -> redis.Redis:
        if self._redis is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis

    async def enqueue_training(self, task: TrainingTask) -> str:
        """
        将训练任务加入队列

        版本号绑定到 payload，用于竞态检查：
        - 入队时获取当前版本号并写入 payload
        - worker 消费时比较 payload 内版本与 Redis 当前版本

        Returns:
            任务 ID (experiment_id)
        """
        # 获取当前版本号，不存在则从 1 开始
        version_key = f"{self.TASK_VERSION_PREFIX}{task.experiment_id}"
        current_version = await self.redis.get(version_key)
        task_version = int(current_version) if current_version else 1

        # 如果是新任务，设置初始版本号
        if not current_version:
            await self.redis.set(version_key, 1, ex=86400)  # 24小时过期

        # 把版本号绑定到 payload
        task_data = task.model_dump()
        task_data["task_version"] = task_version

        await self.redis.rpush(
            self.TRAINING_QUEUE,
            json.dumps(task_data)
        )
        return task.experiment_id

    async def get_task_version(self, experiment_id: str) -> int:
        """获取任务版本号"""
        version_key = f"{self.TASK_VERSION_PREFIX}{experiment_id}"
        version = await self.redis.get(version_key)
        return int(version) if version else 0

    async def increment_task_version(self, experiment_id: str) -> int:
        """
        递增任务版本号（用于取消任务）

        返回递增后的版本号
        """
        version_key = f"{self.TASK_VERSION_PREFIX}{experiment_id}"
        new_version = await self.redis.incr(version_key)
        return new_version

    async def check_task_cancelled(self, experiment_id: str, expected_version: int) -> bool:
        """
        检查任务是否被取消

        如果当前版本号 > expected_version，说明任务已被取消

        Args:
            experiment_id: 实验 ID
            expected_version: 期望的版本号

        Returns:
            True 表示任务已被取消
        """
        current_version = await self.get_task_version(experiment_id)
        return current_version > expected_version

    async def dequeue_training(self, timeout: int = 0) -> Optional[TrainingTask]:
        """
        从队列获取训练任务

        Args:
            timeout: 阻塞超时时间（秒），0 表示无限等待

        Returns:
            训练任务或 None
        """
        result = await self.redis.blpop(self.TRAINING_QUEUE, timeout=timeout)
        if result is None:
            return None

        _, data = result
        return TrainingTask(**json.loads(data))

    async def get_queue_length(self) -> int:
        """获取队列长度"""
        return await self.redis.llen(self.TRAINING_QUEUE)

    async def remove_from_queue(self, experiment_id: str) -> bool:
        """
        从队列中移除指定实验的任务

        Args:
            experiment_id: 实验 ID

        Returns:
            是否成功移除
        """
        # 获取队列中所有任务
        queue_length = await self.redis.llen(self.TRAINING_QUEUE)
        if queue_length == 0:
            return False

        # 读取所有任务
        tasks = await self.redis.lrange(self.TRAINING_QUEUE, 0, -1)

        # 过滤掉要移除的任务
        remaining_tasks = []
        removed = False
        for task_data in tasks:
            task_dict = json.loads(task_data)
            if task_dict.get("experiment_id") == experiment_id:
                removed = True
            else:
                remaining_tasks.append(task_data)

        if removed:
            # 删除原队列
            await self.redis.delete(self.TRAINING_QUEUE)
            # 重新添加剩余任务
            if remaining_tasks:
                for task in remaining_tasks:
                    await self.redis.rpush(self.TRAINING_QUEUE, task)

        return removed

    async def publish_status(self, experiment_id: str, status: str, **kwargs):
        """发布实验状态更新"""
        message = {
            "experiment_id": experiment_id,
            "status": status,
            **kwargs
        }
        await self.redis.publish(
            self.EXPERIMENT_STATUS_CHANNEL,
            json.dumps(message)
        )

    async def set_experiment_progress(self, experiment_id: str, progress: dict):
        """设置实验进度"""
        key = f"experiment:{experiment_id}:progress"
        await self.redis.set(key, json.dumps(progress), ex=3600)  # 1小时过期

    async def get_experiment_progress(self, experiment_id: str) -> Optional[dict]:
        """获取实验进度"""
        key = f"experiment:{experiment_id}:progress"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    @property
    def max_concurrency(self) -> int:
        """获取最大并发数"""
        return self._max_concurrency

    async def get_running_count(self) -> int:
        """获取当前运行中的任务数"""
        return await self.redis.scard(self.RUNNING_TASKS_SET)

    async def get_queued_count(self) -> int:
        """获取当前排队中的任务数"""
        return await self.redis.llen(self.TRAINING_QUEUE)

    async def get_available_slots(self) -> int:
        """获取可用槽位数"""
        running = await self.get_running_count()
        return max(0, self._max_concurrency - running)

    async def get_queue_stats(self) -> QueueStats:
        """获取队列统计信息"""
        running_count = await self.get_running_count()
        queued_count = await self.get_queued_count()
        return QueueStats(
            running_count=running_count,
            queued_count=queued_count,
            max_concurrency=self._max_concurrency,
            available_slots=max(0, self._max_concurrency - running_count)
        )

    async def can_start_training(self) -> bool:
        """检查是否可以开始训练"""
        running = await self.get_running_count()
        return running < self._max_concurrency

    async def register_running_task(self, experiment_id: str) -> bool:
        """
        注册运行中的任务
        
        Returns:
            是否成功注册（如果槽位已满返回 False）
        """
        if not await self.can_start_training():
            return False
        await self.redis.sadd(self.RUNNING_TASKS_SET, experiment_id)
        return True

    async def unregister_running_task(self, experiment_id: str):
        """注销运行中的任务"""
        await self.redis.srem(self.RUNNING_TASKS_SET, experiment_id)

    async def get_running_tasks(self) -> List[str]:
        """获取所有运行中的任务 ID"""
        return list(await self.redis.smembers(self.RUNNING_TASKS_SET))

    async def get_queue_position(self, experiment_id: str) -> Optional[int]:
        """
        获取任务在队列中的位置
        
        Returns:
            位置（从 1 开始），如果不在队列中返回 None
        """
        tasks = await self.redis.lrange(self.TRAINING_QUEUE, 0, -1)
        for i, task_data in enumerate(tasks):
            task_dict = json.loads(task_data)
            if task_dict.get("experiment_id") == experiment_id:
                return i + 1
        return None

    async def get_all_queue_positions(self) -> Dict[str, int]:
        """获取所有排队任务的位置"""
        positions = {}
        tasks = await self.redis.lrange(self.TRAINING_QUEUE, 0, -1)
        for i, task_data in enumerate(tasks):
            task_dict = json.loads(task_data)
            exp_id = task_dict.get("experiment_id")
            if exp_id:
                positions[exp_id] = i + 1
        return positions


# 全局队列服务实例
_queue_service: Optional[QueueService] = None


async def get_queue_service() -> QueueService:
    """获取队列服务单例"""
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService(settings.REDIS_URL)
        await _queue_service.connect()
    return _queue_service