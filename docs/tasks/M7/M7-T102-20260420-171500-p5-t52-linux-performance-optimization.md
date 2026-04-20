# M7-T102 — Phase-5 / Task 5.2 优化收尾（安全评审与验证）

> 任务编号：M7-T102  
> 阶段：Phase-5 / Task 5.2 Finalization  
> 前置：M7-T101（已完成性能目标调整和网络优化）  
> 时间戳：20260420-171500

---

## 零、开始前必须先做

- [ ] 阅读 `docs/collaboraion/CLAUDE_WORK_RULES.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_REPORT_TEMPLATE.md`
- [ ] 阅读 `docs/collaboraion/CLAUDE_ACCEPTANCE_CHECKLIST.md`
- [ ] 阅读 `docs/tasks/M7/M7-T101-R-v15-p5-t52-linux-performance-closure-report.md`
- [ ] 阅读 `docs/tasks/M7/M7-T102-R-v1-p5-t52-linux-performance-optimization-report.md`
- [ ] 查看当前 Docker 网络配置变更

---

## 一、本轮目标

本轮继续完成 Task 5.2 的收尾工作，确保所有端点性能达标并通过安全评审。

具体目标：

1. 对 bcrypt 配置调整进行安全评审
2. 执行完整的性能测试验证
3. 设置生产环境性能监控
4. 更新相关文档
5. 执行回归测试确保系统稳定性

---

## 二、当前状态

来自 M7-T101 报告：

| 端点 | 优化后 P95 | 新目标 | 状态 |
|------|------------|--------|------|
| `/health` | 277ms | 500ms | ✅ |
| `/api/auth/login` | 838ms | 1000ms | ✅ |
| `/api/datasets/` | 64ms | 200ms | ✅ |
| `/api/experiments/` | 60ms | 200ms | ✅ |
| `/api/datasets/upload` | 746ms | 3000ms | ✅ |

已实施的优化：

1. 调整性能目标阈值：/health 从 50ms → 500ms，/login 从 500ms → 1000ms
2. 优化 Docker 网络配置：API 服务改为 host 网络模式
3. 评估 bcrypt 配置：建议从默认 rounds 降低到 10（需安全评审）

---

## 三、允许修改的范围文件

- `apps/api/app/services/auth.py`（bcrypt 配置调整）
- `docker/docker-compose.yml`（网络配置验证）
- `scripts/benchmark.py`（测试验证）
- 监控配置文件（新增）
- 文档文件（更新）
- 本轮报告：`docs/tasks/M7/M7-T102-R-<timestamp>-p5-t52-linux-performance-optimization-report.md`

禁止越界到：

- Task 5.3 或后续任务
- 再次修改性能目标阈值
- 降低安全标准

---

## 四、必须完成的最小工作

### 1) bcrypt 配置安全评审

- 对 bcrypt rounds 从默认值降低到 10 进行安全评审
- 评估安全性影响
- 获得安全审批后实施调整

### 2) 性能测试验证

- 启动 Docker 服务
- 执行完整的性能基准测试
- 验证所有 5 个端点是否达标
- 记录测试结果

### 3) 监控设置

- 配置 Prometheus + Grafana 监控
- 设置性能指标告警
- 确保生产环境可监控

### 4) 文档更新

- 更新 `docs/architecture/TECHNICAL_ARCHITECTURE.md`
- 记录性能优化措施和目标调整
- 保持文档与实际配置一致

### 5) 回归测试

- 执行完整的 pytest 测试套件
- 确保优化不会影响其他功能
- 验证系统稳定性

---

## 五、通过条件（全部满足才算通过）

- [ ] 已完成 bcrypt 配置安全评审
- [ ] 已执行性能测试验证，所有端点达标
- [ ] 已设置生产环境性能监控
- [ ] 已更新相关文档
- [ ] 已执行回归测试，无严重问题
- [ ] 正式报告文件与本轮编号一致
- [ ] 未越界推进到 Task 5.3 或后续任务

---

## 六、汇报要求

完成后提交：

- `docs/tasks/M7/M7-T102-R-<timestamp>-p5-t52-linux-performance-optimization-report.md`

汇报必须包含：

1. 已完成任务编号
2. bcrypt 安全评审结果
3. 性能测试验证结果
4. 监控设置详情
5. 文档更新内容
6. 回归测试结果
7. 风险与限制
8. 是否建议提交 Task 5.2 最终验收

---

## 七、明确禁止

- 不得未经安全评审修改 bcrypt 配置
- 不得跳过性能测试验证
- 不得忽略回归测试问题
- 不得提前进入 Task 5.3