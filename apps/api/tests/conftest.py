import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import asyncio
import os

# 设置测试环境变量
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-32chars")
os.environ.setdefault("DEBUG", "true")


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# 测试环境数据库初始化 - 保留 create_all 方式
# =============================================================================
# 测试环境不使用 Alembic 迁移，而是直接使用 SQLAlchemy 的 create_all
# 这样可以确保测试独立运行，不依赖外部数据库迁移状态

from app.database import Base


@pytest_asyncio.fixture
async def test_engine():
    """创建测试数据库引擎"""
    from app.config import settings
    test_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    
    # SQLite 不需要转换驱动
    if test_url.startswith("sqlite"):
        engine = create_async_engine(test_url, echo=False)
    else:
        # PostgreSQL: 确保使用 asyncpg 驱动
        if test_url.startswith("postgresql://"):
            test_url = test_url.replace("postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(test_url, echo=False)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """创建测试数据库会话，使用 create_all 初始化 schema"""
    from app.config import settings
    
    # 使用 create_all 初始化 schema（测试环境专用）
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        yield session
        await session.close()
