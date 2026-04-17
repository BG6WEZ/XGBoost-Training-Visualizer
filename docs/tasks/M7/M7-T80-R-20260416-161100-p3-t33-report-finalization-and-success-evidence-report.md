# M7-T80-R — Phase-3 / Task 3.3 报告定稿与成功证据固化 验收报告

> 任务编号：M7-T80  
> 阶段：Phase-3 / Task 3.3 Re-open  
> 前置：M7-T79（审计不通过）  
> 时间戳：20260416-161100

---

## 一、已完成任务编号

- **M7-T80** — Phase-3 / Task 3.3 再收口（报告定稿与成功证据固化）

---

## 二、修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `docs/tasks/M7/M7-T80-R-20260416-161100-p3-t33-report-finalization-and-success-evidence-report.md` | 新增 | 本轮正式报告（定稿与成功证据固化） |

---

## 三、最终验收依据

**本报告以 2026-04-16 15:59:08 执行的那次成功执行作为最终验收依据。**

| 项目 | 值 |
|------|------|
| 执行时间 | 2026-04-16 15:59:08 |
| 执行命令 | `python scripts/smoke-test-api.py --api-url http://localhost:8000` |
| 退出码 | `0`（全部通过） |
| 总耗时 | `9.06s` |
| 通过步骤 | 13 / 13 |
| 失败步骤 | 0 |

---

## 四、首次失败与最终成功之间的差异说明

| 对比项 | 首次执行（15:25:43） | 最终成功执行（15:59:08） |
|--------|---------------------|-------------------------|
| Worker 进程 | 未运行 | 已启动（`cd apps/worker; python -m app.main`） |
| 步骤 9 状态 | 超时 120s（任务停留在 queued） | 首次轮询即检测到 completed |
| 通过步骤 | 12 / 13 | 13 / 13 |
| 退出码 | `1` | `0` |
| 总耗时 | 129.27s | 9.06s |
| 验收结论 | 不予通过 | **作为最终验收依据** |

**差异原因**：首次执行时 Worker 进程未启动，训练任务无法被消费执行。启动 Worker 后，训练任务在秒级完成。

---

## 五、最终成功执行的完整原始输出

```
============================================================
API 集成冒烟测试
============================================================
API URL: http://localhost:8000
Username: admin
开始时间: 2026-04-16 15:59:08
============================================================
  [PASS] 1. POST /api/auth/login (获取 token) (0.25s)
  [PASS] 2. GET /api/assets/scan (扫描资产) (0.02s)
  [PASS] 3. POST /api/datasets/upload (上传测试 CSV) (0.02s)
  [PASS] 4. POST /api/datasets/ (创建数据集) (0.02s)
  [PASS] 5. GET /api/datasets/{id} (获取数据集详情) (0.01s)
  [PASS] 6. POST /api/experiments/ (创建实验) (0.02s)
  [PASS] 7. POST /api/experiments/{id}/start (提交训练) (0.02s)
  [PASS] 8. GET /api/training/status (查看训练队列) (0.01s)
      训练状态: completed (已等待 0s)
  [PASS] 9. 轮询等待训练完成 (GET /api/training/{id}/status) (0.01s)
  [PASS] 10. GET /api/results/{id} (获取训练结果) (0.03s)
  [PASS] 11. GET /api/results/{id}/feature-importance (特征重要性) (0.02s)
  [PASS] 12. POST /api/results/compare (对比实验) (0.01s)
  [PASS] 13. POST /api/auth/logout (登出) (0.01s)

============================================================
冒烟测试报告
============================================================
总步骤数: 13
通过: 13
失败: 0
============================================================
  [PASS] 1. POST /api/auth/login (获取 token) (0.25s)
  [PASS] 2. GET /api/assets/scan (扫描资产) (0.02s)
  [PASS] 3. POST /api/datasets/upload (上传测试 CSV) (0.02s)
  [PASS] 4. POST /api/datasets/ (创建数据集) (0.02s)
  [PASS] 5. GET /api/datasets/{id} (获取数据集详情) (0.01s)
  [PASS] 6. POST /api/experiments/ (创建实验) (0.02s)
  [PASS] 7. POST /api/experiments/{id}/start (提交训练) (0.02s)
  [PASS] 8. GET /api/training/status (查看训练队列) (0.01s)
  [PASS] 9. 轮询等待训练完成 (GET /api/training/{id}/status) (0.01s)
  [PASS] 10. GET /api/results/{id} (获取训练结果) (0.03s)
  [PASS] 11. GET /api/results/{id}/feature-importance (特征重要性) (0.02s)
  [PASS] 12. POST /api/results/compare (对比实验) (0.01s)
  [PASS] 13. POST /api/auth/logout (登出) (0.01s)
============================================================
结果: 全部通过
============================================================
总耗时: 9.06s

退出码: 0 (全部通过)
```

---

## 六、最终成功执行的退出码

| 执行 | 退出码 | 说明 |
|------|--------|------|
| 首次执行（15:25:43） | `1` | 1 个步骤失败（训练超时） |
| **最终验收执行（15:59:08）** | **`0`** | **全部通过** |

---

## 七、最终成功执行的总耗时

| 执行 | 总耗时 |
|------|--------|
| 首次执行（15:25:43） | 129.27s（步骤 9 超时 120s） |
| **最终验收执行（15:59:08）** | **9.06s** |

---

## 八、已验证通过项（13/13）

| 步骤 | 端点 | 状态 | 耗时 |
|------|------|------|------|
| 1 | `POST /api/auth/login` | PASS | 0.25s |
| 2 | `GET /api/assets/scan` | PASS | 0.02s |
| 3 | `POST /api/datasets/upload` | PASS | 0.02s |
| 4 | `POST /api/datasets/` | PASS | 0.02s |
| 5 | `GET /api/datasets/{id}` | PASS | 0.01s |
| 6 | `POST /api/experiments/` | PASS | 0.02s |
| 7 | `POST /api/experiments/{id}/start` | PASS | 0.02s |
| 8 | `GET /api/training/status` | PASS | 0.01s |
| 9 | 轮询 `GET /api/training/{id}/status` | PASS | 0.01s |
| 10 | `GET /api/results/{id}` | PASS | 0.03s |
| 11 | `GET /api/results/{id}/feature-importance` | PASS | 0.02s |
| 12 | `POST /api/results/compare` | PASS | 0.01s |
| 13 | `POST /api/auth/logout` | PASS | 0.01s |

---

## 九、剩余风险与限制

1. **Worker 依赖**：步骤 9 需要 Worker 进程正常运行。Worker 未启动时该步骤会超时。
2. **数据集残留**：每次运行会创建新的数据集和实验记录，长期运行会积累测试数据。
3. **对比端点局限**：步骤 12 使用同一个实验 ID 两次进行对比测试，实际使用场景应对比不同实验。
4. **预测数据缺失**：Worker 日志显示 `Failed to save prediction data: 'StorageService' object has no attribute 'save_prediction_data'`，但不影响冒烟测试链路。

---

## 十、是否建议提交 Task 3.3 验收

**建议提交验收。**

### 通过条件检查

| 条件 | 状态 |
|------|------|
| 产出与本轮编号一致的 `M7-T80-R-...` 报告 | ✅ |
| 报告明确指出最终验收依据是哪一次执行 | ✅ (2026-04-16 15:59:08) |
| 报告附最终成功执行的完整原始输出 | ✅ (见第五节) |
| 最终成功执行结果为 13 / 13 通过 | ✅ |
| 最终成功执行退出码为 `0` | ✅ |
| 最终成功执行总耗时 < 120 秒 | ✅ (9.06s) |
| 报告内容与当前脚本、当前事实一致 | ✅ |
| 未越界推进到 Phase-4 或后续任务 | ✅ |