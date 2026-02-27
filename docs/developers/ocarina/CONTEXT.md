# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.9.3
- **开发者**: ocarina
- **上次更新**: 2026-02-27

## 当前任务
- **v0.9.3 完成**: Task/EventLog 核心工作流接通 (DECISION-016)

## 最近完成
- ✅ **v0.9.3 Task CLI 补齐**: `task transition` / `task solidify` / `task rollback` 三个命令
- ✅ **onboard 注入 Task/EventLog**: 活跃 Task 概览 + 最近 EventLog 事件摘要
- ✅ **next 基于 Task 推荐**: REVIEW→solidify / 依赖阻塞 / TODO 积压 智能提示
- ✅ **MCP 新增 2 Tool**: `task_create` + `task_transition`
- ✅ **DECISION-016**: v0.9.3 方向决策 (S 级)
- ✅ **30 新测试**: 1164/1164 passed, 零回归
- ✅ **v0.9.2 Insight 信号增强**: `insight_signal.py` + `session_store.py` + `insight suggest`
- ✅ **v0.9.1 MCP Server**: `vibecollab mcp serve` (stdio/sse) + 12 Tools + 6 Resources + 1 Prompt

## 接下来计划
- v0.9.4 Insight 质量与生命周期（去重 / 关联图谱 / 跨项目导入导出）
- v0.10.0 发布准备（文档完善 / Wiki / README / PyPI 正式发布）
- PyPI v0.9.3 发布

## 技术债务
- 跨项目 Insight 可移植性验证 — 需先实现 export/import API（延后）
- cli_insight.py / cli_task.py 尚未迁移到 Rich 输出风格（延后到 v1.0）
- QA_TEST_CASES.md 全量更新（覆盖 v0.7.x+ 新功能）
- `vibecollab index --watch` 文件变更自动重建索引（延后）
- 代码文件索引（docstring / 函数签名）（延后）

---
*此文件由 ocarina 维护*
