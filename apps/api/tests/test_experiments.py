import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
import asyncio
import os
import tempfile
import pandas as pd
from unittest.mock import AsyncMock, MagicMock

# 设置测试环境
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["MINIO_ENDPOINT"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
os.environ["MINIO_SECRET_KEY"] = "minioadmin"
os.environ["DEBUG"] = "true"

from app.main import app
from app.database import Base, get_db
from app.models import Dataset, DatasetFile, Experiment
from app.services.queue import get_queue_service


@pytest_asyncio.fixture
async def db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """创建测试数据库会话"""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """创建测试客户端"""
    async def override_get_db():
        yield db_session

    # Mock queue service
    mock_queue = MagicMock()
    mock_queue.enqueue_training = AsyncMock(return_value="test-exp-id")
    mock_queue.get_queue_length = AsyncMock(return_value=1)
    mock_queue.remove_from_queue = AsyncMock(return_value=False)  # 默认返回 False（不在队列中）
    mock_queue.increment_task_version = AsyncMock(return_value=2)  # 返回新版本号
    mock_queue.get_task_version = AsyncMock(return_value=1)  # 返回当前版本号

    async def override_get_queue():
        yield mock_queue

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_queue_service] = override_get_queue

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_dataset(client):
    """创建示例数据集"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
            'value': [i * 0.5 for i in range(100)],
        })
        df.to_csv(f, index=False)
        file_path = f.name

    try:
        response = await client.post(
            "/api/datasets/",
            json={
                "name": "实验测试数据集",
                "files": [
                    {
                        "file_path": file_path,
                        "file_name": "test.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 2,
                        "file_size": 1024,
                    }
                ],
                "target_column": "value",
            }
        )
        yield response.json()
    finally:
        os.unlink(file_path)


# ========== 实验测试 ==========

class TestExperimentAPI:
    """实验 API 测试"""

    @pytest.mark.asyncio
    async def test_create_experiment(self, client, sample_dataset):
        """测试创建实验"""
        response = await client.post(
            "/api/experiments/",
            json={
                "name": "测试实验",
                "description": "这是一个测试实验",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试实验"
        assert data["description"] == "这是一个测试实验"
        assert data["dataset_id"] == sample_dataset["id"]
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_experiment_invalid_dataset(self, client):
        """测试创建实验 - 数据集不存在"""
        fake_dataset_id = "00000000-0000-0000-0000-000000000000"
        response = await client.post(
            "/api/experiments/",
            json={
                "name": "无效实验",
                "dataset_id": fake_dataset_id,
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_experiments(self, client, sample_dataset):
        """测试获取实验列表"""
        # 先创建一个实验
        await client.post(
            "/api/experiments/",
            json={
                "name": "列表测试实验",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        response = await client.get("/api/experiments/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_experiments_filter_by_status(self, client, sample_dataset):
        """测试按状态过滤实验列表"""
        # 创建实验
        await client.post(
            "/api/experiments/",
            json={
                "name": "状态过滤测试",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        response = await client.get("/api/experiments/?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert all(e["status"] == "pending" for e in data)

    @pytest.mark.asyncio
    async def test_get_experiment_detail(self, client, sample_dataset):
        """测试获取实验详情"""
        # 创建实验
        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "详情测试实验",
                "description": "测试描述",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        experiment_id = create_response.json()["id"]

        # 获取详情
        response = await client.get(f"/api/experiments/{experiment_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == experiment_id
        assert data["name"] == "详情测试实验"
        assert data["description"] == "测试描述"

    @pytest.mark.asyncio
    async def test_get_experiment_not_found(self, client):
        """测试获取不存在的实验"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/experiments/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_experiment(self, client, sample_dataset):
        """测试更新实验"""
        # 创建实验
        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "待更新实验",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        experiment_id = create_response.json()["id"]

        # 更新实验
        response = await client.patch(
            f"/api/experiments/{experiment_id}",
            json={
                "name": "更新后名称",
                "description": "新描述",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后名称"
        assert data["description"] == "新描述"

    @pytest.mark.asyncio
    async def test_start_experiment(self, client, sample_dataset):
        """测试启动实验"""
        # 创建实验
        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "待启动实验",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        experiment_id = create_response.json()["id"]

        # 启动实验
        response = await client.post(f"/api/experiments/{experiment_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"

        # 验证状态已更新
        get_response = await client.get(f"/api/experiments/{experiment_id}")
        assert get_response.json()["status"] == "queued"

    @pytest.mark.asyncio
    async def test_stop_experiment(self, client, sample_dataset):
        """测试停止实验"""
        # 创建实验
        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "待停止实验",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        experiment_id = create_response.json()["id"]

        # 先启动
        await client.post(f"/api/experiments/{experiment_id}/start")

        # 然后停止
        response = await client.post(f"/api/experiments/{experiment_id}/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_delete_experiment(self, client, sample_dataset):
        """测试删除实验"""
        # 创建实验
        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "待删除实验",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        experiment_id = create_response.json()["id"]

        # 删除实验
        response = await client.delete(f"/api/experiments/{experiment_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # 验证已删除
        get_response = await client.get(f"/api/experiments/{experiment_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_lambda_field_serialization(self, client, sample_dataset):
        """测试 lambda 字段正确序列化"""
        # 创建带 lambda 参数的实验
        response = await client.post(
            "/api/experiments/",
            json={
                "name": "Lambda测试实验",
                "dataset_id": sample_dataset["id"],
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                        "lambda": 2.5,  # 使用 lambda 作为参数名
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        # 验证 config 中的 xgboost_params 包含 lambda 而不是 lambda_
        xgb_params = data["config"]["xgboost_params"]
        assert "lambda" in xgb_params, f"Expected 'lambda' in xgboost_params, got keys: {list(xgb_params.keys())}"
        assert xgb_params["lambda"] == 2.5
        assert "lambda_" not in xgb_params, "lambda_ should not appear in response"

    @pytest.mark.asyncio
    async def test_experiment_with_subset_validation(self, client, sample_dataset):
        """测试创建实验时子集校验"""
        # 使用不存在的子集 ID
        fake_subset_id = "00000000-0000-0000-0000-000000000001"
        response = await client.post(
            "/api/experiments/",
            json={
                "name": "无效子集实验",
                "dataset_id": sample_dataset["id"],
                "subset_id": fake_subset_id,
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "random_seed": 42,
                    "xgboost_params": {
                        "learning_rate": 0.1,
                        "max_depth": 6,
                        "n_estimators": 100,
                    }
                }
            }
        )

        # 子集不存在应该返回 404
        assert response.status_code == 404
        assert "Subset not found" in response.json()["detail"]