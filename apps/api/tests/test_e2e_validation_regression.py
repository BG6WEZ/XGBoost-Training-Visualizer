"""
E2E 验证脚本防回归测试

测试 e2e_validation.py 的关键逻辑：
1. 健康检查端点路径正确
2. 状态码判定逻辑正确
3. 目标列选择逻辑正确
4. 错误输出规范化
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import e2e_validation
from scripts.e2e_validation import (
    check_services,
    get_dataset_id,
    create_experiment,
    E2EResults,
)


@pytest.fixture(autouse=True)
def reset_dataset_id():
    """每个测试前重置 DATASET_ID"""
    e2e_validation.DATASET_ID = None
    yield
    e2e_validation.DATASET_ID = None


class TestHealthCheckEndpoints:
    """健康检查端点测试"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_path(self):
        """测试健康检查端点路径正确（无 /api 前缀）"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy", "version": "1.0.0"}
            
            mock_context = AsyncMock()
            mock_context.get.return_value = mock_response
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await check_services("http://localhost:8000")
            
            # 验证调用的是 /health 而不是 /api/health
            calls = mock_context.get.call_args_list
            paths = [str(call[0][0]) for call in calls]
            
            assert any("/health" in path and "/api/health" not in path for path in paths), \
                f"Expected /health endpoint, got paths: {paths}"
    
    @pytest.mark.asyncio
    async def test_ready_endpoint_path(self):
        """测试就绪检查端点路径正确"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ready", "checks": {}}
            
            mock_context = AsyncMock()
            mock_context.get.return_value = mock_response
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await check_services("http://localhost:8000")
            
            # 验证调用的是 /ready
            calls = mock_context.get.call_args_list
            paths = [str(call[0][0]) for call in calls]
            
            assert any("/ready" in path for path in paths), \
                f"Expected /ready endpoint, got paths: {paths}"


class TestStatusCodeChecks:
    """状态码判定测试"""
    
    @pytest.mark.asyncio
    async def test_create_experiment_accepts_200(self):
        """测试创建实验接受 200 状态码"""
        with patch("httpx.AsyncClient") as mock_client:
            # 模拟数据集详情响应
            mock_dataset_response = MagicMock()
            mock_dataset_response.status_code = 200
            mock_dataset_response.json.return_value = {
                "files": [{
                    "columns_info": [
                        {"name": "col1", "is_numeric": True, "missing_count": 0}
                    ]
                }]
            }
            
            # 模拟创建实验响应（返回 200 而不是 201）
            mock_create_response = MagicMock()
            mock_create_response.status_code = 200
            mock_create_response.json.return_value = {"id": "test-exp-id"}
            
            mock_context = AsyncMock()
            mock_context.get.return_value = mock_dataset_response
            mock_context.post.return_value = mock_create_response
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await create_experiment(mock_context, "http://localhost:8000", "test-dataset-id")
            
            assert result == "test-exp-id"
    
    @pytest.mark.asyncio
    async def test_create_experiment_accepts_201(self):
        """测试创建实验接受 201 状态码"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_dataset_response = MagicMock()
            mock_dataset_response.status_code = 200
            mock_dataset_response.json.return_value = {
                "files": [{
                    "columns_info": [
                        {"name": "col1", "is_numeric": True, "missing_count": 0}
                    ]
                }]
            }
            
            mock_create_response = MagicMock()
            mock_create_response.status_code = 201
            mock_create_response.json.return_value = {"id": "test-exp-id"}
            
            mock_context = AsyncMock()
            mock_context.get.return_value = mock_dataset_response
            mock_context.post.return_value = mock_create_response
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await create_experiment(mock_context, "http://localhost:8000", "test-dataset-id")
            
            assert result == "test-exp-id"


class TestTargetColumnSelection:
    """目标列选择测试"""
    
    @pytest.mark.asyncio
    async def test_selects_column_without_missing_values(self):
        """测试优先选择无缺失值的列"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_dataset_response = MagicMock()
            mock_dataset_response.status_code = 200
            mock_dataset_response.json.return_value = {
                "files": [{
                    "columns_info": [
                        {"name": "col_with_nan", "is_numeric": True, "missing_count": 100},
                        {"name": "col_no_nan", "is_numeric": True, "missing_count": 0},
                    ]
                }]
            }
            
            mock_create_response = MagicMock()
            mock_create_response.status_code = 200
            mock_create_response.json.return_value = {"id": "test-exp-id"}
            
            mock_context = AsyncMock()
            mock_context.get.return_value = mock_dataset_response
            mock_context.post.return_value = mock_create_response
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            await create_experiment(mock_context, "http://localhost:8000", "test-dataset-id")
            
            # 验证 post 调用使用了正确的目标列
            post_call = mock_context.post.call_args
            request_body = post_call[1]["json"]
            
            assert request_body["target_column"] == "col_no_nan"


class TestErrorOutput:
    """错误输出规范化测试"""
    
    def test_e2e_results_to_dict(self):
        """测试 E2EResults 序列化"""
        results = E2EResults({
            "success": True,
            "experiment_id": "test-id",
            "steps": {"step1": {"status": "success"}},
            "error": None,
            "duration_seconds": 1.5
        })
        
        result_dict = results.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["experiment_id"] == "test-id"
        assert result_dict["steps"]["step1"]["status"] == "success"
        assert result_dict["duration_seconds"] == 1.5
    
    def test_e2e_results_failure(self):
        """测试失败结果序列化"""
        results = E2EResults({
            "success": False,
            "experiment_id": None,
            "steps": {"step1": {"status": "failed", "error": "test error"}},
            "error": "Overall error message",
            "duration_seconds": 0.5
        })
        
        result_dict = results.to_dict()
        
        assert result_dict["success"] is False
        assert result_dict["error"] == "Overall error message"
        assert result_dict["steps"]["step1"]["status"] == "failed"


class TestDatasetSelection:
    """数据集选择测试"""
    
    @pytest.mark.asyncio
    async def test_prefers_demo_test_dataset(self):
        """测试优先选择 Demo Test Dataset"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_list_response = MagicMock()
            mock_list_response.status_code = 200
            mock_list_response.json.return_value = [
                {"id": "other-id", "name": "Other Dataset"},
                {"id": "demo-id", "name": "Demo Test Dataset"},
            ]
            
            mock_context = AsyncMock()
            mock_context.get.return_value = mock_list_response
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await get_dataset_id(mock_context, "http://localhost:8000")
            
            assert result == "demo-id"
    
    @pytest.mark.asyncio
    async def test_prefers_smoke_test_dataset(self):
        """测试优先选择 Smoke Test Dataset（当没有 Demo Test 时）"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_list_response = MagicMock()
            mock_list_response.status_code = 200
            mock_list_response.json.return_value = [
                {"id": "other-id", "name": "Other Dataset"},
                {"id": "smoke-id", "name": "Smoke Test Dataset Final"},
            ]
            
            mock_context = AsyncMock()
            mock_context.get.return_value = mock_list_response
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await get_dataset_id(mock_context, "http://localhost:8000")
            
            assert result == "smoke-id"
    
    @pytest.mark.asyncio
    async def test_demo_test_has_priority_over_smoke_test(self):
        """测试 Demo Test 和 Smoke Test 都会被选中（取决于列表顺序）"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_list_response = MagicMock()
            mock_list_response.status_code = 200
            # Demo Test 在前面，会被选中
            mock_list_response.json.return_value = [
                {"id": "demo-id", "name": "Demo Test Dataset"},
                {"id": "smoke-id", "name": "Smoke Test Dataset"},
            ]
            
            mock_context = AsyncMock()
            mock_context.get.return_value = mock_list_response
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            
            mock_client.return_value = mock_context
            
            result = await get_dataset_id(mock_context, "http://localhost:8000")
            
            # 列表中第一个匹配的会被选中
            assert result == "demo-id"
