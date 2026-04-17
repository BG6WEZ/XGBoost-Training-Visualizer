# M7-T65 — Task 2.1 继续收口（延迟根因定位 + 30s 门槛达标）

> 任务编号：M7-T65  
> 阶段：Phase-2 / Task 2.1 Re-open Again  
> 前置：M7-T64（审计不通过）  
> 时间戳：20260415-082924

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T64-AUDIT-SUMMARY-20260415-082924.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 2.1`

---

## 一、本轮目标

本轮仍然**不得进入 Task 2.2**。只允许继续收口 **Task 2.1 大文件上传异步行计数**，本轮的唯一目标是：

1. 找到 `>50MB` 上传请求阶段耗时过长的根因；
2. 让目标测试真实满足 `elapsed < 30`；
3. 用代码与测试证据证明达标。

---

## 二、允许修改的范围文件

- `apps/api/app/routers/datasets.py`
- `apps/api/app/services/storage.py`
- `apps/api/tests/test_datasets.py`
- 如确有必要，可增加与本任务直接相关的测试辅助代码

禁止越界到：

- CORS
- Docker
- Alembic
- 认证
- 前端

---

## 三、必须完成的最小工作

### 1) 先做延迟拆分，定位慢点

你必须先定位 `elapsed=81.95s` 的主要耗时来源，至少拆分以下阶段中的时间：

1. 请求体上传/落盘
2. `pd.read_csv(file_path, nrows=100)` 头部读取
3. `count_lines_async(file_path)` 行计数
4. 响应序列化

要求：

- 可以用临时 instrumentation、日志或测试内测量
- 最终报告必须列出每段耗时
- 如果 instrumentation 只是调试辅助，任务完成前可删除；如果保留，需保证代码整洁

### 2) 修复真实瓶颈，而不是修改门槛

你必须围绕根因做修复，允许但不限于以下方向：

- 优化 `upload_file()` 中 CSV 元信息读取方式，避免不必要的 pandas 成本
- 优化 `count_lines_async()` 的读取粒度/实现方式
- 优化测试上传方式，确保计时只覆盖真正要验收的请求阶段
- 对 `>50MB` 但 `<100MB` 的 CSV，考虑更合适的行数统计策略，但前提是：
  - 不得牺牲正确性
  - 不得把“估算”伪装成“精确计数”
  - 若改为估算，必须同步修改接口语义并补充测试，且需先证明符合 Task 2.1 原意

注意：

- 不允许把验收标准从 `30s` 改成 `120s` 或 `300s`
- 不允许只加超时配置，不解决真实耗时

### 3) 重写目标测试，显式断言 30s 门槛

目标测试：

- `test_upload_large_csv_over_50mb_does_not_block`

必须满足：

- 实际文件大小 `>50MB`
- 计时范围只覆盖请求阶段
- 显式断言：
  - `assert response.status_code == 200`
  - `assert "row_count" in data`
  - `assert data["row_count"] is not None`
  - `assert elapsed < 30`

如果当前环境下仍无法满足 `30s`：

- 本轮任务视为未完成
- 必须在报告中明确写失败，不得再勾选通过

### 4) 汇报必须诚实区分

- 已验证：只写实际跑过并拿到输出的内容
- 未验证：明确列出
- 失败项：必须原样写出，不得省略

特别禁止：

- 把 `Timeout(300)` 说成“显式耗时断言”
- 把“建议阈值”写成“已通过阈值”
- 把“未来生产环境可达标”写成“当前已达标”

---

## 四、验证命令

至少执行以下命令，并在报告中附完整输出：

```bash
cd apps/api
..\..\.venv\Scripts\python.exe -m pytest tests/test_datasets.py::TestLargeFileUpload::test_upload_large_csv_over_50mb_does_not_block -q --tb=short -s
..\..\.venv\Scripts\python.exe -m pytest tests/test_datasets.py -q --tb=short
..\..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

若你增加了耗时拆分日志/辅助测试，也必须把对应命令列出。

---

## 五、通过条件（全部满足才算通过）

- [ ] `>50MB` 目标测试实际运行通过
- [ ] 测试代码中存在显式断言 `assert elapsed < 30`
- [ ] 实际输出中的 `elapsed` 小于 30 秒
- [ ] 上传返回 `200` 且包含 `row_count`
- [ ] 报告给出请求阶段耗时拆分证据
- [ ] 未擅自修改任务门槛
- [ ] 全量回归通过（不得新增 failed）
- [ ] 未越界推进到 Task 2.2 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T65-R-<timestamp>-p2-t21-latency-root-cause-and-threshold-compliance-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 本轮定位到的主要耗时点
4. 采取的修复措施
5. 目标测试代码中的核心断言
6. 实际文件大小
7. 实际 `elapsed`
8. 耗时拆分明细
9. 全量测试结果
10. 未验证部分
11. 风险与限制
12. 是否建议重新提交 Task 2.1 验收

---

## 七、明确禁止

- 不得把客户端超时配置当成性能达标证据
- 不得把任务门槛从 30s 改成任何更宽松值
- 不得省略失败输出
- 不得进入 Task 2.2

---

## 八、后续衔接

只有在 **M7-T65 审计通过** 后，才允许进入：

- Task 2.2 — CORS 配置生产化
