"""
参数校验服务

提供训练参数的组合规则校验，确保参数配置合理。
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationRuleCode(str, Enum):
    """校验规则代码"""
    LOW_LR_LOW_ESTIMATORS = "LOW_LR_LOW_ESTIMATORS"
    HIGH_DEPTH_HIGH_SAMPLE = "HIGH_DEPTH_HIGH_SAMPLE"
    EARLY_STOPPING_TOO_LARGE = "EARLY_STOPPING_TOO_LARGE"
    HIGH_DEPTH_LOW_CHILD_WEIGHT = "HIGH_DEPTH_LOW_CHILD_WEIGHT"
    LEARNING_RATE_OUT_OF_RANGE = "LEARNING_RATE_OUT_OF_RANGE"
    N_ESTIMATORS_TOO_SMALL = "N_ESTIMATORS_TOO_SMALL"
    MAX_DEPTH_OUT_OF_RANGE = "MAX_DEPTH_OUT_OF_RANGE"
    SUBSAMPLE_OUT_OF_RANGE = "SUBSAMPLE_OUT_OF_RANGE"
    COLSAMPLE_OUT_OF_RANGE = "COLSAMPLE_OUT_OF_RANGE"
    EARLY_STOPPING_INVALID = "EARLY_STOPPING_INVALID"


@dataclass
class FieldError:
    """字段错误"""
    fields: List[str]
    rule: str
    current: Dict[str, Any]
    suggestion: str


@dataclass
class ValidationResult:
    """校验结果"""
    valid: bool
    field_errors: List[FieldError]


class ParameterValidationService:
    """参数校验服务"""
    
    @staticmethod
    def validate_training_params(
        learning_rate: float,
        max_depth: int,
        n_estimators: int,
        subsample: float,
        colsample_bytree: float,
        early_stopping_rounds: Optional[int] = None,
        min_child_weight: float = 1.0
    ) -> ValidationResult:
        """
        校验训练参数
        
        Args:
            learning_rate: 学习率
            max_depth: 最大深度
            n_estimators: 树的数量
            subsample: 子采样率
            colsample_bytree: 列采样率
            early_stopping_rounds: 早停轮数
            min_child_weight: 最小子节点权重
            
        Returns:
            ValidationResult: 校验结果
        """
        errors: List[FieldError] = []
        
        if learning_rate < 0.001 or learning_rate > 1.0:
            errors.append(FieldError(
                fields=["learning_rate"],
                rule=ValidationRuleCode.LEARNING_RATE_OUT_OF_RANGE.value,
                current={"learning_rate": learning_rate},
                suggestion="学习率应在 0.001 到 1.0 之间"
            ))
        
        if n_estimators < 10:
            errors.append(FieldError(
                fields=["n_estimators"],
                rule=ValidationRuleCode.N_ESTIMATORS_TOO_SMALL.value,
                current={"n_estimators": n_estimators},
                suggestion="n_estimators 应至少为 10"
            ))
        
        if max_depth < 1 or max_depth > 15:
            errors.append(FieldError(
                fields=["max_depth"],
                rule=ValidationRuleCode.MAX_DEPTH_OUT_OF_RANGE.value,
                current={"max_depth": max_depth},
                suggestion="max_depth 应在 1 到 15 之间"
            ))
        
        if subsample < 0.1 or subsample > 1.0:
            errors.append(FieldError(
                fields=["subsample"],
                rule=ValidationRuleCode.SUBSAMPLE_OUT_OF_RANGE.value,
                current={"subsample": subsample},
                suggestion="subsample 应在 0.1 到 1.0 之间"
            ))
        
        if colsample_bytree < 0.1 or colsample_bytree > 1.0:
            errors.append(FieldError(
                fields=["colsample_bytree"],
                rule=ValidationRuleCode.COLSAMPLE_OUT_OF_RANGE.value,
                current={"colsample_bytree": colsample_bytree},
                suggestion="colsample_bytree 应在 0.1 到 1.0 之间"
            ))
        
        if early_stopping_rounds is not None:
            if early_stopping_rounds < 1:
                errors.append(FieldError(
                    fields=["early_stopping_rounds"],
                    rule=ValidationRuleCode.EARLY_STOPPING_INVALID.value,
                    current={"early_stopping_rounds": early_stopping_rounds},
                    suggestion="early_stopping_rounds 应至少为 1"
                ))
            elif early_stopping_rounds >= n_estimators:
                errors.append(FieldError(
                    fields=["early_stopping_rounds", "n_estimators"],
                    rule=ValidationRuleCode.EARLY_STOPPING_TOO_LARGE.value,
                    current={
                        "early_stopping_rounds": early_stopping_rounds,
                        "n_estimators": n_estimators
                    },
                    suggestion="early_stopping_rounds 应小于 n_estimators"
                ))
        
        if learning_rate <= 0.02 and n_estimators < 150:
            errors.append(FieldError(
                fields=["learning_rate", "n_estimators"],
                rule=ValidationRuleCode.LOW_LR_LOW_ESTIMATORS.value,
                current={
                    "learning_rate": learning_rate,
                    "n_estimators": n_estimators
                },
                suggestion="低学习率配合低迭代轮数可能导致欠拟合。建议将 n_estimators 提高到 >=150，或将 learning_rate 提升到 >=0.05"
            ))
        
        if max_depth >= 10 and subsample >= 0.95 and colsample_bytree >= 0.95:
            errors.append(FieldError(
                fields=["max_depth", "subsample", "colsample_bytree"],
                rule=ValidationRuleCode.HIGH_DEPTH_HIGH_SAMPLE.value,
                current={
                    "max_depth": max_depth,
                    "subsample": subsample,
                    "colsample_bytree": colsample_bytree
                },
                suggestion="高深度配合高采样率可能导致过拟合。建议降低 max_depth 到 <10，或降低 subsample/colsample_bytree 到 <0.95"
            ))
        
        if max_depth >= 10 and min_child_weight < 1.0:
            errors.append(FieldError(
                fields=["max_depth", "min_child_weight"],
                rule=ValidationRuleCode.HIGH_DEPTH_LOW_CHILD_WEIGHT.value,
                current={
                    "max_depth": max_depth,
                    "min_child_weight": min_child_weight
                },
                suggestion="高深度时 min_child_weight 过低可能导致过拟合。建议将 min_child_weight 提高到 >=1.0，或降低 max_depth"
            ))
        
        return ValidationResult(
            valid=len(errors) == 0,
            field_errors=errors
        )

    @staticmethod
    def validate_xgboost_params(params: Dict[str, Any]) -> ValidationResult:
        """
        校验 XGBoost 参数字典
        
        Args:
            params: XGBoost 参数字典
            
        Returns:
            ValidationResult: 校验结果
        """
        return ParameterValidationService.validate_training_params(
            learning_rate=params.get('learning_rate', 0.1),
            max_depth=params.get('max_depth', 6),
            n_estimators=params.get('n_estimators', 100),
            subsample=params.get('subsample', 1.0),
            colsample_bytree=params.get('colsample_bytree', 1.0),
            early_stopping_rounds=params.get('early_stopping_rounds'),
            min_child_weight=params.get('min_child_weight', 1.0)
        )
