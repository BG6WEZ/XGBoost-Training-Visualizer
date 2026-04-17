import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.auth import hash_password
from sqlalchemy import create_engine, text

sync_url = 'postgresql://xgboost:xgboost123@localhost:5432/xgboost_vis'
engine = create_engine(sync_url)

pwd_hash = hash_password('admin123')
print(f'Generated hash: {pwd_hash[:20]}...')

with engine.begin() as conn:
    result = conn.execute(text("SELECT 1 FROM users WHERE username = 'admin'"))
    if result.scalar_one_or_none():
        conn.execute(text("UPDATE users SET password_hash = :ph WHERE username = 'admin'"), {'ph': pwd_hash})
        print('Admin password updated successfully')
    else:
        uid = str(uuid.uuid4())
        conn.execute(
            text("INSERT INTO users (id, username, password_hash, role, status, must_change_password, created_at) VALUES (:id, 'admin', :ph, 'admin', 'active', false, NOW())"),
            {'id': uid, 'ph': pwd_hash}
        )
        print('Admin user created successfully')