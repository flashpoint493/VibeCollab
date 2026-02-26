# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.8.0-dev
- **开发者**: ocarina
- **上次更新**: 2026-02-26

## 当前任务
- **v0.8.0 稳定性验证 + 泛用性压力测试**: 进行中

## 最近完成
- ✅ **Flaky test 修复**: _get_git_uncommitted BaseException 捕获, 连续两次 779/779 passed
- ✅ **测试覆盖率 76% → 81%**: 128 新测试 (llmstxt/templates/git_utils/lifecycle/extension/cli_lifecycle)
- ✅ **Config 配置管理系统**: 三层配置 (env > config file > defaults) + 交互式向导 (38 tests)
- ✅ **Task-Insight 自动关联**: create_task() 自动搜索关联 Insight (28 tests)
- ✅ **CLI task 命令组**: vibecollab task create/list/show/suggest
- ✅ **自举全量验证**: onboard/next/check/insight 全链路正常
- ✅ **protocol_checker 修复**: 多开发者动态发现
- ✅ **CONTRIBUTING_AI.md 补全**: 全量 CLI 命令文档

## 接下来计划
- Agent 模式 E2E 测试（agent plan/run/serve 全链路）
- LLM Client mock 集成测试
- Insight 系统泛用性验证
- QA_TEST_CASES.md 全量更新

## 技术债务
- vibecollab check 未覆盖 QA_TEST_CASES.md 陈旧性检测

---
*此文件由 ocarina 维护*
