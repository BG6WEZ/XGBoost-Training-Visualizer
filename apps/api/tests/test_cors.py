"""CORS 配置测试 - Task 2.2 (M7-T66, M7-T67)"""
import os
from unittest.mock import patch

from fastapi.testclient import TestClient


class TestCorsConfig:
    """CORS 配置解析测试"""

    def test_cors_origins_default(self):
        """验证默认 CORS origins 为 ["http://localhost:3000"]"""
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}, clear=False):
            os.environ.pop("CORS_ORIGINS", None)
            from app.config import Settings
            origins = Settings.parse_cors_origins()
            assert origins == ["http://localhost:3000"]

    def test_cors_origins_from_env(self):
        """验证环境变量覆盖 CORS origins"""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://app.example.com, https://admin.example.com"}):
            from app.config import Settings
            origins = Settings.parse_cors_origins()
            assert origins == ["https://app.example.com", "https://admin.example.com"]

    def test_cors_origins_from_env_with_empty_values(self):
        """验证环境变量中的空值被过滤"""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://app.example.com,  , https://admin.example.com, "}):
            from app.config import Settings
            origins = Settings.parse_cors_origins()
            assert origins == ["https://app.example.com", "https://admin.example.com"]

    def test_cors_origins_from_env_single(self):
        """验证单个 origin 环境变量"""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://app.example.com"}):
            from app.config import Settings
            origins = Settings.parse_cors_origins()
            assert origins == ["https://app.example.com"]

    def test_cors_origins_empty_env_falls_back_to_default(self):
        """验证空环境变量时回退到默认值"""
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}):
            from app.config import Settings
            origins = Settings.parse_cors_origins()
            assert origins == ["http://localhost:3000"]


class TestCorsPreflight:
    """CORS 预检请求 HTTP 行为测试"""

    def test_cors_preflight_allows_configured_origin(self):
        """验证允许的 origin 的 OPTIONS 预检请求返回正确的 CORS headers"""
        # 清除环境变量以确保使用默认配置
        os.environ.pop("CORS_ORIGINS", None)

        # 重新加载配置（清除缓存）
        from app.config import get_settings
        get_settings.cache_clear()

        from app.main import app
        client = TestClient(app)

        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        methods = response.headers.get("access-control-allow-methods", "")
        assert "GET" in methods
        assert "POST" in methods
        assert "DELETE" in methods

    def test_cors_preflight_rejects_unconfigured_origin(self):
        """验证未允许的 origin 不会返回匹配的 access-control-allow-origin"""
        # 清除环境变量以确保使用默认配置
        os.environ.pop("CORS_ORIGINS", None)

        from app.config import get_settings
        get_settings.cache_clear()

        from app.main import app
        client = TestClient(app)

        response = client.options(
            "/api/health",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            }
        )

        # 验证不允许的 origin 不会被放行
        allow_origin = response.headers.get("access-control-allow-origin")
        assert allow_origin != "https://evil.example.com", \
            f"Unconfigured origin should not be allowed, but got: {allow_origin}"