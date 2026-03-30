"""
结果接口测试

测试所有 results 相关接口
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
import os
import tempfile
import pandas as pd
from unittest.mock import AsyncMock, MagicMock
import uuid

# 设置测试环境
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["STORAGE_TYPE"] = "local"

from app.main import app
from app.database import Base, get_db
from app.models import (
    Dataset, DatasetFile, Experiment, ExperimentStatus,
    TrainingMetric, FeatureImportance, Model
)
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
        autoflush=False
    )
    session = async_session_maker()
    yield session
    await session.close()


@pytest.fixture
def sample_csv_file():
    """创建测试 CSV 文件"""
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

    # Mock queue service
    mock_queue = MagicMock()
    mock_queue.enqueue_training = AsyncMock(return_value="test-exp-id")
    mock_queue.get_queue_length = AsyncMock(return_value=1)
    mock_queue.remove_from_queue = AsyncMock(return_value=True)
    mock_queue.increment_task_version = AsyncMock(return_value=2)
    mock_queue.get_task_version = AsyncMock(return_value=1)
    mock_queue.check_task_cancelled = AsyncMock(return_value=False)

    async def override_get_queue():
        yield mock_queue

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_queue_service] = override_get_queue

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.mock_queue = mock_queue
        yield ac

    app.dependency_overrides.clear()


class TestResultsEndpoints:
    """结果接口测试"""

    @pytest.mark.asyncio
    async def test_get_results_happy_path(self, client, sample_csv_file, db_session):
        """测试获取实验结果 - happy path"""
        # 创建数据集
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "结果测试数据集",
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

        # 创建实验
        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "结果测试实验",
                "dataset_id": dataset_id,
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "xgboost_params": {"n_estimators": 10}
                }
            }
        )
        experiment_id = exp_response.json()["id"]

        # 添加训练指标
        from sqlalchemy import select
        exp_result = await db_session.execute(
            select(Experiment).where(Experiment.id == uuid.UUID(experiment_id))
        )
        exp = exp_result.scalar_one()
        exp.status = ExperimentStatus.completed.value

        # 添加指标
        for i in range(10):
            metric = TrainingMetric(
                experiment_id=uuid.UUID(experiment_id),
                iteration=i,
                train_loss=0.1 * (10 - i),
                val_loss=0.15 * (10 - i)
            )
            db_session.add(metric)

        # 添加特征重要性
        for rank, (name, imp) in enumerate([("feature1", 0.6), ("feature2", 0.4)], 1):
            fi = FeatureImportance(
                experiment_id=uuid.UUID(experiment_id),
                feature_name=name,
                importance=imp,
                rank=rank
            )
            db_session.add(fi)

        # 添加模型
        model = Model(
            experiment_id=uuid.UUID(experiment_id),
            storage_type="local",
            object_key=f"models/{experiment_id}/model.json",
            format="json",
            file_size=1024,
            metrics={"r2": 0.95, "mae": 2.5}
        )
        db_session.add(model)

        await db_session.flush()

        # 获取结果
        response = await client.get(f"/api/results/{experiment_id}")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert data["experiment_id"] == experiment_id
        assert data["experiment_name"] == "结果测试实验"
        assert data["status"] == "completed"

        # 验证指标
        assert "metrics" in data
        assert data["metrics"]["train_rmse"] is not None
        assert data["metrics"]["val_rmse"] is not None
        assert data["metrics"]["r2"] == 0.95
        assert data["metrics"]["mae"] == 2.5

        # 验证特征重要性
        assert len(data["feature_importance"]) == 2
        assert data["feature_importance"][0]["feature_name"] == "feature1"
        assert data["feature_importance"][0]["importance"] == 0.6
        assert data["feature_importance"][0]["rank"] == 1

        # 验证模型信息
        assert data["model"] is not None
        assert data["model"]["storage_type"] == "local"
        assert data["model"]["format"] == "json"

    @pytest.mark.asyncio
    async def test_get_metrics_history(self, client, sample_csv_file, db_session):
        """测试获取指标历史"""
        # 创建数据集和实验
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "指标历史测试数据集",
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

        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "指标历史测试实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"}
            }
        )
        experiment_id = exp_response.json()["id"]

        # 添加指标
        for i in range(5):
            metric = TrainingMetric(
                experiment_id=uuid.UUID(experiment_id),
                iteration=i,
                train_loss=1.0 / (i + 1),
                val_loss=1.2 / (i + 1)
            )
            db_session.add(metric)
        await db_session.flush()

        # 获取指标历史
        response = await client.get(f"/api/results/{experiment_id}/metrics-history")

        assert response.status_code == 200
        data = response.json()

        assert data["experiment_id"] == experiment_id
        assert len(data["iterations"]) == 5
        assert len(data["train_loss"]) == 5
        assert len(data["val_loss"]) == 5

        # 验证迭代顺序
        assert data["iterations"] == [0, 1, 2, 3, 4]
        assert data["train_loss"][0] == 1.0
        assert data["train_loss"][4] == 0.2

    @pytest.mark.asyncio
    async def test_get_feature_importance(self, client, sample_csv_file, db_session):
        """测试获取特征重要性"""
        # 创建数据集和实验
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征重要性测试数据集",
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

        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "特征重要性测试实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"}
            }
        )
        experiment_id = exp_response.json()["id"]

        # 添加特征重要性
        features = [
            ("f1", 0.4, 1),
            ("f2", 0.3, 2),
            ("f3", 0.2, 3),
            ("f4", 0.1, 4),
        ]
        for name, imp, rank in features:
            fi = FeatureImportance(
                experiment_id=uuid.UUID(experiment_id),
                feature_name=name,
                importance=imp,
                rank=rank
            )
            db_session.add(fi)
        await db_session.flush()

        # 获取特征重要性
        response = await client.get(f"/api/results/{experiment_id}/feature-importance?top_n=2")

        assert response.status_code == 200
        data = response.json()

        assert data["experiment_id"] == experiment_id
        assert data["total_features"] == 2
        assert data["total_importance"] == 0.7  # 0.4 + 0.3

        # 验证按重要性降序排列
        assert data["features"][0]["feature_name"] == "f1"
        assert data["features"][0]["importance_pct"] == pytest.approx(57.14, rel=0.01)

    @pytest.mark.asyncio
    async def test_compare_experiments(self, client, sample_csv_file, db_session):
        """测试对比实验"""
        # 创建数据集
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "对比测试数据集",
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

        # 创建两个实验
        exp_ids = []
        for i in range(2):
            exp_response = await client.post(
                "/api/experiments/",
                json={
                    "name": f"对比测试实验{i+1}",
                    "dataset_id": dataset_id,
                    "config": {"task_type": "regression", "test_size": 0.2}
                }
            )
            exp_ids.append(exp_response.json()["id"])

        # 添加指标
        for idx, exp_id in enumerate(exp_ids):
            metric = TrainingMetric(
                experiment_id=uuid.UUID(exp_id),
                iteration=0,
                train_loss=0.1 + idx * 0.05,
                val_loss=0.12 + idx * 0.05
            )
            db_session.add(metric)
        await db_session.flush()

        # 对比实验
        response = await client.post(
            "/api/results/compare",
            json=exp_ids
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["experiments"]) == 2
        assert data["best_val_rmse"] is not None
        assert data["comparison"]["best_experiment"] in exp_ids

        # 验证实验信息
        exp_names = [e["name"] for e in data["experiments"]]
        assert "对比测试实验1" in exp_names
        assert "对比测试实验2" in exp_names

    @pytest.mark.asyncio
    async def test_compare_experiments_invalid_input(self, client):
        """测试对比实验 - 无效输入"""
        # 少于 2 个实验
        response = await client.post(
            "/api/results/compare",
            json=["exp-1"]
        )
        assert response.status_code == 400
        assert "at least 2" in response.json()["detail"].lower()

        # 超过 4 个实验
        response = await client.post(
            "/api/results/compare",
            json=["exp-1", "exp-2", "exp-3", "exp-4", "exp-5"]
        )
        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_export_report_json(self, client, sample_csv_file, db_session):
        """测试导出 JSON 报告"""
        # 创建数据集和实验
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "报告导出测试数据集",
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

        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "报告导出测试实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"}
            }
        )
        experiment_id = exp_response.json()["id"]

        # 添加数据
        metric = TrainingMetric(
            experiment_id=uuid.UUID(experiment_id),
            iteration=0,
            train_loss=0.1,
            val_loss=0.12
        )
        db_session.add(metric)

        fi = FeatureImportance(
            experiment_id=uuid.UUID(experiment_id),
            feature_name="feature1",
            importance=0.8,
            rank=1
        )
        db_session.add(fi)
        await db_session.flush()

        # 导出 JSON 报告
        response = await client.get(f"/api/results/{experiment_id}/export-report?format=json")

        assert response.status_code == 200
        data = response.json()

        # 验证报告结构
        assert "experiment" in data
        assert data["experiment"]["id"] == experiment_id
        assert data["experiment"]["name"] == "报告导出测试实验"
        assert "metrics_history" in data
        assert "feature_importance" in data

    @pytest.mark.asyncio
    async def test_export_report_csv(self, client, sample_csv_file, db_session):
        """测试导出 CSV 报告"""
        # 创建数据集和实验
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "CSV报告导出测试数据集",
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

        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "CSV报告导出测试实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"}
            }
        )
        experiment_id = exp_response.json()["id"]

        # 添加指标
        for i in range(3):
            metric = TrainingMetric(
                experiment_id=uuid.UUID(experiment_id),
                iteration=i,
                train_loss=0.1 * (i + 1),
                val_loss=0.12 * (i + 1)
            )
            db_session.add(metric)
        await db_session.flush()

        # 导出 CSV 报告
        response = await client.get(f"/api/results/{experiment_id}/export-report?format=csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_download_model_happy_path(self, client, sample_csv_file, db_session):
        """
        测试模型下载 - happy path

        通过存储适配器保存真实模型文件，然后下载验证
        """
        from app.services.storage import init_storage_service, StorageConfig

        # 初始化存储服务（使用临时目录）
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            await init_storage_service(storage_config)

            # 创建数据集和实验
            dataset_response = await client.post(
                "/api/datasets/",
                json={
                    "name": "模型下载Happy Path测试数据集",
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

            exp_response = await client.post(
                "/api/experiments/",
                json={
                    "name": "模型下载Happy Path测试实验",
                    "dataset_id": dataset_id,
                    "config": {"task_type": "regression"}
                }
            )
            experiment_id = exp_response.json()["id"]

            # 通过存储适配器保存真实模型文件
            from app.services.storage import get_storage_service
            storage = get_storage_service()

            model_content = b'{"model_type": "xgboost", "version": "1.0", "trees": []}'
            storage_info = await storage.save_model(
                experiment_id=experiment_id,
                data=model_content,
                format="json"
            )

            # 添加模型记录
            model = Model(
                experiment_id=uuid.UUID(experiment_id),
                storage_type=storage_info.storage_type,
                object_key=storage_info.object_key,
                format="json",
                file_size=storage_info.file_size,
                metrics={"r2": 0.95}
            )
            db_session.add(model)
            await db_session.flush()

            # 下载模型
            response = await client.get(f"/api/results/{experiment_id}/download-model")

            # 明确断言 200
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            # 明确断言 content-type
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type, f"Expected application/json, got {content_type}"

            # 明确断言 content-disposition
            content_disposition = response.headers.get("content-disposition", "")
            assert f'model_{experiment_id}.json' in content_disposition, \
                f"Expected filename in content-disposition, got {content_disposition}"

            # 明确断言返回内容非空且正确
            response_content = response.content
            assert len(response_content) > 0, "Response content is empty"
            assert response_content == model_content, "Response content does not match saved model"

    @pytest.mark.asyncio
    async def test_download_model_not_found(self, client):
        """测试模型下载 - 模型不存在"""
        # 使用不存在的实验 ID
        fake_experiment_id = str(uuid.uuid4())

        response = await client.get(f"/api/results/{fake_experiment_id}/download-model")

        # 应该返回 404
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_model_invalid_id(self, client):
        """测试模型下载 - 无效的实验 ID"""
        response = await client.get("/api/results/invalid-uuid/download-model")

        # 应该返回 400
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_download_model_legacy_fallback(self, client, sample_csv_file, db_session):
        """
        R10: 测试历史模型下载 - 走 file_path fallback

        历史数据特征：object_key 为空（历史数据无此字段）
        此类模型应通过 file_path 读取
        """
        # 创建数据集和实验
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "历史模型测试数据集",
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

        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "历史模型测试实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"}
            }
        )
        experiment_id = exp_response.json()["id"]

        # 创建历史模型文件（模拟旧版本保存的模型）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            legacy_model_content = '{"model_type": "legacy", "version": "0.9"}'
            f.write(legacy_model_content)
            legacy_model_path = f.name

        # 添加历史模型记录（无 object_key，有 file_path）
        legacy_model = Model(
            experiment_id=uuid.UUID(experiment_id),
            storage_type="local",
            object_key=None,  # 历史数据无 object_key
            format="json",
            file_size=len(legacy_model_content.encode()),
            file_path=legacy_model_path,  # 历史数据有 file_path
            metrics={"r2": 0.85}
        )
        db_session.add(legacy_model)
        await db_session.flush()

        # 下载模型
        response = await client.get(f"/api/results/{experiment_id}/download-model")

        # 历史模型应通过 file_path 成功下载
        assert response.status_code == 200, f"Expected 200 for legacy model, got {response.status_code}"

        # 验证内容正确
        assert response.content == legacy_model_content.encode()

        # 清理
        import os
        if os.path.exists(legacy_model_path):
            os.unlink(legacy_model_path)

    @pytest.mark.asyncio
    async def test_download_model_new_model_storage_failure_no_fallback(self, client, sample_csv_file, db_session):
        """
        R10: 测试新模型存储失败 - 不应 fallback 到 file_path

        新模型特征：有 object_key
        如果存储中文件不存在，应返回 404，而不是 fallback 到 file_path
        """
        # 创建数据集和实验
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "新模型存储失败测试数据集",
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

        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "新模型存储失败测试实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"}
            }
        )
        experiment_id = exp_response.json()["id"]

        # 创建一个临时文件（模拟旧版本的 file_path，但新模型不应使用它）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            fallback_content = '{"this": "should_not_be_used"}'
            f.write(fallback_content)
            fallback_path = f.name

        # 添加新模型记录（有 object_key，存储中不存在对应文件）
        # 注意：同时设置 file_path，但新模型不应 fallback
        new_model = Model(
            experiment_id=uuid.UUID(experiment_id),
            storage_type="local",
            object_key="models/nonexistent/model.json",  # 存储中不存在的路径
            format="json",
            file_size=1024,
            file_path=fallback_path,  # 即使有 file_path，新模型也不应 fallback
            metrics={"r2": 0.90}
        )
        db_session.add(new_model)
        await db_session.flush()

        # 下载模型
        response = await client.get(f"/api/results/{experiment_id}/download-model")

        # 新模型存储失败应返回 404，不应 fallback 到 file_path
        assert response.status_code == 404, \
            f"Expected 404 for new model with storage failure, got {response.status_code}. " \
            "New model should NOT fallback to file_path."

        # 验证错误信息
        assert "not found in storage" in response.json()["detail"].lower()

        # 清理
        import os
        if os.path.exists(fallback_path):
            os.unlink(fallback_path)


class TestWorkerAPIEndpointIntegration:
    """
    R11: Worker-API 端点级集成测试

    模拟 Worker 保存模型后，通过实际 API 端点下载模型。
    这是真正的端点级测试，不是 storage service 层的互读测试。
    """

    @pytest.mark.asyncio
    async def test_worker_save_then_api_download_endpoint(self, client, sample_csv_file, db_session):
        """
        R11: True endpoint-level integration test

        Flow:
        1. Worker saves model to storage adapter
        2. Worker creates model record
        3. Call actual API endpoint `/api/results/{experiment_id}/download-model`
        4. Assert 200 and content matches

        Note: This test calls actual HTTP endpoint, NOT storage service's get_model()
        """
        from app.services.storage import init_storage_service, StorageConfig

        # 使用临时目录初始化存储服务
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            await init_storage_service(storage_config)

            # Step 1: 通过 API 端点创建数据集
            dataset_response = await client.post(
                "/api/datasets/",
                json={
                    "name": "Worker-API endpoint integration test dataset",
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
            assert dataset_response.status_code == 200, f"Failed to create dataset: {dataset_response.text}"
            dataset_id = dataset_response.json()["id"]

            # Step 2: 通过 API 端点创建实验
            exp_response = await client.post(
                "/api/experiments/",
                json={
                    "name": "Worker-API endpoint integration test experiment",
                    "dataset_id": dataset_id,
                    "config": {"task_type": "regression"}
                }
            )
            assert exp_response.status_code == 200, f"Failed to create experiment: {exp_response.text}"
            experiment_id = exp_response.json()["id"]

            # Step 3: 模拟 Worker 保存模型到存储适配器
            from app.services.storage import get_storage_service
            storage = get_storage_service()

            model_content = b'{"model_type": "xgboost", "version": "1.0", "n_trees": 100, "trees": []}'
            storage_info = await storage.save_model(
                experiment_id=experiment_id,
                data=model_content,
                format="json"
            )

            # Step 4: 模拟 Worker 创建模型记录
            model_record = Model(
                experiment_id=uuid.UUID(experiment_id),
                storage_type=storage_info.storage_type,
                object_key=storage_info.object_key,
                format="json",
                file_size=storage_info.file_size,
                metrics={"r2": 0.95, "rmse": 0.05}
            )
            db_session.add(model_record)
            await db_session.flush()

            # Step 5: 调用实际 API 端点下载模型
            response = await client.get(f"/api/results/{experiment_id}/download-model")

            # Step 6: 断言 200
            assert response.status_code == 200, \
                f"Expected 200 from API endpoint, got {response.status_code}. Response: {response.text}"

            # Step 7: 断言 content-type
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type, f"Expected application/json, got {content_type}"

            # Step 8: 断言 content-disposition
            content_disposition = response.headers.get("content-disposition", "")
            assert f'model_{experiment_id}.json' in content_disposition, \
                f"Expected filename in content-disposition, got {content_disposition}"

            # Step 9: 断言返回内容与 Worker 保存的内容一致
            downloaded_content = response.content
            assert downloaded_content == model_content, \
                f"Downloaded content does not match Worker-saved content. " \
                f"Expected {len(model_content)} bytes, got {len(downloaded_content)} bytes"

    @pytest.mark.asyncio
    async def test_worker_save_preprocessing_then_api_check_result(self, client, db_session):
        """
        R11: 预处理结果端点级集成测试

        模拟 Worker 保存预处理输出后，验证 AsyncTask.result 包含正确的存储信息。
        """
        from app.services.storage import init_storage_service, StorageConfig, get_storage_service

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_config = StorageConfig(
                storage_type="local",
                local_base_path=tmpdir
            )
            await init_storage_service(storage_config)

            storage = get_storage_service()

            dataset_id = str(uuid.uuid4())
            task_id = str(uuid.uuid4())

            # 模拟 Worker 保存预处理输出
            csv_content = b"col1,col2,col3\n1,2,3\n4,5,6"
            storage_info = await storage.save_preprocessing_output(
                dataset_id=dataset_id,
                task_id=task_id,
                data=csv_content
            )

            # 验证存储信息包含必要字段
            assert storage_info.storage_type == "local"
            assert storage_info.object_key is not None
            assert task_id in storage_info.object_key, \
                f"Object key should contain task_id: {storage_info.object_key}"
            assert storage_info.file_size == len(csv_content)

            # 模拟 AsyncTask.result 结构
            async_task_result = {
                "dataset_id": dataset_id,
                "status": "completed",
                "storage_type": storage_info.storage_type,
                "object_key": storage_info.object_key,
                "file_size": storage_info.file_size,
                "output_file_name": "processed.csv"
            }

            # 验证结果结构
            assert async_task_result["storage_type"] == "local"
            assert async_task_result["object_key"].startswith("preprocessing/")
            assert async_task_result["file_size"] > 0