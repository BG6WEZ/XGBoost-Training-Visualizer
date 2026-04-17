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


class TestAsyncLineCount:
    """异步行计数测试 - Task 2.1 (M7-T62)"""

    @pytest.mark.asyncio
    async def test_count_lines_async_small_file(self):
        """验证异步行计数对小文件的正确性"""
        import tempfile
        import os
        from app.services.storage import count_lines_async

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write("a,b,c\n")
            f.write("1,2,3\n")
            f.write("4,5,6\n")
            temp_path = f.name

        try:
            count = await count_lines_async(temp_path)
            assert count == 3
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_count_lines_async_empty_file(self):
        """验证异步行计数对空文件的处理"""
        import tempfile
        import os
        from app.services.storage import count_lines_async

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            temp_path = f.name

        try:
            count = await count_lines_async(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_estimate_line_count_accuracy(self):
        """验证采样估算的精度（±20%）"""
        import tempfile
        import os
        from app.services.storage import estimate_line_count

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            for i in range(10000):
                f.write(f"line_{i},data_{i},value_{i}\n")
            temp_path = f.name

        try:
            estimated = await estimate_line_count(temp_path, sample_lines=1000)
            actual = 10000
            error = abs(estimated - actual) / actual
            # 允许 ±20% 误差（采样估算的固有特性）
            assert error < 0.2, f"估算误差过大：{error*100:.1f}%"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_estimate_line_count_empty_file(self):
        """验证采样估算对空文件返回 0"""
        import tempfile
        import os
        from app.services.storage import estimate_line_count

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            temp_path = f.name

        try:
            estimated = await estimate_line_count(temp_path)
            assert estimated == 0
        finally:
            os.unlink(temp_path)


class TestLargeFileUpload:
    """大文件上传不阻塞测试 - Task 2.1 延迟根因定位 + 30s 门槛达标 (M7-T65)"""

    @pytest.mark.asyncio
    async def test_upload_large_csv_over_50mb_does_not_block(self, tmp_path):
        """
        验证：上传 >50MB CSV 文件不超时（统一异步处理）
        
        使用 >50MB 的文件测试，确保：
        1. 请求在 30s 内完成（显式断言）
        2. 返回 200 且含 row_count
        3. 对触发估算分支的文件（>100MB），estimated == true
        """
        import time
        from httpx import AsyncClient, ASGITransport, Timeout

        # 阶段 1：生成 >50MB 的 CSV 文件（使用高效写入，不计入计时）
        large_file_path = tmp_path / "large_50mb.csv"
        
        # 使用固定宽度行，减少循环开销
        # 每行约 48 bytes: "col1=0000000000,col2=0000000000,col3=0000000000\n"
        line = "col1=0000000000,col2=0000000000,col3=0000000000\n"
        line_bytes = len(line.encode('utf-8'))  # ~48 bytes
        target_size = 55 * 1024 * 1024  # 55MB（确保 >50MB）
        num_lines = target_size // line_bytes + 1

        with open(large_file_path, 'w', encoding='utf-8') as f:
            f.write("col1,col2,col3\n")  # 表头
            for i in range(num_lines):
                f.write(line)

        file_size = os.path.getsize(large_file_path)
        assert file_size > 50 * 1024 * 1024, f"Test file must be >50MB, got {file_size / (1024*1024):.1f}MB"

        # 创建带长超时的客户端（避免测试环境超时）
        timeout = Timeout(300.0, connect=10.0)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", timeout=timeout) as ac:
            # 阶段 2：计时上传请求（仅计时请求本身）
            start_time = time.time()
            with open(large_file_path, 'rb') as f:
                response = await ac.post(
                    "/api/datasets/upload",
                    files={"file": ("large_50mb.csv", f, "text/csv")}
                )
            elapsed = time.time() - start_time

            # 断言
            assert response.status_code == 200, f"Upload failed with status {response.status_code}"
            data = response.json()
            assert "row_count" in data, "Response missing row_count"
            assert data["row_count"] is not None, "row_count should not be None"
            # 验证行计数正确（应该等于 num_lines）
            assert data["row_count"] == num_lines, f"Row count mismatch: got {data['row_count']}, expected {num_lines}"
            
            # 验证 estimated 字段
            # 10MB-100MB 使用异步计数（estimated=None），>100MB 使用采样估算（estimated=True）
            if file_size >= 100 * 1024 * 1024:
                assert data.get("estimated") == True, f"Large file ({file_size / (1024*1024):.1f}MB) should have estimated=true"
            
            # 显式断言 30s 门槛（Task 2.1 验收标准）
            assert elapsed < 30, f"Upload took {elapsed:.2f}s, must be <30s"
            
            # 清理
            os.unlink(large_file_path)

            # 记录耗时（用于审计证据）
            print(f"\nLarge file upload (>50MB): {file_size / (1024*1024):.1f}MB, elapsed={elapsed:.2f}s, row_count={data['row_count']}")
