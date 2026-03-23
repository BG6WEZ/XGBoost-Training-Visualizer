# XGBoost 训练可视化工具 - 技术架构设计

## 1. 系统架构概览

### 1.1 整体架构图

```
                              用户浏览器
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx 反向代理                           │
│                    (静态资源 + API 代理)                          │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────────────┐
│      前端应用 (React)      │   │         后端 API 服务              │
│  ┌─────────────────────┐  │   │  ┌─────────────────────────────┐  │
│  │ React 19            │  │   │  │ Express/Fastify             │  │
│  │ TypeScript          │  │   │  │ TypeScript                  │  │
│  │ Tailwind CSS        │  │   │  │ tRPC                        │  │
│  │ shadcn/ui           │  │   │  └─────────────────────────────┘  │
│  │ Recharts            │  │   │              │                    │
│  │ TanStack Query      │  │   │              ▼                    │
│  │ Zustand             │  │   │  ┌─────────────────────────────┐  │
│  └─────────────────────┘  │   │  │ 业务逻辑层                  │  │
└───────────────────────────┘   │  │ - 实验管理                  │  │
                                │  │ - 数据处理                  │  │
                                │  │ - 训练调度                  │  │
                                │  └─────────────────────────────┘  │
                                └───────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
        ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
        │    PostgreSQL     │     │      Redis        │     │   训练服务         │
        │  ┌─────────────┐  │     │  ┌─────────────┐  │     │  ┌─────────────┐  │
        │  │ experiments │  │     │  │ 任务队列    │  │     │  │ Python      │  │
        │  │ datasets    │  │     │  │ 实时状态    │  │     │  │ XGBoost     │  │
        │  │ models      │  │     │  │ WebSocket   │  │     │  │ FastAPI     │  │
        │  │ users       │  │     │  │ 缓存        │  │     │  └─────────────┘  │
        │  └─────────────┘  │     │  └─────────────┘  │     └───────────────────┘
        └───────────────────┘     └───────────────────┘
                    │
                    ▼
        ┌───────────────────┐
        │   文件存储         │
        │  (MinIO/本地)      │
        │  - 数据集文件      │
        │  - 模型文件        │
        │  - 训练日志        │
        └───────────────────┘
```

### 1.2 架构分层

| 层级 | 职责 | 技术组件 |
|------|------|----------|
| 表现层 | 用户界面渲染、交互处理 | React, Tailwind CSS |
| API 网关 | 请求路由、认证授权、限流 | Nginx |
| 应用层 | 业务逻辑处理 | Express, tRPC |
| 训练层 | XGBoost 训练执行 | Python, FastAPI |
| 数据层 | 数据持久化、缓存 | PostgreSQL, Redis |
| 存储层 | 文件存储 | MinIO/本地文件系统 |

---

## 2. Monorepo 项目结构

### 2.1 整体项目结构

采用 **pnpm + Turborepo** 的 Monorepo 架构，实现代码共享和统一管理。

```
xgboost-training-visualizer/
├── apps/                          # 应用程序
│   ├── web/                       # 前端应用 (React)
│   │   ├── src/
│   │   │   ├── app/               # 应用入口
│   │   │   │   ├── App.tsx
│   │   │   │   ├── router.tsx
│   │   │   │   └── providers.tsx
│   │   │   │
│   │   │   ├── pages/             # 页面组件
│   │   │   │   ├── dashboard/
│   │   │   │   ├── data-upload/
│   │   │   │   ├── dataset-split/
│   │   │   │   ├── feature-engineering/
│   │   │   │   ├── training-config/
│   │   │   │   ├── training-monitor/
│   │   │   │   ├── transfer-learning/
│   │   │   │   ├── results/
│   │   │   │   ├── experiments/
│   │   │   │   └── settings/
│   │   │   │
│   │   │   ├── components/        # 组件
│   │   │   │   ├── ui/            # shadcn/ui 组件
│   │   │   │   ├── charts/        # 图表组件
│   │   │   │   ├── training/      # 训练相关组件
│   │   │   │   └── layout/        # 布局组件
│   │   │   │
│   │   │   ├── hooks/             # 自定义 Hooks
│   │   │   ├── stores/            # 状态管理
│   │   │   ├── services/          # API 服务
│   │   │   └── lib/               # 工具函数
│   │   │
│   │   ├── public/
│   │   ├── package.json           # @xgboost-vis/web
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   │
│   ├── api/                       # 后端 API 服务 (Node.js)
│   │   ├── src/
│   │   │   ├── index.ts           # 入口文件
│   │   │   ├── routers/           # 路由定义
│   │   │   ├── services/          # 业务服务
│   │   │   ├── models/            # 数据模型
│   │   │   ├── middleware/        # 中间件
│   │   │   ├── utils/             # 工具函数
│   │   │   ├── config/            # 配置
│   │   │   └── types/             # 类型定义
│   │   │
│   │   ├── prisma/                # 数据库迁移
│   │   │   └── migrations/
│   │   │
│   │   ├── package.json           # @xgboost-vis/api
│   │   └── tsconfig.json
│   │
│   └── trainer/                   # 训练服务 (Python)
│       ├── app/
│       │   ├── main.py            # FastAPI 入口
│       │   ├── routers/
│       │   ├── services/
│       │   ├── callbacks/
│       │   ├── models/
│       │   └── utils/
│       │
│       ├── tests/
│       ├── requirements.txt
│       ├── pyproject.toml
│       └── Dockerfile
│
├── packages/                      # 共享包
│   ├── types/                     # @xgboost-vis/types
│   │   ├── src/
│   │   │   ├── experiment.ts      # 实验相关类型
│   │   │   ├── dataset.ts         # 数据集相关类型
│   │   │   ├── training.ts        # 训练相关类型
│   │   │   ├── api.ts             # API 请求/响应类型
│   │   │   └── index.ts
│   │   │
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── utils/                     # @xgboost-vis/utils
│   │   ├── src/
│   │   │   ├── formatters.ts      # 格式化函数
│   │   │   ├── validators.ts      # 验证函数
│   │   │   ├── constants.ts       # 常量定义
│   │   │   └── index.ts
│   │   │
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── config/                    # 共享配置
│       ├── eslint/
│       │   └── base.js
│       ├── typescript/
│       │   └── base.json
│       └── tailwind/
│           └── base.js
│
├── docker/                        # Docker 配置
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   └── nginx/
│       └── nginx.conf
│
├── docs/                          # 项目文档
│   ├── PROJECT_FUNCTIONAL_SPECIFICATION.md
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── UI_DESIGN_SPECIFICATION.md
│   ├── CORE_FEATURES_DESIGN.md
│   └── references/
│
├── dataset/                       # 示例数据集
├── scripts/                       # 构建和部署脚本
│   ├── build.sh
│   ├── dev.sh
│   ├── deploy.sh
│   └── db-init.sh
│
├── .env.example                   # 环境变量示例
├── .gitignore
├── package.json                   # 根 package.json
├── pnpm-workspace.yaml            # pnpm workspace 配置
├── turbo.json                     # Turborepo 配置
├── pnpm-lock.yaml
└── README.md
```

### 2.2 根配置文件

```json
// package.json (root)
{
  "name": "xgboost-training-visualizer",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "lint": "turbo run lint",
    "test": "turbo run test",
    "clean": "turbo run clean && rm -rf node_modules",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md}\"",
    "typecheck": "turbo run typecheck",
    "docker:up": "docker-compose -f docker/docker-compose.yml up -d",
    "docker:down": "docker-compose -f docker/docker-compose.yml down",
    "docker:dev": "docker-compose -f docker/docker-compose.dev.yml up -d",
    "db:migrate": "pnpm --filter @xgboost-vis/api db:migrate",
    "db:seed": "pnpm --filter @xgboost-vis/api db:seed",
    "db:reset": "pnpm --filter @xgboost-vis/api db:reset"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "eslint": "^8.57.0",
    "prettier": "^3.2.0",
    "turbo": "^2.0.0",
    "typescript": "^5.4.0"
  },
  "packageManager": "pnpm@9.0.0",
  "engines": {
    "node": ">=20.0.0",
    "pnpm": ">=9.0.0"
  }
}
```

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "dependsOn": ["^lint"]
    },
    "typecheck": {
      "dependsOn": ["^typecheck"]
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "clean": {
      "cache": false
    }
  }
}
```

### 2.3 共享包设计

#### @xgboost-vis/types

前后端共享的类型定义，确保类型安全。

```typescript
// packages/types/src/experiment.ts
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
}
```

```typescript
// packages/types/src/dataset.ts
export interface Dataset {
  id: string;
  name: string;
  filePath: string;
  fileSize: number;
  rowCount: number;
  columnCount: number;
  columnsInfo: ColumnInfo[];
  uploadStatus: UploadStatus;
  createdAt: Date;
}

export interface DatasetSubset {
  id: string;
  parentDatasetId: string;
  name: string;
  purpose: 'train' | 'test' | 'compare' | 'transfer_source' | 'transfer_target';
  rowCount: number;
  splitConfig: SplitConfig;
  createdAt: Date;
}

export interface SplitConfig {
  type: 'time' | 'space' | 'mixed';
  timeColumn?: string;
  idColumn?: string;
  splits: SplitDefinition[];
}
```

#### @xgboost-vis/utils

共享的工具函数。

```typescript
// packages/utils/src/formatters.ts
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
```

---

## 3. 前端架构设计 (apps/web)

### 3.1 状态管理设计

使用 Zustand 进行状态管理，按功能域划分：

```typescript
// stores/experiment-store.ts
interface ExperimentStore {
  experiments: Experiment[];
  currentExperiment: Experiment | null;
  filters: ExperimentFilters;

  // Actions
  fetchExperiments: () => Promise<void>;
  selectExperiment: (id: string) => void;
  deleteExperiment: (id: string) => Promise<void>;
  setFilters: (filters: Partial<ExperimentFilters>) => void;
}

// stores/training-store.ts
interface TrainingStore {
  trainingStatus: TrainingStatus;
  progress: number;
  metrics: MetricPoint[];
  logs: LogEntry[];

  // WebSocket 实时更新
  connectToTraining: (experimentId: string) => void;
  disconnect: () => void;
}
```

### 3.2 实时通信设计

```typescript
// services/websocket.ts
class TrainingWebSocket {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<Callback>> = new Map();

  connect(experimentId: string) {
    this.ws = new WebSocket(`ws://api/ws/training/${experimentId}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.emit(data.type, data.payload);
    };
  }

  on(event: TrainingEvent, callback: Callback) {
    // 注册事件监听
  }

  off(event: TrainingEvent, callback: Callback) {
    // 移除事件监听
  }
}

// 事件类型
type TrainingEvent =
  | 'progress'      // 进度更新
  | 'metric'        // 指标更新
  | 'log'           // 日志条目
  | 'completed'     // 训练完成
  | 'error';        // 错误发生
```

### 3.3 图表组件设计

```typescript
// components/charts/loss-curve.tsx
interface LossCurveProps {
  data: {
    iteration: number;
    trainLoss: number;
    valLoss: number;
  }[];
  isRealTime?: boolean;
  height?: number;
}

export function LossCurve({ data, isRealTime, height = 300 }: LossCurveProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <XAxis dataKey="iteration" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="trainLoss"
          stroke="#6366F1"
          isAnimationActive={!isRealTime}
        />
        <Line
          type="monotone"
          dataKey="valLoss"
          stroke="#F59E0B"
          isAnimationActive={!isRealTime}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

---

## 4. 后端架构设计 (apps/api)

### 4.1 API 服务结构

```
api/
├── src/
│   ├── index.ts                  # 入口文件
│   ├── routers/                  # 路由定义
│   │   ├── experiment.router.ts
│   │   ├── dataset.router.ts
│   │   ├── training.router.ts
│   │   └── model.router.ts
│   │
│   ├── services/                 # 业务服务
│   │   ├── experiment.service.ts
│   │   ├── dataset.service.ts
│   │   ├── dataset-split.service.ts    # 数据集切分服务
│   │   ├── feature-engineering.service.ts  # 特征工程服务
│   │   ├── transfer-learning.service.ts    # 迁移学习服务
│   │   ├── training.service.ts
│   │   ├── model-version.service.ts    # 模型版本管理服务
│   │   ├── data-quality.service.ts     # 数据质量检测服务
│   │   ├── shap.service.ts             # SHAP分析服务
│   │   ├── gpu-config.service.ts       # GPU配置服务
│   │   └── storage.service.ts
│   │
│   ├── models/                   # 数据模型
│   │   ├── experiment.model.ts
│   │   ├── dataset.model.ts
│   │   └── training-log.model.ts
│   │
│   ├── middleware/               # 中间件
│   │   ├── auth.ts
│   │   ├── error-handler.ts
│   │   └── rate-limiter.ts
│   │
│   ├── utils/                    # 工具函数
│   │   ├── validation.ts
│   │   └── response.ts
│   │
│   ├── config/                   # 配置
│   │   ├── database.ts
│   │   ├── redis.ts
│   │   └── storage.ts
│   │
│   └── types/                    # 类型定义
│       └── index.ts
│
├── package.json
└── tsconfig.json
```

### 4.2 核心服务设计

#### 实验服务

```typescript
// services/experiment.service.ts
export class ExperimentService {
  constructor(
    private db: Database,
    private redis: RedisClient,
    private trainingQueue: TrainingQueue
  ) {}

  async create(data: CreateExperimentDTO): Promise<Experiment> {
    // 创建实验记录
    const experiment = await this.db.experiments.create({
      name: data.name,
      description: data.description,
      datasetId: data.datasetId,
      config: data.config,
      status: 'pending',
    });

    return experiment;
  }

  async startTraining(experimentId: string): Promise<void> {
    // 验证实验状态
    const experiment = await this.getById(experimentId);
    if (experiment.status !== 'pending') {
      throw new BadRequestError('实验状态不正确');
    }

    // 加入训练队列
    await this.trainingQueue.add({
      experimentId,
      config: experiment.config,
      datasetPath: experiment.dataset.filePath,
    });

    // 更新状态
    await this.updateStatus(experimentId, 'running');
  }

  async getResults(experimentId: string): Promise<TrainingResults> {
    // 获取训练结果
    const metrics = await this.db.metrics.findMany({
      where: { experimentId },
      orderBy: { iteration: 'asc' },
    });

    const featureImportance = await this.db.featureImportance.findMany({
      where: { experimentId },
      orderBy: { importance: 'desc' },
    });

    return { metrics, featureImportance };
  }
}
```

#### 训练服务

```typescript
// services/training.service.ts
export class TrainingService {
  private activeTrainings: Map<string, TrainingProcess> = new Map();

  async startTraining(
    experimentId: string,
    config: TrainingConfig,
    datasetPath: string
  ): Promise<void> {
    // 调用 Python 训练服务
    const response = await fetch(`${PYTHON_SERVICE_URL}/train`, {
      method: 'POST',
      body: JSON.stringify({
        experiment_id: experimentId,
        dataset_path: datasetPath,
        config: config,
        callback_url: `${API_URL}/training/${experimentId}/callback`,
      }),
    });

    const { process_id } = await response.json();

    // 注册 WebSocket 更新
    this.setupProgressListener(experimentId, process_id);
  }

  async stopTraining(experimentId: string): Promise<void> {
    const process = this.activeTrainings.get(experimentId);
    if (process) {
      await fetch(`${PYTHON_SERVICE_URL}/train/${process.id}/stop`, {
        method: 'POST',
      });
    }
  }

  private setupProgressListener(experimentId: string, processId: string) {
    // 订阅 Redis 频道接收训练进度
    const channel = `training:${experimentId}`;
    this.redis.subscribe(channel, (message) => {
      const data = JSON.parse(message);
      this.broadcastProgress(experimentId, data);
    });
  }

  private broadcastProgress(experimentId: string, data: ProgressData) {
    // 通过 WebSocket 广播给前端
    this.wsServer.to(experimentId).emit(data.type, data.payload);
  }
}
```

### 4.3 数据集切分服务

```typescript
// services/dataset-split.service.ts
export class DatasetSplitService {
  constructor(
    private db: Database,
    private storage: StorageService
  ) {}

  /**
   * 按时间维度切分数据集
   * 示例：15天数据 → 训练10天 + 测试3天 + 对比2天
   */
  async splitByTime(
    datasetId: string,
    config: TimeSplitConfig
  ): Promise<SplitResult[]> {
    const dataset = await this.db.datasets.findById(datasetId);
    const df = await this.loadDataset(dataset.filePath);

    const timeColumn = config.timeColumn;
    const splits: SplitResult[] = [];

    for (const split of config.splits) {
      const filtered = df.filter((row) => {
        const time = new Date(row[timeColumn]);
        return time >= split.startDate && time <= split.endDate;
      });

      const splitFile = await this.saveSubset(filtered, split.name);
      splits.push({
        name: split.name,
        purpose: split.purpose, // 'train' | 'test' | 'compare'
        rowCount: filtered.length,
        filePath: splitFile,
        dateRange: { start: split.startDate, end: split.endDate }
      });
    }

    return splits;
  }

  /**
   * 按空间维度切分数据集
   * 示例：按 Building_ID 切分，建筑A用于训练，建筑B用于迁移预测
   */
  async splitBySpace(
    datasetId: string,
    config: SpaceSplitConfig
  ): Promise<SplitResult[]> {
    const dataset = await this.db.datasets.findById(datasetId);
    const df = await this.loadDataset(dataset.filePath);

    const idColumn = config.idColumn;
    const splits: SplitResult[] = [];

    for (const split of config.splits) {
      const filtered = df.filter((row) =>
        split.ids.includes(row[idColumn])
      );

      const splitFile = await this.saveSubset(filtered, split.name);
      splits.push({
        name: split.name,
        purpose: split.purpose,
        rowCount: filtered.length,
        filePath: splitFile,
        ids: split.ids
      });
    }

    return splits;
  }

  /**
   * 混合维度切分
   * 同时按时间和空间切分
   */
  async splitMixed(
    datasetId: string,
    config: MixedSplitConfig
  ): Promise<SplitResult[]> {
    // 先按空间切分，再在每个空间子集中按时间切分
    // 或反之
  }
}
```

### 4.4 特征工程服务

```typescript
// services/feature-engineering.service.ts
export class FeatureEngineeringService {

  /**
   * 自动特征工程
   */
  async process(
    datasetId: string,
    config: FeatureEngineeringConfig
  ): Promise<FeatureEngineeringResult> {
    const df = await this.loadDataset(datasetId);
    let processedDf = df;

    // 1. 时间特征提取
    if (config.timeFeatures?.enabled) {
      processedDf = this.extractTimeFeatures(
        processedDf,
        config.timeFeatures.columns,
        config.timeFeatures.features
      );
    }

    // 2. 滞后特征
    if (config.lagFeatures?.enabled) {
      processedDf = this.createLagFeatures(
        processedDf,
        config.lagFeatures.columns,
        config.lagFeatures.lags
      );
    }

    // 3. 滚动统计特征
    if (config.rollingFeatures?.enabled) {
      processedDf = this.createRollingFeatures(
        processedDf,
        config.rollingFeatures.columns,
        config.rollingFeatures.windows
      );
    }

    // 4. 编码转换
    if (config.encoding?.enabled) {
      processedDf = this.encodeCategories(
        processedDf,
        config.encoding.columns,
        config.encoding.method
      );
    }

    // 5. 缺失值处理
    if (config.missingValue?.enabled) {
      processedDf = this.handleMissingValues(
        processedDf,
        config.missingValue.strategy
      );
    }

    return {
      originalColumns: df.columns,
      processedColumns: processedDf.columns,
      newFeatures: processedDf.columns.filter(c => !df.columns.includes(c)),
      rowCount: processedDf.length,
      processedFilePath: await this.saveDataset(processedDf)
    };
  }

  private extractTimeFeatures(
    df: DataFrame,
    columns: string[],
    features: TimeFeatureType[]
  ): DataFrame {
    for (const col of columns) {
      const dates = df[col].map(v => new Date(v));
      for (const feature of features) {
        switch (feature) {
          case 'hour':
            df[`${col}_hour`] = dates.map(d => d.getHours());
            break;
          case 'day_of_week':
            df[`${col}_day_of_week`] = dates.map(d => d.getDay());
            break;
          case 'day_of_month':
            df[`${col}_day_of_month`] = dates.map(d => d.getDate());
            break;
          case 'month':
            df[`${col}_month`] = dates.map(d => d.getMonth() + 1);
            break;
          case 'is_weekend':
            df[`${col}_is_weekend`] = dates.map(d => d.getDay() === 0 || d.getDay() === 6 ? 1 : 0);
            break;
          case 'quarter':
            df[`${col}_quarter`] = dates.map(d => Math.floor(d.getMonth() / 3) + 1);
            break;
        }
      }
    }
    return df;
  }

  private createLagFeatures(
    df: DataFrame,
    columns: string[],
    lags: number[]
  ): DataFrame {
    for (const col of columns) {
      for (const lag of lags) {
        df[`${col}_lag_${lag}`] = df[col].shift(lag);
      }
    }
    return df;
  }

  private createRollingFeatures(
    df: DataFrame,
    columns: string[],
    windows: number[]
  ): DataFrame {
    for (const col of columns) {
      for (const window of windows) {
        df[`${col}_rolling_mean_${window}`] = df[col].rolling(window).mean();
        df[`${col}_rolling_std_${window}`] = df[col].rolling(window).std();
        df[`${col}_rolling_min_${window}`] = df[col].rolling(window).min();
        df[`${col}_rolling_max_${window}`] = df[col].rolling(window).max();
      }
    }
    return df;
  }
}
```

### 4.5 迁移学习服务

```typescript
// services/transfer-learning.service.ts
export class TransferLearningService {
  constructor(
    private db: Database,
    private trainer: TrainingService
  ) {}

  /**
   * 执行迁移学习
   * 用源建筑数据训练，预测目标建筑
   */
  async executeTransfer(
    config: TransferLearningConfig
  ): Promise<TransferLearningResult> {
    // 1. 加载源建筑模型
    const sourceModel = await this.loadModel(config.sourceModelId);

    // 2. 加载目标建筑数据
    const targetData = await this.loadDataset(config.targetDatasetId);

    // 3. 根据策略执行迁移
    let result: TransferLearningResult;

    switch (config.strategy) {
      case 'direct':
        // 直接使用源模型预测目标数据
        result = await this.directTransfer(sourceModel, targetData, config);
        break;

      case 'finetune':
        // 在目标数据上微调源模型
        result = await this.finetuneTransfer(sourceModel, targetData, config);
        break;

      case 'align':
        // 特征对齐后迁移
        result = await this.alignTransfer(sourceModel, targetData, config);
        break;

      default:
        throw new Error(`Unknown strategy: ${config.strategy}`);
    }

    // 4. 评估迁移效果
    result.evaluation = await this.evaluateTransfer(result, targetData);

    return result;
  }

  /**
   * 直接迁移：不修改模型，直接预测
   */
  private async directTransfer(
    model: XGBoostModel,
    targetData: DataFrame,
    config: TransferLearningConfig
  ): Promise<TransferLearningResult> {
    const predictions = model.predict(targetData.features);

    return {
      strategy: 'direct',
      predictions,
      modelId: model.id,
      targetDatasetId: config.targetDatasetId
    };
  }

  /**
   * 微调迁移：在目标数据上继续训练
   */
  private async finetuneTransfer(
    model: XGBoostModel,
    targetData: DataFrame,
    config: TransferLearningConfig
  ): Promise<TransferLearningResult> {
    // 划分目标数据为训练集和测试集
    const { trainX, trainY, testX, testY } = this.splitTargetData(
      targetData,
      config.finetuneRatio || 0.3
    );

    // 继续训练
    const finetunedModel = await this.trainer.continueTraining(
      model,
      trainX,
      trainY,
      config.finetuneParams || {}
    );

    // 预测
    const predictions = finetunedModel.predict(testX);

    return {
      strategy: 'finetune',
      predictions,
      modelId: finetunedModel.id,
      targetDatasetId: config.targetDatasetId,
      finetuneMetrics: {
        trainSize: trainX.length,
        testSize: testX.length
      }
    };
  }

  /**
   * 评估迁移学习效果
   */
  private async evaluateTransfer(
    result: TransferLearningResult,
    targetData: DataFrame
  ): Promise<TransferEvaluation> {
    const actual = targetData.target;
    const predicted = result.predictions;

    return {
      rmse: this.calculateRMSE(actual, predicted),
      mae: this.calculateMAE(actual, predicted),
      r2: this.calculateR2(actual, predicted),
      mape: this.calculateMAPE(actual, predicted),
      comparisonBaseline: await this.getBaselineComparison(result.modelId, targetData)
    };
  }
}
```

### 4.6 模型版本管理服务

```typescript
// services/model-version.service.ts
export class ModelVersionService {
  constructor(
    private db: Database,
    private storage: StorageService
  ) {}

  /**
   * 创建模型版本
   */
  async createVersion(
    modelId: string,
    data: CreateVersionDTO
  ): Promise<ModelVersion> {
    // 获取模型信息
    const model = await this.db.models.findById(modelId);
    if (!model) {
      throw new NotFoundError('模型不存在');
    }

    // 生成版本号
    const latestVersion = await this.getLatestVersion(modelId);
    const versionNumber = this.incrementVersion(latestVersion?.versionNumber);

    // 创建配置快照
    const experiment = await this.db.experiments.findById(model.experimentId);
    const configSnapshot = experiment.config;
    const metricsSnapshot = await this.getMetricsSnapshot(experiment.id);

    // 创建版本记录
    const version = await this.db.modelVersions.create({
      modelId,
      versionNumber,
      versionName: data.name,
      description: data.description,
      configSnapshot,
      metricsSnapshot,
      tags: data.tags || [],
      createdBy: data.userId
    });

    return version;
  }

  /**
   * 添加版本标签
   */
  async addTag(versionId: string, tag: string): Promise<void> {
    const version = await this.db.modelVersions.findById(versionId);
    if (!version) {
      throw new NotFoundError('版本不存在');
    }

    // 检查标签是否已存在
    if (version.tags.includes(tag)) {
      return;
    }

    // 如果是 production 或 best 标签，移除同模型其他版本的该标签
    if (['production', 'best'].includes(tag)) {
      await this.db.modelVersions.updateMany(
        { modelId: version.modelId, tags: { has: tag } },
        { tags: { pull: tag } }
      );
    }

    await this.db.modelVersions.update(versionId, {
      tags: { push: tag }
    });
  }

  /**
   * 版本比较
   */
  async compareVersions(
    versionIds: string[]
  ): Promise<VersionComparison> {
    const versions = await this.db.modelVersions.findMany({
      where: { id: { in: versionIds } }
    });

    if (versions.length < 2) {
      throw new BadRequestError('至少需要选择两个版本进行比较');
    }

    // 比较配置差异
    const configDiff = this.diffConfigs(
      versions.map(v => v.configSnapshot)
    );

    // 比较指标差异
    const metricsDiff = this.diffMetrics(
      versions.map(v => v.metricsSnapshot)
    );

    return {
      versions: versions.map(v => ({
        id: v.id,
        versionNumber: v.versionNumber,
        name: v.versionName,
        tags: v.tags
      })),
      configDiff,
      metricsDiff
    };
  }

  /**
   * 版本回滚
   */
  async rollback(modelId: string, versionId: string): Promise<void> {
    const version = await this.db.modelVersions.findById(versionId);
    if (!version || version.modelId !== modelId) {
      throw new BadRequestError('版本不存在或不属于该模型');
    }

    // 标记为回滚版本
    await this.addTag(versionId, 'rollback');

    // 可以选择用旧配置创建新的训练任务
    // 这里记录回滚操作，实际回滚需要用户确认
    await this.db.auditLogs.create({
      action: 'model_version_rollback',
      entityId: modelId,
      details: {
        targetVersion: versionId,
        targetVersionNumber: version.versionNumber
      }
    });
  }

  private incrementVersion(current?: string): string {
    if (!current) return 'v1.0.0';

    const match = current.match(/v(\d+)\.(\d+)\.(\d+)/);
    if (!match) return 'v1.0.0';

    const [, major, minor, patch] = match;
    return `v${major}.${minor}.${parseInt(patch) + 1}`;
  }
}
```

### 4.7 数据质量检测服务

```typescript
// services/data-quality.service.ts
export class DataQualityService {
  constructor(
    private db: Database,
    private redis: RedisClient,
    private pythonService: string
  ) {}

  /**
   * 执行数据质量检测
   */
  async analyze(datasetId: string, config?: QualityCheckConfig): Promise<QualityReport> {
    const dataset = await this.db.datasets.findById(datasetId);
    if (!dataset) {
      throw new NotFoundError('数据集不存在');
    }

    // 创建检测任务
    const checkId = uuidv4();
    await this.redis.hset(`quality_check:${checkId}:status`, {
      status: 'running',
      progress: 0,
      startedAt: new Date().toISOString()
    });

    try {
      // 调用 Python 服务执行检测
      const response = await fetch(`${this.pythonService}/quality/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_path: dataset.filePath,
          check_id: checkId,
          config: config || {
            checkCompleteness: true,
            checkAccuracy: true,
            checkConsistency: true,
            checkDistribution: true
          }
        })
      });

      const result = await response.json();

      // 保存报告
      const report = await this.db.dataQualityReports.create({
        datasetId,
        reportType: config?.type || 'full',
        overallScore: result.overall_score,
        completenessScore: result.completeness_score,
        accuracyScore: result.accuracy_score,
        consistencyScore: result.consistency_score,
        distributionScore: result.distribution_score,
        issues: result.issues,
        recommendations: result.recommendations,
        columnStats: result.column_stats
      });

      // 保存问题详情
      for (const issue of result.issues) {
        await this.db.dataQualityIssues.create({
          reportId: report.id,
          columnName: issue.column_name,
          issueType: issue.type,
          severity: issue.severity,
          description: issue.description,
          affectedRows: issue.affected_rows,
          affectedPercentage: issue.affected_percentage,
          suggestion: issue.suggestion
        });
      }

      return report;
    } finally {
      await this.redis.del(`quality_check:${checkId}:status`);
    }
  }

  /**
   * 获取质量评分
   */
  async getQualityScore(datasetId: string): Promise<QualityScore> {
    // 先检查缓存
    const cached = await this.redis.get(`quality_report:${datasetId}:latest`);
    if (cached) {
      return JSON.parse(cached);
    }

    // 获取最新报告
    const latestReport = await this.db.dataQualityReports.findFirst({
      where: { datasetId },
      orderBy: { createdAt: 'desc' }
    });

    if (!latestReport) {
      return { score: null, status: 'not_checked' };
    }

    const result = {
      score: latestReport.overallScore,
      completeness: latestReport.completenessScore,
      accuracy: latestReport.accuracyScore,
      consistency: latestReport.consistencyScore,
      distribution: latestReport.distributionScore,
      issuesCount: latestReport.issues?.length || 0,
      lastChecked: latestReport.createdAt
    };

    // 缓存结果
    await this.redis.setex(
      `quality_report:${datasetId}:latest`,
      3600,
      JSON.stringify(result)
    );

    return result;
  }

  /**
   * 获取改进建议
   */
  async getRecommendations(datasetId: string): Promise<QualityRecommendation[]> {
    const report = await this.db.dataQualityReports.findFirst({
      where: { datasetId },
      orderBy: { createdAt: 'desc' },
      include: { issues: true }
    });

    if (!report) {
      return [];
    }

    // 按严重程度排序的建议
    const criticalIssues = report.issues.filter(i => i.severity === 'critical');
    const warnings = report.issues.filter(i => i.severity === 'warning');

    const recommendations: QualityRecommendation[] = [];

    // 严重问题必须优先处理
    for (const issue of criticalIssues) {
      recommendations.push({
        priority: 'high',
        type: issue.issueType,
        description: issue.description,
        suggestion: issue.suggestion,
        affectedColumn: issue.columnName
      });
    }

    // 警告问题
    for (const issue of warnings) {
      recommendations.push({
        priority: 'medium',
        type: issue.issueType,
        description: issue.description,
        suggestion: issue.suggestion,
        affectedColumn: issue.columnName
      });
    }

    return recommendations;
  }
}
```

### 4.8 GPU 配置服务

```typescript
// services/gpu-config.service.ts
export class GPUConfigService {
  constructor(
    private db: Database,
    private redis: RedisClient,
    private pythonService: string
  ) {}

  /**
   * 检测系统 GPU
   */
  async detectGPUs(): Promise<GPUInfo[]> {
    try {
      const response = await fetch(`${this.pythonService}/gpu/detect`);
      const data = await response.json();

      // 更新 GPU 状态表
      for (const gpu of data.gpus) {
        await this.db.gpuStatus.upsert({
          where: { deviceId: gpu.id },
          create: {
            deviceId: gpu.id,
            deviceName: gpu.name,
            totalMemory: gpu.total_memory,
            freeMemory: gpu.free_memory,
            utilization: gpu.utilization,
            temperature: gpu.temperature,
            isAvailable: true
          },
          update: {
            deviceName: gpu.name,
            freeMemory: gpu.free_memory,
            utilization: gpu.utilization,
            temperature: gpu.temperature,
            isAvailable: true,
            lastChecked: new Date()
          }
        });
      }

      // 缓存 GPU 状态
      await this.redis.setex(
        'gpu:status',
        60,
        JSON.stringify(data.gpus)
      );

      return data.gpus;
    } catch (error) {
      // GPU 检测失败，返回空数组
      return [];
    }
  }

  /**
   * 获取 GPU 状态
   */
  async getGPUStatus(): Promise<GPUStatusResult> {
    // 先检查缓存
    const cached = await this.redis.get('gpu:status');
    if (cached) {
      const gpus = JSON.parse(cached);
      return {
        hasGPU: gpus.length > 0,
        gpus,
        recommendedDevice: gpus.length > 0 ? 'cuda' : 'cpu'
      };
    }

    // 重新检测
    const gpus = await this.detectGPUs();
    return {
      hasGPU: gpus.length > 0,
      gpus,
      recommendedDevice: gpus.length > 0 ? 'cuda' : 'cpu'
    };
  }

  /**
   * 创建 GPU 配置
   */
  async createConfig(data: CreateGPUConfigDTO): Promise<GPUConfig> {
    // 如果设置为默认，取消其他默认配置
    if (data.isDefault) {
      await this.db.gpuConfigs.updateMany(
        { isDefault: true },
        { isDefault: false }
      );
    }

    return await this.db.gpuConfigs.create({
      name: data.name,
      deviceType: data.deviceType,
      deviceIds: data.deviceIds || [],
      memoryLimit: data.memoryLimit,
      autoFallback: data.autoFallback ?? true,
      isDefault: data.isDefault ?? false
    });
  }

  /**
   * 获取默认配置
   */
  async getDefaultConfig(): Promise<GPUConfig> {
    // 先查找用户设置的默认配置
    const defaultConfig = await this.db.gpuConfigs.findFirst({
      where: { isDefault: true }
    });

    if (defaultConfig) {
      return defaultConfig;
    }

    // 根据系统状态返回自动配置
    const status = await this.getGPUStatus();

    if (status.hasGPU) {
      return {
        id: 'auto-gpu',
        name: '自动GPU配置',
        deviceType: 'cuda',
        deviceIds: status.gpus.map(g => g.id),
        autoFallback: true,
        isDefault: true
      };
    }

    return {
      id: 'auto-cpu',
      name: 'CPU配置',
      deviceType: 'cpu',
      deviceIds: [],
      autoFallback: false,
      isDefault: true
    };
  }

  /**
   * 检查 GPU 可用性
   */
  async checkAvailability(deviceId?: number): Promise<GPUAvailability> {
    const status = await this.getGPUStatus();

    if (!status.hasGPU) {
      return {
        available: false,
        reason: 'no_gpu_detected',
        fallback: 'cpu'
      };
    }

    if (deviceId !== undefined) {
      const gpu = status.gpus.find(g => g.id === deviceId);
      if (!gpu) {
        return {
          available: false,
          reason: 'device_not_found',
          fallback: 'cpu'
        };
      }

      // 检查内存是否足够
      if (gpu.freeMemory < 1024) { // 小于 1GB
        return {
          available: false,
          reason: 'insufficient_memory',
          fallback: 'cpu',
          details: { freeMemory: gpu.freeMemory }
        };
      }
    }

    return {
      available: true,
      gpus: status.gpus
    };
  }
}
```

---

## 5. 训练服务设计 (apps/trainer)

### 5.1 项目结构

```
trainer/
├── app/
│   ├── main.py                   # FastAPI 入口
│   ├── routers/
│   │   ├── training.py           # 训练路由
│   │   ├── dataset_split.py      # 数据集切分路由
│   │   ├── feature_engineering.py # 特征工程路由
│   │   ├── transfer_learning.py  # 迁移学习路由
│   │   └── model.py              # 模型操作路由
│   │
│   ├── services/
│   │   ├── trainer.py            # 核心训练逻辑
│   │   ├── data_processor.py     # 数据预处理
│   │   ├── dataset_splitter.py   # 数据集切分服务
│   │   ├── feature_engineer.py   # 特征工程服务
│   │   ├── transfer_learner.py   # 迁移学习服务
│   │   ├── file_splitter.py      # 大文件切分服务
│   │   └── metrics.py            # 指标计算
│   │
│   ├── callbacks/
│   │   ├── progress_callback.py  # 进度回调
│   │   └── logging_callback.py   # 日志回调
│   │
│   ├── models/
│   │   ├── config.py             # 配置模型
│   │   └── results.py            # 结果模型
│   │
│   └── utils/
│       ├── redis_client.py       # Redis 客户端
│       └── storage.py            # 存储操作
│
├── requirements.txt
└── Dockerfile
```

### 5.2 核心训练逻辑

```python
# services/trainer.py
import xgboost as xgb
from typing import Dict, Any, Callable, Optional
import redis
import json

class XGBoostTrainer:
    def __init__(
        self,
        experiment_id: str,
        config: Dict[str, Any],
        progress_callback: Callable
    ):
        self.experiment_id = experiment_id
        self.config = config
        self.progress_callback = progress_callback
        self.model = None
        self.is_stopped = False

    def train(
        self,
        X_train, y_train,
        X_val, y_val
    ) -> Dict[str, Any]:
        """执行训练"""

        # 创建 DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        # 训练参数
        params = self._build_params()
        evals_result = {}

        # 自定义回调
        callbacks = [
            self._create_progress_callback(),
            self._create_logging_callback(),
            self._create_early_stopping_callback()
        ]

        # 执行训练
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=self.config.get('n_estimators', 100),
            evals=[(dtrain, 'train'), (dval, 'val')],
            evals_result=evals_result,
            callbacks=callbacks,
            verbose_eval=False
        )

        return self._build_results(evals_result)

    def _create_progress_callback(self) -> Callable:
        """创建进度回调"""
        total_rounds = self.config.get('n_estimators', 100)

        def callback(env):
            if self.is_stopped:
                raise EarlyStopException()

            iteration = env.iteration
            progress = (iteration + 1) / total_rounds

            # 发送进度更新
            self.progress_callback({
                'type': 'progress',
                'iteration': iteration,
                'total': total_rounds,
                'progress': progress,
                'train_loss': env.evaluation_result_list[0][1],
                'val_loss': env.evaluation_result_list[1][1],
            })

        return callback

    def stop(self):
        """停止训练"""
        self.is_stopped = True

    def save_model(self, path: str, format: str = 'json'):
        """保存模型"""
        if format == 'json':
            self.model.save_model(path)
        elif format == 'ubj':
            self.model.save_model(path)
        elif format == 'pickle':
            import pickle
            with open(path, 'wb') as f:
                pickle.dump(self.model, f)


class ProgressCallback(xgb.callback.TrainingCallback):
    """XGBoost 进度回调"""

    def __init__(self, experiment_id: str, redis_client: redis.Redis):
        self.experiment_id = experiment_id
        self.redis = redis_client
        self.channel = f"training:{experiment_id}"

    def after_iteration(self, model, epoch, evals_log):
        # 发送指标更新
        message = {
            'type': 'metric',
            'iteration': epoch,
            'metrics': {
                'train_loss': evals_log['train']['rmse'][-1],
                'val_loss': evals_log['val']['rmse'][-1],
            }
        }
        self.redis.publish(self.channel, json.dumps(message))
```

### 5.3 FastAPI 路由

```python
# routers/training.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

router = APIRouter()

# 存储活跃的训练进程
active_trainings: Dict[str, TrainingProcess] = {}

class TrainingRequest(BaseModel):
    experiment_id: str
    dataset_path: str
    config: Dict[str, Any]

@router.post("/train")
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """启动训练"""
    process_id = str(uuid.uuid4())

    # 创建训练进程
    trainer = XGBoostTrainer(
        experiment_id=request.experiment_id,
        config=request.config,
        progress_callback=create_progress_callback(request.experiment_id)
    )

    # 存储进程引用
    active_trainings[request.experiment_id] = TrainingProcess(
        id=process_id,
        trainer=trainer,
        status='running'
    )

    # 后台执行训练
    background_tasks.add_task(
        run_training,
        trainer,
        request.dataset_path,
        request.config
    )

    return {"process_id": process_id, "status": "started"}

@router.post("/train/{process_id}/stop")
async def stop_training(process_id: str):
    """停止训练"""
    if process_id not in active_trainings:
        raise HTTPException(status_code=404, detail="训练进程不存在")

    process = active_trainings[process_id]
    process.trainer.stop()
    process.status = 'stopped'

    return {"status": "stopped"}

@router.get("/train/{process_id}/status")
async def get_training_status(process_id: str):
    """获取训练状态"""
    if process_id not in active_trainings:
        raise HTTPException(status_code=404, detail="训练进程不存在")

    process = active_trainings[process_id]
    return {
        "status": process.status,
        "progress": process.progress,
    }
```

### 5.4 大文件切分服务

```python
# services/file_splitter.py
import pandas as pd
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

class FileSplitter:
    """
    大文件自动切分服务
    支持超过 1GB 的文件自动切分
    """

    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
    CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks for upload

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)

    async def check_and_split(
        self,
        file_path: str,
        split_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        检查文件大小并决定是否需要切分
        """
        file_size = os.path.getsize(file_path)

        if file_size <= self.MAX_FILE_SIZE:
            return {
                "needs_split": False,
                "file_path": file_path,
                "file_size": file_size
            }

        # 需要切分
        return await self.split_file(file_path, split_config)

    async def split_file(
        self,
        file_path: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        切分大文件

        切分策略（按优先级）：
        1. 按时间列切分（如果存在时间列）
        2. 按 ID 列切分（如果存在 ID 列）
        3. 按行数均匀切分
        """
        config = config or {}

        # 读取文件元信息
        sample_df = pd.read_csv(file_path, nrows=100)
        total_rows = sum(1 for _ in open(file_path)) - 1

        split_files = []

        # 策略1: 按时间列切分
        if config.get('time_column') and config['time_column'] in sample_df.columns:
            split_files = await self._split_by_time(
                file_path,
                config['time_column'],
                config.get('time_intervals', 'auto')
            )

        # 策略2: 按 ID 列切分
        elif config.get('id_column') and config['id_column'] in sample_df.columns:
            split_files = await self._split_by_id(
                file_path,
                config['id_column'],
                config.get('ids_per_file', 10)
            )

        # 策略3: 按行数均匀切分
        else:
            target_size = self.MAX_FILE_SIZE
            rows_per_file = int(total_rows * target_size / os.path.getsize(file_path))
            split_files = await self._split_by_rows(file_path, rows_per_file)

        return {
            "needs_split": True,
            "original_file": file_path,
            "original_size": os.path.getsize(file_path),
            "split_files": split_files,
            "split_count": len(split_files)
        }

    async def _split_by_time(
        self,
        file_path: str,
        time_column: str,
        intervals: str = 'auto'
    ) -> List[Dict[str, Any]]:
        """按时间列切分"""
        df = pd.read_csv(file_path)
        df[time_column] = pd.to_datetime(df[time_column])

        if intervals == 'auto':
            # 自动确定时间间隔
            date_range = df[time_column].max() - df[time_column].min()
            target_files = max(2, int(os.path.getsize(file_path) / self.MAX_FILE_SIZE))
            interval = date_range / target_files
        else:
            interval = pd.Timedelta(intervals)

        split_files = []
        start_time = df[time_column].min()

        while start_time <= df[time_column].max():
            end_time = start_time + interval
            mask = (df[time_column] >= start_time) & (df[time_column] < end_time)
            subset = df[mask]

            if len(subset) > 0:
                file_name = f"{Path(file_path).stem}_{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}.csv"
                split_path = self.storage_path / file_name
                subset.to_csv(split_path, index=False)

                split_files.append({
                    "file_path": str(split_path),
                    "file_size": os.path.getsize(split_path),
                    "row_count": len(subset),
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                })

            start_time = end_time

        return split_files

    async def _split_by_id(
        self,
        file_path: str,
        id_column: str,
        ids_per_file: int = 10
    ) -> List[Dict[str, Any]]:
        """按 ID 列切分"""
        df = pd.read_csv(file_path)
        unique_ids = df[id_column].unique()

        split_files = []

        for i in range(0, len(unique_ids), ids_per_file):
            batch_ids = unique_ids[i:i + ids_per_file]
            mask = df[id_column].isin(batch_ids)
            subset = df[mask]

            file_name = f"{Path(file_path).stem}_ids_{i//ids_per_file + 1}.csv"
            split_path = self.storage_path / file_name
            subset.to_csv(split_path, index=False)

            split_files.append({
                "file_path": str(split_path),
                "file_size": os.path.getsize(split_path),
                "row_count": len(subset),
                "ids": list(batch_ids)
            })

        return split_files

    async def _split_by_rows(
        self,
        file_path: str,
        rows_per_file: int
    ) -> List[Dict[str, Any]]:
        """按行数均匀切分"""
        df = pd.read_csv(file_path)
        total_rows = len(df)

        split_files = []

        for i in range(0, total_rows, rows_per_file):
            subset = df.iloc[i:i + rows_per_file]

            file_name = f"{Path(file_path).stem}_part_{i // rows_per_file + 1}.csv"
            split_path = self.storage_path / file_name
            subset.to_csv(split_path, index=False)

            split_files.append({
                "file_path": str(split_path),
                "file_size": os.path.getsize(split_path),
                "row_count": len(subset),
                "row_range": {
                    "start": i,
                    "end": min(i + rows_per_file, total_rows)
                }
            })

        return split_files
```

### 5.5 数据集切分服务（Python）

```python
# services/dataset_splitter.py
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

class DatasetSplitter:
    """
    数据集切分服务
    支持按时间维度、空间维度、混合维度切分
    """

    async def split(
        self,
        file_path: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        执行数据集切分

        config 示例:
        {
            "type": "time",  # 或 "space" 或 "mixed"
            "time_column": "Timestamp",
            "splits": [
                {"name": "train", "purpose": "train", "start_date": "2025-01-01", "end_date": "2025-01-10"},
                {"name": "test", "purpose": "test", "start_date": "2025-01-11", "end_date": "2025-01-13"},
                {"name": "compare", "purpose": "compare", "start_date": "2025-01-14", "end_date": "2025-01-15"}
            ]
        }
        """
        split_type = config.get('type', 'time')

        if split_type == 'time':
            return await self.split_by_time(file_path, config)
        elif split_type == 'space':
            return await self.split_by_space(file_path, config)
        elif split_type == 'mixed':
            return await self.split_mixed(file_path, config)
        else:
            raise ValueError(f"Unknown split type: {split_type}")

    async def split_by_time(
        self,
        file_path: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """按时间维度切分"""
        df = pd.read_csv(file_path)
        time_column = config['time_column']
        df[time_column] = pd.to_datetime(df[time_column])

        results = []

        for split_config in config['splits']:
            start_date = pd.to_datetime(split_config['start_date'])
            end_date = pd.to_datetime(split_config['end_date'])

            mask = (df[time_column] >= start_date) & (df[time_column] <= end_date)
            subset = df[mask]

            results.append({
                "name": split_config['name'],
                "purpose": split_config['purpose'],
                "row_count": len(subset),
                "data": subset,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            })

        return results

    async def split_by_space(
        self,
        file_path: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """按空间维度切分（如按建筑ID）"""
        df = pd.read_csv(file_path)
        id_column = config['id_column']

        results = []

        for split_config in config['splits']:
            ids = split_config['ids']
            mask = df[id_column].isin(ids)
            subset = df[mask]

            results.append({
                "name": split_config['name'],
                "purpose": split_config['purpose'],
                "row_count": len(subset),
                "data": subset,
                "ids": ids
            })

        return results

    async def split_mixed(
        self,
        file_path: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """混合维度切分"""
        # 先按空间切分，再在每个子集中按时间切分
        # 或先按时间切分，再按空间切分
        df = pd.read_csv(file_path)
        time_column = config['time_column']
        id_column = config['id_column']

        df[time_column] = pd.to_datetime(df[time_column])

        results = []

        for split_config in config['splits']:
            # 时间过滤
            start_date = pd.to_datetime(split_config['start_date'])
            end_date = pd.to_datetime(split_config['end_date'])
            time_mask = (df[time_column] >= start_date) & (df[time_column] <= end_date)

            # 空间过滤
            ids = split_config.get('ids', df[id_column].unique().tolist())
            space_mask = df[id_column].isin(ids)

            # 组合过滤
            subset = df[time_mask & space_mask]

            results.append({
                "name": split_config['name'],
                "purpose": split_config['purpose'],
                "row_count": len(subset),
                "data": subset,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "ids": ids
            })

        return results
```

---

## 6. 数据库设计

### 6.1 数据库 Schema

```sql
-- 实验表
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dataset_id UUID REFERENCES datasets(id),
    config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

-- 数据集表
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    row_count INTEGER,
    column_count INTEGER,
    columns_info JSONB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 训练指标表
CREATE TABLE training_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id),
    iteration INTEGER NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(experiment_id, iteration, metric_name)
);

-- 特征重要性表
CREATE TABLE feature_importance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id),
    feature_name VARCHAR(255) NOT NULL,
    importance FLOAT NOT NULL,
    rank INTEGER
);

-- 模型表
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id),
    file_path VARCHAR(500) NOT NULL,
    format VARCHAR(20) NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 训练日志表
CREATE TABLE training_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20),
    message TEXT
);

-- 数据集子集表 (支持数据集切分)
CREATE TABLE dataset_subsets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_dataset_id UUID REFERENCES datasets(id),
    name VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL,  -- 'train', 'test', 'compare', 'transfer_source', 'transfer_target'
    file_path VARCHAR(500) NOT NULL,
    row_count INTEGER,
    split_config JSONB,            -- 切分配置信息
    date_range DATERANGE,          -- 时间范围 (时间切分)
    space_ids TEXT[],              -- ID列表 (空间切分)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 特征工程配置表
CREATE TABLE feature_engineering_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id),
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,         -- 特征工程配置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 特征工程结果表
CREATE TABLE feature_engineering_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES feature_engineering_configs(id),
    dataset_id UUID REFERENCES datasets(id),
    original_columns TEXT[],
    processed_columns TEXT[],
    new_features TEXT[],
    processed_file_path VARCHAR(500),
    row_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 迁移学习实验表
CREATE TABLE transfer_learning_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    source_model_id UUID REFERENCES models(id),
    source_dataset_id UUID REFERENCES datasets(id),
    target_dataset_id UUID REFERENCES datasets(id),
    strategy VARCHAR(50) NOT NULL, -- 'direct', 'finetune', 'align'
    config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP
);

-- 迁移学习结果表
CREATE TABLE transfer_learning_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_experiment_id UUID REFERENCES transfer_learning_experiments(id),
    rmse FLOAT,
    mae FLOAT,
    r2 FLOAT,
    mape FLOAT,
    baseline_comparison JSONB,     -- 与基线模型的对比
    predictions_path VARCHAR(500), -- 预测结果文件路径
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_created ON experiments(created_at DESC);
CREATE INDEX idx_metrics_experiment ON training_metrics(experiment_id, iteration);
CREATE INDEX idx_logs_experiment ON training_logs(experiment_id, timestamp);
CREATE INDEX idx_subsets_parent ON dataset_subsets(parent_dataset_id);
CREATE INDEX idx_subsets_purpose ON dataset_subsets(purpose);
CREATE INDEX idx_transfer_status ON transfer_learning_experiments(status);

-- ============================================
-- 新增功能表结构 (v1.2)
-- ============================================

-- 模型版本表
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES models(id) ON DELETE CASCADE,
    version_number VARCHAR(50) NOT NULL,      -- 版本号，如 v1.0.0
    version_name VARCHAR(255),                 -- 版本名称
    description TEXT,                          -- 版本描述
    config_snapshot JSONB NOT NULL,            -- 训练配置快照
    metrics_snapshot JSONB,                    -- 性能指标快照
    tags TEXT[],                               -- 标签，如 ['production', 'best']
    is_active BOOLEAN DEFAULT true,            -- 是否激活
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, version_number)
);

-- 数据质量报告表
CREATE TABLE data_quality_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    report_type VARCHAR(50) DEFAULT 'full',    -- full, quick, custom
    overall_score FLOAT,                       -- 总体质量评分 0-100
    completeness_score FLOAT,                  -- 完整性评分
    accuracy_score FLOAT,                      -- 准确性评分
    consistency_score FLOAT,                   -- 一致性评分
    distribution_score FLOAT,                  -- 分布评分
    issues JSONB,                              -- 检测到的问题列表
    recommendations JSONB,                     -- 改进建议
    column_stats JSONB,                        -- 各列统计信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据质量问题表
CREATE TABLE data_quality_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES data_quality_reports(id) ON DELETE CASCADE,
    column_name VARCHAR(255),                  -- 问题所在列
    issue_type VARCHAR(100) NOT NULL,          -- 问题类型
    severity VARCHAR(20) NOT NULL,             -- 严重程度: critical, warning, info
    description TEXT NOT NULL,                 -- 问题描述
    affected_rows INTEGER,                     -- 受影响行数
    affected_percentage FLOAT,                 -- 受影响比例
    suggestion TEXT,                           -- 修复建议
    is_resolved BOOLEAN DEFAULT false,         -- 是否已解决
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SHAP 分析结果表
CREATE TABLE shap_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,        -- summary, force, dependence, waterfall
    config JSONB,                              -- 分析配置
    result_data JSONB NOT NULL,                -- 分析结果数据
    plot_path VARCHAR(500),                    -- 图表文件路径
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SHAP 特征贡献表
CREATE TABLE shap_feature_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shap_result_id UUID REFERENCES shap_results(id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    mean_abs_shap FLOAT,                       -- 平均绝对SHAP值
    shap_values JSONB,                         -- 各样本的SHAP值
    feature_index INTEGER,                     -- 特征索引
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- GPU 配置表
CREATE TABLE gpu_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,                -- 配置名称
    device_type VARCHAR(20) NOT NULL,          -- cpu, cuda, rocm
    device_ids INTEGER[],                      -- GPU设备ID列表
    memory_limit BIGINT,                       -- 内存限制 (MB)
    auto_fallback BOOLEAN DEFAULT true,        -- 自动回退到CPU
    is_default BOOLEAN DEFAULT false,          -- 是否默认配置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统GPU状态表
CREATE TABLE gpu_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id INTEGER NOT NULL,                -- GPU设备ID
    device_name VARCHAR(255),                  -- 设备名称
    total_memory BIGINT,                       -- 总内存 (MB)
    free_memory BIGINT,                        -- 空闲内存 (MB)
    utilization FLOAT,                         -- GPU利用率
    temperature INTEGER,                       -- 温度 (摄氏度)
    is_available BOOLEAN DEFAULT true,         -- 是否可用
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 新增索引
CREATE INDEX idx_model_versions_model ON model_versions(model_id);
CREATE INDEX idx_model_versions_tags ON model_versions USING GIN(tags);
CREATE INDEX idx_quality_reports_dataset ON data_quality_reports(dataset_id);
CREATE INDEX idx_quality_issues_report ON data_quality_issues(report_id);
CREATE INDEX idx_shap_results_experiment ON shap_results(experiment_id);
CREATE INDEX idx_gpu_status_device ON gpu_status(device_id);
```

### 6.2 Redis 数据结构

```
# 训练进度缓存
training:{experiment_id}:progress
  - current_iteration
  - total_iterations
  - status
  - started_at
  TTL: 24h

# 实时指标缓存
training:{experiment_id}:metrics
  - JSON 数组，存储最近 100 条指标

# 训练队列
training:queue
  - LPUSH/RPOP 操作

# 发布订阅频道
training:{experiment_id}:updates
  - 实时推送训练事件

# 大文件上传进度
upload:{upload_id}:progress
  - total_chunks
  - uploaded_chunks
  - file_size
  - status
  TTL: 24h

# 数据集切分任务缓存
dataset_split:{split_id}:status
  - status
  - progress
  - result
  TTL: 48h

# 特征工程任务缓存
feature_eng:{task_id}:status
  - status
  - progress
  - result
  TTL: 48h

# 迁移学习任务缓存
transfer:{task_id}:status
  - status
  - progress
  - result
  TTL: 48h

# ============================================
# 新增功能缓存结构 (v1.2)
# ============================================

# 模型版本缓存
model:{model_id}:versions
  - JSON 数组，存储版本列表
  TTL: 1h

# 数据质量检测任务缓存
quality_check:{check_id}:status
  - status
  - progress
  - result
  TTL: 24h

# 数据质量报告缓存
quality_report:{dataset_id}:latest
  - JSON 对象，存储最新报告
  TTL: 1h

# SHAP 分析任务缓存
shap:{analysis_id}:status
  - status
  - progress
  - result_path
  TTL: 48h

# SHAP 结果缓存
shap:{experiment_id}:result
  - JSON 对象，存储分析结果
  TTL: 24h

# GPU 状态缓存
gpu:status
  - JSON 数组，存储所有GPU状态
  TTL: 1min

# GPU 使用情况
gpu:{device_id}:usage
  - current_task
  - memory_used
  - started_at
  TTL: 5min
```

---

## 7. 容器化部署

### 7.1 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://api:4000
    depends_on:
      - api

  # API 服务
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/xgboost_vis
      - REDIS_URL=redis://redis:6379
      - PYTHON_SERVICE_URL=http://trainer:8000
    depends_on:
      - postgres
      - redis
      - trainer

  # 训练服务
  trainer:
    build:
      context: ./trainer
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - STORAGE_PATH=/data
    volumes:
      - model-storage:/data/models
      - dataset-storage:/data/datasets
    depends_on:
      - redis

  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=xgboost_vis
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  # MinIO (可选，用于对象存储)
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio-data:/data

volumes:
  postgres-data:
  redis-data:
  model-storage:
  dataset-storage:
  minio-data:
```

### 7.2 前端 Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

### 7.3 API Dockerfile

```dockerfile
# api/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 4000
CMD ["node", "dist/index.js"]
```

### 7.4 训练服务 Dockerfile

```dockerfile
# trainer/Dockerfile
FROM python:3.11-slim
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.5 训练服务 Dockerfile (GPU 支持)

```dockerfile
# trainer/Dockerfile.gpu
FROM nvidia/cuda:11.8-cudnn8-runtime-ubuntu22.04

# 安装 Python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖 (包含 GPU 版本 XGBoost)
COPY requirements-gpu.txt .
RUN pip3 install --no-cache-dir -r requirements-gpu.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.6 Docker Compose (GPU 支持)

```yaml
# docker-compose.gpu.yml
version: '3.8'

services:
  # 训练服务 (GPU 版本)
  trainer:
    build:
      context: ./trainer
      dockerfile: Dockerfile.gpu
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - STORAGE_PATH=/app/data
      - CUDA_VISIBLE_DEVICES=0,1  # 可见GPU列表
    volumes:
      - model-storage:/app/data/models
      - dataset-storage:/app/data/datasets
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    depends_on:
      - redis
```

---

## 8. 性能优化策略

### 8.1 前端优化

| 优化项 | 策略 |
|--------|------|
| 代码分割 | 按路由懒加载，减小初始包体积 |
| 图表渲染 | 使用虚拟化处理大数据量，限制实时数据点数量 |
| WebSocket | 断线重连、心跳检测、消息节流 |
| 缓存策略 | TanStack Query 缓存实验列表、数据集信息 |

### 8.2 后端优化

| 优化项 | 策略 |
|--------|------|
| 数据库查询 | 索引优化、分页查询、避免 N+1 |
| 文件上传 | 流式处理、分块上传、压缩传输 |
| 训练队列 | 使用 Redis 队列，支持并发训练 |
| 缓存 | Redis 缓存热点数据 |

### 8.3 训练服务优化

| 优化项 | 策略 |
|--------|------|
| 内存管理 | 数据分块加载，避免全量加载 |
| GPU 支持 | 可选 CUDA 加速 |
| 并行训练 | 多进程处理，资源隔离 |

---

## 9. 安全设计

### 9.1 认证授权

```typescript
// 简单的 JWT 认证中间件
// middleware/auth.ts
export function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({ error: '未授权' });
  }

  try {
    const payload = verifyJwt(token);
    req.user = payload;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Token 无效' });
  }
}
```

### 9.2 输入验证

```typescript
// 使用 Zod 进行输入验证
const CreateExperimentSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().max(1000).optional(),
  datasetId: z.string().uuid(),
  config: z.object({
    learningRate: z.number().min(0.001).max(1),
    maxDepth: z.number().int().min(1).max(15),
    nEstimators: z.number().int().min(10).max(10000),
    // ...
  }),
});
```

### 9.3 文件安全

- 文件类型白名单检查
- 文件大小限制
- 文件名消毒
- 存储路径隔离

---

## 10. 监控与日志

### 10.1 日志规范

```
[时间戳] [级别] [服务] [请求ID] 消息内容
```

示例：
```
[2026-03-23 10:30:45.123] [INFO] [api] [req-123] 开始训练实验 exp-456
[2026-03-23 10:30:46.234] [DEBUG] [trainer] [req-123] 加载数据集: 7200 行
[2026-03-23 10:35:12.456] [INFO] [api] [req-123] 训练完成 exp-456
```

### 10.2 健康检查

```typescript
// 健康检查端点
app.get('/health', async (req, res) => {
  const checks = {
    database: await checkDatabase(),
    redis: await checkRedis(),
    trainer: await checkTrainerService(),
  };

  const healthy = Object.values(checks).every(Boolean);

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'unhealthy',
    checks,
    timestamp: new Date().toISOString(),
  });
});
```

---

## 11. 开发环境配置

### 11.1 环境变量

```bash
# .env.example

# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/xgboost_vis

# Redis
REDIS_URL=redis://localhost:6379

# 服务地址
API_URL=http://localhost:4000
FRONTEND_URL=http://localhost:3000
PYTHON_SERVICE_URL=http://localhost:8000

# 存储
STORAGE_TYPE=local  # local | s3 | minio
STORAGE_PATH=./data

# 安全
JWT_SECRET=your-secret-key
```

### 11.2 本地开发脚本

```json
// package.json (root)
{
  "scripts": {
    "dev": "concurrently \"npm run dev:api\" \"npm run dev:frontend\" \"npm run dev:trainer\"",
    "dev:api": "cd api && npm run dev",
    "dev:frontend": "cd frontend && npm run dev",
    "dev:trainer": "cd trainer && uvicorn app.main:app --reload",
    "docker:up": "docker-compose up -d",
    "docker:down": "docker-compose down",
    "db:migrate": "cd api && npm run migrate",
    "db:seed": "cd api && npm run seed"
  }
}
```

---

**文档版本**：1.3
**创建日期**：2026-03-23
**更新日期**：2026-03-23
**状态**：待评审

### 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.3 | 2026-03-23 | 新增模型版本管理、数据质量检测、SHAP分析、GPU加速支持的数据库Schema和服务设计 |
| 1.2 | 2026-03-23 | 重构为 Monorepo 架构，新增共享包设计，更新项目结构 |
| 1.1 | 2026-03-23 | 新增数据集切分、特征工程、迁移学习架构；新增大文件切分服务；更新数据库Schema |
| 1.0 | 2026-03-23 | 初始版本 |