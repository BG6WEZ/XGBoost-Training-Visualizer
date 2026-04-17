"""
XGBoost 训练 Worker

独立进程，从 Redis 队列消费训练任务
"""
import asyncio
import logging
import json
import signal
import os
import uuid
from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NotSupportedError

from app.config import settings
from app.logging_config import setup_logging, get_logger
from app.models import (
    Dataset, DatasetFile, Experiment, Model,
    FeatureImportance, TrainingMetric, TrainingLog,
    ExperimentStatus, AsyncTask, ModelVersion
)
from app.tasks.training import run_training_task, run_preprocessing_task, run_feature_engineering_task
from app.storage import init_storage_service, get_storage_service

# Initialize structured logging
setup_logging()
logger = get_logger(__name__)


def _is_invalid_cached_statement_error(error: Exception) -> bool:
    text = str(error)
    return "InvalidCachedStatementError" in text or "cached statement plan is invalid" in text


class TrainingWorker:
    """训练任务 Worker"""

    TRAINING_QUEUE = "training:queue"
    PREPROCESSING_QUEUE = "preprocessing:queue"
    FEATURE_ENGINEERING_QUEUE = "feature_engineering:queue"
    RUNNING_TASKS_SET = "training:running"

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.db_session_maker: Optional[async_sessionmaker] = None
        self.db_engine = None
        self.running = False
        self.inflight_tasks: dict = {}
        self.max_concurrency = settings.MAX_CONCURRENT_TRAININGS

    async def connect(self):
        """初始化连接"""
        logger.info("Initializing connections...")

        # Redis
        self.redis = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Redis connected")

        # 数据库
        db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        self.db_engine = create_async_engine(db_url, echo=settings.DEBUG)
        self.db_session_maker = async_sessionmaker(
            self.db_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("Database connected")

        # 初始化存储服务
        storage_type = os.getenv("STORAGE_TYPE", "local")
        init_storage_service(
            storage_type=storage_type,
            local_base_path=settings.WORKSPACE_DIR,
            minio_endpoint=settings.MINIO_ENDPOINT,
            minio_access_key=settings.MINIO_ACCESS_KEY,
            minio_secret_key=settings.MINIO_SECRET_KEY,
            minio_bucket=settings.MINIO_BUCKET,
            minio_secure=settings.MINIO_SECURE
        )
        logger.info(f"Storage service initialized: {storage_type}")

        # 工作目录
        os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)

    async def disconnect(self):
        """断开连接"""
        if self.redis:
            await self.redis.close()
        if self.db_engine:
            await self.db_engine.dispose()
        logger.info("Connections closed")

    async def update_experiment_status(
        self,
        experiment_id: str,
        status: str,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None
    ):
        """更新实验状态"""
        async with self.db_session_maker() as db:
            result = await db.execute(
                select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
            )
            experiment = result.scalar_one_or_none()
            if experiment:
                experiment.status = status
                experiment.updated_at = datetime.utcnow()
                if error_message:
                    experiment.error_message = error_message
                if started_at:
                    experiment.started_at = started_at
                if finished_at:
                    experiment.finished_at = finished_at
                await db.commit()
                logger.info(f"Experiment {experiment_id} status updated to {status}")

    async def update_async_task_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None,
        result: Optional[dict] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None
    ):
        """更新异步任务状态到数据库"""
        async with self.db_session_maker() as db:
            db_result = await db.execute(
                select(AsyncTask).where(AsyncTask.id == uuid.UUID(task_id))
            )
            async_task = db_result.scalar_one_or_none()
            if async_task:
                async_task.status = status
                if error_message:
                    async_task.error_message = error_message
                if result:
                    async_task.result = result
                if started_at:
                    async_task.started_at = started_at
                if finished_at:
                    async_task.finished_at = finished_at
                await db.commit()
                logger.info(f"AsyncTask {task_id} status updated to {status}")
            else:
                logger.warning(f"AsyncTask {task_id} not found in database")

    async def get_dataset_info(self, dataset_id: str) -> dict:
        """获取数据集信息"""
        async with self.db_session_maker() as db:
            dataset_query = (
                select(Dataset)
                .options(selectinload(Dataset.files))
                .where(Dataset.id == uuid.UUID(dataset_id))
            )

            for attempt in range(2):
                try:
                    result = await db.execute(dataset_query)
                    break
                except NotSupportedError as e:
                    if attempt == 0 and _is_invalid_cached_statement_error(e):
                        logger.warning(
                            "Detected stale prepared statement cache while querying dataset %s, retrying once...",
                            dataset_id,
                        )
                        await db.rollback()
                        continue
                    raise

            dataset = result.scalar_one_or_none()
            if not dataset:
                raise ValueError(f"Dataset not found: {dataset_id}")

            # 获取主文件
            primary_file = next(
                (f for f in dataset.files if f.role == "primary"),
                dataset.files[0] if dataset.files else None
            )

            return {
                "file_path": primary_file.file_path if primary_file else None,
                "target_column": dataset.target_column,
                "name": dataset.name
            }

    async def save_training_result(self, experiment_id: str, result: dict) -> Optional[uuid.UUID]:
        """保存训练结果到数据库（通过存储适配层保存模型）
        
        Returns:
            model_id: 创建的模型ID，用于后续版本创建
        """
        storage = get_storage_service()
        model_format = result.get("model_format", "json")
        model_path = result.get("model_path")

        storage_info = None
        if model_path and os.path.exists(model_path):
            storage_info = await storage.save_model_from_path(
                experiment_id=experiment_id,
                file_path=model_path,
                format=model_format
            )
            logger.info(f"Model saved via storage adapter: {storage_info}")

        async with self.db_session_maker() as db:
            model_id = None
            if storage_info:
                model = Model(
                    experiment_id=uuid.UUID(experiment_id),
                    storage_type=storage_info["storage_type"],
                    object_key=storage_info["object_key"],
                    format=model_format,
                    file_size=storage_info["file_size"],
                    metrics=result.get("metrics")
                )
                db.add(model)
                await db.flush()
                model_id = model.id

            feature_importance = result.get("feature_importance", [])
            for rank, fi in enumerate(feature_importance, start=1):
                feature_imp = FeatureImportance(
                    experiment_id=uuid.UUID(experiment_id),
                    feature_name=fi["feature"],
                    importance=fi["importance"],
                    rank=rank
                )
                db.add(feature_imp)

            training_metrics = result.get("training_metrics", [])
            for metric in training_metrics:
                training_metric = TrainingMetric(
                    experiment_id=uuid.UUID(experiment_id),
                    iteration=metric["iteration"],
                    train_loss=metric.get("train_loss"),
                    val_loss=metric.get("val_loss")
                )
                db.add(training_metric)

            await db.commit()
            logger.info(f"Training results saved for {experiment_id}")
            
            return model_id

    async def _create_model_version(
        self,
        db: AsyncSession,
        experiment_id: str,
        result: dict,
        model_id: Optional[uuid.UUID]
    ):
        """自动创建模型版本快照
        
        前置条件：实验状态必须为 completed
        语义：版本创建发生在实验状态进入 completed 之后
        """
        exp_result = await db.execute(
            select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
        )
        experiment = exp_result.scalar_one_or_none()
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found, skipping version creation")
            return

        # 验证实验状态为 completed（语义闭环）
        if experiment.status != ExperimentStatus.completed.value:
            logger.warning(
                f"Experiment {experiment_id} status is {experiment.status}, "
                f"not completed, skipping version creation"
            )
            return

        version_result = await db.execute(
            select(ModelVersion).where(ModelVersion.experiment_id == uuid.UUID(experiment_id))
        )
        existing_versions = version_result.scalars().all()
        version_number = self._generate_version_number(len(existing_versions))

        active_result = await db.execute(
            select(ModelVersion).where(
                ModelVersion.experiment_id == uuid.UUID(experiment_id),
                ModelVersion.is_active == 1
            )
        )
        previous_active = active_result.scalar_one_or_none()
        if previous_active:
            previous_active.is_active = 0

        version = ModelVersion(
            experiment_id=uuid.UUID(experiment_id),
            version_number=version_number,
            config_snapshot=experiment.config or {},
            metrics_snapshot=result.get("metrics", {}),
            tags=[],
            is_active=1,
            source_model_id=model_id,
        )
        db.add(version)
        await db.commit()

        logger.info(
            f"Created model version {version_number} for experiment {experiment_id} "
            f"(experiment_status={experiment.status})"
        )

    def _generate_version_number(self, existing_count: int) -> str:
        """生成版本号 v{major}.{minor}.{patch}"""
        major = 1
        minor = existing_count
        patch = 0
        return f"v{major}.{minor}.{patch}"

    async def run(self):
        """主循环 - 支持并发训练"""
        await self.connect()
        self.running = True

        logger.info(f"Worker started with max_concurrency={self.max_concurrency}, waiting for tasks...")

        while self.running:
            try:
                self._cleanup_finished_tasks()

                current_running = len(self.inflight_tasks)
                if current_running >= self.max_concurrency:
                    await asyncio.sleep(0.5)
                    continue

                result = await self.redis.blpop(
                    [self.TRAINING_QUEUE, self.PREPROCESSING_QUEUE, self.FEATURE_ENGINEERING_QUEUE],
                    timeout=1
                )

                if result:
                    queue_name, data = result
                    task_data = json.loads(data)

                    if queue_name == self.TRAINING_QUEUE:
                        task = asyncio.create_task(self._process_training_task_with_slot(task_data))
                        experiment_id = task_data.get("experiment_id")
                        if experiment_id:
                            self.inflight_tasks[experiment_id] = task
                    elif queue_name == self.PREPROCESSING_QUEUE:
                        asyncio.create_task(self.process_preprocessing_task(task_data))
                    elif queue_name == self.FEATURE_ENGINEERING_QUEUE:
                        asyncio.create_task(self.process_feature_engineering_task(task_data))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(1)

        if self.inflight_tasks:
            logger.info(f"Waiting for {len(self.inflight_tasks)} inflight tasks to complete...")
            await asyncio.gather(*self.inflight_tasks.values(), return_exceptions=True)

        logger.info("Worker stopped")

    def _cleanup_finished_tasks(self):
        """清理已完成的任务"""
        finished = [exp_id for exp_id, task in self.inflight_tasks.items() if task.done()]
        for exp_id in finished:
            try:
                task = self.inflight_tasks.pop(exp_id)
                if task.exception():
                    logger.error(f"Inflight task {exp_id} failed: {task.exception()}")
            except Exception as e:
                logger.warning(f"Error cleaning up task {exp_id}: {e}")

    async def _process_training_task_with_slot(self, task_data: dict):
        """带槽位管理的训练任务处理"""
        experiment_id = task_data.get("experiment_id")
        registered = False

        try:
            registered = await self._register_running_task(experiment_id)
            if not registered:
                logger.warning(f"Failed to register running task {experiment_id}, re-queuing...")
                await self.redis.rpush(self.TRAINING_QUEUE, json.dumps(task_data))
                return

            await self.process_training_task(task_data)
        except Exception as e:
            logger.error(f"Error processing training task {experiment_id}: {e}", exc_info=True)
        finally:
            if registered:
                await self._unregister_running_task(experiment_id)
            if experiment_id in self.inflight_tasks:
                del self.inflight_tasks[experiment_id]

    async def _register_running_task(self, experiment_id: str) -> bool:
        """注册运行中的任务到 Redis"""
        try:
            current_running = await self.redis.scard(self.RUNNING_TASKS_SET)
            if current_running >= self.max_concurrency:
                return False
            await self.redis.sadd(self.RUNNING_TASKS_SET, experiment_id)
            logger.info(f"Registered running task: {experiment_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register running task {experiment_id}: {e}")
            return False

    async def _unregister_running_task(self, experiment_id: str):
        """从 Redis 注销运行中的任务"""
        try:
            await self.redis.srem(self.RUNNING_TASKS_SET, experiment_id)
            logger.info(f"Unregistered running task: {experiment_id}")
        except Exception as e:
            logger.error(f"Failed to unregister running task {experiment_id}: {e}")

    TASK_VERSION_PREFIX = "task:version:"  # 与 API 保持一致

    async def get_task_version(self, experiment_id: str) -> int:
        """获取任务版本号"""
        version_key = f"{self.TASK_VERSION_PREFIX}{experiment_id}"
        version = await self.redis.get(version_key)
        return int(version) if version else 0

    async def process_training_task(self, task_data: dict):
        """
        处理训练任务

        竞态保护机制（版本号绑定到 payload）：
        1. 入队时版本号写入 payload（task_version）
        2. 消费时比较 payload 内版本与 Redis 当前版本
        3. 如果 Redis 版本 > payload 版本，说明任务已被取消/更新，跳过执行
        4. 更新状态前再次检查版本号
        """
        experiment_id = task_data["experiment_id"]
        dataset_id = task_data["dataset_id"]
        config = task_data["config"]
        payload_version = task_data.get("task_version", 0)  # payload 内的版本号

        logger.info(f"Processing training task: experiment_id={experiment_id}, payload_version={payload_version}")

        # 获取 Redis 当前版本号
        current_version = await self.get_task_version(experiment_id)

        # 竞态检查：如果 Redis 版本 > payload 版本，任务已被取消/更新
        if current_version > payload_version:
            logger.info(
                f"Experiment {experiment_id} cancelled/updated "
                f"(payload_version={payload_version}, redis_version={current_version}), skipping"
            )
            return

        # 第一次检查：消费前检查实验状态
        async with self.db_session_maker() as db:
            result = await db.execute(
                select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
            )
            experiment = result.scalar_one_or_none()
            if not experiment:
                logger.warning(f"Experiment {experiment_id} not found, skipping")
                return
            if experiment.status != ExperimentStatus.queued.value:
                logger.info(f"Experiment {experiment_id} status is {experiment.status}, skipping")
                return

        try:
            # 竞态保护：更新状态前再次检查版本号
            version_before_update = await self.get_task_version(experiment_id)
            if version_before_update > payload_version:
                logger.info(
                    f"Experiment {experiment_id} cancelled during processing "
                    f"(payload_version={payload_version}, redis_version={version_before_update}), skipping"
                )
                return

            # 更新状态为运行中
            async with self.db_session_maker() as db:
                result = await db.execute(
                    select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
                )
                experiment = result.scalar_one_or_none()

                if not experiment:
                    logger.warning(f"Experiment {experiment_id} not found during status update")
                    return

                # 双重检查状态
                if experiment.status != ExperimentStatus.queued.value:
                    logger.info(f"Experiment {experiment_id} status changed to {experiment.status}, skipping")
                    return

                experiment.status = ExperimentStatus.running.value
                experiment.started_at = datetime.utcnow()
                experiment.updated_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Experiment {experiment_id} status updated to running")

            # 获取数据集信息
            dataset_info = await self.get_dataset_info(dataset_id)
            dataset_path = dataset_info["file_path"]

            if not dataset_path or not os.path.exists(dataset_path):
                raise ValueError(f"Dataset file not found: {dataset_path}")

            # 构建训练配置
            training_config = {
                **config,
                "dataset_path": dataset_path,
                "target_column": dataset_info.get("target_column"),
                "work_dir": settings.WORKSPACE_DIR
            }

            # 执行训练
            ctx = {
                "redis": self.redis,
                "db_session_maker": self.db_session_maker
            }

            result = await run_training_task(ctx, experiment_id, training_config)

            if result.get("status") == "completed":
                # 保存结果到数据库（返回 model_id 用于版本创建）
                model_id = await self.save_training_result(experiment_id, result)

                # 更新状态为完成（先更新状态，再创建版本）
                await self.update_experiment_status(
                    experiment_id,
                    "completed",
                    finished_at=datetime.utcnow()
                )
                logger.info(f"Training completed: {experiment_id}")

                # 实验状态进入 completed 后创建版本快照
                try:
                    async with self.db_session_maker() as db:
                        await self._create_model_version(
                            db, experiment_id, result, model_id
                        )
                except Exception as e:
                    logger.error(f"Failed to create model version: {e}", exc_info=True)
            else:
                raise Exception(result.get("error", "Training failed"))

        except Exception as e:
            logger.error(f"Training failed for {experiment_id}: {e}", exc_info=True)
            await self.update_experiment_status(
                experiment_id,
                "failed",
                error_message=str(e),
                finished_at=datetime.utcnow()
            )

    async def process_preprocessing_task(self, task_data: dict):
        """处理预处理任务 - 结果持久化到数据库"""
        task_id = task_data.get("task_id")
        dataset_id = task_data.get("dataset_id")
        config = task_data.get("config", {})

        # 显式注入 task_id 到 config（确保存储适配器能获取正确的 task_id）
        config = {**config, "task_id": task_id}

        logger.info(f"Processing preprocessing task: task_id={task_id}, dataset_id={dataset_id}")

        # 更新状态为运行中
        await self.update_async_task_status(
            task_id,
            "running",
            started_at=datetime.utcnow()
        )

        try:
            ctx = {"redis": self.redis, "db_session_maker": self.db_session_maker}
            result = await run_preprocessing_task(ctx, dataset_id, config)

            # 持久化结果到数据库
            await self.update_async_task_status(
                task_id,
                "completed",
                result=result,
                finished_at=datetime.utcnow()
            )

            # 同时更新 Redis 用于实时通知（可选，短暂保留）
            await self.redis.set(
                f"task:{task_id}:status",
                json.dumps({"status": "completed", **result}),
                ex=3600
            )

            logger.info(f"Preprocessing task completed: task_id={task_id}")

        except Exception as e:
            logger.error(f"Preprocessing task failed: {e}", exc_info=True)

            # 持久化错误到数据库
            await self.update_async_task_status(
                task_id,
                "failed",
                error_message=str(e),
                finished_at=datetime.utcnow()
            )

            # Redis 通知
            await self.redis.set(
                f"task:{task_id}:status",
                json.dumps({"status": "failed", "error": str(e)}),
                ex=3600
            )

    async def process_feature_engineering_task(self, task_data: dict):
        """处理特征工程任务 - 结果持久化到数据库"""
        task_id = task_data.get("task_id")
        dataset_id = task_data.get("dataset_id")
        config = task_data.get("config", {})

        # 显式注入 task_id 到 config（确保存储适配器能获取正确的 task_id）
        config = {**config, "task_id": task_id}

        logger.info(f"Processing feature engineering task: task_id={task_id}, dataset_id={dataset_id}")

        # 更新状态为运行中
        await self.update_async_task_status(
            task_id,
            "running",
            started_at=datetime.utcnow()
        )

        try:
            ctx = {"redis": self.redis, "db_session_maker": self.db_session_maker}
            result = await run_feature_engineering_task(ctx, dataset_id, config)

            # 持久化结果到数据库
            await self.update_async_task_status(
                task_id,
                "completed",
                result=result,
                finished_at=datetime.utcnow()
            )

            # 同时更新 Redis 用于实时通知（可选，短暂保留）
            await self.redis.set(
                f"task:{task_id}:status",
                json.dumps({"status": "completed", **result}),
                ex=3600
            )

            logger.info(f"Feature engineering task completed: task_id={task_id}")

        except Exception as e:
            logger.error(f"Feature engineering task failed: {e}", exc_info=True)

            # 持久化错误到数据库
            await self.update_async_task_status(
                task_id,
                "failed",
                error_message=str(e),
                finished_at=datetime.utcnow()
            )

            # Redis 通知
            await self.redis.set(
                f"task:{task_id}:status",
                json.dumps({"status": "failed", "error": str(e)}),
                ex=3600
            )

    def stop(self):
        """停止 Worker"""
        logger.info("Stop signal received")
        self.running = False


async def main():
    """主入口"""
    worker = TrainingWorker()

    # 信号处理（Windows 兼容）
    import sys
    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        stop_future = loop.create_future()

        def signal_handler():
            worker.stop()
            stop_future.set_result(None)

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        try:
            await worker.run()
        finally:
            await worker.disconnect()
    else:
        # Windows: 直接运行，通过 Ctrl+C 终止
        try:
            await worker.run()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            await worker.disconnect()


if __name__ == "__main__":
    asyncio.run(main())