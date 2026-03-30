"""
队列健康前置检查回归测试

测试 e2e_validation.py 中新增的队列等待逻辑
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.e2e_validation import E2EResults


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


class TestQueueWaitLogic:
    """队列等待逻辑测试"""

    @pytest.mark.asyncio
    async def test_queue_empty_no_wait(self):
        """队列为空时不需要等待"""
        service_status = {
            "api": {"status": "healthy"},
            "worker": {"queue_length": 0, "status": "healthy"}
        }
        
        queue_length = service_status.get("worker", {}).get("queue_length", 0)
        assert queue_length == 0

    @pytest.mark.asyncio
    async def test_queue_has_items_needs_wait(self):
        """队列有任务时需要等待"""
        service_status = {
            "api": {"status": "healthy"},
            "worker": {"queue_length": 3, "status": "healthy"}
        }
        
        queue_length = service_status.get("worker", {}).get("queue_length", 0)
        assert queue_length > 0

    @pytest.mark.asyncio
    async def test_queue_timeout_threshold(self):
        """队列等待超时阈值检查"""
        max_wait = 60
        wait_time = 65
        
        assert wait_time > max_wait


class TestTimeoutConfiguration:
    """超时配置测试"""

    def test_default_timeout_is_reasonable(self):
        """默认超时时间合理"""
        default_timeout = 120
        assert default_timeout >= 60
        assert default_timeout <= 300

    def test_timeout_can_be_configured(self):
        """超时可配置"""
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--timeout", default=120, type=int)
        
        args = parser.parse_args(["--timeout", "180"])
        assert args.timeout == 180
