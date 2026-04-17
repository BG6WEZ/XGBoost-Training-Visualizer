/**
 * API 客户端配置
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const TOKEN_KEY = 'auth_token'

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const token = localStorage.getItem(TOKEN_KEY)

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
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

  uploadFile: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/api/datasets/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP error ${response.status}`)
    }

    return response.json()
  },

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

  preprocess: (id: string, config: PreprocessingRequest) =>
    apiClient<TaskResponse>(`/api/datasets/${id}/preprocess`, {
      method: 'POST',
      body: JSON.stringify({ dataset_id: id, config }),
    }),

  featureEngineering: (id: string, config: FeatureEngineeringRequest) =>
    apiClient<TaskResponse>(`/api/datasets/${id}/feature-engineering`, {
      method: 'POST',
      body: JSON.stringify({ dataset_id: id, config }),
    }),

  getTask: (taskId: string) =>
    apiClient<TaskStatus>(`/api/datasets/tasks/${taskId}`),

  listTasks: (datasetId: string) =>
    apiClient<TaskListResponse[]>(`/api/datasets/${datasetId}/tasks`),

  getQualityScore: (datasetId: string) =>
    apiClient<QualityScoreResponse>(`/api/datasets/${datasetId}/quality-score`),
}

// 实验相关 API
export const experimentsApi = {
  list: (params?: ExperimentFilterParams) => {
    const queryParams = new URLSearchParams()
    if (params?.status) queryParams.append('status', params.status)
    if (params?.tags) queryParams.append('tags', params.tags)
    if (params?.tag_match_mode) queryParams.append('tag_match_mode', params.tag_match_mode)
    if (params?.created_after) queryParams.append('created_after', params.created_after)
    if (params?.created_before) queryParams.append('created_before', params.created_before)
    if (params?.name_contains) queryParams.append('name_contains', params.name_contains)
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
    
    const queryString = queryParams.toString()
    return apiClient<ExperimentListResponse[]>(`/api/experiments/${queryString ? '?' + queryString : ''}`)
  },

  get: (id: string) =>
    apiClient<ExperimentResponse>(`/api/experiments/${id}`),

  create: (data: ExperimentCreateRequest) =>
    apiClient<ExperimentResponse>('/api/experiments/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<ExperimentCreateRequest>) =>
    apiClient<ExperimentResponse>(`/api/experiments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiClient<{ status: string; id: string }>(`/api/experiments/${id}`, {
      method: 'DELETE',
    }),

  start: (id: string) =>
    apiClient<{ status: string; experiment_id: string; message: string; queue_position: number }>(
      `/api/experiments/${id}/start`,
      { method: 'POST' }
    ),

  stop: (id: string) =>
    apiClient<{ status: string; experiment_id: string; removed_from_queue: boolean }>(
      `/api/experiments/${id}/stop`,
      { method: 'POST' }
    ),

  getParamTemplates: () =>
    apiClient<ParamTemplatesResponse>('/api/experiments/param-templates'),

  getQueueStats: () =>
    apiClient<QueueStatsResponse>('/api/experiments/queue/stats'),

  getWithQueueInfo: (status?: string) => {
    const queryParams = status ? `?status=${status}` : ''
    return apiClient<ExperimentWithQueueResponse[]>(`/api/experiments/with-queue-info${queryParams}`)
  },
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

  getPredictionAnalysis: (experimentId: string) =>
    apiClient<PredictionAnalysisResponse>(`/api/results/${experimentId}/prediction-analysis`),

  compare: (experimentIds: string[]) =>
    apiClient<CompareResponse>('/api/results/compare', {
      method: 'POST',
      body: JSON.stringify(experimentIds),
    }),

  downloadModel: (experimentId: string) =>
    `${API_BASE_URL}/api/results/${experimentId}/download-model`,
}

// 任务相关类型定义
export interface PreprocessingRequest {
  missing_value_strategy?: 'forward_fill' | 'mean_fill' | 'drop_rows'
  encoding_strategy?: 'one_hot' | 'label_encoding'
  target_columns?: string[]
  time_column?: string
  entity_column?: string
}

export interface FeatureEngineeringRequest {
  time_features: {
    enabled: boolean
    features: ('hour' | 'dayofweek' | 'month' | 'is_weekend')[]
    column: string
  }
  lag_features: {
    enabled: boolean
    lags: number[]
    columns: string[]
  }
  rolling_features: {
    enabled: boolean
    windows: number[]
    columns: string[]
    functions: ('mean' | 'std' | 'min' | 'max' | 'sum')[]
  }
}

export interface TaskResponse {
  task_id: string
  status: string
}

export interface TaskStatus {
  id: string
  task_type: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  result?: Record<string, unknown>
  error_message?: string
  created_at: string
  updated_at: string
}

export interface TaskListResponse {
  id: string
  task_type: string
  status: string
  created_at: string
  updated_at: string
}

export interface QualityDimensionScores {
  completeness: number
  accuracy: number
  consistency: number
  distribution: number
}

export interface QualityScoreResponse {
  dataset_id: string
  overall_score: number
  dimension_scores: QualityDimensionScores
  errors: Array<{
    code: string
    message: string
    severity: string
    details?: Record<string, unknown>
  }>
  warnings: Array<{
    code: string
    message: string
    severity: string
    details?: Record<string, unknown>
  }>
  recommendations: string[]
  stats: Record<string, unknown>
  evaluated_at: string
  weights: {
    completeness: number
    accuracy: number
    consistency: number
    distribution: number
  }
}

// 类型定义// 类型定义
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

export interface UploadColumnInfo {
  name: string
  dtype: string
  is_numeric: boolean
  is_datetime: boolean
}

export interface UploadResponse {
  file_path: string
  file_name: string
  file_size: number
  row_count?: number
  column_count?: number
  columns_info?: UploadColumnInfo[]
  message?: string
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
  tags?: string[]
  status: string
  created_at: string
  queue_position?: number
}

export interface ExperimentFilterParams {
  status?: string
  tags?: string
  tag_match_mode?: 'any' | 'all'
  created_after?: string
  created_before?: string
  name_contains?: string
  skip?: number
  limit?: number
}

export interface ExperimentResponse {
  id: string
  name: string
  description?: string
  dataset_id: string
  subset_id?: string
  config: ExperimentConfig
  tags?: string[]
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
    early_stopping_rounds?: number
  }
  tags?: string[]
}

export interface TrainingStatus {
  experiment_id: string
  status: string
  progress: number
  started_at?: string
  finished_at?: string
  error_message?: string
}

export interface MetricAvailability {
  available: boolean
  reason?: string
}

export interface BenchmarkMetrics {
  rmse?: number
  mae?: number
  mape?: number
  r2?: number
  rmse_availability?: MetricAvailability
  mae_availability?: MetricAvailability
  mape_availability?: MetricAvailability
  r2_availability?: MetricAvailability
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
  benchmark?: BenchmarkMetrics
  benchmark_mode: string
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

export interface ParamTemplateItem {
  learning_rate: number
  max_depth: number
  n_estimators: number
  subsample: number
  colsample_bytree: number
  early_stopping_rounds: number
  description: string
}

export interface ParamTemplatesResponse {
  templates: {
    conservative: ParamTemplateItem
    balanced: ParamTemplateItem
    aggressive: ParamTemplateItem
  }
}

export interface QueueStatsResponse {
  running_count: number
  queued_count: number
  max_concurrency: number
  available_slots: number
  running_experiments: string[]
  queue_positions: Record<string, number>
}

export interface ExperimentWithQueueResponse {
  id: string
  name: string
  description?: string
  dataset_id: string
  status: string
  created_at: string
  queue_position?: number
}

// ========== 预测分析（P1-T10）==========

export interface ResidualSummary {
  mean: number
  std: number
  min: number
  max: number
  p50: number
  p95: number
}

export interface PredictionScatterPoint {
  actual: number
  predicted: number
}

export interface ResidualHistogramBin {
  bin_start: number
  bin_end: number
  count: number
}

export interface ResidualScatterPoint {
  predicted: number
  residual: number
}

export interface PredictionAnalysisData {
  sample_count: number
  actual_values: number[]
  predicted_values: number[]
  residual_values: number[]
  residual_summary: ResidualSummary
  prediction_scatter_points: PredictionScatterPoint[]
  residual_histogram_bins: ResidualHistogramBin[]
  residual_scatter_points: ResidualScatterPoint[]
}

export interface PredictionAnalysisResponse {
  experiment_id: string
  analysis_available: boolean
  analysis_unavailable_reason?: string
  data?: PredictionAnalysisData
  residual_definition: string
}

// ========== 模型版本管理（P1-T13）==========

export interface ModelVersionResponse {
  id: string
  experiment_id: string
  version_number: string
  config_snapshot: Record<string, unknown>
  metrics_snapshot: Record<string, unknown>
  tags: string[]
  is_active: boolean
  source_model_id?: string
  created_at: string
}

export interface ModelVersionListResponse {
  id: string
  experiment_id: string
  version_number: string
  metrics_snapshot: Record<string, unknown>
  tags: string[]
  is_active: boolean
  created_at: string
}

export interface ConfigDiff {
  param_name: string
  values: Record<string, unknown>
}

export interface MetricsDiff {
  metric_name: string
  values: Record<string, number>
  change?: Record<string, number>
}

export interface VersionCompareResponse {
  versions: ModelVersionResponse[]
  config_diffs: ConfigDiff[]
  metrics_diffs: MetricsDiff[]
}

export interface VersionRollbackResponse {
  success: boolean
  previous_active_version_id?: string
  new_active_version_id: string
  message: string
}

export const versionsApi = {
  list: (experimentId: string) =>
    apiClient<ModelVersionListResponse[]>(`/api/experiments/${experimentId}/versions`),

  get: (versionId: string) =>
    apiClient<ModelVersionResponse>(`/api/versions/${versionId}`),

  create: (data: { experiment_id: string; tags?: string[] }) =>
    apiClient<ModelVersionResponse>('/api/versions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  compare: (versionIds: string[]) =>
    apiClient<VersionCompareResponse>('/api/versions/compare', {
      method: 'POST',
      body: JSON.stringify({ version_ids: versionIds }),
    }),

  rollback: (versionId: string) =>
    apiClient<VersionRollbackResponse>(`/api/versions/${versionId}/rollback`, {
      method: 'POST',
    }),

  updateTags: (versionId: string, tags: string[]) =>
    apiClient<ModelVersionResponse>(`/api/versions/${versionId}/tags`, {
      method: 'PATCH',
      body: JSON.stringify({ tags }),
    }),

  getActive: (experimentId: string) =>
    apiClient<ModelVersionResponse | null>(`/api/experiments/${experimentId}/versions/active`),
}

// ========== 导出功能（P1-T14）==========

export const exportApi = {
  configJson: (experimentId: string) =>
    `${API_BASE_URL}/api/experiments/${experimentId}/export/config/json`,

  configYaml: (experimentId: string) =>
    `${API_BASE_URL}/api/experiments/${experimentId}/export/config/yaml`,

  reportHtml: (experimentId: string) =>
    `${API_BASE_URL}/api/experiments/${experimentId}/export/report/html`,

  reportPdf: (experimentId: string) =>
    `${API_BASE_URL}/api/experiments/${experimentId}/export/report/pdf`,
}

// ========== 认证功能（P1-T15）==========

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

export interface UserResponse {
  id: string
  username: string
  role: string
  status: string
  must_change_password?: boolean
  created_at?: string
  last_login_at?: string
}

export interface UserCreateRequest {
  username: string
  password: string
  role?: string
}

export interface UserUpdateRequest {
  status?: string
  role?: string
}

export interface PasswordChangeRequest {
  old_password: string
  new_password: string
}

export interface PasswordResetRequest {
  new_password: string
}

export interface UserListResponse {
  users: UserResponse[]
  total: number
}

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  logout: () =>
    apiClient<{ message: string }>('/api/auth/logout', {
      method: 'POST',
    }),

  getMe: () =>
    apiClient<UserResponse>('/api/auth/me'),

  changePassword: (data: PasswordChangeRequest) =>
    apiClient<{ message: string }>('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}

export const usersApi = {
  list: () =>
    apiClient<UserListResponse>('/api/admin/users'),

  get: (userId: string) =>
    apiClient<UserResponse>(`/api/admin/users/${userId}`),

  create: (data: UserCreateRequest) =>
    apiClient<UserResponse>('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (userId: string, data: UserUpdateRequest) =>
    apiClient<UserResponse>(`/api/admin/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  resetPassword: (userId: string, data: PasswordResetRequest) =>
    apiClient<{ message: string }>(`/api/admin/users/${userId}/reset-password`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  generatePassword: () =>
    apiClient<{ password: string }>('/api/admin/users/generate-password', {
      method: 'POST',
    }),
}