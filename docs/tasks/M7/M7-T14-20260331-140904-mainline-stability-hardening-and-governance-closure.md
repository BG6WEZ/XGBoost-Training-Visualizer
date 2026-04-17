# M7-T14 任务单：主线稳定性加固与治理闭环

任务编号: M7-T14  
时间戳: 20260331-140904  
所属计划: M7 主线收口  
前置任务: M7-T13（已完成）  
优先级: 最高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T13-R-20260331-095253-upload-ui-closure-and-self-governance-report.md

未完成上述预读，不得开始执行。

---

## 一、背景与目标

M7-T13 已完成上传导入前端闭环，但在真实大数据量场景中暴露出多项运行时稳定性问题：

1. 文件夹上传时，后端按相对路径文件名写盘触发 500。
2. 前端选择文件后缺少精细化治理能力（单个删除、批量删除非法格式）。
3. 上传大小默认 1GB 限制，不满足主线数据规模。
4. 数据集创建在 2GB+ 总文件大小时触发数据库 int32 溢出。
5. 训练链路遇到 schema 变更后 asyncpg 缓存语句失效。
6. 训练目标列非法值（NaN/Inf/过大）错误定位不清晰。

本任务目标是在不偏离主线功能的前提下，完成生产可用级稳定性加固与证据归档。

---

## 二、范围边界

### 2.1 允许修改

- apps/web/src/pages/AssetsPage.tsx
- apps/api/app/config.py
- apps/api/app/routers/datasets.py
- apps/api/app/models/models.py
- apps/api/migrations/*.sql
- apps/worker/app/tasks/training.py
- apps/worker/app/main.py
- docs/tasks/M7/M7-T14-20260331-140904-mainline-stability-hardening-and-governance-closure.md
- docs/tasks/M7/M7-T14-R-20260331-140904-mainline-stability-hardening-and-governance-closure-report.md
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 2.2 禁止修改

- 与主线稳定性无关的 UI 重构
- 与当前问题无关的算法与模型能力扩展
- 无依据的框架升级

---

## 三、详细交付要求

### 任务 3.1 上传链路稳定性修复

1. 修复目录型文件名导致的上传落盘失败。
2. 上传默认取消 1GB 限制（允许配置覆盖）。
3. 保持非法扩展名、空文件校验能力。

### 任务 3.2 上传 UI 治理增强

1. 已选文件支持单个删除。
2. 支持批量删除非法格式文件。
3. 增加“只显示非法文件”筛选开关。

### 任务 3.3 大数据集元数据持久化兼容

1. 将文件大小相关字段升级为 BIGINT。
2. 完成运行库在线迁移并验证。

### 任务 3.4 训练稳定性与可诊断性

1. 训练前增加目标列值合法性校验（NaN/Inf/过大值）。
2. 遇到 asyncpg InvalidCachedStatementError 增加一次自动重试。

---

## 四、协作机制（多角色）

- Frontend 角色：上传选择治理交互增强。
- Backend 角色：上传与数据集创建链路稳定性修复。
- Data/DB 角色：文件大小字段升级与在线迁移执行。
- Worker 角色：训练可诊断性与缓存失效容错。
- QA 角色：Docker 运行态日志回归与链路验证。
- Reviewer 角色：范围收敛、证据一致性与映射更新核对。

---

## 五、完成判定

以下全部满足才算完成：

- [ ] 文件夹上传稳定，不再因路径型文件名 500。
- [ ] 上传 UI 支持单删、批量删非法、只看非法。
- [ ] 上传大小默认无限制，支持超 1GB 场景。
- [ ] 数据集创建支持 2GB+ 总文件大小。
- [ ] 训练前目标列非法值可读报错。
- [ ] InvalidCachedStatementError 不再直接导致训练立即失败。
- [ ] 形成统一汇报文档并更新映射表。
