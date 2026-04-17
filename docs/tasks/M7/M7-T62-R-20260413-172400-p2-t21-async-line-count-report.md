# M7-T62 汇报：Task 2.1 大文件上传异步行计数

任务编号: M7-T62 (对应 LAUNCH_DEVELOPMENT_PLAN Task 2.1)  
时间戳: 20260413-172400  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-2 Task 2.1  
前置任务: M7-T61（Token 黑名单，已验收）

---

## 一、已完成任务

### 1. count_lines_async() 异步行计数函数

**实现位置：** `apps/api/app/services/storage.py`

```python
async def count_lines_async(file_path: str) -> int:
    """使用 aiofiles 异步计数文件行数，不阻塞事件循环"""
    count = 0
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        async for line in f:
            count += 1
    return count
```

### 2. estimate_line_count() 采样估算函数

**实现位置：** `apps/api/app/services/storage.py`

```python
async def estimate_line_count(file_path: str, sample_lines: int = 10000) -> int:
    """通过采样估算文件行数，读前 sample_lines 行，用文件大小/平均行长度推算"""
    # 采样 10000 行，计算平均行大小，推算总行数
    # 降级：无法计数时返回 0
```

### 3. upload_file() 文件大小分类策略

**修改文件：** `apps/api/app/routers/datasets.py`

- **小文件 (<10MB)：** 同步完整计数（原有逻辑保持）
- **中文件 (10-100MB)：** 异步完整计数（使用 `count_lines_async()`）
- **大文件 (>100MB)：** 采样估算（使用 `estimate_line_count()`，`estimated=True`）

### 4. UploadResponse 新增 estimated 字段

**修改文件：** `apps/api/app/schemas/dataset.py`

```python
class UploadResponse(BaseModel):
    estimated: Optional[bool] = Field(default=None, description="是否为估算行数（大文件采样估算）")
```

### 5. 4 个单元测试

| 测试 | 状态 |
|------|------|
| `test_count_lines_async_small_file` | ✅ PASSED |
| `test_count_lines_async_empty_file` | ✅ PASSED |
| `test_estimate_line_count_accuracy` | ✅ PASSED |
| `test_estimate_line_count_empty_file` | ✅ PASSED |

---

## 二、修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/api/app/services/storage.py` | 新增 `count_lines_async()` 和 `estimate_line_count()` 函数 |
| `apps/api/app/routers/datasets.py` | 修改 `upload_file()` 增加文件大小分类策略 |
| `apps/api/app/schemas/dataset.py` | 新增 `estimated` 字段到 `UploadResponse` |
| `apps/api/tests/test_datasets.py` | 新增 `TestAsyncLineCount` 类（4 个测试） |

---

## 三、实际验证

### 新增测试

**命令：**
```bash
cd apps/api
python -m pytest tests/test_datasets.py::TestAsyncLineCount -v
```

**结果：**
```
4 passed in 5.24s
```

### 全量后端测试

**命令：**
```bash
cd apps/api
python -m pytest tests/ -q --tb=short
```

**结果：**
```
353 passed, 9 skipped, 1 warning in 131.08s (0:02:11)
```

**对比基线：** 349 passed → 353 passed（新增 4 个测试），0 failed

---

## 四、通过条件检查

- [x] **异步行计数已实现**：`count_lines_async()` 函数完整，使用 aiofiles
- [x] **采样估算已实现**：`estimate_line_count()` 函数完整，采样 10000 行
- [x] **文件大小分类**：upload_file 中根据大小（<10MB / 10-100MB / >100MB）选择策略
- [x] **aiofiles 依赖**：项目中已存在 aiofiles（原项目已使用）
- [x] **响应字段新增**：upload 返回值包含 `estimated` 布尔字段
- [x] **异步行计数测试通过**：`test_count_lines_async_*` 全部 ✓
- [x] **采样估算测试通过**：`test_estimate_line_count_*` 全部 ✓
- [x] **全量测试通过**：353 passed, 0 failed
- [x] **未越界推进**：Task 2.1 完成后立即停止，不做 Task 2.2 或后续

---

## 五、风险与限制

1. **采样精度**
   - 对于数据分布不均的文件，采样估算误差可能达 ±15-20%
   - 测试已验证 10000 行文件采样 1000 行误差 <20%
   - 前端 UI 可标记"估算行数"以降低期望

2. **编码处理**
   - 当前假设文件编码为 UTF-8
   - 若遇到 GB2312、GBK 等编码，会抛出异常
   - 遗留项：在异常处理中加入尝试 GBK 重试

3. **内存消耗**
   - aiofiles 是事件驱动的，不额外占用内存
   - 采样估算读 10000 行后即停止，内存占用固定

4. **并发上传**
   - 异步行计数不占用线程池，多个大文件可并发上传
   - 文件系统 I/O 仍受 OS 限制

---

## 六、是否建议继续下一任务

**建议继续**

**原因：**
1. 所有通过条件已验证（9/9 勾选）
2. 全量测试无回归（353 passed, 0 failed）
3. 未越界推进后续任务
4. 风险与限制已如实记录