// ============================================
// 枚举类型
// ============================================

export type ExperimentStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled'

export type FileRole = 'primary' | 'supplementary' | 'metadata'

// ============================================
// 数据集领域
// ============================================

// 数据集文件成员
export interface DatasetFile {
  id: string
  file_path: string
  file_name: string
  role: FileRole
  row_count: number
  column_count: number
  file_size: number
  columns_info?: ColumnInfo[]
  created_at: string
}

// 逻辑数据集（支持多文件）
export interface Dataset {
  id: string
  name: string
  description?: string
  time_column?: string
  entity_column?: string
  target_column?: string
  total_row_count: number
  total_column_count: number
  total_file_size: number
  files: DatasetFile[]
  created_at: string
  updated_at: string
}

// 数据集列表项
export interface DatasetListItem {
  id: string
  name: string
  description?: string
  total_row_count: number
  total_column_count: number
  total_file_size: number
  file_count: number
  created_at: string
}

// 数据集预览
export interface DatasetPreview {
  file_id: string
  file_name: string
  columns: string[]
  data: Record<string, unknown>[]
  total_rows: number
  preview_rows: number
}

// 列信息
export interface ColumnInfo {
  name: string
  type: 'string' | 'number' | 'datetime' | 'boolean'
  nullable: boolean
  unique_count: number
  missing_count: number
}

// ============================================
// 实验与训练
// ============================================

// XGBoost 参数
export interface XGBoostParams {
  learning_rate: number
  max_depth: number
  n_estimators: number
  subsample: number
  colsample_bytree: number
  gamma: number
  alpha: number
  lambda: number
  min_child_weight: number
}

// 训练配置
export interface TrainingConfig {
  task_type: 'regression' | 'classification'
  test_size: number
  random_seed: number
  xgboost_params: XGBoostParams
  early_stopping_rounds?: number
}

// 实验
export interface Experiment {
  id: string
  name: string
  description?: string
  dataset_id: string
  subset_id?: string
  config: TrainingConfig
  status: ExperimentStatus
  error_message?: string
  created_at: string
  updated_at: string
  started_at?: string
  finished_at?: string
}

// 训练指标
export interface TrainingMetric {
  iteration: number
  train_loss: number
  val_loss: number
  train_metric?: number
  val_metric?: number
  recorded_at: string
}

// 训练日志
export interface TrainingLog {
  id: string
  level: string
  message: string
  timestamp: string
}

// 特征重要性
export interface FeatureImportance {
  feature_name: string
  importance: number
  rank: number
}

// 模型
export interface Model {
  id: string
  file_path: string
  format: string
  file_size?: number
  metrics?: Record<string, number>
  created_at: string
}

// 训练结果
export interface TrainingResult {
  experiment_id: string
  experiment_name: string
  status: string
  metrics: {
    train_rmse: number
    val_rmse: number
    train_mae?: number
    val_mae?: number
    r2?: number
  }
  feature_importance: FeatureImportance[]
  model?: Model
  training_time_seconds?: number
}

// ============================================
// API 响应类型
// ============================================

// API 响应包装
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}