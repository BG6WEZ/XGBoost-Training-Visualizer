export interface TrainingStatus {
  experimentId: string;
  status: ExperimentStatus;
  progress: number;
  currentIteration: number;
  totalIterations: number;
  metrics: Record<string, number>;
  startTime?: Date;
  estimatedEndTime?: Date;
  queuePosition?: number;
  workerId?: string;
}

export type ExperimentStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface TrainingQueue {
  active: ActiveTraining[];
  queued: QueuedTraining[];
  maxConcurrent: number;
  totalJobs: number;
}

export interface ActiveTraining {
  experimentId: string;
  experimentName: string;
  workerId: string;
  status: 'running' | 'paused';
  progress: number;
  startTime: Date;
  currentIteration: number;
  totalIterations: number;
  metrics: Record<string, number>;
}

export interface QueuedTraining {
  experimentId: string;
  experimentName: string;
  position: number;
  queueTime: Date;
  estimatedStartTime?: Date;
}

export interface TrainingMetric {
  timestamp: Date;
  iteration: number;
  metrics: {
    train?: Record<string, number>;
    val?: Record<string, number>;
  };
}

export interface TrainingLog {
  timestamp: Date;
  level: 'info' | 'warn' | 'error';
  message: string;
  details?: string;
  iteration?: number;
}

export interface WorkerInfo {
  workerId: string;
  status: 'idle' | 'busy' | 'starting' | 'stopping' | 'error';
  currentTask?: string;
  lastHeartbeat: Date;
  totalTrainings: number;
  successfulTrainings: number;
  failedTrainings: number;
}

export interface AutoTuningConfig {
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

export interface AutoTuningResult {
  tuningId: string;
  experimentId: string;
  bestParameters: Record<string, any>;
  bestMetric: number;
  trials: TuningTrial[];
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
}

export interface TuningTrial {
  trialId: string;
  parameters: Record<string, any>;
  metrics: Record<string, number>;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
}

export interface TrainingCallback {
  onProgress?: (progress: number, iteration: number) => void;
  onMetric?: (metrics: Record<string, number>, iteration: number) => void;
  onLog?: (log: TrainingLog) => void;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

export interface GPUConfig {
  enabled: boolean;
  devices?: number[];
  memoryLimit?: number;
  useMultiGPU?: boolean;
  gpuId?: number;
}

export interface ModelVersion {
  id: string;
  modelId: string;
  version: number;
  name: string;
  description?: string;
  config: any;
  metrics: Record<string, number>;
  createdAt: Date;
  createdBy: string;
  tags: string[];
  isActive: boolean;
  filePath: string;
  fileSize: number;
}

export interface ModelComparison {
  models: ModelVersion[];
  metrics: string[];
  featureImportance: boolean;
  predictions: boolean;
  parameters: boolean;
}