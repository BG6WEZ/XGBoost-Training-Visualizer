# M7-T06 任务单：M7-T04 审核修复与证据闭环

任务编号: M7-T06  
时间戳: 20260330-120000  
所属计划: P1-S1 / M7-T04 修复  
前置任务: M7-T04（审核结果：部分通过）  
优先级: 最高（阻断 M7-T07/后续任务）

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T04-20260330-112500-p1-t02-preprocessing-strategies-and-schema-alignment.md

---

## 一、任务背景

M7-T04 任务执行后，Copilot 审核结论为"部分通过"，存在以下阻断项：

1. **测试结果数据失实（阻断）**  
   报告声称"31 passed"，Copilot 独立复现实际结果为"2 failed, 29 passed"。  
   失败测试：`test_workspace_dir_config_consistency` 与 `test_both_services_have_identical_workspace_path`  
   根因：API 与 Worker 的 `WORKSPACE_DIR` 配置不一致（API = XGBoost Training Visualizer\workspace，Worker = project\workspace）。

2. **缺少真实 API 链路证据（阻断）**  
   任务单 §7.2 要求：请求 → task_id → 状态轮询 → 输出文件路径 → 处理摘要。  
   汇报仅提供了 schema 单元测试，无任何真实 API 调用证据。

3. **失败场景证据为文字描述而非实际输出（阻断）**  
   任务单 §7.3 要求贴出实际错误命令输出，汇报仅用文字声称"已验证"。

---

## 二、本任务目标

**仅做 M7-T04 的闭环修复，不做新功能开发。**

1. 修复 Workspace 路径不一致，让 `test_workspace_consistency.py` 全部通过。
2. 补齐真实 API 链路证据（pytest + mock 方式可接受，但必须包含完整链路断言）。
3. 补齐失败场景真实输出。

---

## 三、详细修复要求

### 修复 3.1：WORKSPACE_DIR 路径不一致

**现状**：
- API: `C:\Users\wangd\project\XGBoost Training Visualizer\workspace`
- Worker: `C:\Users\wangd\project\workspace`

**要求**：
- 检查 API 与 Worker 的 `.env` / `settings.py` / `Dockerfile` 中 `WORKSPACE_DIR` 的配置来源
- 确认正确路径，统一到同一个值
- 修复后运行以下命令验证：

```bash
cd apps/api
python -m pytest tests/test_workspace_consistency.py -v --tb=short
```

验收：**全部通过，0 failed**

---

### 修复 3.2：真实 API 链路证据

在测试文件中补充完整端到端链路测试（使用 mock 可接受），证据必须包含：

```python
# 示例结构（不要复制，按实际实现）
response = await client.post(f"/api/datasets/{dataset_id}/preprocess", json={...})
assert response.status_code == 200
task_id = response.json()["task_id"]
assert task_id is not None

# 验证任务状态可查询
status_response = await client.get(f"/api/tasks/{task_id}")
assert status_response.json()["status"] in ["queued", "running", "completed"]
```

执行命令：
```bash
cd apps/api
python -m pytest tests/test_preprocessing.py -v --tb=short
```

验收：
- 至少 1 个 `test_preprocessing_end_to_end_*` 测试通过
- 测试包含 task_id 断言

---

### 修复 3.3：失败场景真实输出

必须提供 **实际命令执行结果**，不能只用文字描述。  
以下两种形式均可接受：

**形式 A（pytest 失败场景测试）**：
```bash
cd apps/api
python -m pytest tests/test_preprocessing.py::TestPreprocessingValidation::test_preprocessing_invalid_* -v
```
要求：贴出实际 pytest 输出，断言清晰显示 422 或 ValueError 的具体字段

**形式 B（本地验证脚本）**：
```bash
cd apps/api
python -c "from app.schemas.dataset import PreprocessingConfig; PreprocessingConfig(missing_value_strategy='invalid')"
```
要求：贴出 ValidationError 的完整错误输出，包括字段路径

---

## 四、禁止事项

- 不得修改无关测试使其"看起来通过"
- 不得在汇报中省略失败测试（必须如实列出所有测试结果）
- 不得只更改配置环境变量而不验证两者路径确实一致

---

## 五、完成判定

以下条件**全部满足**才算完成：

- [ ] `test_workspace_consistency.py` 全部通过（0 failed）
- [ ] `test_new_endpoints.py` + `test_workspace_consistency.py` 合计通过总数 ≥ 31（0 failed）
- [ ] `test_preprocessing.py` 包含至少 1 个链路测试，含 task_id 断言
- [ ] 失败场景有实际命令输出（非文字描述）
- [ ] 汇报如实标注所有测试通过/失败数量

---

## 六、Copilot 审核重点

1. 实际运行 `test_workspace_consistency.py` 验证 0 failed
2. 对比汇报测试数量与实际运行结果是否一致
3. 链路测试中是否包含 task_id 字段断言
4. 失败场景是否有真实命令输出（截图或命令行粘贴）

---

## 七、汇报文件命名

```
docs/tasks/M7/M7-T06-R-20260330-120000-m7-t04-audit-fixes-and-evidence-closure-report.md
```
