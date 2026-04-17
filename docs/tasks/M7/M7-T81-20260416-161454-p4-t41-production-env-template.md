# M7-T81 — Phase-4 / Task 4.1 生产环境配置模板

> 任务编号：M7-T81  
> 阶段：Phase-4 / Task 4.1  
> 前置：M7-T80（Task 3.3 验收通过）  
> 时间戳：20260416-161454

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T80-AUDIT-SUMMARY-20260416-161454.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.1`

---

## 一、本轮目标

进入 `Phase-4 / Task 4.1 — 生产环境配置模板`，目标是补齐**可直接用于部署准备的环境变量模板与部署文档**，降低首次上线配置错误风险。

---

## 二、允许修改的范围文件

- `.env.example`（项目根目录，新增或更新）
- `docker/.env.example`（新增或更新）
- `docs/release/DEPLOYMENT_GUIDE.md`（更新）
- 本轮新增报告文件：`docs/tasks/M7/M7-T81-R-<timestamp>-p4-t41-production-env-template-report.md`

禁止越界到：

- API / Worker 业务逻辑
- 前端页面逻辑
- Nginx 配置（属于 Task 4.2）
- 生产部署脚本大改

---

## 三、必须完成的最小工作

### 1) 创建完整的根目录 `.env.example`

必须包含并注释以下变量：

```env
# === 必须配置 ===
JWT_SECRET=
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
ADMIN_DEFAULT_PASSWORD=

# === 存储配置 ===
STORAGE_TYPE=local
WORKSPACE_DIR=/app/workspace

# === MinIO (当 STORAGE_TYPE=minio 时必须) ===
MINIO_ENDPOINT=
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET=xgboost-vis
MINIO_SECURE=false

# === 可选配置 ===
CORS_ORIGINS=https://your-domain.com
MAX_CONCURRENT_TRAININGS=3
LOG_LEVEL=INFO
```

要求：

- 变量名称需与项目当前实现一致
- 必须加简明注释
- 若项目实际还依赖其他关键变量，应一并补齐

### 2) 创建或更新 `docker/.env.example`

要求：

- 面向 Docker 启动场景
- 值与容器网络、Compose 习惯保持一致
- 不得硬编码真实密钥

### 3) 更新部署文档

更新：

- `docs/release/DEPLOYMENT_GUIDE.md`

至少包含：

1. 部署前置条件
2. 一键启动命令
3. 首次登录步骤
4. 健康检查验证步骤

建议覆盖：

- Docker 版本要求
- 最低资源要求
- `.env` 生成方式
- API / Web / Worker 的检查方法

### 4) 必须做基础验证

至少验证：

- 示例环境变量文件已落盘
- 部署文档中的命令与当前仓库结构不冲突
- 文档里的路径、端口、默认地址与当前项目一致

若可以快速验证，建议补做：

- 根据文档流程做一次最小启动核对

---

## 四、通过条件（全部满足才算通过）

- [ ] `.env.example` 包含所有必须变量且有注释
- [ ] `docker/.env.example` 存在并适用于 Docker 场景
- [ ] `docs/release/DEPLOYMENT_GUIDE.md` 已更新
- [ ] 部署文档包含前置条件 / 启动命令 / 首次登录 / 健康检查
- [ ] 文档内容与当前仓库结构一致
- [ ] 产出与本轮编号一致的 `M7-T81-R-...` 报告
- [ ] 未越界推进到 Task 4.2 或后续任务

---

## 五、汇报要求

完成后提交：

- `M7-T81-R-<timestamp>-p4-t41-production-env-template-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 新增 / 更新的环境变量清单
4. Docker 场景下的配置说明
5. 部署文档补充了哪些章节
6. 实际验证方式
7. 已验证通过项
8. 剩余风险与限制
9. 是否建议提交 Task 4.1 验收

---

## 六、明确禁止

- 不得写入真实密码、真实密钥、真实生产地址
- 不得修改业务逻辑来“适配”示例配置
- 不得提前进入 Task 4.2
