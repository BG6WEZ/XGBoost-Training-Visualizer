"""
结果接口契约测试

覆盖以下场景：
- 成功读取已完成实验结果（200）
- 无效 experiment_id 格式（400）
- 不存在 experiment_id（404）
- 模型记录存在但文件缺失场景（404）
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from unittest.mock import MagicMock, AsyncMock
import uuid
import tempfile
import os
import json

from app.main import app
from app.database import get_db, Base
from app.models import Experiment, Dataset, DatasetFile, Model, ExperimentStatus
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
        expire_on_commit=False,
        autoflush=False,
    )
    session = async_session_maker()
    yield session
    await session.close()


@pytest.fixture
def sample_csv_file():
    """创建测试 CSV 文件"""
    import pandas as pd
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [2.0, 3.0, 4.0, 5.0, 6.0],
            'target': [10, 20, 30, 40, 50]
        })
        df.to_csv(f, index=False)
        return f.name


@pytest_asyncio.fixture
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
    app.dependency_overrides[get_queue_service] = override_get_queue

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestResultsContract:
    """结果接口契约测试"""

    @pytest.mark.asyncio
    async def test_get_results_invalid_id_format(self, client):
        """
        场景：无效 experiment_id 格式
        预期：返回 400，detail 包含 "Invalid experiment ID format"
        """
        response = await client.get("/api/results/not-a-uuid")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid experiment ID format" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_results_not_found(self, client):
        """
        场景：不存在 experiment_id
        预期：返回 404，detail 包含 "Experiment not found"
        """
        non_existent_id = str(uuid.uuid4())
        response = await client.get(f"/api/results/{non_existent_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Experiment not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_results_success_with_model(self, client, sample_csv_file, db_session):
        """
        场景：成功读取已完成实验结果（200）
        预期：
        - 状态码 200
        - 响应包含 experiment_id, experiment_name, status, model 等字段
        - model 字段包含 id, format, file_size, storage_type, object_key
        """
        # 创建数据集
        dataset = Dataset(name="契约测试数据集")
        db_session.add(dataset)
        await db_session.flush()
        
        file = DatasetFile(
            dataset_id=dataset.id,
            file_path=sample_csv_file,
            file_name="test.csv",
            role="primary",
            row_count=100,
            column_count=3,
            file_size=1024,
        )
        db_session.add(file)
        
        # 创建实验
        experiment = Experiment(
            name="契约测试实验",
            dataset_id=dataset.id,
            config={"objective": "regression", "n_estimators": 100},
            status=ExperimentStatus.completed.value,
        )
        db_session.add(experiment)
        await db_session.flush()
        
        experiment_id = str(experiment.id)
        
        # 创建模型记录
        model = Model(
            experiment_id=experiment.id,
            storage_type="local",
            object_key=f"models/{experiment_id}/model.json",
            format="json",
            file_size=2048,
            metrics={"r2": 0.95, "mae": 1.5}
        )
        db_session.add(model)
        await db_session.flush()
        
        # 调用接口
        response = await client.get(f"/api/results/{experiment_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # 契约断言：关键字段存在且类型正确
        assert "experiment_id" in data
        assert data["experiment_id"] == experiment_id
        assert isinstance(data["experiment_id"], str)
        
        assert "experiment_name" in data
        assert data["experiment_name"] == "契约测试实验"
        assert isinstance(data["experiment_name"], str)
        
        assert "status" in data
        assert data["status"] == "completed"
        assert isinstance(data["status"], str)
        
        # 契约断言：model 字段结构
        assert "model" in data
        assert data["model"] is not None
        assert "id" in data["model"]
        assert "format" in data["model"]
        assert data["model"]["format"] == "json"
        assert "file_size" in data["model"]
        assert data["model"]["file_size"] == 2048
        assert "storage_type" in data["model"]
        assert data["model"]["storage_type"] == "local"
        assert "object_key" in data["model"]
        assert experiment_id in data["model"]["object_key"]

    @pytest.mark.asyncio
    async def test_get_results_success_without_model(self, client, sample_csv_file, db_session):
        """
        场景：成功读取实验结果但无模型记录
        预期：model 字段为 None
        """
        # 创建数据集
        dataset = Dataset(name="无模型测试数据集")
        db_session.add(dataset)
        await db_session.flush()
        
        file = DatasetFile(
            dataset_id=dataset.id,
            file_path=sample_csv_file,
            file_name="test.csv",
            role="primary",
            row_count=100,
            column_count=3,
            file_size=1024,
        )
        db_session.add(file)
        
        # 创建实验（不创建模型）
        experiment = Experiment(
            name="无模型测试实验",
            dataset_id=dataset.id,
            config={"objective": "regression", "n_estimators": 100},
            status=ExperimentStatus.pending.value,
        )
        db_session.add(experiment)
        await db_session.flush()
        
        experiment_id = str(experiment.id)
        
        # 调用接口
        response = await client.get(f"/api/results/{experiment_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["experiment_id"] == experiment_id
        assert data["status"] == "pending"
        assert data["model"] is None


class TestDownloadModelContract:
    """模型下载接口契约测试"""

    @pytest.mark.asyncio
    async def test_download_model_invalid_id_format(self, client):
        """
        场景：无效 experiment_id 格式
        预期：返回 400
        """
        response = await client.get("/api/results/invalid-uuid/download-model")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid experiment ID format" in data["detail"]

    @pytest.mark.asyncio
    async def test_download_model_experiment_not_found(self, client):
        """
        场景：不存在 experiment_id
        预期：返回 404，detail 包含 "Model not found" 或 "Experiment not found"
        """
        non_existent_id = str(uuid.uuid4())
        response = await client.get(f"/api/results/{non_existent_id}/download-model")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_download_model_no_model_record(self, client, sample_csv_file, db_session):
        """
        场景：实验存在但无模型记录
        预期：返回 404，detail 包含 "Model not found"
        """
        # 创建数据集
        dataset = Dataset(name="无模型下载测试数据集")
        db_session.add(dataset)
        await db_session.flush()
        
        file = DatasetFile(
            dataset_id=dataset.id,
            file_path=sample_csv_file,
            file_name="test.csv",
            role="primary",
            row_count=100,
            column_count=3,
            file_size=1024,
        )
        db_session.add(file)
        
        # 创建实验（不创建模型）
        experiment = Experiment(
            name="无模型下载测试实验",
            dataset_id=dataset.id,
            config={"objective": "regression", "n_estimators": 100},
            status=ExperimentStatus.completed.value,
        )
        db_session.add(experiment)
        await db_session.flush()
        
        experiment_id = str(experiment.id)
        
        # 调用接口
        response = await client.get(f"/api/results/{experiment_id}/download-model")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Model not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_download_model_file_not_found(self, client, sample_csv_file, db_session):
        """
        场景：模型记录存在但文件缺失
        预期：返回 404，detail 包含 "not found"
        """
        from app.services.storage import init_storage_service, StorageConfig
        
        # 使用临时目录初始化存储服务
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            await init_storage_service(storage_config)
            
            # 创建数据集
            dataset = Dataset(name="文件缺失测试数据集")
            db_session.add(dataset)
            await db_session.flush()
            
            file = DatasetFile(
                dataset_id=dataset.id,
                file_path=sample_csv_file,
                file_name="test.csv",
                role="primary",
                row_count=100,
                column_count=3,
                file_size=1024,
            )
            db_session.add(file)
            
            # 创建实验
            experiment = Experiment(
                name="文件缺失测试实验",
                dataset_id=dataset.id,
                config={"objective": "regression", "n_estimators": 100},
                status=ExperimentStatus.completed.value,
            )
            db_session.add(experiment)
            await db_session.flush()
            
            experiment_id = str(experiment.id)
            
            # 创建模型记录（但不创建实际文件）
            model = Model(
                experiment_id=experiment.id,
                storage_type="local",
                object_key=f"models/{experiment_id}/model.json",
                format="json",
                file_size=1024,
            )
            db_session.add(model)
            await db_session.flush()
            
            # 调用接口
            response = await client.get(f"/api/results/{experiment_id}/download-model")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_download_model_success(self, client, sample_csv_file, db_session):
        """
        场景：成功下载模型文件
        预期：返回 200，Content-Type 正确，文件内容有效
        """
        from app.services.storage import init_storage_service, StorageConfig, get_storage_service
        
        # 使用临时目录初始化存储服务
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            await init_storage_service(storage_config)
            
            # 创建数据集
            dataset = Dataset(name="模型下载成功测试数据集")
            db_session.add(dataset)
            await db_session.flush()
            
            file = DatasetFile(
                dataset_id=dataset.id,
                file_path=sample_csv_file,
                file_name="test.csv",
                role="primary",
                row_count=100,
                column_count=3,
                file_size=1024,
            )
            db_session.add(file)
            
            # 创建实验
            experiment = Experiment(
                name="模型下载成功测试实验",
                dataset_id=dataset.id,
                config={"objective": "regression", "n_estimators": 100},
                status=ExperimentStatus.completed.value,
            )
            db_session.add(experiment)
            await db_session.flush()
            
            experiment_id = str(experiment.id)
            
            # 创建模型文件
            storage = get_storage_service()
            model_content = json.dumps({"model_type": "xgboost", "version": "1.0"}).encode()
            await storage.save_model(
                experiment_id=experiment_id,
                data=model_content,
                format="json"
            )
            
            # 创建模型记录
            model = Model(
                experiment_id=experiment.id,
                storage_type="local",
                object_key=f"models/{experiment_id}/model.json",
                format="json",
                file_size=len(model_content),
            )
            db_session.add(model)
            await db_session.flush()
            
            # 调用接口
            response = await client.get(f"/api/results/{experiment_id}/download-model")
            
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")
            assert "attachment" in response.headers.get("content-disposition", "")
            
            # 验证文件内容
            content = response.content
            assert len(content) > 0
            
            model_data = json.loads(content)
            assert model_data["model_type"] == "xgboost"
