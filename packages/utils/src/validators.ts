import { z } from 'zod';

export const datasetCreateSchema = z.object({
  name: z.string().min(1, '数据集名称不能为空').max(100, '数据集名称不能超过100个字符'),
  fileType: z.enum(['csv', 'excel', 'json']),
  delimiter: z.string().optional(),
  encoding: z.string().optional(),
});

export const experimentCreateSchema = z.object({
  name: z.string().min(1, '实验名称不能为空').max(100, '实验名称不能超过100个字符'),
  description: z.string().optional(),
  datasetId: z.string().min(1, '数据集ID不能为空'),
  subsetId: z.string().optional(),
  config: z.object({
    taskType: z.enum(['regression', 'classification']),
    testSize: z.number().min(0.1, '测试集比例不能小于0.1').max(0.9, '测试集比例不能大于0.9'),
    randomSeed: z.number().min(0),
    xgboostParams: z.object({
      learningRate: z.number().min(0.001, '学习率不能小于0.001').max(1, '学习率不能大于1'),
      maxDepth: z.number().min(1, '最大深度不能小于1').max(30, '最大深度不能大于30'),
      nEstimators: z.number().min(1, ' estimators 数量不能小于1').max(10000, ' estimators 数量不能大于10000'),
      subsample: z.number().min(0.1, '子样本比例不能小于0.1').max(1, '子样本比例不能大于1'),
      colsampleBytree: z.number().min(0.1, '特征采样比例不能小于0.1').max(1, '特征采样比例不能大于1'),
      gamma: z.number().min(0, 'gamma不能小于0'),
      alpha: z.number().min(0, 'alpha不能小于0'),
      lambda: z.number().min(0, 'lambda不能小于0'),
      minChildWeight: z.number().min(0, '最小子节点权重不能小于0'),
      treeMethod: z.string().optional(),
      booster: z.string().optional(),
      objective: z.string().optional(),
      evalMetric: z.string().optional(),
    }),
    earlyStopping: z.object({
      rounds: z.number().min(1, '早停轮数不能小于1'),
      metric: z.string().min(1, '早停指标不能为空'),
      minDelta: z.number().optional(),
    }).optional(),
    featureConfig: z.object({
      selectedFeatures: z.array(z.string()).optional(),
      timeFeatures: z.object({
        enabled: z.boolean(),
        columns: z.array(z.string()),
        features: z.object({
          hour: z.boolean(),
          dayOfWeek: z.boolean(),
          dayOfMonth: z.boolean(),
          month: z.boolean(),
          year: z.boolean(),
        }),
      }).optional(),
      lagFeatures: z.array(z.object({
        column: z.string().min(1),
        lags: z.array(z.number().min(1)),
      })).optional(),
      rollingFeatures: z.array(z.object({
        column: z.string().min(1),
        windows: z.array(z.number().min(1)),
        functions: z.array(z.enum(['mean', 'sum', 'min', 'max', 'std'])),
      })).optional(),
    }).optional(),
    transferLearning: z.object({
      sourceDatasetId: z.string().min(1),
      targetDatasetId: z.string().min(1),
      strategy: z.enum(['fine-tuning', 'feature-extraction', 'domain-adaptation']),
      parameters: z.record(z.string(), z.any()),
    }).optional(),
  }),
  tags: z.array(z.string()).optional(),
});

export const datasetSplitSchema = z.object({
  name: z.string().min(1, '子数据集名称不能为空').max(100, '子数据集名称不能超过100个字符'),
  splitConfig: z.object({
    type: z.enum(['time', 'space', 'mixed']),
    timeColumn: z.string().optional(),
    idColumn: z.string().optional(),
    splits: z.array(z.object({
      name: z.string().min(1),
      purpose: z.enum(['train', 'test', 'compare', 'transfer_source', 'transfer_target']),
      timeRange: z.object({
        start: z.string().min(1),
        end: z.string().min(1),
      }).optional(),
      spaceValues: z.array(z.string()).optional(),
    })),
    timeRange: z.object({
      start: z.string().min(1),
      end: z.string().min(1),
    }).optional(),
    spaceGroups: z.array(z.object({
      name: z.string().min(1),
      values: z.array(z.string()),
      purpose: z.enum(['train', 'test', 'compare', 'transfer_source', 'transfer_target']),
    })).optional(),
  }),
});

export const autoTuningSchema = z.object({
  experimentId: z.string().min(1),
  parameterSpace: z.object({
    learningRate: z.object({
      type: z.literal('float'),
      min: z.number().min(0.001),
      max: z.number().max(1),
      step: z.number().optional(),
    }),
    maxDepth: z.object({
      type: z.literal('int'),
      min: z.number().min(1),
      max: z.number().max(30),
      step: z.number().optional(),
    }),
    nEstimators: z.object({
      type: z.literal('int'),
      min: z.number().min(1),
      max: z.number().max(10000),
      step: z.number().optional(),
    }),
    subsample: z.object({
      type: z.literal('float'),
      min: z.number().min(0.1),
      max: z.number().max(1),
      step: z.number().optional(),
    }),
    colsampleBytree: z.object({
      type: z.literal('float'),
      min: z.number().min(0.1),
      max: z.number().max(1),
      step: z.number().optional(),
    }),
  }),
  strategy: z.enum(['grid', 'random', 'bayesian']),
  maxTrials: z.number().min(1).max(100),
  maxConcurrent: z.number().min(1).max(10),
  metric: z.string().min(1),
  objective: z.enum(['minimize', 'maximize']),
  earlyStoppingRounds: z.number().optional(),
  timeoutMinutes: z.number().optional(),
});

export const transferLearningSchema = z.object({
  sourceDatasetId: z.string().min(1),
  targetDatasetId: z.string().min(1),
  strategy: z.enum(['fine-tuning', 'feature-extraction', 'domain-adaptation']),
  parameters: z.record(z.string(), z.any()),
  name: z.string().min(1).max(100),
  description: z.string().optional(),
});

export const loginSchema = z.object({
  username: z.string().min(1, '用户名不能为空'),
  password: z.string().min(6, '密码不能少于6个字符'),
});

export const createUserSchema = z.object({
  username: z.string().min(3, '用户名不能少于3个字符').max(50, '用户名不能超过50个字符'),
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(6, '密码不能少于6个字符'),
  name: z.string().min(1, '姓名不能为空').max(100, '姓名不能超过100个字符'),
  role: z.enum(['admin', 'user', 'guest']),
});

export function validateFileExtension(fileName: string, allowedExtensions: string[]): boolean {
  const extension = fileName.split('.').pop()?.toLowerCase();
  return extension ? allowedExtensions.includes(extension) : false;
}

export function validateFileSize(fileSize: number, maxSizeMB: number): boolean {
  return fileSize <= maxSizeMB * 1024 * 1024;
}

export function validateDatasetName(name: string): boolean {
  return name.length >= 1 && name.length <= 100;
}

export function validateExperimentName(name: string): boolean {
  return name.length >= 1 && name.length <= 100;
}

export function validateXGBoostParams(params: any): boolean {
  try {
    experimentCreateSchema.shape.config.shape.xgboostParams.parse(params);
    return true;
  } catch {
    return false;
  }
}