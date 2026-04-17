"""新增端点测试"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
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
from app.models import Dataset, DatasetFile, Experiment, ExperimentStatus
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


class TestPreprocessingEndpoints:
    """预处理端点测试"""

    @pytest.mark.asyncio
    async def test_preprocess_dataset(self, client, sample_csv_file):
        """测试触发预处理任务"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "预处理测试数据集",
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

        # 触发预处理
        response = await client.post(
            f"/api/datasets/{dataset_id}/preprocess",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "missing_value_strategy": "mean_fill",
                    "remove_duplicates": True,
                    "handle_outliers": False,
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "task_id" in data

    @pytest.mark.asyncio
    async def test_preprocess_dataset_not_found(self, client):
        """测试预处理不存在的数据集"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.post(
            f"/api/datasets/{fake_id}/preprocess",
            json={
                "dataset_id": fake_id,
                "config": {
                    "missing_value_strategy": "mean_fill",
                }
            }
        )

        assert response.status_code == 404


class TestFeatureEngineeringEndpoints:
    """特征工程端点测试"""

    @pytest.mark.asyncio
    async def test_feature_engineering_dataset(self, client, sample_csv_file):
        """测试触发特征工程任务"""
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

        # 触发特征工程
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": True,
                        "column": "timestamp",
                        "features": ["hour", "dayofweek"]
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

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "task_id" in data


class TestDatasetSplitEndpoint:
    """数据集切分端点测试"""

    @pytest.mark.asyncio
    async def test_split_dataset(self, client, sample_csv_file):
        """测试切分数据集"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "切分测试数据集",
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

        # 切分数据集
        response = await client.post(
            f"/api/datasets/{dataset_id}/split",
            json={"test_size": 0.2, "random_seed": 42}
        )

        assert response.status_code == 200
        data = response.json()
        assert "subsets" in data
        assert len(data["subsets"]) >= 2
        # 检查是否有训练集和测试集
        subset_purposes = [subset["purpose"] for subset in data["subsets"]]
        assert "train" in subset_purposes
        assert "test" in subset_purposes
        # 检查训练集和测试集的行数
        for subset in data["subsets"]:
            if subset["purpose"] == "train":
                assert subset["row_count"] == 80
            elif subset["purpose"] == "test":
                assert subset["row_count"] == 20


class TestHealthEndpoints:
    """健康检查端点测试"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_live_endpoint(self, client):
        """测试存活检查端点"""
        response = await client.get("/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestStopExperimentLogic:
    """停止实验逻辑测试"""

    @pytest.mark.asyncio
    async def test_stop_queued_experiment(self, client, sample_csv_file):
        """测试停止已排队的实验"""
        # 创建数据集
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "停止测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 2,
                    "file_size": 1024,
                }],
            }
        )
        dataset_id = dataset_response.json()["id"]

        # 创建实验
        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "待停止实验",
                "dataset_id": dataset_id,
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

        # 启动实验（排队）
        await client.post(f"/api/experiments/{experiment_id}/start")

        # 停止实验
        response = await client.post(f"/api/experiments/{experiment_id}/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert "removed_from_queue" in data

    @pytest.mark.asyncio
    async def test_version_bound_to_payload(self, client, sample_csv_file):
        """
        核心单元测试：验证版本号绑定到 payload

        这是核心竞态保护逻辑的验证：
        1. 入队时版本号写入 payload（task_version 字段）
        2. worker 消费时比较 payload 内版本与 Redis 当前版本
        3. Redis 版本 > payload 版本，说明任务已被取消/更新
        """
        import json
        from app.services.queue import QueueService, TrainingTask

        # 创建一个 QueueService 实例，使用 mock Redis
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="1")  # 当前版本为 1
        mock_redis.set = AsyncMock()
        mock_redis.rpush = AsyncMock()

        queue = QueueService("redis://localhost:6379")
        queue._redis = mock_redis

        # 创建任务
        task = TrainingTask(
            experiment_id="test-exp-id",
            dataset_id="test-dataset-id",
            config={"task_type": "regression"}
        )

        # 第一次入队（版本 1）
        await queue.enqueue_training(task)

        # 验证 rpush 被调用，且 payload 包含 task_version
        assert mock_redis.rpush.called
        call_args = mock_redis.rpush.call_args
        payload_str = call_args[0][1]  # 第二个参数是 JSON 字符串
        payload = json.loads(payload_str)

        # 核心验证：payload 必须包含 task_version
        assert "task_version" in payload, "payload 必须包含 task_version 字段"
        assert payload["task_version"] == 1, "第一次入队版本应为 1"

        # 模拟版本递增（stop 操作后）
        mock_redis.get.return_value = "2"  # 版本已递增到 2

        # 再次入队（第二次 start）
        mock_redis.rpush.reset_mock()
        await queue.enqueue_training(task)

        call_args = mock_redis.rpush.call_args
        payload_str = call_args[0][1]
        payload = json.loads(payload_str)

        # 新任务的版本号应该是当前版本（2）
        assert payload["task_version"] == 2, "第二次入队版本应为当前版本 2"

        # 验证 check_task_cancelled 逻辑
        # 旧任务 payload_version=1，当前 Redis 版本=2，应该返回 True（已取消）
        is_cancelled = await queue.check_task_cancelled("test-exp-id", expected_version=1)
        assert is_cancelled is True, "payload_version=1 但 Redis 版本=2，应判定为已取消"

        # 新任务 payload_version=2，当前 Redis 版本=2，应该返回 False（有效）
        is_cancelled = await queue.check_task_cancelled("test-exp-id", expected_version=2)
        assert is_cancelled is False, "payload_version=2 且 Redis 版本=2，应判定为有效"

    @pytest.mark.asyncio
    async def test_training_task_model_has_version_field(self):
        """
        验证 TrainingTask 模型包含 task_version 字段

        这是防止 dequeue_training() 静默丢弃版本号的关键
        """
        from app.services.queue import TrainingTask

        # 创建不带 task_version 的任务（使用默认值）
        task = TrainingTask(
            experiment_id="test-exp",
            dataset_id="test-dataset",
            config={"task_type": "regression"}
        )

        # 验证默认值
        assert hasattr(task, "task_version"), "TrainingTask 必须有 task_version 字段"
        assert task.task_version == 0, "默认版本号应为 0"

        # 创建带 task_version 的任务
        task_with_version = TrainingTask(
            experiment_id="test-exp",
            dataset_id="test-dataset",
            config={"task_type": "regression"},
            task_version=5
        )
        assert task_with_version.task_version == 5, "应能指定版本号"

        # 验证 model_dump 包含 task_version
        dump = task_with_version.model_dump()
        assert "task_version" in dump, "model_dump 必须包含 task_version"
        assert dump["task_version"] == 5


class TestLambdaFieldSerialization:
    """Lambda 字段序列化测试"""

    @pytest.mark.asyncio
    async def test_lambda_field_in_config(self, client, sample_csv_file):
        """测试 lambda 字段正确序列化"""
        # 创建数据集
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "Lambda测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 2,
                    "file_size": 1024,
                }],
            }
        )
        dataset_id = dataset_response.json()["id"]

        # 创建带 lambda 参数的实验
        response = await client.post(
            "/api/experiments/",
            json={
                "name": "Lambda测试实验",
                "dataset_id": dataset_id,
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


class TestReadyEndpoint:
    """就绪检查端点测试"""

    @pytest.mark.asyncio
    async def test_ready_endpoint_all_services(self, client):
        """测试就绪检查端点 - 所有服务"""
        response = await client.get("/ready")

        # 由于测试环境可能没有 Redis 和 MinIO，状态可能是 200 或 503
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        # 数据库应该正常
        assert data["checks"]["database"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_ready_endpoint_returns_checks(self, client):
        """测试就绪检查返回各项检查详情"""
        response = await client.get("/ready")

        data = response.json()
        checks = data["checks"]

        # 验证检查项结构
        assert "database" in checks
        assert "status" in checks["database"]
        assert "message" in checks["database"]


class TestDownloadModelEndpoint:
    """模型下载端点测试"""

    @pytest.mark.asyncio
    async def test_download_model_not_found(self, client):
        """测试下载不存在的模型"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/results/{fake_id}/download-model")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_model_invalid_id(self, client):
        """测试下载模型 - 无效 ID"""
        response = await client.get("/api/results/invalid-uuid/download-model")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid experiment ID format" in data["detail"]

    @pytest.mark.asyncio
    async def test_download_model_no_model(self, client, sample_csv_file):
        """测试下载模型 - 实验存在但无模型"""
        # 创建数据集
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "下载测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 2,
                    "file_size": 1024,
                }],
            }
        )
        dataset_id = dataset_response.json()["id"]

        # 创建实验
        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "下载测试实验",
                "dataset_id": dataset_id,
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "xgboost_params": {"n_estimators": 100, "learning_rate": 0.1},
                    "early_stopping_rounds": 5
                }
            }
        )
        experiment_id = exp_response.json()["id"]

        # 尝试下载模型（实验存在但模型不存在）
        response = await client.get(f"/api/results/{experiment_id}/download-model")

        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]


class TestExportReportEndpoint:
    """报告导出端点测试"""

    @pytest.mark.asyncio
    async def test_export_report_not_found(self, client):
        """测试导出不存在的实验报告"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/results/{fake_id}/export-report")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_report_invalid_id(self, client):
        """测试导出报告 - 无效 ID"""
        response = await client.get("/api/results/invalid-uuid/export-report")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid experiment ID format" in data["detail"]

    @pytest.mark.asyncio
    async def test_export_report_json_format(self, client, sample_csv_file):
        """测试导出 JSON 格式报告"""
        # 创建数据集
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "报告导出测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 2,
                    "file_size": 1024,
                }],
            }
        )
        dataset_id = dataset_response.json()["id"]

        # 创建实验
        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "报告导出测试实验",
                "dataset_id": dataset_id,
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "xgboost_params": {"n_estimators": 100, "learning_rate": 0.1},
                    "early_stopping_rounds": 5
                }
            }
        )
        experiment_id = exp_response.json()["id"]

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
    async def test_export_report_csv_format(self, client, sample_csv_file):
        """测试导出 CSV 格式报告"""
        # 创建数据集
        dataset_response = await client.post(
            "/api/datasets/",
            json={
                "name": "CSV导出测试数据集",
                "files": [{
                    "file_path": sample_csv_file,
                    "file_name": "test.csv",
                    "role": "primary",
                    "row_count": 100,
                    "column_count": 2,
                    "file_size": 1024,
                }],
            }
        )
        dataset_id = dataset_response.json()["id"]

        # 创建实验
        exp_response = await client.post(
            "/api/experiments/",
            json={
                "name": "CSV导出测试实验",
                "dataset_id": dataset_id,
                "config": {
                    "task_type": "regression",
                    "test_size": 0.2,
                    "xgboost_params": {"n_estimators": 100, "learning_rate": 0.1},
                    "early_stopping_rounds": 5
                }
            }
        )
        experiment_id = exp_response.json()["id"]

        # 导出 CSV 报告
        response = await client.get(f"/api/results/{experiment_id}/export-report?format=csv")

        assert response.status_code == 200
        # CSV 响应应该返回文件
        assert "text/csv" in response.headers.get("content-type", "")


class TestAsyncTaskPersistence:
    """异步任务持久化测试"""

    @pytest.mark.asyncio
    async def test_preprocessing_task_creates_db_record(self, client, sample_csv_file):
        """测试预处理任务创建数据库记录"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "预处理持久化测试数据集",
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

        # 触发预处理
        response = await client.post(
            f"/api/datasets/{dataset_id}/preprocess",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "missing_value_strategy": "mean_fill",
                    "remove_duplicates": True,
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

        # 查询任务状态
        task_id = data["task_id"]
        status_response = await client.get(f"/api/datasets/tasks/{task_id}")

        assert status_response.status_code == 200
        task_data = status_response.json()
        assert task_data["id"] == task_id
        assert task_data["task_type"] == "preprocessing"
        assert task_data["dataset_id"] == dataset_id

    @pytest.mark.asyncio
    async def test_feature_engineering_task_creates_db_record(self, client, sample_csv_file):
        """测试特征工程任务创建数据库记录"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "特征工程持久化测试数据集",
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

        # 触发特征工程
        response = await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {
                    "time_features": {
                        "enabled": True,
                        "column": "timestamp",
                        "features": ["hour"]
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

        # 查询任务状态
        task_id = data["task_id"]
        status_response = await client.get(f"/api/datasets/tasks/{task_id}")

        assert status_response.status_code == 200
        task_data = status_response.json()
        assert task_data["id"] == task_id
        assert task_data["task_type"] == "feature_engineering"
        assert task_data["dataset_id"] == dataset_id

    @pytest.mark.asyncio
    async def test_list_dataset_tasks(self, client, sample_csv_file):
        """测试列出数据集的任务"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "任务列表测试数据集",
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

        # 触发预处理任务
        await client.post(
            f"/api/datasets/{dataset_id}/preprocess",
            json={
                "dataset_id": dataset_id,
                "config": {"missing_value_strategy": "mean_fill"}
            }
        )

        # 触发特征工程任务
        await client.post(
            f"/api/datasets/{dataset_id}/feature-engineering",
            json={
                "dataset_id": dataset_id,
                "config": {"time_features": {"enabled": False}}
            }
        )

        # 列出任务
        response = await client.get(f"/api/datasets/{dataset_id}/tasks")

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 2

        # 验证任务类型
        task_types = {t["task_type"] for t in tasks}
        assert "preprocessing" in task_types
        assert "feature_engineering" in task_types