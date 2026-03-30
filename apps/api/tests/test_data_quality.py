"""
数据质量门禁测试

测试数据质量校验器的各种场景
"""
import pytest
import tempfile
import os
import pandas as pd
import numpy as np
from pathlib import Path

from app.services.data_quality_validator import (
    DataQualityValidator,
    DataQualityError,
    validate_dataset_quality
)


class TestDataQualityValidator:
    """数据质量校验器测试"""

    # ========== 正常样本测试 ==========

    def test_valid_data_passes_validation(self):
        """测试正常样本可通过校验"""
        # Given: 创建正常的数据文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'building_id': ['A'] * 50 + ['B'] * 50,
                'energy_consumption': [100 + i * 0.5 for i in range(100)],
                'temperature': [20 + i * 0.1 for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When: 执行校验
            result = DataQualityValidator.validate_for_training(
                file_path=file_path,
                target_column='energy_consumption',
                time_column='timestamp'
            )

            # Then: 校验通过
            assert result['is_valid'] is True
            assert len(result['errors']) == 0
            assert 'target_column' in result['stats']
            assert 'time_column' in result['stats']
            assert result['stats']['total_rows'] == 100
            assert result['stats']['total_columns'] == 4

        finally:
            os.unlink(file_path)

    def test_valid_data_with_some_missing_values(self):
        """测试包含少量缺失值的正常样本可通过校验"""
        # Given: 创建包含少量缺失值的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [100 + i * 0.5 if i % 10 != 0 else np.nan for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When: 执行校验
            result = DataQualityValidator.validate_for_training(
                file_path=file_path,
                target_column='target',
                time_column='timestamp'
            )

            # Then: 校验通过，但有警告
            assert result['is_valid'] is True
            assert len(result['errors']) == 0
            assert len(result['warnings']) > 0
            # 检查缺失值警告
            warning_codes = [w['code'] for w in result['warnings']]
            assert 'TARGET_COLUMN_HAS_MISSING_VALUES' in warning_codes

        finally:
            os.unlink(file_path)

    # ========== NaN/Inf 被拒绝测试 ==========

    def test_target_column_with_nan_rejected(self):
        """测试目标列包含 NaN 值被拒绝（缺失率过高）"""
        # Given: 创建目标列缺失率过高的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [np.nan] * 100,  # 全部为 NaN
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TARGET_COLUMN_ALL_MISSING'
            assert '所有值均为空' in exc_info.value.message

        finally:
            os.unlink(file_path)

    def test_target_column_with_inf_rejected(self):
        """测试目标列包含 Inf 值被拒绝"""
        # Given: 创建目标列包含 Inf 值的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [100 + i * 0.5 if i < 95 else np.inf for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TARGET_COLUMN_CONTAINS_INF'
            assert '无穷值' in exc_info.value.message
            assert exc_info.value.details['inf_count'] == 5

        finally:
            os.unlink(file_path)

    def test_target_column_with_negative_inf_rejected(self):
        """测试目标列包含负 Inf 值被拒绝"""
        # Given: 创建目标列包含负 Inf 值的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [100 + i * 0.5 if i < 90 else -np.inf for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TARGET_COLUMN_CONTAINS_INF'
            assert exc_info.value.details['inf_count'] == 10

        finally:
            os.unlink(file_path)

    def test_target_column_high_missing_rate_rejected(self):
        """测试目标列缺失率过高被拒绝"""
        # Given: 创建目标列缺失率超过 95% 的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # 100 行数据，96 行为 NaN（缺失率 96%）
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [100 + i if i < 4 else np.nan for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TARGET_COLUMN_HIGH_MISSING_RATE'
            assert '缺失率过高' in exc_info.value.message

        finally:
            os.unlink(file_path)

    # ========== 时间列不可解析被拒绝测试 ==========

    def test_time_column_unparseable_rejected(self):
        """测试时间列无法解析被拒绝"""
        # Given: 创建时间列格式错误的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': ['invalid_date'] * 100,  # 全部为无效时间格式
                'target': [100 + i * 0.5 for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TIME_COLUMN_PARSE_FAILED'
            assert '无法正确解析为时间格式' in exc_info.value.message
            assert exc_info.value.details['parse_success_rate'] < 0.5

        finally:
            os.unlink(file_path)

    def test_time_column_mostly_unparseable_rejected(self):
        """测试时间列大部分无法解析被拒绝"""
        # Given: 创建时间列大部分格式错误的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            timestamps = []
            for i in range(100):
                if i < 40:
                    timestamps.append('2024-01-01 00:00:00')  # 有效
                else:
                    timestamps.append(f'not_a_date_{i}')  # 无效
            df = pd.DataFrame({
                'timestamp': timestamps,
                'target': [100 + i * 0.5 for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TIME_COLUMN_PARSE_FAILED'
            assert exc_info.value.details['parse_success_rate'] < 0.5

        finally:
            os.unlink(file_path)

    def test_time_column_partial_parse_warning(self):
        """测试时间列部分无法解析产生警告"""
        # Given: 创建时间列部分格式错误的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            timestamps = []
            for i in range(100):
                if i < 80:
                    timestamps.append('2024-01-01 00:00:00')  # 有效
                else:
                    timestamps.append(f'invalid_{i}')  # 无效
            df = pd.DataFrame({
                'timestamp': timestamps,
                'target': [100 + i * 0.5 for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When: 执行校验
            result = DataQualityValidator.validate_for_training(
                file_path=file_path,
                target_column='target',
                time_column='timestamp'
            )

            # Then: 校验通过，但有警告
            assert result['is_valid'] is True
            assert len(result['errors']) == 0
            # 检查时间列解析警告
            warning_codes = [w['code'] for w in result['warnings']]
            assert 'TIME_COLUMN_PARTIAL_PARSE' in warning_codes

        finally:
            os.unlink(file_path)

    # ========== 目标列全空被拒绝测试 ==========

    def test_target_column_all_null_rejected(self):
        """测试目标列全空被拒绝"""
        # Given: 创建目标列全为空的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [None] * 100,  # 全部为 None
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TARGET_COLUMN_ALL_MISSING'
            assert '所有值均为空' in exc_info.value.message
            assert exc_info.value.details['total_count'] == 100
            assert exc_info.value.details['missing_count'] == 100

        finally:
            os.unlink(file_path)

    def test_target_column_insufficient_samples_rejected(self):
        """测试目标列有效样本数过少被拒绝"""
        # Given: 创建目标列有效样本数少于最小阈值的数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # 只有 5 个有效值，小于 MIN_VALID_SAMPLES (10)
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [100 + i if i < 5 else np.nan for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TARGET_COLUMN_INSUFFICIENT_SAMPLES'
            assert '有效样本数过少' in exc_info.value.message
            assert exc_info.value.details['valid_count'] == 5
            assert exc_info.value.details['min_required'] == 10

        finally:
            os.unlink(file_path)

    # ========== 其他边界测试 ==========

    def test_target_column_not_found(self):
        """测试目标列不存在"""
        # Given: 创建数据文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'value': [100 + i * 0.5 for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='non_existent_column',
                    time_column='timestamp'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TARGET_COLUMN_NOT_FOUND'
            assert '不存在于数据中' in exc_info.value.message

        finally:
            os.unlink(file_path)

    def test_time_column_not_found(self):
        """测试时间列不存在"""
        # Given: 创建数据文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'value': [100 + i * 0.5 for i in range(100)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='value',
                    time_column='non_existent_column'
                )

            # 验证错误码
            assert exc_info.value.error_code == 'TIME_COLUMN_NOT_FOUND'

        finally:
            os.unlink(file_path)

    def test_file_not_found(self):
        """测试文件不存在"""
        # Given: 不存在的文件路径
        file_path = '/non/existent/file.csv'

        # When & Then: 校验失败，抛出异常
        with pytest.raises(DataQualityError) as exc_info:
            DataQualityValidator.validate_for_training(
                file_path=file_path,
                target_column='target'
            )

        # 验证错误码
        assert exc_info.value.error_code == 'FILE_NOT_FOUND'

    def test_empty_dataset(self):
        """测试空数据集"""
        # Given: 创建空数据文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame()  # 空 DataFrame
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            # 注意：空 CSV 文件可能导致 FILE_READ_ERROR 或 EMPTY_DATASET
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target'
                )

            # 验证错误码（可能是 FILE_READ_ERROR 或 EMPTY_DATASET）
            assert exc_info.value.error_code in ['EMPTY_DATASET', 'FILE_READ_ERROR']

        finally:
            os.unlink(file_path)

    def test_unsupported_file_format(self):
        """测试不支持的文件格式"""
        # Given: 创建不支持的文件格式
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('some text content')
            file_path = f.name

        try:
            # When & Then: 校验失败，抛出异常
            # 注意：不支持的格式可能导致 FILE_READ_ERROR 或 UNSUPPORTED_FORMAT
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target'
                )

            # 验证错误码（可能是 FILE_READ_ERROR 或 UNSUPPORTED_FORMAT）
            assert exc_info.value.error_code in ['UNSUPPORTED_FORMAT', 'FILE_READ_ERROR']

        finally:
            os.unlink(file_path)

    # ========== 便捷函数测试 ==========

    def test_validate_dataset_quality_function(self):
        """测试便捷函数 validate_dataset_quality"""
        # Given: 创建正常的数据文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=50, freq='h'),
                'target': [100 + i * 0.5 for i in range(50)],
            })
            df.to_csv(f, index=False)
            file_path = f.name

        try:
            # When: 使用便捷函数
            result = validate_dataset_quality(
                file_path=file_path,
                target_column='target',
                time_column='timestamp'
            )

            # Then: 校验通过
            assert result['is_valid'] is True

        finally:
            os.unlink(file_path)


class TestDataQualityValidatorParquet:
    """Parquet 文件格式测试"""

    def test_valid_parquet_file(self):
        """测试 Parquet 文件校验"""
        # Given: 创建 Parquet 文件
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [100 + i * 0.5 for i in range(100)],
            })
            df.to_parquet(f, index=False)
            file_path = f.name

        try:
            # When: 执行校验
            result = DataQualityValidator.validate_for_training(
                file_path=file_path,
                target_column='target',
                time_column='timestamp'
            )

            # Then: 校验通过
            assert result['is_valid'] is True

        finally:
            os.unlink(file_path)

    def test_parquet_with_inf_rejected(self):
        """测试 Parquet 文件包含 Inf 值被拒绝"""
        # Given: 创建包含 Inf 值的 Parquet 文件
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
                'target': [100 + i * 0.5 if i < 95 else np.inf for i in range(100)],
            })
            df.to_parquet(f, index=False)
            file_path = f.name

        try:
            # When & Then: 校验失败
            with pytest.raises(DataQualityError) as exc_info:
                DataQualityValidator.validate_for_training(
                    file_path=file_path,
                    target_column='target',
                    time_column='timestamp'
                )

            assert exc_info.value.error_code == 'TARGET_COLUMN_CONTAINS_INF'

        finally:
            os.unlink(file_path)
