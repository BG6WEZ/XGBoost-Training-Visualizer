"""
Worker 自动版本创建 focused 测试

M7-T33: 直接绑定 TrainingWorker 生产实现
验证训练完成后自动创建版本的时序语义

重要说明：
- 本测试直接导入 apps/worker/app/main.py 中的 TrainingWorker 类
- 直接调用 TrainingWorker._create_model_version 真实实现
- 不在测试文件中复制逻辑
- 明确 mock 边界与未验证范围

测试边界：
- 已验证：TrainingWorker._create_model_version 方法的核心逻辑
- 未验证：Redis 队列消费、完整训练链路、并发安全性

Mock 边界：
- Mock 了：数据库连接（使用内存 SQLite 替代 PostgreSQL）
- Mock 了：Redis 连接（不依赖真实 Redis）
- Mock 了：存储服务（不依赖真实文件系统）
- 未 Mock：_create_model_version 方法本身的逻辑
"""
import pytest
import uuid
import os
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from unittest.mock import MagicMock, patch

from app.models import Base, Experiment, Dataset, Model, ModelVersion, ExperimentStatus


# 直接导入真实的 TrainingWorker
# 使用 importlib 动态导入，避免与 api 的 app 模块冲突
import importlib.util

# 先将 worker 目录添加到 sys.path，确保 app.tasks 等模块能被正确解析
_worker_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    '..', '..', 'worker'
))
if _worker_path not in sys.path:
    sys.path.insert(0, _worker_path)

_worker_main_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    '..', '..', 'worker', 'app', 'main.py'
))

# 动态加载 worker 的 main 模块
_spec = importlib.util.spec_from_file_location("worker_main", _worker_main_path)
_worker_main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_worker_main)

# 获取真实的 TrainingWorker 类
TrainingWorker = _worker_main.TrainingWorker


@pytest.fixture
async def db_engine():
    """创建测试数据库引擎（Mock PostgreSQL）"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session_maker(db_engine):
    """创建测试数据库会话工厂"""
    return async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def worker(db_session_maker):
    """
    创建真实的 TrainingWorker 实例，注入测试数据库
    
    重要：这是 apps/worker/app/main.py 中的真实 TrainingWorker 类，
    不是复制版本。
    
    Mock 边界：
    - redis: Mock（不依赖真实 Redis）
    - db_session_maker: 使用测试数据库（内存 SQLite）
    - 存储服务: 不初始化（_create_model_version 不依赖）
    """
    worker_instance = TrainingWorker()
    worker_instance.db_session_maker = db_session_maker
    worker_instance.redis = MagicMock()
    
    return worker_instance


class TestWorkerAutoVersionCreation:
    """
    直接测试 TrainingWorker._create_model_version 真实实现
    
    重要：本测试类直接调用 apps/worker/app/main.py 中的真实方法，
    不复制任何逻辑。
    
    测试目标：
    1. 验证版本创建发生在实验状态变为 completed 之后
    2. 验证非 completed 状态不会创建版本
    3. 验证版本快照数据正确
    4. 验证激活版本语义正确
    """

    @pytest.mark.asyncio
    async def test_worker_auto_version_created_after_completed(self, db_session_maker, worker):
        """
        验证 worker 自动版本创建发生在实验状态为 completed 之后
        
        直接调用 TrainingWorker._create_model_version 真实方法。
        """
        async with db_session_maker() as db:
            dataset = Dataset(
                name="测试数据集",
                target_column="target"
            )
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            dataset_id = dataset.id

        async with db_session_maker() as db:
            experiment = Experiment(
                dataset_id=dataset_id,
                name="测试实验",
                status=ExperimentStatus.completed.value,
                config={
                    "task_type": "regression",
                    "xgboost_params": {
                        "n_estimators": 100,
                        "max_depth": 6,
                        "learning_rate": 0.1,
                    }
                }
            )
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            experiment_id = str(experiment.id)

        async with db_session_maker() as db:
            model = Model(
                experiment_id=uuid.UUID(experiment_id),
                storage_type="local",
                object_key=f"models/{experiment_id}/model.json",
                format="json",
                file_size=2048,
                metrics={
                    "train_rmse": 0.1234,
                    "val_rmse": 0.2345,
                    "r2": 0.95,
                }
            )
            db.add(model)
            await db.commit()
            await db.refresh(model)
            model_id = model.id

        training_result = {
            "metrics": {
                "train_rmse": 0.1234,
                "val_rmse": 0.2345,
                "r2": 0.95,
            }
        }

        # 直接调用真实的 TrainingWorker._create_model_version 方法
        async with db_session_maker() as db:
            await worker._create_model_version(
                db, experiment_id, training_result, model_id
            )

        async with db_session_maker() as db:
            result = await db.execute(
                select(ModelVersion).where(ModelVersion.experiment_id == uuid.UUID(experiment_id))
            )
            version = result.scalar_one_or_none()
            
            assert version is not None, "Version should be created"
            assert version.version_number == "v1.0.0"
            assert version.is_active == 1
            assert version.config_snapshot["xgboost_params"]["n_estimators"] == 100
            assert version.metrics_snapshot["val_rmse"] == 0.2345

    @pytest.mark.asyncio
    async def test_worker_auto_version_not_created_for_non_completed(self, db_session_maker, worker):
        """
        验证 worker 不会为非 completed 状态的实验创建版本
        
        直接调用 TrainingWorker._create_model_version 真实方法。
        """
        async with db_session_maker() as db:
            dataset = Dataset(
                name="测试数据集",
                target_column="target"
            )
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            dataset_id = dataset.id

        async with db_session_maker() as db:
            experiment = Experiment(
                dataset_id=dataset_id,
                name="测试实验",
                status=ExperimentStatus.running.value,  # 非 completed
                config={"task_type": "regression"}
            )
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            experiment_id = str(experiment.id)

        # 直接调用真实的 TrainingWorker._create_model_version 方法
        async with db_session_maker() as db:
            await worker._create_model_version(
                db, experiment_id, {"metrics": {}}, None
            )

        async with db_session_maker() as db:
            result = await db.execute(
                select(ModelVersion).where(ModelVersion.experiment_id == uuid.UUID(experiment_id))
            )
            version = result.scalar_one_or_none()
            
            assert version is None, "Version should NOT be created for non-completed experiment"

    @pytest.mark.asyncio
    async def test_worker_auto_version_sequence(self, db_session_maker, worker):
        """
        验证 worker 自动创建多个版本时的版本号递增
        
        直接调用 TrainingWorker._create_model_version 真实方法。
        """
        async with db_session_maker() as db:
            dataset = Dataset(
                name="测试数据集",
                target_column="target"
            )
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            dataset_id = dataset.id

        async with db_session_maker() as db:
            experiment = Experiment(
                dataset_id=dataset_id,
                name="测试实验",
                status=ExperimentStatus.completed.value,
                config={"task_type": "regression"}
            )
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            experiment_id = str(experiment.id)

        # 模拟三次训练完成，每次调用真实的 _create_model_version
        for i in range(3):
            training_result = {
                "metrics": {
                    "train_rmse": 0.1 + i * 0.01,
                    "val_rmse": 0.2 + i * 0.01,
                    "r2": 0.95 - i * 0.01,
                }
            }
            async with db_session_maker() as db:
                await worker._create_model_version(
                    db, experiment_id, training_result, None
                )

        async with db_session_maker() as db:
            result = await db.execute(
                select(ModelVersion)
                .where(ModelVersion.experiment_id == uuid.UUID(experiment_id))
                .order_by(ModelVersion.created_at)
            )
            versions = result.scalars().all()
            
            assert len(versions) == 3
            assert versions[0].version_number == "v1.0.0"
            assert versions[1].version_number == "v1.1.0"
            assert versions[2].version_number == "v1.2.0"

            # 验证只有最后一个版本是激活的
            assert versions[0].is_active == 0
            assert versions[1].is_active == 0
            assert versions[2].is_active == 1

    @pytest.mark.asyncio
    async def test_worker_auto_version_snapshot_integrity(self, db_session_maker, worker):
        """
        验证 worker 自动创建的版本快照数据完整性
        
        直接调用 TrainingWorker._create_model_version 真实方法。
        """
        async with db_session_maker() as db:
            dataset = Dataset(
                name="测试数据集",
                target_column="target"
            )
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            dataset_id = dataset.id

        config = {
            "task_type": "regression",
            "xgboost_params": {
                "n_estimators": 200,
                "max_depth": 8,
                "learning_rate": 0.05,
            },
            "feature_engineering": {
                "normalize": True,
            }
        }

        async with db_session_maker() as db:
            experiment = Experiment(
                dataset_id=dataset_id,
                name="测试实验",
                status=ExperimentStatus.completed.value,
                config=config
            )
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            experiment_id = str(experiment.id)

        metrics = {
            "train_rmse": 0.0876,
            "val_rmse": 0.1234,
            "r2": 0.9876,
            "mae": 0.0567,
        }

        training_result = {"metrics": metrics}

        # 调用真实的 _create_model_version
        async with db_session_maker() as db:
            await worker._create_model_version(
                db, experiment_id, training_result, None
            )

        async with db_session_maker() as db:
            result = await db.execute(
                select(ModelVersion).where(ModelVersion.experiment_id == uuid.UUID(experiment_id))
            )
            version = result.scalar_one_or_none()
            
            assert version is not None
            assert version.config_snapshot == config
            assert version.metrics_snapshot == metrics

            # 验证快照中的关键字段
            assert version.config_snapshot["xgboost_params"]["n_estimators"] == 200
            assert version.config_snapshot["feature_engineering"]["normalize"] == True
            assert version.metrics_snapshot["val_rmse"] == 0.1234
            assert version.metrics_snapshot["r2"] == 0.9876
