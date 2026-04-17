# M7-T78 — Phase-3 / Task 3.3 API 集成冒烟测试脚本

> 任务编号：M7-T78  
> 阶段：Phase-3 / Task 3.3  
> 前置：M7-T77（Task 3.2 验收通过）  
> 时间戳：20260416-151003

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T77-AUDIT-SUMMARY-20260416-151003.md`
- [ ] 阅读 `docs/planning/LAUNCH_DEVELOPMENT_PLAN.md` 中 `Task 3.3`

---

## 一、本轮目标

进入 `Phase-3 / Task 3.3 — API 集成冒烟测试脚本`，目标是新增一个**可独立运行的端到端 API 冒烟脚本**，验证从登录、数据集、实验、训练、结果到登出的核心 API 链路。

---

## 二、允许修改的范围文件

- `scripts/smoke-test-api.py`（新增）
- 如确有必要，可补充与脚本运行直接相关的最小文档说明
- 本轮新增报告文件：`docs/tasks/M7/M7-T78-R-<timestamp>-p3-t33-api-smoke-test-script-report.md`

禁止越界到：

- API / Worker 的业务逻辑实现
- 前端页面或 Playwright 用例
- Docker / Alembic / 认证机制的大改动

---

## 三、必须完成的最小工作

### 1) 新增独立可运行的 API 冒烟脚本

新增：

- `scripts/smoke-test-api.py`

要求：

- 使用 Python + `httpx`
- 可独立运行
- 支持命令：

```bash
python scripts/smoke-test-api.py --api-url http://localhost:8000
```

### 2) 覆盖至少 10 个 API 端点

脚本至少覆盖以下链路：

1. `POST /api/auth/login` → 获取 token
2. `GET /api/assets/scan` → 扫描资产
3. `POST /api/datasets/upload` → 上传测试 CSV
4. `POST /api/datasets/` → 创建数据集
5. `GET /api/datasets/{id}` → 获取详情
6. `POST /api/experiments/` → 创建实验
7. `POST /api/training/submit` → 提交训练
8. `GET /api/training/status` → 查看队列
9. 轮询等待训练完成
10. `GET /api/results/{id}` → 获取结果
11. `GET /api/results/{id}/feature-importance` → 特征重要性
12. `POST /api/results/compare` → 对比实验
13. `POST /api/auth/logout` → 登出

如个别端点因现有后端已知限制无法通过，必须：

- 在脚本输出中明确标记 PASS / FAIL
- 在报告中如实区分“已通过”和“被环境/既有缺陷阻断”
- 不得把失败步骤包装成通过

### 3) 每一步都要输出 PASS/FAIL + 耗时

要求：

- 每个步骤打印：
  - 步骤名
  - PASS / FAIL
  - 耗时
- 最终打印汇总结果

示例格式可自行设计，但必须清晰可读。

### 4) 退出码必须反映整体结果

要求：

- 全部通过：退出码 `0`
- 存在失败：退出码 `1`

### 5) 必须做真实执行

至少执行：

```bash
python scripts/smoke-test-api.py --api-url http://localhost:8000
```

要求：

- 报告中附完整原始输出
- 报告中写清是否满足 exit code 要求
- 若未全部通过，必须写清阻断步骤与原因

---

## 四、通过条件（全部满足才算通过）

- [ ] `scripts/smoke-test-api.py` 已新增
- [ ] 可通过 `python scripts/smoke-test-api.py --api-url http://localhost:8000` 独立运行
- [ ] 覆盖 ≥ 10 个 API 端点
- [ ] 每步输出 PASS/FAIL + 耗时
- [ ] 退出码正确反映整体结果
- [ ] 本地全栈启动后脚本真实执行
- [ ] 总耗时 < 120 秒（含训练等待）
- [ ] 产出与本轮编号一致的 `M7-T78-R-...` 报告
- [ ] 未越界推进到 Phase-4 或后续任务

---

## 五、汇报要求

完成后提交：

- `M7-T78-R-<timestamp>-p3-t33-api-smoke-test-script-report.md`

汇报必须包含：

1. 已完成任务编号
2. 修改文件清单
3. 脚本支持的运行方式
4. 覆盖的 API 步骤清单
5. 实际执行命令
6. 完整原始输出
7. 实际退出码
8. 已验证通过项
9. 未验证 / 失败步骤
10. 风险与限制
11. 是否建议提交 Task 3.3 验收

---

## 六、明确禁止

- 不得只写脚本而不真实执行
- 不得把失败步骤伪装成通过
- 不得跳过关键链路却声称“全链路冒烟完成”
- 不得提前进入 Phase-4 或后续任务
