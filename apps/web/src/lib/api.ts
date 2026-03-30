/**
 * API 客户端配置
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }

  return response.json()
}

// 数据资产相关 API
export const assetsApi = {
  scan: () => apiClient<{ total_assets: number; assets: ScannedAsset[] }>('/api/assets/scan'),

  register: (asset: RegisterAssetRequest) =>
    apiClient<RegisteredDataset>('/api/assets/register', {
      method: 'POST',
      body: JSON.stringify(asset),
    }),

  profile: (filePath: string) =>
    apiClient<FileProfile>(`/api/assets/profile?file_path=${encodeURIComponent(filePath)}`),
}

// 数据集相关 API
export const datasetsApi = {
  list: () => apiClient<DatasetListResponse[]>('/api/datasets/'),

  get: (id: string) => apiClient<DatasetResponse>(`/api/datasets/${id}`),

  create: (data: DatasetCreateRequest) =>
    apiClient<DatasetResponse>('/api/datasets/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<DatasetCreateRequest>) =>
    apiClient<DatasetResponse>(`/api/datasets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiClient<{ status: string }>(`/api/datasets/${id}`, { method: 'DELETE' }),

  preview: (id: string, rows = 10) =>
    apiClient<DatasetPreview>(`/api/datasets/${id}/preview?rows=${rows}`),

  split: (id: string, config: SplitConfig) =>
    apiClient<SplitResponse>(`/api/datasets/${id}/split`, {
      method: 'POST',
      body: JSON.stringify(config),
    }),
}

// 实验相关 API
export const experimentsApi = {
  list: (status?: string) =>
    apiClient<ExperimentListResponse[]>(`/api/experiments/${status ? `?status=${status}` : ''}`),

  get: (id: string) => apiClient<ExperimentResponse>(`/api/experiments/${id}`),

  create: (data: ExperimentCreateRequest) =>
    apiClient<ExperimentResponse>('/api/experiments/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  start: (id: string) =>
    apiClient<{ status: string; experiment_id: string }>(`/api/experiments/${id}/start`, {
      method: 'POST',
    }),

  stop: (id: string) =>
    apiClient<{ status: string }>(`/api/experiments/${id}/stop`, { method: 'POST' }),

  delete: (id: string) =>
    apiClient<{ status: string }>(`/api/experiments/${id}`, { method: 'DELETE' }),
}

// 训练相关 API
export const trainingApi = {
  getStatus: (experimentId: string) =>
    apiClient<TrainingStatus>(`/api/training/${experimentId}/status`),
}

// 结果相关 API
export const resultsApi = {
  get: (experimentId: string) =>
    apiClient<ExperimentResult>(`/api/results/${experimentId}`),

  getFeatureImportance: (experimentId: string, topN = 20) =>
    apiClient<FeatureImportanceResponse>(`/api/results/${experimentId}/feature-importance?top_n=${topN}`),

  getMetricsHistory: (experimentId: string) =>
    apiClient<MetricsHistoryResponse>(`/api/results/${experimentId}/metrics-history`),

  compare: (experimentIds: string[]) =>
    apiClient<CompareResponse>('/api/results/compare', {
      method: 'POST',
      body: JSON.stringify(experimentIds),
    }),

  downloadModel: (experimentId: string) =>
    `${API_BASE_URL}/api/results/${experimentId}/download-model`,
}

// 类型定义
export interface ScannedAsset {
  name: string
  source_type: string
  source_name: string
  path: string
  path_type: string
  is_raw: boolean
  description?: string
  member_files: Array<{
    file_path: string
    file_name: string
    role: string
  }>
  registered: boolean
  registered_dataset_id?: string
}

export interface RegisterAssetRequest {
  asset_name: string
  source_type: string
  path: string
  path_type: string
  is_raw: boolean
  description?: string
  member_files: Array<{
    file_path: string
    file_name: string
    role: string
  }>
  auto_detect_columns?: boolean
}

export interface FileProfile {
  file_path: string
  file_name: string
  row_count: number
  column_count: number
  columns_info: ColumnInfo[]
  time_candidates: string[]
  target_candidates: string[]
  entity_candidates: string[]
  quality_summary: {
    total_cells: number
    missing_cells: number
    missing_rate: number
  }
}

export interface ColumnInfo {
  name: string
  dtype: string
  missing_count: number
  missing_rate: number
  unique_count: number
  is_numeric: boolean
  is_datetime: boolean
  is_categorical: boolean
  is_time_candidate: boolean
  is_target_candidate: boolean
  is_entity_candidate: boolean
  min?: number
  max?: number
  mean?: number
  std?: number
}

export interface RegisteredDataset {
  id: string
  name: string
  time_column?: string
  entity_column?: string
  target_column?: string
  total_row_count: number
  total_column_count: number
  file_count: number
  status: string
}

export interface DatasetListResponse {
  id: string
  name: string
  description?: string
  total_row_count: number
  total_column_count: number
  total_file_size: number
  file_count: number
  created_at: string
}

export interface DatasetResponse {
  id: string
  name: string
  description?: string
  time_column?: string
  entity_column?: string
  target_column?: string
  total_row_count: number
  total_column_count: number
  total_file_size: number
  files: Array<{
    id: string
    file_path: string
    file_name: string
    role: string
    row_count: number
    column_count: number
    file_size: number
    columns_info?: ColumnInfo[]
  }>
  created_at: string
  updated_at: string
}

export interface DatasetCreateRequest {
  name: string
  description?: string
  files: Array<{
    file_path: string
    file_name: string
    role: string
    row_count?: number
    column_count?: number
    file_size?: number
  }>
  time_column?: string
  entity_column?: string
  target_column?: string
}

export interface DatasetPreview {
  file_id: string
  file_name: string
  columns: string[]
  data: Record<string, unknown>[]
  total_rows: number
  preview_rows: number
}

export interface SplitConfig {
  split_method?: 'random' | 'time'
  test_size?: number
  random_seed?: number
  time_column?: string
  train_end_date?: string
  val_start_date?: string
  val_end_date?: string
  test_start_date?: string
}

export interface SplitResponse {
  dataset_id: string
  split_method: string
  subsets: Array<{
    id: string
    name: string
    purpose: string
    row_count: number
    file_path: string
  }>
  split_config: Record<string, unknown>
}

export interface XGBoostParams {
  n_estimators?: number
  max_depth?: number
  learning_rate?: number
  [key: string]: unknown
}

export interface ExperimentConfig {
  task_type?: string
  test_size?: number
  xgboost_params?: XGBoostParams
  [key: string]: unknown
}

export interface ExperimentListResponse {
  id: string
  name: string
  description?: string
  dataset_id: string
  status: string
  created_at: string
}

export interface ExperimentResponse {
  id: string
  name: string
  description?: string
  dataset_id: string
  subset_id?: string
  config: ExperimentConfig
  status: string
  error_message?: string
  created_at: string
  updated_at: string
  started_at?: string
  finished_at?: string
}

export interface ExperimentCreateRequest {
  name: string
  description?: string
  dataset_id: string
  subset_id?: string
  config: {
    task_type: string
    test_size?: number
    xgboost_params: Record<string, unknown>
  }
}

export interface TrainingStatus {
  experiment_id: string
  status: string
  progress: number
  started_at?: string
  finished_at?: string
  error_message?: string
}

export interface ExperimentResult {
  experiment_id: string
  experiment_name: string
  status: string
  metrics: {
    train_rmse?: number
    val_rmse?: number
    r2?: number
    mae?: number
  }
  feature_importance: Array<{
    feature_name: string
    importance: number
    rank: number
  }>
  model?: {
    id: string
    format: string
    file_size: number
    storage_type: string
    object_key: string
  }
  training_time_seconds?: number
}

export interface FeatureImportanceResponse {
  experiment_id: string
  total_features: number
  total_importance: number
  features: Array<{
    feature_name: string
    importance: number
    importance_pct: number
    rank: number
  }>
}

export interface MetricsHistoryResponse {
  experiment_id: string
  iterations: number[]
  train_loss: number[]
  val_loss: number[]
  train_metric: number[]
  val_metric: number[]
}

export interface CompareResponse {
  experiments: Array<{
    experiment_id: string
    name: string
    status: string
    config: ExperimentConfig
    metrics: {
      train_rmse?: number
      val_rmse?: number
    }
  }>
  best_val_rmse?: number
  comparison: {
    best_experiment?: string
  }
}