from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import os
from app.config import settings

DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Connection pool optimization (M7-T101)
# Key insight: pool_pre_ping=True adds a "SELECT 1" before every query,
# which significantly impacts latency under high concurrency.
# We disable pool_pre_ping for lower latency, relying on pool_recycle for stale connections.
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_timeout=10,
    pool_recycle=3600,
    pool_pre_ping=False,
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def _check_alembic_version() -> bool:
    """检查 alembic_version 表是否存在，判断迁移是否已执行。
    
    Returns:
        True 如果 alembic_version 表存在且至少有一个版本记录
        False 如果表不存在或为空
    """
    from sqlalchemy import inspect, text
    
    try:
        async with engine.begin() as conn:
            # 检查 alembic_version 表是否存在
            result = await conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version')"
            ))
            table_exists = result.scalar()
            
            if not table_exists:
                return False
            
            # 检查是否有版本记录
            result = await conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
            count = result.scalar()
            return count > 0
    except Exception:
        return False


async def init_db():
    """初始化数据库
    
    生产环境：不再自动 create_all，而是检查 alembic 迁移状态
    如果检测到未迁移，打印警告并安全返回，不访问任何业务表
    """
    import logging
    
    migrated = await _check_alembic_version()
    
    if not migrated:
        logging.warning(
            "Database migration not detected. "
            "Please run 'alembic upgrade head' to initialize the database schema. "
            "See docs/tasks/M7/M7-T70-*.md for details."
        )
        # 未迁移时安全返回，不访问任何业务表
        return
    
    # 已迁移后才访问业务表
    async with async_session_maker() as session:
        from app.models import User, UserRole, UserStatus
        from app.services.auth import hash_password
        
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            import os
            import secrets
            
            # Get admin password from environment variable, generate secure random if not set
            admin_password = os.getenv("ADMIN_DEFAULT_PASSWORD")
            if not admin_password:
                # Generate a secure random password (32 chars alphanumeric) if env var not set
                admin_password = secrets.token_urlsafe(24)
                logging.warning(
                    "ADMIN_DEFAULT_PASSWORD not set in environment. "
                    "Generated temporary password for initial admin account. "
                    "Please set ADMIN_DEFAULT_PASSWORD env var and reset admin password."
                )
            
            admin_user = User(
                username="admin",
                password_hash=hash_password(admin_password),
                role=UserRole.admin.value,
                status=UserStatus.active.value,
                must_change_password=True,
            )
            session.add(admin_user)
            try:
                await session.commit()
                logging.info("Default admin user created successfully (username: admin)")
            except IntegrityError:
                await session.rollback()
                logging.info("Default admin user already exists; startup race handled safely")


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
