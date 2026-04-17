"""
参数校验测试

测试目标：
1. 验证单字段越界校验
2. 验证组合规则冲突校验
3. 验证错误响应结构
"""
import pytest
from app.services.parameter_validation import (
    ParameterValidationService,
    ValidationRuleCode,
    FieldError,
)


class TestParameterValidation:
    """参数校验测试"""

    def test_learning_rate_too_high(self):
        """测试学习率越界（>1）"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=1.5,
            max_depth=6,
            n_estimators=100,
            subsample=1.0,
            colsample_bytree=1.0,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.LEARNING_RATE_OUT_OF_RANGE.value for e in result.field_errors)
        print("✓ 学习率越界校验通过")

    def test_learning_rate_too_low(self):
        """测试学习率越界（<0.001）"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.0001,
            max_depth=6,
            n_estimators=100,
            subsample=1.0,
            colsample_bytree=1.0,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.LEARNING_RATE_OUT_OF_RANGE.value for e in result.field_errors)
        print("✓ 学习率过低校验通过")

    def test_n_estimators_too_small(self):
        """测试 n_estimators 过小（<10）"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.1,
            max_depth=6,
            n_estimators=5,
            subsample=1.0,
            colsample_bytree=1.0,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.N_ESTIMATORS_TOO_SMALL.value for e in result.field_errors)
        print("✓ n_estimators 过小校验通过")

    def test_early_stopping_too_large(self):
        """测试 early_stopping_rounds >= n_estimators"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.1,
            max_depth=6,
            n_estimators=50,
            subsample=1.0,
            colsample_bytree=1.0,
            early_stopping_rounds=60,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.EARLY_STOPPING_TOO_LARGE.value for e in result.field_errors)
        print("✓ early_stopping_rounds 过大校验通过")

    def test_low_lr_low_estimators_conflict(self):
        """测试低学习率 + 低迭代轮数冲突"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.01,
            max_depth=6,
            n_estimators=80,
            subsample=1.0,
            colsample_bytree=1.0,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.LOW_LR_LOW_ESTIMATORS.value for e in result.field_errors)
        
        error = next(e for e in result.field_errors if e.rule == ValidationRuleCode.LOW_LR_LOW_ESTIMATORS.value)
        assert 'learning_rate' in error.current
        assert 'n_estimators' in error.current
        print("✓ 低学习率+低迭代轮数冲突校验通过")

    def test_high_depth_high_sample_conflict(self):
        """测试高深度 + 高采样率冲突"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.1,
            max_depth=12,
            n_estimators=100,
            subsample=0.98,
            colsample_bytree=0.98,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.HIGH_DEPTH_HIGH_SAMPLE.value for e in result.field_errors)
        print("✓ 高深度+高采样率冲突校验通过")

    def test_max_depth_out_of_range(self):
        """测试 max_depth 越界"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.1,
            max_depth=20,
            n_estimators=100,
            subsample=1.0,
            colsample_bytree=1.0,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.MAX_DEPTH_OUT_OF_RANGE.value for e in result.field_errors)
        print("✓ max_depth 越界校验通过")

    def test_valid_params_pass(self):
        """测试合法参数通过校验"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.1,
            max_depth=6,
            n_estimators=100,
            subsample=1.0,
            colsample_bytree=1.0,
            early_stopping_rounds=10,
        )
        
        assert result.valid == True
        assert len(result.field_errors) == 0
        print("✓ 合法参数校验通过")

    def test_valid_conservative_params(self):
        """测试保守模板参数通过校验"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.01,
            max_depth=3,
            n_estimators=500,
            subsample=0.8,
            colsample_bytree=0.8,
            early_stopping_rounds=20,
        )
        
        assert result.valid == True
        print("✓ 保守模板参数校验通过")

    def test_valid_aggressive_params(self):
        """测试激进模板参数通过校验"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.3,
            max_depth=9,
            n_estimators=50,
            subsample=1.0,
            colsample_bytree=1.0,
            early_stopping_rounds=5,
        )
        
        assert result.valid == True
        print("✓ 激进模板参数校验通过")

    def test_subsample_out_of_range(self):
        """测试 subsample 越界"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.1,
            max_depth=6,
            n_estimators=100,
            subsample=1.5,
            colsample_bytree=1.0,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.SUBSAMPLE_OUT_OF_RANGE.value for e in result.field_errors)
        print("✓ subsample 越界校验通过")

    def test_colsample_out_of_range(self):
        """测试 colsample_bytree 越界"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.1,
            max_depth=6,
            n_estimators=100,
            subsample=1.0,
            colsample_bytree=0.05,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.COLSAMPLE_OUT_OF_RANGE.value for e in result.field_errors)
        print("✓ colsample_bytree 越界校验通过")

    def test_high_depth_low_child_weight_conflict(self):
        """测试高深度 + 低 min_child_weight 冲突"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.1,
            max_depth=12,
            n_estimators=100,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=0.1,
        )
        
        assert result.valid == False
        assert any(e.rule == ValidationRuleCode.HIGH_DEPTH_LOW_CHILD_WEIGHT.value for e in result.field_errors)
        print("✓ 高深度+低min_child_weight冲突校验通过")

    def test_error_response_structure(self):
        """测试错误响应结构"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=0.01,
            max_depth=6,
            n_estimators=80,
            subsample=1.0,
            colsample_bytree=1.0,
        )
        
        assert result.valid == False
        assert len(result.field_errors) > 0
        
        error = result.field_errors[0]
        assert hasattr(error, 'fields')
        assert hasattr(error, 'rule')
        assert hasattr(error, 'current')
        assert hasattr(error, 'suggestion')
        assert isinstance(error.fields, list)
        assert isinstance(error.rule, str)
        assert isinstance(error.current, dict)
        assert isinstance(error.suggestion, str)
        print("✓ 错误响应结构正确")

    def test_validate_xgboost_params_dict(self):
        """测试 validate_xgboost_params 方法"""
        result = ParameterValidationService.validate_xgboost_params({
            'learning_rate': 0.1,
            'max_depth': 6,
            'n_estimators': 100,
            'subsample': 1.0,
            'colsample_bytree': 1.0,
        })
        
        assert result.valid == True
        print("✓ validate_xgboost_params 方法正确")

    def test_multiple_errors(self):
        """测试多个错误同时存在"""
        result = ParameterValidationService.validate_training_params(
            learning_rate=2.0,
            max_depth=20,
            n_estimators=5,
            subsample=1.5,
            colsample_bytree=1.5,
        )
        
        assert result.valid == False
        assert len(result.field_errors) >= 4
        print(f"✓ 多错误同时存在校验通过，共 {len(result.field_errors)} 个错误")
