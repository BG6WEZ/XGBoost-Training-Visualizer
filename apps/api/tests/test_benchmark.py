"""
Benchmark 指标计算测试

P1-T11: 统一输出指标体系
测试 RMSE、MAE、MAPE、R2 四种核心评估指标的计算逻辑
"""
import pytest
import numpy as np
from app.services.benchmark import (
    calculate_rmse,
    calculate_mae,
    calculate_mape,
    calculate_r2,
    calculate_benchmark_metrics,
)


class TestRMSECalculation:
    """RMSE 计算测试"""

    def test_rmse_normal_case(self):
        """正常情况计算 RMSE"""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted = np.array([1.1, 2.2, 2.9, 4.1, 4.9])
        
        rmse, availability = calculate_rmse(actual, predicted)
        
        assert availability.available is True
        assert rmse is not None
        assert 0.1 < rmse < 0.2

    def test_rmse_perfect_prediction(self):
        """完美预测时 RMSE 为 0"""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        rmse, availability = calculate_rmse(actual, predicted)
        
        assert availability.available is True
        assert rmse == 0.0

    def test_rmse_empty_data(self):
        """空数据返回不可用"""
        actual = np.array([])
        predicted = np.array([])
        
        rmse, availability = calculate_rmse(actual, predicted)
        
        assert availability.available is False
        assert rmse is None
        assert "空" in availability.reason

    def test_rmse_length_mismatch(self):
        """长度不一致返回不可用"""
        actual = np.array([1.0, 2.0, 3.0])
        predicted = np.array([1.0, 2.0])
        
        rmse, availability = calculate_rmse(actual, predicted)
        
        assert availability.available is False
        assert rmse is None
        assert "长度不一致" in availability.reason

    def test_rmse_nan_values(self):
        """包含 NaN 返回不可用"""
        actual = np.array([1.0, np.nan, 3.0])
        predicted = np.array([1.0, 2.0, 3.0])
        
        rmse, availability = calculate_rmse(actual, predicted)
        
        assert availability.available is False
        assert rmse is None
        assert "NaN" in availability.reason

    def test_rmse_inf_values(self):
        """包含无穷值返回不可用"""
        actual = np.array([1.0, np.inf, 3.0])
        predicted = np.array([1.0, 2.0, 3.0])
        
        rmse, availability = calculate_rmse(actual, predicted)
        
        assert availability.available is False
        assert rmse is None
        assert "无穷" in availability.reason


class TestMAECalculation:
    """MAE 计算测试"""

    def test_mae_normal_case(self):
        """正常情况计算 MAE"""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted = np.array([1.1, 2.2, 2.9, 4.1, 4.9])
        
        mae, availability = calculate_mae(actual, predicted)
        
        assert availability.available is True
        assert mae is not None
        assert 0.1 < mae < 0.2

    def test_mae_perfect_prediction(self):
        """完美预测时 MAE 为 0"""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        mae, availability = calculate_mae(actual, predicted)
        
        assert availability.available is True
        assert mae == 0.0

    def test_mae_empty_data(self):
        """空数据返回不可用"""
        actual = np.array([])
        predicted = np.array([])
        
        mae, availability = calculate_mae(actual, predicted)
        
        assert availability.available is False
        assert mae is None


class TestMAPECalculation:
    """MAPE 计算测试"""

    def test_mape_normal_case(self):
        """正常情况计算 MAPE"""
        actual = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
        predicted = np.array([110.0, 190.0, 310.0, 390.0, 510.0])
        
        mape, availability = calculate_mape(actual, predicted)
        
        assert availability.available is True
        assert mape is not None
        assert 3.0 < mape < 7.0

    def test_mape_zero_actual_values(self):
        """实际值包含零时返回不可用（诚实降级）"""
        actual = np.array([0.0, 100.0, 200.0])
        predicted = np.array([10.0, 110.0, 210.0])
        
        mape, availability = calculate_mape(actual, predicted)
        
        assert availability.available is False
        assert mape is None
        assert "零值" in availability.reason

    def test_mape_all_zero_actual_values(self):
        """所有实际值为零时返回不可用"""
        actual = np.array([0.0, 0.0, 0.0])
        predicted = np.array([1.0, 2.0, 3.0])
        
        mape, availability = calculate_mape(actual, predicted)
        
        assert availability.available is False
        assert mape is None
        assert "零值" in availability.reason

    def test_mape_empty_data(self):
        """空数据返回不可用"""
        actual = np.array([])
        predicted = np.array([])
        
        mape, availability = calculate_mape(actual, predicted)
        
        assert availability.available is False
        assert mape is None


class TestR2Calculation:
    """R² 计算测试"""

    def test_r2_normal_case(self):
        """正常情况计算 R²"""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted = np.array([1.1, 2.0, 2.9, 4.1, 4.9])
        
        r2, availability = calculate_r2(actual, predicted)
        
        assert availability.available is True
        assert r2 is not None
        assert 0.95 < r2 <= 1.0

    def test_r2_perfect_prediction(self):
        """完美预测时 R² 为 1"""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        r2, availability = calculate_r2(actual, predicted)
        
        assert availability.available is True
        assert r2 == 1.0

    def test_r2_single_sample(self):
        """单样本返回不可用"""
        actual = np.array([1.0])
        predicted = np.array([1.0])
        
        r2, availability = calculate_r2(actual, predicted)
        
        assert availability.available is False
        assert r2 is None
        assert "少于 2" in availability.reason

    def test_r2_zero_variance(self):
        """实际值方差为零时返回不可用"""
        actual = np.array([5.0, 5.0, 5.0, 5.0])
        predicted = np.array([4.0, 5.0, 6.0, 7.0])
        
        r2, availability = calculate_r2(actual, predicted)
        
        assert availability.available is False
        assert r2 is None
        assert "方差为零" in availability.reason

    def test_r2_empty_data(self):
        """空数据返回不可用"""
        actual = np.array([])
        predicted = np.array([])
        
        r2, availability = calculate_r2(actual, predicted)
        
        assert availability.available is False
        assert r2 is None


class TestBenchmarkMetricsIntegration:
    """Benchmark 指标集成测试"""

    def test_calculate_benchmark_metrics_success(self):
        """成功计算所有指标"""
        actual_values = [10.0, 20.0, 30.0, 40.0, 50.0]
        predicted_values = [11.0, 19.0, 31.0, 39.0, 51.0]
        
        benchmark = calculate_benchmark_metrics(actual_values, predicted_values)
        
        assert benchmark.rmse is not None
        assert benchmark.mae is not None
        assert benchmark.mape is not None
        assert benchmark.r2 is not None
        
        assert benchmark.rmse_availability.available is True
        assert benchmark.mae_availability.available is True
        assert benchmark.mape_availability.available is True
        assert benchmark.r2_availability.available is True

    def test_calculate_benchmark_metrics_mape_unavailable(self):
        """MAPE 不可用时的诚实降级"""
        actual_values = [0.0, 20.0, 30.0, 40.0, 50.0]
        predicted_values = [11.0, 19.0, 31.0, 39.0, 51.0]
        
        benchmark = calculate_benchmark_metrics(actual_values, predicted_values)
        
        assert benchmark.rmse is not None
        assert benchmark.mae is not None
        assert benchmark.mape is None
        assert benchmark.r2 is not None
        
        assert benchmark.rmse_availability.available is True
        assert benchmark.mae_availability.available is True
        assert benchmark.mape_availability.available is False
        assert "零值" in benchmark.mape_availability.reason
        assert benchmark.r2_availability.available is True

    def test_calculate_benchmark_metrics_empty_data(self):
        """空数据时所有指标不可用"""
        actual_values = []
        predicted_values = []
        
        benchmark = calculate_benchmark_metrics(actual_values, predicted_values)
        
        assert benchmark.rmse is None
        assert benchmark.mae is None
        assert benchmark.mape is None
        assert benchmark.r2 is None
        
        assert benchmark.rmse_availability.available is False
        assert benchmark.mae_availability.available is False
        assert benchmark.mape_availability.available is False
        assert benchmark.r2_availability.available is False

    def test_benchmark_structure_consistency(self):
        """验证 Benchmark 结构一致性"""
        actual_values = [10.0, 20.0, 30.0, 40.0, 50.0]
        predicted_values = [11.0, 19.0, 31.0, 39.0, 51.0]
        
        benchmark = calculate_benchmark_metrics(actual_values, predicted_values)
        
        assert hasattr(benchmark, 'rmse')
        assert hasattr(benchmark, 'mae')
        assert hasattr(benchmark, 'mape')
        assert hasattr(benchmark, 'r2')
        assert hasattr(benchmark, 'rmse_availability')
        assert hasattr(benchmark, 'mae_availability')
        assert hasattr(benchmark, 'mape_availability')
        assert hasattr(benchmark, 'r2_availability')
