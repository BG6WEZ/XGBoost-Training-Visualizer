# M7-T84-R — Phase-4 / Task 4.2 再收口（上传路径验证与响应头收敛）

> 任务编号：M7-T84-R  
> 阶段：Phase-4 / Task 4.2 Re-open  
> 前置：M7-T83（审计不通过）  
> 时间戳：2026-04-16 17:26:00  
> 执行人：AI Coding Agent

---

## 一、已完成任务编号

- **M7-T84**：Phase-4 / Task 4.2 再收口（上传路径验证与响应头收敛）

---

## 二、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `apps/web/nginx.conf` | 修改 | 移除 `expires 1y` 指令，避免与 `add_header Cache-Control` 产生双 Cache-Control 头 |

---

## 三、双 Cache-Control 头收敛

### 问题描述

上一轮验证中发现静态资源响应返回两条 `Cache-Control` 头：
```
Cache-Control: max-age=31536000           # 来自 expires 1y
Cache-Control: public, max-age=31536000, immutable  # 来自 add_header
```

### 修改方案

移除 `expires 1y` 指令，仅保留 `add_header Cache-Control`：

**修改前**：
```nginx
location ~* \.(js|css)$ {
    expires 1y;
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

**修改后**：
```nginx
location ~* \.(js|css)$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

### 验证结果

通过 `curl -I http://localhost:3001/assets/index-DbCZpVGF.js` 确认：
```
Cache-Control: public, max-age=31536000, immutable
```

✅ 仅返回单条 `Cache-Control` 头，收敛完成。

---

## 四、大文件上传验证

### 验证方法

使用 `curl` 向 Nginx 代理的上传端点发送 5MB 测试文件：

```bash
# 创建 5MB 测试文件
fsutil file createnew test_5mb.csv 5242880

# 通过 Nginx 上传（端口 3001）
curl.exe -s -o /dev/null -w "HTTP_CODE: %{http_code}\nSIZE_UPLOAD: %{size_upload}" \
  -X POST -F "file=@test_5mb.csv" http://localhost:3001/api/datasets/upload
```

### 验证结果

```
HTTP_CODE: 502
SIZE_UPLOAD: 5243080
TIME_TOTAL: 0.045225
```

### 结果分析

| 指标 | 值 | 说明 |
|------|-----|------|
| HTTP_CODE | 502 | Bad Gateway（测试容器中无 API 后端，预期行为） |
| SIZE_UPLOAD | 5,243,080 bytes (~5MB) | **文件全部通过 Nginx 发送** |
| 是否 413 | **否** | ✅ 未被 Nginx 以 `413 Request Entity Too Large` 拦截 |

**关键结论**：5MB 文件完整通过 Nginx 代理，证明 `client_max_body_size 500M` 配置生效，Nginx 没有提前拦截大文件上传。502 错误是因为测试容器中不存在 API 后端（`api:8000` 主机不可达），这是预期行为。

---

## 五、安全头验证结果

```
HTTP/1.1 200 OK
Server: nginx/1.29.8
X-Frame-Options: SAMEORIGIN                    ✅ 通过
X-Content-Type-Options: nosniff                ✅ 通过
X-XSS-Protection: 1; mode=block               ✅ 通过
Referrer-Policy: strict-origin-when-cross-origin  ✅ 通过
```

---

## 六、静态资源缓存头验证结果

```
HTTP/1.1 200 OK
Cache-Control: public, max-age=31536000, immutable  ✅ 通过（单条）
```

✅ 仅返回单条 `Cache-Control` 头，值为 `public, max-age=31536000, immutable`。

---

## 七、实际执行命令

```bash
# 1. 修改 nginx.conf（移除 expires 1y）

# 2. 重新构建 Docker 镜像
cd apps/web
docker build -t xgboost-vis-web:test .

# 3. 启动测试容器
docker run -d --name nginx-test -p 3001:3000 xgboost-vis-web:test

# 4. 验证静态资源缓存头
curl.exe -sI http://localhost:3001/assets/index-DbCZpVGF.js

# 5. 创建 5MB 测试文件
fsutil file createnew $env:TEMP\test_upload_5mb.bin 5242880

# 6. 大文件上传验证
curl.exe -s -o /dev/null -w "HTTP_CODE: %{http_code}\nSIZE_UPLOAD: %{size_upload}\nTIME_TOTAL: %{time_total}\n" \
  -X POST -F "file=@$env:TEMP\test_upload_5mb.bin;filename=test_5mb.csv;type=text/csv" \
  http://localhost:3001/api/datasets/upload

# 7. 清理测试环境
docker rm -f nginx-test
Remove-Item $env:TEMP\test_upload_5mb.bin -Force
```

---

## 八、已验证通过项

- [x] `apps/web/nginx.conf` 已更新（移除 `expires 1y`）
- [x] 4 个安全头均出现在首页响应中
- [x] 静态资源缓存头收敛为单条：`public, max-age=31536000, immutable`
- [x] 已实际验证 5MB 文件上传未被 Nginx 以 413 拦截
- [x] 报告附真实上传验证命令与结果
- [x] 产出与本轮编号一致的 `M7-T84-R-20260416-172600-p4-t42-upload-path-verification-and-header-cleanup-report.md`
- [x] 未越界推进到 Task 4.3 或后续任务

---

## 九、未验证部分

| 步骤 | 状态 | 说明 |
|------|------|------|
| 生产环境大文件上传 | ⚠️ 未执行 | 本次仅验证 Nginx 代理层，未验证端到端生产环境 |
| WebSocket 代理验证 | ⚠️ 未执行 | 需要 API 服务配合 |
| API 代理超时实际效果 | ⚠️ 未执行 | 需要长时间运行的请求验证 |

> **说明**：大文件上传的 Nginx 层验证已完成（5MB 文件通过代理，未被 413 拦截）。端到端验证需要完整 compose 环境，建议在 Phase-5 集成验收时统一验证。

---

## 十、风险与限制

1. **测试环境限制**：仅在独立 Nginx 容器中验证，API 后端不可达（502 预期）
2. **文件大小**：仅验证 5MB，未验证更大的文件（如 100MB+）
3. **网络环境**：测试在本地 Docker 网络中进行，与生产环境可能有差异

---

## 十一、建议

### 建议提交 Task 4.2 验收

**理由**：

1. `apps/web/nginx.conf` 已按要求更新，包含所有必须配置项
2. 双 `Cache-Control` 头已收敛为单条
3. 大文件上传未被 Nginx 以 413 拦截（5MB 文件完整通过代理，HTTP 502 非 413）
4. 4 个安全头验证全部通过
5. 静态资源缓存头验证通过
6. 已产出正式报告

**建议在提交验收前人工确认**：

- 确认完整 compose 环境中的大文件上传端到端验证
- 确认生产环境中大文件（如 50MB+）上传行为