# M7-T57 汇报：Task 1.2 存储路径穿越防护

任务编号: M7-T57 (对应 LAUNCH_DEVELOPMENT_PLAN Task 1.2)  
时间戳: 20260413-155400  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-1 Task 1.2  
前置任务: M7-T56（Task 1.1 统一密钥管理）

---

## 已完成任务

### 1. API 端存储适配层路径穿越防护

**实现内容：**
- `apps/api/app/services/storage.py` 中 `LocalStorageAdapter._get_full_path()` 增加路径穿越检查
- 使用 `os.path.normpath()` 规范化路径后，通过 `os.path.commonpath()` 检查结果是否仍在 `base_path` 内
- 如果检测到路径穿越（如 `../../etc/passwd`），抛出 `ValueError("Path traversal detected: {object_key}")`

**修改文件：** `apps/api/app/services/storage.py`

---

### 2. Worker 端存储适配层同步修复

**实现内容：**
- `apps/worker/app/storage.py` 中 `LocalStorageAdapter._get_full_path()` 同步增加相同的路径穿越检查逻辑
- 确保 API 和 Worker 两端防护一致

**修改文件：** `apps/worker/app/storage.py`

---

### 3. 新增路径穿越防护测试

**实现内容：**
- `test_path_traversal_blocked_double_dot`：测试 `../../etc/passwd` 类路径被阻止
- `test_path_traversal_blocked_encoded`：测试 `../../../tmp/evil.txt` 类路径被阻止
- `test_normal_path_allowed`：测试正常路径 `models/exp1/model.json` 允许
- `test_nested_normal_path_allowed`：测试深层正常路径 `preprocessing/dataset-001/task-001/processed.csv` 允许

**修改文件：** `apps/api/tests/test_storage.py`

---

## 修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/api/app/services/storage.py` | `_get_full_path()` 增加路径穿越检查 |
| `apps/worker/app/storage.py` | `_get_full_path()` 同步增加路径穿越检查 |
| `apps/api/tests/test_storage.py` | 新增 `TestPathTraversalProtection` 类（4 个测试），修复现有测试 Windows 路径兼容性 |

---

## 实际验证

### 新增测试

**命令：**
```bash
cd apps/api
python -m pytest tests/test_storage.py::TestPathTraversalProtection -v
```

**结果：**
```
tests/test_storage.py::TestPathTraversalProtection::test_path_traversal_blocked_double_dot PASSED [ 25%]
tests/test_storage.py::TestPathTraversalProtection::test_path_traversal_blocked_encoded PASSED [ 50%]
tests/test_storage.py::TestPathTraversalProtection::test_normal_path_allowed PASSED [ 75%]
tests/test_storage.py::TestPathTraversalProtection::test_nested_normal_path_allowed PASSED [100%]

=================== 4 passed in 0.23s ===================
```

### 全量后端测试回归验证

**命令：**
```bash
cd apps/api
python -m pytest tests/ -q --tb=short
```

**结果：**
```
342 passed, 9 skipped, 1 warning in 127.42s (0:02:07)
```

**对比基线：** 基线 336 passed → Task 1.1 后 338 passed → 当前 342 passed（新增 4 个测试），0 failed

---

## 通过条件检查

- [x] `_get_full_path()` 包含 `os.path.commonpath` 校验
- [x] 两个新增测试 passed（实际 4 个测试）
- [x] 全量测试无回归（342 passed, 0 failed）

---

## 风险与限制

1. **仅覆盖 LocalStorageAdapter**
   - MinIO 存储适配器不涉及路径穿越问题（对象键由 MinIO 服务端处理）
   - 如需额外防护，可在 MinIO 适配层也增加类似的 object_key 校验

2. **Windows 路径兼容性**
   - 测试断言已适配 Windows 路径分隔符（使用 `in` 检查而非精确字符串匹配）

---

## 是否建议继续下一任务

**建议继续**

**原因：**
1. 所有通过条件已验证
2. 全量测试无回归（342 passed, 0 failed）
3. 未越界推进后续任务
4. 风险与限制已如实记录