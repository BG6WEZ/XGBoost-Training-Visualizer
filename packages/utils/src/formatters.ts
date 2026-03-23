export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function formatNumber(num: number, decimals: number = 2): string {
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatPercentage(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatExperimentStatus(status: string): string {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    queued: '排队中',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  };
  return statusMap[status] || status;
}

export function formatUploadStatus(status: string): string {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    uploading: '上传中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  };
  return statusMap[status] || status;
}

export function formatProgress(progress: number): string {
  return `${Math.round(progress * 100)}%`;
}

export function formatMetricName(metric: string): string {
  const metricMap: Record<string, string> = {
    rmse: '均方根误差',
    mse: '均方误差',
    mae: '平均绝对误差',
    r2: 'R² 评分',
    accuracy: '准确率',
    precision: '精确率',
    recall: '召回率',
    f1: 'F1 分数',
    auc: 'AUC 值',
  };
  return metricMap[metric] || metric;
}

export function formatTaskType(taskType: string): string {
  const taskMap: Record<string, string> = {
    regression: '回归',
    classification: '分类',
  };
  return taskMap[taskType] || taskType;
}

export function formatSplitType(splitType: string): string {
  const splitMap: Record<string, string> = {
    time: '时间维度',
    space: '空间维度',
    mixed: '混合维度',
  };
  return splitMap[splitType] || splitType;
}

export function formatTransferStrategy(strategy: string): string {
  const strategyMap: Record<string, string> = {
    'fine-tuning': '微调',
    'feature-extraction': '特征提取',
    'domain-adaptation': '域适应',
  };
  return strategyMap[strategy] || strategy;
}

export function formatAutoTuningStrategy(strategy: string): string {
  const strategyMap: Record<string, string> = {
    grid: '网格搜索',
    random: '随机搜索',
    bayesian: '贝叶斯优化',
  };
  return strategyMap[strategy] || strategy;
}