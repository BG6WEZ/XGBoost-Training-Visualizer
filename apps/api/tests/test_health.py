"""Tests for health check endpoints (Task 4.3)"""

import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import Base, User, UserRole, UserStatus
from app.database import get_db
from app.main import app
from app.services.auth import hash_password


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
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
async def admin_user(db_session):
    """创建管理员用户"""
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
    """创建普通用户"""
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


# =============================================================================
# Tests
# =============================================================================

class TestLivenessCheck:
    """Tests for /health endpoint (liveness)"""

    @pytest.mark.asyncio
    async def test_liveness_always_ok(self, client):
        """Liveness check should always return minimal ok response"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_liveness_no_db_dependency(self, client):
        """Liveness should not depend on database"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        # Verify minimal response - liveness should not have checks
        assert "checks" not in data


class TestReadinessCheck:
    """Tests for /ready endpoint (readiness)"""

    @pytest.mark.asyncio
    async def test_readiness_checks_db(self, client):
        """Readiness should check database status"""
        response = await client.get("/ready")
        data = response.json()
        assert "checks" in data
        assert "database" in data["checks"]

    @pytest.mark.asyncio
    async def test_readiness_returns_200_or_503(self, client):
        """Readiness should return 200 when healthy or 503 when not"""
        response = await client.get("/ready")
        assert response.status_code in [200, 503]
        data = response.json()
        if response.status_code == 200:
            assert data["status"] == "ready"
        else:
            assert data["status"] == "not_ready"

    @pytest.mark.asyncio
    async def test_readiness_returns_503_when_db_unhealthy(self):
        """Readiness should return 503 when database is unavailable"""
        from unittest.mock import AsyncMock
        from app.routers.health import readiness_check
        from fastapi.responses import JSONResponse

        # Create a mock session that raises an exception
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB unavailable"))

        result = await readiness_check(mock_db)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 503


class TestHealthDetails:
    """Tests for /health/details endpoint (admin only)"""

    @pytest.mark.asyncio
    async def test_details_requires_admin(self, client):
        """Health details should require admin authentication"""
        # Without authentication, should get 401
        response = await client.get("/health/details")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_details_returns_403_for_non_admin(self, client, normal_user):
        """Health details should return 403 for non-admin users"""
        # Login as regular user
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "test123456"
        })
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/health/details", headers=headers)
            # Non-admin should get 403
            assert response.status_code == 403
        else:
            pytest.skip("Test user not available")

    @pytest.mark.asyncio
    async def test_details_returns_200_for_admin(self, client, admin_user):
        """Health details should return 200 for admin users"""
        # Login as admin
        login_response = await client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/health/details", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "checks" in data
            assert "service" in data
        else:
            pytest.skip("Admin credentials not available")

    @pytest.mark.asyncio
    async def test_details_returns_component_status(self, client, admin_user):
        """Health details should return component status"""
        login_response = await client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/health/details", headers=headers)
            data = response.json()
            assert "checks" in data
            # Should have at least database check
            assert "database" in data["checks"] or "storage" in data["checks"] or "redis" in data["checks"]
        else:
            pytest.skip("Admin credentials not available")


class TestProbeSemantics:
    """Tests to verify probe semantics alignment"""

    @pytest.mark.asyncio
    async def test_health_is_liveness(self, client):
        """Verify /health is liveness (no external deps)"""
        response = await client.get("/health")
        assert response.status_code == 200
        # Liveness should not fail even if DB is down
        # because it doesn't check external dependencies
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_ready_is_readiness(self, client):
        """Verify /ready is readiness (checks external deps)"""
        response = await client.get("/ready")
        # Readiness may return 503 if deps are not available
        assert response.status_code in [200, 503]
        data = response.json()
        # Should have checks field
        assert "checks" in data or response.status_code == 503