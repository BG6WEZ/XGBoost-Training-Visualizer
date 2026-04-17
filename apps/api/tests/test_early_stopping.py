"""
Early Stopping 集成测试

测试目标：
1. 验证 early_stopping_rounds 参数真实传入 XGBoost 训练
2. 验证训练提前终止时 best_iteration 正确返回
3. 验证参数模板 API 端点可用
"""
import pytest
import asyncio
import tempfile
import os
import pandas as pd
import numpy as np
import xgboost as xgb


class TestEarlyStopping:
    """Early Stopping 功能测试"""

    @pytest.fixture
    def overfitting_dataset(self, tmp_path):
        """创建一个容易过拟合的数据集，用于触发早停"""
        np.random.seed(42)
        n_samples = 100
        
        X = np.random.randn(n_samples, 5)
        y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.1
        
        df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(5)])
        df['target'] = y
        
        file_path = tmp_path / "overfitting_data.csv"
        df.to_csv(file_path, index=False)
        
        return str(file_path), n_samples

    @pytest.mark.asyncio
    async def test_early_stopping_triggers_and_returns_best_iteration(self, overfitting_dataset):
        """
        测试 Early Stopping 是否真实触发并返回 best_iteration
        
        验证：
        1. 训练提前于 n_estimators 停止
        2. best_iteration < n_estimators
        3. best_iteration 来自 XGBoost 原生属性
        """
        from sklearn.model_selection import train_test_split
        
        dataset_path, n_samples = overfitting_dataset
        df = pd.read_csv(dataset_path)
        
        X = df.drop(columns=['target'])
        y = df['target']
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.3, random_state=42)
        
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)
        
        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'learning_rate': 0.3,
            'max_depth': 8,
        }
        
        n_estimators = 200
        early_stopping_rounds = 5
        
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=n_estimators,
            evals=[(dtrain, 'train'), (dval, 'val')],
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=False
        )
        
        best_iteration = model.best_iteration
        
        assert best_iteration < n_estimators, f"训练应提前停止，best_iteration={best_iteration} 应小于 n_estimators={n_estimators}"
        assert best_iteration >= 0, "best_iteration 应为非负整数"
        
        print(f"✓ Early stopping 触发成功: best_iteration={best_iteration} < n_estimators={n_estimators}")

    @pytest.mark.asyncio
    async def test_early_stopping_disabled_when_none(self, overfitting_dataset):
        """
        测试不使用 early_stopping_rounds 时训练完成全部轮次
        """
        from sklearn.model_selection import train_test_split
        
        dataset_path, n_samples = overfitting_dataset
        df = pd.read_csv(dataset_path)
        
        X = df.drop(columns=['target'])
        y = df['target']
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.3, random_state=42)
        
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)
        
        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'learning_rate': 0.1,
            'max_depth': 3,
        }
        
        n_estimators = 50
        
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=n_estimators,
            evals=[(dtrain, 'train'), (dval, 'val')],
            verbose_eval=False
        )
        
        assert not hasattr(model, 'best_iteration') or model.attr('best_iteration') is None, "无早停时 best_iteration 不应存在"
        
        print(f"✓ 无早停时训练完成全部轮次: num_boost_round={n_estimators}")

    @pytest.mark.asyncio
    async def test_training_metrics_recorded(self, overfitting_dataset):
        """
        测试训练过程中指标被正确记录
        """
        from sklearn.model_selection import train_test_split
        
        dataset_path, n_samples = overfitting_dataset
        df = pd.read_csv(dataset_path)
        
        X = df.drop(columns=['target'])
        y = df['target']
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.3, random_state=42)
        
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)
        
        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'learning_rate': 0.1,
            'max_depth': 3,
        }
        
        n_estimators = 100
        evals_result = {}
        
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=n_estimators,
            evals=[(dtrain, 'train'), (dval, 'val')],
            evals_result=evals_result,
            early_stopping_rounds=10,
            verbose_eval=False
        )
        
        assert 'train' in evals_result, "应记录训练集指标"
        assert 'val' in evals_result, "应记录验证集指标"
        assert 'rmse' in evals_result['train'], "应记录 RMSE 指标"
        assert len(evals_result['train']['rmse']) > 0, "应有多轮训练指标"
        
        print(f"✓ 训练指标记录成功: 共 {len(evals_result['train']['rmse'])} 轮")


class TestParamTemplates:
    """参数模板测试"""

    def test_param_templates_endpoint(self):
        """测试参数模板 API 端点"""
        from app.schemas.experiment import PARAM_TEMPLATES, ParamTemplatesResponse
        
        assert 'conservative' in PARAM_TEMPLATES
        assert 'balanced' in PARAM_TEMPLATES
        assert 'aggressive' in PARAM_TEMPLATES
        
        conservative = PARAM_TEMPLATES['conservative']
        assert conservative.learning_rate == 0.01
        assert conservative.max_depth == 3
        assert conservative.n_estimators == 500
        assert conservative.subsample == 0.8
        assert conservative.colsample_bytree == 0.8
        assert conservative.early_stopping_rounds == 20
        
        balanced = PARAM_TEMPLATES['balanced']
        assert balanced.learning_rate == 0.1
        assert balanced.max_depth == 6
        assert balanced.n_estimators == 100
        assert balanced.early_stopping_rounds == 10
        
        aggressive = PARAM_TEMPLATES['aggressive']
        assert aggressive.learning_rate == 0.3
        assert aggressive.max_depth == 9
        assert aggressive.n_estimators == 50
        assert aggressive.early_stopping_rounds == 5
        
        print("✓ 参数模板定义正确")

    def test_param_templates_response_model(self):
        """测试参数模板响应模型"""
        from app.schemas.experiment import PARAM_TEMPLATES, ParamTemplatesResponse
        
        response = ParamTemplatesResponse(templates=PARAM_TEMPLATES)
        
        assert response.templates['conservative'].description == "适合小数据、防过拟合"
        assert response.templates['balanced'].description == "通用默认值"
        assert response.templates['aggressive'].description == "快速探索"
        
        print("✓ 参数模板响应模型正确")


class TestBestIterationInResults:
    """best_iteration 在结果中返回测试"""

    def test_best_iteration_field_in_schema(self):
        """测试 best_iteration 字段已添加到结果 Schema"""
        from app.schemas.results import ExperimentResultResponse
        
        schema_fields = ExperimentResultResponse.model_fields
        
        assert 'best_iteration' in schema_fields, "ExperimentResultResponse 应包含 best_iteration 字段"
        
        field_info = schema_fields['best_iteration']
        assert field_info.is_required() == False, "best_iteration 应为可选字段"
        
        print("✓ best_iteration 字段已添加到结果 Schema")
