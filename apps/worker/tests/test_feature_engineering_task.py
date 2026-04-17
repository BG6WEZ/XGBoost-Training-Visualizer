"""Feature engineering task tests - Task 3.1 (M7-T72)

Test coverage:
- test_feature_engineering_runs (对应任务要求 #7)
"""
import pytest
from unittest.mock import patch

from app.tasks.training import run_feature_engineering_task


class TestFeatureEngineeringRuns:
    """测试: test_feature_engineering_runs
    
    核心验证点: 特征工程任务有可验证产物或状态
    """

    @pytest.mark.asyncio
    async def test_feature_engineering_runs(self, sample_csv_file, temp_dir, mock_storage):
        """验证特征工程任务能成功运行并产生可验证结果"""
        config = {
            "dataset_path": sample_csv_file,
            "task_id": "test_feature_eng_001",
            "time_features": {
                "enabled": True,
                "column": "timestamp",
                "features": ["hour", "dayofweek", "month", "is_weekend"],
            },
            "lag_features": {
                "enabled": True,
                "columns": ["feature_a"],
                "lags": [1, 2],
            },
            "rolling_features": {
                "enabled": False,
            },
        }

        with patch("app.storage.get_storage_service", return_value=mock_storage):
            result = await run_feature_engineering_task(
                ctx={},
                dataset_id="test_dataset_001",
                config=config,
            )

        # 验证任务成功完成
        assert result["status"] == "completed", f"Feature engineering should complete. Error: {result.get('error')}"

        # 验证新增特征
        assert "new_features" in result, "Result should include new features list"
        assert len(result["new_features"]) > 0, "Should have created new features"

        # 验证时间特征被创建
        new_feature_names = result["new_features"]
        assert any("hour" in f for f in new_feature_names), f"Should have hour feature. Features: {new_feature_names}"
        assert any("dayofweek" in f for f in new_feature_names), f"Should have dayofweek feature. Features: {new_feature_names}"

        # 验证滞后特征被创建
        assert any("lag" in f for f in new_feature_names), f"Should have lag features. Features: {new_feature_names}"

        # 验证总列数增加
        assert result["total_columns"] > len(result["original_columns"]), (
            f"Total columns ({result['total_columns']}) should be more than original ({len(result['original_columns'])})"
        )

        # 验证存储信息
        assert "storage_type" in result, "Result should include storage info"
        assert "object_key" in result, "Result should include object key"