# M4-T10 任务指令：无告警回归与 M4 收口确认

**任务编号**: M4-T10  
**发布时间**: 2026-03-28 22:16:21  
**前置任务**: M4-T09（已审核通过）  
**预期汇报文件名**: `M4-T10-R-20260328-221621-warning-free-regression-and-m4-closure-report.md`

---

## 零、开始前必须先做

执行任何操作之前，按顺序完成以下检查：

- [ ] 读取 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 读取 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 读取本任务单全文

---

## 一、任务背景

M4-T09 已修复 `metrics-history` 的 404 契约语义，并通过：
- `tests/test_results_extended_contract.py`：14 passed
- 全量回归：49 passed

但在全量回归输出中仍出现非阻断告警：
- `PytestUnhandledThreadExceptionWarning`
- 根因堆栈指向 `aiosqlite` 连接线程在事件循环关闭后回调（`Event loop is closed`）

这类告警会影响 CI 稳定性与质量门禁可信度，需在 M4 正式收口前清理。

---

## 二、任务目标

### 任务 1：清理 aiosqlite 线程告警

排查并修复测试资源释放时序，重点关注：
- `apps/api/tests/test_results_extended_contract.py` 中 `async_client` fixture
- 其他使用 `sqlite+aiosqlite:///:memory:` 的 fixture

建议修复动作：
1. fixture 结束前显式关闭/清理会话与依赖覆盖
2. 对创建的 engine 执行 `await engine.dispose()`
3. 避免后台线程在 loop 关闭后仍回调

### 任务 2：验证告警清零

执行命令并提供原始输出：

```bash
python -m pytest tests/test_results_extended_contract.py -v --tb=short
python -m pytest tests/test_results_contract.py tests/test_results_extended_contract.py tests/test_e2e_validation_regression.py tests/test_workspace_consistency.py tests/test_observability_regression.py --tb=short
```

验收要求：
- 保持通过数不下降（14 / 49）
- 输出中不出现 `PytestUnhandledThreadExceptionWarning`
- 输出中不出现 `RuntimeError: Event loop is closed`

### 任务 3：M4 收口核对

在汇报中补充 M4 两条完成标准的最终证据指针：
1. "能查看单次结果" 的证据（接口/测试文件）
2. "能对比两次以上实验" 的证据（`/api/results/compare` 对应用例）

---

## 三、内部智能体分工建议

| 智能体 | 负责范围 |
|--------|---------|
| backend-expert | 修复 fixture 资源释放与异步清理时序 |
| qa-engineer | 回归测试与告警扫描 |
| tech-lead | 汇总 M4 收口证据并输出报告 |

---

## 四、必须提供的实测证据

1. 两条 pytest 命令的完整输出（含 summary）
2. 告警清零证据（输出中无 threadexception warning）
3. 关键修复代码片段（fixture teardown / engine.dispose）

---

## 五、禁止事项

- 禁止通过过滤 warning（例如强行 `-p no:warnings`）来掩盖问题
- 禁止减少测试集合以回避告警
- 禁止引入 skip/xfail 覆盖失败

---

## 六、完成判定

以下条件全部满足才算完成：

- [ ] 全量回归仍 49 passed（或更高）
- [ ] 无 `PytestUnhandledThreadExceptionWarning`
- [ ] 无 `Event loop is closed`
- [ ] 汇报包含 M4 收口证据指针
