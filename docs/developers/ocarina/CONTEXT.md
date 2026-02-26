# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.8.0-dev
- **开发者**: ocarina
- **上次更新**: 2026-02-26

## 当前任务
- **v0.8.0 稳定性验证 + 泛用性压力测试**: 进行中

## 最近完成
- ✅ **Agent 稳定性压力测试**: 13 新测试 (100 周期/PID 锁/退避/回滚), 899/899 passed
- ✅ **Insight 泛用性测试**: 20 新测试 (大规模/衰减/关联/循环保护), 899/899 passed
- ✅ **LLM Client mock 集成测试**: 26 新测试 (双 provider + 配置层 + 边界), 868/868 passed
- ✅ **Agent 模式 E2E 测试**: 35 新测试 (executor 21 + cli_ai 14), 844/844 passed
- ✅ **CLI E2E 测试全量覆盖**: 48/48 命令 CliRunner 覆盖 (27 新测试)
- ✅ **系统性 subprocess 异常处理修复**: 12 处 `except Exception` → `except BaseException`
- ✅ **Flaky test 修复**: test_onboard_basic + test_whoami_basic, 全量 809/809 passed
- ✅ **key_files 陈旧性检查**: max_stale_days 功能 (schema + checker + config + 3 tests)
- ✅ **测试覆盖率 76% → 81%**: 128 新测试 (llmstxt/templates/git_utils/lifecycle/extension/cli_lifecycle)
- ✅ **Config 配置管理系统**: 三层配置 (env > config file > defaults) + 交互式向导 (38 tests)
- ✅ **Task-Insight 自动关联**: create_task() 自动搜索关联 Insight (28 tests)

## 接下来计划
- 人机交互质量验证（Unicode 兼容、Rich 渲染、输出质量、错误友好度）
- 泛用性验证（外部项目、多 Python 版本、多 OS）
- 文档与质量（QA_TEST_CASES.md 更新、README.md 更新、已知问题清零）

## 技术债务
- 跨项目 Insight 可移植性验证 — 需先实现 export/import API（延后）

---
*此文件由 ocarina 维护*
