# M7-T66 — Task 2.2 CORS 配置生产化

> 任务编号：M7-T66  
> 阶段：Phase-2 / Task 2.2  
> 前置：M7-T65（Task 2.1 已通过）  
> 时间戳：20260415-084206

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T65-AUDIT-SUMMARY-20260415-084206.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 2.2`

---

## 一、本轮目标

进入 `Task 2.2 — CORS 配置生产化`，目标是把当前 API 的跨域配置从宽松开发态收敛到可上线的显式配置，同时保留开发环境的基本可用性。

---

## 二、允许修改的范围文件

- `apps/api/app/config.py`
- `apps/api/app/main.py`
- `apps/api/tests/` 下与 CORS 直接相关的测试文件

如需新增测试，建议：

- `apps/api/tests/test_cors.py`

禁止越界到：

- Docker
- Alembic
- 认证
- 前端
- 其他路由/业务逻辑

---

## 三、具体要求

### 1) `CORS_ORIGINS` 默认值收敛

在 `apps/api/app/config.py` 中：

- `CORS_ORIGINS` 默认值改为：

```python
["http://localhost:3000"]
```

要求：

- 不再默认包含额外源
- 语义上明确这是开发态默认值

### 2) 支持环境变量覆盖

生产环境必须可通过环境变量 `CORS_ORIGINS` 注入真实域名。

要求：

- 支持逗号分隔字符串解析为 `List[str]`
- 自动去除首尾空格
- 不得把空字符串解析成无效 origin

建议覆盖示例：

```bash
CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

### 3) `allow_methods` 显式化

在 `apps/api/app/main.py` 中，将：

- `allow_methods=["*"]`

改为：

```python
["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
```

### 4) `allow_headers` 显式化

在 `apps/api/app/main.py` 中，将：

- `allow_headers=["*"]`

改为：

```python
["Content-Type", "Authorization", "Accept"]
```

---

## 四、测试要求

至少补充以下自动化验证：

### 1) 环境变量覆盖测试

新增测试：

- `test_cors.py::test_cors_origins_from_env`

验证点：

- 设置 `CORS_ORIGINS` 环境变量后，应用使用解析后的 origin 列表

### 2) OPTIONS 预检请求测试

新增或补充测试，验证：

- 对允许的 origin 发起 `OPTIONS` 预检请求
- 响应包含正确的 `Access-Control-Allow-Origin`
- 响应的方法/头字段与显式配置一致

如你愿意补强，也可增加“未允许 origin 不应被放行”的负向测试，但不是强制项。

---

## 五、验证命令

至少执行以下命令，并在报告中附实际输出：

```bash
cd apps/api
..\..\.venv\Scripts\python.exe -m pytest tests/test_cors.py -q --tb=short
..\..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

如果测试文件名不是 `test_cors.py`，请在报告中明确说明实际路径与命令。

---

## 六、通过条件（全部满足才算通过）

- [ ] `CORS_ORIGINS` 默认值为 `["http://localhost:3000"]`
- [ ] 环境变量可覆盖并正确解析多个 origin
- [ ] `allow_methods` 为显式列表
- [ ] `allow_headers` 为显式列表
- [ ] `OPTIONS` 预检请求测试通过
- [ ] 全量回归通过（不得新增 failed）
- [ ] 未越界推进到 Task 2.3 或后续任务

---

## 七、汇报要求

完成后提交：

- `M7-T66-R-<timestamp>-p2-t22-cors-productionization-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. `config.py` 中的默认值与解析逻辑
4. `main.py` 中的最终 CORS 配置
5. 新增测试名称与验证点
6. 实际执行命令
7. 实际输出原文
8. 未验证部分
9. 风险与限制
10. 是否建议进入 Task 2.3

---

## 八、明确禁止

- 不得把生产域名硬编码到默认值中
- 不得保留 `allow_methods=["*"]`
- 不得保留 `allow_headers=["*"]`
- 不得跳过 CORS 自动化测试
- 不得提前进入 Task 2.3
