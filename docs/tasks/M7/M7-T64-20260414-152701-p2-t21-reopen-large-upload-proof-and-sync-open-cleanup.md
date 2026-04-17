# M7-T64 — Task 2.1 复核修复（大文件证据重做 + 同步 open 清理）

> 任务编号：M7-T64  
> 阶段：Phase-2 / Task 2.1 Re-open  
> 前置：M7-T63（审计不通过）  
> 时间戳：20260414-152701

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T63-AUDIT-SUMMARY-20260414-152701.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 2.1`

---

## 一、本轮目标

本轮**不得进入 Task 2.2**。只允许继续收口 **Task 2.1 大文件上传异步行计数**，补齐以下两个阻断点：

1. 提供**真实达标**的 `>50MB` 非阻塞证据；
2. 移除 `upload_file()` 中剩余的同步 `open()` 调用，满足父任务通过条件。

---

## 二、允许修改的范围文件

- `apps/api/app/routers/datasets.py`
- `apps/api/tests/test_datasets.py`
- 如确有必要，可补充与本任务直接相关的测试辅助代码，但不得越界到 CORS、Docker、认证等其他任务

---

## 三、必须完成的最小工作

### 1) 清理 `upload_file()` 中剩余同步 `open()`

在 `apps/api/app/routers/datasets.py` 中：

- 处理 CSV 上传行计数时，不允许继续保留：
  - `sum(1 for _ in open(file_path, ...))`
- 小文件分支也要改为复用统一的异步实现，或用同等语义的非阻塞实现

通过要求：

- `upload_file()` 函数体内不再出现同步 `open(file_path...)` 计数逻辑
- 行计数语义保持正确：
  - 有表头时返回数据行数
  - 空文件与异常文件处理不退化

### 2) 重做 `>50MB` 非阻塞自动化测试

在 `apps/api/tests/test_datasets.py` 中重写或替换现有大文件测试，要求：

- 测试文件实际大小必须 **>50MB**
- 计时范围只能覆盖“发起上传请求到收到响应”，**不得把测试文件生成耗时混入验收时间**
- 必须有明确断言：
  - `assert response.status_code == 200`
  - `assert "row_count" in data`
  - `assert data["row_count"] is not None`
  - `assert elapsed < 30`

建议命名：

- `test_upload_large_csv_over_50mb_does_not_block`

实现建议：

- 使用固定宽度 payload，减少生成超大文件时的 Python 循环开销
- 若需要，可把“大文件生成”与“请求计时”拆成两个阶段
- 不允许再出现“目标 15MB、实际 10.5MB”这种与任务口径不一致的情况

### 3) 如实处理 `estimated` 分支

本轮**不是必须**验证 `>100MB` 采样估算分支，但汇报必须诚实：

- 如果没有实际跑到 `>100MB`，就写“未验证”
- 不得因为“代码逻辑已实现”就勾选为“已验证通过”

如你愿意额外补强，可增加一个更小成本的针对性测试来验证：

- `>100MB` 时响应中的 `estimated == true`

但该补强不是替代 `>50MB` 非阻塞证据的手段。

---

## 四、验证命令

至少执行以下命令，并在报告中附实际输出：

```bash
cd apps/api
..\..\.venv\Scripts\python.exe -m pytest tests/test_datasets.py::TestLargeFileUpload -q --tb=short -s
..\..\.venv\Scripts\python.exe -m pytest tests/test_datasets.py -q --tb=short
..\..\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

若你补了 `estimated` 分支验证，也要把对应命令列出。

---

## 五、通过条件（全部满足才算通过）

- [ ] `upload_file()` 中已无同步 `open()` 行计数调用
- [ ] 自动化测试实际上传文件大小 `>50MB`
- [ ] 测试对请求耗时有显式断言 `elapsed < 30`
- [ ] 上传返回 `200` 且包含 `row_count`
- [ ] 报告中对 `estimated` 分支区分“已验证 / 未验证”
- [ ] 全量回归通过（不得新增 failed）
- [ ] 未越界推进到 Task 2.2 或后续任务

---

## 六、汇报要求

完成后提交：

- `M7-T64-R-<timestamp>-p2-t21-reopen-large-upload-proof-and-sync-open-cleanup-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 删除/替换了哪段同步 `open()` 逻辑
4. 新测试名称、实际生成文件大小、核心断言
5. 实际执行命令
6. 实际输出原文（包含耗时）
7. 未验证部分
8. 风险与限制
9. 是否建议重新提交 Task 2.1 验收

---

## 七、明确禁止

- 不得修改 CORS 配置
- 不得提前做 Docker、Alembic、前端测试等后续任务
- 不得把“推断成立”写成“验证通过”
- 不得省略失败信息、耗时信息、文件大小信息

---

## 八、后续衔接

只有在 **M7-T64 审计通过** 后，才允许进入：

- Task 2.2 — CORS 配置生产化
