import logging
from typing import Dict, Any, Optional, Callable, List
import asyncio
import os
import json
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class XGBoostTrainer:
    """XGBoost 训练器"""

    def __init__(
        self,
        experiment_id: str,
        config: Dict[str, Any],
        dataset_path: str,
        work_dir: str,
        progress_callback: Optional[Callable] = None,
        metrics_callback: Optional[Callable] = None
    ):
        self.experiment_id = experiment_id
        self.config = config
        self.dataset_path = dataset_path
        self.work_dir = work_dir
        self.progress_callback = progress_callback
        self.metrics_callback = metrics_callback
        self.is_stopped = False
        self.model = None
        self.metrics: List[Dict[str, Any]] = []

    async def load_data(self) -> tuple:
        """加载训练数据"""
        import pandas as pd
        import numpy as np
        from sklearn.model_selection import train_test_split

        logger.info(f"Loading dataset from {self.dataset_path}")

        # 检测文件类型
        if self.dataset_path.endswith('.csv'):
            df = pd.read_csv(self.dataset_path)
        elif self.dataset_path.endswith('.parquet'):
            df = pd.read_parquet(self.dataset_path)
        else:
            raise ValueError(f"Unsupported file format: {self.dataset_path}")

        logger.info(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")

        # 获取目标列
        target_column = self.config.get('target_column')
        if not target_column:
            # 尝试自动检测
            potential_targets = [col for col in df.columns if 'target' in col.lower() or 'y' == col.lower()]
            if potential_targets:
                target_column = potential_targets[0]
            else:
                target_column = df.columns[-1]  # 默认最后一列

        logger.info(f"Using target column: {target_column}")

        if target_column not in df.columns:
            raise ValueError(
                f"Target column '{target_column}' not found in dataset columns: {list(df.columns)}"
            )

        # 分离特征和目标
        X = df.drop(columns=[target_column])
        y_raw = df[target_column]
        y = pd.to_numeric(y_raw, errors='coerce')

        # 训练前强校验标签列，避免触发底层 XGBoost 报错且无法定位。
        y_values = y.to_numpy(dtype='float64')
        nan_count = int(np.isnan(y_values).sum())
        inf_count = int(np.isinf(y_values).sum())
        finite_mask = np.isfinite(y_values)
        too_large_count = int(((np.abs(y_values) > np.finfo(np.float32).max) & finite_mask).sum())

        invalid_mask = np.isnan(y_values) | np.isinf(y_values) | (
            (np.abs(y_values) > np.finfo(np.float32).max) & finite_mask
        )
        invalid_count = int(invalid_mask.sum())

        if invalid_count > 0:
            invalid_indices = np.where(invalid_mask)[0][:5]
            sample_values = [
                {
                    "row_index": int(idx),
                    "value": str(y_raw.iloc[idx]),
                }
                for idx in invalid_indices
            ]
            raise ValueError(
                f"Invalid target values in column '{target_column}': "
                f"nan={nan_count}, inf={inf_count}, too_large={too_large_count}, "
                f"invalid_total={invalid_count}, samples={sample_values}. "
                "Please clean target column values via preprocessing or choose a valid target column."
            )

        y = pd.Series(y_values, index=df.index, name=target_column)

        # 处理非数值列
        for col in X.select_dtypes(include=['object']).columns:
            X[col] = pd.Categorical(X[col]).codes

        # 处理时间列
        for col in X.select_dtypes(include=['datetime64']).columns:
            X[col] = X[col].astype('int64') // 10**9

        # 填充缺失值
        X = X.fillna(X.mean())

        # 划分训练集和验证集
        test_size = self.config.get('test_size', 0.2)
        random_seed = self.config.get('random_seed', 42)

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=random_seed
        )

        logger.info(f"Train set: {len(X_train)} samples, Val set: {len(X_val)} samples")

        return X_train, X_val, y_train, y_val, list(X.columns)

    async def train(self) -> Dict[str, Any]:
        """执行训练"""
        import xgboost as xgb
        import numpy as np

        # 加载数据
        X_train, X_val, y_train, y_val, feature_names = await self.load_data()

        # 构建 XGBoost 参数
        xgb_params = self.config.get('xgboost_params', {})
        n_estimators = xgb_params.get('n_estimators', 100)

        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'learning_rate': xgb_params.get('learning_rate', 0.1),
            'max_depth': xgb_params.get('max_depth', 6),
            'subsample': xgb_params.get('subsample', 1.0),
            'colsample_bytree': xgb_params.get('colsample_bytree', 1.0),
            'gamma': xgb_params.get('gamma', 0),
            'alpha': xgb_params.get('alpha', 0),
            'lambda': xgb_params.get('lambda', 1),
            'min_child_weight': xgb_params.get('min_child_weight', 1),
            'seed': self.config.get('random_seed', 42),
        }

        # 创建 DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        evals_result = {}
        early_stopping_rounds = self.config.get('early_stopping_rounds')
        trainer_self = self

        class ProgressCallback(xgb.callback.TrainingCallback):
            def __init__(self):
                super().__init__()

            def after_iteration(self, model, epoch, evals_log):
                if trainer_self.is_stopped:
                    return True

                if evals_log and 'train' in evals_log and 'val' in evals_log:
                    train_rmse = evals_log['train']['rmse'][-1] if evals_log['train']['rmse'] else None
                    val_rmse = evals_log['val']['rmse'][-1] if evals_log['val']['rmse'] else None

                    if train_rmse is not None and val_rmse is not None:
                        trainer_self.metrics.append({
                            'iteration': epoch + 1,
                            'train_loss': float(train_rmse),
                            'val_loss': float(val_rmse)
                        })

                return False

        progress_callback = ProgressCallback()

        logger.info(f"Starting XGBoost training with {n_estimators} iterations")
        if early_stopping_rounds and early_stopping_rounds > 0:
            logger.info(f"Early stopping enabled with {early_stopping_rounds} rounds")

        train_kwargs = {
            'params': params,
            'dtrain': dtrain,
            'num_boost_round': n_estimators,
            'evals': [(dtrain, 'train'), (dval, 'val')],
            'evals_result': evals_result,
            'callbacks': [progress_callback],
            'verbose_eval': False
        }
        
        if early_stopping_rounds and early_stopping_rounds > 0:
            train_kwargs['early_stopping_rounds'] = early_stopping_rounds

        self.model = xgb.train(**train_kwargs)

        best_iteration = self.model.best_iteration if hasattr(self.model, 'best_iteration') else n_estimators - 1
        best_val_loss = evals_result.get('val', {}).get('rmse', [float('inf')])[-1] if evals_result else float('inf')

        # 计算最终指标
        y_pred_train = self.model.predict(dtrain)
        y_pred_val = self.model.predict(dval)

        metrics = self._calculate_metrics(y_train, y_pred_train, y_val, y_pred_val)

        # 获取特征重要性
        importance = self.model.get_score(importance_type='gain')
        feature_importance = [
            {'feature': k, 'importance': v}
            for k, v in sorted(importance.items(), key=lambda x: x[1], reverse=True)
        ]

        # 保存预测数据（用于结果分析）
        # 残差定义: residual = actual - predicted
        self._prediction_data = {
            'experiment_id': self.experiment_id,
            'validation': {
                'actual_values': y_val.tolist() if hasattr(y_val, 'tolist') else list(y_val),
                'predicted_values': y_pred_val.tolist() if hasattr(y_pred_val, 'tolist') else list(y_pred_val),
                'residual_values': (
                    (y_val.values if hasattr(y_val, 'values') else y_val) - y_pred_val
                ).tolist() if hasattr(y_val, 'values') else (y_val - y_pred_val).tolist(),
                'sample_count': len(y_val)
            }
        }

        return {
            'experiment_id': self.experiment_id,
            'metrics': metrics,
            'feature_importance': feature_importance,
            'best_iteration': best_iteration,
            'n_features': len(feature_names),
            'feature_names': feature_names
        }

    def _calculate_metrics(self, y_train, y_pred_train, y_val, y_pred_val) -> Dict[str, float]:
        """计算评估指标"""
        import numpy as np
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
        train_mae = mean_absolute_error(y_train, y_pred_train)
        val_mae = mean_absolute_error(y_val, y_pred_val)
        r2 = r2_score(y_val, y_pred_val)

        return {
            'train_rmse': float(train_rmse),
            'val_rmse': float(val_rmse),
            'train_mae': float(train_mae),
            'val_mae': float(val_mae),
            'r2': float(r2)
        }

    async def save_model(self, format: str = 'json') -> str:
        """保存模型"""
        os.makedirs(self.work_dir, exist_ok=True)

        model_dir = os.path.join(self.work_dir, 'models')
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, f"{self.experiment_id}.{format}")

        if format == 'json':
            self.model.save_model(model_path)
        elif format == 'ubj':
            self.model.save_model(model_path)
        else:
            raise ValueError(f"Unsupported model format: {format}")

        logger.info(f"Model saved to {model_path}")
        return model_path

    def stop(self):
        """停止训练"""
        self.is_stopped = True


async def run_training_task(ctx: Dict[str, Any], experiment_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行训练任务

    Args:
        ctx: 上下文
        experiment_id: 实验ID
        config: 训练配置

    Returns:
        训练结果
    """
    from app.storage import get_storage_service
    
    logger.info(f"Starting training task for experiment {experiment_id}")

    try:
        # 获取数据集路径
        dataset_path = config.get('dataset_path')
        work_dir = config.get('work_dir', './workspace')

        if not dataset_path:
            raise ValueError("dataset_path is required in config")

        # 创建训练器
        trainer = XGBoostTrainer(
            experiment_id=experiment_id,
            config=config,
            dataset_path=dataset_path,
            work_dir=work_dir
        )

        # 执行训练
        result = await trainer.train()

        # 保存模型
        model_format = config.get('model_format', 'json')
        model_path = await trainer.save_model(model_format)

        result['model_path'] = model_path
        result['status'] = 'completed'
        result['training_metrics'] = trainer.metrics  # 包含所有训练指标

        # 保存预测数据（用于结果分析）
        if hasattr(trainer, '_prediction_data') and trainer._prediction_data:
            try:
                storage = get_storage_service()
                prediction_data_bytes = json.dumps(trainer._prediction_data).encode('utf-8')
                await storage.save_prediction_data(experiment_id, prediction_data_bytes)
                logger.info(f"Prediction data saved for experiment {experiment_id}")
            except Exception as e:
                logger.warning(f"Failed to save prediction data: {e}")

        logger.info(f"Training completed for experiment {experiment_id}")
        return result

    except Exception as e:
        logger.exception(f"Training failed for experiment {experiment_id}: {e}")
        return {
            "experiment_id": experiment_id,
            "status": "failed",
            "error": str(e)
        }


async def run_preprocessing_task(ctx: Dict[str, Any], dataset_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行数据预处理任务

    Args:
        ctx: 上下文
        dataset_id: 数据集ID
        config: 预处理配置

    Returns:
        预处理结果（包含存储信息）
    """
    import pandas as pd
    import numpy as np
    import tempfile
    from app.storage import get_storage_service

    logger.info(f"Starting preprocessing task for dataset {dataset_id}")

    try:
        dataset_path = config.get('dataset_path')
        if not dataset_path:
            raise ValueError("dataset_path is required")

        # 加载数据
        if dataset_path.endswith('.csv'):
            df = pd.read_csv(dataset_path)
        else:
            df = pd.read_parquet(dataset_path)

        original_shape = df.shape
        summary = {
            "missing_value_handling": {},
            "encoding": {},
            "remove_duplicates": {
                "original_count": len(df),
                "duplicates_removed": 0
            },
            "columns": {
                "original": list(df.columns),
                "processed": [],
                "added": [],
                "removed": []
            }
        }

        # 预处理步骤
        
        # 1. 处理缺失值
        missing_strategy = config.get('missing_value_strategy', 'mean_fill')
        target_columns = config.get('target_columns', df.columns.tolist())
        
        if missing_strategy == 'forward_fill':
            # 对所有列执行前向填充
            for col in target_columns:
                if col in df.columns:
                    original_nan = df[col].isna().sum()
                    if original_nan > 0:
                        df[col] = df[col].ffill()
                        summary["missing_value_handling"][col] = {
                            "strategy": "forward_fill",
                            "original_nan_count": int(original_nan),
                            "remaining_nan_count": int(df[col].isna().sum())
                        }
        elif missing_strategy == 'mean_fill':
            # 仅对数值列执行均值填充
            for col in target_columns:
                if col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        original_nan = df[col].isna().sum()
                        if original_nan > 0:
                            df[col] = df[col].fillna(df[col].mean())
                            summary["missing_value_handling"][col] = {
                                "strategy": "mean_fill",
                                "original_nan_count": int(original_nan),
                                "remaining_nan_count": int(df[col].isna().sum())
                            }
                    else:
                        raise ValueError(f"Cannot apply mean_fill to non-numeric column: {col}")
        elif missing_strategy == 'drop_rows':
            # 计算删除的行数
            original_rows = len(df)
            df = df.dropna(subset=target_columns)
            dropped_rows = original_rows - len(df)
            summary["missing_value_handling"]["drop_rows"] = {
                "original_row_count": original_rows,
                "dropped_row_count": dropped_rows,
                "remaining_row_count": len(df)
            }

        # 2. 处理重复行
        if config.get('remove_duplicates', True):
            original_count = len(df)
            df = df.drop_duplicates()
            duplicates_removed = original_count - len(df)
            summary["remove_duplicates"]["duplicates_removed"] = duplicates_removed

        # 3. 异常值处理
        if config.get('handle_outliers', False):
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df[col] = df[col].clip(lower_bound, upper_bound)

        # 4. 编码策略
        encoding_strategy = config.get('encoding_strategy')
        if encoding_strategy:
            # 自动识别分类列
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            if target_columns:
                categorical_cols = [col for col in categorical_cols if col in target_columns]
            
            if not categorical_cols:
                summary["encoding"]["message"] = "No categorical columns found for encoding"
            else:
                original_columns = df.columns.tolist()
                
                if encoding_strategy == 'one_hot':
                    # 检查基数
                    high_cardinality_cols = []
                    for col in categorical_cols:
                        if df[col].nunique() > 10:
                            high_cardinality_cols.append(col)
                    
                    if high_cardinality_cols:
                        raise ValueError(f"High cardinality columns found: {high_cardinality_cols}. Consider using label encoding instead.")
                    
                    # 执行独热编码
                    df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
                    new_columns = [col for col in df.columns if col not in original_columns]
                    summary["encoding"]["one_hot"] = {
                        "columns": categorical_cols,
                        "new_columns_added": new_columns,
                        "total_columns_added": len(new_columns)
                    }
                
                elif encoding_strategy == 'label_encoding':
                    # 执行标签编码
                    for col in categorical_cols:
                        df[col] = pd.Categorical(df[col]).codes
                    summary["encoding"]["label_encoding"] = {
                        "columns": categorical_cols
                    }

        # 更新列信息
        summary["columns"]["processed"] = list(df.columns)
        summary["columns"]["added"] = [col for col in df.columns if col not in summary["columns"]["original"]]
        summary["columns"]["removed"] = [col for col in summary["columns"]["original"] if col not in df.columns]

        # 通过存储适配层保存预处理结果
        task_id = config.get('task_id', 'unknown')
        storage = get_storage_service()

        # 将 DataFrame 转换为 bytes
        output_buffer = df.to_csv(index=False)
        output_data = output_buffer.encode('utf-8')

        # 通过存储适配层保存
        storage_info = await storage.save_preprocessing_output(
            dataset_id=dataset_id,
            task_id=task_id,
            data=output_data,
            filename="processed.csv"
        )

        logger.info(f"Preprocessed data saved via storage adapter: {storage_info}")

        return {
            "dataset_id": dataset_id,
            "status": "completed",
            "original_shape": original_shape,
            "processed_shape": df.shape,
            "summary": summary,
            # 存储信息
            "storage_type": storage_info["storage_type"],
            "object_key": storage_info["object_key"],
            "file_size": storage_info["file_size"],
            "output_file_name": "processed.csv",
            "full_path": storage_info.get("full_path")  # 仅 local 模式有
        }

    except Exception as e:
        logger.exception(f"Preprocessing failed for dataset {dataset_id}: {e}")
        return {
            "dataset_id": dataset_id,
            "status": "failed",
            "error": str(e)
        }


async def run_feature_engineering_task(ctx: Dict[str, Any], dataset_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行特征工程任务

    Args:
        ctx: 上下文
        dataset_id: 数据集ID
        config: 特征工程配置

    Returns:
        特征工程结果（包含存储信息）
    """
    import pandas as pd
    import numpy as np
    from app.storage import get_storage_service

    logger.info(f"Starting feature engineering task for dataset {dataset_id}")

    try:
        dataset_path = config.get('dataset_path')
        if not dataset_path:
            raise ValueError("dataset_path is required")

        df = pd.read_csv(dataset_path)
        original_columns = list(df.columns)
        new_features = []

        # 时间特征
        time_config = config.get('time_features', {})
        if time_config.get('enabled'):
            time_column = time_config.get('column')
            if time_column and time_column in df.columns:
                df[time_column] = pd.to_datetime(df[time_column])

                features = time_config.get('features', ['hour', 'dayofweek', 'month', 'is_weekend'])

                if 'hour' in features:
                    df[f'{time_column}_hour'] = df[time_column].dt.hour
                    new_features.append(f'{time_column}_hour')

                if 'dayofweek' in features:
                    df[f'{time_column}_dayofweek'] = df[time_column].dt.dayofweek
                    new_features.append(f'{time_column}_dayofweek')

                if 'month' in features:
                    df[f'{time_column}_month'] = df[time_column].dt.month
                    new_features.append(f'{time_column}_month')

                if 'is_weekend' in features:
                    df[f'{time_column}_is_weekend'] = df[time_column].dt.dayofweek.isin([5, 6]).astype(int)
                    new_features.append(f'{time_column}_is_weekend')

        # 滞后特征
        lag_config = config.get('lag_features', {})
        if lag_config.get('enabled'):
            columns = lag_config.get('columns', [])
            lags = lag_config.get('lags', [1, 2, 3])

            for col in columns:
                if col in df.columns:
                    for lag in lags:
                        feature_name = f'{col}_lag_{lag}'
                        df[feature_name] = df[col].shift(lag)
                        new_features.append(feature_name)

        # 滚动特征
        rolling_config = config.get('rolling_features', {})
        if rolling_config.get('enabled'):
            columns = rolling_config.get('columns', [])
            windows = rolling_config.get('windows', [3, 6, 24])

            for col in columns:
                if col in df.columns:
                    for window in windows:
                        df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window=window).mean()
                        df[f'{col}_rolling_min_{window}'] = df[col].rolling(window=window).min()
                        df[f'{col}_rolling_max_{window}'] = df[col].rolling(window=window).max()
                        df[f'{col}_rolling_std_{window}'] = df[col].rolling(window=window).std()
                        new_features.extend([
                            f'{col}_rolling_mean_{window}',
                            f'{col}_rolling_min_{window}',
                            f'{col}_rolling_max_{window}',
                            f'{col}_rolling_std_{window}'
                        ])

        # 通过存储适配层保存特征工程结果
        task_id = config.get('task_id', 'unknown')
        storage = get_storage_service()

        # 将 DataFrame 转换为 bytes
        output_buffer = df.to_csv(index=False)
        output_data = output_buffer.encode('utf-8')

        # 通过存储适配层保存
        storage_info = await storage.save_feature_engineering_output(
            dataset_id=dataset_id,
            task_id=task_id,
            data=output_data,
            filename="features.csv"
        )

        logger.info(f"Feature engineered data saved via storage adapter: {storage_info}")

        return {
            "dataset_id": dataset_id,
            "status": "completed",
            "original_columns": original_columns,
            "new_features": new_features,
            "total_columns": len(df.columns),
            # 存储信息
            "storage_type": storage_info["storage_type"],
            "object_key": storage_info["object_key"],
            "file_size": storage_info["file_size"],
            "output_file_name": "features.csv",
            "full_path": storage_info.get("full_path")  # 仅 local 模式有
        }

    except Exception as e:
        logger.exception(f"Feature engineering failed for dataset {dataset_id}: {e}")
        return {
            "dataset_id": dataset_id,
            "status": "failed",
            "error": str(e)
        }