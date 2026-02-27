# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.9.4
- **开发者**: ocarina
- **上次更新**: 2026-02-27

## 当前任务
- **v0.9.4 完成**: Insight 质量与生命周期（去重 / 关联图谱 / 导入导出）

## 最近完成
- ✅ **v0.9.4 Insight 质量与生命周期**:
  - `find_duplicates()`: 指纹+标题+标签三维去重检测
  - `build_graph()` / `to_mermaid()`: Insight 关联图谱可视化
  - `export_insights()` / `import_insights()`: 跨项目导入导出 (skip/rename/overwrite)
  - CLI: `insight graph` / `insight export` / `insight import` / `insight add --force`
  - MCP: `insight_graph` / `insight_export`
  - 36 新测试, 1201/1201 passed, 零回归
- ✅ **v0.9.3 Task CLI 补齐**: `task transition` / `task solidify` / `task rollback`
- ✅ **v0.9.2 Insight 信号增强**: `insight_signal.py` + `session_store.py` + `insight suggest`
- ✅ **v0.9.1 MCP Server**: `vibecollab mcp serve` (stdio/sse) + 14 Tools + 6 Resources + 1 Prompt

## 接下来计划
- v0.10.0 发布准备（文档完善 / Wiki / README / PyPI 正式发布）
- PyPI v0.9.4 发布

## 技术债务
- cli_insight.py / cli_task.py 尚未迁移到 Rich 输出风格（延后到 v1.0）
- QA_TEST_CASES.md 全量更新（覆盖 v0.7.x+ 新功能）
- `vibecollab index --watch` 文件变更自动重建索引（延后）
- 代码文件索引（docstring / 函数签名）（延后）

---
*此文件由 ocarina 维护*
