import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import pandas as pd
import tempfile
import os

# 设置测试环境
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["MINIO_ENDPOINT"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
os.environ["MINIO_SECRET_KEY"] = "minioadmin"
os.environ["DEBUG"] = "true"

from app.main import app
from app.database import get_db, Base
from app.services.queue import get_queue_service


@pytest_asyncio.fixture
async def client():
    """创建测试客户端"""
    # 创建测试数据库引擎
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建测试数据库会话
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session_maker() as session:
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

        async def override_get_db():
            yield session

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
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

from app.schemas.dataset import PreprocessingRequest, PreprocessingConfig, MissingValueStrategyEnum, EncodingStrategyEnum


class TestPreprocessingValidation:
    """测试预处理配置验证"""

    def test_preprocessing_valid_config(self):
        """测试有效的预处理配置"""
        config = PreprocessingConfig(
            missing_value_strategy=MissingValueStrategyEnum.MEAN_FILL,
            encoding_strategy=EncodingStrategyEnum.ONE_HOT,
            remove_duplicates=True,
            handle_outliers=False,
            target_columns=["col1", "col2"]
        )
        request = PreprocessingRequest(
            dataset_id="test-dataset-id",
            config=config
        )
        assert request.dataset_id == "test-dataset-id"
        assert request.config.missing_value_strategy == MissingValueStrategyEnum.MEAN_FILL
        assert request.config.encoding_strategy == EncodingStrategyEnum.ONE_HOT

    def test_preprocessing_invalid_missing_value_strategy(self):
        """测试无效的缺失值处理策略"""
        with pytest.raises(ValueError):
            PreprocessingConfig(
                missing_value_strategy="invalid_strategy"
            )

    def test_preprocessing_invalid_encoding_strategy(self):
        """测试无效的编码策略"""
        with pytest.raises(ValueError):
            PreprocessingConfig(
                encoding_strategy="invalid_strategy"
            )


class TestPreprocessingEndToEnd:
    """测试预处理端到端链路"""

    @pytest.mark.asyncio
    async def test_preprocessing_end_to_end(self, client):
        """测试预处理端到端链路"""
        # 创建测试数据集
        test_data = pd.DataFrame({
            "numeric_col": [1, 2, None, 4, 5],
            "categorical_col": ["A", "B", "A", "B", "C"]
        })
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        test_data.to_csv(temp_file, index=False)
        temp_file.close()
        
        try:
            # 创建数据集
            create_response = await client.post(
                "/api/datasets/",
                json={
                    "name": "端到端测试数据集",
                    "files": [{
                        "file_path": temp_file.name,
                        "file_name": "test.csv",
                        "role": "primary",
                        "row_count": 5,
                        "column_count": 2,
                        "file_size": 100
                    }]
                }
            )
            assert create_response.status_code == 200
            dataset_id = create_response.json()["id"]
            
            # 触发预处理任务
            preprocess_response = await client.post(
                f"/api/datasets/{dataset_id}/preprocess",
                json={
                    "dataset_id": dataset_id,
                    "config": {
                        "missing_value_strategy": "mean_fill",
                        "encoding_strategy": "one_hot",
                        "target_columns": ["numeric_col", "categorical_col"]
                    }
                }
            )
            assert preprocess_response.status_code == 200
            preprocess_data = preprocess_response.json()
            task_id = preprocess_data["task_id"]
            assert task_id is not None
            assert preprocess_data["status"] == "queued"
            
            # 验证任务状态可查询（正确路径: /api/datasets/tasks/{task_id}）
            status_response = await client.get(f"/api/datasets/tasks/{task_id}")
            assert status_response.status_code == 200, \
                f"任务状态查询失败: {status_response.status_code} {status_response.text}"
            status_data = status_response.json()
            assert status_data["id"] == task_id, "返回的 task_id 与请求不一致"
            assert status_data["status"] in ["queued", "running", "completed"], \
                f"任务状态非预期值: {status_data['status']}"
            assert status_data["task_type"] == "preprocessing", \
                f"任务类型错误: {status_data['task_type']}"
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
