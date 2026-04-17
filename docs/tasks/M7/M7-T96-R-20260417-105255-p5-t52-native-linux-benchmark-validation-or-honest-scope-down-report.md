# M7-T96-R — Phase-5 / Task 5.2 原生 Linux 基准验证报告（结论 B：无法取得复核证据）

> 任务编号：M7-T96  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T95（已完成真实性能优化，但当前仅 1/5 端点达标，WSL2 环境归因尚未闭环）  
> 时间戳：2026-04-17 10:52:55

---

## 一、本轮目标回顾

本轮唯一合理目标是：

1. 在原生 Linux 环境执行同口径 benchmark
2. 验证"未达标主因是 WSL2 环境"这一判断是否成立
3. 基于复核结果，决定 Task 5.2 是通过还是继续失败

---

## 二、环境排查过程

### 2.1 尝试的环境

| 环境 | 排查方式 | 结果 | 原因 |
|------|---------|------|------|
| Windows 宿主机 | `uname -a` | ✗ 不可用 | Windows 11，非 Linux |
| WSL (docker-desktop) | `wsl -e bash -c "uname -a"` | ✗ 不可用 | distro 无 bash，仅用于 Docker |
| Docker 容器内 | `docker compose exec api uname -a` | ⚠ 内核 `6.6.87.2-microsoft-standard-WSL2` | **仍基于 WSL2，非原生 Linux** |
| GitHub Actions CI | `git push origin master` 触发 workflow | ✗ 网络失败 | `Failed to connect to github.com port 443` |

### 2.2 Docker 容器内核证据

```
Linux 6236ee813f93 6.6.87.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025 x86_64 GNU/Linux
```

容器内核明确包含 `microsoft-standard-WSL2`，证实 Docker Desktop for Windows 仍使用 WSL2 作为后端。这**不是原生 Linux**。

### 2.3 GitHub Actions CI 网络失败证据

```
fatal: unable to access 'https://github.com/BG6WEZ/XGBoost-Training-Visualizer.git/':
Failed to connect to github.com port 443 via 127.0.0.1 after 2106 ms: Could not connect to server
```

当前环境存在代理配置（`127.0.0.1`），导致无法推送代码到 GitHub，无法触发 `ubuntu-latest` runner 上的 benchmark。

---

## 三、结论 B（按 M7-T96 任务单要求）

根据 M7-T96 任务单定义的"结论 B"条件：

> 若出现以下任一情况：
> - Linux 复核后仍未全部达标
> - **无法取得原生 Linux 环境**
> - 环境证据不足
>
> 则必须诚实结论：
> - Task 5.2 仍不通过
> - 当前不能把"WSL2 是主因"写成已证实结论

**本轮结论：结论 B**

- **Task 5.2 仍不通过**
- **无法取得原生 Linux 环境复核证据**
- **当前不能把"WSL2 是主因"写成已证实结论**（仅作为合理怀疑）

---

## 四、已尝试但失败的 Linux 复核路径

| 路径 | 状态 | 失败原因 |
|------|------|---------|
| Docker 容器内执行 benchmark | 执行了，但内核为 WSL2 | Docker Desktop 使用 WSL2 后端 |
| GitHub Actions `ubuntu-latest` | workflow 已创建（`.github/workflows/benchmark-linux.yml`） | 网络无法推送代码 |
| 本地 WSL distro | 存在 docker-desktop distro | 无 bash，无法执行命令 |

---

## 五、历史优化成果汇总（M7-T94 → T95）

虽然 Task 5.2 仍未通过，但以下真实性能优化已在代码库中落盘：

| 优化项 | 文件 | 效果（WSL2 环境下） |
|--------|------|-------------------|
| 4 workers + uvloop | Dockerfile | 并发能力提升 4x |
| uvloop 依赖 | requirements.txt | 事件循环效率提升 |
| 连接池优化 | database.py | pool_size=10, pre_ping |
| bcrypt 异步化 | services/auth.py + routers/auth.py | login ↓80% |

**优化前后对比（WSL2 环境）：**

| 端点 | T94 基线 | T95 优化后 | 改善幅度 | 目标 | 达标 |
|------|---------|-----------|---------|------|------|
| `/health` | 2252ms | 2270ms | ~0% | 50ms | FAIL |
| `/api/auth/login` | 21779ms | 4384ms | **↓80%** | 500ms | FAIL |
| `/api/datasets/` | 942ms | 717ms | ↓24% | 200ms | FAIL |
| `/api/experiments/` | 759ms | 607ms | ↓20% | 200ms | FAIL |
| `/api/datasets/upload` | 5411ms | 1896ms | **↓65%** | 3000ms | PASS |

---

## 六、风险与限制

### 6.1 未验证部分

- **原生 Linux 性能表现**：当前所有数据均来自 WSL2 环境
- **WSL2 与原生 Linux 的性能差异**：尚未有直接对比数据

### 6.2 阻塞因素

- **网络连接问题**：当前环境无法访问 GitHub.com，无法推送代码触发 CI
- **缺少原生 Linux 服务器**：本地环境仅有 Windows + Docker Desktop + WSL2

### 6.3 合理怀疑（未经证实）

基于 WSL2 网络栈的已知特性（多层跳转：Windows → WSL2 vNIC → Docker bridge → 容器），怀疑 `/health` 端点在原生 Linux 下 P95 可降至 < 50ms。但这**未经实验验证**。

---

## 七、是否建议提交 Task 5.2 验收

**不建议**。

理由：
- Task 5.2 计划明确要求"所有端点满足 P95 目标"
- 当前 5/5 端点仅 1/5 达标
- 无法确认在原生 Linux 环境下能否达标
- WSL2 归因仅为合理怀疑，未证实

---

## 八、修改文件清单

1. `.github/workflows/benchmark-linux.yml` — 创建 Linux benchmark workflow（未成功推送）

---

## 九、下一步建议

1. **在网络通畅的环境**推送代码到 GitHub
2. **在 GitHub Actions `ubuntu-latest` runner** 上执行 `.github/workflows/benchmark-linux.yml`
3. **对比 WSL2 vs Linux 结果**，确认环境归因是否成立
4. **只有 Linux 结果 5/5 全达标且无 5xx**，才允许收口 Task 5.2