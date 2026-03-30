# 数据资产清单与建模适配说明

> 版本：v1.0  
> 更新日期：2026-03-25  
> 目的：基于当前 `dataset/` 目录的真实内容，梳理数据资产、建模适配范围与导入约束，为软件功能设计和开发排期提供依据。

---

## 1. 文档结论

当前项目已经具备较强的数据基础，且数据类型明显超过“单一表格训练”范畴。软件需要支持的不是单一上传页，而是一套围绕数据资产管理、特征构造、实验训练与跨数据集验证的工作流。

从现有数据看，项目至少应支持以下四类核心场景：

1. 单建筑或单数据表的快速回归训练与结果可视化。
2. 多建筑、多站点的大规模基准训练与横向比较。
3. 天气、占用、HVAC 等多源时序特征融合。
4. 跨建筑、跨数据集的迁移验证与泛化评估。

---

## 2. 数据目录总览

| 数据源 | 文件数 | 体量 | 数据特征 | 适合场景 |
|------|------:|------:|------|------|
| `HEEW` | 306 | 1064.88 MB | 多建筑能耗与天气，含原始与清洗版本 | 单/多建筑回归、切分验证、迁移实验 |
| `ashrae-gepiii` | 7 | 2489.97 MB | 比赛型大规模训练/测试集，含天气与建筑元数据 | 基准训练、泛化评估、排行榜式验证 |
| `bdg2` | 95 | 1706.03 MB | 多站点、多建筑、多计量类型、带元数据与天气 | 多站点基准、数据质量分析、跨建筑比较 |
| `A three-year dataset...` | 32 | 2221.72 MB | 单建筑多传感器高频数据，含占用、HVAC、室内环境 | 多源特征融合、时序特征工程、解释性分析 |
| `google-trends-for-buildings-master` | 34 | 27.39 MB | Google Trends 外生行为代理数据 | 外部特征融合、研究型实验 |
| `building_energy_data_extended.csv` | 1 | 小样例 | 教学/演示用综合表 | 原型联调、流程演示、冒烟测试 |

---

## 3. 各数据源说明

### 3.1 `dataset/building_energy_data_extended.csv`

样例字段：

- `Timestamp`
- `Building_ID`
- `Energy_Usage (kWh)`
- `Temperature (°C)`
- `Humidity (%)`
- `Building_Type`
- `Occupancy_Level`

用途判断：

- 适合作为产品原型的默认演示数据。
- 适合验证列映射、基础训练、结果展示、前后端联调。
- 不适合作为真实算法能力评估基准。

建议定位：

- 作为 `demo` 级别内置示例数据。

### 3.2 `dataset/HEEW`

观察到的数据结构：

- `cleaned data/Total_energy.csv`：按 `Year/Month/Day/Hour` 组织的总能耗数据，包含 `Electricity`、`Cooling`、`Heat`、`Emission`、`Total Energy` 等字段。
- `cleaned data/Total_weather.csv`：同时间粒度天气数据，包含 `Temperature`、`Humidity`、`Wind Speed`、`Pressure`、`Precip` 等。
- `cleaned data/BNxxx_energy.csv`、`CNxx_energy.csv`：按建筑拆分的数据文件。
- 同时保留 `raw data/` 与 `cleaned data/` 两个层次。

用途判断：

- 支持“总表模式”和“单建筑模式”两种训练入口。
- 适合做建筑级回归预测、时间切分验证、建筑间迁移实验。
- 因为存在原始与清洗版本，软件应支持数据版本标识与质量状态标识。

建议定位：

- 作为 MVP 阶段最重要的数据资产之一。

### 3.3 `dataset/ashrae-gepiii/raw`

观察到的数据结构：

- `train.csv` / `test.csv`：比赛标准训练测试集。
- `weather_train.csv` / `weather_test.csv`：按 `site_id + timestamp` 关联的天气数据。
- `building_metadata.csv`：建筑元数据。
- `sample_submission.csv`：预测输出格式参考。

用途判断：

- 非常适合作为标准化 benchmark 数据源。
- 软件需要支持多表 Join，而不是只处理单 CSV。
- 因为存在官方测试集和提交样式，适合构建“离线评估 + 导出预测结果”的流程。

建议定位：

- 作为“基准验证模式”的首选数据集。

### 3.4 `dataset/bdg2`

观察到的数据结构：

- `data/meters/raw` 与 `data/meters/cleaned`：按表计类型拆分。
- `data/metadata/metadata.csv`：建筑、行业、面积、地理、计量类型等信息。
- `data/weather/weather.csv`：站点天气。
- `notebooks/`：提供了 EDA、数据质量、异常检测、模型评估等研究路径。

用途判断：

- 支持多建筑、多表计、多站点的大规模训练与分析。
- 软件应支持“选择 meter 类型”“选择站点”“按 building_id 聚合/筛选”。
- 非常适合后续扩展异常检测、天气敏感性、归一化分析等高级模块。

建议定位：

- 作为 P1 阶段的重要 benchmark 与分析型数据资产。

### 3.5 `dataset/A three-year dataset supporting research on building energy, HVAC controls, and occupancy analytics`

观察到的数据结构：

- `Bldg59_clean data/ele.csv`：15 分钟级电力相关序列。
- `Bldg59_clean data/occ.csv`：分钟级占用数据。
- `Bldg59_clean data/site_weather.csv`：15 分钟级天气。
- 还包含 `zone_temp_*`、`zone_co2.csv`、`wifi.csv`、`rtu_*`、`uft_*`、`ashp_*` 等 HVAC 与室内环境序列。
- 附带 Brick 模型和元数据 JSON。

用途判断：

- 这是最适合做“多源特征工程工作台”的数据源。
- 软件需要支持不同采样频率的对齐与重采样。
- 软件需要支持按特征组装：能耗、天气、占用、HVAC、室内环境。

建议定位：

- 作为 P1 阶段“高级特征工程”和“解释性分析”的核心数据集。

### 3.6 `dataset/google-trends-for-buildings-master`

观察到的数据结构：

- `google-trends-data_2016-2018.csv`：按日期、地区、主题记录的 Google Trends 数值。
- 配套 notebook 展示了与建筑能耗的相关性分析流程。

用途判断：

- 属于研究型外部特征，不适合放入 MVP 主流程。
- 适合作为“可选外生变量源”纳入高级实验。

建议定位：

- 作为 P2 阶段研究扩展模块。

---

## 4. 数据能力对产品功能的直接影响

### 4.1 必须支持的能力

1. 单文件、目录、多文件集合三种导入模式。
2. 时间列识别、实体列识别、目标列识别。
3. 多表关联：主表 + 天气表 + 建筑元数据。
4. 不同采样频率的重采样与对齐。
5. 原始数据与清洗数据的并行登记，不覆盖原文件。
6. 数据集级、建筑级、表计级的切分与筛选。

### 4.2 不能假定的数据前提

1. 不能假定所有数据都只有一个 `timestamp` 列名。
2. 不能假定所有数据都只有一个目标变量。
3. 不能假定所有数据都已完成清洗。
4. 不能假定所有数据都能直接训练，部分需要 Join、聚合或重采样。
5. 不能假定所有场景都是“上传文件后立刻训练”，因为仓库本身已经内置了大量数据集。

---

## 5. 推荐的内部数据抽象

为了统一不同来源的数据，建议在系统内部建立以下概念模型：

### 5.1 Dataset Source

表示数据来源类型，例如：

- `heew`
- `ashrae_gepiii`
- `bdg2`
- `bldg59`
- `google_trends`
- `demo`

### 5.2 Dataset Asset

表示一个可被软件登记和使用的数据资产，最少应包含：

- 数据源
- 文件路径、目录路径或文件集合
- 原始/清洗状态
- 时间范围
- 粒度
- 实体粒度
- 推荐目标列
- 可用特征组

补充说明：

- 一个数据集不应被限制为“单个 CSV 文件”。
- 数据集可以由一个目录下的多个 CSV 文件组成。
- 典型情况包括：
  - 主表 + 天气表 + 元数据表
  - 按建筑拆分的多个 CSV 共同构成一个数据集
  - 按时间分片的多个 CSV 共同构成一个数据集

### 5.3 Schema Profile

表示导入后识别出的模式信息：

- 时间列
- 实体列
- 目标列
- 数值列
- 分类列
- Join 键
- 缺失率
- 采样频率

### 5.4 Feature Recipe

表示一个可复用的特征构造方案：

- 原始列选择
- 重采样策略
- 缺失值处理
- 时间特征
- 滞后特征
- 滚动窗口特征
- 外部特征融合规则

### 5.5 Evaluation Profile

表示评估策略：

- 时间切分
- 随机切分
- 建筑留一验证
- 站点留一验证
- 官方测试集评估

---

## 6. 软件导入约束

### 6.1 数据管理原则

1. 不直接修改 `dataset/` 下原始文件。
2. 所有标准化结果输出到系统工作目录，如 `workspace/data/processed/`。
3. 所有数据转换都需要保留可追溯元数据。

### 6.2 最低导入元信息

每个已登记数据资产至少需要记录：

- `name`
- `source_type`
- `path`
- `path_type` (`file` / `directory` / `file_set`)
- `member_files`
- `is_raw`
- `time_column`
- `entity_column`
- `target_column`
- `granularity`
- `timezone`

### 6.3 推荐标准列名映射

导入后建议统一映射到以下逻辑名称：

- `timestamp`
- `entity_id`
- `target`
- `site_id`
- `weather_*`
- `occ_*`
- `hvac_*`
- `meta_*`

---

## 7. 对开发的直接建议

### P0

- 先打通 `demo + HEEW + ASHRAE` 三类数据。
- 先支持 CSV 和目录导入，不急于处理 Excel 和 Notebook。
- 先做回归任务，不扩展分类任务。

### P1

- 加入 `BDG2` 和 `Bldg59` 的多表融合支持。
- 增强特征工程、重采样、对齐和 benchmark 评估。

### P2

- 引入 Google Trends 等外部代理特征。
- 支持更复杂的跨域迁移实验与研究模式。

---

## 8. 本文档与其他文档的关系

- 该文档回答“我们现在手里有什么数据，能支撑什么软件能力”。
- 功能组合与产品范围见 `docs/specification/SOFTWARE_FUNCTION_BLUEPRINT.md`。
- 开发落地顺序见 `docs/planning/DEVELOPMENT_PREPARATION_GUIDE.md`。
