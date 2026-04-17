"""Training task tests - Task 3.1 (M7-T72)

Test coverage:
- test_xgboost_trainer_loads_csv (对应任务要求 #1)
- test_xgboost_trainer_runs_training (对应任务要求 #2)
- test_xgboost_trainer_early_stopping (对应任务要求 #3)
- test_xgboost_trainer_invalid_target_column (对应任务要求 #4)
- test_xgboost_trainer_saves_metrics (对应任务要求 #5)
"""
import os
import json
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from app.tasks.training import XGBoostTrainer, run_training_task


class TestXGBoostTrainerLoadsCSV:
    """测试: test_xgboost_trainer_loads_csv
    
    核心验证点: 训练器能正确读取 CSV 并解析数据
    """

    @pytest.mark.asyncio
    async def test_xgboost_trainer_loads_csv(self, sample_csv_file):
        """验证训练器正确加载 CSV 文件并解析特征和目标列"""
        trainer = XGBoostTrainer(
            experiment_id="test_exp_001",
            config={"target_column": "target"},
            dataset_path=sample_csv_file,
            work_dir="/tmp/test_workdir",
        )

        X_train, X_val, y_train, y_val, feature_names = await trainer.load_data()

        # 验证数据加载成功
        assert len(X_train) > 0, "Training data should not be empty"
        assert len(X_val) > 0, "Validation data should not be empty"
        assert len(y_train) > 0, "Training labels should not be empty"
        assert len(y_val) > 0, "Validation labels should not be empty"

        # 验证特征列数正确 (3 features: timestamp, feature_a, feature_b after encoding)
        assert len(feature_names) >= 3, f"Should have at least 3 features, got {len(feature_names)}"

        # 验证划分比例 (默认 test_size=0.2)
        total_samples = len(X_train) + len(X_val)
        assert len(X_train) == int(total_samples * 0.8), "Train/val split should be 80/20"


class TestXGBoostTrainerRunsTraining:
    """测试: test_xgboost_trainer_runs_training
    
    核心验证点: 训练后确实生成 model 文件
    """

    @pytest.mark.asyncio
    async def test_xgboost_trainer_runs_training(self, sample_csv_file, temp_dir):
        """验证训练器能完成训练并保存模型文件"""
        trainer = XGBoostTrainer(
            experiment_id="test_exp_002",
            config={
                "target_column": "target",
                "xgboost_params": {"n_estimators": 10, "max_depth": 3},
            },
            dataset_path=sample_csv_file,
            work_dir=temp_dir,
        )

        # 执行训练
        result = await trainer.train()

        # 验证训练结果
        assert result["status"] if "status" in result else True
        assert "metrics" in result, "Result should contain metrics"
        assert "feature_importance" in result, "Result should contain feature importance"
        assert result["n_features"] > 0, "Should have trained with features"
        assert len(result["feature_names"]) > 0, "Should have feature names"

        # 保存模型
        model_path = await trainer.save_model("json")

        # 验证模型文件确实生成
        assert os.path.exists(model_path), f"Model file should exist at {model_path}"
        assert os.path.getsize(model_path) > 0, "Model file should not be empty"


class TestXGBoostTrainerEarlyStopping:
    """测试: test_xgboost_trainer_early_stopping
    
    核心验证点: early stopping 真的触发并提前终止
    """

    @pytest.mark.asyncio
    async def test_xgboost_trainer_early_stopping(self, sample_csv_file, temp_dir):
        """验证 early stopping 机制能够正常工作"""
        trainer = XGBoostTrainer(
            experiment_id="test_exp_003",
            config={
                "target_column": "target",
                "xgboost_params": {"n_estimators": 1000, "max_depth": 3},
                "early_stopping_rounds": 5,
            },
            dataset_path=sample_csv_file,
            work_dir=temp_dir,
        )

        result = await trainer.train()

        # 验证 early stopping 触发了（best_iteration 远小于 n_estimators）
        best_iteration = result.get("best_iteration", 0)
        assert best_iteration < 1000, (
            f"Early stopping should have triggered. Best iteration: {best_iteration}"
        )
        # 通常 early stopping 会在 10-30 轮内触发，用 200 作为宽松阈值
        assert best_iteration < 200, (
            f"Early stopping should have triggered early. Best iteration: {best_iteration}"
        )


class TestXGBoostTrainerInvalidTargetColumn:
    """测试: test_xgboost_trainer_invalid_target_column
    
    核心验证点: 目标列不存在时返回明确错误
    """

    @pytest.mark.asyncio
    async def test_xgboost_trainer_invalid_target_column(self, sample_csv_missing_target):
        """验证目标列不存在时抛出明确的 ValueError"""
        trainer = XGBoostTrainer(
            experiment_id="test_exp_004",
            config={"target_column": "nonexistent_column"},
            dataset_path=sample_csv_missing_target,
            work_dir="/tmp/test_workdir",
        )

        with pytest.raises(ValueError) as exc_info:
            await trainer.load_data()

        # 验证错误信息包含有用的上下文
        error_message = str(exc_info.value)
        assert "nonexistent_column" in error_message or "not found" in error_message.lower(), (
            f"Error message should mention the missing column: {error_message}"
        )

    @pytest.mark.asyncio
    async def test_xgboost_trainer_invalid_target_values(self, sample_csv_invalid_target):
        """验证目标列包含无效值时抛出明确的 ValueError"""
        trainer = XGBoostTrainer(
            experiment_id="test_exp_005",
            config={"target_column": "target"},
            dataset_path=sample_csv_invalid_target,
            work_dir="/tmp/test_workdir",
        )

        with pytest.raises(ValueError) as exc_info:
            await trainer.load_data()

        error_message = str(exc_info.value)
        assert "Invalid" in error_message or "invalid" in error_message, (
            f"Error message should mention invalid values: {error_message}"
        )


class TestXGBoostTrainerSavesMetrics:
    """测试: test_xgboost_trainer_saves_metrics
    
    核心验证点: metrics 列表非空，包含训练过程指标
    """

    @pytest.mark.asyncio
    async def test_xgboost_trainer_saves_metrics(self, sample_csv_file, temp_dir):
        """验证训练过程中正确收集 metrics"""
        trainer = XGBoostTrainer(
            experiment_id="test_exp_006",
            config={
                "target_column": "target",
                "xgboost_params": {"n_estimators": 20, "max_depth": 3},
            },
            dataset_path=sample_csv_file,
            work_dir=temp_dir,
        )

        result = await trainer.train()

        # 验证 metrics 列表非空
        assert len(trainer.metrics) > 0, "Metrics list should not be empty after training"

        # 验证第一个 metric 的结构
        first_metric = trainer.metrics[0]
        assert "iteration" in first_metric, "Metric should have iteration"
        assert "train_loss" in first_metric, "Metric should have train_loss"
        assert "val_loss" in first_metric, "Metric should have val_loss"

        # 验证 metrics 数量与训练轮数匹配
        assert len(trainer.metrics) == 20, f"Should have 20 metric entries, got {len(trainer.metrics)}"

        # 验证结果中包含 metrics
        assert "metrics" in result, "Result should contain metrics"
        assert "val_rmse" in result["metrics"], "Result metrics should include val_rmse"


class TestRunTrainingTaskIntegration:
    """集成测试: run_training_task 端到端流程"""

    @pytest.mark.asyncio
    async def test_run_training_task_completes(self, sample_csv_file, temp_dir):
        """验证 run_training_task 函数完成并返回结果"""
        config = {
            "dataset_path": sample_csv_file,
            "work_dir": temp_dir,
            "target_column": "target",
            "xgboost_params": {"n_estimators": 10, "max_depth": 3},
            "model_format": "json",
        }

        with patch("app.storage.get_storage_service") as mock_storage:
            mock_storage.return_value.save_prediction_data = AsyncMock()

            result = await run_training_task(
                ctx={},
                experiment_id="test_exp_007",
                config=config,
            )

        # 验证任务完成
        assert result["status"] == "completed", f"Task should complete successfully. Error: {result.get('error')}"
        assert "model_path" in result, "Result should include model path"
        assert os.path.exists(result["model_path"]), f"Model file should exist: {result['model_path']}"
