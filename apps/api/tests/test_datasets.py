import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
import asyncio
import os
import tempfile
import pandas as pd

# 设置测试环境
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["MINIO_ENDPOINT"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
os.environ["MINIO_SECRET_KEY"] = "minioadmin"
os.environ["DEBUG"] = "true"

from app.main import app
from app.database import Base, get_db
from app.models import Dataset, DatasetFile


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

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
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


# ========== 数据集测试 ==========

class TestDatasetAPI:
    """数据集 API 测试"""

    @pytest.mark.asyncio
    async def test_create_dataset_with_single_file(self, client, sample_csv_file):
        """测试创建单文件数据集"""
        response = await client.post(
            "/api/datasets/",
            json={
                "name": "测试数据集",
                "description": "单文件测试",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "test_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
                "time_column": "timestamp",
                "entity_column": "building_id",
                "target_column": "energy_consumption",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试数据集"
        assert len(data["files"]) == 1
        assert data["files"][0]["file_name"] == "test_data.csv"
        assert data["total_row_count"] == 100

    @pytest.mark.asyncio
    async def test_create_dataset_with_multiple_files(self, client, sample_csv_file):
        """测试创建多文件数据集"""
        # 创建第二个文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f2:
            df2 = pd.DataFrame({
                'timestamp': pd.date_range('2024-02-01', periods=50, freq='h'),
                'building_id': ['C'] * 50,
                'energy_consumption': [150 + i * 0.3 for i in range(50)],
                'temperature': [18 + i * 0.2 for i in range(50)],
            })
            df2.to_csv(f2, index=False)
            file2_path = f2.name

        try:
            response = await client.post(
                "/api/datasets/",
                json={
                    "name": "多文件数据集",
                    "description": "多文件测试",
                    "files": [
                        {
                            "file_path": sample_csv_file,
                            "file_name": "train_data.csv",
                            "role": "primary",
                            "row_count": 100,
                            "column_count": 4,
                            "file_size": 2048,
                        },
                        {
                            "file_path": file2_path,
                            "file_name": "test_data.csv",
                            "role": "supplementary",
                            "row_count": 50,
                            "column_count": 4,
                            "file_size": 1024,
                        }
                    ],
                    "time_column": "timestamp",
                    "target_column": "energy_consumption",
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "多文件数据集"
            assert len(data["files"]) == 2
            assert data["total_row_count"] == 150  # 100 + 50
        finally:
            os.unlink(file2_path)

    @pytest.mark.asyncio
    async def test_create_dataset_validation_error(self, client):
        """测试创建数据集验证失败 - 缺少文件"""
        response = await client.post(
            "/api/datasets/",
            json={
                "name": "无文件数据集",
                "description": "应该失败",
                "files": [],  # 空文件列表
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_datasets(self, client, sample_csv_file):
        """测试获取数据集列表"""
        # 先创建一个数据集
        await client.post(
            "/api/datasets/",
            json={
                "name": "列表测试数据集",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "test.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )

        response = await client.get("/api/datasets/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_dataset_detail(self, client, sample_csv_file):
        """测试获取数据集详情"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "详情测试数据集",
                "description": "测试描述",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "detail.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )

        dataset_id = create_response.json()["id"]

        # 获取详情
        response = await client.get(f"/api/datasets/{dataset_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dataset_id
        assert data["name"] == "详情测试数据集"
        assert len(data["files"]) == 1

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(self, client):
        """测试获取不存在的数据集"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/datasets/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_dataset(self, client, sample_csv_file):
        """测试更新数据集"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "原始名称",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "test.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )

        dataset_id = create_response.json()["id"]

        # 更新数据集
        response = await client.patch(
            f"/api/datasets/{dataset_id}",
            json={
                "name": "更新后名称",
                "description": "新描述",
                "target_column": "energy_consumption",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后名称"
        assert data["description"] == "新描述"
        assert data["target_column"] == "energy_consumption"

    @pytest.mark.asyncio
    async def test_delete_dataset(self, client, sample_csv_file):
        """测试删除数据集"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "待删除数据集",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "test.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )

        dataset_id = create_response.json()["id"]

        # 删除数据集
        response = await client.delete(f"/api/datasets/{dataset_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # 验证已删除
        get_response = await client.get(f"/api/datasets/{dataset_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_preview_dataset(self, client, sample_csv_file):
        """测试预览数据集"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "预览测试数据集",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "preview.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )

        dataset_id = create_response.json()["id"]

        # 预览数据
        response = await client.get(f"/api/datasets/{dataset_id}/preview?rows=5")

        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == "preview.csv"
        assert len(data["columns"]) == 4
        assert len(data["data"]) == 5
        assert data["total_rows"] == 100

    @pytest.mark.asyncio
    async def test_add_file_to_dataset(self, client, sample_csv_file):
        """测试向数据集添加文件"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "文件添加测试",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "file1.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )

        dataset_id = create_response.json()["id"]

        # 添加新文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df2 = pd.DataFrame({
                'timestamp': pd.date_range('2024-02-01', periods=50, freq='h'),
                'value': [i * 0.3 for i in range(50)],
            })
            df2.to_csv(f, index=False)
            new_file_path = f.name

        try:
            response = await client.post(
                f"/api/datasets/{dataset_id}/files",
                json={
                    "file_path": new_file_path,
                    "file_name": "file2.csv",
                    "role": "supplementary",
                    "row_count": 50,
                    "column_count": 2,
                    "file_size": 1024,
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["files"]) == 2
            assert data["total_row_count"] == 150  # 100 + 50
        finally:
            os.unlink(new_file_path)

    @pytest.mark.asyncio
    async def test_remove_file_from_dataset(self, client, sample_csv_file):
        """测试从数据集移除文件"""
        # 创建多文件数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "文件删除测试",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "file1.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    },
                    {
                        "file_path": sample_csv_file,
                        "file_name": "file2.csv",
                        "role": "supplementary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )

        dataset_id = create_response.json()["id"]
        files = create_response.json()["files"]
        file_to_delete = files[1]["id"]

        # 删除文件
        response = await client.delete(f"/api/datasets/{dataset_id}/files/{file_to_delete}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 1
        assert data["total_row_count"] == 100

    @pytest.mark.asyncio
    async def test_replace_dataset_files(self, client, sample_csv_file):
        """测试替换数据集文件列表"""
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "文件替换测试",
                "files": [
                    {
                        "file_path": sample_csv_file,
                        "file_name": "old_file.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )

        dataset_id = create_response.json()["id"]

        # 替换文件列表
        response = await client.put(
            f"/api/datasets/{dataset_id}/files",
            json=[
                {
                    "file_path": sample_csv_file,
                    "file_name": "new_file1.csv",
                    "role": "primary",
                    "row_count": 80,
                    "column_count": 3,
                    "file_size": 1024,
                },
                {
                    "file_path": sample_csv_file,
                    "file_name": "new_file2.csv",
                    "role": "supplementary",
                    "row_count": 20,
                    "column_count": 2,
                    "file_size": 512,
                }
            ]
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 2
        assert data["total_row_count"] == 100  # 80 + 20
        # 检查文件名
        file_names = [f["file_name"] for f in data["files"]]
        assert "new_file1.csv" in file_names
        assert "new_file2.csv" in file_names