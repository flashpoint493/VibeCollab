# VibeCollab - ocarina 的工作上下文

## 当前状态
- **版本**: v0.9.0-dev
- **开发者**: ocarina
- **上次更新**: 2026-02-27

## 当前任务
- **v0.9.1 自举能力**: 协议自举 (`vibecollab bootstrap`) + 协议模板自测框架

## 最近完成
- ✅ **v0.9.0 语义检索引擎完成**: Embedder + VectorStore + Indexer + CLI (index/search/insight search --semantic) + onboard 语义增强，84 新测试，1040/1040 passed
- ✅ **onboard 语义增强**: 从 CONTEXT.md/开发者上下文提取任务 → 向量检索 Top-N 相关 Insight，Rich 面板 + JSON 输出
- ✅ **`vibecollab prompt` 命令**: LLM 上下文 prompt 生成器，23 新测试
- ✅ **Protocol Checker watch_files 机制**: DECISIONS.md/PRD.md 跟随检查 + max_inactive_hours 可配置
- ✅ **Config 三层配置系统**: config_manager + cli_config + LLMConfig 集成
- ✅ **Task-Insight 自动关联**: create_task 自动搜索 + CLI task 命令组

## 接下来计划
- v0.9.1 协议自举 (`vibecollab bootstrap`) + 协议模板自测框架
- v0.9.1 `ContextBuilder` 重构 + `insight suggest`
- v0.10.0 MCP Server + IDE 集成

## 技术债务
- 跨项目 Insight 可移植性验证 — 需先实现 export/import API（延后）
- cli_insight.py / cli_task.py 尚未迁移到 Rich 输出风格（延后到 v1.0）
- QA_TEST_CASES.md 全量更新（覆盖 v0.7.x+ 新功能）
- `vibecollab index --watch` 文件变更自动重建索引（延后）
- 代码文件索引（docstring / 函数签名）（延后）

---
*此文件由 ocarina 维护*
