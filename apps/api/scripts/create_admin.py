import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Use environment DATABASE_URL if set (Docker), otherwise fallback to localhost (local dev)
if not os.environ.get('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis'
if not os.environ.get('JWT_SECRET'):
    os.environ['JWT_SECRET'] = 'test-secret-key-not-for-production'

from app.config import settings
from app.database import engine
from app.services.auth import hash_password
from sqlalchemy import text

async def create_admin():
    pwd_hash = hash_password("admin123")
    sql = """
        UPDATE users
        SET password_hash = :password_hash
        WHERE username = 'admin'
    """
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1 FROM users WHERE username = 'admin'"))
        if result.scalar_one_or_none():
            await conn.execute(text(sql), {"password_hash": pwd_hash})
            print("Admin password updated successfully")
        else:
            insert_sql = """
                INSERT INTO users (id, username, password_hash, role, status, must_change_password, created_at)
                VALUES (gen_random_uuid(), 'admin', :password_hash, 'admin', 'active', false, NOW())
            """
            await conn.execute(text(insert_sql), {"password_hash": pwd_hash})
            print("Admin user created successfully")

asyncio.run(create_admin())