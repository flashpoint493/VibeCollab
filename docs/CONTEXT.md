# VibeCollab 全局上下文

> ! **此文件自动生成，请勿手动编辑**
> 上次更新: 2026-03-02
> 聚合自: alice, ocarina

## 项目整体状态
- **版本**: v0.9.7 (开发中)
- **上一版本**: v0.9.6 (PyPI 已发布)
- **活跃开发者**: 2 (alice, ocarina)
- **测试**: 1344 passed, 89% 覆盖率
- **当前阶段**: v0.9.7 迭代，推进 v0.10.0 功能冻结

## 各开发者工作状态

### alice
- **上次更新**: 2026-02-25
- **活跃度**: 暂停（上次活跃于 v0.5.4）
- **已完成**: CLI 开发者切换功能 (TASK-DEV-004), switch 命令测试和文档 (TASK-DEV-005)
- **无遗留任务**

### ocarina
- **上次更新**: 2026-03-02
- **当前任务**: 目录重构 + GBK 编码修复
- **最近完成**:
  - 目录重构: 36 个平铺 .py 文件重组为 7 个子包 (cli/core/domain/insight/search/agent/utils)
  - GBK 编码彻底修复: 三层防御体系 (ensure_safe_stdout + safe_console + EMOJI 映射扩充)
  - v0.9.5 ROADMAP / Task 集成 (RoadmapParser + CLI + MCP + 40 tests)
  - README 双语重构 (英文主 README + README.zh-CN.md)
  - PyPI v0.9.5/v0.9.6 发布

## 活跃任务

无活跃任务

## 架构变更 (v0.9.7)

### 目录重构
36 个平铺模块重组为 7 个子包:
- `cli/` (11 文件) — CLI 命令层 (main, ai, guide, config, lifecycle, insight, task, roadmap, mcp, index)
- `core/` (8 文件) — 核心业务 (generator, project, templates, pattern_engine, extension, health, protocol_checker)
- `domain/` (8 文件) — 领域模型 (task_manager, event_log, developer, lifecycle, roadmap_parser, conflict_detector, prd_manager, session_store)
- `insight/` (3 文件) — Insight 沉淀系统 (manager, signal)
- `search/` (2 文件) — 语义检索 (embedder, indexer, vector_store)
- `agent/` (3 文件) — Agent/LLM/MCP (llm_client, agent_executor, mcp_server)
- `utils/` (2 文件) — 工具 (git, llmstxt)

### GBK 编码三层防御
- 第一层: `ensure_safe_stdout()` — CLI 启动时 reconfigure stdout/stderr errors='replace'
- 第二层: `safe_console()` — Rich Console 工厂函数
- 第三层: EMOJI 映射扩充 — 新增 check/cross/arrow/bar_fill/bar_empty/severity 等

## 跨开发者协作
(详见 docs/developers/COLLABORATION.md)

## 全局技术债务
- 外部 QA 验证 (Phase 11 TC-E2E-001~010) 待执行
- events.jsonl Windows 文件锁问题需排查
- i18n 英文化待推进

---
*此文件由多开发者上下文自动聚合生成*
