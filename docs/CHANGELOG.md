# VibeCollab Changelog

## v0.10.1-dev (2026-03-03) - Code Internationalization (i18n)

### i18n Framework
- **CLI i18n architecture**: gettext-based localization with zero external dependencies
  - Created `src/vibecollab/i18n/` module: `_()`, `setup_locale()`, `ngettext()`, `get_current_language()`
  - Language selection: `--lang` CLI option > `VIBECOLLAB_LANG` env var > English fallback
  - Pre-parse `--lang` from `sys.argv` at module import time (before Click evaluates `help=` decorators)
  - Locale directory: `src/vibecollab/i18n/locales/{lang}/LC_MESSAGES/vibecollab.po/.mo`
  - `pyproject.toml` artifacts updated to include `.mo` files in wheel builds
- **316 unique translatable strings** extracted across all 11 CLI files
  - All `help=` parameters wrapped with `_()` in: main.py, ai.py, guide.py, insight.py, config.py, lifecycle.py, index.py, mcp.py, roadmap.py, task.py
  - Key runtime output strings wrapped in main.py, lifecycle.py, index.py, mcp.py
  - f-strings with variables converted to `_('text {var}').format(var=val)` pattern
  - Rich markup separated from translatable text: `f"[red]{_('Error:')}[/red]"`
- **Chinese translation (zh_CN)**: 131 key strings translated, `.po`/`.mo` generated
  - `.pot` template with 316 entries for future translators
  - Verified end-to-end: `vibecollab --lang zh insight add --help` shows Chinese help text

### i18n (Code English Translation)
- **Full English translation** of all source code and test files (96 files, ~4900 lines changed)
  - 62 source `.py` files: all Chinese docstrings, comments, error messages, and runtime output strings translated to English
  - 27 `.j2` template files + `manifest.yaml`: all Chinese content translated
  - 34 test files: all Chinese assertions, comments, and docstrings translated
    - Test assertions updated to match new English source output strings
    - `pytest.raises(match=...)` patterns updated from Chinese to English/regex
    - Functional Chinese test data preserved (Unicode preservation tests, backward-compat parsing patterns, Chinese tag search tests, Chinese NLP tag extraction tests)
  - Cross-referenced source output strings via subagent before updating test assertions to ensure consistency

### Bug Fix
- Fixed `health.py` truncated `return "F"` (was `ret`) causing `NameError`
- Fixed `vector_store.py` truncated `return False` (was `return Fa`) causing `NameError`
- Fixed `test_cli_insight.py` 6 leftover Chinese assertions from previous sessions
- Fixed `test_insight_quality.py` 6 leftover Chinese comments/docstrings
- Fixed `test_insight_manager.py` incorrect Chinese-to-English tag search test (preserved Chinese tags as functional test data)

### Test
- All **1344 tests passed**, zero regression
- Intentionally preserved Chinese in 7 test files (31 occurrences) for functional testing:
  - `test_developer.py`: Chinese headings for backward-compat parsing + Unicode stripping
  - `test_event_log.py`: Unicode payload preservation
  - `test_insight_manager.py`: Chinese tag search functionality
  - `test_indexer.py`: Chinese CONTRIBUTING_AI.md content simulation
  - `test_llm_client.py`: Unicode content preservation
  - `test_task_insight_integration.py`: Chinese NLP tag extraction
  - `test_task_manager.py`: Unicode feature preservation

## v0.9.7 (2026-03-02) - Directory Restructure + GBK Encoding Fix

### Refactor
- **目录重构**: 36 个平铺 `.py` 模块重组为 7 个功能子包
  - `cli/` (11 文件): main, ai, guide, config, lifecycle, insight, task, roadmap, mcp, index
  - `core/` (8 文件): generator, project, templates, pattern_engine, extension, health, protocol_checker
  - `domain/` (8 文件): task_manager, event_log, developer, lifecycle, roadmap_parser, conflict_detector, prd_manager, session_store
  - `insight/` (3 文件): manager, signal
  - `search/` (3 文件): embedder, indexer, vector_store
  - `agent/` (3 文件): llm_client, agent_executor, mcp_server
  - `utils/` (2 文件): git, llmstxt
  - Phase 1: 文件迁移 + 内部导入更新 + 薄代理保证向后兼容
  - Phase 2: 35 个测试文件导入路径迁移 + 12 个 mock/patch 路径修复 + 35 个薄代理删除
  - `__init__.py` 公共 API 导出从旧路径更新为新子包路径
  - `pyproject.toml` entry_point `vibecollab.cli:main` 无需修改 (cli 包 `__init__.py` 导出 main)

### Bug Fix
- **GBK 编码彻底修复**: 三层防御体系消除所有 Windows GBK 终端 `UnicodeEncodeError`
  - **第一层** `ensure_safe_stdout()`: CLI 启动时将 `sys.stdout`/`sys.stderr` 的 errors 模式从 strict/surrogateescape 改为 replace，无法编码字符变为 `?` 而非崩溃
  - **第二层** `safe_console()`: Rich Console 工厂函数，确保 Console 创建前 stdout 已安全；6 个 CLI 模块 `Console()` 统一改为 `safe_console()`
  - **第三层** EMOJI 映射扩充: 新增 `check`/`cross`/`arrow`/`bar_fill`/`bar_empty`/`high`/`medium`/`low`/`idea` 等 9 个映射
  - 修复 `cli/roadmap.py` 硬编码 `█░↔→←☑☐` 字符
  - 修复 `cli/guide.py` 硬编码 `✓✗` 字符
  - 修复 `core/project.py` 硬编码 `✅⏳` 字符
  - 修复 `domain/developer.py` 硬编码 `✅⚠️` 字符
  - 消除 `domain/conflict_detector.py` 重复的 `is_windows_gbk()` 实现，统一使用 `_compat`
  - 关键修复: `surrogateescape` 错误模式在 GBK 编码下仍会崩溃，`ensure_safe_stdout()` 通过编码能力检测而非 errors 模式检测来判断是否需要 reconfigure

### Improvement
- **严格 `###` 里程碑格式**: `MILESTONE_HEADER_RE` 正则明确只接受 `### vX.Y.Z` 三级标题
- **零里程碑格式提示**: `roadmap status/parse/sync` 找不到里程碑时输出 `MILESTONE_FORMAT_HINT`
- **init 模板兼容**: `vibecollab init` 生成的 ROADMAP.md 使用 `### v0.1.0` 格式

### Test
- 全量 **1344 passed**, 零回归
- E2E 验证 **36 个 CLI 场景全部通过**
- 修复 `test_cli_ai.py` mock 路径 (`Console` -> `console` 实例)
- 修复 `test_conflict_detector.py` mock 路径 (`conflict_detector.platform` -> `_compat.platform`)

## v0.9.6 (2026-02-28) - PyPI 适配 + 文档质量

### Improvement
- **PyPI README 分离** (`README.pypi.md`): 新增 PyPI 专用 README
  - Mermaid 图表替换为 ASCII 文本流程图（PyPI 不支持 Mermaid 渲染）
  - 所有相对链接转换为 GitHub 绝对 URL（PyPI 无法解析相对路径）
  - `pyproject.toml` `readme` 字段指向 `README.pypi.md`（GitHub README 保持不变）
- **CONTEXT.md 过期任务清理**: TASK-DEV-005 (alice) 标记完成，移除遗留状态
- **README.md 更新**: CLI Reference 新增 `vibecollab roadmap` 命令组，Version History 补充 v0.9.4/v0.9.5

### Task
- TASK-DEV-006: PyPI README adaptation (README.pypi.md, 去 Mermaid + 绝对 URL) ✅
- TASK-DEV-007: CONTEXT.md stale task cleanup + v0.9.6 update ✅

## v0.9.5 (2026-02-28) - ROADMAP ↔ Task 集成

### New Feature
- **RoadmapParser 模块** (`roadmap_parser.py`): ROADMAP.md ↔ TaskManager 双向集成
  - 解析 ROADMAP.md 提取里程碑（`### vX.Y.Z - Title` 格式）和 checklist 项
  - 从 checklist 行内提取 `TASK-{ROLE}-{SEQ}` ID 引用（正则确定性匹配，非向量化）
  - **双向同步**: ROADMAP `[x]` → Task DONE / Task DONE → ROADMAP `[x]`
  - 三种同步方向: `both`（默认）/ `roadmap_to_tasks` / `tasks_to_roadmap`
  - dry-run 预览模式
  - 每里程碑进度聚合（total/done/progress_pct/task_breakdown）
  - 未关联 ROADMAP 的孤立 Task 检测
- **Task `milestone` 字段** (`task_manager.py`): Task dataclass 新增 `milestone: str` 属性
  - `from_dict` / `to_dict` 完整序列化支持，向后兼容旧数据
  - `list_tasks()` 新增 `--milestone` 过滤参数
- **CLI `vibecollab roadmap` 命令组** (`cli_roadmap.py`):
  - `vibecollab roadmap status [--json]` — 各里程碑进度概览（进度条+Task 状态分布）
  - `vibecollab roadmap sync [-d both] [--dry-run] [--json]` — 双向同步
  - `vibecollab roadmap parse [--json]` — 解析 ROADMAP 结构
- **CLI `vibecollab task` 增强** (`cli_task.py`):
  - `task create --milestone v0.9.3` — 创建任务时关联里程碑
  - `task list --milestone v0.9.3` — 按里程碑筛选
  - `task show` 显示里程碑字段
- **MCP Server 新增 Tool** (`mcp_server.py`):
  - `roadmap_status` — AI IDE 可查看 ROADMAP 进度
  - `roadmap_sync` — AI IDE 可触发 ROADMAP ↔ Task 同步

### Test
- 新增 **40 个单元测试** (`test_roadmap_parser.py`)
  - TestRegex (7): 里程碑 header / Task ID 正则
  - TestParse (7): 解析里程碑/items/checked/task_ids/progress/边界
  - TestStatus (5): 聚合统计/未关联 Task/breakdown
  - TestSync (6): 双向同步/dry-run/milestone 字段设置
  - TestMilestoneDataclass (3): 数据结构
  - TestTaskMilestoneField (6): Task milestone 字段 CRUD/序列化/过滤
  - TestCLI (6): CLI 命令 CliRunner 全覆盖
- 全量 **1331 passed**, 覆盖率 **89%**，零回归

## v0.10.0-dev (2026-02-27) - 覆盖率改进 & 稳定性

### Test
- **cli_index.py 覆盖率 17% → 91%**: 新建 `test_cli_index.py` (12 tests)
  - TestIndexCmd (5): basic/rebuild/auto_backend/with_insights/nonexistent_config
  - TestSearchCmd (7): no_index/basic/type_filter/min_score/top_k/empty_index/no_results
  - 修复测试 DB schema 缺少 `source` 列的问题
- **mcp_server.py 覆盖率 47% → 100%**: 新建 `test_mcp_server_closures.py` (42 tests)
  - Fake Module 注入法捕获 create_mcp_server() 内部闭包
  - TestResources (8): 6 个文档 resource + 空项目 + 缺失文件
  - TestCliTools (24): 14 个 CLI tools 的命令构建验证（含可选参数分支）
  - TestDirectTools (5): developer_context + session_save（成功/全字段/异常）
  - TestPrompts (4): start_conversation（基本/开发者/空项目/未知开发者）
  - TestRunCliEdge (1) + TestRunServer (1)
- **protocol_checker.py 覆盖率 71% → 96%**: 新建 `test_protocol_checker_git.py` (26 tests)
  - Git 一致性检查: commit 级别同步/跨标签发布检查
  - 真实 Git 仓库测试: `_is_file_tracked_in_git` / `_get_last_commit_time`
  - 文档更新阈值分支 / PRD 缺失 / 协作文档过期 / 开发者发现
- **cli_task.py 覆盖率 78% → 98%**: 新建 `test_cli_task_richtext.py` (10 tests)
  - 非 JSON 输出路径: list/show/suggest 的 rich text 格式化
  - `_load_config` 单元测试 + `_get_managers` InsightManager 异常分支
- 全量 **1291 passed**, 总覆盖率 **85% → 89%**

### Insight
- INS-016: Fake Module 注入法测试工厂函数内部闭包
- INS-017: 覆盖率提升的 ROI 优先级排序策略

## v0.9.4 (2026-02-27) - Insight 质量与生命周期

### New Feature
- **Insight 自动去重** (`insight_manager.py`): 新增 Insight 时自动检测重复
  - `find_duplicates()`: 基于 SHA-256 指纹精确匹配 + 标题 Jaccard 相似度 + 标签重叠率
  - `_content_key()`: 提取标题+标签+body 生成内容指纹
  - `insight add` 命令集成去重检测，发现重复时提示并阻止创建
  - `--force` 标志跳过去重检测强制创建
  - 相似度阈值可控
- **Insight 关联图谱** (`insight_manager.py`): 可视化 Insight 之间的派生/关联关系
  - `build_graph()`: 构建全局 Insight 关联图谱（节点+边+统计）
  - `_count_components()`: Union-Find 算法计算连通分量
  - `to_mermaid()`: 生成 Mermaid 图表语法，支持直接嵌入 Markdown
  - `vibecollab insight graph`: CLI 命令，支持 `--format text/json/mermaid`
- **跨项目 Insight 导入导出** (`insight_manager.py`):
  - `export_insights()`: 导出 Insight Bundle (YAML 格式)，支持全量/选择性导出，可选包含注册表
  - `import_insights()`: 导入 Insight Bundle，三种冲突策略 (skip/rename/overwrite)
  - 导入时自动设置 `source.project` 标记来源项目
  - `vibecollab insight export [--ids] [--output] [--include-registry]`
  - `vibecollab insight import <file> [--strategy skip/rename/overwrite] [--json]`
- **MCP Server 新增 2 个 Tool** (`mcp_server.py`):
  - `insight_graph`: 获取 Insight 关联图谱 (json/text/mermaid)
  - `insight_export`: 导出 Insight Bundle

### Test
- 36 个新单元测试 (`test_insight_quality.py`):
  - TestFindDuplicates (7): empty/fingerprint/title_similarity/tag_similarity/no_dup/threshold/without_body
  - TestBuildGraph (5): empty/edges/isolated/components/node_data
  - TestToMermaid (2): output/empty
  - TestExportInsights (4): all/selected/with_registry/empty
  - TestImportInsights (7): to_empty/skip/rename/overwrite/invalid/source_project/with_registry
  - TestCLIGraph (3): text/json/mermaid
  - TestCLIExportImport (5): stdout/to_file/import/invalid/rename_strategy
  - TestCLIAddDedup (3): detect_duplicate/force_bypass/no_duplicate
- 全量 1201 passed, 零回归

## v0.9.3 (2026-02-27) - Task/EventLog 核心工作流接通

### New Feature
- **Task CLI 三个新命令** (`cli_task.py`): 补齐 TaskManager 状态管理 CLI 入口
  - `vibecollab task transition <ID> <STATUS>`: 推进任务状态 (TODO→IN_PROGRESS→REVIEW→DONE)
  - `vibecollab task solidify <ID>`: 固化任务，通过验证门控后标记为 DONE
  - `vibecollab task rollback <ID>`: 回滚任务到上一个状态
  - 所有命令支持 `--json` 输出和 `--reason` 参数
- **onboard 注入 Task/EventLog** (`cli_guide.py`):
  - 活跃 Task 概览: 显示 TODO/IN_PROGRESS/REVIEW 任务列表和统计
  - 最近 EventLog 事件摘要: 显示最近 5 条审计事件
  - JSON 输出包含 `task_summary` / `active_tasks` / `recent_events`
- **next 基于 Task 推荐** (`cli_guide.py`):
  - REVIEW 状态任务自动推荐 solidify 操作 (P1 优先级)
  - 依赖阻塞任务提示 (P2 优先级)
  - TODO 积压提示 (>3 个待办时触发, P2 优先级)
- **MCP Server 新增 2 个 Tool** (`mcp_server.py`):
  - `task_create`: AI IDE 可直接创建任务 (自动关联 Insight)
  - `task_transition`: AI IDE 可推进任务状态
  - `start_conversation` prompt 工具列表从 10 个更新为 12 个
- **DECISION-016**: v0.9.3 优先接通 Task/EventLog 到核心工作流 (S 级方向决策)

### Test
- 30 个新单元测试 (`test_task_workflow_integration.py`):
  - TestTransitionCommand (5): success / with_reason / illegal / not_found / json_output
  - TestSolidifyCommand (4): success / not_in_review / not_found / json_output
  - TestRollbackCommand (5): success / with_reason / from_todo / not_found / json_output
  - TestFullLifecycle (2): complete_lifecycle / rollback_and_retry
  - TestOnboardInjection (5): tasks_json / tasks_rich / no_tasks / events_json / events_rich
  - TestNextTaskRecommendations (2): with_review_tasks / no_tasks
  - TestMcpNewTools (3): task_create_tool / task_transition_tool / start_conversation_lists
  - TestCollectProjectContext (4): includes_tasks / includes_events / no_tasks / no_events
- 全量 1164 passed, 1 skipped, 零回归

## v0.9.2 (2026-02-27) - Insight 沉淀信号增强

### New Feature
- **Insight Signal Collector** (`src/vibecollab/insight_signal.py`): 结构化信号驱动的 Insight 候选推荐
  - `InsightSignalCollector`: 从 git 增量 commit、文档变更 diff、Task 变化中提取候选 Insight
  - `SignalSnapshot`: 信号快照管理，记录上次沉淀时间点和 commit hash
  - `InsightCandidate`: 候选 Insight 数据结构（含 confidence、source_signal）
  - 4 种信号分析策略: git_feature / git_bugfix / git_refactor / git_large_change
  - 3 种文档信号: doc_decisions (0.8) / doc_roadmap (0.6) / doc_context (0.4)
  - Task 完成信号: 批量 Task 关闭检测
  - 候选去重: 标题 Jaccard 相似度 > 0.6 自动去重
- **Session Store** (`src/vibecollab/session_store.py`): 对话 summary 持久化存储
  - `SessionStore`: `.vibecollab/sessions/` 目录管理
  - `Session`: 对话记录数据结构（summary / key_decisions / files_changed / tags）
  - CRUD: save / get / list_all / list_recent / list_since / delete / count
  - `get_summaries_text()`: 获取最近 session 摘要文本用于 insight suggest
- **CLI `insight suggest`** (`cli_insight.py`): 交互式/自动候选推荐命令
  - `--json`: JSON 输出模式
  - `--auto-confirm`: 非交互模式自动创建所有候选
  - 交互模式支持编号选择 / all / q 退出
- **MCP Server 新增 2 个 Tool**:
  - `insight_suggest`: 基于信号推荐候选 Insight
  - `session_save`: 保存对话 session summary（支持 decisions / files / tags）
- **`insight add` 快照联动**: 手动创建 Insight 时自动更新信号快照

### Test
- 60 个新单元测试:
  - `test_insight_signal.py` (42 tests): SignalSnapshot / InsightCandidate / SnapshotCRUD / GitSignals / DocChanges / TaskChanges / Analysis / Suggest / Helpers
  - `test_session_store.py` (18 tests): Session / SessionStore CRUD / list / count / summaries
- 全量 1134 passed, 1 skipped, 零回归

## v0.9.1 (2026-02-27) - MCP Server + AI IDE 集成

### New Feature
- **MCP Server** (`vibecollab mcp serve`): 标准 Model Context Protocol Server 实现
  - 6 个 Resources: `contributing_ai`, `context`, `decisions`, `roadmap`, `changelog`, `insights/list`
  - 8 个 Tools: `insight_search`, `insight_add`, `check`, `onboard`, `next_step`, `task_list`, `project_prompt`, `developer_context`, `search_docs`
  - 1 个 Prompt: `start_conversation` (项目信息 + CONTEXT 摘要 + 开发者上下文)
  - 支持 `stdio` / `sse` 两种传输模式
  - 可选依赖 `pip install vibe-collab[mcp]`
- **MCP CLI 命令组** (`vibecollab mcp`):
  - `mcp serve` — 启动 MCP Server
  - `mcp config --ide cursor/cline/codebuddy` — 输出 IDE 配置内容
  - `mcp inject --ide all` — 自动注入配置到 IDE 配置文件（合并已有配置）
- **CodeBuddy Rule**: `.codebuddy/rules/vibecollab-protocol.mdc` always 规则，项目 clone 即生效

### Decision
- **DECISION-015**: 砍掉 v0.9.2 自举能力 + v0.10.1 Agent 增强 (S 级)
  - `bootstrap` 价值不足，`vibecollab ai` 保持 experimental 冻结
  - 版本链简化为: v0.9.0(语义检索) → v0.9.1(MCP) → v0.9.2(信号驱动沉淀) → v0.9.3(Insight 生命周期) → v0.10.0(发布)

### Insight
- INS-013: 版本规划应果断砍掉低价值里程碑
- INS-014: 功能重复时优先判断是否已有外部替代方案
- INS-015: Insight 沉淀需要结构化信号而非纯 LLM 推理

### Test
- 35 个 MCP Server 单元测试（34 passed, 1 skipped）
- 全量 1074 passed, 零回归

## v0.8.0-dev (开发中) - Config 配置管理系统

### Architecture
- **三层配置架构**: `环境变量 > ~/.vibecollab/config.yaml > 内置默认值`
- 配置文件存放在用户 home 目录（`~/.vibecollab/config.yaml`），不进 git
- 轻量 .env 解析：自实现 `parse_dotenv()`，仅提取 `VIBECOLLAB_*` 前缀变量
- **v0.9.0 语义检索引擎**:
  - `Embedder` 模块 — 轻量 embedding 抽象层，支持 OpenAI / sentence-transformers / pure_python 三后端
  - `VectorStore` 模块 — SQLite 持久化向量存储，纯 Python 余弦相似度
  - `Indexer` 模块 — 项目文档 + Insight YAML 索引器（Markdown chunk 拆分）
  - `vibecollab index` 命令 — 增量/重建索引
  - `vibecollab search` 命令 — 全局语义搜索
  - `vibecollab insight search --semantic` — Insight 语义搜索模式
  - 零外部依赖降级方案: pure_python trigram 哈希 embedding
  - 可选 `pip install vibe-collab[embedding]` 安装 sentence-transformers
  - `onboard` 语义增强 — 从 CONTEXT.md/开发者上下文提取任务描述 → 向量检索 Top-N 相关 Insight
    - Rich 面板 "与当前任务相关的 Insight (语义匹配)" + JSON `related_insights` 字段
    - 开发者上下文优先于全局 CONTEXT.md 作为查询文本
    - 11 个新增单元测试（_search_related_insights + onboard 集成）

### Decision
- **`vibecollab ai` 命令组标记为 experimental**: VibeCollab 核心定位是协议管理工具，LLM 通信和 Tool Use 交给 Cline/Cursor/Aider 等专业终端。`ai ask/chat/agent` 保留作为轻量替代，但不再作为主力开发方向。受影响模块：`cli_ai.py`、`llm_client.py`、`agent_executor.py`、`config_manager.py`（均可干净隔离，核心功能零依赖）

### Refactor
- **统一 Windows GBK 编码兼容层** (`_compat.py`): 提取 `is_windows_gbk()` / `EMOJI` / `BULLET` 到共享模块
  - 消除 4 处重复定义（cli.py / cli_ai.py / cli_lifecycle.py / cli_config.py）
  - 为 cli_guide.py / cli_insight.py 补充缺失的 GBK 兼容机制
  - 修复 7 处硬编码 emoji（📦 ⏳ ● •），避免 Windows GBK 终端 UnicodeEncodeError
  - 统一 cli_insight.py 的 `sys.exit(1)` → `raise SystemExit(1)`（9 处）
  - 移除不再需要的 `import platform` / `import sys`
- **cli_insight.py `_load_insight_manager()` 错误处理**: 检查 `.vibecollab/` 目录存在性，提供友好提示
- **Ruff lint 全量修复**: 68 errors → 0（61 auto-fix + 7 手动修复：E402 导入位置、F841 未使用变量、F401 未使用导入、I001 导入排序、F541 空 f-string）

### New Feature
- **`vibecollab prompt` 命令**: 生成 LLM 可直接使用的上下文 prompt 文本
  - 从 CONTRIBUTING_AI.md 自动提取协议核心章节（决策分级/对话流程/角色定义/Git 规范）
  - 注入项目当前状态（CONTEXT.md / 最近决策 / 路线图待办 / 未提交变更）
  - 注入 Insight 经验摘要 + Insight 工作流说明
  - `--compact` 精简模式（仅协议核心 + 状态，省略路线图和角色定义）
  - `--sections protocol,context,insight` 选择性注入
  - `--copy` 直接复制到剪贴板（Windows clip 支持）
  - `-d <developer>` 含开发者个人上下文
  - 替代手动复制 CONTRIBUTING_AI.md 到 LLM 对话窗口
- **`_collect_project_context()` 共享函数**: 从 `onboard` 提取数据收集逻辑，`onboard` 和 `prompt` 复用
- **`_extract_md_sections()` 工具函数**: 从 Markdown 按标题提取指定章节内容
- **`_build_prompt_text()` 格式化器**: 构建纯 Markdown 格式的 LLM prompt
- **Insight 经验沉淀工作流** (IDE 对话模式融入):
  - 新增 `27_insight_workflow.md.j2` 模板章节 — 定义何时/如何沉淀经验
  - 对话结束流程增加"经验沉淀检查"步骤（`06_dialogue_protocol.md.j2` 更新）
  - `vibecollab next` 命令增加 Insight 沉淀提示（基于 5 种信号自动检测）
  - manifest.yaml 注册 `insight_workflow` 章节（默认开启，可通过 `insight.enabled: false` 关闭）
- **`vibecollab config setup`**: 交互式 LLM 配置向导
  - Provider 选择（OpenAI / Anthropic）
  - API Key 安全输入（隐藏输入）
  - Base URL 预设（OpenAI 官方 / OpenRouter / DeepSeek / 阿里云百炼 / 自定义）
  - 可选模型名设置
- **`vibecollab config show`**: 查看当前配置（三层合并结果 + 来源标识）
- **`vibecollab config set <key> <value>`**: 单项配置设置
- **`vibecollab config path`**: 显示配置文件路径
- **`resolve_llm_config()`**: 统一三层配置解析函数
- **`LLMConfig.__post_init__`**: 改为三层优先级（显式参数 > 环境变量 > 配置文件 > 默认值）
- **改进错误提示**: `_ensure_llm_configured()` 提供三种配置方式指引
- **`vibecollab check` key_files 陈旧性检查**: 支持 `max_stale_days` 配置
  - `documentation.key_files` 新增可选 `max_stale_days` 字段
  - 文件存在但超过配置天数未更新时，报 warning 并提示 `update_trigger`
  - `QA_TEST_CASES.md` 配置 7 天阈值，`ROADMAP.md` 配置 14 天阈值
  - 3 个单元测试覆盖（触发/未触发/未配置）

### Bug Fix
- **CI/CD 修复**: 
  - `__init__.py` 版本号 `0.5.9` → `0.8.0.dev0`（与 pyproject.toml 同步）
  - Python 矩阵从 `3.8-3.12` 更新为 `3.9-3.13`（3.8 已 EOL，`actions/setup-python@v5` 不支持）
  - `requires-python` 从 `>=3.8` 更新为 `>=3.9`
  - classifiers 移除 3.8、添加 3.13
- **修复 OpenAI 空 choices 导致 IndexError**: `_call_openai()` 中 `data.get("choices", [{}])[0]` 在 API 返回空 `choices: []` 时崩溃，改为安全取值
- **修复 flaky test `test_onboard_basic`**: Windows 环境下 `test_serve_lock_conflict` 的 `SystemExit(1)` 导致 `subprocess.run` 内部线程残留 `KeyboardInterrupt`，污染后续 `onboard` 命令的 `_get_git_uncommitted()` 调用
  - 根因: `KeyboardInterrupt` 继承自 `BaseException` 而非 `Exception`，原有的 `except Exception` 无法捕获
  - 修复: `cli_guide.py` 中 `_get_git_uncommitted()` 和 `_get_git_diff_files()` 的异常处理从 `except Exception` 改为 `except BaseException`
  - 验证: 连续两次全量 779/779 passed
- **修复 flaky test `test_whoami_basic`**: `developer.py` 的 `_get_git_username()` 同样受 `KeyboardInterrupt` 残留影响
  - 修复: `except Exception` → `except BaseException`
  - 验证: 全量 809/809 passed
- **系统性修复所有 subprocess 相关的 `except Exception`**: 审计并批量修复 9 处 subprocess 调用的异常处理
  - `protocol_checker.py`: 5 处 git 命令调用
  - `git_utils.py`: 2 处 git init/status 调用
  - `agent_executor.py`: 2 处测试执行/git commit 调用
  - 统一从 `except Exception` 改为 `except BaseException`，防止 `KeyboardInterrupt` 残留导致 flaky test

### Testing
- **Agent 模式 E2E 测试**: 35 个新测试覆盖 agent_executor + cli_ai 的高优缺口
  - `test_agent_executor.py` (+21 tests): git_commit 真实 git repo (成功/无变更/无 repo)、run_tests 超时/异常/自定义命令、apply_changes 写入失败/删除不存在、validate 无效路径、rollback 失败/空、full_cycle git 失败/真实 git、parse_single_change 边界输入
  - `test_cli_ai.py` (+14 tests): serve 断路器触发、自适应退避、内存阈值停止、pending-solidify 等待、_execute_agent_cycle 5 个分支 (plan 失败/exec 失败/无变更/异常/成功)、run 有效变更/plan 失败、ask/chat/plan 异常路径、status 陈旧锁/无效锁
  - 全量 844/844 passed (连续两次稳定)
- **LLM Client mock 集成测试**: 26 个新测试覆盖双 provider + 配置文件层 + 边界情况
  - `test_llm_client.py` (+26 tests): 配置文件三层解析 (文件回退/env 覆盖/显式覆盖/异常降级)、OpenAI+Anthropic 双 provider 深度 (URL 拼接/header 验证/未知 provider 降级/空 choices/多 system 消息/多内容块)、build_project_context 边界 (tasks 损坏/events 损坏/空文件/全 DONE)、ask() 路径 (双参数/temperature/默认构造)
  - 发现并修复 OpenAI 空 choices IndexError bug
  - 全量 868/868 passed (连续两次稳定)
- **Agent 稳定性压力测试**: 13 个新测试覆盖长运行/并发/回滚/退避
  - `test_agent_executor.py` (+13 tests): 100 周期连续 apply、交替成功/失败周期、多实例文件操作隔离、PID 锁获取/释放/陈旧接管/活跃拒绝、自适应退避不超 max/成功重置、回滚恢复/移除新文件/多文件回滚/无效输出/受保护文件
- **Insight 系统泛用性测试**: 20 个新测试覆盖大规模/衰减/关联/循环保护
  - `test_insight_manager.py` (+20 tests): 100 条 Insight 创建/搜索/列出/衰减、多 tags 搜索、10 层溯源链、50 轮衰减收敛、衰减+奖励稳态、大量 record_use 增长、权重精度验证、停用→激活→再衰减、阈值边界、中文标签、大小写不敏感、部分重叠、空标签、循环引用保护
  - 全量 899/899 passed
- **极简/复杂项目边界测试**: 15 个新测试覆盖 init+generate+check+health+validate
  - `TestMinimalProject` (7 tests): 最少参数 init、极简 generate、极简 check/health/validate、空 YAML、只有 project_name
  - `TestComplexProject` (8 tests): 全量配置（多开发者+lifecycle+documentation）的 generate/check/health/upgrade/validate/JSON 输出、所有 domain 的 init
  - 全量 914/914 passed
- **Insight 工作流 + next 命令测试**: 16 个新测试覆盖 Insight 沉淀提示 + 模板渲染
  - `TestCheckInsightOpportunity` (11 tests): 无变更/单文件/多类型+测试/仅测试/配置变更/大量变更/首次沉淀/已有 Insight/YAML 扩展名/组合信号
  - `TestInsightWorkflowTemplate` (5 tests): manifest 注册/默认渲染/禁用/位置/对话协议集成
  - 全量 929/929 passed
- **CLI E2E 测试全量覆盖**: 48 个 CLI 命令中 12 个缺失测试已全部补齐
  - `tests/test_cli_dev.py` (17 tests): dev 命令组 7 个子命令（whoami/list/status/sync/init/switch/conflicts）
  - `tests/test_cli.py` (+10 tests): 顶层命令（templates/export-template/version-info/check/health）
  - 全量 809/809 passed
- **测试覆盖率 76% → 81%**: 新增 128 个测试覆盖 6 个低覆盖模块
  - `test_llmstxt.py` (17 tests): 68% → 97%
  - `test_templates.py` (13 tests): 60% → 91%
  - `test_git_utils.py` (21 tests): 52% → 100%
  - `test_lifecycle.py` (25 tests): 28% → 93%
  - `test_extension.py` (41 tests, 重写): 64% → 100%
  - `test_cli_lifecycle.py` (11 tests): 23% → 92%
- **新增 38 个单元测试** (`tests/test_config_manager.py`):
  - `TestConfigPaths` (2): 路径正确性
  - `TestLoadSaveConfig` (5): 文件操作
  - `TestGetSetConfigValue` (5): 嵌套读写
  - `TestParseDotenv` (8): .env 解析
  - `TestResolveLLMConfig` (7): 三层合并
  - `TestLLMConfigWithFile` (4): LLMConfig 集成
  - `TestCLIConfig` (7): CLI 命令端到端

---

## v0.7.2 (2026-02-25) - README 全面更新

### Documentation
- **README.md 全面重写**: 特性说明从 v0.5.x 更新到 v0.7.1
  - 特性列表重组为 5 大分类（知识沉淀/协作引擎/项目管理/多开发者/基础设施）
  - 工作流程图新增 Task-Insight 自动关联 + Insight 沉淀 + Agent 引导节点
  - CLI 命令新增 insight (13 子命令) / task (4 子命令) / onboard / next
  - 项目结构新增 insight_manager / cli_insight / cli_task / cli_guide / insight.schema
  - 版本历史更新至 v0.7.1
- PyPI 项目描述同步更新（README.md 作为 long_description）

---

## v0.7.1 (2026-02-25) - Task-Insight 自动关联

### Architecture
- **DECISION-014 (A 级)**: Task-Insight 单向自动关联 — Task 创建时自动搜索关联 Insight
- **零配置集成**: InsightManager 可选注入，无 InsightManager 时自动退化，完全向后兼容

### New Feature
- **Task-Insight 自动关联** (`src/vibecollab/task_manager.py`):
  - `TaskManager.__init__` 新增可选 `insight_manager` 参数
  - `_extract_search_tags()`: 从 feature/description/role 提取关键词，过滤停用词
  - `_find_related_insights()`: Jaccard × weight 匹配，结果存入 `task.metadata["related_insights"]`
  - `suggest_insights()`: 对已有任务推荐关联 Insight
  - EventLog 自动记录 `related_insights` 到 TASK_CREATED 事件
- **Task CLI 命令** (`src/vibecollab/cli_task.py`):
  - `vibecollab task create --id --role --feature [--assignee] [--description] [--json]`
  - `vibecollab task list [--status] [--assignee] [--json]`
  - `vibecollab task show <id> [--json]`
  - `vibecollab task suggest <id> [-n limit] [--json]`

### Testing
- **新增 28 个单元测试** (`tests/test_task_insight_integration.py`):
  - `TestExtractSearchTags` (8 tests): 关键词提取（英文/中文/停用词/去重）
  - `TestInsightAutoLink` (7 tests): 自动关联（匹配/无匹配/无 IM/score/event/持久化/description增强）
  - `TestSuggestInsights` (4 tests): 推荐（存在/不存在/无IM/limit）
  - `TestBackwardCompatibility` (2 tests): 向后兼容验证
  - `TestCLI` (7 tests): CLI 端到端（create/show/list/suggest/invalid/empty/rich）

---

## v0.7.0 (2026-02-25) - Insight 沉淀系统 + Agent 引导

### Architecture
- **DECISION-012 (S 级)**: 砍掉 Web UI，转向 Insight 沉淀系统
- **两层分离架构**: Insight 本体（可移植知识包）+ Registry 注册表（项目级使用状态）
- **Tag 驱动 Developer 描述**: 开放式标签体系替代枚举字段
- **自描述溯源协议**: origin.context + source.description/url/project, ref 降级为 hint
- **关联文档一致性检查**: linked_groups 三级检查 (local_mtime / git_commit / release)
- **Agent 引导系统**: onboard (接入引导) + next (行动建议)，从被动诊断进化为主动引导
- **DECISION-012 (S 级)**: 砍掉 Web UI，转向 Insight 沉淀系统
- **两层分离架构**: Insight 本体（可移植知识包）+ Registry 注册表（项目级使用状态）
- **Tag 驱动 Developer 描述**: 开放式标签体系替代枚举字段

### New Feature
- **`schema/insight.schema.yaml`**: Insight 三部分 Schema（本体 + Registry + Developer Tag 扩展）
- **`src/vibecollab/insight_manager.py`**: 核心管理模块
  - CRUD: create / get / list_all / update / delete
  - Registry: record_use / apply_decay / get_active_insights
  - 搜索: search_by_tags (Jaccard × 权重) / search_by_category
  - 溯源: get_derived_tree (派生关系树)
  - 一致性校验: check_consistency (5 项全量检查)
  - EventLog 集成: 所有操作自动记录审计事件
  - SHA-256 内容指纹防篡改
- **Developer metadata 扩展** (`src/vibecollab/developer.py`):
  - tags / contributed / bookmarks CRUD 方法
  - `_read_metadata()` / `_write_metadata()` 内部助手
  - `get_tags()` / `set_tags()` / `add_tag()` / `remove_tag()`
  - `get_contributed()` / `add_contributed()` / `remove_contributed()`
  - `get_bookmarks()` / `add_bookmark()` / `remove_bookmark()`
- **CLI 命令组** (`src/vibecollab/cli_insight.py` — `vibecollab insight`):
  - `insight list [--active-only] [--json]` — 列出所有沉淀
  - `insight show <id>` — 查看沉淀详情
  - `insight add --title --tags --category --scenario --approach [...]` — 创建沉淀
  - `insight search --tags/--category` — 搜索沉淀
  - `insight use <id>` — 记录使用，奖励权重
  - `insight decay [--dry-run]` — 执行权重衰减
  - `insight check [--json]` — 一致性校验
  - `insight delete <id> [-y]` — 删除沉淀
  - `insight bookmark <id>` — 收藏沉淀
  - `insight unbookmark <id>` — 取消收藏
  - `insight trace <id> [--json]` — 溯源树可视化（ASCII 树 + JSON）
  - `insight who <id> [--json]` — 查看跨开发者使用信息
  - `insight stats [--json]` — 跨开发者共享统计
- **跨开发者共享** (`src/vibecollab/insight_manager.py`):
  - `get_full_trace()`: 递归展开上下游派生树
  - `get_insight_developers()`: 反查创建者/使用者/收藏者/贡献者
  - `get_cross_developer_stats()`: 汇总跨开发者贡献/使用/收藏统计
- **Agent 引导命令** (`src/vibecollab/cli_guide.py`):
  - `vibecollab onboard [-d <developer>] [--json]` — AI 接入引导（项目概况/进度/决策/待办/应读文件/开发者视角/关键文件清单）
  - `vibecollab next [--json]` — 行动建议（关联文档同步P0/超时检查P1/commit建议P1/缺失文件P2/自检P3）
- **文档一致性检查增强** (`src/vibecollab/protocol_checker.py`):
  - `update_threshold_hours` 从 24h → 0.25h (15min)，可配置
  - `_check_document_consistency()`: linked_groups 关联文档组检查
  - `_check_mtime_consistency()`: 本地文件修改时间级别检查
  - `_check_git_commit_consistency()`: git 提交同步检查
  - `_check_release_consistency()`: 版本标签同步检查
  - `key_files` 声明的文件存在性检查

### Testing
- **新增 266 个单元测试** (全量 566 tests, 零回归):
  - `tests/test_developer.py` (88 tests): developer.py 全覆盖（含 Tag 扩展）
  - `tests/test_insight_manager.py` (74 tests): insight_manager.py 全覆盖
  - `tests/test_cli_insight.py` (45 tests): cli_insight.py 全覆盖
  - `tests/test_protocol_checker.py` (21 tests): protocol_checker.py 全覆盖（含一致性检查）
  - `tests/test_cli_guide.py` (29 tests): cli_guide.py 全覆盖（onboard/next/helpers）

### Cleanup
- `.gitignore` 添加 `Reference/` 排除外部参考仓库
- 清理 ROADMAP.md / DECISIONS.md 中的外部专有术语引用
- **protocol_checker 多开发者动态发现**: `_check_multi_developer_protocol()` 从 `docs/developers/` 目录自动扫描开发者，无需静态 `multi_developer.developers` 配置
- **CONTRIBUTING_AI.md 命令文档补全**: 新增 onboard/next/insight(13 子命令)/health/check --insights 到 CLI 命令参考
- **ROADMAP.md 同步**: 添加 v0.7.0 全部已完成项（一致性检查/Agent 引导/技术债务/动态发现）
- **自举全量验证**: onboard → next → check → insight 全链路在项目自身上正常工作

---

## v0.6.0 (2026-02-24) - 协议成熟度提升 + 测试覆盖率增强

### 里程碑完成
本版本完成了 v0.6.0 里程碑的所有核心目标，标志着 VibeCollab 协议框架进入成熟阶段。

### Testing
- **测试覆盖率提升**: 58% → 68% (+10%)
- **新增 74 个单元测试** (总计 359 tests):
  - `test_conflict_detector.py` (38 tests): 冲突检测全覆盖
  - `test_prd_manager.py` (36 tests): PRD 管理全覆盖
- **模块覆盖率**:
  - `conflict_detector.py`: 0% → 99%
  - `prd_manager.py`: 0% → 92%

### Cleanup
- **移除遗留文件**:
  - `project.yaml.broken` (旧版配置备份)
  - `check_protocol.py` (已被 CLI 替代)
  - `llm_example.txt` (示例输出文件)
  - `test-vibe-project/` (空测试目录)
  - `test-project-1696446371/` (临时测试项目)

### v0.6.0 里程碑总结
- ✅ EventLog append-only 审计日志
- ✅ TaskManager 验证-固化-回滚
- ✅ Pattern Engine + Template Overlay
- ✅ Legacy 代码移除 (generator.py 1713→83 行)
- ✅ CI/CD 流程 (GitHub Actions)
- ✅ Health Signal Extractor
- ✅ Agent Executor
- ✅ Ruff lint 全量修复
- ✅ 测试覆盖率提升 (58%→68%)

---

## v0.5.9 (2026-02-24) - Pattern Engine + Health Signals + Agent Executor

### New Feature
- **PatternEngine** (`src/vibecollab/pattern_engine.py`):
  - Jinja2 模板驱动的 CONTRIBUTING_AI.md 生成引擎
  - `manifest.yaml` 控制章节顺序、条件、模板映射
  - 27 个 `.md.j2` 模板文件替代硬编码 Python 方法
  - 条件求值支持 `|default` 语法 (如 `config.x.enabled|true`)
  - `DEFAULT_STAGES` 内置阶段定义回退

- **Template Overlay** (本地模板覆盖机制):
  - 项目可在 `.vibecollab/patterns/` 创建自定义模板
  - Jinja2 `ChoiceLoader` 实现本地优先、内置回退的模板解析
  - 本地 `manifest.yaml` 支持: 覆盖章节、插入新章节(`after` 定位)、排除章节(`exclude` 列表)
  - `list_patterns()` 标注 `source: "local" | "builtin"`

- **Health Signal Extractor** (`src/vibecollab/health.py`):
  - 从 ProtocolChecker + EventLog + TaskManager 提取项目健康信号
  - 三级信号: CRITICAL / WARNING / INFO
  - 10+ 信号类型: 协议合规、日志完整性、活跃度、冲突、验证失败率、任务进度、积压、审核瓶颈、依赖阻塞、负载均衡
  - 评分系统: 0-100 分 + A/B/C/D/F 等级
  - CLI 命令 `vibecollab health` (支持 `--json` JSON 输出)

- **Agent Executor** (`src/vibecollab/agent_executor.py`):
  - 将 LLM 计划转化为实际文件变更 (解析 JSON → 写入文件 → 运行测试 → git commit)
  - 安全措施: 路径穿越检测、受保护文件列表、文件大小限制、最大变更文件数
  - 测试失败自动回滚 (备份/恢复机制)
  - `agent run` 和 `agent serve` 现在实际执行变更而非仅打印

### Refactor
- **Legacy 代码移除**: `generator.py` 从 1713 行精简到 83 行

### CI/CD
- **GitHub Actions** (`.github/workflows/ci.yml`):
  - 矩阵测试: Python 3.8-3.12 × Ubuntu + Windows
  - Ruff lint + pytest + coverage
  - 构建验证 + artifact 上传 + Codecov 集成

### Code Quality
- **Ruff lint 全量修复**: 908 个 auto-fixable 错误已修复

### Architecture
- DECISION-011: Pattern Engine 架构 (manifest 驱动 + 模板覆盖 + legacy 移除)

### Testing
- 285 tests 总计 (新增 70):
  - 40 PatternEngine tests (含 8 Template Overlay)
  - 32 Health Signal tests
  - 38 Agent Executor tests
- 全量零回归

---

## v0.5.8 (2026-02-24) - AI CLI 命令层 (三模式架构)

### New Feature
- **AI CLI 命令** (`src/vibecollab/cli_ai.py`):
  - `vibecollab ai ask "问题"` — 单轮 AI 提问，自动注入项目上下文
  - `vibecollab ai chat` — 多轮对话模式，支持 exit/quit/bye 退出
  - `vibecollab ai agent plan` — 只读分析，生成行动计划不执行
  - `vibecollab ai agent run` — 单次 Plan→Execute→Solidify 周期
  - `vibecollab ai agent serve -n 50` — 长运行 Agent 服务 (服务器部署)
  - `vibecollab ai agent status` — 查看 Agent 运行状态

### Safety Gates
- **PID 单例锁**: 防止多个 agent 实例同时运行
- **pending-solidify 门控**: REVIEW 状态任务未固化时阻塞新周期
- **最大周期数**: 默认 50，可通过 `VIBECOLLAB_AGENT_MAX_CYCLES` 配置
- **自适应睡眠 + 指数退避**: 失败/过快周期自动退避 (2s→300s)
- **修复循环断路器**: 连续 3 次失败 → 长等待后重置
- **RSS 内存阈值**: 默认 500MB，超限自动停止

### Architecture
- 三模式共存: IDE 对话 / CLI 人机交互 / Agent 自主
- DECISION-010: 三模式架构决策记录

### Testing
- 32 新增 unit tests (全覆盖: 配置/PID锁/solidify门控/ask/chat/plan/run/serve/status)
- 全量 174 tests，零回归

## v0.5.7 (2026-02-24) - LLM Client for CLI + API Key mode

### New Feature
- **LLM Client module** (`src/vibecollab/llm_client.py`):
  - Provider-agnostic: OpenAI-compatible APIs and Anthropic Claude
  - Zero impact on existing offline features (pure additive, lazy httpx import)
  - `LLMConfig`: environment variable based config (`VIBECOLLAB_LLM_*`)
  - `LLMClient.chat()`: multi-turn conversation
  - `LLMClient.ask()`: single-question convenience with auto project context
  - `build_project_context()`: assembles project.yaml, CONTEXT.md, tasks, events into LLM-ready prompt
  - API key safety: `to_safe_dict()` masks secrets, no keys in project files
  - Custom endpoint support: any OpenAI-compatible base URL

### New Tests
- **30 unit tests** (`tests/test_llm_client.py`):
  - `TestLLMConfig` (7): defaults, env vars, overrides, safe serialization
  - `TestMessageAndResponse` (4): data classes
  - `TestBuildProjectContext` (8): context assembly, truncation, Unicode, section toggles
  - `TestLLMClient` (11): provider dispatch, mock API calls, error handling, context injection

### Installation
- `httpx` added as optional dependency: `pip install vibe-collab[llm]`

---

## v0.5.6 (2026-02-24) - TaskManager with validate-solidify-rollback

### New Feature
- **TaskManager module** (`src/vibecollab/task_manager.py`):
  - Structured `Task` dataclass with all fields from project.yaml `task_unit` schema
  - `TaskStatus` enum: TODO → IN_PROGRESS → REVIEW → DONE
  - State machine with legal transitions (including pause/reject paths)
  - `TaskManager` class: create, get, list, transition, validate, solidify, rollback, count
  - Validate-solidify gate pipeline: required fields → dependency satisfaction → output check
  - Rollback support: IN_PROGRESS → TODO, REVIEW → IN_PROGRESS
  - Full EventLog integration: every CRUD/transition/solidify auto-logs events
  - Atomic JSON persistence (`.vibecollab/tasks.json`)
  - Task ID format validation (`TASK-{ROLE}-{SEQ}`)

### New Tests
- **53 unit tests** (`tests/test_task_manager.py`):
  - `TestTask` (5): defaults, explicit fields, roundtrip, ID validation
  - `TestStateMachine` (4): transition legality
  - `TestValidationResult` (3): ok/failed/serialization
  - `TestTaskManager` (41): CRUD, transitions, validation, solidify, rollback, persistence, full lifecycle, Unicode

### Integration Verified
- TaskManager + EventLog cross-module validation: full lifecycle produces 5 events, integrity CLEAN
- Total test suite: 112 tests, zero regression

---

## v0.5.5 (2026-02-24) - EventLog append-only audit trail

### New Feature
- **EventLog module** (`src/vibecollab/event_log.py`):
  - Append-only JSONL audit trail for all project operations
  - 17 event types covering task lifecycle, developer actions, collaboration, validation, lifecycle, and decisions
  - SHA-256 content-addressable fingerprinting for tamper detection
  - `EventLog` class: `append()`, `read_all()`, `read_recent(n)`, `query()`, `count()`, `verify_integrity()`
  - Atomic append with `fsync` for write durability
  - Parent-event linkage via `parent_id` for causal chains
  - Default storage: `.vibecollab/events.jsonl`

### New Tests
- **23 unit tests** (`tests/test_event_log.py`):
  - `TestEvent` (6): auto-fields, explicit fields, fingerprint determinism, content sensitivity, serialization, roundtrip
  - `TestAtomicAppend` (3): file creation, preservation, newline handling
  - `TestEventLog` (14): CRUD, query filters, integrity verification, malformed line handling, Unicode support

### Architecture Decision
- **DECISION-009**: Selective pattern borrowing for protocol maturity (Direction B confirmed)

---

## v0.5.4 (2026-02-24) - CLI 开发者切换功能

### 新功能
- **CLI 开发者切换** (`vibecollab dev switch`):
  - 支持通过 CLI 切换当前开发者身份，无需修改 Git 配置或环境变量
  - `vibecollab dev switch alice` - 直接切换到指定开发者
  - `vibecollab dev switch` - 交互式选择开发者
  - `vibecollab dev switch --clear` - 清除切换设置，恢复默认识别策略
  - 切换状态持久化到 `.vibecollab.local.yaml`（已加入 .gitignore）

### 改进
- **`vibecollab dev whoami` 增强**:
  - 显示身份来源（CLI 切换 / 环境变量 / Git 用户名 / 系统用户名）
  - 更清晰地展示当前开发者识别方式

### 技术实现
- `DeveloperManager` 新增方法:
  - `switch_developer(developer)` - 切换开发者并持久化
  - `clear_switch()` - 清除切换设置
  - `get_identity_source()` - 获取身份来源
  - `_get_local_developer()` - 从本地配置读取开发者
- 身份识别优先级：本地配置 > 环境变量 > 主策略 > 降级策略

### 文档更新
- CONTRIBUTING_AI.md 更新 CLI 命令参考，添加 switch 命令说明
- alice 的 CONTEXT.md 更新工作方向

---

## v0.5.1 (2026-02-10) - 跨开发者冲突检测

### 重大特性
- **跨开发者冲突检测** (v0.5.1):
  - 自动检测多个开发者之间的工作冲突
  - 支持文件冲突、任务冲突、依赖冲突、命名冲突检测
  - 提供详细的冲突报告和处理建议

### 新增模块
- `src/vibecollab/conflict_detector.py`:
  - `ConflictDetector`: 跨开发者冲突检测器
  - `Conflict`: 冲突对象表示
  - 支持检测文件冲突、任务重叠、循环依赖、命名冲突

### CLI 命令扩展
- 新增 `vibecollab dev conflicts` 命令:
  - 检测当前开发者与其他开发者的冲突
  - `--verbose`: 显示详细冲突信息
  - `--between alice bob`: 检测特定两人之间的冲突
  - 自动识别高/中/低优先级冲突

### 文档完善
- **CONTRIBUTING_AI.md 新增章节**: 
  - "八、多开发者/Agent 协作协议" 完整章节
  - 协作模式概述、目录结构、身份识别
  - 上下文管理、协作文档、对话流程适配
  - 冲突检测与预防、CLI 命令参考、最佳实践
- **README.md 更新**:
  - 添加多开发者模式初始化示例
  - 展示单/多开发者目录结构对比
  - 补充多开发者相关 CLI 命令文档

### 冲突检测算法
- 文件冲突：检测多个开发者同时修改相同文件
- 任务冲突：基于相似度算法检测重复/重叠任务
- 依赖冲突：深度优先搜索检测循环依赖
- 命名冲突：检测代码块中的类名/函数名重复

### 向后兼容
- 所有 v0.5.0 功能保持不变
- 冲突检测为增量特性，不影响现有使用

### Bug 修复
- **本项目自身启用多开发者模式** (对话19):
  - project.yaml 添加 multi_developer 配置（enabled: true）
  - 重新生成 CONTRIBUTING_AI.md，包含完整多开发者章节
  - 实践自己提倡的协作特性
- **upgrade 命令支持 multi_developer 配置保留**:
  - 修复升级时未保留用户 multi_developer 配置的问题
  - 添加 Tuple 类型导入修复 NameError
  - 确保旧项目升级到 v0.5.1 时包含多开发者配置（默认 disabled）



---

## v0.5.0 (2026-02-10) - 多开发者支持

### 重大特性
- **多开发者协同支持** (DECISION-008):
  - 支持多个开发者/多个 AI Agent 协同开发同一项目
  - 开发者身份自动识别（基于 Git 用户名）
  - 开发者独立上下文管理（`docs/developers/{developer}/CONTEXT.md`）
  - 全局上下文自动聚合（`docs/CONTEXT.md` 自动生成）
  - 开发者协作文档（`docs/developers/COLLABORATION.md`）记录依赖和交接

### 新增模块
- `src/vibecollab/developer.py`:
  - `DeveloperManager`: 开发者身份识别、目录管理、元数据维护
  - `ContextAggregator`: 全局上下文聚合算法
  - `migrate_to_multi_developer()`: 单开发者项目迁移工具

### CLI 命令扩展
- 新增 `vibecollab dev` 命令组:
  - `dev whoami`: 显示当前开发者身份
  - `dev list`: 列出所有开发者及状态
  - `dev status [developer]`: 查看开发者详细状态
  - `dev sync`: 手动触发全局 CONTEXT 聚合
  - `dev init [-d developer]`: 初始化开发者上下文
- `vibecollab init` 新增 `--multi-dev` 选项，支持初始化多开发者项目

### 配置扩展
- `project.yaml` 新增 `multi_developer` 配置节:
  - `identity`: 开发者识别策略（git_username/system_user/manual）
  - `context`: 上下文管理配置（目录结构、聚合规则）
  - `collaboration`: 协作管理配置（依赖跟踪、交接记录）
  - `dialogue_protocol`: 多开发者模式下的对话流程

### 决策记录
- DECISION-008: 多开发者支持架构设计 (A 级)
  - CHANGELOG.md、DECISIONS.md 保持全局统一
  - 添加 `initiator` 和 `participants` 字段标记参与者
  - Git commit 不额外标记，使用原生 author 信息

### 测试验证
- 所有核心功能测试通过
- 开发者身份识别正常
- 上下文聚合算法验证通过
- 文件生成结构正确

### 向后兼容
- 单开发者模式完全兼容
- 现有项目可平滑迁移到多开发者模式

---

## v0.4.3 (2026-02-09)

### Bug 修复
- **Windows 编码问题修复** (对话16):
  - 修复 `vibecollab check` 在 Windows GBK 环境下的 emoji 编码错误
  - 实现 `is_windows_gbk()` 平台检测函数
  - 添加 emoji 字符映射（✅→OK, ⚠️→!, ❌→X, ℹ️→i）
  - 添加 bullet point 映射（•→-）
  - 修复 `cli.py` 和 `cli_lifecycle.py` 中所有 emoji 使用

### 配置改进
- **关键文件职责配置完善**:
  - 补充 `llms.txt`, `DECISIONS.md`, `QA_TEST_CASES.md`, `ROADMAP.md` 到文档体系配置
  - 确保其他仓库使用时能生成完整的关键文件职责说明（CONTRIBUTING_AI.md 第八章）
  - 同步更新 `project.yaml` 和 `default.project.yaml` 模板

### 发布
- 构建 PyPI 发布包 (dist/vibe_collab-0.4.3.tar.gz, vibe_collab-0.4.3-py3-none-any.whl)
- 待上传到 PyPI

---

## v0.4.2 (2026-01-21)

### 新功能
- **协议自检机制**: 
  - 协议检查器模块 (`protocol_checker.py`)，检查 Git 协议、文档更新、对话流程协议
  - CLI 命令 `vibecollab check` 执行协议检查，支持严格模式
  - 在 CONTRIBUTING_AI.md 中添加协议自检章节（第十章节）
  - 支持对话中通过触发词触发自检（"检查协议"、"协议自检"等）
- **PRD 文档管理**: 
  - PRD 管理器模块 (`prd_manager.py`)，支持需求的创建、更新、状态管理
  - 需求变化历史跟踪
  - 项目初始化时自动创建 PRD.md 模板
  - 在 CONTRIBUTING_AI.md 中添加 PRD 管理章节（第十一章节）
  - 支持对话中通过触发词管理 PRD（"记录需求"、"更新 PRD"等）

### 改进
- 更新项目配置模板，添加 `protocol_check` 和 `prd_management` 配置项
- 在文档列表中添加 PRD.md
- 完善快速参考章节，添加协议自检触发词

### 文档
- 创建 PRD.md 记录项目需求（REQ-001: 协议自检机制, REQ-002: PRD 文档管理）

---

## v0.4.1 (2026-01-21)

### 改进
- **阶段定义优化**: 
  - Production 阶段添加"完善发布平台标准"原则
  - Commercial 阶段添加"插件化增量开发"和"数据热更"重点
- **阶段化规则设计优化**: CONTRIBUTING_AI.md 中的阶段规则改为类型定义和模板，具体当前阶段信息移至 ROADMAP.md

---

## v0.4.0 (2026-01-21)

### 新功能
- **Git 检查和初始化**: 项目初始化时自动检查 Git，可选自动初始化仓库
- **项目生涯管理**: 4个阶段（demo/production/commercial/stable）的完整管理系统
- **阶段化协作规则**: CONTRIBUTING_AI.md 中包含所有阶段的规则，标注当前激活阶段
- **ROADMAP 集成**: 在 ROADMAP.md 中显示项目生涯阶段信息
- **生涯管理命令**: `vibecollab lifecycle check` 和 `upgrade` 命令

### 改进
- 将生涯阶段信息放在 ROADMAP.md（PM 侧重的文档）
- Demo 阶段早期介入 CI/CD
- Production 阶段前确立性能规范和代码重构
- 完善文档体系（DECISIONS.md, ROADMAP.md, QA_TEST_CASES.md）

### 重构
- 全局替换 llm.txt 为 CONTRIBUTING_AI.md
- 更新所有代码、文档、模板引用

---

## v0.3.0 (2026-01-20)

### 新功能
- **llms.txt 标准集成**: 自动检测并更新 llms.txt，添加 AI Collaboration 章节
- **llmstxt.py 模块**: 管理 llms.txt 的创建和更新

### 重构
- 重命名包为 `vibe-collab`
- 重命名仓库为 `VibeCollab`

---

## v0.2.0 (2026-01-20)

### 新功能
- **需求澄清协议**: 将用户模糊需求自动转化为结构化描述
- **upgrade 命令**: `llmcontext upgrade` 无缝升级协议到最新版本，保留用户配置
- **Git 初始化约束**: 协议层强制新项目初始化 Git 仓库
- **使用流程图**: README 添加完整工作流程图

### 改进
- README 补充完整章节列表、Cursor Skill 说明
- SKILL.md 同步所有协议更新
- project_template.yaml 新增需求澄清、快速验收、构建配置

---

## v0.1.1 (2026-01-20)

### 对话10: 需求澄清协议 [FEAT]

**generator.py**:
- 新增 `_add_requirement_clarification()` 方法
- 将用户模糊需求转化为结构化描述

**结构化需求模板**:
- 原始描述 → 需求分析（目标/场景/用户）
- 功能要求 → 验收标准
- 待确认项 → 决策等级

---

### 对话9: CONTRIBUTING_AI.md 自更新 + README 更新 [VIBE] [DOC]

- 新增 `project.yaml` - 项目自身配置
- `CONTRIBUTING_AI.md` 使用生成器自更新，包含全部章节
- README 补充完整章节列表、Cursor Skill 说明

---

### 对话8: 补充遗漏章节 [FEAT]

**generator.py 新增方法**:
- `_add_iteration_protocols()` - 迭代建议管理、版本回顾、构建打包、配置级迭代
- `_add_qa_protocol()` - QA 验收协议、快速验收模板
- `_add_prompt_engineering()` - Prompt 工程最佳实践
- `_add_decisions_summary()` - 已确认决策汇总
- `_add_changelog()` - 文档迭代日志
- `_add_git_history_reference()` - Git 历史参考

---

### 对话7: 封装 Cursor Skill [FEAT]

- 创建 `.cursor/skills/llmcontext/SKILL.md`
- 添加 references/project_template.yaml
- 添加 assets/CONTEXT_TEMPLATE.md、CHANGELOG_TEMPLATE.md
- 打包为 llmcontext-skill.zip

---

### 对话6: 清理重复模板 [REFACTOR]

- 删除根目录 `templates/`（保留包内）
- 更新 pyproject.toml 构建配置

---

### 对话5: 实现扩展钩子处理 [DEV]

- 新增 `extension.py`: 钩子管理、条件评估、上下文解析
- 支持 reference/template/file_list/computed 四种上下文
- 集成到 generator.py 生成扩展章节
- 新增 13 个扩展机制单元测试

---

## 对话记录

### 对话16: 修复 Windows 编码问题 (2026-02-10) [FIX]

**问题**:
- `vibecollab check` 命令在 Windows GBK 环境下因 emoji 字符崩溃
- UnicodeEncodeError: 'gbk' codec can't encode character

**解决方案**:
- 实现 `is_windows_gbk()` 平台检测函数
- 添加 emoji 和特殊字符映射表：
  - ✅ → OK, ❌ → X, ⚠️ → !, ℹ️ → i
  - • → -, 🔒 → [保留]
- 修改所有 CLI 输出使用 EMOJI_MAP 和 BULLET

**修改文件**:
- `src/vibecollab/cli.py`: 添加平台检测和字符替代（+80 行）
- `src/vibecollab/cli_lifecycle.py`: 同步修改生涯管理命令（+36 行）

**测试结果**:
- ✅ `vibecollab check` 在 Windows GBK 下正常运行
- ✅ 显示格式良好，易读性未受影响

**技术债务**:
- ✅ **已解决**: Windows 控制台编码问题（高优先级）

### 对话15: 协议自检执行 (2026-02-10) [VIBE]

**检查结果**:
- ✅ Git 仓库正常
- ⚠️ CHANGELOG.md 19天未更新
- ⚠️ CONTEXT.md 2天未更新
- 总计 3 项检查：0 错误，2 警告，1 信息

**发现问题**:
- Windows 控制台编码问题：`vibecollab check` 因 emoji 字符导致 GBK 编码错误
- 临时方案：直接调用 Python `ProtocolChecker` 模块

**产出**:
- 更新 CONTEXT.md 记录对话15
- 补充 CHANGELOG.md 缺失的记录（对话14、v0.4.3）
- 将 Windows 编码问题记录到技术债务

### 对话14: 完善关键文件职责配置 (2026-02-09) [CONFIG]

**背景**:
- 从 GitHub 拉取最新代码
- 发现 documentation.key_files 配置不完整

**改进**:
- 补充 4 个关键文件配置：llms.txt, DECISIONS.md, QA_TEST_CASES.md, ROADMAP.md
- 同步更新 project.yaml 和 templates/default.project.yaml

**发布**:
- 版本升级到 v0.4.3
- 构建发布包：`python -m build`

---

## 历史版本

### 对话1-4: 项目初始化到文档同步

- 项目初始化、CLI 实现
- Schema 设计、生成器核心逻辑
- 领域模板创建
