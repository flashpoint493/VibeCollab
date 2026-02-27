# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.10.0.dev0
- **开发者**: ocarina
- **上次更新**: 2026-02-27

## 当前任务
- **DECISION-017**: v0.10.x 发布工程规划已确认 (S 级)
- **v0.10.0**: 功能冻结 + 稳定性门槛（外部 QA 验证 + 覆盖率 85%）

## 最近完成
- ✅ **v0.9.4 Insight 质量与生命周期**: 去重/图谱/导入导出, 1201 tests
- ✅ **v0.9.3 Task CLI**: transition/solidify/rollback
- ✅ **v0.9.2 Insight 信号增强**: insight_signal + session_store + suggest
- ✅ **v0.9.1 MCP Server**: stdio/sse, 14 Tools, 6 Resources, 1 Prompt
- ✅ **QA Phase 7~11 补齐**: 39 个新测试用例 (含 10 个 E2E 集成)

## 接下来计划 (DECISION-017)
1. **v0.10.0** — 外部 QA 验证 + 覆盖率 85% + 功能冻结
2. **v0.10.1** — 代码国际化 (36 文件, ~2055 行中文→英文)
3. **v0.10.2** — 文档双语化 (README EN + CHANGELOG EN)
4. **v0.10.3** — Git 历史重写 (97 commits) + GitHub 门面
5. **v1.0.0** — 正式发布

## 技术债务
- cli_insight.py / cli_task.py 尚未迁移到 Rich 输出风格（延后到 v1.0）
- QA_TEST_CASES.md 全量更新（已补齐到 v0.9.4）
- `vibecollab index --watch` 文件变更自动重建索引（延后）

---
*此文件由 ocarina 维护*
