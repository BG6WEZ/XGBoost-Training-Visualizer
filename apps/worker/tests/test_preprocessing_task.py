"""Preprocessing task tests - Task 3.1 (M7-T72)

Test coverage:
- test_preprocessing_runs_successfully (对应任务要求 #6)
"""
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.tasks.training import run_preprocessing_task


class TestPreprocessingRunsSuccessfully:
    """测试: test_preprocessing_runs_successfully
    
    核心验证点: 预处理/特征工程任务有可验证产物或状态
    """

    @pytest.mark.asyncio
    async def test_preprocessing_runs_successfully(self, sample_csv_file, temp_dir, mock_storage):
        """验证预处理任务能成功运行并产生可验证结果"""
        config = {
            "dataset_path": sample_csv_file,
            "task_id": "test_preprocess_001",
            "missing_value_strategy": "drop_rows",
            "remove_duplicates": True,
            "handle_outliers": True,
        }

        with patch("app.storage.get_storage_service", return_value=mock_storage):
            result = await run_preprocessing_task(
                ctx={},
                dataset_id="test_dataset_001",
                config=config,
            )

        # 验证任务成功完成
        assert result["status"] == "completed", f"Preprocessing should complete. Error: {result.get('error')}"

        # 验证形状信息
        assert result["original_shape"][1] > 0, "Original data should have columns"
        assert result["processed_shape"][1] > 0, "Processed data should have columns"

        # 验证 summary 包含预期的处理步骤
        summary = result["summary"]
        assert "missing_value_handling" in summary, "Summary should include missing value handling"
        assert "remove_duplicates" in summary, "Summary should include duplicate removal"

        # 验证存储信息
        assert "storage_type" in result, "Result should include storage info"
        assert "object_key" in result, "Result should include object key"
        assert result["file_size"] > 0, "Processed file size should be positive"