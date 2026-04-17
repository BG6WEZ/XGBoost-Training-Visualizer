# M7-T67 汇报：Task 2.2 补测收口（CORS 预检请求闭环）

任务编号: M7-T67 (对应 LAUNCH_DEVELOPMENT_PLAN Task 2.2 Re-open)  
时间戳: 20260415-093200  
所属计划: LAUNCH_DEVELOPMENT_PLAN / Phase-2 Task 2.2 CORS 配置生产化 补测收口  
前置任务: M7-T66（审计不通过，缺少真实 HTTP 预检测试）

---

## 一、已完成任务

### 1. 保持现有配置收敛结果不退化

以下配置保持上一轮结果：
- `CORS_ORIGINS` 默认值为 `["http://localhost:3000"]`
- 环境变量支持逗号分隔解析
- `allow_methods` 为显式列表 `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`
- `allow_headers` 为显式列表 `["Content-Type", "Authorization", "Accept"]`

### 2. 新增真实 OPTIONS 预检请求测试

**修改文件：** `apps/api/tests/test_cors.py`

**新增测试类：** `TestCorsPreflight`

| 测试名称 | 验证点 |
|---------|--------|
| `test_cors_preflight_allows_configured_origin` | 允许的 origin 返回正确的 `access-control-allow-origin` 和 `access-control-allow-methods` |
| `test_cors_preflight_rejects_unconfigured_origin` | 未允许的 origin 不会返回匹配的 `access-control-allow-origin` |

---

## 二、修改文件清单

| 文件路径 | 修改目的 |
|---------|---------|
| `apps/api/tests/test_cors.py` | 新增 `TestCorsPreflight` 类（2 个真实 HTTP 预检测试） |

---

## 三、测试清单

### 配置解析测试（5 个，来自 M7-T66）

| 测试名称 | 类型 |
|---------|------|
| `test_cors_origins_default` | 配置解析 |
| `test_cors_origins_from_env` | 配置解析 |
| `test_cors_origins_from_env_with_empty_values` | 配置解析 |
| `test_cors_origins_from_env_single` | 配置解析 |
| `test_cors_origins_empty_env_falls_back_to_default` | 配置解析 |

### 预检请求测试（2 个，M7-T67 新增）

| 测试名称 | 类型 |
|---------|------|
| `test_cors_preflight_allows_configured_origin` | HTTP 预检 |
| `test_cors_preflight_rejects_unconfigured_origin` | HTTP 预检（负向） |

---

## 四、实际执行结果

### CORS 测试

**执行命令：**
```bash
cd apps/api
python -m pytest tests/test_cors.py -q --tb=short
```

**结果：**
```
7 passed in 5.25s
```

### 全量回归测试

**执行命令：**
```bash
cd apps/api
python -m pytest tests/ -q --tb=short
```

**结果：**
```
361 passed, 9 skipped, 1 warning in 130.79s (0:02:10)
```

**对比基线：** 359 passed → 361 passed（新增 2 个预检测试），0 failed

---

## 五、通过条件检查

- [x] `CORS_ORIGINS` 默认值仍为 `["http://localhost:3000"]`
- [x] 环境变量覆盖解析仍然正确
- [x] `allow_methods` 为显式列表
- [x] `allow_headers` 为显式列表
- [x] 至少 1 个真实 OPTIONS 预检请求测试通过（2 个通过）
- [x] 预检测试验证了 `access-control-allow-origin`
- [x] 全量回归通过（0 failed，361 passed）
- [x] 未越界推进到 Task 2.3 或后续任务

---

## 六、未验证部分

无。所有通过条件已验证。

---

## 七、风险与限制

无新增风险。

---

## 八、是否建议重新提交 Task 2.2 验收

**建议重新提交验收**

**原因：**
1. 所有通过条件已验证（8/8 勾选）
2. 全量测试无回归（361 passed, 0 failed）
3. 真实 HTTP OPTIONS 预检请求测试已补充（2 个）
4. 配置解析测试与预检测试已明确区分