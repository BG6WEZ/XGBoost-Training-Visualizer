"""
数据质量校验服务

提供数据登记前的质量防线，拦截可能导致训练失败的问题数据
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """数据质量错误"""
    
    def __init__(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class DataQualityValidator:
    """数据质量校验器"""
    
    # 最小有效样本数阈值
    MIN_VALID_SAMPLES = 10
    
    # 目标列缺失率阈值（超过此比例视为全空）
    MAX_MISSING_RATE = 0.95
    
    @classmethod
    def validate_for_training(
        cls,
        file_path: str,
        target_column: Optional[str] = None,
        time_column: Optional[str] = None,
        sample_rows: int = 10000
    ) -> Dict[str, Any]:
        """
        对数据文件进行训练前的质量校验
        
        Args:
            file_path: 数据文件路径
            target_column: 目标列名称（可选）
            time_column: 时间列名称（可选）
            sample_rows: 采样行数（用于大文件）
            
        Returns:
            校验结果字典，包含:
            - is_valid: bool, 是否通过校验
            - errors: List[Dict], 错误列表
            - warnings: List[Dict], 警告列表
            - stats: Dict, 数据统计信息
            
        Raises:
            DataQualityError: 当发现致命质量问题时抛出
        """
        path = Path(file_path)
        if not path.exists():
            raise DataQualityError(
                error_code="FILE_NOT_FOUND",
                message=f"数据文件不存在: {file_path}",
                details={"file_path": file_path}
            )
        
        # 读取数据
        try:
            if path.suffix == '.csv':
                df = pd.read_csv(file_path, nrows=sample_rows)
            elif path.suffix == '.parquet':
                df = pd.read_parquet(file_path)
                if len(df) > sample_rows:
                    df = df.head(sample_rows)
            else:
                raise DataQualityError(
                    error_code="UNSUPPORTED_FORMAT",
                    message=f"不支持的文件格式: {path.suffix}",
                    details={"file_path": file_path, "format": path.suffix}
                )
        except Exception as e:
            raise DataQualityError(
                error_code="FILE_READ_ERROR",
                message=f"无法读取数据文件: {str(e)}",
                details={"file_path": file_path, "error": str(e)}
            )
        
        errors = []
        warnings = []
        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "sample_rows_used": len(df)
        }
        
        # 1. 校验目标列
        if target_column:
            target_errors, target_warnings, target_stats = cls._validate_target_column(
                df, target_column
            )
            errors.extend(target_errors)
            warnings.extend(target_warnings)
            stats["target_column"] = target_stats
        else:
            warnings.append({
                "code": "NO_TARGET_COLUMN",
                "message": "未指定目标列，无法进行目标列质量校验",
                "severity": "warning"
            })
        
        # 2. 校验时间列
        if time_column:
            time_errors, time_warnings, time_stats = cls._validate_time_column(
                df, time_column
            )
            errors.extend(time_errors)
            warnings.extend(time_warnings)
            stats["time_column"] = time_stats
        
        # 3. 通用数据质量检查
        general_errors, general_warnings, general_stats = cls._validate_general_quality(df)
        errors.extend(general_errors)
        warnings.extend(general_warnings)
        stats["general"] = general_stats
        
        # 如果存在致命错误，抛出异常
        if errors:
            # 取第一个错误作为主要错误
            first_error = errors[0]
            raise DataQualityError(
                error_code=first_error["code"],
                message=first_error["message"],
                details={
                    **first_error.get("details", {}),
                    "all_errors": errors,
                    "warnings": warnings,
                    "stats": stats
                }
            )
        
        return {
            "is_valid": True,
            "errors": errors,
            "warnings": warnings,
            "stats": stats
        }
    
    @classmethod
    def _validate_target_column(
        cls,
        df: pd.DataFrame,
        target_column: str
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        校验目标列质量
        
        检查项：
        1. 目标列是否存在
        2. 目标列是否全空或有效样本过少
        3. 目标列是否存在 NaN/Inf 值
        """
        errors = []
        warnings = []
        stats = {}
        
        # 检查列是否存在
        if target_column not in df.columns:
            errors.append({
                "code": "TARGET_COLUMN_NOT_FOUND",
                "message": f"目标列 '{target_column}' 不存在于数据中",
                "severity": "error",
                "details": {
                    "target_column": target_column,
                    "available_columns": list(df.columns)
                }
            })
            return errors, warnings, stats
        
        series = df[target_column]
        stats["column_name"] = target_column
        stats["dtype"] = str(series.dtype)
        stats["total_count"] = len(series)
        
        # 检查是否为数值类型
        is_numeric = pd.api.types.is_numeric_dtype(series)
        stats["is_numeric"] = is_numeric
        
        # 计算缺失值
        missing_count = series.isnull().sum()
        missing_rate = missing_count / len(series) if len(series) > 0 else 0
        stats["missing_count"] = int(missing_count)
        stats["missing_rate"] = float(missing_rate)
        
        # 检查1: 目标列全空
        if missing_count == len(series):
            errors.append({
                "code": "TARGET_COLUMN_ALL_MISSING",
                "message": f"目标列 '{target_column}' 所有值均为空，无法进行训练",
                "severity": "error",
                "details": {
                    "target_column": target_column,
                    "total_count": len(series),
                    "missing_count": int(missing_count)
                }
            })
            return errors, warnings, stats
        
        # 检查2: 目标列缺失率过高
        if missing_rate > cls.MAX_MISSING_RATE:
            errors.append({
                "code": "TARGET_COLUMN_HIGH_MISSING_RATE",
                "message": f"目标列 '{target_column}' 缺失率过高 ({missing_rate:.1%})，有效样本不足",
                "severity": "error",
                "details": {
                    "target_column": target_column,
                    "missing_rate": float(missing_rate),
                    "threshold": cls.MAX_MISSING_RATE,
                    "missing_count": int(missing_count),
                    "total_count": len(series)
                }
            })
            return errors, warnings, stats
        
        # 计算有效样本数
        valid_count = len(series) - missing_count
        stats["valid_count"] = int(valid_count)
        
        # 检查3: 有效样本过少
        if valid_count < cls.MIN_VALID_SAMPLES:
            errors.append({
                "code": "TARGET_COLUMN_INSUFFICIENT_SAMPLES",
                "message": f"目标列 '{target_column}' 有效样本数过少 ({valid_count} < {cls.MIN_VALID_SAMPLES})，无法进行有效训练",
                "severity": "error",
                "details": {
                    "target_column": target_column,
                    "valid_count": int(valid_count),
                    "min_required": cls.MIN_VALID_SAMPLES,
                    "missing_count": int(missing_count)
                }
            })
            return errors, warnings, stats
        
        # 检查4: 数值型目标列的 NaN/Inf 值
        if is_numeric:
            # 检查 Inf 值
            inf_mask = np.isinf(series)
            inf_count = inf_mask.sum()
            
            if inf_count > 0:
                inf_rate = inf_count / len(series)
                stats["inf_count"] = int(inf_count)
                stats["inf_rate"] = float(inf_rate)
                
                errors.append({
                    "code": "TARGET_COLUMN_CONTAINS_INF",
                    "message": f"目标列 '{target_column}' 包含 {inf_count} 个无穷值 (Inf/-Inf)，会导致训练失败",
                    "severity": "error",
                    "details": {
                        "target_column": target_column,
                        "inf_count": int(inf_count),
                        "inf_rate": float(inf_rate),
                        "sample_inf_indices": series[inf_mask].index[:5].tolist()
                    }
                })
                return errors, warnings, stats
            
            # 检查 NaN 值（已通过 missing_count 检查，这里作为警告）
            if missing_count > 0:
                warnings.append({
                    "code": "TARGET_COLUMN_HAS_MISSING_VALUES",
                    "message": f"目标列 '{target_column}' 包含 {missing_count} 个缺失值 ({missing_rate:.1%})，训练时将被排除",
                    "severity": "warning",
                    "details": {
                        "target_column": target_column,
                        "missing_count": int(missing_count),
                        "missing_rate": float(missing_rate)
                    }
                })
            
            # 统计有效值的范围
            valid_series = series.dropna()
            if len(valid_series) > 0:
                stats["min_value"] = float(valid_series.min())
                stats["max_value"] = float(valid_series.max())
                stats["mean_value"] = float(valid_series.mean())
                stats["std_value"] = float(valid_series.std())
        
        return errors, warnings, stats
    
    @classmethod
    def _validate_time_column(
        cls,
        df: pd.DataFrame,
        time_column: str
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        校验时间列质量
        
        检查项：
        1. 时间列是否存在
        2. 时间列是否可以解析为时间格式
        3. 时间列是否存在无效值
        """
        errors = []
        warnings = []
        stats = {}
        
        # 检查列是否存在
        if time_column not in df.columns:
            errors.append({
                "code": "TIME_COLUMN_NOT_FOUND",
                "message": f"时间列 '{time_column}' 不存在于数据中",
                "severity": "error",
                "details": {
                    "time_column": time_column,
                    "available_columns": list(df.columns)
                }
            })
            return errors, warnings, stats
        
        series = df[time_column]
        stats["column_name"] = time_column
        stats["dtype"] = str(series.dtype)
        stats["total_count"] = len(series)
        
        # 检查是否已经是时间类型
        if pd.api.types.is_datetime64_any_dtype(series):
            stats["is_datetime"] = True
            stats["parse_success_rate"] = 1.0
        else:
            # 尝试解析为时间
            stats["is_datetime"] = False
            try:
                # 采样部分数据进行解析测试
                sample_size = min(1000, len(series))
                sample_series = series.head(sample_size)
                
                parsed = pd.to_datetime(sample_series, errors='coerce')
                parse_success_count = parsed.notna().sum()
                parse_success_rate = parse_success_count / sample_size
                
                stats["parse_success_rate"] = float(parse_success_rate)
                stats["parse_success_count"] = int(parse_success_count)
                stats["parse_sample_size"] = sample_size
                
                # 如果解析成功率过低，视为错误
                if parse_success_rate < 0.5:
                    errors.append({
                        "code": "TIME_COLUMN_PARSE_FAILED",
                        "message": f"时间列 '{time_column}' 无法正确解析为时间格式 (成功率: {parse_success_rate:.1%})",
                        "severity": "error",
                        "details": {
                            "time_column": time_column,
                            "parse_success_rate": float(parse_success_rate),
                            "sample_size": sample_size,
                            "parse_success_count": int(parse_success_count)
                        }
                    })
                    return errors, warnings, stats
                
                # 如果解析成功率不是100%，发出警告
                if parse_success_rate < 1.0:
                    warnings.append({
                        "code": "TIME_COLUMN_PARTIAL_PARSE",
                        "message": f"时间列 '{time_column}' 部分值无法解析为时间格式 ({(1-parse_success_rate)*100:.1f}% 失败)",
                        "severity": "warning",
                        "details": {
                            "time_column": time_column,
                            "parse_success_rate": float(parse_success_rate)
                        }
                    })
                
            except Exception as e:
                errors.append({
                    "code": "TIME_COLUMN_PARSE_ERROR",
                    "message": f"时间列 '{time_column}' 解析失败: {str(e)}",
                    "severity": "error",
                    "details": {
                        "time_column": time_column,
                        "error": str(e)
                    }
                })
                return errors, warnings, stats
        
        # 检查缺失值
        missing_count = series.isnull().sum()
        missing_rate = missing_count / len(series) if len(series) > 0 else 0
        stats["missing_count"] = int(missing_count)
        stats["missing_rate"] = float(missing_rate)
        
        if missing_rate > 0.5:
            errors.append({
                "code": "TIME_COLUMN_HIGH_MISSING_RATE",
                "message": f"时间列 '{time_column}' 缺失率过高 ({missing_rate:.1%})",
                "severity": "error",
                "details": {
                    "time_column": time_column,
                    "missing_rate": float(missing_rate),
                    "missing_count": int(missing_count)
                }
            })
        elif missing_count > 0:
            warnings.append({
                "code": "TIME_COLUMN_HAS_MISSING_VALUES",
                "message": f"时间列 '{time_column}' 包含 {missing_count} 个缺失值 ({missing_rate:.1%})",
                "severity": "warning",
                "details": {
                    "time_column": time_column,
                    "missing_count": int(missing_count),
                    "missing_rate": float(missing_rate)
                }
            })
        
        return errors, warnings, stats
    
    @classmethod
    def _validate_general_quality(
        cls,
        df: pd.DataFrame
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        通用数据质量检查
        
        检查项：
        1. 数据是否为空（无行或无列）
        2. 全局缺失率
        3. 是否存在全空列
        """
        errors = []
        warnings = []
        stats = {}
        
        stats["row_count"] = len(df)
        stats["column_count"] = len(df.columns)
        
        # 检查1: 数据是否为空
        if len(df) == 0:
            errors.append({
                "code": "EMPTY_DATASET",
                "message": "数据集为空（无任何行）",
                "severity": "error",
                "details": {}
            })
            return errors, warnings, stats
        
        if len(df.columns) == 0:
            errors.append({
                "code": "NO_COLUMNS",
                "message": "数据集无任何列",
                "severity": "error",
                "details": {}
            })
            return errors, warnings, stats
        
        # 检查2: 全局缺失率
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        global_missing_rate = missing_cells / total_cells if total_cells > 0 else 0
        
        stats["total_cells"] = int(total_cells)
        stats["missing_cells"] = int(missing_cells)
        stats["global_missing_rate"] = float(global_missing_rate)
        
        if global_missing_rate > 0.8:
            warnings.append({
                "code": "HIGH_GLOBAL_MISSING_RATE",
                "message": f"数据集全局缺失率过高 ({global_missing_rate:.1%})",
                "severity": "warning",
                "details": {
                    "global_missing_rate": float(global_missing_rate),
                    "missing_cells": int(missing_cells),
                    "total_cells": int(total_cells)
                }
            })
        
        # 检查3: 全空列
        empty_columns = [col for col in df.columns if df[col].isnull().all()]
        if empty_columns:
            stats["empty_columns"] = empty_columns
            stats["empty_column_count"] = len(empty_columns)
            
            warnings.append({
                "code": "EMPTY_COLUMNS_EXIST",
                "message": f"数据集包含 {len(empty_columns)} 个全空列，建议移除",
                "severity": "warning",
                "details": {
                    "empty_columns": empty_columns[:10],  # 最多显示10个
                    "empty_column_count": len(empty_columns)
                }
            })
        
        return errors, warnings, stats


def validate_dataset_quality(
    file_path: str,
    target_column: Optional[str] = None,
    time_column: Optional[str] = None,
    sample_rows: int = 10000
) -> Dict[str, Any]:
    """
    便捷函数：验证数据集质量
    
    Args:
        file_path: 数据文件路径
        target_column: 目标列名称
        time_column: 时间列名称
        sample_rows: 采样行数
        
    Returns:
        校验结果字典
        
    Raises:
        DataQualityError: 当发现致命质量问题时抛出
    """
    return DataQualityValidator.validate_for_training(
        file_path=file_path,
        target_column=target_column,
        time_column=time_column,
        sample_rows=sample_rows
    )
