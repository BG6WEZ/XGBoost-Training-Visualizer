# M6-T03 任务单：Worker 容器修复与版本对齐

**任务编号**: M6-T03  
**时间戳**: 20260329-210708  
**前置任务**: M6-T02（部分通过）  
**优先级**: 高（阻断 RC1 完成）

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`

---

## 一、任务背景

M6-T02 审核发现以下两个缺陷未修复，阻碍 RC1 正式关闭：

| 缺陷编号 | 描述 | 严重程度 |
|----------|------|----------|
| D1 | `apps/worker/app/config.py` 在 Docker 容器中崩溃：`parents[4]` IndexError | 阻断 |
| D2 | 根 `package.json` 版本仍为 `"1.0.0"`，未更新为 `"1.0.0-rc1"` | 高 |

---

## 二、任务目标

### 任务 2.1：修复 Worker `config.py` 容器路径问题

**现象**：`docker-worker-1` Exited (1)，日志：
```
IndexError: 4
  File "/app/app/config.py", line 8, in <module>
    PROJECT_ROOT = Path(__file__).resolve().parents[4]
```

**原因**：容器内路径为 `/app/app/config.py`，只有 3 个父目录（`/app/app`、`/app`、`/`），`parents[4]` 越界。

**修复要求**：
- 参考 `apps/api/app/config.py` 的已有修复方式（try-except IndexError）
- 在 `apps/worker/app/config.py` 第 8 行附近做同等修复：

```python
# 修复前（容器内会 IndexError）
PROJECT_ROOT = Path(__file__).resolve().parents[4]

# 修复后（与 API config.py 保持一致）
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[4]
except IndexError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
```

**注意**：修复后必须重新构建 worker 镜像：
```bash
docker build -t xgboost-vis-worker:rc1 -f apps/worker/Dockerfile apps/worker
```

### 任务 2.2：更新根 `package.json` 版本

**当前值**：`"version": "1.0.0"`  
**要求值**：`"version": "1.0.0-rc1"`

操作：
```bash
# 修改 package.json 第 3 行
"version": "1.0.0-rc1",
```

---

## 三、完整验收标准（全部必须通过）

### 3.1 Docker Compose 完整冒烟

```bash
# 启动所有服务
docker compose -f docker/docker-compose.prod.yml up -d

# 等待 30 秒后检查
docker compose -f docker/docker-compose.prod.yml ps
```

**必须显示**：所有 6 个服务均为 `Up`（不得有 `Exited`）：
- `docker-api-1` → `Up` + `(healthy)`
- `docker-worker-1` → `Up`（不得 Exited）
- `docker-frontend-1` → `Up`
- `docker-postgres-1` → `Up` + `(healthy)`
- `docker-redis-1` → `Up`
- `docker-minio-1` → `Up`

### 3.2 HTTP 端点检查

```bash
# API 健康
curl.exe -s http://localhost:8000/health
# 期望：{"status":"healthy","version":"1.0.0",...}

# 前端
curl.exe -sS -o NUL -w "%{http_code}" http://localhost:3000
# 期望：200

# Worker 状态（通过 API 代理）
curl.exe -s http://localhost:8000/api/training/status
# 期望：{"worker_status":"healthy",...}
```

### 3.3 版本对齐

```bash
# 检查 package.json 版本
Get-Content package.json | Select-String '"version"'
# 必须输出：  "version": "1.0.0-rc1",
```

### 3.4 Worker 日志验证

```bash
# 确认 worker 容器运行而不是崩溃
docker logs docker-worker-1 2>&1 | Select-Object -Last 5
# 不得包含 IndexError 或 Traceback
```

### 3.5 清理

```bash
docker compose -f docker/docker-compose.prod.yml down -v
```

汇报中须包含 `EXIT_CODE=0` 的输出证据。

---

## 四、汇报要求

汇报文件保存至：
```
docs/tasks/M6/M6-T03-R-20260329-210708-worker-config-and-release-version-alignment-report.md
```

汇报必须包含：
1. `docker compose ps` 完整输出（截图或文字，所有 6 个服务 Up）
2. `docker logs docker-worker-1` 最后 5 行（无 IndexError）
3. `curl.exe` 检查结果：`/health` + `localhost:3000` HTTP 200
4. `Get-Content package.json | Select-String '"version"'` 输出（显示 1.0.0-rc1）
5. `docker compose down -v` 完成证据（EXIT_CODE=0）
6. 修改的文件清单（至少：`apps/worker/app/config.py`、`package.json`）

---

## 五、不在本任务范围内

- 不要修改 API 的任何现有逻辑
- 不要修改测试文件
- 不要更新 CHANGELOG.md（已在 M6-T01 完成）
- 不要执行 `git tag` 或 `git push`

---

## 六、角色分工建议

本任务涉及后端容器（worker）和发布元数据（package.json），建议：
- **DevOps 角色**：执行 Docker 构建和冒烟测试
- **后端角色**：修复 `config.py`
- **QA 角色**：验收全部 3.1-3.5 检查点
