# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.8.0-dev
- **开发者**: ocarina
- **上次更新**: 2026-02-27

## 当前任务
- **v0.8.0 稳定性验证 + 泛用性压力测试**: 进行中

## 最近完成
- ✅ **定位决策: ai 模块标记 experimental**: `vibecollab ai` 标记 [experimental]，核心定位回归协议管理工具，LLM 通信/Tool Use 交给 Cline/Cursor/Aider
- ✅ **Insight 读取路径完善**: 协议模板增加对话开始时 Insight 检索指引 + onboard 展示 Top-5 Insight 摘要
- ✅ **Insight 融入 IDE 对话模式**: `27_insight_workflow.md.j2` 模板 + 对话结束沉淀检查 + `next` 命令 5 种信号提示 + 16 新测试, 929/929 passed
- ✅ **CI/CD 修复**: 版本号统一 `0.8.0.dev0` + Python 矩阵 3.9-3.13 + requires-python >=3.9
- ✅ **Ruff lint 全量修复**: 68 errors → 0（auto-fix 61 + 手动 7）
- ✅ **Windows GBK 统一兼容层**: `_compat.py` 共享模块, 消除 4 处重复, 修复 7 处硬编码 emoji
- ✅ **极简/复杂项目边界测试**: 15 新测试 (empty YAML/name-only/full-config), 914/914 passed
- ✅ **Agent 稳定性压力测试**: 13 新测试 (100 周期/PID 锁/退避/回滚)
- ✅ **Insight 泛用性测试**: 20 新测试 (大规模/衰减/关联/循环保护)

## 接下来计划
- Git commit + push 触发 CI 验证
- 外部项目泛用性验证（3+ 项目 init/generate/check）— 用户手动验证
- Rich 面板 Windows PowerShell/CMD/WSL 渲染手动验证
- onboard/next 大型项目输出质量手动验证

## 技术债务
- 跨项目 Insight 可移植性验证 — 需先实现 export/import API（延后）
- cli_insight.py / cli_task.py 尚未迁移到 Rich 输出风格（延后到 v1.0）
- QA_TEST_CASES.md 全量更新（覆盖 v0.7.x+ 新功能）

---
*此文件由 ocarina 维护*
