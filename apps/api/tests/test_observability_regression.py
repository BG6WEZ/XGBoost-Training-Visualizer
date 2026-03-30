"""
可观测性防回归测试

测试 Worker 状态端点和模型校验语义：
1. Worker 状态端点返回正确格式
2. 模型校验输出完整字段
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWorkerStatusEndpoint:
    """Worker 状态端点测试"""
    
    @pytest.mark.asyncio
    async def test_worker_status_endpoint_returns_correct_format(self):
        """测试 Worker 状态端点返回正确格式"""
        from app.routers.training import get_worker_status
        
        with patch("app.routers.training.get_queue_service") as mock_queue:
            mock_queue_service = MagicMock()
            mock_queue_service.redis = MagicMock()
            mock_queue_service.get_queue_length = AsyncMock(return_value=0)
            mock_queue.return_value = mock_queue_service
            
            result = await get_worker_status()
            
            assert "worker_status" in result
            assert "redis_status" in result
            assert "queue_length" in result
            assert "timestamp" in result
            assert result["worker_status"] in ["healthy", "degraded", "unavailable"]
            assert result["redis_status"] in ["connected", "disconnected"]
    
    @pytest.mark.asyncio
    async def test_worker_status_healthy_when_redis_connected(self):
        """测试 Redis 连接时 Worker 状态为 healthy"""
        from app.routers.training import get_worker_status
        
        with patch("app.routers.training.get_queue_service") as mock_queue:
            mock_queue_service = MagicMock()
            mock_queue_service.redis = MagicMock()
            mock_queue_service.get_queue_length = AsyncMock(return_value=0)
            mock_queue.return_value = mock_queue_service
            
            result = await get_worker_status()
            
            assert result["worker_status"] == "healthy"
            assert result["redis_status"] == "connected"
            assert result["queue_length"] == 0
    
    @pytest.mark.asyncio
    async def test_worker_status_unavailable_when_redis_disconnected(self):
        """测试 Redis 断开时 Worker 状态为 unavailable"""
        from app.routers.training import get_worker_status
        
        with patch("app.routers.training.get_queue_service") as mock_queue:
            mock_queue.side_effect = Exception("Redis connection refused")
            
            result = await get_worker_status()
            
            assert result["worker_status"] == "unavailable"
            assert result["redis_status"] == "disconnected"


class TestModelValidationSemantics:
    """模型校验语义测试"""
    
    def test_model_validation_includes_all_fields(self):
        """测试模型校验包含所有必需字段"""
        from scripts.e2e_validation import E2EResults
        
        results = E2EResults({
            "success": True,
            "experiment_id": "test-id",
            "steps": {
                "model_validation": {
                    "status": "success",
                    "model_type": "xgboost",
                    "format": "json",
                    "size_bytes": 1024,
                    "has_feature_names": True,
                    "has_target": True,
                    "validation_level": "full",
                    "message": "XGBoost model validated successfully"
                }
            },
            "error": None,
            "duration_seconds": 1.5
        })
        
        model_validation = results.steps["model_validation"]
        
        assert model_validation["model_type"] == "xgboost"
        assert model_validation["format"] == "json"
        assert model_validation["validation_level"] == "full"
        assert "message" in model_validation
    
    def test_model_validation_partial_for_unknown_type(self):
        """测试未知模型类型时校验级别为 partial"""
        from scripts.e2e_validation import E2EResults
        
        results = E2EResults({
            "success": True,
            "experiment_id": "test-id",
            "steps": {
                "model_validation": {
                    "status": "success",
                    "model_type": "unknown",
                    "format": "json",
                    "validation_level": "partial",
                    "message": "Model type not specified"
                }
            },
            "error": None,
            "duration_seconds": 1.5
        })
        
        model_validation = results.steps["model_validation"]
        
        assert model_validation["validation_level"] == "partial"


class TestWorkerStatusInServiceCheck:
    """服务检查中的 Worker 状态测试"""
    
    @pytest.mark.asyncio
    async def test_service_check_includes_worker_status(self):
        """测试服务检查包含 Worker 状态"""
        from scripts.e2e_validation import check_services
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_health_response = MagicMock()
            mock_health_response.status_code = 200
            mock_health_response.json.return_value = {"status": "healthy", "version": "1.0.0"}
            
            mock_ready_response = MagicMock()
            mock_ready_response.status_code = 200
            mock_ready_response.json.return_value = {"status": "ready", "checks": {}}
            
            mock_worker_response = MagicMock()
            mock_worker_response.status_code = 200
            mock_worker_response.json.return_value = {
                "worker_status": "healthy",
                "redis_status": "connected",
                "queue_length": 0
            }
            
            mock_context = AsyncMock()
            mock_context.get.side_effect = [mock_health_response, mock_ready_response, mock_worker_response]
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await check_services("http://localhost:8000")
            
            assert "worker" in result
            assert result["worker"]["status"] == "healthy"
            assert "redis_status" in result["worker"]
            assert "queue_length" in result["worker"]
    
    @pytest.mark.asyncio
    async def test_service_check_worker_unavailable(self):
        """测试 Worker 不可用时的状态"""
        from scripts.e2e_validation import check_services
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_health_response = MagicMock()
            mock_health_response.status_code = 200
            mock_health_response.json.return_value = {"status": "healthy", "version": "1.0.0"}
            
            mock_ready_response = MagicMock()
            mock_ready_response.status_code = 200
            mock_ready_response.json.return_value = {"status": "ready", "checks": {}}
            
            mock_worker_response = MagicMock()
            mock_worker_response.status_code = 404
            
            mock_context = AsyncMock()
            mock_context.get.side_effect = [mock_health_response, mock_ready_response, mock_worker_response]
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await check_services("http://localhost:8000")
            
            assert "worker" in result
            assert result["worker"]["status"] == "not_available"
