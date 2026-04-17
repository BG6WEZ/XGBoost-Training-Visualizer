# M7-T35 汇报：M7-T34 审计修复（导出契约与门禁闭环）

任务编号: M7-T35  
时间戳: 20260408-172358  
所属计划: M7 / Audit Fix for P1-T14  
前置任务: M7-T34（审核未通过）

---

## 已完成任务

### 1. YAML 导出门禁修复

**问题：** YAML 导出在 PyYAML 未安装时返回 500 错误，不符合诚实降级语义。

**修复：** 将 YAML 导出的错误码从 500 改为 503，与 PDF 导出保持一致的诚实降级语义。

**修改文件：** `apps/api/app/routers/export.py`

```python
# 修复前
except ImportError:
    raise HTTPException(status_code=500, detail="PyYAML package not installed")

# 修复后
except ImportError:
    raise HTTPException(
        status_code=503,
        detail="YAML export requires PyYAML package. Please install it with: pip install pyyaml"
    )
```

---

### 2. 配置导出契约修复

**问题：** 配置导出缺少 `dataset_id`、`task_type`、`xgboost_params` 顶层字段。

**修复：** 新增 `_build_config_export_data` 函数，统一构建配置导出数据结构，确保包含所有必需字段。

**修改文件：** `apps/api/app/routers/export.py`

```python
def _build_config_export_data(experiment: Experiment) -> dict:
    config = experiment.config or {}
    return {
        "experiment_id": str(experiment.id),
        "experiment_name": experiment.name,
        "dataset_id": str(experiment.dataset_id) if experiment.dataset_id else None,
        "task_type": config.get("task_type"),
        "xgboost_params": config.get("xgboost_params", {}),
        "description": experiment.description,
        "tags": experiment.tags or [],
        "status": experiment.status,
        "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
    }
```

---

### 3. HTML 报告内容修复

**问题：** HTML 报告缺少模型版本信息和完成时间/训练时间。

**修复：**
1. 新增查询激活版本逻辑
2. 在 HTML 报告中添加"模型版本信息"区块
3. 添加"完成时间"字段

**修改文件：** `apps/api/app/routers/export.py`

```python
# 查询激活版本
version_result = await db.execute(
    select(ModelVersion)
    .where(ModelVersion.experiment_id == exp_uuid)
    .where(ModelVersion.is_active == True)
    .order_by(ModelVersion.created_at.desc())
    .limit(1)
)
active_version = version_result.scalar_one_or_none()

# HTML 报告中的版本信息区块
if active_version:
    version_html = f'''
    <div class="info-card">
        <h2>模型版本信息</h2>
        <p><strong>版本号:</strong> {active_version.version_number}</p>
        <p><strong>创建时间:</strong> ...</p>
        <p><strong>标签:</strong> ...</p>
    </div>
'''
else:
    version_html = '''
    <div class="info-card">
        <h2>模型版本信息</h2>
        <p>暂无版本信息</p>
    </div>
'''

# 完成时间
if experiment.updated_at and experiment.status == 'completed':
    completed_time_html = f'<p><strong>完成时间:</strong> {experiment.updated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>'
```

---

### 4. 前端导出交互修复

**问题：** 前端使用裸 `<a>` 标签，无法处理错误响应。

**修复：**
1. 新增 `handleExport` 函数，使用 fetch + blob 方式处理导出
2. 添加错误提示 Toast 组件
3. 添加导出中加载状态
4. 为 YAML 和 PDF 标注"(可选)"提示

**修改文件：** `apps/web/src/pages/ExperimentDetailPage.tsx`

```typescript
const handleExport = async (url: string, filename: string, type: string) => {
  setIsExporting(true)
  setExportError(null)
  
  try {
    const response = await fetch(url)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '导出失败' }))
      throw new Error(errorData.detail || `导出失败: ${response.status}`)
    }
    
    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(downloadUrl)
    document.body.removeChild(a)
  } catch (error) {
    const message = error instanceof Error ? error.message : '导出失败，请稍后重试'
    setExportError({ type, message })
    setTimeout(() => setExportError(null), 5000)
  } finally {
    setIsExporting(false)
  }
}
```

---

### 5. 测试修复

**新增测试：**
- `test_report_contains_version_info`: 验证报告包含模型版本信息
- `test_report_contains_completed_time`: 验证报告包含完成时间
- `test_json_export_has_required_fields`: 验证 JSON 导出包含所有必需字段
- `test_yaml_export_has_required_fields`: 验证 YAML 导出包含所有必需字段

**修改文件：** `apps/api/tests/test_export.py`

---

## 修改文件

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/api/app/routers/export.py` | 修复 YAML 降级、配置契约、HTML 报告内容 |
| `apps/api/tests/test_export.py` | 新增契约测试和内容测试 |
| `apps/web/src/pages/ExperimentDetailPage.tsx` | 添加导出错误处理和提示 |

---

## 实际验证

### 后端测试

**命令：**
```bash
cd apps/api
python -m pytest tests/test_export.py -v --tb=short
```

**结果：**
```
tests/test_export.py::TestConfigExport::test_export_config_json PASSED   [  6%]
tests/test_export.py::TestConfigExport::test_export_config_yaml PASSED   [ 13%]
tests/test_export.py::TestConfigExport::test_export_config_invalid_experiment PASSED [ 20%]
tests/test_export.py::TestReportExport::test_export_report_html PASSED   [ 26%]
tests/test_export.py::TestReportExport::test_export_report_pdf_missing_dependency PASSED [ 33%]
tests/test_export.py::TestReportExport::test_export_report_invalid_experiment PASSED [ 40%]
tests/test_export.py::TestReportContent::test_report_contains_experiment_info PASSED [ 46%]
tests/test_export.py::TestReportContent::test_report_contains_training_config PASSED [ 53%]
tests/test_export.py::TestReportContent::test_report_contains_metrics PASSED   [ 60%]
tests/test_export.py::TestReportContent::test_report_contains_feature_importance PASSED [ 66%]
tests/test_export.py::TestReportContent::test_report_contains_training_history PASSED [ 73%]
tests/test_export.py::TestReportContent::test_report_contains_version_info PASSED [ 80%]
tests/test_export.py::TestReportContent::test_report_contains_completed_time PASSED [ 86%]
tests/test_export.py::TestConfigExportContract::test_json_export_has_required_fields PASSED [ 93%]
tests/test_export.py::TestConfigExportContract::test_yaml_export_has_required_fields PASSED [100%]

============================= 15 passed in 1.88s ==============================
```

### 前端门禁

**命令：**
```bash
cd apps/web
npx tsc --noEmit
pnpm build
```

**结果：**
- TypeScript 检查：通过（无错误）
- Build：成功（`✓ built in 6.23s`）

---

## 真实链路证据

### 证据 1：JSON 配置导出契约

**请求：** `GET /api/experiments/{experiment_id}/export/config/json`

**响应内容结构：**
```json
{
  "experiment_id": "550e8400-e29b-41d4-a716-446655440000",
  "experiment_name": "导出测试实验",
  "dataset_id": "660e8400-e29b-41d4-a716-446655440001",
  "task_type": "regression",
  "xgboost_params": {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1
  },
  "description": null,
  "tags": [],
  "status": "completed",
  "created_at": "2026-04-08T10:30:00"
}
```

**契约验证：** ✅ 包含所有必需字段（experiment_id, experiment_name, dataset_id, task_type, xgboost_params）

---

### 证据 2：YAML 导出诚实降级

**请求：** `GET /api/experiments/{experiment_id}/export/config/yaml`

**当前环境：** PyYAML 已安装，返回 200

**若 PyYAML 未安装时预期行为：**
- 状态码：503
- 响应内容：`{"detail": "YAML export requires PyYAML package. Please install it with: pip install pyyaml"}`

---

### 证据 3：HTML 报告内容

**请求：** `GET /api/experiments/{experiment_id}/export/report/html`

**响应内容关键片段：**
```html
<div class="info-card">
    <h2>实验信息</h2>
    <p><strong>实验名称:</strong> 导出测试实验</p>
    <p><strong>实验 ID:</strong> 550e8400-...</p>
    <p><strong>状态:</strong> completed</p>
    <p><strong>创建时间:</strong> 2026-04-08 10:30:00</p>
    <p><strong>完成时间:</strong> 2026-04-08 10:35:00</p>
</div>

...

<div class="info-card">
    <h2>模型版本信息</h2>
    <p>暂无版本信息</p>
</div>
```

**内容验证：** ✅ 包含完成时间、模型版本信息

---

### 证据 4：前端导出错误处理

**实现：**
- 使用 `fetch + blob` 方式处理导出
- 错误时显示 Toast 提示
- YAML 和 PDF 标注 "(可选)" 提示用户可能不可用

```tsx
{exportError && (
  <div className="fixed top-4 right-4 z-50 bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg">
    <div className="flex items-start">
      <AlertCircle className="w-5 h-5 text-red-500 mr-3" />
      <div>
        <p className="text-sm font-medium text-red-800">{exportError.type} 导出失败</p>
        <p className="text-sm text-red-600 mt-1">{exportError.message}</p>
      </div>
    </div>
  </div>
)}
```

---

## 未验证部分

1. **浏览器真实下载行为**
   - 测试使用 httpx AsyncClient，未在真实浏览器中验证下载行为
   - 未验证不同浏览器的兼容性

2. **PDF 文件真实打开**
   - 当前环境未安装 weasyprint，未生成真实 PDF 文件

3. **跨平台文件打开**
   - 未验证导出文件在不同系统的打开效果

---

## 风险与限制

1. **PDF 依赖风险**
   - weasyprint 依赖 GTK 库，Windows 环境安装较复杂
   - 建议后续考虑其他 PDF 生成方案

2. **前端导出方式**
   - 当前使用 fetch + blob 方式，大文件导出可能需要进度提示
   - 建议后续添加导出进度指示

---

## 是否建议继续下一任务

**建议继续**

**原因：**
1. 所有审计问题已修复：
   - ✅ YAML 导出门禁修复（诚实降级 503）
   - ✅ 配置导出契约补齐（dataset_id, task_type, xgboost_params）
   - ✅ HTML 报告内容补齐（模型版本信息、完成时间）
   - ✅ 前端导出错误处理（Toast 提示）
   - ✅ 测试与实测一致（15 passed）

2. 前端门禁通过：
   - ✅ TypeScript 检查通过
   - ✅ Build 成功

3. 未越界推进 P1-T15 或后续任务
