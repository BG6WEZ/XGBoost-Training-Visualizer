# M7-T67 — Task 2.2 补测收口（CORS 预检请求闭环）

> 任务编号：M7-T67  
> 阶段：Phase-2 / Task 2.2 Re-open  
> 前置：M7-T66（审计不通过）  
> 时间戳：20260415-092135

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T66-AUDIT-SUMMARY-20260415-092135.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 2.2`

---

## 一、本轮目标

本轮**不得进入 Task 2.3**。只允许继续收口 **Task 2.2 CORS 配置生产化**，补齐上一轮缺失的真实 HTTP 预检验证。

---

## 二、允许修改的范围文件

- `apps/api/app/config.py`
- `apps/api/app/main.py`
- `apps/api/tests/test_cors.py`
- 如确有必要，可新增极少量与 CORS 测试直接相关的测试辅助代码

禁止越界到：

- Docker
- Alembic
- 认证
- 前端
- 其他路由/业务逻辑

---

## 三、必须完成的最小工作

### 1) 保持现有配置收敛结果不退化

以下已完成项不得回退：

- `CORS_ORIGINS` 默认值为 `["http://localhost:3000"]`
- 环境变量支持逗号分隔解析
- `allow_methods` 为显式列表
- `allow_headers` 为显式列表

### 2) 新增真实 `OPTIONS` 预检请求测试

你必须在 `apps/api/tests/test_cors.py` 中新增真实 HTTP 行为测试，而不是只测配置解析。

至少包含一个测试验证：

- 对允许的 origin 发起 `OPTIONS` 预检请求
- 请求头包含：
  - `Origin`
  - `Access-Control-Request-Method`
  - 如有需要，`Access-Control-Request-Headers`

至少断言：

- 响应状态码符合 CORS 中间件预期
- `access-control-allow-origin` 等于允许的 origin
- `access-control-allow-methods` 包含显式配置的方法
- 如响应包含 `access-control-allow-headers`，其内容与显式配置一致或兼容

建议测试名：

- `test_cors_preflight_allows_configured_origin`

### 3) 建议补一个负向测试

虽然不是绝对强制，但强烈建议新增：

- 未允许 origin 的预检请求不应被正常放行，或至少不返回匹配的 `access-control-allow-origin`

建议测试名：

- `test_cors_preflight_rejects_unconfigured_origin`

### 4) 汇报必须如实区分“解析测试”和“预检测试”

报告中必须明确区分：

- 配置解析测试
- HTTP 预检行为测试

不得再出现：

- 只有解析测试，却写成“预检测试通过”

---

## 四、验证命令

至少执行以下命令，并在报告中附实际输出：

```bash
cd apps/api
..\..\.venv\Scripts\python.exe -m pytest tests/test_cors.py -q --tb=short
..\..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

如果你拆分了单测与集成测试，也要在报告中明确列出额外命令。

---

## 五、通过条件（全部满足才算通过）

- [ ] `CORS_ORIGINS` 默认值仍为 `["http://localhost:3000"]`
- [ ] 环境变量覆盖解析仍然正确
- [ ] `allow_methods` 为显式列表
- [ ] `allow_headers` 为显式列表
- [ ] 至少 1 个真实 `OPTIONS` 预检请求测试通过
- [ ] 预检测试验证了 `access-control-allow-origin`
- [ ] 全量回归通过（不得新增 failed）
- [ ] 未越界推进到 Task 2.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T67-R-<timestamp>-p2-t22-cors-preflight-closure-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 当前 `config.py` 默认值与解析逻辑
4. 当前 `main.py` 最终 CORS 配置
5. 解析测试清单
6. 预检请求测试清单
7. 实际执行命令
8. 实际输出原文
9. 未验证部分
10. 风险与限制
11. 是否建议重新提交 Task 2.2 验收

---

## 七、明确禁止

- 不得把配置解析测试写成预检行为测试
- 不得跳过真实 `OPTIONS` 请求验证
- 不得提前进入 Task 2.3
