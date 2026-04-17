"""特征工程校验测试"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
import os
import tempfile
import pandas as pd

# 设置测试环境
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["DEBUG"] = "true"

from app.main import app
from app.database import Base, get_db
from app.services.queue import get_queue_service
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


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
    mock_queue.remove_from_queue = AsyncMock(return_value=True)
    mock_queue.increment_task_version = AsyncMock(return_value=2)
    mock_queue.get_task_version = AsyncMock(return_value=1)
    mock_queue.check_task_cancelled = AsyncMock(return_value=False)
    mock_queue.redis = MagicMock()
    mock_queue.redis.rpush = AsyncMock()
    mock_queue.redis.set = AsyncMock()

    async def override_get_queue():
        yield mock_queue

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_queue_service] = override_get_queue

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 将 mock_queue 附加到 client 以便测试访问
        ac.mock_queue = mock_queue
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_csv_file():
    """创建示例 CSV 文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
            'building_id': ['A'] * 50 + ['B'] * 50,
            'energy_consumption': [100 + i * 0.5 for i in range(100)],
            'temperature': [20 + i * 0.1 for i in range(100)],
        })
        df.to_csv(f, index=False)
        file_path = f.name

    yield file_path
    os.unlink(file_path)


class TestFeatureEngineeringValidation:
    """特征工程校验测试"""

    @pytest.mark.asyncio
    async def test_feature_engineering_valid_config(self, client, sample_csv_file):
        """测试有效的特征工程配置"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征工程测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 4,
                    "file_size": 2048,
                }],
            }
        )
        dataset_id = create_response.json()["id"]

        # 触发特征工程（有效配置）
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": True,
                        "column": "timestamp",
                        "features": ["hour", "dayofweek", "month", "is_weekend"]
                    },
                    "lag_features": {
                        "enabled": True,
                        "columns": ["energy_consumption"],
                        "lags": [1, 6, 12, 24]
                    },
                    "rolling_features": {
                        "enabled": True,
                        "columns": ["energy_consumption"],
                        "windows": [3, 6, 24]
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "task_id" in data

    @pytest.mark.asyncio
    async def test_feature_engineering_invalid_time_feature(self, client, sample_csv_file):
        """测试无效的时间特征"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征工程测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 4,
                    "file_size": 2048,
                }],
            }
        )
        dataset_id = create_response.json()["id"]

        # 触发特征工程（无效时间特征）
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": True,
                        "column": "timestamp",
                        "features": ["hour", "day_of_week"]  # 无效特征
                    },
                    "lag_features": {
                        "enabled": False
                    },
                    "rolling_features": {
                        "enabled": False
                    }
                }
            }
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("time_features" in str(item.get("loc", [])) for item in error_detail)

    @pytest.mark.asyncio
    async def test_feature_engineering_missing_time_column(self, client, sample_csv_file):
        """测试缺少时间列"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征工程测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 4,
                    "file_size": 2048,
                }],
            }
        )
        dataset_id = create_response.json()["id"]

        # 触发特征工程（缺少时间列）
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": True,
                        "features": ["hour", "dayofweek"]  # 缺少 column
                    },
                    "lag_features": {
                        "enabled": False
                    },
                    "rolling_features": {
                        "enabled": False
                    }
                }
            }
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert "time_features.column is required" in str(error_detail)

    @pytest.mark.asyncio
    async def test_feature_engineering_invalid_lag_value(self, client, sample_csv_file):
        """测试无效的滞后值"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征工程测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 4,
                    "file_size": 2048,
                }],
            }
        )
        dataset_id = create_response.json()["id"]

        # 触发特征工程（无效滞后值）
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": False
                    },
                    "lag_features": {
                        "enabled": True,
                        "columns": ["energy_consumption"],
                        "lags": [1, 0, -1]  # 包含无效值
                    },
                    "rolling_features": {
                        "enabled": False
                    }
                }
            }
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert "lag value must be a positive integer" in str(error_detail)

    @pytest.mark.asyncio
    async def test_feature_engineering_invalid_window_value(self, client, sample_csv_file):
        """测试无效的窗口值"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征工程测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 4,
                    "file_size": 2048,
                }],
            }
        )
        dataset_id = create_response.json()["id"]

        # 触发特征工程（无效窗口值）
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": False
                    },
                    "lag_features": {
                        "enabled": False
                    },
                    "rolling_features": {
                        "enabled": True,
                        "columns": ["energy_consumption"],
                        "windows": [3, 0, -1]  # 包含无效值
                    }
                }
            }
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert "window value must be a positive integer" in str(error_detail)

    @pytest.mark.asyncio
    async def test_feature_engineering_missing_lag_columns(self, client, sample_csv_file):
        """测试缺少滞后特征列"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征工程测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 4,
                    "file_size": 2048,
                }],
            }
        )
        dataset_id = create_response.json()["id"]

        # 触发特征工程（缺少滞后特征列）
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": False
                    },
                    "lag_features": {
                        "enabled": True,
                        "lags": [1, 6, 12, 24]  # 缺少 columns
                    },
                    "rolling_features": {
                        "enabled": False
                    }
                }
            }
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert "lag_features.columns cannot be empty" in str(error_detail)

    @pytest.mark.asyncio
    async def test_feature_engineering_missing_rolling_columns(self, client, sample_csv_file):
        """测试缺少滚动特征列"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征工程测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 4,
                    "file_size": 2048,
                }],
            }
        )
        dataset_id = create_response.json()["id"]

        # 触发特征工程（缺少滚动特征列）
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": False
                    },
                    "lag_features": {
                        "enabled": False
                    },
                    "rolling_features": {
                        "enabled": True,
                        "windows": [3, 6, 24]  # 缺少 columns
                    }
                }
            }
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert "rolling_features.columns cannot be empty" in str(error_detail)
