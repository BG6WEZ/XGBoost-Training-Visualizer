"""Alembic environment configuration for async SQLAlchemy.

This module is designed to work independently from app.config.Settings
to avoid pydantic validation errors (JWT_SECRET, etc.) during migration.
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Set required env vars BEFORE importing app modules to avoid pydantic validation errors
os.environ.setdefault("JWT_SECRET", "alembic-migration-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))

# Import database Base
from app.database import Base

# Import all models to ensure they are registered with Base.metadata
from app.models import models  # noqa: F401

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata


def get_database_url() -> str:
    """Get the database URL from environment or alembic.ini.
    
    Priority:
    1. DATABASE_URL environment variable
    2. sqlalchemy.url from alembic.ini
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        # Convert postgresql:// to postgresql+asyncpg:// for async driver
        if url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        return url
    
    # Fallback to alembic.ini setting
    url = config.get_main_option("sqlalchemy.url")
    if url and url != "postgresql+asyncpg://placeholder:placeholder@localhost:5432/placeholder":
        return url
    
    raise ValueError(
        "DATABASE_URL environment variable must be set "
        "or sqlalchemy.url must be configured in alembic.ini"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()