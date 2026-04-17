"""
导出功能测试

P1-T14: 配置/报告导出
测试配置导出（JSON/YAML）和报告导出（HTML/PDF）功能
"""
import pytest
import tempfile
import uuid
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models import Base, Experiment, Dataset, Model, TrainingMetric, FeatureImportance, ExperimentStatus, ModelVersion
from app.database import get_db
from app.main import app


@pytest.fixture
async def db_session():
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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("feature1,feature2,target\n")
        for i in range(100):
            f.write(f"{i},{i*2},{i*3}\n")
        yield f.name


@pytest.fixture
async def setup_completed_experiment(client, sample_csv_file, db_session):
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
                "name": "导出测试数据集",
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
                "name": "导出测试实验",
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
            }
        )
        db_session.add(model)

        for i in range(10):
            metric = TrainingMetric(
                experiment_id=uuid.UUID(experiment_id),
                iteration=i,
                train_loss=0.5 - i * 0.03,
                val_loss=0.6 - i * 0.035,
            )
            db_session.add(metric)

        for i in range(5):
            fi = FeatureImportance(
                experiment_id=uuid.UUID(experiment_id),
                feature_name=f"feature_{i}",
                importance=0.2 - i * 0.03,
                rank=i + 1,
            )
            db_session.add(fi)

        await db_session.commit()

        return {
            "experiment_id": experiment_id,
            "dataset_id": dataset_id,
        }


class TestConfigExport:
    """配置导出测试"""

    @pytest.mark.asyncio
    async def test_export_config_json(self, client, setup_completed_experiment):
        """导出配置为 JSON 格式"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]
        dataset_id = setup["dataset_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/config/json"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers.get("content-disposition", "")

        data = response.json()
        assert data["experiment_id"] == experiment_id
        assert data["experiment_name"] == "导出测试实验"
        assert data["dataset_id"] == dataset_id
        assert data["task_type"] == "regression"
        assert "xgboost_params" in data
        assert data["xgboost_params"]["n_estimators"] == 100
        assert data["xgboost_params"]["max_depth"] == 6
        assert data["xgboost_params"]["learning_rate"] == 0.1

    @pytest.mark.asyncio
    async def test_export_config_yaml(self, client, setup_completed_experiment):
        """导出配置为 YAML 格式"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]
        dataset_id = setup["dataset_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/config/yaml"
        )

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            assert "attachment" in response.headers.get("content-disposition", "")

            content = response.text
            assert "experiment_id:" in content
            assert "experiment_name:" in content
            assert "导出测试实验" in content
            assert "dataset_id:" in content
            assert "task_type:" in content
            assert "xgboost_params:" in content
        else:
            assert "pyyaml" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_export_config_invalid_experiment(self, client):
        """导出不存在的实验配置"""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/experiments/{fake_id}/export/config/json"
        )

        assert response.status_code == 404


class TestReportExport:
    """报告导出测试"""

    @pytest.mark.asyncio
    async def test_export_report_html(self, client, setup_completed_experiment):
        """导出报告为 HTML 格式"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/html"
        )

        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "")

        content = response.text
        assert "<!DOCTYPE html>" in content
        assert "导出测试实验" in content
        assert "训练配置" in content
        assert "最终指标" in content
        assert "特征重要性" in content

    @pytest.mark.asyncio
    async def test_export_report_pdf_missing_dependency(self, client, setup_completed_experiment):
        """导出报告为 PDF 格式（依赖缺失）"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/pdf"
        )

        assert response.status_code in [200, 503]

        if response.status_code == 503:
            assert "weasyprint" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_export_report_invalid_experiment(self, client):
        """导出不存在的实验报告"""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/experiments/{fake_id}/export/report/html"
        )

        assert response.status_code == 404


class TestReportContent:
    """报告内容测试"""

    @pytest.mark.asyncio
    async def test_report_contains_experiment_info(self, client, setup_completed_experiment):
        """报告包含实验基本信息"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/html"
        )

        assert response.status_code == 200
        content = response.text

        assert "实验名称" in content
        assert "实验 ID" in content
        assert "状态" in content
        assert "创建时间" in content

    @pytest.mark.asyncio
    async def test_report_contains_training_config(self, client, setup_completed_experiment):
        """报告包含训练配置"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/html"
        )

        assert response.status_code == 200
        content = response.text

        assert "训练配置" in content
        assert "n_estimators" in content
        assert "100" in content

    @pytest.mark.asyncio
    async def test_report_contains_metrics(self, client, setup_completed_experiment):
        """报告包含最终指标"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/html"
        )

        assert response.status_code == 200
        content = response.text

        assert "最终指标" in content
        assert "train_rmse" in content
        assert "val_rmse" in content

    @pytest.mark.asyncio
    async def test_report_contains_feature_importance(self, client, setup_completed_experiment):
        """报告包含特征重要性"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/html"
        )

        assert response.status_code == 200
        content = response.text

        assert "特征重要性" in content
        assert "feature_0" in content

    @pytest.mark.asyncio
    async def test_report_contains_training_history(self, client, setup_completed_experiment):
        """报告包含训练历史"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/html"
        )

        assert response.status_code == 200
        content = response.text

        assert "训练历史" in content
        assert "迭代" in content
        assert "训练损失" in content
        assert "验证损失" in content

    @pytest.mark.asyncio
    async def test_report_contains_version_info(self, client, setup_completed_experiment):
        """报告包含模型版本信息"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/html"
        )

        assert response.status_code == 200
        content = response.text

        assert "模型版本信息" in content
        assert "暂无版本信息" in content

    @pytest.mark.asyncio
    async def test_report_contains_completed_time(self, client, setup_completed_experiment):
        """报告包含完成时间"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/report/html"
        )

        assert response.status_code == 200
        content = response.text

        assert "完成时间" in content


class TestConfigExportContract:
    """配置导出契约测试"""

    @pytest.mark.asyncio
    async def test_json_export_has_required_fields(self, client, setup_completed_experiment):
        """JSON 导出包含所有必需字段"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/config/json"
        )

        assert response.status_code == 200
        data = response.json()

        required_fields = ["experiment_id", "experiment_name", "dataset_id", "task_type", "xgboost_params"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_yaml_export_has_required_fields(self, client, setup_completed_experiment):
        """YAML 导出包含所有必需字段"""
        setup = setup_completed_experiment
        experiment_id = setup["experiment_id"]

        response = await client.get(
            f"/api/experiments/{experiment_id}/export/config/yaml"
        )

        if response.status_code == 200:
            content = response.text

            required_fields = ["experiment_id:", "experiment_name:", "dataset_id:", "task_type:", "xgboost_params:"]
            for field in required_fields:
                assert field in content, f"Missing required field: {field}"
