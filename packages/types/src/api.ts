export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface ErrorResponse {
  error: string;
  code: number;
  message: string;
  details?: any;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
  expiresAt: Date;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
  name: string;
  createdAt: Date;
  lastLoginAt?: Date;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  name: string;
  role: 'admin' | 'user' | 'guest';
}

export interface UpdateUserRequest {
  email?: string;
  name?: string;
  role?: 'admin' | 'user' | 'guest';
  password?: string;
}

export interface DatasetCreateRequest {
  name: string;
  fileType: 'csv' | 'excel' | 'json';
  delimiter?: string;
  encoding?: string;
}

export interface DatasetUploadRequest {
  uploadId: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  totalChunks: number;
  fileHash: string;
}

export interface DatasetUploadChunkRequest {
  uploadId: string;
  chunkIndex: number;
  totalChunks: number;
  chunkSize: number;
  totalSize: number;
  fileHash: string;
  data: Buffer;
}

export interface DatasetSplitRequest {
  name: string;
  splitConfig: SplitConfig;
}

export interface SplitConfig {
  type: 'time' | 'space' | 'mixed';
  timeColumn?: string;
  idColumn?: string;
  splits: SplitDefinition[];
  timeRange?: {
    start: string;
    end: string;
  };
  spaceGroups?: SpaceGroup[];
}

export interface SplitDefinition {
  name: string;
  purpose: 'train' | 'test' | 'compare' | 'transfer_source' | 'transfer_target';
  timeRange?: {
    start: string;
    end: string;
  };
  spaceValues?: string[];
}

export interface SpaceGroup {
  name: string;
  values: string[];
  purpose: 'train' | 'test' | 'compare' | 'transfer_source' | 'transfer_target';
}

export interface ExperimentCreateRequest {
  name: string;
  description?: string;
  datasetId: string;
  subsetId?: string;
  config: TrainingConfig;
  tags?: string[];
}

export interface TrainingConfig {
  taskType: 'regression' | 'classification';
  testSize: number;
  randomSeed: number;
  xgboostParams: XGBoostParams;
  earlyStopping?: EarlyStoppingConfig;
  featureConfig?: FeatureConfig;
  transferLearning?: TransferLearningConfig;
}

export interface XGBoostParams {
  learningRate: number;
  maxDepth: number;
  nEstimators: number;
  subsample: number;
  colsampleBytree: number;
  gamma: number;
  alpha: number;
  lambda: number;
  minChildWeight: number;
  treeMethod?: string;
  booster?: string;
  objective?: string;
  evalMetric?: string;
}

export interface EarlyStoppingConfig {
  rounds: number;
  metric: string;
  minDelta?: number;
}

export interface FeatureConfig {
  selectedFeatures?: string[];
  timeFeatures?: TimeFeatureConfig;
  lagFeatures?: LagFeatureConfig[];
  rollingFeatures?: RollingFeatureConfig[];
}

export interface TimeFeatureConfig {
  enabled: boolean;
  columns: string[];
  features: {
    hour: boolean;
    dayOfWeek: boolean;
    dayOfMonth: boolean;
    month: boolean;
    year: boolean;
  };
}

export interface LagFeatureConfig {
  column: string;
  lags: number[];
}

export interface RollingFeatureConfig {
  column: string;
  windows: number[];
  functions: ('mean' | 'sum' | 'min' | 'max' | 'std')[];
}

export interface TransferLearningConfig {
  sourceDatasetId: string;
  targetDatasetId: string;
  strategy: 'fine-tuning' | 'feature-extraction' | 'domain-adaptation';
  parameters: Record<string, any>;
}

export interface AutoTuningRequest {
  experimentId: string;
  parameterSpace: ParameterSpace;
  strategy: 'grid' | 'random' | 'bayesian';
  maxTrials: number;
  maxConcurrent: number;
  metric: string;
  objective: 'minimize' | 'maximize';
  earlyStoppingRounds?: number;
  timeoutMinutes?: number;
}

export interface ParameterSpace {
  learningRate: {
    type: 'float';
    min: number;
    max: number;
    step?: number;
  };
  maxDepth: {
    type: 'int';
    min: number;
    max: number;
    step?: number;
  };
  nEstimators: {
    type: 'int';
    min: number;
    max: number;
    step?: number;
  };
  subsample: {
    type: 'float';
    min: number;
    max: number;
    step?: number;
  };
  colsampleBytree: {
    type: 'float';
    min: number;
    max: number;
    step?: number;
  };
  [key: string]: {
    type: 'float' | 'int' | 'categorical';
    min?: number;
    max?: number;
    step?: number;
    values?: any[];
  };
}

export interface ExperimentCompareRequest {
  experimentIds: string[];
  metrics: string[];
  compareFeatures: boolean;
  compareParameters: boolean;
  comparePredictions: boolean;
}

export interface TransferLearningRequest {
  sourceDatasetId: string;
  targetDatasetId: string;
  strategy: 'fine-tuning' | 'feature-extraction' | 'domain-adaptation';
  parameters: Record<string, any>;
  name: string;
  description?: string;
}

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: Date;
}

export interface TrainingWebSocketMessage {
  type: 'progress' | 'metric' | 'log' | 'completed' | 'error';
  payload: any;
  experimentId: string;
  timestamp: Date;
}