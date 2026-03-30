# 项目文档中心

> XGBoost Training Visualizer 文档导航与开发基线入口

---

## 📌 当前建议先读文档

以下 3 份文档是本轮根据真实数据资产重新整理后的开发基线，建议优先阅读：

1. [DATASET_ASSET_INVENTORY.md](./architecture/DATASET_ASSET_INVENTORY.md)
   - 回答“项目手里有什么数据，这些数据能支持什么功能”
2. [SOFTWARE_FUNCTION_BLUEPRINT.md](./specification/SOFTWARE_FUNCTION_BLUEPRINT.md)
   - 回答“软件应该由哪些组合功能构成，当前范围如何收敛”
3. [DEVELOPMENT_PREPARATION_GUIDE.md](./planning/DEVELOPMENT_PREPARATION_GUIDE.md)
   - 回答“如何按阶段落地开发，先做什么，如何验收”

---

## 📁 文档结构

```text
docs/
├── architecture/       # 架构设计与数据资产文档
├── design/             # UI/UX 设计文档
├── planning/           # 开发规划与准备文档
├── specification/      # 功能规格与产品蓝图
└── README.md           # 本文档
```

---

## 📖 文档索引

### 1. 架构设计 (architecture/)

| 文档 | 说明 | 状态 |
|------|------|------|
| [DATASET_ASSET_INVENTORY.md](./architecture/DATASET_ASSET_INVENTORY.md) | 基于 `dataset/` 目录的真实数据资产清单、建模适配范围与导入约束 | 当前开发基线 |
| [TECHNICAL_ARCHITECTURE.md](./architecture/TECHNICAL_ARCHITECTURE.md) | 详细技术架构草案，包含系统架构、数据库、API、服务设计 | 历史详细方案 |
| [CORE_FEATURES_DESIGN.md](./architecture/CORE_FEATURES_DESIGN.md) | 核心功能技术设计草案 | 历史详细方案 |

### 2. 功能规格 (specification/)

| 文档 | 说明 | 状态 |
|------|------|------|
| [SOFTWARE_FUNCTION_BLUEPRINT.md](./specification/SOFTWARE_FUNCTION_BLUEPRINT.md) | 按真实数据与开发目标整理的软件组合功能蓝图 | 当前开发基线 |
| [PROJECT_FUNCTIONAL_SPECIFICATION.md](./specification/PROJECT_FUNCTIONAL_SPECIFICATION.md) | 原有详细功能规格草案 | 历史详细方案 |

### 3. 项目规划 (planning/)

| 文档 | 说明 | 状态 |
|------|------|------|
| [DEVELOPMENT_PLAN.md](./planning/DEVELOPMENT_PLAN.md) | 详细开发计划，包含里程碑、任务拆分和上传能力基线 | 当前开发基线 |
| [DEVELOPMENT_PREPARATION_GUIDE.md](./planning/DEVELOPMENT_PREPARATION_GUIDE.md) | 开发准备、阶段划分、目录建议与 MVP 验收标准 | 当前开发基线 |
| [TEST_PLAN.md](./planning/TEST_PLAN.md) | MVP 测试范围、层级、通过标准与回归重点 | 当前开发基线 |
| [TEST_CASES_DATASET_INGESTION.md](./planning/TEST_CASES_DATASET_INGESTION.md) | 数据集导入、文件夹上传、多 CSV 逻辑数据集测试用例 | 当前开发基线 |
| [DEVELOPMENT_COLLABORATION_GUIDE.md](./planning/DEVELOPMENT_COLLABORATION_GUIDE.md) | 多阶段协作和测试草案 | 参考文档 |

### 4. UI/UX 设计 (design/)

| 文档 | 说明 | 状态 |
|------|------|------|
| [UI_DESIGN_SPECIFICATION.md](./design/UI_DESIGN_SPECIFICATION.md) | UI 规范文档 | 参考文档 |

#### 设计参考文档 (design/references/)

| 文档 | 说明 | 使用规则 |
|------|------|------|
| [DESIGN_SYSTEM.md](./design/references/DESIGN_SYSTEM.md) | 设计系统概述 | 仅作参考，不得直接使用 |
| [DESIGN_SYSTEM_DETAILED.md](./design/references/DESIGN_SYSTEM_DETAILED.md) | 设计系统详细说明 | 仅作参考，不得直接使用 |
| [PAGE_DESIGN_SPECIFICATIONS.md](./design/references/PAGE_DESIGN_SPECIFICATIONS.md) | 页面设计规格 | 仅作参考，不得直接使用 |
| [PROTOTYPE_DESIGN_SUMMARY.md](./design/references/PROTOTYPE_DESIGN_SUMMARY.md) | 原型设计总结 | 仅作参考，不得直接使用 |
| [PROTOTYPE_OVERVIEW.md](./design/references/PROTOTYPE_OVERVIEW.md) | 原型概览 | 仅作参考，不得直接使用 |

---

## 🚀 推荐阅读顺序

### 准备开发时

1. [DATASET_ASSET_INVENTORY.md](./architecture/DATASET_ASSET_INVENTORY.md)
2. [SOFTWARE_FUNCTION_BLUEPRINT.md](./specification/SOFTWARE_FUNCTION_BLUEPRINT.md)
3. [DEVELOPMENT_PREPARATION_GUIDE.md](./planning/DEVELOPMENT_PREPARATION_GUIDE.md)
4. [TECHNICAL_ARCHITECTURE.md](./architecture/TECHNICAL_ARCHITECTURE.md)
5. [UI_DESIGN_SPECIFICATION.md](./design/UI_DESIGN_SPECIFICATION.md)

### 做页面或交互时

1. 先看 [SOFTWARE_FUNCTION_BLUEPRINT.md](./specification/SOFTWARE_FUNCTION_BLUEPRINT.md) 明确页面对应的真实任务
2. 再看 [UI_DESIGN_SPECIFICATION.md](./design/UI_DESIGN_SPECIFICATION.md)
3. 最后参考 `design/references/`，但不能直接复刻

---

## 🧭 当前文档使用原则

1. 先以“真实数据资产”定义需求，不反过来拿原型页面倒推功能。
2. 先以“当前开发基线”文档推进实施，旧文档保留为补充说明。
3. 如果新实现与历史草案冲突，以开发基线文档为准，并再回写更新详细方案。

---

## 📝 文档维护建议

1. 每新增一个核心能力，优先更新“数据资产清单 / 功能蓝图 / 开发准备”三类文档中的相关部分。
2. 详细架构和 UI 草案在能力边界稳定后再同步细化。
3. 对 `design/references/` 的引用必须保留“仅作参考，不得直接使用”的说明。

---

*最后更新：2026-03-25*
