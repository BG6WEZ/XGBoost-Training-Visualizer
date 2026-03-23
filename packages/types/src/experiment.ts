export interface Experiment {
  id: string;
  name: string;
  description?: string;
  datasetId: string;
  subsetId?: string;
  config: TrainingConfig;
  status: ExperimentStatus;
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
  startedAt?: Date;
  finishedAt?: Date;
}

export type ExperimentStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

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

export interface ExperimentMetric {
  experimentId: string;
  timestamp: Date;
  iteration: number;
  metrics: Record<string, number>;
}

export interface ExperimentResult {
  experimentId: string;
  metrics: {
    train: Record<string, number>;
    test: Record<string, number>;
  };
  featureImportance: FeatureImportance[];
  predictions: {
    actual: number[];
    predicted: number[];
  };
  trainingDuration: number;
  modelSize: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ExperimentLog {
  experimentId: string;
  timestamp: Date;
  level: 'info' | 'warn' | 'error';
  message: string;
  details?: string;
}