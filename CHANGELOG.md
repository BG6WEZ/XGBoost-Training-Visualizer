# Changelog

All notable changes to this project will be documented in this file.

## [RC1] - 2026-03-29

### Release Summary

RC1 是 XGBoost Training Visualizer 的第一个发布候选版本，包含完整的 MVP 功能：
- 数据集管理与多文件导入
- XGBoost 模型训练与可视化
- Docker 容器化部署支持
- 完整的 E2E 验收测试

### Docker Images

| 镜像 | 大小 | 说明 |
|------|------|------|
| xgboost-vis-api:rc1 | 592MB | FastAPI 后端服务 |
| xgboost-vis-worker:rc1 | 567MB | 训练任务消费者 |
| xgboost-vis-web:rc1 | 26.2MB | React 前端服务 |

### Added
- Docker 镜像支持 (api, worker, web)
- Docker Compose 生产部署配置
- RC Smoke 一键验收脚本
- Worker 启动脚本 (Windows/Unix)
- 队列治理脚本
- Worker 健康检查脚本
- 队列健康前置检查 (e2e_validation.py)
- NaN 序列化修复 (dataset_scanner.py)
- RC1 最终闸门复核脚本 (rc1_final_gate.ps1)

### Changed
- Dockerfile 使用国内镜像源加速
- pytest 版本降级解决依赖冲突
- package.json 版本更新为 1.0.0-rc1

### Fixed
- PostgreSQL JSON NaN 序列化问题
- 队列积压导致 e2e 超时问题
- Web 前端 Docker 构建 node_modules 冲突
- Worker config.py Docker 容器路径问题
- Worker 缺少 aiofiles 依赖

### Test Coverage
- 57 项回归测试全部通过
- E2E 验证 success=true
- RC Smoke success=true
- Docker Compose 冒烟测试通过

### Known Issues
- Worker 需手动启动（无自动重启机制）
- 无监控告警
- 队列积压需要手动处理

### Quick Start

```bash
# 构建镜像
docker build -t xgboost-vis-api:rc1 -f apps/api/Dockerfile apps/api
docker build -t xgboost-vis-worker:rc1 -f apps/worker/Dockerfile apps/worker
docker build -t xgboost-vis-web:rc1 -f apps/web/Dockerfile apps/web

# 启动服务
docker compose -f docker/docker-compose.prod.yml up -d

# 验证服务
curl http://localhost:8000/health
```
