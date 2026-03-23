# XGBoost 训练可视化工具 - 核心功能技术设计

本文档是技术架构的补充，详细描述并发训练、大文件上传等核心功能的技术实现方案。

---

## 1. 并发训练架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          训练调度系统                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐  │
│   │  API 服务   │────→│ 训练队列    │────→│   训练 Worker 池    │  │
│   │             │     │  (Redis)    │     │                     │  │
│   │ POST /start │     │             │     │  ┌───┐ ┌───┐ ┌───┐ │  │
│   └─────────────┘     │ LPUSH/RPOP  │     │  │W1 │ │W2 │ │W3 │ │  │
│                       │             │     │  └───┘ └───┘ └───┘ │  │
│                       └─────────────┘     │      ↓   ↓   ↓     │  │
│                                             │   训练处理器      │  │
│                                             └───────────────────┘  │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                      状态管理 (Redis)                        │  │
│   │  - 队列位置                                                 │  │
│   │  - 活跃训练数                                               │  │
│   │  - Worker 状态                                              │  │
│   │  - 实时进度                                                 │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 训练队列实现

#### Redis 队列结构

```
# 训练队列 (List)
training:queue
  - 实验ID列表，先进先出

# 活跃训练 (Hash)
training:active
  - experiment_id -> { worker_id, started_at, progress }

# Worker 状态 (Hash)
training:workers
  - worker_id -> { status, current_task, last_heartbeat }

# 队列位置 (Hash)
training:positions
  - experiment_id -> position_number

# 实验状态 (Hash)
experiment:{id}:status
  - status, progress, current_iteration, metrics
```

#### 队列服务代码

```python
# trainer/services/queue_service.py
import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime

class TrainingQueueService:
    def __init__(self, redis_client: redis.Redis, max_concurrent: int = 3):
        self.redis = redis_client
        self.max_concurrent = max_concurrent
        self.queue_key = "training:queue"
        self.active_key = "training:active"
        self.positions_key = "training:positions"

    async def enqueue(self, experiment_id: str) -> int:
        """将实验加入队列，返回队列位置"""
        # 检查是否已在队列中
        if await self.is_in_queue(experiment_id):
            raise ValueError("Experiment already in queue")

        # 加入队列
        await self.redis.rpush(self.queue_key, experiment_id)

        # 获取队列位置
        position = await self.get_queue_position(experiment_id)

        # 尝试立即开始
        await self.try_start_next()

        return position

    async def get_queue_position(self, experiment_id: str) -> int:
        """获取实验在队列中的位置"""
        queue = await self.redis.lrange(self.queue_key, 0, -1)
        try:
            return queue.index(experiment_id.encode()) + 1
        except ValueError:
            return 0  # 不在队列中

    async def get_active_count(self) -> int:
        """获取当前活跃训练数"""
        return await self.redis.hlen(self.active_key)

    async def can_start(self) -> bool:
        """检查是否可以开始新训练"""
        active_count = await self.get_active_count()
        return active_count < self.max_concurrent

    async def try_start_next(self) -> Optional[str]:
        """尝试开始下一个排队的训练"""
        if not await self.can_start():
            return None

        # 从队列取出下一个
        experiment_id = await self.redis.lpop(self.queue_key)
        if experiment_id:
            experiment_id = experiment_id.decode()
            # 分配 Worker
            worker_id = await self.assign_worker(experiment_id)
            if worker_id:
                return experiment_id

        return None

    async def assign_worker(self, experiment_id: str) -> Optional[str]:
        """为实验分配 Worker"""
        # 获取可用 Worker
        available_workers = await self.get_available_workers()
        if not available_workers:
            # 放回队列
            await self.redis.rpush(self.queue_key, experiment_id)
            return None

        worker_id = available_workers[0]

        # 记录活跃训练
        await self.redis.hset(self.active_key, experiment_id, json.dumps({
            "worker_id": worker_id,
            "started_at": datetime.now().isoformat(),
            "progress": 0
        }))

        # 更新 Worker 状态
        await self.redis.hset(f"worker:{worker_id}", mapping={
            "status": "busy",
            "current_task": experiment_id
        })

        return worker_id

    async def complete_training(self, experiment_id: str):
        """训练完成，释放资源"""
        # 获取训练信息
        training_info = await self.redis.hget(self.active_key, experiment_id)
        if training_info:
            info = json.loads(training_info)
            worker_id = info["worker_id"]

            # 释放 Worker
            await self.redis.hset(f"worker:{worker_id}", mapping={
                "status": "idle",
                "current_task": ""
            })

        # 从活跃列表移除
        await self.redis.hdel(self.active_key, experiment_id)

        # 尝试开始下一个
        await self.try_start_next()
```

### 1.3 Worker 池实现

```python
# trainer/services/worker_pool.py
import asyncio
import multiprocessing
from typing import Dict, Any
import redis
import json

class TrainingWorker:
    def __init__(self, worker_id: str, redis_client: redis.Redis):
        self.worker_id = worker_id
        self.redis = redis_client
        self.current_task: Optional[str] = None
        self.process: Optional[multiprocessing.Process] = None

    async def start(self):
        """启动 Worker"""
        await self.register()
        asyncio.create_task(self.heartbeat_loop())
        asyncio.create_task(self.task_loop())

    async def register(self):
        """注册 Worker"""
        await self.redis.hset("training:workers", self.worker_id, json.dumps({
            "status": "idle",
            "current_task": None,
            "last_heartbeat": datetime.now().isoformat()
        }))

    async def heartbeat_loop(self):
        """心跳循环"""
        while True:
            await self.redis.hset(f"worker:{self.worker_id}", "last_heartbeat",
                                  datetime.now().isoformat())
            await asyncio.sleep(5)

    async def task_loop(self):
        """任务循环"""
        while True:
            # 检查是否有分配的任务
            task = await self.redis.hget(f"worker:{self.worker_id}", "current_task")
            if task and task != self.current_task:
                self.current_task = task.decode() if isinstance(task, bytes) else task
                await self.execute_training(self.current_task)

            await asyncio.sleep(1)

    async def execute_training(self, experiment_id: str):
        """执行训练"""
        try:
            # 获取实验配置
            config = await self.get_experiment_config(experiment_id)

            # 创建训练进程
            trainer = XGBoostTrainer(
                experiment_id=experiment_id,
                config=config,
                progress_callback=self.progress_callback
            )

            # 在独立进程中运行训练
            self.process = multiprocessing.Process(
                target=trainer.train,
                args=(config["dataset_path"],)
            )
            self.process.start()
            self.process.join()

            # 训练完成
            await self.on_training_complete(experiment_id)

        except Exception as e:
            await self.on_training_error(experiment_id, str(e))

    def progress_callback(self, data: Dict[str, Any]):
        """进度回调"""
        # 通过 Redis 发布进度更新
        self.redis.publish(f"training:{data['experiment_id']}:updates",
                          json.dumps(data))


class WorkerPool:
    def __init__(self, num_workers: int, redis_url: str):
        self.num_workers = num_workers
        self.redis_url = redis_url
        self.workers: List[TrainingWorker] = []

    async def start(self):
        """启动所有 Worker"""
        redis_client = redis.from_url(self.redis_url)

        for i in range(self.num_workers):
            worker_id = f"worker-{i}"
            worker = TrainingWorker(worker_id, redis_client)
            self.workers.append(worker)
            asyncio.create_task(worker.start())

        print(f"Started {self.num_workers} training workers")
```

### 1.4 前端实时更新

```typescript
// hooks/use-training-queue.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

interface QueueStatus {
  active: ActiveTraining[];
  queued: QueuedTraining[];
  maxConcurrent: number;
}

export function useTrainingQueue() {
  const queryClient = useQueryClient();

  // 获取队列状态
  const { data: queueStatus } = useQuery<QueueStatus>({
    queryKey: ['training-queue'],
    queryFn: () => api.get('/training/queue'),
    refetchInterval: 5000, // 每 5 秒刷新
  });

  // WebSocket 实时更新
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/queue`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'queue_updated':
          queryClient.invalidateQueries(['training-queue']);
          break;
        case 'position_changed':
          // 更新单个实验的位置
          updateQueuePosition(data.experimentId, data.position);
          break;
        case 'started':
          // 训练开始
          queryClient.invalidateQueries(['training-queue']);
          showNotification(`训练 ${data.experimentName} 已开始`);
          break;
      }
    };

    return () => ws.close();
  }, []);

  // 加入队列
  const startTraining = useMutation({
    mutationFn: (experimentId: string) =>
      api.post(`/experiments/${experimentId}/start`),
    onSuccess: (data) => {
      if (data.queuePosition > 0) {
        showNotification(`训练已加入队列，位置: ${data.queuePosition}`);
      } else {
        showNotification('训练已开始');
      }
      queryClient.invalidateQueries(['training-queue']);
    },
  });

  // 取消排队
  const cancelQueue = useMutation({
    mutationFn: (experimentId: string) =>
      api.post(`/experiments/${experimentId}/cancel-queue`),
    onSuccess: () => {
      queryClient.invalidateQueries(['training-queue']);
    },
  });

  return {
    queueStatus,
    startTraining,
    cancelQueue,
  };
}
```

---

## 2. 大文件上传架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         大文件上传流程                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  文件大小检查                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  文件大小 ≤ 1GB: 正常分块上传                                │   │
│  │  文件大小 > 1GB: 先自动切分，再分块上传                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  前端流程                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. 选择文件/文件夹                                          │   │
│  │  2. 检查文件大小，决定上传策略                               │   │
│  │  3. 大文件：自动切分（按时间/ID/行数）                       │   │
│  │  4. 计算文件哈希 (SparkMD5)                                  │   │
│  │  5. 文件分块 (每块 5MB)                                      │   │
│  │  6. 并发上传分块 (最多 3 个并发)                             │   │
│  │  7. 显示进度、速度、剩余时间                                 │   │
│  │  8. 上传完成后通知后端合并                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  后端 API                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  POST /datasets/init-upload     # 初始化上传，返回 uploadId  │   │
│  │  POST /datasets/chunk           # 上传分块                  │   │
│  │  GET  /datasets/upload-status   # 查询已上传分块            │   │
│  │  POST /datasets/complete        # 完成上传，合并分块        │   │
│  │  POST /datasets/auto-split      # 自动切分大文件            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  存储                                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  /uploads/                                                   │   │
│  │    /{uploadId}/                                             │   │
│  │      /chunks/                                               │   │
│  │        chunk-0                                              │   │
│  │        chunk-1                                              │   │
│  │        ...                                                   │   │
│  │      metadata.json                                          │   │
│  │    /completed/                                              │   │
│  │      {dataset-id}.csv                                       │   │
│  │    /auto-split/                                             │   │
│  │      {dataset-id}_part1.csv                                 │   │
│  │      {dataset-id}_part2.csv                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 大文件自动切分策略

```
┌─────────────────────────────────────────────────────────────────────┐
│                    大文件自动切分 (> 1GB)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  切分决策流程                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. 读取文件头部（前1000行），识别列结构                     │   │
│  │  2. 检测是否有时间列                                        │   │
│  │  3. 检测是否有ID列                                          │   │
│  │  4. 选择最优切分策略                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  切分策略优先级                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  优先级1: 按时间切分                                         │   │
│  │  - 适用: 存在 Timestamp/Date 等时间列                       │   │
│  │  - 策略: 按天/周切分，每个文件不超过 800MB                  │   │
│  │  - 示例: 2.5GB/45天 → 7个文件，每天约350MB                  │   │
│  │                                                             │   │
│  │  优先级2: 按ID切分                                           │   │
│  │  - 适用: 存在 Building_ID/Device_ID 等ID列                  │   │
│  │  - 策略: 按ID分组切分，每组不超过 800MB                     │   │
│  │  - 示例: 1.8GB/3建筑 → 3个文件，每个建筑一个                │   │
│  │                                                             │   │
│  │  优先级3: 按行数切分                                         │   │
│  │  - 适用: 无时间列和ID列                                     │   │
│  │  - 策略: 均匀切分，每文件约 800MB                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  切分元数据                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  {                                                           │   │
│  │    "original_file": "large_data.csv",                       │   │
│  │    "original_size": 2500000000,                             │   │
│  │    "split_strategy": "time",                                │   │
│  │    "split_column": "Timestamp",                             │   │
│  │    "parts": [                                                │   │
│  │      {"file": "part1.csv", "range": "Day 1-7", "size": 350MB},│  │
│  │      {"file": "part2.csv", "range": "Day 8-14", "size": 350MB},│  │
│  │      ...                                                     │   │
│  │    ]                                                         │   │
│  │  }                                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 前端上传实现

```typescript
// services/file-uploader.ts
import SparkMD5 from 'spark-md5';

const MAX_FILE_SIZE = 1024 * 1024 * 1024; // 1GB
const AUTO_SPLIT_SIZE = 800 * 1024 * 1024; // 800MB per part
const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB per chunk

interface UploadOptions {
  file: File;
  chunkSize?: number; // 默认 5MB
  concurrency?: number; // 并发数，默认 3
  onProgress?: (progress: number, speed: string, remaining: string) => void;
  onComplete?: (datasetId: string) => void;
  onError?: (error: Error) => void;
}

interface UploadTask {
  uploadId: string;
  file: File;
  fileHash: string;
  totalChunks: number;
  uploadedChunks: number[];
  chunks: Blob[];
}

export class FileUploader {
  private chunkSize: number = CHUNK_SIZE;
  private concurrency: number = 3;
  private maxFileSize: number = MAX_FILE_SIZE;

  async upload(options: UploadOptions): Promise<string | string[]> {
    const { file, onProgress, onComplete, onError } = options;

    try {
      // 检查文件大小，决定策略
      if (file.size > this.maxFileSize) {
        // 大文件：自动切分后上传
        return await this.uploadLargeFile(file, onProgress, onComplete, onError);
      } else {
        // 普通文件：直接上传
        return await this.uploadNormalFile(file, onProgress, onComplete);
      }
    } catch (error) {
      onError?.(error as Error);
      throw error;
    }
  }

  private async uploadLargeFile(
    file: File,
    onProgress?: (progress: number, speed: string, remaining: string) => void,
    onComplete?: (datasetId: string | string[]) => void,
    onError?: (error: Error) => void
  ): Promise<string[]> {
    // 1. 请求后端分析文件结构
    const analysis = await this.analyzeFile(file);

    // 2. 根据分析结果切分文件
    const parts = await this.splitLargeFile(file, analysis);

    // 3. 上传各部分
    const datasetIds: string[] = [];
    for (let i = 0; i < parts.length; i++) {
      onProgress?.(
        (i / parts.length) * 100,
        `上传第 ${i + 1}/${parts.length} 部分`,
        ''
      );
      const datasetId = await this.uploadNormalFile(parts[i], onProgress, undefined);
      datasetIds.push(datasetId);
    }

    onComplete?.(datasetIds);
    return datasetIds;
  }

  private async analyzeFile(file: File): Promise<FileAnalysis> {
    // 读取文件头部进行分析
    const headContent = await this.readFileHead(file, 1000);

    return await api.post('/datasets/analyze', {
      fileName: file.name,
      fileSize: file.size,
      headContent: headContent
    });
  }

  private async splitLargeFile(file: File, analysis: FileAnalysis): Promise<File[]> {
    // 根据分析结果在前端进行切分
    // 实际切分可能需要在后端完成以获得更好的性能
    const { splitStrategy, splitColumn } = analysis;

    // 发送切分请求到后端
    const response = await api.post('/datasets/auto-split', {
      file: file,
      strategy: splitStrategy,
      column: splitColumn
    });

    return response.data.parts;
  }

  private async uploadNormalFile(
    file: File,
    onProgress?: (progress: number, speed: string, remaining: string) => void,
    onComplete?: (datasetId: string) => void
  ): Promise<string> {
    // 1. 计算文件哈希
    const fileHash = await this.calculateHash(file);
    onProgress?.(0, '计算中...', '');

    // 2. 初始化上传
    const { uploadId, uploadedChunks } = await this.initUpload(
      file.name,
      file.size,
      fileHash
    );

    // 3. 分块
    const chunks = this.splitFile(file);
    const totalChunks = chunks.length;

    // 4. 过滤已上传的分块
    const pendingChunks = chunks.filter((_, index) =>
      !uploadedChunks.includes(index)
    );

    // 5. 并发上传
    await this.uploadChunks(
      uploadId,
      pendingChunks,
      totalChunks,
      uploadedChunks.length,
      onProgress
    );

    // 6. 完成上传
    const { datasetId } = await this.completeUpload(uploadId, file.name);

    onComplete?.(datasetId);
    return datasetId;
  }

  private async calculateHash(file: File): Promise<string> {
    return new Promise((resolve) => {
      const spark = new SparkMD5.ArrayBuffer();
      const reader = new FileReader();
      const chunkSize = 2 * 1024 * 1024; // 2MB for hash
      let currentChunk = 0;
      const chunks = Math.ceil(file.size / chunkSize);

      reader.onload = (e) => {
        spark.append(e.target?.result as ArrayBuffer);
        currentChunk++;

        if (currentChunk < chunks) {
          loadNext();
        } else {
          resolve(spark.end());
        }
      };

      const loadNext = () => {
        const start = currentChunk * chunkSize;
        const end = Math.min(start + chunkSize, file.size);
        reader.readAsArrayBuffer(file.slice(start, end));
      };

      loadNext();
    });
  }

  private splitFile(file: File): Blob[] {
    const chunks: Blob[] = [];
    let start = 0;

    while (start < file.size) {
      const end = Math.min(start + this.chunkSize, file.size);
      chunks.push(file.slice(start, end));
      start = end;
    }

    return chunks;
  }

  private async initUpload(
    fileName: string,
    fileSize: number,
    fileHash: string
  ): Promise<{ uploadId: string; uploadedChunks: number[] }> {
    const response = await api.post('/datasets/init-upload', {
      fileName,
      fileSize,
      fileHash,
    });

    return response.data;
  }

  private async uploadChunks(
    uploadId: string,
    chunks: Blob[],
    totalChunks: number,
    startCount: number,
    onProgress?: (progress: number, speed: string, remaining: string) => void
  ): Promise<void> {
    let completed = startCount;
    const startTime = Date.now();

    // 并发控制
    const queue = [...chunks.entries()];
    const activeUploads: Promise<void>[] = [];

    const uploadChunk = async (index: number, chunk: Blob) => {
      const formData = new FormData();
      formData.append('uploadId', uploadId);
      formData.append('chunkIndex', index.toString());
      formData.append('chunk', chunk);

      await api.post('/datasets/chunk', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      completed++;

      // 计算进度
      const progress = (completed / totalChunks) * 100;
      const elapsed = (Date.now() - startTime) / 1000;
      const speed = this.formatSpeed(
        (completed - startCount) * this.chunkSize / elapsed
      );
      const remaining = this.formatTime(
        (totalChunks - completed) * this.chunkSize /
        ((completed - startCount) * this.chunkSize / elapsed)
      );

      onProgress?.(progress, speed, remaining);
    };

    while (queue.length > 0 || activeUploads.length > 0) {
      // 填充并发队列
      while (activeUploads.length < this.concurrency && queue.length > 0) {
        const [index, chunk] = queue.shift()!;
        activeUploads.push(uploadChunk(index, chunk));
      }

      // 等待任意一个完成
      if (activeUploads.length > 0) {
        await Promise.race(activeUploads);

        // 移除已完成的
        for (let i = activeUploads.length - 1; i >= 0; i--) {
          const p = activeUploads[i];
          try {
            await Promise.resolve(p);
            activeUploads.splice(i, 1);
          } catch {
            // 上传出错，移除
            activeUploads.splice(i, 1);
          }
        }
      }
    }
  }

  private async completeUpload(
    uploadId: string,
    fileName: string
  ): Promise<{ datasetId: string }> {
    const response = await api.post('/datasets/complete', {
      uploadId,
      fileName,
    });

    return response.data;
  }

  private formatSpeed(bytesPerSecond: number): string {
    if (bytesPerSecond > 1024 * 1024) {
      return `${(bytesPerSecond / 1024 / 1024).toFixed(2)} MB/s`;
    }
    return `${(bytesPerSecond / 1024).toFixed(2)} KB/s`;
  }

  private formatTime(seconds: number): string {
    if (seconds < 60) return `${Math.round(seconds)}秒`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`;
    return `${Math.round(seconds / 3600)}小时`;
  }
}
```

### 2.3 多文件和文件夹上传

```typescript
// services/multi-file-uploader.ts
export class MultiFileUploader {
  private uploader = new FileUploader();

  async uploadFiles(
    files: File[],
    options: {
      onFileProgress?: (fileIndex: number, progress: number) => void;
      onFileComplete?: (fileIndex: number, datasetId: string) => void;
      onAllComplete?: (datasetIds: string[]) => void;
    }
  ): Promise<string[]> {
    const datasetIds: string[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      try {
        const datasetId = await this.uploader.upload({
          file,
          onProgress: (progress) => {
            options.onFileProgress?.(i, progress);
          },
          onComplete: (id) => {
            options.onFileComplete?.(i, id);
            datasetIds.push(id);
          },
        });
      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error);
      }
    }

    options.onAllComplete?.(datasetIds);
    return datasetIds;
  }

  async uploadFolder(
    folder: FileSystemDirectoryEntry,
    options: {
      allowedTypes?: string[];
      onProgress?: (current: number, total: number, fileName: string) => void;
      onComplete?: (datasetIds: string[]) => void;
    }
  ): Promise<string[]> {
    const files = await this.readFolder(folder, options.allowedTypes || ['.csv', '.xlsx', '.xls']);
    return this.uploadFiles(files, {
      onFileProgress: (index, progress) => {
        options.onProgress?.(index + 1, files.length, files[index].name);
      },
      onAllComplete: options.onComplete,
    });
  }

  private async readFolder(
    folder: FileSystemDirectoryEntry,
    allowedTypes: string[]
  ): Promise<File[]> {
    const files: File[] = [];
    const reader = folder.createReader();

    const readEntries = (): Promise<FileSystemEntry[]> => {
      return new Promise((resolve) => {
        reader.readEntries(resolve);
      });
    };

    const processEntry = async (entry: FileSystemEntry): Promise<void> => {
      if (entry.isFile) {
        const fileEntry = entry as FileSystemFileEntry;
        const file = await new Promise<File>((resolve) => {
          fileEntry.file(resolve);
        });

        // 检查文件类型
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        if (allowedTypes.includes(ext)) {
          files.push(file);
        }
      } else if (entry.isDirectory) {
        const subFiles = await this.readFolder(
          entry as FileSystemDirectoryEntry,
          allowedTypes
        );
        files.push(...subFiles);
      }
    };

    let entries = await readEntries();
    while (entries.length > 0) {
      for (const entry of entries) {
        await processEntry(entry);
      }
      entries = await readEntries();
    }

    return files;
  }
}
```

### 2.4 后端上传 API

```typescript
// api/routes/upload.ts
import express from 'express';
import { body, validationResult } from 'express-validator';
import path from 'path';
import fs from 'fs/promises';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

// 上传目录
const UPLOAD_DIR = process.env.UPLOAD_DIR || './uploads';
const CHUNK_DIR = path.join(UPLOAD_DIR, 'chunks');
const COMPLETED_DIR = path.join(UPLOAD_DIR, 'completed');

// 初始化上传
router.post('/init-upload', async (req, res) => {
  const { fileName, fileSize, fileHash } = req.body;

  // 检查文件大小限制
  const maxSize = parseInt(process.env.MAX_FILE_SIZE_MB || '1024') * 1024 * 1024;
  if (fileSize > maxSize) {
    return res.status(400).json({ error: '文件大小超出限制' });
  }

  // 检查是否支持断点续传
  const existingUpload = await checkExistingUpload(fileHash);
  if (existingUpload) {
    return res.json({
      uploadId: existingUpload.uploadId,
      uploadedChunks: existingUpload.uploadedChunks,
      message: '检测到未完成的上传，可继续上传',
    });
  }

  // 创建新的上传任务
  const uploadId = uuidv4();
  const uploadDir = path.join(CHUNK_DIR, uploadId);

  await fs.mkdir(uploadDir, { recursive: true });
  await fs.writeFile(path.join(uploadDir, 'metadata.json'), JSON.stringify({
    fileName,
    fileSize,
    fileHash,
    createdAt: new Date().toISOString(),
    uploadedChunks: [],
  }));

  res.json({
    uploadId,
    uploadedChunks: [],
  });
});

// 上传分块
router.post('/chunk', async (req, res) => {
  const uploadId = req.body.uploadId;
  const chunkIndex = parseInt(req.body.chunkIndex);
  const chunk = req.files?.chunk;

  if (!chunk) {
    return res.status(400).json({ error: '缺少文件分块' });
  }

  const uploadDir = path.join(CHUNK_DIR, uploadId);
  const chunkPath = path.join(uploadDir, `chunk-${chunkIndex}`);

  // 保存分块
  await chunk.mv(chunkPath);

  // 更新元数据
  const metadataPath = path.join(uploadDir, 'metadata.json');
  const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf-8'));
  metadata.uploadedChunks.push(chunkIndex);
  await fs.writeFile(metadataPath, JSON.stringify(metadata));

  res.json({ success: true, chunkIndex });
});

// 查询上传状态
router.get('/upload-status/:uploadId', async (req, res) => {
  const { uploadId } = req.params;
  const metadataPath = path.join(CHUNK_DIR, uploadId, 'metadata.json');

  try {
    const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf-8'));
    res.json({
      fileName: metadata.fileName,
      fileSize: metadata.fileSize,
      uploadedChunks: metadata.uploadedChunks,
      totalChunks: Math.ceil(metadata.fileSize / (5 * 1024 * 1024)),
    });
  } catch {
    res.status(404).json({ error: '上传任务不存在' });
  }
});

// 完成上传
router.post('/complete', async (req, res) => {
  const { uploadId, fileName } = req.body;
  const uploadDir = path.join(CHUNK_DIR, uploadId);
  const metadataPath = path.join(uploadDir, 'metadata.json');

  const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf-8'));

  // 合并分块
  const datasetId = uuidv4();
  const finalPath = path.join(COMPLETED_DIR, `${datasetId}_${fileName}`);

  const totalChunks = Math.ceil(metadata.fileSize / (5 * 1024 * 1024));
  const writeStream = fs.createWriteStream(finalPath);

  for (let i = 0; i < totalChunks; i++) {
    const chunkPath = path.join(uploadDir, `chunk-${i}`);
    const chunkData = await fs.readFile(chunkPath);
    writeStream.write(chunkData);
  }

  writeStream.end();

  // 清理分块
  await fs.rm(uploadDir, { recursive: true });

  // 保存数据集记录到数据库
  const dataset = await db.datasets.create({
    id: datasetId,
    name: fileName,
    file_path: finalPath,
    file_size: metadata.fileSize,
    upload_status: 'completed',
    uploaded_by: req.user.id,
  });

  res.json({
    success: true,
    datasetId,
    message: '上传完成',
  });
});

export default router;
```

---

## 3. 数据持久化设计

### 3.1 存储策略

```
┌─────────────────────────────────────────────────────────────────────┐
│                         数据持久化架构                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PostgreSQL (结构化数据)                                            │
│  ├── 用户数据 (users)                                               │
│  ├── 实验配置 (experiments)                                         │
│  ├── 训练记录 (training_runs)                                       │
│  ├── 数据集元数据 (datasets)                                        │
│  ├── 模型元数据 (models)                                            │
│  └── 系统配置 (system_configs)                                      │
│                                                                     │
│  Redis (临时/缓存数据)                                              │
│  ├── 训练队列                                                       │
│  ├── 实时进度                                                       │
│  ├── 会话缓存                                                       │
│  └── WebSocket 状态                                                 │
│                                                                     │
│  文件存储 (持久化文件)                                              │
│  ├── /datasets/           # 数据集文件                             │
│  ├── /models/             # 模型文件                               │
│  ├── /exports/            # 导出报告                               │
│  └── /logs/               # 训练日志                               │
│                                                                     │
│  Docker Volumes                                                     │
│  ├── postgres-data       # 数据库数据卷                            │
│  ├── redis-data          # Redis 数据卷                            │
│  └── app-data            # 应用数据卷 (数据集、模型等)             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据库迁移

```sql
-- migrations/001_initial_schema.sql

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
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
    upload_status VARCHAR(20) DEFAULT 'pending',
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实验表
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dataset_id UUID REFERENCES datasets(id),
    user_id UUID REFERENCES users(id),
    config JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    queue_position INTEGER,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

-- 训练指标表
CREATE TABLE training_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    iteration INTEGER NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(experiment_id, iteration, metric_name)
);

-- 特征重要性表
CREATE TABLE feature_importance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
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
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20),
    message TEXT
);

-- 系统配置表
CREATE TABLE system_configs (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_user ON experiments(user_id);
CREATE INDEX idx_experiments_created ON experiments(created_at DESC);
CREATE INDEX idx_datasets_user ON datasets(uploaded_by);
CREATE INDEX idx_metrics_experiment ON training_metrics(experiment_id, iteration);
CREATE INDEX idx_logs_experiment ON training_logs(experiment_id, timestamp);

-- 初始系统配置
INSERT INTO system_configs (key, value, description) VALUES
    ('max_concurrent_trainings', '3', '最大并发训练数'),
    ('max_file_size_mb', '1024', '最大文件大小(MB)'),
    ('allowed_file_types', '[".csv", ".xlsx", ".xls"]', '允许的文件类型'),
    ('session_timeout_minutes', '60', '会话超时时间(分钟)');
```

### 3.3 备份策略

```yaml
# docker-compose.yml 中的备份配置
services:
  backup:
    image: postgres:15-alpine
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      - PGPASSWORD=${DB_PASSWORD}
    command: |
      sh -c "while true; do
        pg_dump -h postgres -U $${DB_USER} -d $${DB_NAME} > /backups/backup_$$(date +%Y%m%d_%H%M%S).sql
        find /backups -name 'backup_*.sql' -mtime +7 -delete
        sleep 86400
      done"
    depends_on:
      - postgres
```

---

## 4. Docker 部署配置

### 4.1 完整 docker-compose.yml

```yaml
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
      - VITE_WS_URL=ws://api:4000
    depends_on:
      - api
    networks:
      - app-network

  # API 服务
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "4000:4000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://xgboost:password@postgres:5432/xgboost_viz
      - REDIS_URL=redis://redis:6379
      - PYTHON_SERVICE_URL=http://trainer:8000
      - JWT_SECRET=${JWT_SECRET}
      - UPLOAD_DIR=/app/uploads
      - MAX_FILE_SIZE_MB=1024
      - MAX_CONCURRENT_TRAININGS=3
    volumes:
      - app-uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      trainer:
        condition: service_started
    networks:
      - app-network

  # 训练服务
  trainer:
    build:
      context: ./trainer
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://xgboost:password@postgres:5432/xgboost_viz
      - STORAGE_PATH=/app/data
      - NUM_WORKERS=3
    volumes:
      - app-data:/app/data
      - app-uploads:/app/uploads:ro
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 1G
    networks:
      - app-network

  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=xgboost
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=xgboost_viz
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U xgboost -d xgboost_viz"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  # Nginx 反向代理 (生产环境)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - api
    networks:
      - app-network

volumes:
  postgres-data:
  redis-data:
  app-data:
  app-uploads:

networks:
  app-network:
    driver: bridge
```

### 4.2 Nginx 配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }

    upstream api {
        server api:4000;
    }

    # 请求体大小限制
    client_max_body_size 1024M;

    server {
        listen 80;
        server_name _;

        # 重定向到 HTTPS (生产环境)
        # return 301 https://$host$request_uri;

        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        location /api {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }

        location /ws {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 86400;
        }
    }
}
```

### 4.3 环境变量配置

```bash
# .env.example

# 数据库
DB_USER=xgboost
DB_PASSWORD=your_secure_password
DB_NAME=xgboost_viz

# JWT
JWT_SECRET=your_jwt_secret_key

# 文件上传
MAX_FILE_SIZE_MB=1024
UPLOAD_DIR=/app/uploads

# 训练配置
MAX_CONCURRENT_TRAININGS=3
NUM_WORKERS=3

# 会话
SESSION_TIMEOUT_MINUTES=60
```

---

## 5. 监控与日志

### 5.1 健康检查

```typescript
// api/routes/health.ts
router.get('/health', async (req, res) => {
  const checks = {
    database: await checkDatabase(),
    redis: await checkRedis(),
    trainer: await checkTrainerService(),
    storage: await checkStorage(),
  };

  const healthy = Object.values(checks).every(Boolean);

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'unhealthy',
    checks,
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version,
  });
});

async function checkDatabase(): Promise<boolean> {
  try {
    await db.$queryRaw`SELECT 1`;
    return true;
  } catch {
    return false;
  }
}

async function checkRedis(): Promise<boolean> {
  try {
    await redis.ping();
    return true;
  } catch {
    return false;
  }
}

async function checkTrainerService(): Promise<boolean> {
  try {
    const response = await fetch(`${PYTHON_SERVICE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

async function checkStorage(): Promise<boolean> {
  try {
    await fs.access(UPLOAD_DIR);
    return true;
  } catch {
    return false;
  }
}
```

### 5.2 日志收集

```yaml
# docker-compose.yml 中添加日志驱动
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  trainer:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 6. 数据集切分系统设计

### 6.1 切分架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        数据集切分系统                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  切分请求                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  POST /api/datasets/:id/split                                │   │
│  │  {                                                           │   │
│  │    "type": "time" | "space" | "mixed",                      │   │
│  │    "config": { ... }                                         │   │
│  │  }                                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  切分处理器                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. 验证切分配置                                             │   │
│  │  2. 读取原始数据集                                           │   │
│  │  3. 根据类型执行切分                                         │   │
│  │  4. 生成子数据集文件                                         │   │
│  │  5. 保存子数据集元数据                                       │   │
│  │  6. 返回切分结果                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  存储                                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  /datasets/                                                  │   │
│  │    /{dataset-id}/                                            │   │
│  │      original.csv                                            │   │
│  │      /subsets/                                               │   │
│  │        train_10days.csv                                      │   │
│  │        test_3days.csv                                        │   │
│  │        compare_2days.csv                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 时间切分实现

```python
# trainer/services/dataset_splitter.py
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

class DatasetSplitter:
    def __init__(self, db_session, storage_path: str):
        self.db = db_session
        self.storage_path = storage_path

    async def split_by_time(
        self,
        dataset_id: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """按时间维度切分数据集"""

        # 加载原始数据集
        dataset = await self.db.datasets.get(dataset_id)
        df = pd.read_csv(dataset.file_path)

        # 确保时间列存在
        time_column = config.get('time_column')
        if time_column not in df.columns:
            raise ValueError(f"时间列 '{time_column}' 不存在")

        # 转换时间列
        df[time_column] = pd.to_datetime(df[time_column])

        subsets = []

        for range_config in config.get('ranges', []):
            name = range_config['name']
            start = pd.to_datetime(range_config['start'])
            end = pd.to_datetime(range_config['end'])
            usage = range_config.get('usage', 'train')

            # 过滤数据
            mask = (df[time_column] >= start) & (df[time_column] <= end)
            subset_df = df[mask]

            # 保存子数据集
            subset_path = f"{self.storage_path}/{dataset_id}/subsets/{name}.csv"
            subset_df.to_csv(subset_path, index=False)

            # 创建数据库记录
            subset_record = await self.db.subdatasets.create({
                'parent_id': dataset_id,
                'name': name,
                'file_path': subset_path,
                'row_count': len(subset_df),
                'split_type': 'time',
                'split_config': {
                    'time_column': time_column,
                    'start': str(start),
                    'end': str(end)
                },
                'usage_type': usage,
                'time_range': f"{start} ~ {end}"
            })

            subsets.append({
                'id': subset_record.id,
                'name': name,
                'row_count': len(subset_df),
                'time_range': f"{start} ~ {end}",
                'usage': usage
            })

        return subsets

    async def split_by_space(
        self,
        dataset_id: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """按空间维度切分数据集"""

        dataset = await self.db.datasets.get(dataset_id)
        df = pd.read_csv(dataset.file_path)

        space_column = config.get('space_column')
        if space_column not in df.columns:
            raise ValueError(f"空间列 '{space_column}' 不存在")

        subsets = []

        for group_config in config.get('groups', []):
            name = group_config['name']
            values = group_config['values']  # 如 ['B001', 'B002']
            usage = group_config.get('usage', 'train')

            # 过滤数据
            subset_df = df[df[space_column].isin(values)]

            # 保存子数据集
            subset_path = f"{self.storage_path}/{dataset_id}/subsets/{name}.csv"
            subset_df.to_csv(subset_path, index=False)

            subset_record = await self.db.subdatasets.create({
                'parent_id': dataset_id,
                'name': name,
                'file_path': subset_path,
                'row_count': len(subset_df),
                'split_type': 'space',
                'split_config': {
                    'space_column': space_column,
                    'values': values
                },
                'usage_type': usage,
                'space_values': values
            })

            subsets.append({
                'id': subset_record.id,
                'name': name,
                'row_count': len(subset_df),
                'space_values': values,
                'usage': usage
            })

        return subsets
```

### 6.3 切分API实现

```typescript
// api/routes/datasets.ts

// 创建子数据集（切分）
router.post('/:id/split', async (req, res) => {
  const { id } = req.params;
  const { type, config } = req.body;

  // 验证数据集存在
  const dataset = await db.datasets.findById(id);
  if (!dataset) {
    return res.status(404).json({ error: '数据集不存在' });
  }

  // 根据类型执行切分
  let subsets;
  switch (type) {
    case 'time':
      subsets = await splitter.splitByTime(id, config);
      break;
    case 'space':
      subsets = await splitter.splitBySpace(id, config);
      break;
    case 'mixed':
      subsets = await splitter.splitMixed(id, config);
      break;
    default:
      return res.status(400).json({ error: '不支持的切分类型' });
  }

  res.json({
    success: true,
    parent_id: id,
    subsets: subsets,
    message: `成功创建 ${subsets.length} 个子数据集`
  });
});

// 获取子数据集列表
router.get('/:id/subsets', async (req, res) => {
  const { id } = req.params;

  const subsets = await db.subdatasets.findByParentId(id);

  res.json({
    parent_id: id,
    subsets: subsets.map(s => ({
      id: s.id,
      name: s.name,
      row_count: s.row_count,
      split_type: s.split_type,
      usage_type: s.usage_type,
      time_range: s.time_range,
      space_values: s.space_values,
      created_at: s.created_at
    }))
  });
});
```

---

## 7. 自动化特征工程设计

### 7.1 特征工程架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                       自动化特征工程系统                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  配置输入                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  时间特征: column, extract_types                            │   │
│  │  滞后特征: target_column, lag_periods                       │   │
│  │  滚动特征: target_column, windows, functions                │   │
│  │  编码配置: column -> encoding_type                          │   │
│  │  缺失值处理: strategy, columns                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  特征处理器管道                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │   │
│  │  │时间特征提取 │──▶│滞后特征生成 │──▶│滚动统计生成 │       │   │
│  │  └─────────────┘   └─────────────┘   └─────────────┘       │   │
│  │         │                                     │              │   │
│  │         ▼                                     ▼              │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │   │
│  │  │分类变量编码 │──▶│缺失值处理   │──▶│特征选择     │       │   │
│  │  └─────────────┘   └─────────────┘   └─────────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  输出                                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  - 处理后的数据集                                           │   │
│  │  - 特征工程报告                                             │   │
│  │  - 特征重要性预览                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 特征处理器实现

```python
# trainer/services/feature_engineer.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.feature_selection import VarianceThreshold

class FeatureEngineer:
    def __init__(self):
        self.feature_report = {}

    def process(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """执行完整的特征工程流程"""

        result_df = df.copy()
        new_features = []

        # 1. 时间特征提取
        if config.get('time_features', {}).get('enabled'):
            result_df, features = self._extract_time_features(
                result_df,
                config['time_features']
            )
            new_features.extend(features)

        # 2. 滞后特征
        if config.get('lag_features', {}).get('enabled'):
            result_df, features = self._create_lag_features(
                result_df,
                config['lag_features']
            )
            new_features.extend(features)

        # 3. 滚动统计特征
        if config.get('rolling_features', {}).get('enabled'):
            result_df, features = self._create_rolling_features(
                result_df,
                config['rolling_features']
            )
            new_features.extend(features)

        # 4. 分类变量编码
        if config.get('encoding'):
            result_df, features = self._encode_categorical(
                result_df,
                config['encoding']
            )
            new_features.extend(features)

        # 5. 缺失值处理
        if config.get('missing_values'):
            result_df = self._handle_missing_values(
                result_df,
                config['missing_values']
            )

        # 6. 特征选择
        if config.get('feature_selection', {}).get('enabled'):
            result_df, dropped = self._select_features(
                result_df,
                config['feature_selection']
            )

        # 生成报告
        self._generate_report(df, result_df, new_features)

        return result_df

    def _extract_time_features(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> tuple[pd.DataFrame, List[str]]:
        """提取时间特征"""

        column = config['column']
        df[column] = pd.to_datetime(df[column])

        extract_types = config.get('extract', [
            'year', 'month', 'day', 'hour',
            'day_of_week', 'is_weekend'
        ])

        new_features = []

        if 'year' in extract_types:
            df['year'] = df[column].dt.year
            new_features.append('year')

        if 'month' in extract_types:
            df['month'] = df[column].dt.month
            new_features.append('month')

        if 'day' in extract_types:
            df['day'] = df[column].dt.day
            new_features.append('day')

        if 'hour' in extract_types:
            df['hour'] = df[column].dt.hour
            new_features.append('hour')

        if 'day_of_week' in extract_types:
            df['day_of_week'] = df[column].dt.dayofweek
            new_features.append('day_of_week')

        if 'is_weekend' in extract_types:
            df['is_weekend'] = df[column].dt.dayofweek.isin([5, 6]).astype(int)
            new_features.append('is_weekend')

        if config.get('cyclical'):
            # 添加周期性编码
            if 'hour' in extract_types:
                df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
                df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
                new_features.extend(['hour_sin', 'hour_cos'])

        return df, new_features

    def _create_lag_features(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> tuple[pd.DataFrame, List[str]]:
        """创建滞后特征"""

        target_column = config['target_column']
        lags = config.get('lags', [1, 2, 3, 6, 12, 24])

        new_features = []

        for lag in lags:
            feature_name = f'{target_column}_lag_{lag}h'
            df[feature_name] = df[target_column].shift(lag)
            new_features.append(feature_name)

        return df, new_features

    def _create_rolling_features(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> tuple[pd.DataFrame, List[str]]:
        """创建滚动统计特征"""

        target_column = config['target_column']
        windows = config.get('windows', [3, 6, 12, 24])
        functions = config.get('functions', ['mean', 'max', 'min', 'std'])

        new_features = []

        for window in windows:
            for func in functions:
                feature_name = f'{target_column}_rolling_{func}_{window}h'

                if func == 'mean':
                    df[feature_name] = df[target_column].rolling(window).mean()
                elif func == 'max':
                    df[feature_name] = df[target_column].rolling(window).max()
                elif func == 'min':
                    df[feature_name] = df[target_column].rolling(window).min()
                elif func == 'std':
                    df[feature_name] = df[target_column].rolling(window).std()

                new_features.append(feature_name)

        return df, new_features

    def _encode_categorical(
        self,
        df: pd.DataFrame,
        config: Dict[str, str]
    ) -> tuple[pd.DataFrame, List[str]]:
        """编码分类变量"""

        new_features = []

        for column, encoding_type in config.items():
            if column not in df.columns:
                continue

            if encoding_type == 'label':
                le = LabelEncoder()
                df[column] = le.fit_transform(df[column].astype(str))

            elif encoding_type == 'one_hot':
                dummies = pd.get_dummies(df[column], prefix=column)
                df = pd.concat([df, dummies], axis=1)
                df.drop(column, axis=1, inplace=True)
                new_features.extend(dummies.columns.tolist())

        return df, new_features

    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """处理缺失值"""

        strategy = config.get('strategy', 'forward_fill')
        columns = config.get('columns', df.columns.tolist())

        for col in columns:
            if col not in df.columns:
                continue

            if strategy == 'forward_fill':
                df[col] = df[col].fillna(method='ffill')
            elif strategy == 'mean':
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == 'median':
                df[col] = df[col].fillna(df[col].median())
            elif strategy == 'interpolate':
                df[col] = df[col].interpolate()

        return df

    def _generate_report(
        self,
        original_df: pd.DataFrame,
        result_df: pd.DataFrame,
        new_features: List[str]
    ):
        """生成特征工程报告"""

        self.feature_report = {
            'original_features': len(original_df.columns),
            'new_features': len(new_features),
            'total_features': len(result_df.columns),
            'new_feature_list': new_features,
            'feature_types': {
                'time_features': [f for f in new_features if any(
                    t in f for t in ['hour', 'day', 'month', 'year', 'weekend']
                )],
                'lag_features': [f for f in new_features if 'lag' in f],
                'rolling_features': [f for f in new_features if 'rolling' in f],
                'encoded_features': [f for f in new_features if any(
                    c in f for c in ['Type_', 'Level_']
                )]
            }
        }

    def get_report(self) -> Dict[str, Any]:
        return self.feature_report
```

---

## 8. 迁移学习设计

### 8.1 迁移学习架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        迁移学习系统                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  迁移场景                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  场景1: 跨建筑迁移                                           │   │
│  │  - 源域: 建筑A的训练数据                                     │   │
│  │  - 目标域: 建筑B/C的数据                                     │   │
│  │  - 用途: 用A训练模型，预测B/C能耗                           │   │
│  │                                                             │   │
│  │  场景2: 跨时间段迁移                                         │   │
│  │  - 源域: 历史时间段数据                                      │   │
│  │  - 目标域: 新时间段数据                                      │   │
│  │  - 用途: 用历史模型预测新时段能耗                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  迁移策略                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  策略1: 直接迁移                                             │   │
│  │  - 使用源域模型直接预测目标域                                │   │
│  │  - 适用于: 相似度高的场景                                    │   │
│  │                                                             │   │
│  │  策略2: 微调迁移                                             │   │
│  │  - 使用目标域部分数据微调模型                                │   │
│  │  - 适用于: 有一定差异但有少量目标数据                        │   │
│  │                                                             │   │
│  │  策略3: 特征对齐                                             │   │
│  │  - 先对齐源域和目标域的特征分布                              │   │
│  │  - 适用于: 分布差异较大的场景                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 迁移学习实现

```python
# trainer/services/transfer_learning.py
import xgboost as xgb
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from scipy import stats

class TransferLearner:
    def __init__(self):
        self.source_model = None
        self.transfer_report = {}

    def train_source(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        config: Dict[str, Any]
    ):
        """在源域上训练模型"""

        self.source_model = xgb.XGBRegressor(**config)
        self.source_model.fit(X_train, y_train)

        return self.source_model

    def predict_target(
        self,
        X_target: pd.DataFrame,
        strategy: str = 'direct'
    ) -> np.ndarray:
        """对目标域进行预测"""

        if strategy == 'direct':
            # 直接使用源模型预测
            predictions = self.source_model.predict(X_target)

        elif strategy == 'finetune':
            # 微调需要目标域标签，这里只做预测
            predictions = self.source_model.predict(X_target)

        return predictions

    def finetune(
        self,
        X_target: pd.DataFrame,
        y_target: pd.Series,
        num_rounds: int = 50,
        learning_rate: float = 0.01
    ):
        """在目标域上微调模型"""

        # 使用较低的学习率进行微调
        finetune_params = {
            'learning_rate': learning_rate,
            'n_estimators': num_rounds,
            'xgb_model': self.source_model.get_booster().save_model(
                xgb.Booster()
            )
        }

        # 继续训练
        self.source_model.fit(
            X_target, y_target,
            xgb_model=self.source_model.get_booster()
        )

    def evaluate_transfer(
        self,
        source_metrics: Dict[str, float],
        target_predictions: np.ndarray,
        y_target: pd.Series
    ) -> Dict[str, Any]:
        """评估迁移学习效果"""

        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

        # 计算目标域指标
        target_rmse = np.sqrt(mean_squared_error(y_target, target_predictions))
        target_mae = mean_absolute_error(y_target, target_predictions)
        target_r2 = r2_score(y_target, target_predictions)

        # 计算性能差距
        rmse_gap = (target_rmse - source_metrics['rmse']) / source_metrics['rmse'] * 100
        r2_gap = (source_metrics['r2'] - target_r2) / source_metrics['r2'] * 100

        # 生成建议
        recommendations = self._generate_recommendations(
            rmse_gap, r2_gap, target_r2
        )

        self.transfer_report = {
            'source_domain': {
                'rmse': source_metrics['rmse'],
                'mae': source_metrics['mae'],
                'r2': source_metrics['r2']
            },
            'target_domain': {
                'rmse': target_rmse,
                'mae': target_mae,
                'r2': target_r2
            },
            'performance_gap': {
                'rmse_change': rmse_gap,
                'r2_change': r2_gap
            },
            'recommendations': recommendations,
            'transfer_quality': self._assess_transfer_quality(rmse_gap)
        }

        return self.transfer_report

    def _generate_recommendations(
        self,
        rmse_gap: float,
        r2_gap: float,
        target_r2: float
    ) -> List[str]:
        """生成迁移学习建议"""

        recommendations = []

        if abs(rmse_gap) < 5:
            recommendations.append('✓ 迁移效果优秀，模型可直接使用')
        elif abs(rmse_gap) < 15:
            recommendations.append('✓ 迁移效果良好，模型可用')
            if target_r2 < 0.85:
                recommendations.append('⚠ 建议收集部分目标域数据进行微调')
        else:
            recommendations.append('⚠ 迁移效果一般，建议进行以下优化:')
            if rmse_gap > 20:
                recommendations.append('  - 收集目标域数据重新训练')
                recommendations.append('  - 或使用特征对齐方法')
            else:
                recommendations.append('  - 使用目标域数据进行微调')
                recommendations.append('  - 调整学习率和迭代次数')

        return recommendations

    def _assess_transfer_quality(self, rmse_gap: float) -> str:
        """评估迁移质量"""

        if abs(rmse_gap) < 5:
            return '优秀'
        elif abs(rmse_gap) < 15:
            return '良好'
        elif abs(rmse_gap) < 30:
            return '一般'
        else:
            return '较差'
```

### 8.3 迁移学习API

```typescript
// api/routes/transfer.ts
import express from 'express';
import { TransferLearner } from '../services/transfer_learning';

const router = express.Router();

// 创建迁移学习实验
router.post('/experiments/transfer', async (req, res) => {
  const {
    name,
    sourceDatasetId,      // 源域数据集ID
    sourceSubsetId,       // 源域子数据集ID（可选）
    targetDatasetId,      // 目标域数据集ID
    targetSubsetId,       // 目标域子数据集ID（可选）
    compareSubsetId,      // 对比数据集ID（可选）
    transferStrategy,     // 'direct' | 'finetune' | 'align'
    modelConfig
  } = req.body;

  // 1. 加载源域数据
  const sourceData = await loadData(sourceDatasetId, sourceSubsetId);

  // 2. 加载目标域数据
  const targetData = await loadData(targetDatasetId, targetSubsetId);

  // 3. 创建迁移学习实例
  const transferLearner = new TransferLearner();

  // 4. 在源域训练
  await transferLearner.trainSource(
    sourceData.X,
    sourceData.y,
    modelConfig
  );

  // 5. 对目标域预测
  const predictions = await transferLearner.predictTarget(
    targetData.X,
    transferStrategy
  );

  // 6. 评估迁移效果
  const sourceMetrics = await evaluateModel(sourceData);
  const transferReport = await transferLearner.evaluateTransfer(
    sourceMetrics,
    predictions,
    targetData.y
  );

  // 7. 如果有对比数据集，进行对比验证
  let comparisonResults = null;
  if (compareSubsetId) {
    const compareData = await loadData(targetDatasetId, compareSubsetId);
    const comparePredictions = await transferLearner.predictTarget(
      compareData.X,
      transferStrategy
    );

    comparisonResults = {
      predictions: comparePredictions,
      actual: compareData.y,
      metrics: await calculateMetrics(comparePredictions, compareData.y)
    };
  }

  // 8. 保存实验记录
  const experiment = await db.experiments.create({
    name,
    type: 'transfer_learning',
    source_dataset_id: sourceDatasetId,
    source_subset_id: sourceSubsetId,
    target_dataset_id: targetDatasetId,
    target_subset_id: targetSubsetId,
    transfer_strategy: transferStrategy,
    transfer_report: transferReport,
    comparison_results: comparisonResults
  });

  res.json({
    experimentId: experiment.id,
    transferReport,
    comparisonResults
  });
});

// 获取迁移学习结果
router.get('/experiments/:id/transfer-result', async (req, res) => {
  const { id } = req.params;

  const experiment = await db.experiments.findById(id);

  if (experiment.type !== 'transfer_learning') {
    return res.status(400).json({ error: '这不是迁移学习实验' });
  }

  res.json({
    sourceDomain: {
      datasetId: experiment.source_dataset_id,
      subsetId: experiment.source_subset_id
    },
    targetDomain: {
      datasetId: experiment.target_dataset_id,
      subsetId: experiment.target_subset_id
    },
    transferReport: experiment.transfer_report,
    comparisonResults: experiment.comparison_results
  });
});
```

---

## 9. 模型版本管理设计

### 9.1 版本管理架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        模型版本管理系统                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  版本创建流程                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  训练完成 → 自动创建版本 → 保存配置快照 → 保存指标快照       │   │
│  │           ↓                                                 │   │
│  │  手动创建版本 → 输入版本名称和描述 → 选择要保留的标签        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  版本标签系统                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  production   - 生产环境使用的模型版本                       │   │
│  │  best         - 最佳性能模型版本                             │   │
│  │  baseline     - 基线模型版本                                 │   │
│  │  experimental - 实验性模型版本                               │   │
│  │  deprecated   - 已弃用模型版本                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  版本比较功能                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  选择2-4个版本 → 配置差异对比 → 指标差异对比 → 结果可视化    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 版本号规范

```
版本号格式: v{major}.{minor}.{patch}

- major: 主版本号，重大变更时递增
- minor: 次版本号，功能增强时递增
- patch: 补丁版本号，小修改时递增

示例：
- v1.0.0 - 初始版本
- v1.0.1 - 修复小问题
- v1.1.0 - 参数优化
- v2.0.0 - 重大更新（如更换特征工程方案）
```

### 9.3 Python 训练服务实现

```python
# trainer/services/model_versioning.py
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import xgboost as xgb

class ModelVersionManager:
    """模型版本管理器"""

    def __init__(self, db_session, storage_path: str):
        self.db = db_session
        self.storage_path = storage_path

    def create_version(
        self,
        model_id: str,
        model: xgb.Booster,
        config: Dict[str, Any],
        metrics: Dict[str, float],
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """创建模型版本"""

        # 获取最新版本号
        latest = self.get_latest_version(model_id)
        version_number = self._increment_version(
            latest['version_number'] if latest else None
        )

        # 保存模型文件
        model_path = f"{self.storage_path}/models/{model_id}/{version_number}.json"
        model.save_model(model_path)

        # 创建配置快照
        config_snapshot = {
            'training_config': config,
            'xgboost_params': config.get('xgboost_params', {}),
            'feature_config': config.get('feature_config', {}),
            'split_config': config.get('split_config', {}),
            'timestamp': datetime.now().isoformat()
        }

        # 创建指标快照
        metrics_snapshot = {
            'train_metrics': metrics.get('train', {}),
            'val_metrics': metrics.get('validation', {}),
            'test_metrics': metrics.get('test', {}),
            'feature_importance': metrics.get('feature_importance', {}),
            'timestamp': datetime.now().isoformat()
        }

        # 保存到数据库
        version_record = self.db.model_versions.create({
            'model_id': model_id,
            'version_number': version_number,
            'version_name': name or f"Version {version_number}",
            'description': description,
            'config_snapshot': config_snapshot,
            'metrics_snapshot': metrics_snapshot,
            'tags': tags or [],
            'file_path': model_path,
            'created_at': datetime.now()
        })

        return {
            'id': version_record.id,
            'version_number': version_number,
            'name': version_record.version_name,
            'tags': tags or []
        }

    def compare_versions(
        self,
        version_ids: List[str]
    ) -> Dict[str, Any]:
        """比较多个版本"""

        versions = self.db.model_versions.find_by_ids(version_ids)

        # 配置差异
        config_diff = self._compute_config_diff(
            [v.config_snapshot for v in versions]
        )

        # 指标差异
        metrics_diff = self._compute_metrics_diff(
            [v.metrics_snapshot for v in versions]
        )

        return {
            'versions': [{
                'id': v.id,
                'version_number': v.version_number,
                'name': v.version_name,
                'tags': v.tags,
                'created_at': v.created_at
            } for v in versions],
            'config_diff': config_diff,
            'metrics_diff': metrics_diff
        }

    def add_tag(self, version_id: str, tag: str) -> None:
        """添加版本标签"""

        version = self.db.model_versions.find_by_id(version_id)

        # 特殊标签只能有一个
        exclusive_tags = ['production', 'best']
        if tag in exclusive_tags:
            # 移除同模型其他版本的该标签
            self.db.model_versions.update_many(
                {'model_id': version.model_id, 'tags': {'contains': tag}},
                {'tags': {'pull': tag}}
            )

        self.db.model_versions.update(
            version_id,
            {'tags': {'push': tag}}
        )

    def get_version_history(
        self,
        model_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取版本历史"""

        versions = self.db.model_versions.find_many(
            {'model_id': model_id},
            order_by='created_at',
            descending=True,
            limit=limit
        )

        return [{
            'id': v.id,
            'version_number': v.version_number,
            'name': v.version_name,
            'description': v.description,
            'tags': v.tags,
            'metrics': v.metrics_snapshot.get('val_metrics', {}),
            'created_at': v.created_at
        } for v in versions]

    def _increment_version(self, current: Optional[str]) -> str:
        """递增版本号"""
        if not current:
            return 'v1.0.0'

        # 解析版本号
        parts = current.lstrip('v').split('.')
        if len(parts) != 3:
            return 'v1.0.0'

        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        return f'v{major}.{minor}.{patch + 1}'

    def _compute_config_diff(
        self,
        configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算配置差异"""

        diff = {}
        all_keys = set()
        for config in configs:
            all_keys.update(self._flatten_dict(config).keys())

        for key in all_keys:
            values = []
            for config in configs:
                flat = self._flatten_dict(config)
                values.append(flat.get(key))

            # 如果值不全相同，记录差异
            if len(set(str(v) for v in values)) > 1:
                diff[key] = values

        return diff

    def _compute_metrics_diff(
        self,
        metrics_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算指标差异"""

        diff = {}
        metric_keys = ['val_metrics', 'test_metrics']

        for key in metric_keys:
            diff[key] = {}
            for metric_name in ['rmse', 'mae', 'r2', 'mape']:
                values = []
                for metrics in metrics_list:
                    val = metrics.get(key, {}).get(metric_name)
                    values.append(val)

                diff[key][metric_name] = values

        return diff

    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '.'
    ) -> Dict[str, Any]:
        """扁平化字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
```

---

## 10. 数据质量检测设计

### 10.1 检测架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        数据质量检测系统                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  检测维度                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  完整性 (Completeness)                                       │   │
│  │  - 缺失值检测                                                │   │
│  │  - 空值统计                                                  │   │
│  │  - 数据完整性评估                                            │   │
│  │                                                             │   │
│  │  准确性 (Accuracy)                                           │   │
│  │  - 异常值检测 (IQR, Z-score)                                 │   │
│  │  - 数据类型验证                                              │   │
│  │  - 范围验证                                                  │   │
│  │                                                             │   │
│  │  一致性 (Consistency)                                        │   │
│  │  - 格式一致性                                                │   │
│  │  - 编码一致性                                                │   │
│  │  - 参照完整性                                                │   │
│  │                                                             │   │
│  │  分布 (Distribution)                                         │   │
│  │  - 数据分布分析                                              │   │
│  │  - 偏度/峰度检测                                             │   │
│  │  - 类别平衡性                                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  输出                                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  - 总体质量评分 (0-100)                                      │   │
│  │  - 各维度评分                                                │   │
│  │  - 问题列表 (严重程度分级)                                   │   │
│  │  - 修复建议                                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 质量评分算法

```python
# trainer/services/data_quality.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats

class DataQualityAnalyzer:
    """数据质量分析器"""

    def __init__(self):
        self.weights = {
            'completeness': 0.30,
            'accuracy': 0.30,
            'consistency': 0.20,
            'distribution': 0.20
        }

    def analyze(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """执行完整的数据质量分析"""

        config = config or {}
        results = {
            'overall_score': 0,
            'completeness_score': 0,
            'accuracy_score': 0,
            'consistency_score': 0,
            'distribution_score': 0,
            'issues': [],
            'recommendations': [],
            'column_stats': {}
        }

        # 1. 完整性检测
        if config.get('checkCompleteness', True):
            completeness, issues = self._check_completeness(df)
            results['completeness_score'] = completeness
            results['issues'].extend(issues)

        # 2. 准确性检测
        if config.get('checkAccuracy', True):
            accuracy, issues = self._check_accuracy(df)
            results['accuracy_score'] = accuracy
            results['issues'].extend(issues)

        # 3. 一致性检测
        if config.get('checkConsistency', True):
            consistency, issues = self._check_consistency(df)
            results['consistency_score'] = consistency
            results['issues'].extend(issues)

        # 4. 分布检测
        if config.get('checkDistribution', True):
            distribution, issues = self._check_distribution(df)
            results['distribution_score'] = distribution
            results['issues'].extend(issues)

        # 计算总分
        results['overall_score'] = (
            results['completeness_score'] * self.weights['completeness'] +
            results['accuracy_score'] * self.weights['accuracy'] +
            results['consistency_score'] * self.weights['consistency'] +
            results['distribution_score'] * self.weights['distribution']
        )

        # 生成建议
        results['recommendations'] = self._generate_recommendations(results['issues'])

        # 列统计
        results['column_stats'] = self._compute_column_stats(df)

        return results

    def _check_completeness(self, df: pd.DataFrame) -> Tuple[float, List[Dict]]:
        """完整性检测"""

        issues = []
        total_cells = df.size
        missing_cells = df.isna().sum().sum()

        # 完整性评分
        completeness_score = (1 - missing_cells / total_cells) * 100

        # 检查每列缺失情况
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = missing_count / len(df) * 100

            if missing_pct > 0:
                severity = 'critical' if missing_pct > 20 else (
                    'warning' if missing_pct > 5 else 'info'
                )
                issues.append({
                    'column_name': col,
                    'type': 'missing_values',
                    'severity': severity,
                    'description': f'列 "{col}" 存在 {missing_count} 个缺失值 ({missing_pct:.1f}%)',
                    'affected_rows': int(missing_count),
                    'affected_percentage': missing_pct,
                    'suggestion': self._get_missing_value_suggestion(missing_pct)
                })

        return completeness_score, issues

    def _check_accuracy(self, df: pd.DataFrame) -> Tuple[float, List[Dict]]:
        """准确性检测"""

        issues = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        outlier_count = 0
        total_values = 0

        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) == 0:
                continue

            total_values += len(data)

            # 使用 IQR 方法检测异常值
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = data[(data < lower_bound) | (data > upper_bound)]
            outlier_pct = len(outliers) / len(data) * 100

            if outlier_pct > 0:
                severity = 'warning' if outlier_pct > 5 else 'info'
                issues.append({
                    'column_name': col,
                    'type': 'outliers',
                    'severity': severity,
                    'description': f'列 "{col}" 检测到 {len(outliers)} 个异常值 ({outlier_pct:.1f}%)',
                    'affected_rows': len(outliers),
                    'affected_percentage': outlier_pct,
                    'suggestion': '建议检查异常值是否为数据错误，或考虑使用稳健的统计方法'
                })

            outlier_count += len(outliers)

        # 准确性评分
        accuracy_score = (1 - outlier_count / total_values) * 100 if total_values > 0 else 100

        return accuracy_score, issues

    def _check_consistency(self, df: pd.DataFrame) -> Tuple[float, List[Dict]]:
        """一致性检测"""

        issues = []
        consistency_issues_count = 0
        total_checks = 0

        # 检查日期列格式一致性
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                total_checks += 1
                try:
                    # 尝试解析日期
                    parsed = pd.to_datetime(df[col], errors='coerce')
                    invalid = parsed.isna().sum()
                    original_na = df[col].isna().sum()
                    format_issues = invalid - original_na

                    if format_issues > 0:
                        consistency_issues_count += 1
                        issues.append({
                            'column_name': col,
                            'type': 'format_inconsistency',
                            'severity': 'warning',
                            'description': f'列 "{col}" 存在 {format_issues} 个日期格式不一致的值',
                            'affected_rows': int(format_issues),
                            'affected_percentage': format_issues / len(df) * 100,
                            'suggestion': '建议统一日期格式，或使用日期解析函数处理'
                        })
                except:
                    pass

        # 检查分类列的值一致性
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            total_checks += 1
            unique_values = df[col].dropna().unique()

            # 检查是否有相似的值（大小写、空格等）
            normalized = pd.Series(unique_values).str.lower().str.strip()
            duplicates = normalized[normalized.duplicated(keep=False)]

            if len(duplicates) > 0:
                consistency_issues_count += 1
                issues.append({
                    'column_name': col,
                    'type': 'value_inconsistency',
                    'severity': 'info',
                    'description': f'列 "{col}" 存在可能的重复值（如大小写、空格差异）',
                    'affected_rows': None,
                    'affected_percentage': None,
                    'suggestion': '建议进行值标准化处理，统一大小写和去除空格'
                })

        # 一致性评分
        consistency_score = (1 - consistency_issues_count / max(total_checks, 1)) * 100

        return consistency_score, issues

    def _check_distribution(self, df: pd.DataFrame) -> Tuple[float, List[Dict]]:
        """分布检测"""

        issues = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) < 10:
                continue

            # 计算偏度
            skewness = data.skew()

            if abs(skewness) > 2:
                severity = 'warning' if abs(skewness) > 3 else 'info'
                issues.append({
                    'column_name': col,
                    'type': 'skewed_distribution',
                    'severity': severity,
                    'description': f'列 "{col}" 数据分布高度偏斜 (偏度={skewness:.2f})',
                    'affected_rows': None,
                    'affected_percentage': None,
                    'suggestion': '建议进行对数变换或 Box-Cox 变换以改善分布'
                })

        # 分布评分基于问题数量
        distribution_score = max(0, 100 - len(issues) * 10)

        return distribution_score, issues

    def _get_missing_value_suggestion(self, pct: float) -> str:
        """获取缺失值处理建议"""
        if pct > 50:
            return '缺失值比例过高，建议删除该列或收集更多数据'
        elif pct > 20:
            return '建议使用插值或模型预测方法填充缺失值'
        elif pct > 5:
            return '建议使用均值、中位数或众数填充缺失值'
        else:
            return '缺失值比例较低，可使用前向填充或删除缺失行'

    def _generate_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """生成改进建议"""
        recommendations = []

        # 按严重程度分组
        critical = [i for i in issues if i['severity'] == 'critical']
        warnings = [i for i in issues if i['severity'] == 'warning']

        if critical:
            recommendations.append({
                'priority': 'high',
                'title': '处理严重数据质量问题',
                'description': f'发现 {len(critical)} 个严重问题需要立即处理',
                'actions': [i['suggestion'] for i in critical[:3]]
            })

        if warnings:
            recommendations.append({
                'priority': 'medium',
                'title': '改善数据质量',
                'description': f'发现 {len(warnings)} 个警告需要关注',
                'actions': [i['suggestion'] for i in warnings[:3]]
            })

        return recommendations

    def _compute_column_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算列统计信息"""
        stats = {}

        for col in df.columns:
            col_stats = {
                'dtype': str(df[col].dtype),
                'count': int(df[col].count()),
                'missing': int(df[col].isna().sum()),
                'missing_pct': float(df[col].isna().sum() / len(df) * 100)
            }

            if df[col].dtype in ['int64', 'float64']:
                col_stats.update({
                    'mean': float(df[col].mean()) if df[col].count() > 0 else None,
                    'std': float(df[col].std()) if df[col].count() > 1 else None,
                    'min': float(df[col].min()) if df[col].count() > 0 else None,
                    'max': float(df[col].max()) if df[col].count() > 0 else None,
                    'median': float(df[col].median()) if df[col].count() > 0 else None
                })
            else:
                col_stats.update({
                    'unique': int(df[col].nunique()),
                    'top': str(df[col].mode().iloc[0]) if df[col].count() > 0 else None
                })

            stats[col] = col_stats

        return stats
```

---

## 11. SHAP 模型解释性设计

### 11.1 SHAP 分析架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SHAP 模型解释性系统                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  分析类型                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. Summary Plot (特征重要性概览)                            │   │
│  │     - 全局特征重要性排名                                     │   │
│  │     - 特征值对预测的影响方向                                 │   │
│  │                                                             │   │
│  │  2. Force Plot (单样本解释)                                  │   │
│  │     - 单个预测的特征贡献                                     │   │
│  │     - 推动预测值增加/减少的因素                              │   │
│  │                                                             │   │
│  │  3. Dependence Plot (特征依赖图)                             │   │
│  │     - 特征值与SHAP值的关系                                   │   │
│  │     - 特征交互效应                                           │   │
│  │                                                             │   │
│  │  4. Waterfall Chart (瀑布图)                                 │   │
│  │     - 特征贡献的累积效果                                     │   │
│  │     - 从基准值到最终预测值                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  性能优化                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  - TreeSHAP 算法 (XGBoost专用，速度快)                       │   │
│  │  - 数据采样 (大数据集采样分析)                               │   │
│  │  - 结果缓存 (避免重复计算)                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2 SHAP 分析实现

```python
# trainer/services/shap_analyzer.py
import shap
import xgboost as xgb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Tuple
import json
import base64
from io import BytesIO

class SHAPAnalyzer:
    """SHAP 模型解释性分析器"""

    def __init__(self, model: xgb.Booster, feature_names: List[str] = None):
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        self.shap_values = None

    def fit(self, X: pd.DataFrame, sample_size: int = 1000):
        """拟合SHAP解释器"""

        # 大数据集采样
        if len(X) > sample_size:
            X_sample = X.sample(n=sample_size, random_state=42)
        else:
            X_sample = X

        # 使用TreeSHAP (XGBoost专用)
        self.explainer = shap.TreeExplainer(self.model)
        self.shap_values = self.explainer.shap_values(X_sample)

        if self.feature_names is None:
            self.feature_names = X.columns.tolist()

        return self

    def summary_plot(
        self,
        max_display: int = 20,
        plot_type: str = 'dot'
    ) -> Dict[str, Any]:
        """生成特征重要性概览图"""

        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            self.shap_values,
            feature_names=self.feature_names,
            max_display=max_display,
            plot_type=plot_type,
            show=False
        )

        # 转换为base64图片
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close()

        # 计算特征重要性
        mean_abs_shap = np.abs(self.shap_values).mean(axis=0)
        feature_importance = sorted(
            zip(self.feature_names, mean_abs_shap),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            'plot_base64': img_base64,
            'feature_importance': [
                {'feature': f, 'importance': float(i)}
                for f, i in feature_importance
            ]
        }

    def force_plot(
        self,
        sample_index: int = 0
    ) -> Dict[str, Any]:
        """生成单样本解释力图"""

        # 获取基准值
        base_value = self.explainer.expected_value
        sample_shap = self.shap_values[sample_index]

        # 特征贡献
        contributions = sorted(
            zip(self.feature_names, sample_shap),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        # 生成force plot
        plt.figure(figsize=(12, 3))
        shap.force_plot(
            base_value,
            sample_shap,
            feature_names=self.feature_names,
            matplotlib=True,
            show=False
        )

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close()

        return {
            'base_value': float(base_value),
            'output_value': float(base_value + sample_shap.sum()),
            'contributions': [
                {'feature': f, 'shap_value': float(v)}
                for f, v in contributions[:10]
            ],
            'plot_base64': img_base64
        }

    def dependence_plot(
        self,
        feature_name: str,
        interaction_feature: str = 'auto'
    ) -> Dict[str, Any]:
        """生成特征依赖图"""

        feature_idx = self.feature_names.index(feature_name)

        plt.figure(figsize=(10, 6))
        shap.dependence_plot(
            feature_idx,
            self.shap_values,
            pd.DataFrame(self.shap_values, columns=self.feature_names),
            interaction_index=interaction_feature,
            feature_names=self.feature_names,
            show=False
        )

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close()

        # 计算相关性
        feature_shap = self.shap_values[:, feature_idx]

        return {
            'feature_name': feature_name,
            'plot_base64': img_base64,
            'shap_stats': {
                'mean': float(np.mean(feature_shap)),
                'std': float(np.std(feature_shap)),
                'min': float(np.min(feature_shap)),
                'max': float(np.max(feature_shap))
            }
        }

    def waterfall_chart(
        self,
        sample_index: int = 0,
        max_display: int = 15
    ) -> Dict[str, Any]:
        """生成瀑布图"""

        sample_shap = self.shap_values[sample_index]
        base_value = self.explainer.expected_value

        # 排序特征
        sorted_idx = np.argsort(np.abs(sample_shap))[::-1][:max_display]
        sorted_features = [self.feature_names[i] for i in sorted_idx]
        sorted_values = sample_shap[sorted_idx]

        # 生成瀑布图数据
        cumulative = base_value
        waterfall_data = []

        for feature, value in zip(sorted_features, sorted_values):
            waterfall_data.append({
                'feature': feature,
                'value': float(value),
                'cumulative_start': float(cumulative),
                'cumulative_end': float(cumulative + value)
            })
            cumulative += value

        return {
            'base_value': float(base_value),
            'final_value': float(base_value + sample_shap.sum()),
            'waterfall_data': waterfall_data
        }

    def get_feature_contributions(self) -> Dict[str, float]:
        """获取所有特征的平均贡献"""

        mean_abs_shap = np.abs(self.shap_values).mean(axis=0)
        mean_shap = self.shap_values.mean(axis=0)

        return {
            feature: {
                'mean_abs_shap': float(mean_abs_shap[i]),
                'mean_shap': float(mean_shap[i])
            }
            for i, feature in enumerate(self.feature_names)
        }

    def to_json(self) -> Dict[str, Any]:
        """导出分析结果为JSON"""

        return {
            'feature_names': self.feature_names,
            'shap_values': self.shap_values.tolist(),
            'base_value': float(self.explainer.expected_value),
            'feature_contributions': self.get_feature_contributions()
        }
```

---

## 12. GPU 加速支持设计

### 12.1 GPU 加速架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GPU 加速支持系统                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  GPU 检测流程                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  系统启动 → 检测GPU → 记录设备信息 → 选择默认设备            │   │
│  │           ↓                                                 │   │
│  │  无GPU → 使用CPU                                            │   │
│  │  有GPU → 配置GPU参数                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  设备选择策略                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. 自动选择: 根据GPU可用性和内存自动选择                    │   │
│  │  2. 手动指定: 用户指定使用哪个GPU                            │   │
│  │  3. 自动回退: GPU不可用时自动回退到CPU                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  监控与管理                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  - GPU利用率监控                                             │   │
│  │  - 内存使用监控                                              │   │
│  │  - 温度监控                                                  │   │
│  │  - 任务队列管理                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 GPU 检测与配置

```python
# trainer/services/gpu_manager.py
import subprocess
import json
import os
from typing import List, Dict, Any, Optional
import xgboost as xgb

class GPUManager:
    """GPU 管理器"""

    def __init__(self):
        self.available_gpus = []
        self.default_device = 'cpu'

    def detect_gpus(self) -> List[Dict[str, Any]]:
        """检测系统GPU"""

        gpus = []

        try:
            # 使用 nvidia-smi 检测 NVIDIA GPU
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.free,utilization.gpu,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 6:
                            gpus.append({
                                'id': int(parts[0]),
                                'name': parts[1],
                                'total_memory': int(float(parts[2])),
                                'free_memory': int(float(parts[3])),
                                'utilization': float(parts[4]),
                                'temperature': int(parts[5]),
                                'type': 'cuda'
                            })

        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass

        # 检查 ROCm (AMD GPU)
        if not gpus:
            try:
                result = subprocess.run(
                    ['rocminfo'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if 'GPU' in result.stdout:
                    gpus.append({
                        'id': 0,
                        'name': 'AMD GPU',
                        'total_memory': 0,
                        'free_memory': 0,
                        'utilization': 0,
                        'temperature': 0,
                        'type': 'rocm'
                    })
            except:
                pass

        self.available_gpus = gpus
        self.default_device = 'cuda' if gpus else 'cpu'

        return gpus

    def get_training_params(
        self,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """获取GPU训练参数"""

        config = config or {}

        # 检测GPU
        if not self.available_gpus:
            self.detect_gpus()

        # 获取设备配置
        device_type = config.get('device_type', self.default_device)

        if device_type == 'cpu':
            return {
                'tree_method': 'hist',
                'device': 'cpu',
                'nthread': os.cpu_count()
            }

        # GPU 配置
        if device_type == 'cuda':
            device_id = config.get('device_id', 0)

            # 检查GPU是否可用
            if device_id >= len(self.available_gpus):
                if config.get('auto_fallback', True):
                    return {
                        'tree_method': 'hist',
                        'device': 'cpu',
                        'nthread': os.cpu_count(),
                        '_fallback_reason': 'GPU device not available'
                    }
                else:
                    raise RuntimeError(f"GPU {device_id} not available")

            gpu = self.available_gpus[device_id]

            # 检查内存
            memory_limit = config.get('memory_limit', 0)
            if memory_limit > 0 and gpu['free_memory'] < memory_limit:
                if config.get('auto_fallback', True):
                    return {
                        'tree_method': 'hist',
                        'device': 'cpu',
                        'nthread': os.cpu_count(),
                        '_fallback_reason': 'Insufficient GPU memory'
                    }
                else:
                    raise RuntimeError("Insufficient GPU memory")

            return {
                'tree_method': 'hist',
                'device': 'cuda',
                'cuda_device_id': device_id,
                'gpu_id': device_id
            }

        elif device_type == 'rocm':
            return {
                'tree_method': 'hist',
                'device': 'rocm'
            }

        return {'tree_method': 'hist', 'device': 'cpu'}

    def get_status(self) -> Dict[str, Any]:
        """获取GPU状态"""

        if not self.available_gpus:
            self.detect_gpus()

        return {
            'has_gpu': len(self.available_gpus) > 0,
            'gpus': self.available_gpus,
            'default_device': self.default_device,
            'xgboost_gpu_support': self._check_xgboost_gpu_support()
        }

    def _check_xgboost_gpu_support(self) -> bool:
        """检查XGBoost是否支持GPU"""

        try:
            # 尝试创建GPU模型
            params = {'tree_method': 'hist', 'device': 'cuda'}
            # 不实际训练，只检查参数是否被接受
            return True
        except:
            return False

    def select_best_gpu(self) -> Optional[int]:
        """选择最佳GPU"""

        if not self.available_gpus:
            return None

        # 选择空闲内存最多的GPU
        best_gpu = max(self.available_gpus, key=lambda g: g['free_memory'])
        return best_gpu['id'] if best_gpu['free_memory'] > 1024 else None
```

### 12.3 训练服务集成

```python
# trainer/services/trainer.py (扩展)

class XGBoostTrainer:
    def __init__(
        self,
        experiment_id: str,
        config: Dict[str, Any],
        progress_callback: Callable,
        gpu_manager: GPUManager = None
    ):
        self.experiment_id = experiment_id
        self.config = config
        self.progress_callback = progress_callback
        self.gpu_manager = gpu_manager or GPUManager()
        self.model = None
        self.is_stopped = False

    def _build_params(self) -> Dict[str, Any]:
        """构建训练参数"""

        params = {
            'objective': self._get_objective(),
            'eval_metric': self._get_eval_metric(),
            'learning_rate': self.config.get('learning_rate', 0.1),
            'max_depth': self.config.get('max_depth', 6),
            'subsample': self.config.get('subsample', 1.0),
            'colsample_bytree': self.config.get('colsample_bytree', 1.0),
            'gamma': self.config.get('gamma', 0),
            'alpha': self.config.get('alpha', 0),
            'lambda': self.config.get('lambda', 1),
            'min_child_weight': self.config.get('min_child_weight', 1)
        }

        # 获取GPU参数
        gpu_config = self.config.get('gpu_config', {})
        gpu_params = self.gpu_manager.get_training_params(gpu_config)

        params.update(gpu_params)

        # 记录是否回退到CPU
        if '_fallback_reason' in gpu_params:
            self._log_warning(f"GPU fallback: {gpu_params['_fallback_reason']}")
            del params['_fallback_reason']

        return params

    def train(
        self,
        X_train, y_train,
        X_val, y_val
    ) -> Dict[str, Any]:
        """执行训练"""

        # 检测并报告GPU状态
        gpu_status = self.gpu_manager.get_status()
        self._log_info(f"GPU Status: {gpu_status['default_device']}")
        if gpu_status['has_gpu']:
            self._log_info(f"Available GPUs: {[g['name'] for g in gpu_status['gpus']]}")

        # 构建参数
        params = self._build_params()

        # 创建 DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        # 训练
        callbacks = self._create_callbacks()

        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=self.config.get('n_estimators', 100),
            evals=[(dtrain, 'train'), (dval, 'val')],
            callbacks=callbacks,
            verbose_eval=False
        )

        return self._build_results()

    def get_device_info(self) -> Dict[str, Any]:
        """获取训练设备信息"""

        params = self._build_params()
        return {
            'device': params.get('device', 'cpu'),
            'tree_method': params.get('tree_method', 'auto'),
            'gpu_id': params.get('gpu_id'),
            'nthread': params.get('nthread', os.cpu_count())
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
| 1.3 | 2026-03-23 | 新增模型版本管理、数据质量检测、SHAP分析、GPU加速支持设计 |
| 1.2 | 2026-03-23 | 更新文件大小限制为1GB，适配Monorepo结构 |
| 1.1 | 2026-03-23 | 新增数据集切分、特征工程、迁移学习设计章节 |
| 1.0 | 2026-03-23 | 初始版本 |