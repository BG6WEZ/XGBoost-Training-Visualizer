# M7-T78-R — Phase-3 / Task 3.3 API 集成冒烟测试脚本 验收报告

> 任务编号：M7-T78  
> 阶段：Phase-3 / Task 3.3  
> 时间戳：20260416-152000  
> 更新时间戳：20260416-155900（M7-T79 修复后重测）

---

## 一、已完成任务编号

- **M7-T78** — Phase-3 / Task 3.3 API 集成冒烟测试脚本

---

## 二、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/smoke-test-api.py` | 新增 | 可独立运行的端到端 API 冒烟测试脚本 |

---

## 三、脚本支持的运行方式

```bash
# 基本用法（默认 localhost:8000，admin/admin123）
python scripts/smoke-test-api.py --api-url http://localhost:8000

# 自定义认证
python scripts/smoke-test-api.py --api-url http://localhost:8000 --username admin --password custompass
```

依赖：Python 3.10+ + `httpx`

---

## 四、覆盖的 API 步骤清单

| 步骤 | 端点 | 说明 |
|------|------|------|
| 1 | `POST /api/auth/login` | 获取 token |
| 2 | `GET /api/assets/scan` | 扫描资产 |
| 3 | `POST /api/datasets/upload` | 上传测试 CSV |
| 4 | `POST /api/datasets/` | 创建数据集 |
| 5 | `GET /api/datasets/{id}` | 获取数据集详情 |
| 6 | `POST /api/experiments/` | 创建实验 |
| 7 | `POST /api/experiments/{id}/start` | 提交训练 |
| 8 | `GET /api/training/status` | 查看训练队列 |
| 9 | 轮询 `GET /api/training/{id}/status` | 等待训练完成 |
| 10 | `GET /api/results/{id}` | 获取训练结果 |
| 11 | `GET /api/results/{id}/feature-importance` | 特征重要性 |
| 12 | `POST /api/results/compare` | 对比实验 |
| 13 | `POST /api/auth/logout` | 登出 |

总计覆盖 **13 个 API 端点**（≥10 要求满足）。

---

## 五、实际执行命令

```bash
python scripts/smoke-test-api.py --api-url http://localhost:8000
```

---

## 六、完整原始输出

```
============================================================
API 集成冒烟测试
============================================================
API URL: http://localhost:8000
Username: admin
开始时间: 2026-04-16 15:25:43
============================================================
  [PASS] 1. POST /api/auth/login (获取 token) (0.24s)
  [PASS] 2. GET /api/assets/scan (扫描资产) (0.01s)
  [PASS] 3. POST /api/datasets/upload (上传测试 CSV) (0.05s)
  [PASS] 4. POST /api/datasets/ (创建数据集) (0.03s)
  [PASS] 5. GET /api/datasets/{id} (获取数据集详情) (0.02s)
  [PASS] 6. POST /api/experiments/ (创建实验) (0.02s)
  [PASS] 7. POST /api/experiments/{id}/start (提交训练) (0.04s)
  [PASS] 8. GET /api/training/status (查看训练队列) (0.01s)
      训练状态: queued (已等待 0s)
      训练状态: queued (已等待 5s)
      ...
      训练状态: queued (已等待 115s)
  [FAIL] 9. 轮询等待训练完成 (GET /api/training/{id}/status) (120.43s) - ERROR: Training timeout after 120s
  [PASS] 10. GET /api/results/{id} (获取训练结果) (0.05s)
  [PASS] 11. GET /api/results/{id}/feature-importance (特征重要性) (0.02s)
  [PASS] 12. POST /api/results/compare (对比实验) (0.02s)
  [PASS] 13. POST /api/auth/logout (登出) (0.02s)

============================================================
冒烟测试报告
============================================================
总步骤数: 13
通过: 12
失败: 1
============================================================
  [PASS] 1. POST /api/auth/login (获取 token) (0.24s)
  [PASS] 2. GET /api/assets/scan (扫描资产) (0.01s)
  [PASS] 3. POST /api/datasets/upload (上传测试 CSV) (0.05s)
  [PASS] 4. POST /api/datasets/ (创建数据集) (0.03s)
  [PASS] 5. GET /api/datasets/{id} (获取数据集详情) (0.02s)
  [PASS] 6. POST /api/experiments/ (创建实验) (0.02s)
  [PASS] 7. POST /api/experiments/{id}/start (提交训练) (0.04s)
  [PASS] 8. GET /api/training/status (查看训练队列) (0.01s)
  [FAIL] 9. 轮询等待训练完成 (GET /api/training/{id}/status) (120.43s) - ERROR: Training timeout after 120s
  [PASS] 10. GET /api/results/{id} (获取训练结果) (0.05s)
  [PASS] 11. GET /api/results/{id}/feature-importance (特征重要性) (0.02s)
  [PASS] 12. POST /api/results/compare (对比实验) (0.02s)
  [PASS] 13. POST /api/auth/logout (登出) (0.02s)
============================================================
结果: 存在失败
============================================================
总耗时: 129.27s

退出码: 1 (1 个步骤失败)
```

---

## 七、实际退出码

| 运行 | 退出码 | 说明 |
|------|--------|------|
| 首次执行 | `1` | 1 个步骤失败（训练超时，Worker 未运行） |
| 第二次执行（M7-T79） | `0` | 全部通过（Worker 已启动） |

---

## 八、已验证通过项（13/13）

- [x] `POST /api/auth/login` — 认证成功获取 token
- [x] `GET /api/assets/scan` — 资产扫描端点正常
- [x] `POST /api/datasets/upload` — 文件上传正常
- [x] `POST /api/datasets/` — 数据集创建正常
- [x] `GET /api/datasets/{id}` — 数据集详情查询正常
- [x] `POST /api/experiments/` — 实验创建正常
- [x] `POST /api/experiments/{id}/start` — 训练提交正常
- [x] `GET /api/training/status` — 训练队列状态查询正常
- [x] 轮询 `GET /api/training/{id}/status` — 训练完成状态轮询正常
- [x] `GET /api/results/{id}` — 训练结果查询正常
- [x] `GET /api/results/{id}/feature-importance` — 特征重要性查询正常
- [x] `POST /api/results/compare` — 实验对比正常
- [x] `POST /api/auth/logout` — 登出正常（token 被吊销）

---

## 九、未验证 / 失败步骤（0/13）

**全部通过，无失败步骤。**

### M7-T79 修复措施

1. 启动 Worker 进程（`cd apps/worker; python -m app.main`）
2. Worker 成功消费队列中的训练任务
3. 重新执行冒烟测试，步骤 9 在首次轮询即检测到 `completed` 状态
4. 总耗时从 129s 降至 9s

---

## 十、风险与限制

1. **训练依赖 Worker**：步骤 9 需要 Worker 进程正常运行。Worker 启动后训练在 9 秒内完成。
2. **数据集残留**：每次运行会创建新的数据集和实验记录，长期运行会积累测试数据。
3. **对比端点局限**：步骤 12 使用同一个实验 ID 两次进行对比测试，实际使用场景应对比不同实验。
4. **无 Worker 集成测试**：本脚本只验证 API 层面，不验证 Worker 实际执行训练的能力。

---

## 十一、是否建议提交 Task 3.3 验收

**建议提交验收。**

### 通过条件检查（M7-T79 修复后）

| 条件 | 状态 |
|------|------|
| `scripts/smoke-test-api.py` 已新增 | ✅ |
| 可通过 `python scripts/smoke-test-api.py --api-url http://localhost:8000` 独立运行 | ✅ |
| 覆盖 ≥ 10 个 API 端点 | ✅ (13 个) |
| 每步输出 PASS/FAIL + 耗时 | ✅ |
| 退出码正确反映整体结果 | ✅ (全部通过 → exit 0) |
| 本地全栈启动后脚本真实执行 | ✅ (已执行 2 次) |
| 总耗时 < 120 秒（含训练等待） | ✅ (9s) |
| 产出与本轮编号一致的报告 | ✅ (本报告) |
| 未越界推进到 Phase-4 或后续任务 | ✅ |

### 最终执行结果

```
总步骤数: 13
通过: 13
失败: 0
结果: 全部通过
总耗时: 9.06s
退出码: 0 (全部通过)
```
