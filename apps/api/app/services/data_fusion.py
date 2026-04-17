"""
数据融合服务

提供多表级联Join功能，支持多种Join类型和编码处理
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import os

from app.schemas.dataset import JoinTable, JoinTypeEnum

logger = logging.getLogger(__name__)


class DataFusionError(Exception):
    """数据融合错误"""
    
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


class DataFusionService:
    """数据融合服务"""
    
    # 支持的编码列表
    SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1', 'iso-8859-1', 'cp1252']
    
    @classmethod
    def execute_join(
        cls,
        main_file_path: str,
        main_join_key: str,
        join_tables: List[JoinTable],
        output_dir: str
    ) -> Dict[str, Any]:
        """
        执行多表级联Join
        
        Args:
            main_file_path: 主表文件路径
            main_join_key: 主表Join键
            join_tables: 从表配置列表
            output_dir: 输出目录
            
        Returns:
            Join结果字典，包含:
            - success: bool, 是否成功
            - before_rows: int, Join前主表行数
            - after_rows: int, Join后行数
            - rows_lost: int, 丢失的行数
            - rows_added_columns: int, 新增的列数
            - message: str, 结果消息
            - joined_columns: List[str], Join后所有列名
            - output_file_path: str, 输出文件路径
            
        Raises:
            DataFusionError: 当Join过程出现错误时抛出
        """
        # 验证主表文件存在
        if not os.path.exists(main_file_path):
            raise DataFusionError(
                error_code="MAIN_FILE_NOT_FOUND",
                message=f"主表文件不存在: {main_file_path}",
                details={"file_path": main_file_path}
            )
        
        # 读取主表
        try:
            main_df = cls._read_file_with_encoding(main_file_path)
            before_rows = len(main_df)
            original_columns = set(main_df.columns)
            logger.info(f"主表加载成功: {main_file_path}, 行数={before_rows}, 列数={len(main_df.columns)}")
        except Exception as e:
            raise DataFusionError(
                error_code="MAIN_FILE_READ_ERROR",
                message=f"无法读取主表文件: {str(e)}",
                details={"file_path": main_file_path, "error": str(e)}
            )
        
        # 验证主表Join键存在
        if main_join_key not in main_df.columns:
            raise DataFusionError(
                error_code="MAIN_JOIN_KEY_NOT_FOUND",
                message=f"主表Join键 '{main_join_key}' 不存在",
                details={
                    "main_join_key": main_join_key,
                    "available_columns": list(main_df.columns)
                }
            )
        
        # 级联Join
        current_df = main_df.copy()
        join_messages = []
        
        for idx, join_table in enumerate(join_tables):
            try:
                current_df, join_msg = cls._execute_single_join(
                    current_df,
                    main_join_key,
                    join_table,
                    idx + 1
                )
                join_messages.append(join_msg)
                logger.info(f"Join完成: 从表{idx+1} '{join_table.name}', {join_msg}")
            except DataFusionError:
                raise
            except Exception as e:
                raise DataFusionError(
                    error_code="JOIN_EXECUTION_ERROR",
                    message=f"Join执行失败 (从表: {join_table.name}): {str(e)}",
                    details={
                        "join_table_name": join_table.name,
                        "join_table_file": join_table.file_path,
                        "error": str(e)
                    }
                )
        
        # 计算结果统计
        after_rows = len(current_df)
        rows_lost = max(0, before_rows - after_rows)
        final_columns = set(current_df.columns)
        rows_added_columns = len(final_columns - original_columns)
        
        # 保存结果
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, f"joined_{os.path.basename(main_file_path)}")
        
        try:
            current_df.to_csv(output_file_path, index=False, encoding='utf-8')
            logger.info(f"Join结果已保存: {output_file_path}")
        except Exception as e:
            raise DataFusionError(
                error_code="OUTPUT_SAVE_ERROR",
                message=f"无法保存Join结果: {str(e)}",
                details={"output_file_path": output_file_path, "error": str(e)}
            )
        
        message = f"成功完成 {len(join_tables)} 个表的级联Join。"
        if rows_lost > 0:
            message += f" 丢失 {rows_lost} 行数据（由于inner join）。"
        message += f" 新增 {rows_added_columns} 列。"
        
        return {
            "success": True,
            "before_rows": before_rows,
            "after_rows": after_rows,
            "rows_lost": rows_lost,
            "rows_added_columns": rows_added_columns,
            "message": message,
            "joined_columns": list(current_df.columns),
            "output_file_path": output_file_path
        }
    
    @classmethod
    def _execute_single_join(
        cls,
        main_df: pd.DataFrame,
        main_join_key: str,
        join_table: JoinTable,
        table_index: int
    ) -> Tuple[pd.DataFrame, str]:
        """
        执行单个Join操作
        
        Args:
            main_df: 主表DataFrame
            main_join_key: 主表Join键
            join_table: 从表配置
            table_index: 从表索引
            
        Returns:
            (Join后的DataFrame, 消息字符串)
            
        Raises:
            DataFusionError: 当Join过程出现错误时抛出
        """
        # 验证从表文件存在
        if not os.path.exists(join_table.file_path):
            raise DataFusionError(
                error_code="JOIN_TABLE_FILE_NOT_FOUND",
                message=f"从表文件不存在: {join_table.file_path}",
                details={
                    "join_table_name": join_table.name,
                    "file_path": join_table.file_path
                }
            )
        
        # 读取从表
        try:
            join_df = cls._read_file_with_encoding(join_table.file_path)
            logger.info(f"从表加载成功: {join_table.name}, 行数={len(join_df)}, 列数={len(join_df.columns)}")
        except Exception as e:
            raise DataFusionError(
                error_code="JOIN_TABLE_READ_ERROR",
                message=f"无法读取从表文件 '{join_table.name}': {str(e)}",
                details={
                    "join_table_name": join_table.name,
                    "file_path": join_table.file_path,
                    "error": str(e)
                }
            )
        
        # 验证从表Join键存在
        if join_table.join_key not in join_df.columns:
            raise DataFusionError(
                error_code="JOIN_TABLE_KEY_NOT_FOUND",
                message=f"从表 '{join_table.name}' 的Join键 '{join_table.join_key}' 不存在",
                details={
                    "join_table_name": join_table.name,
                    "join_key": join_table.join_key,
                    "available_columns": list(join_df.columns)
                }
            )
        
        # 处理列重名问题（跳过join_key）
        join_df = cls._rename_duplicate_columns(main_df, join_df, join_table.name, table_index, join_table.join_key)
        
        # 执行Join
        before_rows = len(main_df)
        
        # 准备Join参数
        join_kwargs = {
            "left_on": main_join_key,
            "right_on": join_table.join_key,
            "how": join_table.join_type.value,
            "suffixes": ("", f"_{join_table.name}")
        }
        
        # 执行merge
        result_df = pd.merge(main_df, join_df, **join_kwargs)
        after_rows = len(result_df)
        
        # 构建消息
        rows_change = after_rows - before_rows
        if join_table.join_type == JoinTypeEnum.INNER:
            msg = f"从表'{join_table.name}': inner join, 行数 {before_rows} -> {after_rows}"
        elif join_table.join_type == JoinTypeEnum.RIGHT:
            msg = f"从表'{join_table.name}': right join, 行数 {before_rows} -> {after_rows}"
        elif join_table.join_type == JoinTypeEnum.OUTER:
            msg = f"从表'{join_table.name}': outer join, 行数 {before_rows} -> {after_rows}"
        else:  # LEFT
            msg = f"从表'{join_table.name}': left join, 行数 {before_rows} -> {after_rows}"
        
        return result_df, msg
    
    @classmethod
    def _read_file_with_encoding(cls, file_path: str) -> pd.DataFrame:
        """
        尝试多种编码读取文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            DataFrame
            
        Raises:
            Exception: 当所有编码都失败时抛出
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        errors = []
        
        if suffix == '.csv':
            for encoding in cls.SUPPORTED_ENCODINGS:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.debug(f"成功使用编码 {encoding} 读取文件: {file_path}")
                    return df
                except UnicodeDecodeError as e:
                    errors.append(f"{encoding}: {str(e)}")
                    continue
                except Exception as e:
                    errors.append(f"{encoding}: {str(e)}")
                    continue
            
            raise Exception(
                f"无法用支持的编码读取CSV文件。尝试的编码: {cls.SUPPORTED_ENCODINGS}。"
                f"错误: {'; '.join(errors[:3])}"
            )
        
        elif suffix == '.parquet':
            try:
                return pd.read_parquet(file_path)
            except Exception as e:
                raise Exception(f"无法读取Parquet文件: {str(e)}")
        
        elif suffix in {'.xlsx', '.xls'}:
            try:
                return pd.read_excel(file_path)
            except Exception as e:
                raise Exception(f"无法读取Excel文件: {str(e)}")
        
        else:
            raise Exception(f"不支持的文件格式: {suffix}")
    
    @classmethod
    def _rename_duplicate_columns(
        cls,
        main_df: pd.DataFrame,
        join_df: pd.DataFrame,
        join_table_name: str,
        table_index: int,
        join_key: str = None
    ) -> pd.DataFrame:
        """
        重命名重复列（保留Join键）
        
        Args:
            main_df: 主表DataFrame
            join_df: 从表DataFrame
            join_table_name: 从表名称
            table_index: 从表索引
            join_key: Join键（不会被重命名）
            
        Returns:
            重命名后的从表DataFrame
        """
        main_columns = set(main_df.columns)
        join_columns = list(join_df.columns)
        
        rename_map = {}
        for col in join_columns:
            # 跳过Join键，不重命名
            if join_key and col == join_key:
                continue
            
            if col in main_columns:
                # 重命名冲突列
                new_col = f"{col}_{join_table_name}"
                # 确保新列名唯一
                counter = 1
                while new_col in main_columns or new_col in rename_map.values():
                    new_col = f"{col}_{join_table_name}_{counter}"
                    counter += 1
                rename_map[col] = new_col
        
        if rename_map:
            join_df = join_df.rename(columns=rename_map)
            logger.info(f"从表 '{join_table_name}' 列重命名: {rename_map}")
        
        return join_df


def execute_data_join(
    main_file_path: str,
    main_join_key: str,
    join_tables: List[JoinTable],
    output_dir: str
) -> Dict[str, Any]:
    """
    便捷函数：执行多表Join
    
    Args:
        main_file_path: 主表文件路径
        main_join_key: 主表Join键
        join_tables: 从表配置列表
        output_dir: 输出目录
        
    Returns:
        Join结果字典
        
    Raises:
        DataFusionError: 当Join过程出现错误时抛出
    """
    return DataFusionService.execute_join(
        main_file_path=main_file_path,
        main_join_key=main_join_key,
        join_tables=join_tables,
        output_dir=output_dir
    )
