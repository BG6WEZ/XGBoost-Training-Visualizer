"""
Benchmark 指标计算服务

P1-T11: 统一输出指标体系
实现 RMSE、MAE、MAPE、R2 四种核心评估指标的标准化计算逻辑
"""
import numpy as np
from typing import Tuple, Optional, List
from app.schemas.results import BenchmarkMetrics, MetricAvailability


def calculate_rmse(actual: np.ndarray, predicted: np.ndarray) -> Tuple[Optional[float], MetricAvailability]:
    """
    计算 RMSE (Root Mean Square Error)
    
    公式: RMSE = sqrt(mean((actual - predicted)^2))
    
    Args:
        actual: 实际值数组
        predicted: 预测值数组
        
    Returns:
        (RMSE 值, 可用性说明)
    """
    if len(actual) == 0 or len(predicted) == 0:
        return None, MetricAvailability(available=False, reason="数据为空")
    
    if len(actual) != len(predicted):
        return None, MetricAvailability(available=False, reason="实际值与预测值长度不一致")
    
    if np.any(np.isnan(actual)) or np.any(np.isnan(predicted)):
        return None, MetricAvailability(available=False, reason="数据包含 NaN 值")
    
    if np.any(np.isinf(actual)) or np.any(np.isinf(predicted)):
        return None, MetricAvailability(available=False, reason="数据包含无穷值")
    
    mse = np.mean((actual - predicted) ** 2)
    rmse = float(np.sqrt(mse))
    
    return rmse, MetricAvailability(available=True)


def calculate_mae(actual: np.ndarray, predicted: np.ndarray) -> Tuple[Optional[float], MetricAvailability]:
    """
    计算 MAE (Mean Absolute Error)
    
    公式: MAE = mean(|actual - predicted|)
    
    Args:
        actual: 实际值数组
        predicted: 预测值数组
        
    Returns:
        (MAE 值, 可用性说明)
    """
    if len(actual) == 0 or len(predicted) == 0:
        return None, MetricAvailability(available=False, reason="数据为空")
    
    if len(actual) != len(predicted):
        return None, MetricAvailability(available=False, reason="实际值与预测值长度不一致")
    
    if np.any(np.isnan(actual)) or np.any(np.isnan(predicted)):
        return None, MetricAvailability(available=False, reason="数据包含 NaN 值")
    
    if np.any(np.isinf(actual)) or np.any(np.isinf(predicted)):
        return None, MetricAvailability(available=False, reason="数据包含无穷值")
    
    mae = float(np.mean(np.abs(actual - predicted)))
    
    return mae, MetricAvailability(available=True)


def calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> Tuple[Optional[float], MetricAvailability]:
    """
    计算 MAPE (Mean Absolute Percentage Error)
    
    公式: MAPE = mean(|actual - predicted| / |actual|) * 100
    
    注意: MAPE 在实际值为 0 时不可计算
    
    Args:
        actual: 实际值数组
        predicted: 预测值数组
        
    Returns:
        (MAPE 值, 可用性说明)
    """
    if len(actual) == 0 or len(predicted) == 0:
        return None, MetricAvailability(available=False, reason="数据为空")
    
    if len(actual) != len(predicted):
        return None, MetricAvailability(available=False, reason="实际值与预测值长度不一致")
    
    if np.any(np.isnan(actual)) or np.any(np.isnan(predicted)):
        return None, MetricAvailability(available=False, reason="数据包含 NaN 值")
    
    if np.any(np.isinf(actual)) or np.any(np.isinf(predicted)):
        return None, MetricAvailability(available=False, reason="数据包含无穷值")
    
    zero_count = np.sum(actual == 0)
    if zero_count > 0:
        return None, MetricAvailability(
            available=False, 
            reason=f"实际值包含 {zero_count} 个零值，MAPE 不可计算"
        )
    
    mape = float(np.mean(np.abs((actual - predicted) / actual)) * 100)
    
    return mape, MetricAvailability(available=True)


def calculate_r2(actual: np.ndarray, predicted: np.ndarray) -> Tuple[Optional[float], MetricAvailability]:
    """
    计算 R² (R-squared / 决定系数)
    
    公式: R² = 1 - SS_res / SS_tot
    其中:
        SS_res = sum((actual - predicted)^2)
        SS_tot = sum((actual - mean(actual))^2)
    
    Args:
        actual: 实际值数组
        predicted: 预测值数组
        
    Returns:
        (R² 值, 可用性说明)
    """
    if len(actual) == 0 or len(predicted) == 0:
        return None, MetricAvailability(available=False, reason="数据为空")
    
    if len(actual) != len(predicted):
        return None, MetricAvailability(available=False, reason="实际值与预测值长度不一致")
    
    if np.any(np.isnan(actual)) or np.any(np.isnan(predicted)):
        return None, MetricAvailability(available=False, reason="数据包含 NaN 值")
    
    if np.any(np.isinf(actual)) or np.any(np.isinf(predicted)):
        return None, MetricAvailability(available=False, reason="数据包含无穷值")
    
    if len(actual) < 2:
        return None, MetricAvailability(available=False, reason="样本数少于 2，无法计算 R²")
    
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    
    if ss_tot == 0:
        return None, MetricAvailability(available=False, reason="实际值方差为零，无法计算 R²")
    
    r2 = float(1 - (ss_res / ss_tot))
    
    return r2, MetricAvailability(available=True)


def calculate_benchmark_metrics(
    actual_values: List[float],
    predicted_values: List[float]
) -> BenchmarkMetrics:
    """
    计算完整的 Benchmark 指标集
    
    Args:
        actual_values: 实际值列表
        predicted_values: 预测值列表
        
    Returns:
        BenchmarkMetrics 对象
    """
    actual = np.array(actual_values, dtype=np.float64)
    predicted = np.array(predicted_values, dtype=np.float64)
    
    rmse, rmse_avail = calculate_rmse(actual, predicted)
    mae, mae_avail = calculate_mae(actual, predicted)
    mape, mape_avail = calculate_mape(actual, predicted)
    r2, r2_avail = calculate_r2(actual, predicted)
    
    return BenchmarkMetrics(
        rmse=rmse,
        mae=mae,
        mape=mape,
        r2=r2,
        rmse_availability=rmse_avail,
        mae_availability=mae_avail,
        mape_availability=mape_avail,
        r2_availability=r2_avail
    )


def calculate_benchmark_from_residuals(
    actual_values: List[float],
    predicted_values: List[float],
    residual_values: Optional[List[float]] = None
) -> BenchmarkMetrics:
    """
    从预测数据计算 Benchmark 指标
    
    Args:
        actual_values: 实际值列表
        predicted_values: 预测值列表
        residual_values: 残差列表（可选，用于验证）
        
    Returns:
        BenchmarkMetrics 对象
    """
    return calculate_benchmark_metrics(actual_values, predicted_values)
