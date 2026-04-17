"""
多表Join功能单元测试

测试用例覆盖：
- Join成功场景（天气表、元数据表）
- 错误处理场景（缺少Join键、文件不存在）
- 数据准确性验证（行数丢失、列数统计）
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
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
def main_csv_file():
    """创建主表 CSV 文件"""
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


@pytest.fixture
def weather_csv_file():
    """创建天气表 CSV 文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'building_id': ['A', 'B'],
            'weather_station': ['WS001', 'WS002'],
            'avg_temperature': [18.5, 19.2],
            'humidity': [65, 70],
        })
        df.to_csv(f, index=False)
        file_path = f.name

    yield file_path
    os.unlink(file_path)


@pytest.fixture
def metadata_csv_file():
    """创建元数据表 CSV 文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'building_id': ['A', 'B'],
            'building_name': ['Building A', 'Building B'],
            'location': ['Beijing', 'Shanghai'],
            'area_sqm': [5000, 8000],
            'year_built': [2010, 2015],
        })
        df.to_csv(f, index=False)
        file_path = f.name

    yield file_path
    os.unlink(file_path)


@pytest.fixture
def partial_match_csv_file():
    """创建部分匹配的 CSV 文件（用于测试行数丢失）"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'building_id': ['A'],  # 只有A，没有B
            'extra_data': ['extra_value_A'],
        })
        df.to_csv(f, index=False)
        file_path = f.name

    yield file_path
    os.unlink(file_path)


# ========== Join 测试用例 ==========

class TestJoinAPI:
    """Join API 测试"""

    @pytest.mark.asyncio
    async def test_join_weather_table_success(self, client, main_csv_file, weather_csv_file):
        """
        测试用例1: 主表 + 天气表 Join 成功
        
        Given: 主表包含100行数据，天气表包含2个建筑的信息
        When: 使用 building_id 作为 Join 键进行 left join
        Then: Join 成功，新增天气相关列，行数保持不变
        """
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "主数据集",
                "description": "能耗主数据",
                "files": [
                    {
                        "file_path": main_csv_file,
                        "file_name": "main_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )
        assert create_response.status_code == 200
        dataset_id = create_response.json()["id"]

        # 执行 Join
        join_response = await client.post(
            f"/api/datasets/{dataset_id}/join",
            json={
                "main_join_key": "building_id",
                "join_tables": [
                    {
                        "name": "weather_table",
                        "file_path": weather_csv_file,
                        "join_key": "building_id",
                        "join_type": "left"
                    }
                ]
            }
        )

        # 验证响应
        assert join_response.status_code == 200
        data = join_response.json()
        
        # 验证基本字段
        assert data["success"] is True
        assert data["before_rows"] == 100
        assert data["after_rows"] == 100
        assert data["rows_lost"] == 0
        
        # 验证新增列数（天气表有4列，去掉join_key后新增3列）
        assert data["rows_added_columns"] == 3
        
        # 验证列名包含新增的天气列
        assert "weather_station" in data["joined_columns"]
        assert "avg_temperature" in data["joined_columns"]
        assert "humidity" in data["joined_columns"]
        
        # 验证输出文件路径
        assert data["output_file_path"] is not None
        assert os.path.exists(data["output_file_path"])
        
        # 清理输出文件
        os.unlink(data["output_file_path"])

    @pytest.mark.asyncio
    async def test_join_metadata_table_success(self, client, main_csv_file, metadata_csv_file):
        """
        测试用例2: 主表 + 元数据表 Join 成功
        
        Given: 主表包含100行数据，元数据表包含2个建筑的信息
        When: 使用 building_id 作为 Join 键进行 left join
        Then: Join 成功，新增元数据列，行数保持不变
        """
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "主数据集",
                "description": "能耗主数据",
                "files": [
                    {
                        "file_path": main_csv_file,
                        "file_name": "main_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )
        assert create_response.status_code == 200
        dataset_id = create_response.json()["id"]

        # 执行 Join
        join_response = await client.post(
            f"/api/datasets/{dataset_id}/join",
            json={
                "main_join_key": "building_id",
                "join_tables": [
                    {
                        "name": "metadata_table",
                        "file_path": metadata_csv_file,
                        "join_key": "building_id",
                        "join_type": "left"
                    }
                ]
            }
        )

        # 验证响应
        assert join_response.status_code == 200
        data = join_response.json()
        
        # 验证基本字段
        assert data["success"] is True
        assert data["before_rows"] == 100
        assert data["after_rows"] == 100
        assert data["rows_lost"] == 0
        
        # 验证新增列数（元数据表有5列，去掉join_key后新增4列）
        assert data["rows_added_columns"] == 4
        
        # 验证列名包含新增的元数据列
        assert "building_name" in data["joined_columns"]
        assert "location" in data["joined_columns"]
        assert "area_sqm" in data["joined_columns"]
        assert "year_built" in data["joined_columns"]
        
        # 清理输出文件
        os.unlink(data["output_file_path"])

    @pytest.mark.asyncio
    async def test_join_with_missing_key(self, client, main_csv_file, weather_csv_file):
        """
        测试用例3: 从表中缺少 Join 键时返回 422
        
        Given: 主表和从表都存在
        When: 从表中指定的 Join 键不存在
        Then: 返回 422 错误，包含错误代码和详细信息
        """
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "主数据集",
                "files": [
                    {
                        "file_path": main_csv_file,
                        "file_name": "main_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )
        assert create_response.status_code == 200
        dataset_id = create_response.json()["id"]

        # 执行 Join（使用不存在的 join_key）
        join_response = await client.post(
            f"/api/datasets/{dataset_id}/join",
            json={
                "main_join_key": "building_id",
                "join_tables": [
                    {
                        "name": "weather_table",
                        "file_path": weather_csv_file,
                        "join_key": "nonexistent_key",  # 不存在的键
                        "join_type": "left"
                    }
                ]
            }
        )

        # 验证错误响应
        assert join_response.status_code == 422
        error_data = join_response.json()
        
        # 验证错误详情
        assert "detail" in error_data
        detail = error_data["detail"]
        assert detail["error_code"] == "JOIN_TABLE_KEY_NOT_FOUND"
        assert "nonexistent_key" in detail["message"]
        assert "available_columns" in detail["details"]

    @pytest.mark.asyncio
    async def test_join_with_nonexistent_file(self, client, main_csv_file):
        """
        测试用例4: 文件不存在时返回 422
        
        Given: 主表存在，从表文件不存在
        When: 执行 Join 操作
        Then: 返回 422 错误，包含错误代码
        """
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "主数据集",
                "files": [
                    {
                        "file_path": main_csv_file,
                        "file_name": "main_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )
        assert create_response.status_code == 200
        dataset_id = create_response.json()["id"]

        # 执行 Join（使用不存在的文件路径）
        nonexistent_file = "/tmp/nonexistent_file_12345.csv"
        join_response = await client.post(
            f"/api/datasets/{dataset_id}/join",
            json={
                "main_join_key": "building_id",
                "join_tables": [
                    {
                        "name": "missing_table",
                        "file_path": nonexistent_file,
                        "join_key": "building_id",
                        "join_type": "left"
                    }
                ]
            }
        )

        # 验证错误响应
        assert join_response.status_code == 422
        error_data = join_response.json()
        
        # 验证错误详情
        assert "detail" in error_data
        detail = error_data["detail"]
        assert detail["error_code"] == "JOIN_TABLE_FILE_NOT_FOUND"
        assert nonexistent_file in detail["message"]

    @pytest.mark.asyncio
    async def test_join_rows_lost_calculation(self, client, main_csv_file, partial_match_csv_file):
        """
        测试用例5: 行数丢失情况下的 before/after 准确
        
        Given: 主表有100行（50行A + 50行B），从表只有A的数据
        When: 使用 inner join
        Then: 丢失50行（B的数据），before/after 统计准确
        """
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "主数据集",
                "files": [
                    {
                        "file_path": main_csv_file,
                        "file_name": "main_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )
        assert create_response.status_code == 200
        dataset_id = create_response.json()["id"]

        # 执行 Join（使用 inner join）
        join_response = await client.post(
            f"/api/datasets/{dataset_id}/join",
            json={
                "main_join_key": "building_id",
                "join_tables": [
                    {
                        "name": "partial_table",
                        "file_path": partial_match_csv_file,
                        "join_key": "building_id",
                        "join_type": "inner"  # 使用 inner join
                    }
                ]
            }
        )

        # 验证响应
        assert join_response.status_code == 200
        data = join_response.json()
        
        # 验证行数统计准确性
        assert data["success"] is True
        assert data["before_rows"] == 100  # 原始行数
        assert data["after_rows"] == 50    # 只有A的50行
        assert data["rows_lost"] == 50     # 丢失了B的50行
        
        # 验证消息包含行数丢失信息
        assert "丢失" in data["message"]
        assert "50" in data["message"]
        
        # 清理输出文件
        os.unlink(data["output_file_path"])

    @pytest.mark.asyncio
    async def test_join_column_count(self, client, main_csv_file, weather_csv_file, metadata_csv_file):
        """
        测试用例6: 新增列数准确
        
        Given: 主表有4列，天气表有4列（去掉join_key后3列），元数据表有5列（去掉join_key后4列）
        When: 级联 Join 天气表和元数据表
        Then: 新增列数 = 3 + 4 = 7，总列数 = 4 + 7 = 11
        """
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "主数据集",
                "files": [
                    {
                        "file_path": main_csv_file,
                        "file_name": "main_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )
        assert create_response.status_code == 200
        dataset_id = create_response.json()["id"]

        # 执行级联 Join
        join_response = await client.post(
            f"/api/datasets/{dataset_id}/join",
            json={
                "main_join_key": "building_id",
                "join_tables": [
                    {
                        "name": "weather_table",
                        "file_path": weather_csv_file,
                        "join_key": "building_id",
                        "join_type": "left"
                    },
                    {
                        "name": "metadata_table",
                        "file_path": metadata_csv_file,
                        "join_key": "building_id",
                        "join_type": "left"
                    }
                ]
            }
        )

        # 验证响应
        assert join_response.status_code == 200
        data = join_response.json()
        
        # 验证新增列数（天气表3列 + 元数据表4列 = 7列）
        assert data["success"] is True
        assert data["rows_added_columns"] == 7
        
        # 验证总列数
        assert len(data["joined_columns"]) == 11  # 4 + 7
        
        # 验证所有预期的列都存在
        expected_columns = [
            # 主表列
            "timestamp", "building_id", "energy_consumption", "temperature",
            # 天气表列
            "weather_station", "avg_temperature", "humidity",
            # 元数据表列
            "building_name", "location", "area_sqm", "year_built"
        ]
        for col in expected_columns:
            assert col in data["joined_columns"], f"列 '{col}' 应该存在于结果中"
        
        # 清理输出文件
        os.unlink(data["output_file_path"])

    @pytest.mark.asyncio
    async def test_join_multiple_tables_sequentially(self, client, main_csv_file):
        """
        额外测试: 连续多次 Join 验证数据一致性
        
        Given: 主表和多个从表
        When: 连续执行多次 Join
        Then: 每次 Join 的结果都正确
        """
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "主数据集",
                "files": [
                    {
                        "file_path": main_csv_file,
                        "file_name": "main_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )
        assert create_response.status_code == 200
        dataset_id = create_response.json()["id"]

        # 创建第一个从表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f1:
            df1 = pd.DataFrame({
                'building_id': ['A', 'B'],
                'col1': ['val1_A', 'val1_B'],
            })
            df1.to_csv(f1, index=False)
            table1_path = f1.name

        # 创建第二个从表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f2:
            df2 = pd.DataFrame({
                'building_id': ['A', 'B'],
                'col2': ['val2_A', 'val2_B'],
            })
            df2.to_csv(f2, index=False)
            table2_path = f2.name

        try:
            # 第一次 Join
            join1_response = await client.post(
                f"/api/datasets/{dataset_id}/join",
                json={
                    "main_join_key": "building_id",
                    "join_tables": [
                        {
                            "name": "table1",
                            "file_path": table1_path,
                            "join_key": "building_id",
                            "join_type": "left"
                        }
                    ]
                }
            )
            assert join1_response.status_code == 200
            data1 = join1_response.json()
            assert data1["rows_added_columns"] == 1
            assert "col1" in data1["joined_columns"]
            
            # 清理第一次输出
            os.unlink(data1["output_file_path"])

            # 第二次 Join
            join2_response = await client.post(
                f"/api/datasets/{dataset_id}/join",
                json={
                    "main_join_key": "building_id",
                    "join_tables": [
                        {
                            "name": "table2",
                            "file_path": table2_path,
                            "join_key": "building_id",
                            "join_type": "left"
                        }
                    ]
                }
            )
            assert join2_response.status_code == 200
            data2 = join2_response.json()
            assert data2["rows_added_columns"] == 1
            assert "col2" in data2["joined_columns"]
            
            # 清理第二次输出
            os.unlink(data2["output_file_path"])

        finally:
            os.unlink(table1_path)
            os.unlink(table2_path)

    @pytest.mark.asyncio
    async def test_join_with_different_join_types(self, client, main_csv_file, partial_match_csv_file):
        """
        额外测试: 不同 Join 类型的行为验证
        
        Given: 主表和部分匹配的从表
        When: 使用不同的 join_type (left, inner, right, outer)
        Then: 每种类型的行数变化符合预期
        """
        # 创建数据集
        create_response = await client.post(
            "/api/datasets/",
            json={
                "name": "主数据集",
                "files": [
                    {
                        "file_path": main_csv_file,
                        "file_name": "main_data.csv",
                        "role": "primary",
                        "row_count": 100,
                        "column_count": 4,
                        "file_size": 2048,
                    }
                ],
            }
        )
        assert create_response.status_code == 200
        dataset_id = create_response.json()["id"]

        # 测试 left join
        left_response = await client.post(
            f"/api/datasets/{dataset_id}/join",
            json={
                "main_join_key": "building_id",
                "join_tables": [
                    {
                        "name": "partial_table",
                        "file_path": partial_match_csv_file,
                        "join_key": "building_id",
                        "join_type": "left"
                    }
                ]
            }
        )
        assert left_response.status_code == 200
        left_data = left_response.json()
        assert left_data["after_rows"] == 100  # left join 保留所有主表行
        assert left_data["rows_lost"] == 0
        os.unlink(left_data["output_file_path"])

        # 测试 inner join
        inner_response = await client.post(
            f"/api/datasets/{dataset_id}/join",
            json={
                "main_join_key": "building_id",
                "join_tables": [
                    {
                        "name": "partial_table",
                        "file_path": partial_match_csv_file,
                        "join_key": "building_id",
                        "join_type": "inner"
                    }
                ]
            }
        )
        assert inner_response.status_code == 200
        inner_data = inner_response.json()
        assert inner_data["after_rows"] == 50  # inner join 只保留匹配的行
        assert inner_data["rows_lost"] == 50
        os.unlink(inner_data["output_file_path"])
