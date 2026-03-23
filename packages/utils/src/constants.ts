export const APP_NAME = 'XGBoost 训练可视化工具';

export const MAX_FILE_SIZE_MB = 1024; // 1GB
export const MAX_CHUNK_SIZE_MB = 5; // 5MB
export const MAX_CONCURRENT_UPLOADS = 3;

export const MAX_CONCURRENT_TRAININGS = 3;

export const DEFAULT_PAGE_SIZE = 20;

export const DEFAULT_TEST_SIZE = 0.2;

export const DEFAULT_RANDOM_SEED = 42;

export const XGBOOST_DEFAULT_PARAMS = {
  learningRate: 0.1,
  maxDepth: 6,
  nEstimators: 100,
  subsample: 1.0,
  colsampleBytree: 1.0,
  gamma: 0,
  alpha: 0,
  lambda: 1,
  minChildWeight: 1,
  treeMethod: 'auto',
  booster: 'gbtree',
};

export const TASK_TYPES = [
  { value: 'regression', label: '回归' },
  { value: 'classification', label: '分类' },
];

export const EVAL_METRICS = {
  regression: [
    { value: 'rmse', label: 'RMSE (均方根误差)' },
    { value: 'mse', label: 'MSE (均方误差)' },
    { value: 'mae', label: 'MAE (平均绝对误差)' },
    { value: 'r2', label: 'R² 评分' },
  ],
  classification: [
    { value: 'accuracy', label: '准确率' },
    { value: 'precision', label: '精确率' },
    { value: 'recall', label: '召回率' },
    { value: 'f1', label: 'F1 分数' },
    { value: 'auc', label: 'AUC 值' },
  ],
};

export const EARLY_STOPPING_METRICS = [
  { value: 'rmse', label: 'RMSE' },
  { value: 'mse', label: 'MSE' },
  { value: 'mae', label: 'MAE' },
  { value: 'r2', label: 'R²' },
  { value: 'accuracy', label: '准确率' },
  { value: 'auc', label: 'AUC' },
];

export const SPLIT_TYPES = [
  { value: 'time', label: '时间维度' },
  { value: 'space', label: '空间维度' },
  { value: 'mixed', label: '混合维度' },
];

export const SUBSET_PURPOSES = [
  { value: 'train', label: '训练集' },
  { value: 'test', label: '测试集' },
  { value: 'compare', label: '对比集' },
  { value: 'transfer_source', label: '迁移源' },
  { value: 'transfer_target', label: '迁移目标' },
];

export const TRANSFER_STRATEGIES = [
  { value: 'fine-tuning', label: '微调' },
  { value: 'feature-extraction', label: '特征提取' },
  { value: 'domain-adaptation', label: '域适应' },
];

export const AUTO_TUNING_STRATEGIES = [
  { value: 'grid', label: '网格搜索' },
  { value: 'random', label: '随机搜索' },
  { value: 'bayesian', label: '贝叶斯优化' },
];

export const FILE_TYPES = [
  { value: 'csv', label: 'CSV 文件', extensions: ['.csv'] },
  { value: 'excel', label: 'Excel 文件', extensions: ['.xlsx', '.xls'] },
  { value: 'json', label: 'JSON 文件', extensions: ['.json'] },
];

export const COLORS = {
  primary: '#6366F1',
  secondary: '#8B5CF6',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  background: '#F9FAFB',
  foreground: '#1F2937',
  border: '#E5E7EB',
};

export const CHART_COLORS = [
  '#6366F1',
  '#F59E0B',
  '#10B981',
  '#EF4444',
  '#8B5CF6',
  '#3B82F6',
  '#14B8A6',
  '#F97316',
  '#84CC16',
  '#EC4899',
];

export const STATUS_COLORS = {
  pending: '#9CA3AF',
  queued: '#6B7280',
  running: '#3B82F6',
  paused: '#F59E0B',
  completed: '#10B981',
  failed: '#EF4444',
  cancelled: '#6B7280',
};

export const UPLOAD_STATUS_COLORS = {
  pending: '#9CA3AF',
  uploading: '#3B82F6',
  processing: '#F59E0B',
  completed: '#10B981',
  failed: '#EF4444',
};

export const API_ENDPOINTS = {
  auth: {
    login: '/api/auth/login',
    logout: '/api/auth/logout',
    me: '/api/auth/me',
  },
  datasets: {
    list: '/api/datasets',
    create: '/api/datasets',
    detail: (id: string) => `/api/datasets/${id}`,
    delete: (id: string) => `/api/datasets/${id}`,
    preview: (id: string) => `/api/datasets/${id}/preview`,
    columns: (id: string) => `/api/datasets/${id}/columns`,
    subsets: (id: string) => `/api/datasets/${id}/subsets`,
    features: (id: string) => `/api/datasets/${id}/features`,
  },
  experiments: {
    list: '/api/experiments',
    create: '/api/experiments',
    detail: (id: string) => `/api/experiments/${id}`,
    delete: (id: string) => `/api/experiments/${id}`,
    start: (id: string) => `/api/experiments/${id}/start`,
    pause: (id: string) => `/api/experiments/${id}/pause`,
    resume: (id: string) => `/api/experiments/${id}/resume`,
    stop: (id: string) => `/api/experiments/${id}/stop`,
    logs: (id: string) => `/api/experiments/${id}/logs`,
    metrics: (id: string) => `/api/experiments/${id}/metrics`,
    results: (id: string) => `/api/experiments/${id}/results`,
    featureImportance: (id: string) => `/api/experiments/${id}/feature-importance`,
  },
  transfer: {
    create: '/api/transfer',
    result: (id: string) => `/api/transfer/${id}/result`,
  },
  compare: {
    compare: '/api/compare',
  },
  models: {
    detail: (id: string) => `/api/models/${id}`,
    download: (id: string) => `/api/models/${id}/download`,
  },
  admin: {
    users: '/api/admin/users',
    user: (id: string) => `/api/admin/users/${id}`,
  },
};

export const WEBSOCKET_ENDPOINTS = {
  training: (experimentId: string) => `/ws/training/${experimentId}`,
  queue: '/ws/queue',
  progress: '/ws/progress',
};

export const STORAGE_KEYS = {
  token: 'xgboost-vis-token',
  user: 'xgboost-vis-user',
  theme: 'xgboost-vis-theme',
  preferences: 'xgboost-vis-preferences',
};

export const ERROR_MESSAGES = {
  network: '网络连接失败，请检查网络设置',
  server: '服务器错误，请稍后重试',
  unauthorized: '未授权访问，请重新登录',
  forbidden: '权限不足，无法访问该资源',
  notFound: '请求的资源不存在',
  validation: '数据验证失败，请检查输入',
  upload: '文件上传失败，请重试',
  training: '训练失败，请检查配置',
  generic: '操作失败，请稍后重试',
};

export const SUCCESS_MESSAGES = {
  create: '创建成功',
  update: '更新成功',
  delete: '删除成功',
  upload: '上传成功',
  training: '训练完成',
  login: '登录成功',
  logout: '登出成功',
  generic: '操作成功',
};