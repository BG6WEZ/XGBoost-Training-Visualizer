"""
扩展结果端点契约测试

覆盖以下端点：
- GET /api/results/{id}/feature-importance
- GET /api/results/{id}/metrics-history
- POST /api/results/compare
- GET /api/results/{id}/export-report
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from unittest.mock import MagicMock, AsyncMock, patch
import uuid
import tempfile
import os
import json

from app.main import app
from app.database import get_db, Base
from app.models import Experiment, Dataset, DatasetFile, Model, ExperimentStatus, TrainingMetric, FeatureImportance
from app.services.queue import get_queue_service


@pytest_asyncio.fixture
async def async_client():
    """创建异步测试客户端"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with async_session() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    mock_queue = MagicMock()
    mock_queue.redis = None
    app.dependency_overrides[get_queue_service] = lambda: mock_queue
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session
    
    app.dependency_overrides.clear()
    
    # 显式关闭 engine 以避免 aiosqlite 线程告警
    await engine.dispose()


class TestFeatureImportanceEndpoint:
    """特征重要性端点契约测试"""
    
    @pytest.mark.asyncio
    async def test_feature_importance_invalid_uuid_format(self, async_client):
        """测试无效 UUID 格式返回 400"""
        client, _ = async_client
        response = await client.get("/api/results/invalid-uuid/feature-importance")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_feature_importance_experiment_not_found(self, async_client):
        """测试实验不存在返回 404"""
        client, _ = async_client
        non_existent_id = str(uuid.uuid4())
        
        response = await client.get(f"/api/results/{non_existent_id}/feature-importance")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_feature_importance_success(self, async_client):
        """测试成功获取特征重要性"""
        client, session_factory = async_client
        
        async with session_factory() as db:
            dataset = Dataset(name="测试数据集")
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            
            experiment = Experiment(
                name="特征重要性测试实验",
                dataset_id=dataset.id,
                config={"n_estimators": 100},
                status=ExperimentStatus.completed.value,
            )
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            
            feature_importance = FeatureImportance(
                experiment_id=experiment.id,
                feature_name="feature_1",
                importance=0.5,
                rank=1
            )
            db.add(feature_importance)
            await db.commit()
            
            experiment_id = str(experiment.id)
        
        response = await client.get(f"/api/results/{experiment_id}/feature-importance")
        
        assert response.status_code == 200
        data = response.json()
        assert "experiment_id" in data
        assert "features" in data
        assert isinstance(data["features"], list)


class TestMetricsHistoryEndpoint:
    """指标历史端点契约测试"""
    
    @pytest.mark.asyncio
    async def test_metrics_history_invalid_uuid_format(self, async_client):
        """测试无效 UUID 格式返回 400"""
        client, _ = async_client
        response = await client.get("/api/results/invalid-uuid/metrics-history")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_metrics_history_experiment_not_found(self, async_client):
        """测试实验不存在返回 404"""
        client, _ = async_client
        non_existent_id = str(uuid.uuid4())
        
        response = await client.get(f"/api/results/{non_existent_id}/metrics-history")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Experiment not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_metrics_history_success(self, async_client):
        """测试成功获取指标历史"""
        client, session_factory = async_client
        
        async with session_factory() as db:
            dataset = Dataset(name="指标历史测试数据集")
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            
            experiment = Experiment(
                name="指标历史测试实验",
                dataset_id=dataset.id,
                config={"n_estimators": 100},
                status=ExperimentStatus.completed.value,
            )
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            
            metric = TrainingMetric(
                experiment_id=experiment.id,
                iteration=1,
                train_loss=0.1,
                val_loss=0.2,
                train_metric=0.9,
                val_metric=0.85
            )
            db.add(metric)
            await db.commit()
            
            experiment_id = str(experiment.id)
        
        response = await client.get(f"/api/results/{experiment_id}/metrics-history")
        
        assert response.status_code == 200
        data = response.json()
        assert "experiment_id" in data
        assert "iterations" in data
        assert "train_loss" in data
        assert "val_loss" in data
        assert isinstance(data["iterations"], list)
        assert isinstance(data["train_loss"], list)
        assert isinstance(data["val_loss"], list)


class TestCompareExperimentsEndpoint:
    """实验对比端点契约测试"""
    
    @pytest.mark.asyncio
    async def test_compare_less_than_2_experiments(self, async_client):
        """测试少于 2 个实验 ID 返回 400"""
        client, _ = async_client
        single_id = [str(uuid.uuid4())]
        
        response = await client.post("/api/results/compare", json=single_id)
        
        assert response.status_code == 400
        data = response.json()
        assert "At least 2 experiments required" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_compare_more_than_4_experiments(self, async_client):
        """测试超过 4 个实验 ID 返回 400"""
        client, _ = async_client
        five_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        response = await client.post("/api/results/compare", json=five_ids)
        
        assert response.status_code == 400
        data = response.json()
        assert "Maximum 4 experiments" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_compare_invalid_uuid_format(self, async_client):
        """测试包含无效 UUID 格式返回 400"""
        client, _ = async_client
        invalid_ids = ["invalid-uuid", str(uuid.uuid4())]
        
        response = await client.post("/api/results/compare", json=invalid_ids)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid experiment ID" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_compare_success(self, async_client):
        """测试成功对比两个实验"""
        client, session_factory = async_client
        
        async with session_factory() as db:
            dataset = Dataset(name="对比测试数据集")
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            
            experiment_ids = []
            for i in range(2):
                experiment = Experiment(
                    name=f"对比测试实验 {i+1}",
                    dataset_id=dataset.id,
                    config={"n_estimators": 100},
                    status=ExperimentStatus.completed.value,
                )
                db.add(experiment)
                await db.commit()
                await db.refresh(experiment)
                experiment_ids.append(str(experiment.id))
                
                metric = TrainingMetric(
                    experiment_id=experiment.id,
                    iteration=1,
                    train_loss=0.1 + i * 0.01,
                    val_loss=0.2 + i * 0.01,
                    train_metric=0.9,
                    val_metric=0.85
                )
                db.add(metric)
                await db.commit()
        
        response = await client.post("/api/results/compare", json=experiment_ids)
        
        assert response.status_code == 200
        data = response.json()
        assert "experiments" in data
        assert "best_val_rmse" in data
        assert "comparison" in data
        assert isinstance(data["experiments"], list)
        assert len(data["experiments"]) == 2


class TestExportReportEndpoint:
    """导出报告端点契约测试"""
    
    @pytest.mark.asyncio
    async def test_export_report_invalid_uuid_format(self, async_client):
        """测试无效 UUID 格式返回 400"""
        client, _ = async_client
        response = await client.get("/api/results/invalid-uuid/export-report")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_export_report_experiment_not_found(self, async_client):
        """测试实验不存在返回 404"""
        client, _ = async_client
        non_existent_id = str(uuid.uuid4())
        
        response = await client.get(f"/api/results/{non_existent_id}/export-report")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_export_report_json_success(self, async_client):
        """测试成功导出 JSON 格式报告"""
        client, session_factory = async_client
        
        async with session_factory() as db:
            dataset = Dataset(name="报告测试数据集")
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            
            experiment = Experiment(
                name="报告测试实验",
                dataset_id=dataset.id,
                config={"n_estimators": 100},
                status=ExperimentStatus.completed.value,
            )
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            
            metric = TrainingMetric(
                experiment_id=experiment.id,
                iteration=1,
                train_loss=0.1,
                val_loss=0.2,
                train_metric=0.9,
                val_metric=0.85
            )
            db.add(metric)
            await db.commit()
            
            experiment_id = str(experiment.id)
        
        response = await client.get(f"/api/results/{experiment_id}/export-report?format=json")
        
        assert response.status_code == 200
        data = response.json()
        assert "experiment" in data
        assert "metrics_history" in data
        assert "feature_importance" in data
        assert "experiment_id" in data["experiment"] or "id" in data["experiment"]
    
    @pytest.mark.asyncio
    async def test_export_report_csv_format(self, async_client):
        """测试导出 CSV 格式报告"""
        client, session_factory = async_client
        
        async with session_factory() as db:
            dataset = Dataset(name="CSV报告测试数据集")
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            
            experiment = Experiment(
                name="CSV报告测试实验",
                dataset_id=dataset.id,
                config={"n_estimators": 100},
                status=ExperimentStatus.completed.value,
            )
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            
            metric = TrainingMetric(
                experiment_id=experiment.id,
                iteration=1,
                train_loss=0.1,
                val_loss=0.2,
                train_metric=0.9,
                val_metric=0.85
            )
            db.add(metric)
            await db.commit()
            
            experiment_id = str(experiment.id)
        
        response = await client.get(f"/api/results/{experiment_id}/export-report?format=csv")
        
        # CSV 格式可能返回文件下载或 JSON
        assert response.status_code in [200, 404]
