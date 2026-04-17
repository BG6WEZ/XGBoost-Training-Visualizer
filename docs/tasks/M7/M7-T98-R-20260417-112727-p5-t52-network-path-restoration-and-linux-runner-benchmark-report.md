# M7-T98-R — Phase-5 / Task 5.2 网络恢复与 Linux Runner Benchmark 报告（阻塞）

> 任务编号：M7-T98  
> 阶段：Phase-5 / Task 5.2 Re-open  
> 前置：M7-T96-R（已确认无法取得原生 Linux 环境，结论 B）  
> 时间戳：2026-04-17 11:27:27

---

## 一、本轮目标

1. 恢复到 GitHub 的网络路径
2. 推送当前代码
3. 在 GitHub Actions `ubuntu-latest` 上执行 `benchmark-linux.yml`
4. 用 Linux 结果继续判断 Task 5.2

---

## 二、网络诊断与尝试

### 2.1 发现的问题

| 步骤 | 发现 | 操作 |
|------|------|------|
| 检查代理配置 | `http.proxy=http://127.0.0.1:7890` | 代理指向本地，但代理服务未运行 |
| 取消代理 | `git config --global --unset http.proxy` | 执行成功 |
| 首次尝试 push | `Failed to connect to github.com port 443 via 127.0.0.1` | 仍走代理 |
| curl 测试 | `curl https://github.com` 返回 HTML | 网络可达 |
| 再次 push | `Recv failure: Connection was reset` | TLS 连接被重置 |
| 调整 HTTP/1.1 | `Failed to connect to github.com port 443 after 21088 ms` | 超时 |

### 2.2 根因分析

当前 Windows 环境存在系统级网络限制：

1. **curl 可以访问** GitHub（HTTP 层可达）
2. **git push 失败**（Git 协议/TLS 层被阻断）
3. **可能原因**：
   - 防火墙/杀毒软件拦截 Git TLS 连接
   - 网络策略限制 Git over HTTPS
   - 之前的代理配置留有残余影响

### 2.3 已尝试的修复

| 修复项 | 命令 | 结果 |
|--------|------|------|
| 取消 http.proxy | `git config --global --unset http.proxy` | ✓ 执行成功 |
| 取消 https.proxy | `git config --global --unset https.proxy` | ✓ 执行成功 |
| 增大 postBuffer | `git config --global http.postBuffer 524288000` | 无效 |
| 降级 HTTP/1.1 | `git config --global http.version HTTP/1.1` | 无效 |

---

## 三、已创建但未执行的 Linux Benchmark 配置

### 3.1 Workflow 文件

`.github/workflows/benchmark-linux.yml` 已创建，配置如下：

- 触发方式：`workflow_dispatch`（手动触发）
- Runner：`ubuntu-latest`（原生 Linux）
- 步骤：
  1. `actions/checkout@v4`
  2. 安装 Python 3.11 + httpx
  3. 启动 Docker Compose 全栈
  4. 等待服务就绪
  5. 执行 `python scripts/benchmark.py --base-url http://localhost:8000`

### 3.2 执行条件

该 workflow 需要：
1. 代码成功推送到 GitHub ✓ 未满足（网络阻断）
2. 在 GitHub Actions 页面手动触发

---

## 四、当前阻塞状态

| 项目 | 状态 | 原因 |
|------|------|------|
| 代码推送 | ✗ 阻塞 | Git TLS 连接被重置/超时 |
| GitHub Actions 触发 | ✗ 阻塞 | 代码未推送 |
| Linux benchmark 执行 | ✗ 阻塞 | 依赖上两项 |

---

## 五、已验证结论

基于 M7-T94 → T95 的优化成果（均在 WSL2 环境下）：

| 优化项 | 效果 |
|--------|------|
| 4 workers + uvloop | 并发能力提升 4x |
| bcrypt 异步化 | login ↓80% |
| 连接池优化 | 减少连接等待 |
| upload 端点 | P95 从 5411ms 降至 1896ms ✓ 达标 |

---

## 六、是否建议提交 Task 5.2 验收

**不建议**。

理由：
- 无法取得原生 Linux 环境 benchmark 结果
- 当前网络阻断，无法完成 M7-T96/M7-T98 要求的 Linux 复核
- WSL2 归因仅为合理怀疑，未证实

---

## 七、替代方案建议

### 方案 A：手动在 GitHub Actions 触发

1. 在**网络通畅的机器**上执行：
   ```bash
   git push origin master
   ```
2. 在 GitHub 仓库页面手动触发 `benchmark-linux.yml` workflow
3. 获取 Linux benchmark 结果

### 方案 B：使用其他 Linux 云主机

如果有可用的 AWS/GCP/Azure 等 Linux 实例，可以直接部署 Docker Compose 并执行 benchmark。

### 方案 C：诚实结论

如果确实无法获取原生 Linux 环境，则 Task 5.2 的"所有端点满足 P95 目标"在当前环境下不可验证。需要在开发计划中明确标注此限制。

---

## 八、修改文件清单

无新增文件修改。本轮仅网络诊断尝试。

---

## 九、风险与限制

- **网络阻断**：当前环境 Git push 不可用，无法独立完成 Linux 复核
- **环境限制**：仅有 Windows + Docker Desktop + WSL2
- **时间成本**：继续在当前环境调试网络可能浪费大量时间