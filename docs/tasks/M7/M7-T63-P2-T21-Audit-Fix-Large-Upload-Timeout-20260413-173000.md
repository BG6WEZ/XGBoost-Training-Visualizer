# M7-T63 — Task 2.1 审计补测修复（大文件非阻塞证据）

> 任务编号：M7-T63  
> 阶段：Phase-2 / Task 2.1 Audit Fix  
> 前置：M7-T62（有条件通过，缺少关键验收证据）  
> 时间戳：20260413-173000

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T62-AUDIT-SUMMARY-20260413-173000.md`

---

## 一、补测目标

补齐 Task 2.1 的唯一阻断项：**证明大文件上传不会因行计数而阻塞/超时**。

---

## 二、必须完成的最小工作

### 1) 自动化测试（必做）

在 `apps/api/tests/test_datasets.py` 新增等价用例（名称可不同，但语义必须一致）：
- 用例目标：上传大文件时请求可在阈值内返回，不出现超时。
- 推荐阈值：30s（与任务单一致）。
- 断言：
  1. `status_code == 200`
  2. 响应含 `row_count`
  3. 对触发估算分支的文件，`estimated == true`

建议命名：`test_upload_large_csv_does_not_block`。

### 2) 手工链路证据（二选一，推荐都做）

- A. >50MB 文件上传耗时截图/日志
- B. >100MB 文件上传耗时截图/日志（可触发采样估算分支）

输出至少包含：
- 文件大小
- 请求总耗时
- 响应 JSON 关键字段（`row_count`, `estimated`）

---

## 三、验证命令

```bash
cd apps/api
python -m pytest tests/test_datasets.py -q --tb=short
python -m pytest tests/ -q --tb=short
```

若提供手工验证：
```bash
# 启动 API 后进行上传
curl -X POST http://localhost:8000/api/datasets/upload -F "file=@<large-file.csv>" -w "\nTime: %{time_total}s\n"
```

---

## 四、通过条件（全部满足）

- [ ] 已新增“上传大文件不阻塞”测试并通过
- [ ] 大文件上传返回 200 且含 `row_count`
- [ ] 触发估算分支时 `estimated=true`
- [ ] 全量回归通过（0 failed）
- [ ] 补充报告中明确区分自动化验证与手工验证

---

## 五、汇报要求

补测完成后提交：
- `M7-T63-R-<timestamp>-p2-t21-audit-fix-large-upload-timeout-report.md`

汇报必须包含：
1. 修改文件清单
2. 新增测试名称与核心断言
3. 实际执行命令
4. 实际输出（耗时和测试结果）
5. 风险与限制
6. 是否建议进入 Task 2.2

---

## 六、后续衔接

M7-T63 通过后，下一任务：
- Task 2.2 CORS 配置生产化（M7-T64）
