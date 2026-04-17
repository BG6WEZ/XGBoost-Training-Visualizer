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


    # 评分权重配置
    SCORE_WEIGHTS = {
        "completeness": 0.30,
        "accuracy": 0.30,
        "consistency": 0.25,
        "distribution": 0.15
    }

    @classmethod
    def calculate_quality_score(
        cls,
        file_path: str,
        target_column: Optional[str] = None,
        time_column: Optional[str] = None,
        sample_rows: int = 10000
    ) -> Dict[str, Any]:
        """
        计算数据质量四维评分
        
        Args:
            file_path: 数据文件路径
            target_column: 目标列名称（可选）
            time_column: 时间列名称（可选）
            sample_rows: 采样行数（用于大文件）
            
        Returns:
            评分结果字典，包含:
            - dataset_id: 数据集标识（文件路径）
            - overall_score: 总分（0-100）
            - dimension_scores: 四维评分
            - errors: 错误列表
            - warnings: 警告列表
            - recommendations: 修复建议列表
            - stats: 数据统计信息
            - evaluated_at: 评估时间
            - weights: 评分权重
        """
        from datetime import datetime
        
        path = Path(file_path)
        errors = []
        warnings = []
        recommendations = []
        
        if not path.exists():
            return {
                "dataset_id": file_path,
                "overall_score": 0,
                "dimension_scores": {
                    "completeness": 0,
                    "accuracy": 0,
                    "consistency": 0,
                    "distribution": 0
                },
                "errors": [{
                    "code": "FILE_NOT_FOUND",
                    "message": f"数据文件不存在: {file_path}",
                    "severity": "error"
                }],
                "warnings": [],
                "recommendations": ["请检查文件路径是否正确"],
                "stats": {},
                "evaluated_at": datetime.now().isoformat(),
                "weights": cls.SCORE_WEIGHTS
            }
        
        try:
            if path.suffix == '.csv':
                df = pd.read_csv(file_path, nrows=sample_rows)
            elif path.suffix == '.parquet':
                df = pd.read_parquet(file_path)
                if len(df) > sample_rows:
                    df = df.head(sample_rows)
            elif path.suffix in {'.xlsx', '.xls'}:
                df = pd.read_excel(file_path, nrows=sample_rows)
            else:
                return {
                    "dataset_id": file_path,
                    "overall_score": 0,
                    "dimension_scores": {
                        "completeness": 0,
                        "accuracy": 0,
                        "consistency": 0,
                        "distribution": 0
                    },
                    "errors": [{
                        "code": "UNSUPPORTED_FORMAT",
                        "message": f"不支持的文件格式: {path.suffix}",
                        "severity": "error"
                    }],
                    "warnings": [],
                    "recommendations": ["请使用 CSV、Excel 或 Parquet 格式"],
                    "stats": {"format": path.suffix},
                    "evaluated_at": datetime.now().isoformat(),
                    "weights": cls.SCORE_WEIGHTS
                }
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
            return {
                "dataset_id": file_path,
                "overall_score": 0,
                "dimension_scores": {
                    "completeness": 0,
                    "accuracy": 0,
                    "consistency": 0,
                    "distribution": 0
                },
                "errors": [{
                    "code": "FILE_READ_ERROR",
                    "message": f"无法读取数据文件: {str(e)}",
                    "severity": "error"
                }],
                "warnings": [],
                "recommendations": ["请检查文件是否损坏或格式是否正确"],
                "stats": {"error": str(e)},
                "evaluated_at": datetime.now().isoformat(),
                "weights": cls.SCORE_WEIGHTS
            }
        
        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "sample_rows_used": len(df),
            "file_size_mb": path.stat().st_size / (1024 * 1024) if path.exists() else 0
        }
        
        logger.info(f"开始评分: dataset={file_path}, rows={len(df)}, cols={len(df.columns)}")
        
        completeness_score, comp_errors, comp_warnings, comp_recs, comp_stats = cls._calculate_completeness_score(df)
        errors.extend(comp_errors)
        warnings.extend(comp_warnings)
        recommendations.extend(comp_recs)
        stats["completeness"] = comp_stats
        
        accuracy_score, acc_errors, acc_warnings, acc_recs, acc_stats = cls._calculate_accuracy_score(df, target_column)
        errors.extend(acc_errors)
        warnings.extend(acc_warnings)
        recommendations.extend(acc_recs)
        stats["accuracy"] = acc_stats
        
        consistency_score, cons_errors, cons_warnings, cons_recs, cons_stats = cls._calculate_consistency_score(df, time_column)
        errors.extend(cons_errors)
        warnings.extend(cons_warnings)
        recommendations.extend(cons_recs)
        stats["consistency"] = cons_stats
        
        distribution_score, dist_errors, dist_warnings, dist_recs, dist_stats = cls._calculate_distribution_score(df, target_column)
        errors.extend(dist_errors)
        warnings.extend(dist_warnings)
        recommendations.extend(dist_recs)
        stats["distribution"] = dist_stats
        
        overall_score = (
            completeness_score * cls.SCORE_WEIGHTS["completeness"] +
            accuracy_score * cls.SCORE_WEIGHTS["accuracy"] +
            consistency_score * cls.SCORE_WEIGHTS["consistency"] +
            distribution_score * cls.SCORE_WEIGHTS["distribution"]
        )
        overall_score = max(0, min(100, round(overall_score, 2)))
        
        dimension_scores = {
            "completeness": round(completeness_score, 2),
            "accuracy": round(accuracy_score, 2),
            "consistency": round(consistency_score, 2),
            "distribution": round(distribution_score, 2)
        }
        
        logger.info(f"评分完成: overall={overall_score}, dimensions={dimension_scores}")
        
        return {
            "dataset_id": file_path,
            "overall_score": overall_score,
            "dimension_scores": dimension_scores,
            "errors": errors,
            "warnings": warnings,
            "recommendations": list(set(recommendations)),
            "stats": stats,
            "evaluated_at": datetime.now().isoformat(),
            "weights": cls.SCORE_WEIGHTS
        }

    @classmethod
    def _calculate_completeness_score(
        cls,
        df: pd.DataFrame
    ) -> Tuple[float, List[Dict], List[Dict], List[str], Dict]:
        """
        计算完整性评分
        
        基于缺失率、空列占比、有效样本占比
        """
        errors = []
        warnings = []
        recommendations = []
        stats = {}
        
        if len(df) == 0:
            errors.append({
                "code": "EMPTY_DATASET",
                "message": "数据集为空（无任何行）",
                "severity": "error"
            })
            return 0, errors, warnings, ["数据集为空，请检查数据源"], stats
        
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        global_missing_rate = missing_cells / total_cells if total_cells > 0 else 0
        
        stats["total_cells"] = int(total_cells)
        stats["missing_cells"] = int(missing_cells)
        stats["global_missing_rate"] = float(global_missing_rate)
        
        empty_columns = [col for col in df.columns if df[col].isnull().all()]
        empty_column_ratio = len(empty_columns) / len(df.columns) if len(df.columns) > 0 else 0
        stats["empty_columns"] = empty_columns[:10]
        stats["empty_column_count"] = len(empty_columns)
        stats["empty_column_ratio"] = float(empty_column_ratio)
        
        valid_row_ratio = (1 - df.isnull().all(axis=1).sum() / len(df)) if len(df) > 0 else 0
        stats["valid_row_ratio"] = float(valid_row_ratio)
        
        if empty_columns:
            warnings.append({
                "code": "EMPTY_COLUMNS_EXIST",
                "message": f"数据集包含 {len(empty_columns)} 个全空列",
                "severity": "warning",
                "details": {"empty_columns": empty_columns[:5]}
            })
            recommendations.append(f"建议移除 {len(empty_columns)} 个全空列以提高数据质量")
        
        if global_missing_rate > 0.5:
            warnings.append({
                "code": "HIGH_MISSING_RATE",
                "message": f"数据集全局缺失率过高 ({global_missing_rate:.1%})",
                "severity": "warning",
                "details": {"missing_rate": float(global_missing_rate)}
            })
            recommendations.append("建议检查数据采集流程，减少缺失值")
        
        missing_score = max(0, 100 * (1 - global_missing_rate))
        empty_col_score = max(0, 100 * (1 - empty_column_ratio))
        valid_row_score = max(0, 100 * valid_row_ratio)
        
        completeness_score = missing_score * 0.5 + empty_col_score * 0.3 + valid_row_score * 0.2
        
        return completeness_score, errors, warnings, recommendations, stats

    @classmethod
    def _calculate_accuracy_score(
        cls,
        df: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> Tuple[float, List[Dict], List[Dict], List[str], Dict]:
        """
        计算准确性评分
        
        基于目标列非法值（NaN/Inf/不可解析）与关键字段可解析率
        """
        errors = []
        warnings = []
        recommendations = []
        stats = {}
        
        if len(df) == 0:
            return 0, errors, warnings, recommendations, stats
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        stats["numeric_column_count"] = len(numeric_cols)
        
        total_inf_count = 0
        total_nan_in_numeric = 0
        
        for col in numeric_cols:
            inf_count = np.isinf(df[col]).sum()
            nan_count = df[col].isnull().sum()
            total_inf_count += inf_count
            total_nan_in_numeric += nan_count
            
            if inf_count > 0:
                warnings.append({
                    "code": "COLUMN_CONTAINS_INF",
                    "message": f"列 '{col}' 包含 {inf_count} 个无穷值",
                    "severity": "warning",
                    "details": {"column": col, "inf_count": int(inf_count)}
                })
        
        stats["total_inf_count"] = int(total_inf_count)
        stats["total_nan_in_numeric"] = int(total_nan_in_numeric)
        
        if total_inf_count > 0:
            recommendations.append("建议处理数值列中的无穷值（Inf/-Inf）")
        
        target_score = 100
        if target_column and target_column in df.columns:
            target_series = df[target_column]
            stats["target_column"] = target_column
            
            if pd.api.types.is_numeric_dtype(target_series):
                target_nan = target_series.isnull().sum()
                target_inf = np.isinf(target_series).sum()
                target_invalid = target_nan + target_inf
                target_invalid_rate = target_invalid / len(target_series) if len(target_series) > 0 else 0
                
                stats["target_nan_count"] = int(target_nan)
                stats["target_inf_count"] = int(target_inf)
                stats["target_invalid_rate"] = float(target_invalid_rate)
                
                if target_inf > 0:
                    errors.append({
                        "code": "TARGET_COLUMN_CONTAINS_INF",
                        "message": f"目标列 '{target_column}' 包含 {target_inf} 个无穷值",
                        "severity": "error",
                        "details": {"target_column": target_column, "inf_count": int(target_inf)}
                    })
                    recommendations.append(f"目标列 '{target_column}' 包含无穷值，必须处理后再训练")
                
                target_score = max(0, 100 * (1 - target_invalid_rate))
            else:
                stats["target_is_numeric"] = False
        elif target_column:
            errors.append({
                "code": "TARGET_COLUMN_NOT_FOUND",
                "message": f"目标列 '{target_column}' 不存在",
                "severity": "error",
                "details": {"target_column": target_column}
            })
            target_score = 0
            recommendations.append(f"目标列 '{target_column}' 不存在，请检查列名")
        
        total_numeric_values = sum(len(df[col].dropna()) for col in numeric_cols)
        if total_numeric_values > 0:
            inf_rate = total_inf_count / total_numeric_values
            numeric_accuracy = max(0, 100 * (1 - inf_rate))
        else:
            numeric_accuracy = 100 if not numeric_cols else 0
        
        accuracy_score = target_score * 0.6 + numeric_accuracy * 0.4
        
        return accuracy_score, errors, warnings, recommendations, stats

    @classmethod
    def _calculate_consistency_score(
        cls,
        df: pd.DataFrame,
        time_column: Optional[str] = None
    ) -> Tuple[float, List[Dict], List[Dict], List[str], Dict]:
        """
        计算一致性评分
        
        基于时间列解析一致性、重复记录比例、关键列类型一致性
        """
        errors = []
        warnings = []
        recommendations = []
        stats = {}
        
        if len(df) == 0:
            return 0, errors, warnings, recommendations, stats
        
        duplicate_count = df.duplicated().sum()
        duplicate_ratio = duplicate_count / len(df) if len(df) > 0 else 0
        stats["duplicate_count"] = int(duplicate_count)
        stats["duplicate_ratio"] = float(duplicate_ratio)
        
        if duplicate_ratio > 0.1:
            warnings.append({
                "code": "HIGH_DUPLICATE_RATIO",
                "message": f"数据集重复记录比例过高 ({duplicate_ratio:.1%})",
                "severity": "warning",
                "details": {"duplicate_count": int(duplicate_count), "duplicate_ratio": float(duplicate_ratio)}
            })
            recommendations.append(f"建议去重，当前有 {duplicate_count} 条重复记录")
        
        duplicate_score = max(0, 100 * (1 - duplicate_ratio * 5))
        
        time_score = 100
        if time_column and time_column in df.columns:
            time_series = df[time_column]
            stats["time_column"] = time_column
            
            if pd.api.types.is_datetime64_any_dtype(time_series):
                stats["time_is_datetime"] = True
                stats["time_parse_rate"] = 1.0
            else:
                stats["time_is_datetime"] = False
                try:
                    sample_size = min(1000, len(time_series))
                    sample_series = time_series.head(sample_size)
                    parsed = pd.to_datetime(sample_series, errors='coerce')
                    parse_success_count = parsed.notna().sum()
                    parse_rate = parse_success_count / sample_size
                    
                    stats["time_parse_rate"] = float(parse_rate)
                    stats["time_parse_sample_size"] = sample_size
                    
                    if parse_rate < 0.5:
                        errors.append({
                            "code": "TIME_COLUMN_PARSE_FAILED",
                            "message": f"时间列 '{time_column}' 解析成功率过低 ({parse_rate:.1%})",
                            "severity": "error",
                            "details": {"time_column": time_column, "parse_rate": float(parse_rate)}
                        })
                        recommendations.append(f"时间列 '{time_column}' 格式不一致，请检查数据格式")
                    elif parse_rate < 1.0:
                        warnings.append({
                            "code": "TIME_COLUMN_PARTIAL_PARSE",
                            "message": f"时间列 '{time_column}' 部分值无法解析 ({(1-parse_rate)*100:.1f}% 失败)",
                            "severity": "warning",
                            "details": {"time_column": time_column, "parse_rate": float(parse_rate)}
                        })
                    
                    time_score = max(0, 100 * parse_rate)
                except Exception as e:
                    errors.append({
                        "code": "TIME_COLUMN_PARSE_ERROR",
                        "message": f"时间列 '{time_column}' 解析失败: {str(e)}",
                        "severity": "error",
                        "details": {"time_column": time_column, "error": str(e)}
                    })
                    time_score = 0
        elif time_column:
            errors.append({
                "code": "TIME_COLUMN_NOT_FOUND",
                "message": f"时间列 '{time_column}' 不存在",
                "severity": "error",
                "details": {"time_column": time_column}
            })
            time_score = 0
        
        type_consistency_score = 100
        object_cols = df.select_dtypes(include=['object']).columns.tolist()
        mixed_type_cols = []
        
        for col in object_cols:
            sample = df[col].dropna().head(100)
            if len(sample) > 0:
                types = set(type(x).__name__ for x in sample)
                if len(types) > 1:
                    mixed_type_cols.append(col)
        
        if mixed_type_cols:
            stats["mixed_type_columns"] = mixed_type_cols[:5]
            stats["mixed_type_column_count"] = len(mixed_type_cols)
            type_consistency_score = max(0, 100 - len(mixed_type_cols) * 10)
            
            warnings.append({
                "code": "MIXED_TYPE_COLUMNS",
                "message": f"发现 {len(mixed_type_cols)} 列存在混合类型",
                "severity": "warning",
                "details": {"columns": mixed_type_cols[:5]}
            })
            recommendations.append("建议统一列数据类型以提高一致性")
        
        consistency_score = duplicate_score * 0.4 + time_score * 0.35 + type_consistency_score * 0.25
        
        return consistency_score, errors, warnings, recommendations, stats

    @classmethod
    def _calculate_distribution_score(
        cls,
        df: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> Tuple[float, List[Dict], List[Dict], List[str], Dict]:
        """
        计算分布评分
        
        基于极端值比例、偏态/离散异常提示
        """
        errors = []
        warnings = []
        recommendations = []
        stats = {}
        
        if len(df) == 0:
            return 0, errors, warnings, recommendations, stats
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            stats["distribution_applicable"] = False
            return 100, errors, warnings, ["无数值列，分布评分不适用"], stats
        
        stats["distribution_applicable"] = True
        stats["numeric_columns_analyzed"] = len(numeric_cols)
        
        outlier_info = []
        skewness_info = []
        
        for col in numeric_cols[:10]:
            series = df[col].dropna()
            if len(series) < 10:
                continue
            
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            
            if iqr > 0:
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = ((series < lower_bound) | (series > upper_bound)).sum()
                outlier_ratio = outliers / len(series)
                
                if outlier_ratio > 0.05:
                    outlier_info.append({
                        "column": col,
                        "outlier_count": int(outliers),
                        "outlier_ratio": float(outlier_ratio)
                    })
            
            if len(series) > 2:
                skewness = series.skew()
                if abs(skewness) > 2:
                    skewness_info.append({
                        "column": col,
                        "skewness": float(skewness)
                    })
        
        stats["outlier_columns"] = [o["column"] for o in outlier_info]
        stats["outlier_column_count"] = len(outlier_info)
        stats["high_skewness_columns"] = [s["column"] for s in skewness_info]
        stats["high_skewness_column_count"] = len(skewness_info)
        
        if outlier_info:
            warnings.append({
                "code": "OUTLIERS_DETECTED",
                "message": f"发现 {len(outlier_info)} 列存在较多极端值",
                "severity": "warning",
                "details": {"outlier_info": outlier_info[:3]}
            })
            recommendations.append("建议检查极端值是否为数据错误或需要特殊处理")
        
        if skewness_info:
            warnings.append({
                "code": "HIGH_SKEWNESS",
                "message": f"发现 {len(skewness_info)} 列分布高度偏态",
                "severity": "warning",
                "details": {"skewness_info": skewness_info[:3]}
            })
            recommendations.append("高度偏态的数据可能影响模型效果，可考虑对数变换")
        
        outlier_penalty = min(len(outlier_info) * 5, 30)
        skewness_penalty = min(len(skewness_info) * 3, 20)
        
        distribution_score = max(0, 100 - outlier_penalty - skewness_penalty)
        
        if target_column and target_column in numeric_cols:
            target_series = df[target_column].dropna()
            if len(target_series) > 10:
                target_skewness = target_series.skew()
                stats["target_skewness"] = float(target_skewness)
                
                if abs(target_skewness) > 2:
                    recommendations.append(f"目标列 '{target_column}' 分布高度偏态（偏度={target_skewness:.2f}），可考虑变换")
        
        return distribution_score, errors, warnings, recommendations, stats


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


def calculate_quality_score(
    file_path: str,
    target_column: Optional[str] = None,
    time_column: Optional[str] = None,
    sample_rows: int = 10000
) -> Dict[str, Any]:
    """
    便捷函数：计算数据质量评分
    
    Args:
        file_path: 数据文件路径
        target_column: 目标列名称
        time_column: 时间列名称
        sample_rows: 采样行数
        
    Returns:
        评分结果字典
    """
    return DataQualityValidator.calculate_quality_score(
        file_path=file_path,
        target_column=target_column,
        time_column=time_column,
        sample_rows=sample_rows
    )
