# M7-T13 任务单：上传导入前端闭环与自执行治理收口

任务编号: M7-T13  
时间戳: 20260331-095253  
所属计划: P1-S1 / MVP 导入体验补齐  
前置任务: M7-T12（已完成）  
优先级: 最高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T12-20260331-091851-mvp-upload-recovery-and-docker-ingestion-simplification.md
- [ ] docs/tasks/M7/M7-T12-R-20260331-091851-mvp-upload-recovery-and-docker-ingestion-simplification-report.md

未完成上述预读，不得开始执行。

---

## 一、背景与目标

M7-T12 已验证后端上传 API 可用，但前端资产页仍未提供可直接操作的上传入口，导致用户无法在页面完成“上传 -> 创建数据集”闭环。本任务目标是补齐前端上传交互并完成可复核证据归档。

目标：

1. 资产页新增上传导入入口并可选择文件上传。
2. 上传成功后可在页面一键创建数据集。
3. 保留扫描登记能力，形成上传/扫描双通道。
4. 完成门禁与真实链路证据，形成任务-汇报闭环归档。

---

## 二、范围边界

### 2.1 允许修改

- apps/web/src/lib/api.ts
- apps/web/src/pages/AssetsPage.tsx
- docs/tasks/M7/M7-T13-20260331-095253-upload-ui-closure-and-self-governance.md
- docs/tasks/M7/M7-T13-R-20260331-095253-upload-ui-closure-and-self-governance-report.md
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 2.2 禁止修改

- apps/api/app/**
- apps/worker/**
- 与导入无关的页面和业务逻辑

---

## 三、交付要求

1. 前端 API 契约增加上传方法（multipart/form-data）。
2. Assets 页签新增“上传导入”。
3. 支持上传结果回显（行数、列数、字段）并允许填写数据集信息。
4. 提供一键创建数据集按钮，调用现有 POST /api/datasets/。
5. 扫描登记页签保持可用，文案明确适用场景差异。
6. 提供上传成功链路、失败链路、门禁命令输出。

---

## 四、协作机制

本任务采用自执行多角色协作（同一执行者承担多角色）：

- Frontend 角色：上传 UI、交互状态、错误提示。
- Contract 角色：api.ts 请求结构与返回类型对齐。
- QA 角色：typecheck/build、后端回归、上传链路证据采集。
- Reviewer 角色：范围收敛与闭环文档一致性核对。

---

## 五、门禁与证据要求

必须执行并在汇报中记录：

```bash
pnpm --filter @xgboost-vis/web typecheck
pnpm --filter @xgboost-vis/web build
python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -v --tb=short
```

必须提供链路证据：

1. 成功链路 A：上传 CSV 返回文件元信息。
2. 成功链路 B：基于上传结果创建数据集并 preview 成功。
3. 失败链路 A：非法扩展名返回 400。
4. 失败链路 B：空文件返回 400。

---

## 六、完成判定

以下全部满足才算完成：

- [ ] 前端上传入口可用
- [ ] 上传后可一键创建数据集
- [ ] 扫描登记能力保留
- [ ] 前后端门禁命令通过
- [ ] 2 成功 + 2 失败链路证据完整
- [ ] 汇报归档完成并更新映射表
