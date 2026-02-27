# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.8.0-dev
- **开发者**: ocarina
- **上次更新**: 2026-02-27

## 当前任务
- **v0.9.0 语义检索引擎**: 准备中（roadmap 下一步）

## 最近完成
- ✅ **`vibecollab prompt` 命令**: LLM 上下文 prompt 生成器 — 替代手动复制 CONTRIBUTING_AI.md，支持 --compact/--copy/--sections/-d，23 新测试，956/956 passed
- ✅ **Protocol Checker watch_files 机制**: DECISIONS.md/PRD.md 跟随检查 + max_inactive_hours 可配置 + max_stale_days 补配
- ✅ **定位决策: ai 模块标记 experimental**: `vibecollab ai` 标记 [experimental]，核心定位回归协议管理工具，LLM 通信/Tool Use 交给 Cline/Cursor/Aider
- ✅ **Insight 融入 IDE 对话模式**: `27_insight_workflow.md.j2` 模板 + 对话结束沉淀检查 + `next` 命令 5 种信号提示
- ✅ **Config 三层配置系统**: config_manager + cli_config + LLMConfig 集成 + 38 tests
- ✅ **Task-Insight 自动关联**: create_task 自动搜索 + CLI task 命令组 + 28 tests

## 接下来计划
- v0.9.0 语义检索引擎：`Embedder` + `VectorStore` + `vibecollab index`
- `vibecollab insight search --semantic` 混合检索
- 协议自举 (`vibecollab bootstrap`)
- 外部项目泛用性验证（3+ 项目 init/generate/check）

## 技术债务
- 跨项目 Insight 可移植性验证 — 需先实现 export/import API（延后）
- cli_insight.py / cli_task.py 尚未迁移到 Rich 输出风格（延后到 v1.0）
- QA_TEST_CASES.md 全量更新（覆盖 v0.7.x+ 新功能）

---
*此文件由 ocarina 维护*
