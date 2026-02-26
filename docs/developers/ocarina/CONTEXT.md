# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.8.0-dev
- **开发者**: ocarina
- **上次更新**: 2026-02-26

## 当前任务
- **v0.8.0 稳定性验证 + 泛用性压力测试**: 进行中

## 最近完成
- ✅ **Windows GBK 统一兼容层**: `_compat.py` 共享模块, 消除 4 处重复, 修复 7 处硬编码 emoji
- ✅ **极简/复杂项目边界测试**: 15 新测试 (empty YAML/name-only/full-config), 914/914 passed
- ✅ **README.md 更新**: 项目结构/测试数/版本历史同步 v0.8.0-dev
- ✅ **已知问题清零**: QA_TEST_CASES.md 中优先级问题全部解决或延后
- ✅ **Agent 稳定性压力测试**: 13 新测试 (100 周期/PID 锁/退避/回滚), 899/899 passed
- ✅ **Insight 泛用性测试**: 20 新测试 (大规模/衰减/关联/循环保护), 899/899 passed
- ✅ **LLM Client mock 集成测试**: 26 新测试 (双 provider + 配置层 + 边界), 868/868 passed
- ✅ **Agent 模式 E2E 测试**: 35 新测试 (executor 21 + cli_ai 14), 844/844 passed
- ✅ **CLI E2E 测试全量覆盖**: 48/48 命令 CliRunner 覆盖 (27 新测试)
- ✅ **系统性 subprocess 异常处理修复**: 12 处 `except Exception` → `except BaseException`
- ✅ **Config 配置管理系统**: 三层配置 (env > config file > defaults) + 交互式向导 (38 tests)

## 接下来计划
- QA_TEST_CASES.md 全量更新（覆盖 v0.7.x+ 新功能）
- Rich 面板 Windows PowerShell/CMD/WSL 渲染手动验证
- onboard/next 大型项目输出质量手动验证
- 外部项目泛用性验证（3+ 项目）
- 多 Python 版本 / 多 OS 兼容性验证（需 CI）

## 技术债务
- 跨项目 Insight 可移植性验证 — 需先实现 export/import API（延后）
- cli_insight.py / cli_task.py 尚未迁移到 Rich 输出风格（延后到 v1.0）

---
*此文件由 ocarina 维护*
