#!/usr/bin/env python3
"""
数据库迁移脚本 - 用于检查和修复数据库结构

用法:
    python scripts/migrate_db.py --check       # 检查数据库结构
    python scripts/migrate_db.py --init        # 初始化新库（使用 psql）
    python scripts/migrate_db.py --upgrade     # 升级旧库（使用 psql）
    python scripts/migrate_db.py --verify      # 验证迁移结果
"""

import argparse
import asyncio
import os
import subprocess
import shutil
import sys
import urllib.parse
from pathlib import Path


def parse_database_url(database_url: str) -> dict:
    """解析 DATABASE_URL 获取连接参数"""
    # postgresql://user:password@host:port/database
    parsed = urllib.parse.urlparse(database_url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "database": parsed.path.lstrip("/") if parsed.path else "postgres",
    }


def get_migrations_dir() -> Path:
    """获取迁移脚本目录"""
    # 脚本在 apps/api/scripts/，迁移脚本在 apps/api/migrations/
    return Path(__file__).parent.parent / "migrations"


def run_psql(sql_file: Path) -> bool:
    """
    使用 psql 执行 SQL 文件

    返回: True 成功，False 失败
    """
    if not sql_file.exists():
        print(f"[X] 迁移脚本不存在: {sql_file}")
        return False

    # 检查 psql 是否可用
    psql_path = shutil.which("psql")
    if not psql_path:
        print("[X] psql 未安装或不在 PATH 中")
        print("\n请手动执行以下命令:")
        print(f"  psql -h <host> -U <user> -d <database> -f {sql_file}")
        return False

    # 解析数据库连接参数
    database_url = os.getenv("DATABASE_URL", "postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis")
    params = parse_database_url(database_url)

    # 设置环境变量传递密码
    env = os.environ.copy()
    if params["password"]:
        env["PGPASSWORD"] = params["password"]

    # 构建命令
    cmd = [
        psql_path,
        "-h", params["host"],
        "-p", str(params["port"]),
        "-U", params["user"],
        "-d", params["database"],
        "-f", str(sql_file),
        "-v", "ON_ERROR_STOP=1",  # 遇到错误时停止
    ]

    print(f"执行: {' '.join(cmd[:7])} -f {sql_file.name}")

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[X] 执行失败:\n{result.stderr}")
            return False
        if result.stdout:
            print(result.stdout)
        return True
    except Exception as e:
        print(f"[X] 执行异常: {e}")
        return False


def _check_sqlalchemy():
    """检查 sqlalchemy 是否可用"""
    try:
        from sqlalchemy import text  # noqa: F401
        from sqlalchemy.ext.asyncio import create_async_engine  # noqa: F401
        return True
    except ImportError:
        return False


async def get_engine():
    """获取数据库引擎"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
    except ImportError:
        raise ImportError("sqlalchemy 未安装，请执行: pip install sqlalchemy asyncpg")

    database_url = os.getenv("DATABASE_URL", "postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis")
    async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    return create_async_engine(async_url)


async def check_database():
    """检查数据库结构和连接"""
    if not _check_sqlalchemy():
        print("[X] sqlalchemy 未安装，请执行: pip install sqlalchemy asyncpg")
        return False

    from sqlalchemy import text

    print("=" * 60)
    print("检查数据库结构")
    print("=" * 60)

    engine = await get_engine()

    expected_tables = [
        "datasets",
        "dataset_files",
        "dataset_subsets",
        "experiments",
        "training_metrics",
        "training_logs",
        "models",
        "feature_importance",
        "async_tasks",
    ]

    async with engine.connect() as conn:
        # 检查表是否存在
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        existing_tables = [row[0] for row in result]

        print("\n表检查结果:")
        all_exist = True
        for table in expected_tables:
            exists = table in existing_tables
            status = "[OK] 存在" if exists else "[X] 不存在"
            print(f"  {table}: {status}")
            if not exists:
                all_exist = False

        # 检查关键字段
        print("\n关键字段检查:")

        # datasets 表字段
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'datasets'"
        ))
        dataset_columns = [row[0] for row in result]
        required_dataset_cols = ["time_column", "entity_column", "target_column",
                                  "total_row_count", "total_column_count", "total_file_size"]
        for col in required_dataset_cols:
            exists = col in dataset_columns
            status = "[OK]" if exists else "[X]"
            print(f"  datasets.{col}: {status}")

        # models 表字段
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'models'"
        ))
        models_columns = [row[0] for row in result]
        required_models_cols = ["storage_type", "object_key", "file_path"]
        for col in required_models_cols:
            exists = col in models_columns
            status = "[OK]" if exists else "[X]"
            print(f"  models.{col}: {status}")

        # async_tasks 表字段
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'async_tasks'"
        ))
        async_columns = [row[0] for row in result]
        required_async_cols = ["task_type", "dataset_id", "status", "config", "result"]
        for col in required_async_cols:
            exists = col in async_columns
            status = "[OK]" if exists else "[X]"
            print(f"  async_tasks.{col}: {status}")

    await engine.dispose()

    if all_exist:
        print("\n[OK] 数据库结构完整")
        return True
    else:
        print("\n[X] 数据库结构不完整，需要迁移")
        return False


def init_database():
    """初始化新数据库（使用 psql 执行 SQL 文件）"""
    print("=" * 60)
    print("初始化新数据库")
    print("=" * 60)

    migrations_dir = get_migrations_dir()
    init_script = migrations_dir / "001_init_schema.sql"

    if run_psql(init_script):
        print("[OK] 数据库初始化完成")
        return True
    return False


def upgrade_database():
    """升级旧数据库（使用 psql 执行 SQL 文件）"""
    print("=" * 60)
    print("升级旧数据库")
    print("=" * 60)

    migrations_dir = get_migrations_dir()
    upgrade_script = migrations_dir / "002_upgrade_multi_file.sql"

    if run_psql(upgrade_script):
        print("[OK] 数据库升级完成")
        return True
    return False


async def verify_migration():
    """验证迁移结果"""
    if not _check_sqlalchemy():
        print("[X] sqlalchemy 未安装，请执行: pip install sqlalchemy asyncpg")
        return False

    from sqlalchemy import text

    print("=" * 60)
    print("验证迁移结果")
    print("=" * 60)

    engine = await get_engine()

    async with engine.connect() as conn:
        # 检查 UUID 扩展
        result = await conn.execute(text(
            "SELECT * FROM pg_extension WHERE extname = 'uuid-ossp'"
        ))
        if result.rowcount > 0:
            print("[OK] uuid-ossp 扩展已安装")
        else:
            print("[X] uuid-ossp 扩展未安装")

        # 检查索引
        result = await conn.execute(text(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'dataset_files'"
        ))
        indexes = [row[0] for row in result]
        if "idx_dataset_files_dataset_id" in indexes:
            print("[OK] dataset_files 索引已创建")
        else:
            print("[X] dataset_files 索引未创建")

        # 检查触发器
        result = await conn.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgname LIKE 'update_%'"
        ))
        triggers = [row[0] for row in result]
        if "update_datasets_updated_at" in triggers:
            print("[OK] datasets updated_at 触发器已创建")
        else:
            print("[X] datasets updated_at 触发器未创建")

    await engine.dispose()
    return True


def main():
    parser = argparse.ArgumentParser(description="数据库迁移工具")
    parser.add_argument("--check", action="store_true", help="检查数据库结构")
    parser.add_argument("--init", action="store_true", help="初始化新数据库（使用 psql）")
    parser.add_argument("--upgrade", action="store_true", help="升级旧数据库（使用 psql）")
    parser.add_argument("--verify", action="store_true", help="验证迁移结果")

    args = parser.parse_args()

    if args.check:
        asyncio.run(check_database())
    elif args.init:
        init_database()
    elif args.upgrade:
        upgrade_database()
    elif args.verify:
        asyncio.run(verify_migration())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()