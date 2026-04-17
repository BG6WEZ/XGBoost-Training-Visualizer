"""Test database helper - provides create_all for test environment.

This module is used by tests to initialize the database schema directly,
bypassing Alembic migrations. This ensures tests can run independently
without requiring a running PostgreSQL with migrations.
"""
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base


async def init_test_db():
    """Initialize test database using create_all.
    
    This is used in conftest.py for testing purposes.
    """
    from app.config import settings
    
    # Use SQLite for testing by default
    test_db_url = settings.DATABASE_URL
    if test_db_url.startswith("sqlite"):
        engine = create_async_engine(test_db_url, echo=False)
    else:
        # For tests that use PostgreSQL, use the test database
        engine = create_async_engine(test_db_url, echo=False)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return engine, async_session


async def cleanup_test_db(engine):
    """Clean up test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """Provide a database session for tests with automatic cleanup."""
    import os
    
    # Set test database URL
    original_url = os.environ.get("DATABASE_URL")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    
    engine, async_session = await init_test_db()
    
    async with async_session() as session:
        yield session
        await session.close()
    
    await cleanup_test_db(engine)
    
    # Restore original URL
    if original_url is not None:
        os.environ["DATABASE_URL"] = original_url