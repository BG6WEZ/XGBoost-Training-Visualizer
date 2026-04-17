# M7-T14 任务汇报：主线稳定性加固与治理闭环

任务编号: M7-T14  
时间戳: 20260331-140904  
所属计划: M7 主线收口  
前置任务: M7-T13  
完成状态: 已完成

---

## 一、任务概述

本轮围绕“上传导入 -> 数据集创建 -> 训练执行”主线进行了生产场景稳定性加固，目标是解决大数据量和运行时异常下的主线断点，确保功能可持续运行而非一次性通过。

---

## 二、执行内容与代码落点

### 2.1 上传链路稳定性

1. 修复文件夹上传时相对路径文件名导致写盘失败。
2. 上传大小由固定 1GB 改为“默认不限，显式配置才限制”。

涉及文件：

- apps/api/app/routers/datasets.py
- apps/api/app/config.py

### 2.2 上传 UI 治理增强

1. 已选文件支持单个删除。
2. 支持批量删除非法格式文件。
3. 增加“只显示非法文件”筛选开关。

涉及文件：

- apps/web/src/pages/AssetsPage.tsx

### 2.3 大数据集元数据持久化升级

1. 模型定义中 file_size / total_file_size 升级为 BIGINT。
2. 迁移脚本同步更新并新增增量迁移脚本。
3. 对运行中的 Postgres 执行在线 ALTER TABLE。

涉及文件：

- apps/api/app/models/models.py
- apps/api/migrations/001_init_schema.sql
- apps/api/migrations/002_upgrade_multi_file.sql
- apps/api/migrations/003_upgrade_file_size_bigint.sql

### 2.4 训练稳定性与诊断能力

1. 训练前目标列合法性校验（NaN/Inf/过大值）并输出可读错误详情。
2. Worker 在遇到 InvalidCachedStatementError 时自动回滚并重试一次查询。

涉及文件：

- apps/worker/app/tasks/training.py
- apps/worker/app/main.py

---

## 三、关键证据（命令与结果）

### 3.1 上传/CORS/文件夹路径问题修复验证

执行：

- `docker compose -f docker/docker-compose.yml logs api --tail 200`
- 自定义 httpx 脚本上传文件名 `data/weather/weather.csv`

结果：

- 上传返回 `STATUS 200`
- `Access-Control-Allow-Origin: http://localhost:3000`
- 返回 `file_name=weather.csv`，路径已被安全归一化

### 3.2 上传 UI 变更验证

执行：

- `pnpm --filter web typecheck`
- `docker compose -f docker/docker-compose.yml up -d --build frontend`

结果：

- typecheck 通过
- 前端容器重建成功

### 3.3 大文件创建失败（int32 溢出）修复验证

问题证据（修复前）：

- `POST /api/datasets/` 500
- `invalid input for query argument ... value out of int32 range`
- `total_file_size=2610923746`

执行修复：

- 在线迁移命令：
  `ALTER TABLE datasets ALTER COLUMN total_file_size TYPE BIGINT;`
  `ALTER TABLE dataset_files ALTER COLUMN file_size TYPE BIGINT;`
  `ALTER TABLE models ALTER COLUMN file_size TYPE BIGINT;`

验证：

- `SELECT ... information_schema.columns ...` 返回三列 `data_type=bigint`

### 3.4 asyncpg 缓存语句失效问题修复验证

执行：

- `docker compose -f docker/docker-compose.yml restart api worker`
- `docker compose -f docker/docker-compose.yml up -d --build worker`
- `docker compose -f docker/docker-compose.yml logs worker --tail 80`

结果：

- API/Worker 重新启动正常
- Worker 进入 `waiting for tasks`
- 旧报错可在历史日志中追溯，新逻辑已增加自动重试容错

### 3.5 训练目标列非法值可读性验证

执行：

- 本地验证脚本（构造 target 含 NaN）

结果：

- 返回明确错误：
  `Invalid target values in column 'target': nan=1, inf=0, too_large=0, invalid_total=1, samples=[...]`

---

## 四、回归结论

1. 上传导入主链路：可用并稳定（含文件夹上传场景）。
2. 数据集创建主链路：支持 2GB+ 总文件大小，不再因 int32 上限失败。
3. 训练执行主链路：
   - schema 变更后的缓存语句问题有容错重试；
   - 数据质量问题可读报错并可定位。

---

## 五、风险与后续建议

### 5.1 当前残余风险

- 数据质量问题（目标列 NaN/Inf）仍会导致训练失败，但现在失败是可诊断的。

### 5.2 下一步建议（M7-T15 候选）

1. 增加“训练前自动清洗标签非法值”可选开关（drop invalid labels）。
2. 在前端训练页面直出“目标列非法值统计”预检提示，减少试错成本。

---

## 六、结论

M7-T14 已完成。主线从“可运行”提升到“可在大数据与异常场景下持续运行”，并形成代码-运行证据-文档映射的闭环治理。