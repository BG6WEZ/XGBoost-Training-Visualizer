"""
E2E 队列健康前置检查回归测试

测试目标：确保 e2e_validation.py 中的队列健康前置检查逻辑正确工作
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from scripts.e2e_validation import run_e2e_validation, E2EResults


class TestQueueHealthCheck:
    """队列健康前置检查测试"""

    @pytest.mark.asyncio
    async def test_queue_empty_proceeds_immediately(self):
        """队列空时立即继续执行"""
        mock_client = AsyncMock()
        
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"queue_length": 0, "worker_status": "healthy"}
        
        mock_client.get = AsyncMock(return_value=mock_get_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        service_status = {
            "api": {"status": "healthy"},
            "worker": {"queue_length": 0, "status": "healthy"}
        }
        
        with patch('scripts.e2e_validation.check_services', return_value=service_status):
            with patch('scripts.e2e_validation.httpx.AsyncClient', return_value=mock_client):
                with patch('scripts.e2e_validation.get_dataset_id', return_value="test-dataset-id"):
                    with patch('scripts.e2e_validation.split_dataset', return_value={"subsets": []}):
                        with patch('scripts.e2e_validation.create_experiment', return_value="exp-id"):
                            with patch('scripts.e2e_validation.start_training', return_value={"queue_position": 0}):
                                with patch('scripts.e2e_validation.wait_for_completion', return_value=True):
                                    with patch('scripts.e2e_validation.get_results', return_value={"model": {}}):
                                        with patch('scripts.e2e_validation.download_model', return_value=b'{"learner": {}}'):
                                            result = await run_e2e_validation("http://localhost:8000", 120, True)
        
        assert result.success == True

    @pytest.mark.asyncio
    async def test_queue_wait_timeout_returns_error(self):
        """队列等待超时返回错误"""
        service_status = {
            "api": {"status": "healthy"},
            "worker": {"queue_length": 5, "status": "healthy"}
        }
        
        mock_client = AsyncMock()
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"queue_length": 5}
        mock_client.get = AsyncMock(return_value=mock_get_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('scripts.e2e_validation.check_services', return_value=service_status):
            with patch('scripts.e2e_validation.httpx.AsyncClient', return_value=mock_client):
                result = await run_e2e_validation("http://localhost:8000", 120, True)
        
        assert result.success == False
        assert "Queue not empty" in result.error

    @pytest.mark.asyncio
    async def test_queue_clears_then_proceeds(self):
        """队列清空后继续执行"""
        call_count = [0]
        
        def mock_get_training_status(*args, **kwargs):
            call_count[0] += 1
            response = MagicMock()
            response.status_code = 200
            if call_count[0] <= 3:
                response.json.return_value = {"queue_length": 2}
            else:
                response.json.return_value = {"queue_length": 0}
            return response
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=mock_get_training_status)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        service_status = {
            "api": {"status": "healthy"},
            "worker": {"queue_length": 2, "status": "healthy"}
        }
        
        with patch('scripts.e2e_validation.check_services', return_value=service_status):
            with patch('scripts.e2e_validation.httpx.AsyncClient', return_value=mock_client):
                with patch('scripts.e2e_validation.get_dataset_id', return_value="test-dataset-id"):
                    with patch('scripts.e2e_validation.split_dataset', return_value={"subsets": []}):
                        with patch('scripts.e2e_validation.create_experiment', return_value="exp-id"):
                            with patch('scripts.e2e_validation.start_training', return_value={"queue_position": 0}):
                                with patch('scripts.e2e_validation.wait_for_completion', return_value=True):
                                    with patch('scripts.e2e_validation.get_results', return_value={"model": {}}):
                                        with patch('scripts.e2e_validation.download_model', return_value=b'{"learner": {}}'):
                                            result = await run_e2e_validation("http://localhost:8000", 120, True)
        
        assert result.success == True
        assert "queue_check" in result.steps


class TestE2EResultsModel:
    """E2EResults 数据模型测试"""

    def test_success_parsing(self):
        """成功结果解析"""
        data = {
            "success": True,
            "experiment_id": "test-exp-id",
            "steps": {"step1": {"status": "success"}},
            "error": None,
            "duration_seconds": 10.5
        }
        result = E2EResults(data)
        assert result.success == True
        assert result.experiment_id == "test-exp-id"
        assert result.error is None

    def test_failure_parsing(self):
        """失败结果解析"""
        data = {
            "success": False,
            "experiment_id": None,
            "steps": {},
            "error": "Connection refused",
            "duration_seconds": 1.0
        }
        result = E2EResults(data)
        assert result.success == False
        assert result.error == "Connection refused"

    def test_to_dict(self):
        """转换为字典"""
        data = {
            "success": True,
            "experiment_id": "exp-123",
            "steps": {"check": "passed"},
            "error": None,
            "duration_seconds": 5.0
        }
        result = E2EResults(data)
        output = result.to_dict()
        assert output["success"] == True
        assert output["experiment_id"] == "exp-123"
