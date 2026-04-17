"""
认证功能测试

P1-T15: 简化登录与用户管理
测试登录、登出、用户信息、修改密码、用户管理功能
"""
import os
import pytest
import uuid
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models import Base, User, UserRole, UserStatus
from app.database import get_db
from app.main import app
from app.services.auth import hash_password


class TestJwtSecretValidation:
    """JWT_SECRET 启动校验测试"""

    def test_missing_jwt_secret_raises(self, monkeypatch):
        """未设 JWT_SECRET 时启动应抛出 ValueError"""
        # 清除环境变量中的 JWT_SECRET
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

        # 清除 lru_cache 以强制重新创建 Settings
        from app.config import get_settings
        get_settings.cache_clear()

        # Also prevent .env file from providing a fallback value
        from app.config import Settings as OriginalSettings

        class TestSettings(OriginalSettings):
            class Config:
                env_file = ".env.nonexistent"
                case_sensitive = True
                extra = "ignore"

        with pytest.raises(ValueError, match="JWT_SECRET must be set"):
            TestSettings()

    def test_missing_database_url_raises(self, monkeypatch):
        """未设 DATABASE_URL 时启动应抛出 ValueError"""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("JWT_SECRET", "test-secret-for-validation")

        from app.config import get_settings
        get_settings.cache_clear()

        with pytest.raises(ValueError, match="DATABASE_URL must be set"):
            from app.config import Settings
            Settings()


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db_session):
    user = User(
        id=uuid.uuid4(),
        username="admin",
        password_hash=hash_password("admin123"),
        role=UserRole.admin.value,
        status=UserStatus.active.value,
        must_change_password=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def normal_user(db_session):
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        password_hash=hash_password("test123456"),
        role=UserRole.user.value,
        status=UserStatus.active.value,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def disabled_user(db_session):
    user = User(
        id=uuid.uuid4(),
        username="disabled_user",
        password_hash=hash_password("test123456"),
        role=UserRole.user.value,
        status=UserStatus.disabled.value,
    )
    db_session.add(user)
    await db_session.commit()
    return user


class TestLogin:
    """登录测试"""

    @pytest.mark.asyncio
    async def test_login_success(self, client, admin_user):
        """登录成功"""
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, admin_user):
        """密码错误"""
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client):
        """用户不存在"""
        response = await client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_disabled_user(self, client, disabled_user):
        """登录被禁用用户"""
        response = await client.post(
            "/api/auth/login",
            json={"username": "disabled_user", "password": "test123456"}
        )
        assert response.status_code == 403
        assert "用户已被禁用" in response.json()["detail"]


class TestAuthMe:
    """获取当前用户信息测试"""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client, admin_user):
        """获取当前用户信息成功"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_get_me_no_token(self, client):
        """无令牌"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401


class TestChangePassword:
    """修改密码测试"""

    @pytest.mark.asyncio
    async def test_change_password_success(self, client, admin_user):
        """修改密码成功"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "admin123", "new_password": "newpassword123"}
        )
        assert response.status_code == 200
        assert "密码修改成功" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, client, admin_user):
        """原密码错误"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "wrongpassword", "new_password": "newpassword123"}
        )
        assert response.status_code == 400
        assert "原密码错误" in response.json()["detail"]


class TestUserManagement:
    """用户管理测试 - 使用 /api/admin/users 路径"""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, client, admin_user, normal_user):
        """管理员获取用户列表"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["users"]) == 2

    @pytest.mark.asyncio
    async def test_list_users_as_normal_user(self, client, normal_user):
        """普通用户无权获取用户列表"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "test123456"}
        )
        token = login_response.json()["access_token"]

        response = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_user_success(self, client, admin_user):
        """管理员创建用户"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={"username": "newuser", "password": "newpassword123", "role": "user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "user"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, client, admin_user, normal_user):
        """创建重复用户名"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.post(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={"username": "testuser", "password": "newpassword123", "role": "user"}
        )
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_disable_user(self, client, admin_user, normal_user):
        """禁用用户"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.patch(
            f"/api/admin/users/{normal_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_cannot_disable_self(self, client, admin_user):
        """不能禁用自己"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.patch(
            f"/api/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"}
        )
        assert response.status_code == 400
        assert "不能禁用自己的账号" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reset_password(self, client, admin_user, normal_user):
        """重置密码"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.post(
            f"/api/admin/users/{normal_user.id}/reset-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"new_password": "resetpassword123"}
        )
        assert response.status_code == 200
        assert "密码重置成功" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_generate_password(self, client, admin_user):
        """生成随机密码"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.post(
            "/api/admin/users/generate-password",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "password" in response.json()
        assert len(response.json()["password"]) == 12


class TestLogout:
    """登出测试"""

    @pytest.mark.asyncio
    async def test_logout_success(self, client, admin_user):
        """登出成功"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "登出成功" in response.json()["message"]


class TestMustChangePassword:
    """首次登录强制改密测试 - Task 1.4"""

    @pytest.mark.asyncio
    async def test_admin_must_change_password_on_first_login(self, client, admin_user):
        """默认 admin 首次登录返回 must_change_password=true"""
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["must_change_password"] is True

    @pytest.mark.asyncio
    async def test_normal_user_no_must_change_password(self, client, normal_user):
        """普通用户创建时 must_change_password=false"""
        response = await client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "test123456"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["must_change_password"] is False

    @pytest.mark.asyncio
    async def test_change_password_clears_flag(self, client, admin_user):
        """改密成功后清除 must_change_password 标记"""
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # 首次登录 must_change_password=true
        assert login_response.json()["user"]["must_change_password"] is True

        # 修改密码
        change_response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "admin123", "new_password": "newpassword123"}
        )
        assert change_response.status_code == 200

        # 再次登录 must_change_password=false
        login_response2 = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "newpassword123"}
        )
        assert login_response2.status_code == 200
        assert login_response2.json()["user"]["must_change_password"] is False


class TestTokenBlacklist:
    """Token 黑名单测试 - Task 1.5 (M7-T61)"""

    @pytest.mark.asyncio
    async def test_create_access_token_includes_jti(self, client, admin_user):
        """验证 create_access_token 自动注入 JTI claim"""
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        # Decode the token to check claims
        from jose import jwt
        from app.config import settings
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        assert "jti" in payload
        assert isinstance(payload["jti"], str)
        assert len(payload["jti"]) > 0

    @pytest.mark.asyncio
    async def test_logout_revokes_token(self, client, admin_user, monkeypatch):
        """
        验证：登出后，使用同一 token 请求 /auth/me 返回 401
        使用 mock Redis 模拟黑名单
        """
        from app.services.auth import token_blacklist

        # 使用内存字典模拟 Redis
        mock_store = {}

        class MockRedis:
            def setex(self, key, ttl, value):
                mock_store[key] = value
            def exists(self, key):
                return 1 if key in mock_store else 0
            def ping(self):
                return True

        monkeypatch.setattr(token_blacklist, 'redis_client', MockRedis())

        # 1. 登录
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # 2. 验证 token 有效
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200

        # 3. 登出
        response = await client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "登出成功"

        # 4. 尝试用同一 token 请求 /auth/me
        response = await client.get("/api/auth/me", headers=headers)
        # 应返回 401（token 已被吊销）
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_without_redis_degrades_gracefully(self, client, admin_user, monkeypatch):
        """
        验证：Redis 不可用时，logout 和 login 仍正常工作
        """
        # 模拟 Redis 不可用
        from app.services.auth import token_blacklist
        monkeypatch.setattr(token_blacklist, 'redis_client', None)

        # 登录
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        token1 = response.json()["access_token"]

        # 登出（应该成功，即使 Redis 不可用）
        headers = {"Authorization": f"Bearer {token1}"}
        response = await client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200

        # 重新登录（应该成功）
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        token2 = response.json()["access_token"]

        # Token 应该不同（因为 JTI 随机）
        assert token1 != token2

    @pytest.mark.asyncio
    async def test_revoked_token_rejected(self, client, admin_user, monkeypatch):
        """
        验证：黑名单中的 token 被拒绝
        使用 mock Redis 模拟黑名单
        """
        from app.services.auth import token_blacklist

        # 使用内存字典模拟 Redis
        mock_store = {}

        class MockRedis:
            def setex(self, key, ttl, value):
                mock_store[key] = value
            def exists(self, key):
                return 1 if key in mock_store else 0
            def ping(self):
                return True

        monkeypatch.setattr(token_blacklist, 'redis_client', MockRedis())

        # 登录
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 验证 token 有效
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200

        # 登出（将 token 加入黑名单）
        response = await client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200

        # 再次尝试使用已吊销的 token，应该被拒绝
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
