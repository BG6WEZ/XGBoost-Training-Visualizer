# XGBoost Training Visualizer

> XGBoost 训练可视化工具 - 专业的时间序列预测模型训练平台

---

## 项目简介

XGBoost Training Visualizer 是一个面向专业用户的时间序列预测模型训练平台，提供从数据上传、特征工程、模型训练到结果分析的全流程可视化操作界面。

### 核心特性

- 📊 **数据管理** - 支持 CSV/Excel/JSON 格式，大文件自动切分
- 🔧 **特征工程** - 时间特征、滞后特征、滚动统计特征自动生成
- 🎯 **模型训练** - XGBoost 参数可视化配置，实时训练监控
- 📈 **结果分析** - 多维度性能指标，特征重要性分析
- 🔄 **迁移学习** - 跨数据集模型迁移，支持多种迁移策略
- ⚡ **GPU 加速** - 自动检测 GPU，支持多卡训练

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Tailwind CSS + Chart.js |
| 后端 API | Node.js + Express + WebSocket |
| 训练服务 | Python + FastAPI + XGBoost |
| 数据层 | PostgreSQL + Redis |
| 构建工具 | pnpm + Turborepo + Vite |

---

## 项目结构

```
XGBoost-Training-Visualizer/
├── apps/
│   ├── web/                 # React 前端应用
│   ├── api/                 # Node.js API 服务
│   └── trainer/             # Python 训练服务
├── packages/
│   ├── types/               # 共享类型定义
│   ├── utils/               # 工具函数
│   └── config/              # 共享配置
├── docs/                    # 项目文档
│   ├── architecture/        # 架构设计
│   ├── design/              # UI/UX 设计
│   ├── planning/            # 项目规划
│   └── specification/       # 功能规格
├── dataset/                 # 示例数据集
└── turbo.json              # Turborepo 配置
```

---

## 快速开始

### 环境要求

- Node.js >= 18
- pnpm >= 8
- Python >= 3.10
- PostgreSQL >= 14
- Redis >= 6

### 安装依赖

```bash
# 安装 Node.js 依赖
pnpm install

# 安装 Python 依赖
cd apps/trainer
pip install -r requirements.txt
```

### 启动开发服务

```bash
# 启动所有服务
pnpm dev

# 单独启动前端
pnpm --filter @xgboost-vis/web dev

# 单独启动 API
pnpm --filter @xgboost-vis/api dev
```

### 构建生产版本

```bash
pnpm build
```

---

## 文档导航

详细文档请访问 [docs/](./docs/) 目录：

| 文档类型 | 路径 | 说明 |
|----------|------|------|
| 📋 功能规格 | [specification/](./docs/specification/) | 项目功能需求说明 |
| 🏗️ 架构设计 | [architecture/](./docs/architecture/) | 技术架构和功能设计 |
| 🎨 UI设计 | [design/](./docs/design/) | 界面设计和交互规范 |
| 📅 项目规划 | [planning/](./docs/planning/) | 开发计划和协作指南 |

---

## 开发状态

| 阶段 | 状态 | 完成度 |
|------|------|--------|
| Phase 1: 项目基础设施 | ✅ 完成 | 100% |
| Phase 2: 核心功能开发 | 🚧 进行中 | 70% |
| Phase 3: 高级功能 | ⏳ 待开始 | 0% |

详见 [开发检查报告](./docs/planning/DEVELOPMENT_REVIEW_REPORT.md)

---

## 许可证

MIT License

---

*最后更新：2026-03-23*