# M7-T83 — Phase-4 / Task 4.2 Nginx 反向代理生产配置

> 任务编号：M7-T83  
> 阶段：Phase-4 / Task 4.2  
> 前置：M7-T82（Task 4.1 验收通过）  
> 时间戳：20260416-165408

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T82-AUDIT-SUMMARY-20260416-165408.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.2`

---

## 一、本轮目标

进入 `Phase-4 / Task 4.2 — Nginx 反向代理生产配置`，目标是完善前端 Nginx 配置，使其更适合生产环境的安全性、上传能力和缓存策略要求。

---

## 二、允许修改的范围文件

- `apps/web/nginx.conf`
- 如确有必要，可补充极少量与本轮验证直接相关的说明
- 本轮新增报告文件：`docs/tasks/M7/M7-T83-R-<timestamp>-p4-t42-nginx-production-proxy-report.md`

禁止越界到：

- API / Worker / Frontend 业务逻辑
- Docker Compose 结构大改
- Task 4.3 或后续任务

---

## 三、必须完成的最小工作

### 1) 增加 4 个安全响应头

必须加入：

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

要求：

- 至少覆盖首页响应
- 若配置层级会影响静态资源或 SPA 路由，也要考虑一致性

### 2) 为 API 代理增加超时配置

必须加入：

```nginx
proxy_read_timeout 300s;
```

说明：

- 训练提交等请求可能较慢
- 应加在合适的 API 代理位置

### 3) 增加上传大小限制

必须加入：

```nginx
client_max_body_size 500M;
```

要求：

- 避免大文件上传被默认 Nginx 限制拦截

### 4) 完善静态资源缓存头

要求：

- js/css 文件返回：

```nginx
Cache-Control: public, max-age=31536000, immutable
```

- 当前仅有 `public, immutable` 还不够，需要补足 `max-age=31536000`

### 5) 必须做本轮验证

至少完成：

1. 前端镜像可构建
2. 启动后 `curl -I http://localhost:3000/` 可看到安全头

若能进一步验证，建议补做：

- 静态资源响应头检查
- 大文件上传路径不被 Nginx 提前拦截的验证

---

## 四、通过条件（全部满足才算通过）

- [ ] `apps/web/nginx.conf` 已更新
- [ ] 4 个安全头均出现在响应中
- [ ] API 代理包含 `proxy_read_timeout 300s`
- [ ] 已配置 `client_max_body_size 500M`
- [ ] 静态资源有 `Cache-Control: public, max-age=31536000, immutable`
- [ ] 前端镜像构建成功
- [ ] 产出与本轮编号一致的 `M7-T83-R-...` 报告
- [ ] 未越界推进到 Task 4.3 或后续任务

---

## 五、汇报要求

完成后提交：

- `M7-T83-R-<timestamp>-p4-t42-nginx-production-proxy-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 新增了哪些安全头
4. API 代理超时如何配置
5. 上传大小限制如何配置
6. 静态资源缓存头如何配置
7. 实际验证命令
8. 实际响应头结果
9. 已验证通过项
10. 未验证部分
11. 风险与限制
12. 是否建议提交 Task 4.2 验收

---

## 六、明确禁止

- 不得只改配置而不做响应头验证
- 不得提前进入 Task 4.3
- 不得把未验证的上传行为写成已验证通过
