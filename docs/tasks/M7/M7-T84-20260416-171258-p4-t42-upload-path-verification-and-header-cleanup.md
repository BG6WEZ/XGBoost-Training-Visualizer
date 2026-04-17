# M7-T84 — Phase-4 / Task 4.2 再收口（上传路径验证与响应头收敛）

> 任务编号：M7-T84  
> 阶段：Phase-4 / Task 4.2 Re-open  
> 前置：M7-T83（审计不通过）  
> 时间戳：20260416-171258

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T83-AUDIT-SUMMARY-20260416-171258.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 4.2`

---

## 一、本轮目标

本轮**不得进入 Task 4.3**。只允许继续收口 **Task 4.2 Nginx 反向代理生产配置**，重点补齐：

1. **大文件上传不被 Nginx 拦截的真实验证**
2. **静态资源双 `Cache-Control` 头的收敛（建议项）**

---

## 二、允许修改的范围文件

- `apps/web/nginx.conf`
- 如确有必要，可补充极少量与验证直接相关的说明
- 本轮新增报告文件：`docs/tasks/M7/M7-T84-R-<timestamp>-p4-t42-upload-path-verification-and-header-cleanup-report.md`

禁止越界到：

- API / Worker / Frontend 业务逻辑
- Task 4.3 或后续任务
- 与本轮验证无关的 Docker 结构大改

---

## 三、上一轮未通过的核心问题

你必须逐项消除以下问题：

1. **大文件上传路径仍未验证**
   - 原计划通过条件明确要求：`大文件上传不被 Nginx 拦截`
   - 上一轮报告明确写了“未执行”

2. **静态资源存在双 `Cache-Control` 头**
   - 当前响应中出现两条 `Cache-Control`
   - 建议本轮收敛为单一、明确的目标值

---

## 四、必须完成的最小工作

### 1) 验证大文件上传不会被 Nginx 提前拦截

至少完成一种真实验证方式：

#### 方案 A：真实上传验证

- 通过前端或直接 HTTP 请求向上传路径发送较大文件
- 文件大小应足以覆盖“超过默认 1MB 限制”的场景
- 结果需证明请求没有被 Nginx 以 `413 Request Entity Too Large` 提前拦截

#### 方案 B：受控构造验证

- 使用一个明显大于 1MB 的测试文件
- 对实际上传端点发起请求
- 即使最终被应用层拒绝，也必须证明**不是** Nginx 拒绝

要求：

- 必须有真实命令与真实响应
- 必须明确区分“被应用层拒绝”和“被 Nginx 拒绝”

### 2) 若可能，收敛静态资源双 `Cache-Control` 头

目标：

- 最终尽量只返回一条明确的目标缓存头

推荐方向：

- 调整 `expires` 与 `add_header Cache-Control` 的组合方式

要求：

- 不得破坏 `public, max-age=31536000, immutable`

### 3) 必须重新验证安全头与静态资源缓存头

至少再次验证：

1. 首页安全头仍存在
2. 静态资源缓存头仍满足目标值

### 4) 报告必须附真实验证证据

至少包含：

- 大文件上传测试命令
- 上传响应状态码
- 响应体或关键错误信息
- 安全头检查结果
- 静态资源缓存头检查结果

### 5) 未验证项必须如实写明

若仍有无法验证内容，必须明确写：

- 哪些未验证
- 原因是什么

但本轮**不得**再把“大文件上传不被 Nginx 拦截”列为未验证。

---

## 五、通过条件（全部满足才算通过）

- [ ] `apps/web/nginx.conf` 保持满足安全头 / 超时 / 上传限制 / 缓存策略要求
- [ ] 4 个安全头均出现在响应中
- [ ] 静态资源缓存头满足目标值
- [ ] 已实际验证大文件上传未被 Nginx 以 413 拦截
- [ ] 报告附真实上传验证命令与结果
- [ ] 产出与本轮编号一致的 `M7-T84-R-...` 报告
- [ ] 未越界推进到 Task 4.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T84-R-<timestamp>-p4-t42-upload-path-verification-and-header-cleanup-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 大文件上传如何验证
4. 上传响应结果与是否经过 Nginx 拦截
5. 安全头验证结果
6. 静态资源缓存头验证结果
7. 实际执行命令
8. 已验证通过项
9. 未验证部分
10. 风险与限制
11. 是否建议提交 Task 4.2 验收

---

## 七、明确禁止

- 不得继续把“大文件上传不被 Nginx 拦截”留在未验证区
- 不得把应用层拒绝误写成 Nginx 拒绝
- 不得提前进入 Task 4.3
