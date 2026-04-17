# M7-T100-R — Phase-5 / Task 5.2（Linux Runner Schema 初始化与 Benchmark 重跑）报告

任务编号：M7-T100  
阶段：Phase-5 / Task 5.2 Re-open  
时间戳：2026-04-17 12:10:00  
执行人：GPT-5.4

---

## 一、目标回顾

本轮目标：

1. 修复 Linux runner 上 benchmark 失败的根因（数据库 schema / 初始化未就绪）
2. 在 GitHub Actions `ubuntu-latest` 上重跑 `benchmark-linux.yml`
3. 取得一份完整可复现的 Linux benchmark 输出，用于继续判断 `Task 5.2`

---

## 二、根因定位

上一轮 Linux run `24552029858` 失败点是 `Run benchmark`，页面可见线索指向 SQLAlchemy `f405`，其本质是：

- Docker Compose 启动了服务
- 但在执行 benchmark 之前没有运行 Alembic 迁移
- `init_db()` 在检测到未迁移时会安全返回，不访问业务表（见 `apps/api/app/database.py:init_db`）
- 因此访问 `/api/experiments/` 等业务接口会触发 schema 缺失错误

结论：缺少 **`alembic upgrade head`** 这一前置初始化步骤。

---

## 三、修改内容

### 1) CI workflow：在 benchmark 前执行迁移并重启 API

文件：

- `.github/workflows/benchmark-linux.yml`

变更：

- `docker compose up -d` 后新增：
  - `docker compose exec -T api python -m alembic upgrade head`
  - `docker compose restart api`
  - `/ready` 等待时间从 30s 扩展到 60s

目的：

- 确保 schema 已就绪
- 重启 API 让 `init_db()` 在“已迁移”状态下执行，从而具备最小可用数据（含 admin 初始化逻辑）

### 2) Docker Compose：注入稳定的 admin 初始密码

文件：

- `docker/docker-compose.yml`

变更：

- `api` 服务新增环境变量：
  - `ADMIN_DEFAULT_PASSWORD=${ADMIN_DEFAULT_PASSWORD:-admin123}`

目的：

- 让 `init_db()` 创建 admin 时使用确定密码，避免 benchmark 登录阶段出现随机密码导致的不可控状态

---

## 四、GitHub Actions 运行证据

### 1) 触发信息

- Workflow：`Performance Benchmark (Linux)`
- Branch：`master`
- Commit：`336109b`
- Inputs：`task_id = M7-T100`

### 2) Run 信息

- Run ID：`24554310231`
- Run URL：`https://github.com/BG6WEZ/XGBoost-Training-Visualizer/actions/runs/24554310231`
- 结果：`failed`

失败原因说明：

- Benchmark 脚本退出码以“是否全部端点达标”为准
- 本次 Linux benchmark 已完整执行并输出汇总表，但多端点 P95 未达标，导致 `exit code 1`

---

## 五、Benchmark 原始结果（Linux runner）

执行命令（workflow 中）：

```bash
python scripts/benchmark.py --base-url http://localhost:8000
```

### 端点汇总（P95）

| 端点 | P95(ms) | 目标(ms) | 达标 | 总请求 | 成功 | 失败 | 错误率 |
|---|---:|---:|---|---:|---:|---:|---:|
| /health | 2392.38 | 50 | FAIL | 500 | 500 | 0 | 0.00% |
| /api/auth/login | 6911.86 | 500 | FAIL | 100 | 100 | 0 | 0.00% |
| /api/datasets/ | 666.97 | 200 | FAIL | 200 | 200 | 0 | 0.00% |
| /api/experiments/ | 568.58 | 200 | FAIL | 200 | 200 | 0 | 0.00% |
| /api/datasets/upload (1MB CSV) | 2839.09 | 3000 | PASS | 50 | 50 | 0 | 0.00% |

### 汇总指标

- 5xx 错误总计：`0`
- 整体请求成功率：`100.00%`
- 全部端点达标：`否`
- GitHub Actions 退出码：`1`

---

## 六、验收判断

### 对 M7-T100 的判断

本轮目标是“修复 schema 阻断并在 Linux runner 上跑出完整 benchmark 输出”。这一目标已达成：

- schema 阻断已解除（benchmark 可完整执行并输出结果表）
- 已获取 Linux runner 的完整输出与 run 证据

因此：

- ✅ **M7-T100 可判定为完成**

### 对 Task 5.2 的判断

总计划 `Task 5.2` 的通过条件要求：

- 所有端点满足 P95 目标

当前 Linux runner 的结果显示：

- 仅 `1/5` 端点达标

因此：

- ❌ **Task 5.2 仍不通过**

---

## 七、下一步建议

进入下一轮继续收口 `Task 5.2`：

1. 基于 Linux runner 的结果，对 `/health`、`/api/auth/login` 等 P95 异常高的原因做定位
2. 修复后重新跑 Linux benchmark，直到 `5/5` 全部端点达标

附：当前结果已证明 “Linux runner 可跑通但仍未达标”，因此后续讨论需以 Linux 结果为准，不再以 WSL2 作为唯一假设。
