# M7-T17 任务单：P1-T06 多表 Join 与数据融合

任务编号: M7-T17  
时间戳: 20260331-164748  
所属计划: P1-S2 / P1-T06  
前置任务: M7-T16（已完成）  
优先级: 高

---

## 零、开始前必须先做

在执行任何操作前，必须先完整阅读以下文件：

- [ ] docs/collaboraion/CLAUDE_WORK_RULES.md
- [ ] docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md
- [ ] docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md
- [ ] docs/tasks/M7/M7-T01-20260330-110500-p1-p2-agent-dev-plan-and-governance.md（重点阅读 P1-T06 验收标准）
- [ ] docs/tasks/M7/M7-T16-20260331-160630-p1-t05-frontend-quality-report-page-and-visualization.md
- [ ] docs/tasks/M7/M7-T16-R-20260331-160630-p1-t05-frontend-quality-report-page-and-visualization-report.md

未完成上述预读，不得开始执行。

---

## 一、任务背景

当前系统支持上传单个 CSV/XLSX 文件并对其进行预处理、特征工程、训练等操作。但在真实业务场景中，计能源/天气预测往往需要多个数据源的融合：

- 主表：建筑用电数据（timestamp + value）
- 天气表：气象观测数据（timestamp + temperature + humidity + ...）
- 元数据表：建筑属性（building_id + area + construction_type + ...）

本任务用于补齐数据融合能力，允许用户通过配置 Join 键将多个数据源融合成一个训练数据集。

---

## 二、任务目标

完成一个可实际使用、可验证、可扩展的多表 Join 能力，至少实现以下功能：

1. API 端点支持多表 Join 配置和执行（后端）。
2. 支持通过 Join 键（可配置）将天气表与主表关联。
3. 支持通过 Join 键将元数据表与主表关联。
4. Join 后的行数变化可解释（输出 before/after 及变化原因）。
5. 前端提供 Join 配置界面与结果反馈（可选但建议）。

---

## 三、范围边界

### 3.1 允许修改

**后端**:
- apps/api/app/schemas/dataset.py（新增 Join 配置 schema）
- apps/api/app/routers/datasets.py（新增 Join 端点）
- apps/api/app/services/（新增或修改数据融合服务）
- apps/api/tests/（新增 Join 相关测试）

**前端**（可选）:
- apps/web/src/lib/api.ts（新增 Join API 方法）
- apps/web/src/pages/DatasetDetailPage.tsx（可选入口）
- apps/web/src/components/（可选 Join 配置组件）

**其他**:
- docs/tasks/M7/M7-T17-20260331-164748-p1-t06-multi-table-join-and-data-fusion.md
- docs/tasks/M7/M7-T17-R-20260331-164748-p1-t06-multi-table-join-and-data-fusion-report.md（执行完成后生成）
- docs/planning/MILESTONE_TASK_REPORT_MAPPING.md

### 3.2 禁止修改

- 训练执行链路（apps/worker/**）
- 数据库模型与迁移（apps/api/app/models/**, apps/api/migrations/**）
- 与 Join 无关的前端页面大范围重构
- 提前实现 P1-T07 或任何后续任务

---

## 四、详细交付要求

### 4.1 Join 配置 Schema 定义

在 `apps/api/app/schemas/dataset.py` 中新增 Join 相关数据模型：

```python
class JoinTable(BaseModel):
    """Join 表配置"""
    name: str  # 表名或数据源标识（如 "weather", "metadata"）
    file_path: str  # 文件路径
    join_key: str  # 用于关联的键名（如 "timestamp", "building_id"）
    join_type: str = "left"  # join 类型：left/inner/right/outer

class JoinConfig(BaseModel):
    """多表 Join 配置"""
    main_dataset_id: str  # 主表数据集 ID
    main_join_key: str  # 主表中的键名
    join_tables: List[JoinTable]  # 要关联的表列表

class JoinResult(BaseModel):
    """Join 执行结果"""
    success: bool
    before_rows: int  # Join 前行数
    after_rows: int  # Join 后行数
    rows_lost: int  # 丢失的行数（不匹配的记录）
    rows_added_columns: int  # 新增的列数
    message: str  # 执行结果说明
    joined_columns: List[str]  # 新增的列名
```

### 4.2 Join 执行 API 端点

新增 POST 端点用于执行 Join 操作：

**建议路径**: `POST /api/datasets/{dataset_id}/join`

**请求体**:
```json
{
  "main_join_key": "timestamp",
  "join_tables": [
    {
      "name": "weather",
      "file_path": "data/weather.csv",
      "join_key": "timestamp",
      "join_type": "left"
    },
    {
      "name": "metadata",
      "file_path": "data/metadata.csv",
      "join_key": "building_id",
      "join_type": "left"
    }
  ]
}
```

**响应体**:
```json
{
  "success": true,
  "before_rows": 100,
  "after_rows": 98,
  "rows_lost": 2,
  "rows_added_columns": 15,
  "message": "Join 成功完成。2 条主表记录因无匹配而被过滤。新增 15 列。",
  "joined_columns": ["temperature", "humidity", "area", "construction_type", ...]
}
```

**错误场景**:
- 主表数据集不存在：404
- Join 键不存在于主表：422（附具体键名）
- 从表文件不存在：422（附文件路径）
- 从表中 Join 键缺失：422（附表名与键名）
- Join 类型非法：422（建议的有效类型列表）

### 4.3 Join 执行后的数据处理

Join 成功后，系统应该：

1. **生成融合数据集**: 将 Join 结果写入 workspace 中新的临时或正式文件。
2. **记录行数变化**: 在 stats 中记录 before/after/lost 数据。
3. **列映射**: 记录新增列与源表的对应关系（可选）。

示意伪码：
```python
def execute_join(main_dataset, join_config):
    df_main = load_dataset(main_dataset)
    result = {
        'before_rows': len(df_main),
        'joined_columns': []
    }
    
    for join_table in join_config.join_tables:
        df_join = load_dataset(join_table.file_path)
        
        # 执行 Join
        df_main = pd.merge(
            df_main,
            df_join,
            left_on=join_config.main_join_key,
            right_on=join_table.join_key,
            how=join_table.join_type
        )
        
        result['joined_columns'].extend([...])
    
    result['after_rows'] = len(df_main)
    result['rows_lost'] = result['before_rows'] - result['after_rows']
    
    # 保存融合数据
    save_dataset(df_main, ...)
    
    return result
```

### 4.4 容错与验证

必须处理的异常情况：

- 文件不存在或损坏：返回 422 + 具体错误
- 编码问题：自动尝试多种编码格式（UTF-8, GBK, Latin-1）
- 行数不匹配导致的行丢失：在响应中明确告知丢失行数及原因
- 列重名：自动重命名或返回警告

---

## 五、多角色协同执行要求（强制）

本任务必须采用内部多角色协同并在汇报中明确责任归属：

1. `Backend-Service-Agent`：实现 Join 配置 schema、API 端点、Join 执行逻辑。
2. `Data-Quality-Agent`：验证 Join 结果的正确性（行数、列数、值匹配）、容错逻辑。
3. `Frontend-Integration-Agent`（可选）：若实现前端配置界面，负责 UI/UX。
4. `QA-Agent`：测试覆盖（正常场景、失败场景、边界值）、门禁验证。
5. `Reviewer-Agent`：范围漂移检查、文档一致性、验收标准闭环。

汇报中必须按角色拆分职责说明，不接受混杂的总结段落。

---

## 六、必须提供的实测证据

### 6.1 后端单元测试

```bash
python -m pytest apps/api/tests/test_join.py -q
```

至少包含以下测试用例：

- `test_join_weather_table_success`：主表 + 天气表 Join 成功
- `test_join_metadata_table_success`：主表 + 元数据表 Join 成功  
- `test_join_with_missing_key`：从表中缺少 Join 键时返回 422
- `test_join_with_nonexistent_file`：文件不存在时返回 422
- `test_join_rows_lost_calculation`：行数丢失情况下的 before/after 准确
- `test_join_column_count`：新增列数准确

要求：所有测试通过，一条跳过的算失败。

### 6.2 后端回归测试

```bash
python -m pytest apps/api/tests/test_new_endpoints.py apps/api/tests/test_preprocessing.py -q
```

要求：不得破坏现有数据注册、预处理、特征工程链路。

### 6.3 真实 Join 链路证据（必须）

至少提供以下真实证据：

1. **成功链路**: 
   - 主表 + 天气表 Join
   - 输入参数 + 返回结果（包含 before_rows/after_rows/rows_lost）

2. **行数变化链路**:
   - 展示主表与从表的行数
   - 展示 Join 后行数与丢失行数说明
   - 说明丢失的原因（如 timestamp 不匹配）

3. **失败链路**:
   - 从表文件不存在时的错误响应
   - 从表中缺少 Join 键时的错误响应
   - 错误消息可读

证据形式：真实 API 请求/响应、测试输出、数据对比说明，禁止使用示例值冒充。

---

## 七、完成判定

以下条件全部满足才可宣称完成：

- [ ] Join 配置 Schema 已定义，包含 join_type、join_key、from/to 表路径
- [ ] Join API 端点已实现，支持多表级联 Join
- [ ] Join 执行结果包含 before_rows/after_rows/rows_lost/joined_columns
- [ ] 至少覆盖 2 类场景：天气表 Join + 元数据表 Join
- [ ] Join 键缺失或表文件不存在时返回可读 422 错误
- [ ] 行数变化可解释（from/to 明确、丢失原因可追踪）
- [ ] 单元测试 >= 6 条全部通过
- [ ] 后端回归测试全部通过，不破坏现有链路
- [ ] 提供 2 成功 + 2 失败真实链路证据
- [ ] 汇报按统一格式与多角色分工提交
- [ ] 未越界推进 P1-T07 或其他后续任务

---

## 八、Copilot 审核重点

1. Join 键是否真的可配置，还是硬编码在代码中。
2. 行数变化的计算是否准确，是否能解释丢失原因。
3. 是否真实处理了从表缺字段的场景，还是只处理了 happy path。
4. API 错误响应是否可读且具体，而非泛化的 "Join failed"。
5. 是否越界修改了数据库迁移或训练链路。
6. 汇报中的证据是否为真实执行结果，而非示例值。

---

## 九、风险提示

1. **行数不匹配的处理**: 天气表可能没有所有 timestamp，需要明确说明 left join 与 inner join 的差异及后果。
2. **列名冲突**: 若主表与从表有相同列名，需要明确重命名策略。
3. **编码问题**: CSV 可能使用不同编码（GBK vs UTF-8），需要做容错。
4. **大文件性能**: 若从表很大，Join 可能耗时；允许采样，但需明确说明。

---

## 十、汇报文件命名

本任务预期汇报文件：

`docs/tasks/M7/M7-T17-R-20260331-164748-p1-t06-multi-table-join-and-data-fusion-report.md`

执行完成后必须按该命名提交统一证据汇报。

---

## 十一、停点要求

本任务完成并提交汇报后，必须停点等待人工验收；未经确认不得推进 M7-T18 / P1-T07。
