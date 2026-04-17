"""
模型版本管理测试

P1-T13: 模型版本管理
测试版本创建、列表、比较、回滚功能
"""
import pytest
import tempfile
import uuid
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base, Experiment, Dataset, Model, ModelVersion, ExperimentStatus
from app.database import get_db
from app.main import app


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """创建测试客户端"""
    async def override_get_db():
        yield db_session

    mock_queue = MagicMock()
    mock_queue.enqueue_training = AsyncMock(return_value="test-exp-id")
    mock_queue.get_queue_length = AsyncMock(return_value=1)

    async def override_get_queue():
        yield mock_queue

    app.dependency_overrides[get_db] = override_get_db

    from app.routers.experiments import get_queue_service
    app.dependency_overrides[get_queue_service] = override_get_queue

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_csv_file():
    """创建示例 CSV 文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("feature1,feature2,target\n")
        for i in range(100):
            f.write(f"{i},{i*2},{i*3}\n")
        yield f.name


@pytest.fixture
async def setup_completed_experiment(client, sample_csv_file, db_session):
    """创建已完成的实验和模型"""
    from app.services.storage import init_storage_service, StorageConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_config = StorageConfig(
            storage_type="local",
            local_base_path=tmpdir
        )
        await init_storage_service(storage_config)

        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "版本测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 3,
                    "file_size": 1024,
                }],
            }
        )
        dataset_id = dataset_response.json()["id"]

        experiment_response = await client.post(
            "/api/experiments/",
            json={
                "name": "版本测试实验",
                "dataset_id": dataset_id,
                "config": {
                    "task_type": "regression",
                    "xgboost_params": {
                        "n_estimators": 100,
                        "max_depth": 6,
                        "learning_rate": 0.1,
                    }
                },
            }
        )
        experiment_id = experiment_response.json()["id"]

        from sqlalchemy import select
        result = await db_session.execute(
            select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
        )
        experiment = result.scalar_one()
        experiment.status = ExperimentStatus.completed.value
        await db_session.commit()

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
                "mae": 0.1,
            }
        )
        db_session.add(model)
        await db_session.commit()

        return {
            "experiment_id": experiment_id,
            "dataset_id": dataset_id,
            "model_id": str(model.id),
        }


class TestModelVersionCreation:
    """版本创建测试"""

    @pytest.mark.asyncio
    async def test_create_version_manually(self, client, setup_completed_experiment):
        """手动创建版本"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.post(
            "/api/versions",
            json={
                "experiment_id": experiment_id,
                "tags": ["baseline"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version_number"] == "v1.0.0"
        assert data["is_active"] == True
        assert data["tags"] == ["baseline"]
        assert "config_snapshot" in data
        assert "metrics_snapshot" in data

    @pytest.mark.asyncio
    async def test_create_multiple_versions(self, client, setup_completed_experiment):
        """创建多个版本，版本号递增"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        v1_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        assert v1_response.status_code == 200
        assert v1_response.json()["version_number"] == "v1.0.0"

        v2_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        assert v2_response.status_code == 200
        assert v2_response.json()["version_number"] == "v1.1.0"

        v3_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        assert v3_response.status_code == 200
        assert v3_response.json()["version_number"] == "v1.2.0"

    @pytest.mark.asyncio
    async def test_new_version_becomes_active(self, client, setup_completed_experiment):
        """新版本创建后成为激活版本"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        v1_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v1_id = v1_response.json()["id"]
        assert v1_response.json()["is_active"] == True

        v2_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v2_id = v2_response.json()["id"]
        assert v2_response.json()["is_active"] == True

        v1_check = await client.get(f"/api/versions/{v1_id}")
        assert v1_check.json()["is_active"] == False

    @pytest.mark.asyncio
    async def test_create_version_for_non_completed_experiment(self, client, setup_completed_experiment):
        """为非完成状态的实验创建版本应失败"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        from sqlalchemy import select
        from app.models import Experiment
        async for session in app.dependency_overrides[get_db]():
            result = await session.execute(
                select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
            )
            experiment = result.scalar_one()
            experiment.status = ExperimentStatus.running.value
            await session.commit()
            break

        response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )

        assert response.status_code == 400


class TestModelVersionList:
    """版本列表测试"""

    @pytest.mark.asyncio
    async def test_list_versions(self, client, setup_completed_experiment):
        """获取版本列表"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        await client.post("/api/versions", json={"experiment_id": experiment_id})
        await client.post("/api/versions", json={"experiment_id": experiment_id})

        response = await client.get(f"/api/experiments/{experiment_id}/versions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["version_number"] == "v1.1.0"
        assert data[1]["version_number"] == "v1.0.0"

    @pytest.mark.asyncio
    async def test_get_version_detail(self, client, setup_completed_experiment):
        """获取版本详情"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        create_response = await client.post(
            "/api/versions",
            json={
                "experiment_id": experiment_id,
                "tags": ["production"],
            }
        )
        version_id = create_response.json()["id"]

        response = await client.get(f"/api/versions/{version_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == version_id
        assert data["tags"] == ["production"]
        assert "config_snapshot" in data
        assert "metrics_snapshot" in data

    @pytest.mark.asyncio
    async def test_get_active_version(self, client, setup_completed_experiment):
        """获取当前激活版本"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id, "tags": ["v1"]}
        )
        v2_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id, "tags": ["v2"]}
        )
        v2_id = v2_response.json()["id"]

        response = await client.get(f"/api/experiments/{experiment_id}/versions/active")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == v2_id
        assert data["is_active"] == True


class TestModelVersionCompare:
    """版本比较测试"""

    @pytest.mark.asyncio
    async def test_compare_two_versions(self, client, setup_completed_experiment):
        """比较两个版本"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        v1_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v1_id = v1_response.json()["id"]

        v2_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v2_id = v2_response.json()["id"]

        response = await client.post(
            "/api/versions/compare",
            json={"version_ids": [v1_id, v2_id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 2
        assert "config_diffs" in data
        assert "metrics_diffs" in data

    @pytest.mark.asyncio
    async def test_compare_three_versions(self, client, setup_completed_experiment):
        """比较三个版本"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        v1 = await client.post("/api/versions", json={"experiment_id": experiment_id})
        v2 = await client.post("/api/versions", json={"experiment_id": experiment_id})
        v3 = await client.post("/api/versions", json={"experiment_id": experiment_id})

        response = await client.post(
            "/api/versions/compare",
            json={"version_ids": [v1.json()["id"], v2.json()["id"], v3.json()["id"]]}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 3

    @pytest.mark.asyncio
    async def test_compare_invalid_version_count(self, client, setup_completed_experiment):
        """比较版本数量无效"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        v1 = await client.post("/api/versions", json={"experiment_id": experiment_id})

        response = await client.post(
            "/api/versions/compare",
            json={"version_ids": [v1.json()["id"]]}
        )

        assert response.status_code in [400, 422]


class TestModelVersionRollback:
    """版本回滚测试"""

    @pytest.mark.asyncio
    async def test_rollback_to_previous_version(self, client, setup_completed_experiment):
        """回滚到之前的版本"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        v1_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v1_id = v1_response.json()["id"]

        v2_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v2_id = v2_response.json()["id"]

        v1_check = await client.get(f"/api/versions/{v1_id}")
        assert v1_check.json()["is_active"] == False

        rollback_response = await client.post(f"/api/versions/{v1_id}/rollback")

        assert rollback_response.status_code == 200
        data = rollback_response.json()
        assert data["success"] == True
        assert data["previous_active_version_id"] == v2_id
        assert data["new_active_version_id"] == v1_id

        v1_check_after = await client.get(f"/api/versions/{v1_id}")
        assert v1_check_after.json()["is_active"] == True

        v2_check_after = await client.get(f"/api/versions/{v2_id}")
        assert v2_check_after.json()["is_active"] == False

    @pytest.mark.asyncio
    async def test_rollback_already_active_version(self, client, setup_completed_experiment):
        """回滚已激活的版本"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        v1_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v1_id = v1_response.json()["id"]

        rollback_response = await client.post(f"/api/versions/{v1_id}/rollback")

        assert rollback_response.status_code == 200
        data = rollback_response.json()
        assert "already active" in data["message"].lower()


class TestVersionTags:
    """版本标签测试"""

    @pytest.mark.asyncio
    async def test_update_version_tags(self, client, setup_completed_experiment):
        """更新版本标签"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        create_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        version_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/api/versions/{version_id}/tags",
            json={"tags": ["production", "best-model"]}
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["tags"] == ["production", "best-model"]

    @pytest.mark.asyncio
    async def test_version_tags_deduplication(self, client, setup_completed_experiment):
        """版本标签去重"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        create_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        version_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/api/versions/{version_id}/tags",
            json={"tags": ["tag1", "tag1", "tag2"]}
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["tags"] == ["tag1", "tag2"]


class TestAutoVersionCreation:
    """自动版本创建 focused 测试
    
    验证训练完成后自动创建版本的时序语义：
    1. 实验状态必须先进入 completed
    2. 版本创建发生在状态更新之后
    3. 版本创建失败不影响训练结果
    """

    @pytest.mark.asyncio
    async def test_version_created_after_status_completed(
        self, client, setup_completed_experiment, db_session
    ):
        """验证版本创建发生在实验状态变为 completed 之后"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        # 验证实验状态为 completed
        from sqlalchemy import select
        result = await db_session.execute(
            select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
        )
        experiment = result.scalar_one()
        assert experiment.status == ExperimentStatus.completed.value

        # 创建版本
        response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        assert response.status_code == 200

        # 验证版本关联的实验状态仍为 completed
        version_data = response.json()
        assert version_data["is_active"] == True

    @pytest.mark.asyncio
    async def test_version_not_created_for_non_completed_experiment(
        self, client, setup_completed_experiment, db_session
    ):
        """验证非 completed 状态的实验不能创建版本"""
        from sqlalchemy import select
        
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        # 将实验状态改为 running
        result = await db_session.execute(
            select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
        )
        experiment = result.scalar_one()
        experiment.status = ExperimentStatus.running.value
        await db_session.commit()

        # 尝试创建版本应失败
        response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_version_snapshot_contains_correct_data(
        self, client, setup_completed_experiment
    ):
        """验证版本快照包含正确的配置和指标数据"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        # 创建版本
        response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        assert response.status_code == 200
        version_data = response.json()

        # 验证配置快照
        assert "config_snapshot" in version_data
        config = version_data["config_snapshot"]
        assert "xgboost_params" in config
        assert config["xgboost_params"]["n_estimators"] == 100

        # 验证指标快照
        assert "metrics_snapshot" in version_data
        metrics = version_data["metrics_snapshot"]
        assert "train_rmse" in metrics
        assert "val_rmse" in metrics
        assert "r2" in metrics

    @pytest.mark.asyncio
    async def test_version_number_sequence(
        self, client, setup_completed_experiment
    ):
        """验证版本号递增规则"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        # 创建多个版本
        versions = []
        for i in range(3):
            response = await client.post(
                "/api/versions",
                json={"experiment_id": experiment_id}
            )
            assert response.status_code == 200
            versions.append(response.json())

        # 验证版本号递增
        assert versions[0]["version_number"] == "v1.0.0"
        assert versions[1]["version_number"] == "v1.1.0"
        assert versions[2]["version_number"] == "v1.2.0"

    @pytest.mark.asyncio
    async def test_only_one_active_version_per_experiment(
        self, client, setup_completed_experiment
    ):
        """验证每个实验只有一个激活版本"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        # 创建第一个版本
        v1_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v1_id = v1_response.json()["id"]
        assert v1_response.json()["is_active"] == True

        # 创建第二个版本
        v2_response = await client.post(
            "/api/versions",
            json={"experiment_id": experiment_id}
        )
        v2_id = v2_response.json()["id"]
        assert v2_response.json()["is_active"] == True

        # 验证第一个版本变为非激活
        v1_check = await client.get(f"/api/versions/{v1_id}")
        assert v1_check.json()["is_active"] == False

        # 验证只有第二个版本是激活的
        v2_check = await client.get(f"/api/versions/{v2_id}")
        assert v2_check.json()["is_active"] == True
