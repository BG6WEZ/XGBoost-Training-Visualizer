# M7-T12 任务单：MVP 上传能力回归与 Docker 导入简化闭环

任务编号: M7-T12  
时间戳: 20260331-091851  
所属计划: P1-S1 / MVP 体验回归专项  
前置任务: M7-T11（已完成）  
优先级: 最高（阻断后续数据导入体验验收）

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/specification/PROJECT_FUNCTIONAL_SPECIFICATION.md
- [ ] docs/specification/SOFTWARE_FUNCTION_BLUEPRINT.md
- [ ] docs/tasks/M7/M7-T11-R-20260331-085010-m7-t10-audit-fixes-scope-and-archive-governance-closure-report.md

未完成上述预读，不得开始执行。

---

## 一、背景与问题定义

当前用户实际体验与 MVP 预期存在偏差：

1. MVP 预期是“可上传导入数据集”，但当前主路径偏向“扫描 dataset/ 并登记”。
2. Docker 部署时，数据导入依赖宿主机卷挂载和容器可见路径，操作门槛高。
3. 缺少“上传导入（便捷）+ 扫描登记（批量）”双通道清晰分工。

本任务目标不是推翻现有扫描能力，而是补齐上传能力，恢复 MVP 体验，并将 Docker 导入流程降复杂。

---

## 二、任务目标

完成以下闭环能力：

1. 前端支持直接上传文件（至少 CSV），后端可接收并落盘。
2. 上传成功后可直接创建/登记为数据集，不再要求用户手动准备容器内路径。
3. 保留并兼容现有扫描登记能力，明确两种导入路径的适用场景。
4. Docker 部署下给出一键可复现导入流程（命令 + 页面 + 证据）。

---

## 三、范围边界

### 3.1 允许修改

- apps/api/app/routers/**（仅导入相关路由）
- apps/api/app/schemas/**（仅导入/上传相关契约）
- apps/api/app/services/**（仅上传落盘、登记编排相关）
- apps/web/src/pages/**（仅数据资产/数据集导入相关页面）
- apps/web/src/lib/api.ts（导入 API 契约）
- docker/docker-compose.dev.yml
- docker/docker-compose.prod.yml
- README.md
- docs/planning/TEST_CASES_DATASET_INGESTION.md（必要补充）

### 3.2 禁止修改

- 训练算法与模型逻辑
- 结果分析与对比逻辑
- 与导入无关的页面与 API
- 无关依赖升级与无关重构

---

## 四、详细交付要求

### 任务 4.1：上传导入 API 最小闭环

要求：

1. 新增上传入口（支持 multipart/form-data）。
2. 服务端将上传文件落到 WORKSPACE_DIR 下可管理目录（如 workspace/uploads）。
3. 上传完成后返回可用于创建数据集的结构化信息（file_path、file_name、size 等）。
4. 增加基础安全校验：扩展名白名单、空文件拦截、路径注入防护。

验收标准：

- 上传成功返回 200/201，并含可追踪文件路径。
- 非法文件类型返回 4xx 且有清晰错误。

### 任务 4.2：数据集创建链路打通

要求：

1. 前端可从上传结果一键创建数据集。
2. 保持原有 `POST /api/datasets/` 契约兼容，不破坏历史流程。
3. 上传路径生成的数据集可被 preview/split/preprocess 正常消费。

验收标准：

- 至少完成 1 条上传 -> 创建数据集 -> 预览成功链路。

### 任务 4.3：扫描与上传双通道治理

要求：

1. 页面层面明确提供两种入口：
   - 上传导入（推荐个人/临时数据）
   - 扫描登记（推荐批量/预置数据）
2. 文案中明确两者差异，不允许混淆。
3. 不得移除现有扫描能力。

验收标准：

- 用户无需理解容器路径也可完成上传导入。
- 扫描流程仍可用且结果一致。

### 任务 4.4：Docker 导入简化

要求：

1. 统一并显式声明 DATASET_DIR/WORKSPACE_DIR 在 dev/prod compose 中的策略。
2. 提供 Docker 场景导入最小步骤（最多 3 步），并写入 README。
3. 给出“上传导入无需手动挂载数据目录”的验证证据。

验收标准：

- 全新机器按 README 可复现。
- 无需手工进入容器拷贝文件即可完成导入。

---

## 五、协作机制（必须体现多角色）

本任务必须采用内部多角色协同（可一人多角色，但需在汇报中明确职责与产出）：

- Frontend 角色：上传交互、入口分流、错误提示
- Backend 角色：上传 API、落盘校验、创建链路
- DevOps 角色：Docker 变量与卷策略、README 操作路径
- QA 角色：本地与 Docker 双环境验证、证据采集
- Reviewer 角色：范围控制、契约一致性、回归风险核对

---

## 六、必须提供的实测证据

### 6.1 自动化与门禁

在项目根目录执行并贴出完整输出：

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -v --tb=short
```

### 6.2 上传链路证据（必须）

至少 2 条成功 + 1 条失败：

1. 成功链路 A：上传 CSV -> 返回文件信息
2. 成功链路 B：基于上传结果创建数据集 -> preview 成功
3. 失败链路：非法扩展名或空文件 -> 返回 4xx + 明确 detail

每条链路必须包含：请求方式、URL、请求体/表单关键字段、响应关键字段。

### 6.3 Docker 场景证据（必须）

至少包含：

1. `docker compose -f docker/docker-compose.prod.yml up -d` 成功启动
2. 页面完成上传导入并成功创建数据集
3. 对应数据集 preview 正常返回

---

## 七、完成判定

以下全部满足才算完成：

- [ ] 支持上传导入并成功落盘
- [ ] 上传结果可直接创建并使用数据集
- [ ] 扫描与上传双通道并存且文案清晰
- [ ] Docker 下导入步骤显著简化并可复现
- [ ] 门禁命令通过且结果如实记录
- [ ] 汇报为统一证据报告（不是摘要式结论）

---

## 八、Copilot 审核重点

1. 是否真正实现“上传导入”，而非继续要求本地路径填写。
2. 是否兼容并保留扫描登记能力。
3. Docker 导入是否降低操作复杂度且可复现。
4. 是否存在范围漂移（改动到训练/结果等无关模块）。

---

## 九、汇报文件命名

本任务预期汇报文件：

docs/tasks/M7/M7-T12-R-20260331-091851-mvp-upload-recovery-and-docker-ingestion-simplification-report.md

Trae 完成后必须按该命名提交，且必须提交统一证据报告。
