"""
数据资产扫描与登记服务

提供：
- 目录扫描与数据源识别
- 自动Schema探测
- 数据资产登记
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# 数据源类型定义
DATASET_SOURCES = {
    "heew": {
        "name": "HEEW",
        "patterns": ["HEEW"],
        "description": "多建筑能耗与天气数据集"
    },
    "ashrae_gepiii": {
        "name": "ASHRAE GEP III",
        "patterns": ["ashrae-gepiii"],
        "description": "ASHRAE 能源预测竞赛数据集"
    },
    "bdg2": {
        "name": "BDG2",
        "patterns": ["bdg2"],
        "description": "建筑数据基因组2数据集"
    },
    "bldg59": {
        "name": "Bldg59",
        "patterns": ["A three-year dataset"],
        "description": "单建筑多传感器高频数据集"
    },
    "google_trends": {
        "name": "Google Trends for Buildings",
        "patterns": ["google-trends-for-buildings"],
        "description": "Google Trends 外生行为代理数据"
    },
    "demo": {
        "name": "Demo",
        "patterns": ["building_energy_data_extended.csv"],
        "description": "演示用综合表"
    }
}

# 常见时间列名模式
TIME_COLUMN_PATTERNS = [
    r"timestamp", r"time", r"date", r"datetime",
    r"^dt$", r"^ts$", r"年", r"月", r"日", r"时",
    r"^Year$", r"^Month$", r"^Day$", r"^Hour$"
]

# 常见目标列名模式
TARGET_COLUMN_PATTERNS = [
    r"energy", r"power", r"consumption", r"usage",
    r"load", r"demand", r"kwh", r"electricity",
    r"target", r"^y$", r"label"
]

# 常见实体列名模式
ENTITY_COLUMN_PATTERNS = [
    r"building", r"site", r"entity", r"id",
    r"building_id", r"site_id", r"meter_id"
]


class DatasetScanner:
    """数据集扫描器"""

    def __init__(self, dataset_base_path: str):
        self.base_path = Path(dataset_base_path)
        if not self.base_path.exists():
            raise ValueError(f"Dataset directory not found: {dataset_base_path}")

    def scan_directory(self) -> List[Dict[str, Any]]:
        """
        扫描数据集目录，返回发现的数据资产列表
        """
        assets = []

        # 扫描顶层目录
        for item in self.base_path.iterdir():
            if item.is_dir():
                # 尝试识别数据源类型
                source_info = self._identify_source(item.name)
                if source_info:
                    # 扫描数据源目录
                    source_assets = self._scan_source_directory(item, source_info)
                    assets.extend(source_assets)
            elif item.is_file() and item.suffix in ['.csv', '.parquet']:
                # 单文件数据集（如 demo 数据）
                source_info = self._identify_source(item.name)
                if source_info:
                    asset = self._create_file_asset(item, source_info)
                    if asset:
                        assets.append(asset)

        return assets

    def _identify_source(self, name: str) -> Optional[Dict[str, Any]]:
        """识别数据源类型"""
        name_lower = name.lower()

        for source_key, source_config in DATASET_SOURCES.items():
            for pattern in source_config["patterns"]:
                if pattern.lower() in name_lower:
                    return {
                        "key": source_key,
                        "name": source_config["name"],
                        "description": source_config["description"]
                    }

        return None

    def _scan_source_directory(self, source_dir: Path, source_info: Dict) -> List[Dict[str, Any]]:
        """扫描数据源目录，识别可登记的数据资产"""
        assets = []

        # 检查是否有 cleaned data 和 raw data 目录
        cleaned_dir = source_dir / "cleaned data"
        raw_dir = source_dir / "raw data" / "raw" if (source_dir / "raw data").exists() else source_dir / "raw"

        # 检查常见的子目录结构
        subdirs = list(source_dir.iterdir())

        # 对于 HEEW 类型的数据
        if source_info["key"] == "heew":
            # 扫描 cleaned data 目录
            if cleaned_dir.exists():
                # 检查是否有总表文件
                total_energy = cleaned_dir / "Total_energy.csv"
                total_weather = cleaned_dir / "Total_weather.csv"

                if total_energy.exists():
                    assets.append({
                        "name": f"{source_info['name']} - Total Energy",
                        "source_type": source_info["key"],
                        "source_name": source_info["name"],
                        "path": str(total_energy),
                        "path_type": "file",
                        "is_raw": False,
                        "description": "HEEW 总能耗数据（清洗后）",
                        "member_files": [{
                            "file_path": str(total_energy),
                            "file_name": "Total_energy.csv",
                            "role": "primary"
                        }]
                    })

                    if total_weather.exists():
                        assets[-1]["member_files"].append({
                            "file_path": str(total_weather),
                            "file_name": "Total_weather.csv",
                            "role": "supplementary"
                        })

                # 扫描单建筑文件
                building_files = list(cleaned_dir.glob("BN*_energy.csv")) + list(cleaned_dir.glob("CN*_energy.csv"))
                if building_files:
                    # 可以创建一个"所有建筑"的数据集
                    assets.append({
                        "name": f"{source_info['name']} - All Buildings",
                        "source_type": source_info["key"],
                        "source_name": source_info["name"],
                        "path": str(cleaned_dir),
                        "path_type": "directory",
                        "is_raw": False,
                        "description": "HEEW 所有建筑能耗数据",
                        "member_files": [
                            {
                                "file_path": str(f),
                                "file_name": f.name,
                                "role": "primary"
                            }
                            for f in sorted(building_files)[:10]  # 限制数量
                        ]
                    })

            # 扫描 raw data 目录
            if raw_dir.exists():
                raw_files = list(raw_dir.glob("*.csv"))
                if raw_files:
                    assets.append({
                        "name": f"{source_info['name']} - Raw Data",
                        "source_type": source_info["key"],
                        "source_name": source_info["name"],
                        "path": str(raw_dir),
                        "path_type": "directory",
                        "is_raw": True,
                        "description": "HEEW 原始能耗数据",
                        "member_files": [
                            {
                                "file_path": str(f),
                                "file_name": f.name,
                                "role": "primary"
                            }
                            for f in sorted(raw_files)[:10]
                        ]
                    })

        # 对于 ASHRAE 类型的数据
        elif source_info["key"] == "ashrae_gepiii":
            raw_path = source_dir / "raw"
            if raw_path.exists():
                train_csv = raw_path / "train.csv"
                test_csv = raw_path / "test.csv"
                weather_train = raw_path / "weather_train.csv"
                weather_test = raw_path / "weather_test.csv"
                building_meta = raw_path / "building_metadata.csv"

                if train_csv.exists():
                    members = [{
                        "file_path": str(train_csv),
                        "file_name": "train.csv",
                        "role": "primary"
                    }]
                    if weather_train.exists():
                        members.append({
                            "file_path": str(weather_train),
                            "file_name": "weather_train.csv",
                            "role": "supplementary"
                        })
                    if building_meta.exists():
                        members.append({
                            "file_path": str(building_meta),
                            "file_name": "building_metadata.csv",
                            "role": "metadata"
                        })

                    assets.append({
                        "name": f"{source_info['name']} - Training Set",
                        "source_type": source_info["key"],
                        "source_name": source_info["name"],
                        "path": str(raw_path),
                        "path_type": "directory",
                        "is_raw": True,
                        "description": "ASHRAE GEP III 训练数据集",
                        "member_files": members
                    })

        # 对于 Bldg59 类型的数据
        elif source_info["key"] == "bldg59":
            clean_dir = source_dir / "Bldg59_clean data"
            if clean_dir.exists():
                # 识别所有 CSV 文件
                csv_files = list(clean_dir.glob("*.csv"))

                # 分类文件
                primary_files = []
                supplementary_files = []

                for f in csv_files:
                    name_lower = f.stem.lower()
                    if "ele" in name_lower or "energy" in name_lower:
                        primary_files.append(f)
                    else:
                        supplementary_files.append(f)

                if primary_files:
                    members = [
                        {"file_path": str(f), "file_name": f.name, "role": "primary"}
                        for f in primary_files[:5]
                    ]
                    members.extend([
                        {"file_path": str(f), "file_name": f.name, "role": "supplementary"}
                        for f in supplementary_files[:5]  # 限制数量
                    ])

                    assets.append({
                        "name": f"{source_info['name']} - Clean Data",
                        "source_type": source_info["key"],
                        "source_name": source_info["name"],
                        "path": str(clean_dir),
                        "path_type": "directory",
                        "is_raw": False,
                        "description": "Bldg59 多传感器数据集",
                        "member_files": members
                    })

        # 对于 BDG2 类型的数据
        elif source_info["key"] == "bdg2":
            data_dir = source_dir / "data"
            if data_dir.exists():
                meters_dir = data_dir / "meters" / "cleaned"
                metadata_file = data_dir / "metadata" / "metadata.csv"
                weather_file = data_dir / "weather" / "weather.csv"

                if meters_dir.exists():
                    meter_files = list(meters_dir.glob("*.csv"))[:5]  # 限制数量

                    if meter_files:
                        members = [
                            {"file_path": str(f), "file_name": f.name, "role": "primary"}
                            for f in meter_files
                        ]
                        if metadata_file.exists():
                            members.append({
                                "file_path": str(metadata_file),
                                "file_name": "metadata.csv",
                                "role": "metadata"
                            })
                        if weather_file.exists():
                            members.append({
                                "file_path": str(weather_file),
                                "file_name": "weather.csv",
                                "role": "supplementary"
                            })

                        assets.append({
                            "name": f"{source_info['name']} - Meter Data",
                            "source_type": source_info["key"],
                            "source_name": source_info["name"],
                            "path": str(meters_dir),
                            "path_type": "directory",
                            "is_raw": False,
                            "description": "BDG2 建筑能耗表计数据",
                            "member_files": members
                        })

        # 通用扫描：如果没有特殊处理，直接扫描 CSV 文件
        if not assets:
            csv_files = list(source_dir.glob("**/*.csv"))[:10]
            if csv_files:
                assets.append({
                    "name": f"{source_info['name']} - Data Files",
                    "source_type": source_info["key"],
                    "source_name": source_info["name"],
                    "path": str(source_dir),
                    "path_type": "directory",
                    "is_raw": True,
                    "description": source_info["description"],
                    "member_files": [
                        {"file_path": str(f), "file_name": f.name, "role": "primary"}
                        for f in csv_files
                    ]
                })

        return assets

    def _create_file_asset(self, file_path: Path, source_info: Dict) -> Optional[Dict[str, Any]]:
        """创建单文件数据资产"""
        return {
            "name": f"{source_info['name']} - {file_path.stem}",
            "source_type": source_info["key"],
            "source_name": source_info["name"],
            "path": str(file_path),
            "path_type": "file",
            "is_raw": True,
            "description": source_info["description"],
            "member_files": [{
                "file_path": str(file_path),
                "file_name": file_path.name,
                "role": "primary"
            }]
        }


class SchemaProfiler:
    """Schema 探测器"""

    @staticmethod
    def _clean_nan_values(obj: Any) -> Any:
        """递归清理 NaN 值，转换为 None（PostgreSQL JSON 不支持 NaN）"""
        if isinstance(obj, dict):
            return {k: SchemaProfiler._clean_nan_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [SchemaProfiler._clean_nan_values(item) for item in obj]
        elif isinstance(obj, float) and (np.isnan(obj) or pd.isna(obj)):
            return None
        elif obj is pd.NA or obj is np.nan:
            return None
        else:
            return obj

    @staticmethod
    def profile_file(file_path: str, sample_rows: int = 1000) -> Dict[str, Any]:
        """
        分析文件并生成 Schema Profile

        返回：
        - 列信息列表
        - 行数
        - 推荐的时间列候选
        - 推荐的目标列候选
        - 推荐的实体列候选
        - 数据质量摘要
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 读取文件
        if path.suffix == '.csv':
            df = pd.read_csv(file_path, nrows=sample_rows)
            total_rows = sum(1 for _ in open(file_path)) - 1  # 减去 header
        elif path.suffix == '.parquet':
            df = pd.read_parquet(file_path)
            total_rows = len(df)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        columns_info = []
        time_candidates = []
        target_candidates = []
        entity_candidates = []

        for col in df.columns:
            col_info = SchemaProfiler._analyze_column(df, col)
            columns_info.append(col_info)

            # 检测候选列
            col_lower = col.lower()
            if col_info["is_time_candidate"]:
                time_candidates.append(col)
            if col_info["is_target_candidate"]:
                target_candidates.append(col)
            if col_info["is_entity_candidate"]:
                entity_candidates.append(col)

        result = {
            "file_path": file_path,
            "file_name": path.name,
            "row_count": total_rows,
            "column_count": len(df.columns),
            "columns_info": columns_info,
            "time_candidates": time_candidates,
            "target_candidates": target_candidates,
            "entity_candidates": entity_candidates,
            "quality_summary": {
                "total_cells": total_rows * len(df.columns),
                "missing_cells": int(df.isnull().sum().sum()),
                "missing_rate": float(df.isnull().sum().sum() / (total_rows * len(df.columns))) if total_rows > 0 else 0
            }
        }
        return SchemaProfiler._clean_nan_values(result)

    @staticmethod
    def _analyze_column(df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """分析单列"""
        series = df[col]
        col_lower = col.lower()

        # 基础信息
        info = {
            "name": col,
            "dtype": str(series.dtype),
            "missing_count": int(series.isnull().sum()),
            "missing_rate": float(series.isnull().sum() / len(series)) if len(series) > 0 else 0,
            "unique_count": int(series.nunique()),
            "is_numeric": pd.api.types.is_numeric_dtype(series),
            "is_datetime": pd.api.types.is_datetime64_any_dtype(series),
            "is_categorical": pd.api.types.is_categorical_dtype(series) or (
                pd.api.types.is_object_dtype(series) and series.nunique() < len(series) * 0.1
            ),
            "is_time_candidate": False,
            "is_target_candidate": False,
            "is_entity_candidate": False,
        }

        # 检测时间列候选
        for pattern in TIME_COLUMN_PATTERNS:
            if re.search(pattern, col_lower, re.IGNORECASE):
                info["is_time_candidate"] = True
                break

        # 如果列名不明显，尝试解析
        if not info["is_time_candidate"] and info["dtype"] == 'object':
            try:
                pd.to_datetime(series.head(100), errors='raise')
                info["is_time_candidate"] = True
                info["dtype"] = "datetime"
            except:
                pass

        # 检测目标列候选
        for pattern in TARGET_COLUMN_PATTERNS:
            if re.search(pattern, col_lower, re.IGNORECASE):
                info["is_target_candidate"] = True
                break

        # 检测实体列候选
        for pattern in ENTITY_COLUMN_PATTERNS:
            if re.search(pattern, col_lower, re.IGNORECASE):
                info["is_entity_candidate"] = True
                break

        # 数值列统计
        if info["is_numeric"]:
            min_val = series.min()
            max_val = series.max()
            mean_val = series.mean()
            std_val = series.std()
            
            # 转换 NaN 为 None（PostgreSQL JSON 不支持 NaN）
            info["min"] = None if pd.isna(min_val) else float(min_val)
            info["max"] = None if pd.isna(max_val) else float(max_val)
            info["mean"] = None if pd.isna(mean_val) else float(mean_val)
            info["std"] = None if pd.isna(std_val) else float(std_val)

        return info


async def register_dataset_asset(
    asset_info: Dict[str, Any],
    db_session,
    generate_profile: bool = True
) -> Dict[str, Any]:
    """
    登记数据资产到数据库

    Args:
        asset_info: 数据资产信息（来自扫描结果）
        db_session: 数据库会话
        generate_profile: 是否生成详细的 Schema Profile

    Returns:
        创建的数据集记录
        
    Note:
        返回的 dataset 对象的 files 关系已填充，可在 session 外安全访问
    """
    from app.models import Dataset, DatasetFile, FileRole

    # 创建数据集记录
    dataset = Dataset(
        name=asset_info["name"],
        description=asset_info.get("description", ""),
        # 存储数据源信息在 description 中或创建新字段
    )
    
    # 确保 files 列表已初始化（避免懒加载）
    if not hasattr(dataset, '_files_loaded'):
        dataset._files_loaded = True

    # 处理成员文件
    total_rows = 0
    total_columns = 0
    total_size = 0

    for member in asset_info.get("member_files", []):
        file_path = member["file_path"]
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        # 获取文件大小
        file_size = path.stat().st_size if path.exists() else 0

        # 生成 Schema Profile
        columns_info = None
        row_count = 0
        column_count = 0

        if generate_profile and path.suffix in ['.csv', '.parquet']:
            try:
                profile = SchemaProfiler.profile_file(file_path)
                columns_info = profile["columns_info"]
                row_count = profile["row_count"]
                column_count = profile["column_count"]
            except Exception as e:
                logger.error(f"Failed to profile file {file_path}: {e}")

        # 创建文件记录
        file_record = DatasetFile(
            file_path=file_path,
            file_name=member["file_name"],
            role=member.get("role", FileRole.primary.value),
            file_size=file_size,
            row_count=row_count,
            column_count=column_count,
            columns_info=columns_info
        )
        
        # 直接添加到 files 列表（避免依赖懒加载）
        dataset.files.append(file_record)

        total_rows += row_count
        total_columns = max(total_columns, column_count)
        total_size += file_size

    # 更新汇总统计
    dataset.total_row_count = total_rows
    dataset.total_column_count = total_columns
    dataset.total_file_size = total_size

    return dataset