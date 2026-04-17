"""
实验标签和筛选测试

P1-T12: 实验标签与筛选功能
测试标签创建、更新、筛选功能
"""
import pytest
import tempfile
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base, Experiment, Dataset, ExperimentStatus
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
    mock_queue.remove_from_queue = AsyncMock(return_value=False)
    mock_queue.increment_task_version = AsyncMock(return_value=2)

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
async def setup_dataset(client, sample_csv_file, db_session):
    """创建测试数据集"""
    from app.services.storage import init_storage_service, StorageConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_config = StorageConfig(
            storage_type="local",
            local_base_path=tmpdir
        )
        await init_storage_service(storage_config)

        response = await client.post(
            "/api/datasets/",
            json={
                "name": "标签测试数据集",
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
        return response.json()["id"]


@pytest.fixture
async def setup_experiments_with_tags(client, setup_dataset):
    """创建带标签的测试实验"""
    dataset_id = setup_dataset

    experiments = []
    tags_list = [
        ["baseline", "v1.0"],
        ["baseline", "v2.0"],
        ["production"],
        ["experiment", "test"],
        [],
    ]

    for i, tags in enumerate(tags_list):
        response = await client.post(
            "/api/experiments/",
            json={
                "name": f"带标签的实验 {i+1}",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": tags if tags else None,
            }
        )
        experiments.append(response.json())

    return experiments


class TestExperimentTags:
    """实验标签功能测试"""

    @pytest.mark.asyncio
    async def test_create_experiment_with_tags(self, client, setup_dataset):
        """创建带标签的实验"""
        dataset_id = setup_dataset

        response = await client.post(
            "/api/experiments/",
            json={
                "name": "带标签的实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": ["baseline", "v1.0"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["baseline", "v1.0"]

    @pytest.mark.asyncio
    async def test_create_experiment_without_tags(self, client, setup_dataset):
        """创建不带标签的实验"""
        dataset_id = setup_dataset

        response = await client.post(
            "/api/experiments/",
            json={
                "name": "无标签的实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == [] or data["tags"] is None

    @pytest.mark.asyncio
    async def test_update_experiment_tags(self, client, setup_dataset):
        """更新实验标签"""
        dataset_id = setup_dataset

        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "待更新标签的实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": ["initial"],
            }
        )
        experiment_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/api/experiments/{experiment_id}",
            json={
                "tags": ["updated", "new-tag"],
            }
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["tags"] == ["updated", "new-tag"]

    @pytest.mark.asyncio
    async def test_get_experiment_with_tags(self, client, setup_dataset):
        """获取带标签的实验详情"""
        dataset_id = setup_dataset

        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "获取标签测试实验",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": ["test", "example"],
            }
        )
        experiment_id = create_response.json()["id"]

        get_response = await client.get(f"/api/experiments/{experiment_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["tags"] == ["test", "example"]


class TestExperimentFiltering:
    """实验筛选功能测试"""

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client, setup_experiments_with_tags):
        """按状态筛选"""
        response = await client.get("/api/experiments/?status=pending")

        assert response.status_code == 200
        data = response.json()
        for exp in data:
            assert exp["status"] == "pending"

    @pytest.mark.asyncio
    async def test_filter_by_single_tag_any_mode(self, client, setup_experiments_with_tags):
        """按单个标签筛选（any 模式）"""
        all_response = await client.get("/api/experiments/")
        all_data = all_response.json()

        baseline_experiments = [exp for exp in all_data if exp.get("tags") and "baseline" in exp.get("tags", [])]
        assert len(baseline_experiments) >= 2, f"Expected at least 2 experiments with 'baseline' tag, got {len(baseline_experiments)}"

        response = await client.get("/api/experiments/?tags=baseline&tag_match_mode=any")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2, f"Expected at least 2 experiments, got {len(data)}"
        for exp in data:
            if exp.get("tags"):
                assert "baseline" in exp["tags"]

    @pytest.mark.asyncio
    async def test_filter_by_multiple_tags_any_mode(self, client, setup_experiments_with_tags):
        """按多个标签筛选（any 模式 - 任一匹配）"""
        response = await client.get("/api/experiments/?tags=baseline,production&tag_match_mode=any")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1, f"Expected at least 1 experiment, got {len(data)}"

    @pytest.mark.asyncio
    async def test_filter_by_multiple_tags_all_mode(self, client, setup_experiments_with_tags):
        """按多个标签筛选（all 模式 - 全部匹配）"""
        response = await client.get("/api/experiments/?tags=baseline,v1.0&tag_match_mode=all")

        assert response.status_code == 200
        data = response.json()
        for exp in data:
            if exp.get("tags"):
                assert "baseline" in exp["tags"]
                assert "v1.0" in exp["tags"]

    @pytest.mark.asyncio
    async def test_filter_by_name_contains(self, client, setup_experiments_with_tags):
        """按名称模糊搜索"""
        response = await client.get("/api/experiments/?name_contains=带标签")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for exp in data:
            assert "带标签" in exp["name"]

    @pytest.mark.asyncio
    async def test_combined_filter_status_and_tag(self, client, setup_experiments_with_tags):
        """组合筛选：状态 + 标签"""
        response = await client.get("/api/experiments/?status=pending&tags=baseline&tag_match_mode=any")

        assert response.status_code == 200
        data = response.json()
        for exp in data:
            assert exp["status"] == "pending"
            if exp.get("tags"):
                assert "baseline" in exp["tags"]

    @pytest.mark.asyncio
    async def test_filter_experiments_with_no_tags(self, client, setup_experiments_with_tags):
        """筛选无标签的实验"""
        all_response = await client.get("/api/experiments/")
        all_data = all_response.json()

        no_tags_experiments = [exp for exp in all_data if not exp.get("tags") or len(exp.get("tags", [])) == 0]
        assert len(no_tags_experiments) >= 1

    @pytest.mark.asyncio
    async def test_list_experiments_returns_tags(self, client, setup_experiments_with_tags):
        """实验列表返回标签字段"""
        response = await client.get("/api/experiments/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        for exp in data:
            assert "tags" in exp


class TestTagCleaning:
    """标签清洗功能测试"""

    @pytest.mark.asyncio
    async def test_tag_deduplication(self, client, setup_dataset):
        """标签去重"""
        dataset_id = setup_dataset

        response = await client.post(
            "/api/experiments/",
            json={
                "name": "重复标签测试",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": ["tag1", "tag1", "tag2", "tag1"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["tag1", "tag2"]

    @pytest.mark.asyncio
    async def test_tag_strip_whitespace(self, client, setup_dataset):
        """标签去除首尾空格"""
        dataset_id = setup_dataset

        response = await client.post(
            "/api/experiments/",
            json={
                "name": "空格标签测试",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": ["  tag1  ", " tag2", "tag3  "],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["tag1", "tag2", "tag3"]

    @pytest.mark.asyncio
    async def test_tag_remove_empty_strings(self, client, setup_dataset):
        """标签去除空字符串"""
        dataset_id = setup_dataset

        response = await client.post(
            "/api/experiments/",
            json={
                "name": "空字符串标签测试",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": ["tag1", "", "tag2", "   ", "tag3"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["tag1", "tag2", "tag3"]

    @pytest.mark.asyncio
    async def test_tag_cleaning_preserves_order(self, client, setup_dataset):
        """标签清洗保持原始顺序"""
        dataset_id = setup_dataset

        response = await client.post(
            "/api/experiments/",
            json={
                "name": "顺序保持测试",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": ["z-tag", "a-tag", "m-tag", "z-tag"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["z-tag", "a-tag", "m-tag"]

    @pytest.mark.asyncio
    async def test_update_tags_with_cleaning(self, client, setup_dataset):
        """更新标签时也进行清洗"""
        dataset_id = setup_dataset

        create_response = await client.post(
            "/api/experiments/",
            json={
                "name": "更新标签清洗测试",
                "dataset_id": dataset_id,
                "config": {"task_type": "regression"},
                "tags": ["initial"],
            }
        )
        experiment_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/api/experiments/{experiment_id}",
            json={
                "tags": ["  updated  ", "", "new", "new"],
            }
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["tags"] == ["updated", "new"]


class TestDateRangeFiltering:
    """日期范围筛选测试"""

    @pytest.mark.asyncio
    async def test_filter_by_created_after(self, client, setup_experiments_with_tags):
        """按创建时间起始筛选"""
        now = datetime.utcnow()
        yesterday = (now.replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()

        response = await client.get(f"/api/experiments/?created_after={yesterday}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_filter_by_created_before(self, client, setup_experiments_with_tags):
        """按创建时间截止筛选"""
        now = datetime.utcnow()
        tomorrow = (now.replace(hour=23, minute=59, second=59, microsecond=0)).isoformat()

        response = await client.get(f"/api/experiments/?created_before={tomorrow}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client, setup_experiments_with_tags):
        """按日期范围筛选"""
        now = datetime.utcnow()
        yesterday = (now.replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
        tomorrow = (now.replace(hour=23, minute=59, second=59, microsecond=0)).isoformat()

        response = await client.get(
            f"/api/experiments/?created_after={yesterday}&created_before={tomorrow}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
