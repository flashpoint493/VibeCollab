# VibeCollab Changelog

## v0.10.1-dev (2026-03-03) - Code Internationalization (i18n)

### Documentation English Translation (v0.10.2)
- **All 10 docs/ files translated** from Chinese to English (~4000+ lines, ~6400 line changes)
  - CHANGELOG.md, DECISIONS.md, ROADMAP.md, PRD.md, QA_TEST_CASES.md
  - LIFECYCLE_DESIGN.md, TEST_VALIDATION.md, developers/COLLABORATION.md
  - developers/alice/CONTEXT.md, developers/ocarina/CONTEXT.md
- **All 3 schema/ files translated** (project.schema.yaml, insight.schema.yaml, extension.schema.yaml)
- **README version sync**: Both README.md and README.zh-CN.md updated with v0.9.6/v0.9.7 entries, footer version corrected to v0.9.7
- Translation principles: technical terms/code/YAML/version numbers preserved exactly, Markdown structure maintained

### Version Unification + Pipeline Module + Task Lifecycle
- **Version unification**: Hatchling dynamic versioning via `pyproject.toml` → `__init__.py` as single source of truth
- **Pipeline module** (`src/vibecollab/core/pipeline.py`): SchemaValidator, ActionRegistry, DocSyncChecker, Pipeline orchestrator (~310 lines)
- **Task lifecycle hooks**: `on_complete()`, `on_transition()` callbacks in TaskManager, completion action hints in CLI

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
- **Directory restructure**: 36 flat `.py` modules reorganized into 7 functional sub-packages
  - `cli/` (11 files): main, ai, guide, config, lifecycle, insight, task, roadmap, mcp, index
  - `core/` (8 files): generator, project, templates, pattern_engine, extension, health, protocol_checker
  - `domain/` (8 files): task_manager, event_log, developer, lifecycle, roadmap_parser, conflict_detector, prd_manager, session_store
  - `insight/` (3 files): manager, signal
  - `search/` (3 files): embedder, indexer, vector_store
  - `agent/` (3 files): llm_client, agent_executor, mcp_server
  - `utils/` (2 files): git, llmstxt
  - Phase 1: File migration + internal import updates + thin proxies for backward compatibility
  - Phase 2: 35 test files import path migration + 12 mock/patch path fixes + 35 thin proxies removed
  - `__init__.py` public API exports updated from old paths to new sub-package paths
  - `pyproject.toml` entry_point `vibecollab.cli:main` unchanged (cli package `__init__.py` exports main)

### Bug Fix
- **GBK encoding comprehensive fix**: 3-layer defense system eliminates all Windows GBK terminal `UnicodeEncodeError`
  - **Layer 1** `ensure_safe_stdout()`: At CLI startup, reconfigure `sys.stdout`/`sys.stderr` errors mode from strict/surrogateescape to replace — unencodable characters become `?` instead of crashing
  - **Layer 2** `safe_console()`: Rich Console factory function ensures stdout is safe before Console creation; 6 CLI modules unified from `Console()` to `safe_console()`
  - **Layer 3** EMOJI mapping expansion: Added 9 new mappings: `check`/`cross`/`arrow`/`bar_fill`/`bar_empty`/`high`/`medium`/`low`/`idea`
  - Fixed `cli/roadmap.py` hardcoded `█░↔→←☑☐` characters
  - Fixed `cli/guide.py` hardcoded `✓✗` characters
  - Fixed `core/project.py` hardcoded `✅⏳` characters
  - Fixed `domain/developer.py` hardcoded `✅⚠️` characters
  - Eliminated duplicate `is_windows_gbk()` in `domain/conflict_detector.py`, unified to `_compat`
  - Key fix: `surrogateescape` error mode still crashes under GBK encoding; `ensure_safe_stdout()` detects encoding capability rather than error mode to determine if reconfigure is needed

### Improvement
- **Strict `###` milestone format**: `MILESTONE_HEADER_RE` regex now only accepts `### vX.Y.Z` level-3 headings
- **Zero milestone format hint**: `roadmap status/parse/sync` outputs `MILESTONE_FORMAT_HINT` when no milestones found
- **init template compatibility**: `vibecollab init` generated ROADMAP.md uses `### v0.1.0` format

### Test
- Full **1344 passed**, zero regression
- E2E verified **all 36 CLI scenarios passed**
- Fixed `test_cli_ai.py` mock path (`Console` -> `console` instance)
- Fixed `test_conflict_detector.py` mock path (`conflict_detector.platform` -> `_compat.platform`)

## v0.9.6 (2026-02-28) - PyPI Adaptation + Documentation Quality

### Improvement
- **PyPI README separation** (`README.pypi.md`): New PyPI-specific README
  - Mermaid diagrams replaced with ASCII text flowcharts (PyPI doesn't support Mermaid rendering)
  - All relative links converted to GitHub absolute URLs (PyPI can't resolve relative paths)
  - `pyproject.toml` `readme` field points to `README.pypi.md` (GitHub README unchanged)
- **CONTEXT.md stale task cleanup**: TASK-DEV-005 (alice) marked complete, removed legacy status
- **README.md update**: CLI Reference added `vibecollab roadmap` command group, Version History added v0.9.4/v0.9.5

### Task
- TASK-DEV-006: PyPI README adaptation (README.pypi.md, remove Mermaid + absolute URLs) ✅
- TASK-DEV-007: CONTEXT.md stale task cleanup + v0.9.6 update ✅

## v0.9.5 (2026-02-28) - ROADMAP ↔ Task Integration

### New Feature
- **RoadmapParser module** (`roadmap_parser.py`): ROADMAP.md ↔ TaskManager bidirectional integration
  - Parse ROADMAP.md to extract milestones (`### vX.Y.Z - Title` format) and checklist items
  - Extract `TASK-{ROLE}-{SEQ}` ID references from checklist lines (deterministic regex matching, not vectorized)
  - **Bidirectional sync**: ROADMAP `[x]` → Task DONE / Task DONE → ROADMAP `[x]`
  - Three sync directions: `both` (default) / `roadmap_to_tasks` / `tasks_to_roadmap`
  - Dry-run preview mode
  - Per-milestone progress aggregation (total/done/progress_pct/task_breakdown)
  - Orphan Task detection (Tasks not linked to any ROADMAP item)
- **Task `milestone` field** (`task_manager.py`): Task dataclass new `milestone: str` attribute
  - `from_dict` / `to_dict` full serialization support, backward compatible with old data
  - `list_tasks()` new `--milestone` filter parameter
- **CLI `vibecollab roadmap` command group** (`cli_roadmap.py`):
  - `vibecollab roadmap status [--json]` — Per-milestone progress overview (progress bar + Task status distribution)
  - `vibecollab roadmap sync [-d both] [--dry-run] [--json]` — Bidirectional sync
  - `vibecollab roadmap parse [--json]` — Parse ROADMAP structure
- **CLI `vibecollab task` enhancements** (`cli_task.py`):
  - `task create --milestone v0.9.3` — Associate milestone at creation
  - `task list --milestone v0.9.3` — Filter by milestone
  - `task show` displays milestone field
- **MCP Server new Tools** (`mcp_server.py`):
  - `roadmap_status` — AI IDE can view ROADMAP progress
  - `roadmap_sync` — AI IDE can trigger ROADMAP ↔ Task sync

### Test
- Added **40 unit tests** (`test_roadmap_parser.py`)
  - TestRegex (7): Milestone header / Task ID regex
  - TestParse (7): Parse milestones/items/checked/task_ids/progress/edge cases
  - TestStatus (5): Aggregate stats/orphan Tasks/breakdown
  - TestSync (6): Bidirectional sync/dry-run/milestone field assignment
  - TestMilestoneDataclass (3): Data structures
  - TestTaskMilestoneField (6): Task milestone field CRUD/serialization/filtering
  - TestCLI (6): CLI commands CliRunner full coverage
- Full **1331 passed**, coverage **89%**, zero regression

## v0.10.0-dev (2026-02-27) - Coverage Improvement & Stability

### Test
- **cli_index.py coverage 17% → 91%**: New `test_cli_index.py` (12 tests)
  - TestIndexCmd (5): basic/rebuild/auto_backend/with_insights/nonexistent_config
  - TestSearchCmd (7): no_index/basic/type_filter/min_score/top_k/empty_index/no_results
  - Fixed test DB schema missing `source` column
- **mcp_server.py coverage 47% → 100%**: New `test_mcp_server_closures.py` (42 tests)
  - Fake Module injection method to capture create_mcp_server() internal closures
  - TestResources (8): 6 document resources + empty project + missing files
  - TestCliTools (24): 14 CLI tools command construction verification (including optional parameter branches)
  - TestDirectTools (5): developer_context + session_save (success/all fields/exception)
  - TestPrompts (4): start_conversation (basic/developer/empty project/unknown developer)
  - TestRunCliEdge (1) + TestRunServer (1)
- **protocol_checker.py coverage 71% → 96%**: New `test_protocol_checker_git.py` (26 tests)
  - Git consistency checks: commit-level sync / cross-tag release checks
  - Real Git repo tests: `_is_file_tracked_in_git` / `_get_last_commit_time`
  - Document update threshold branches / PRD missing / collaboration doc stale / developer discovery
- **cli_task.py coverage 78% → 98%**: New `test_cli_task_richtext.py` (10 tests)
  - Non-JSON output paths: list/show/suggest rich text formatting
  - `_load_config` unit test + `_get_managers` InsightManager exception branch
- Full **1291 passed**, total coverage **85% → 89%**

### Insight
- INS-016: Fake Module injection method for testing factory function internal closures
- INS-017: Coverage improvement ROI priority ranking strategy

## v0.9.4 (2026-02-27) - Insight Quality & Lifecycle

### New Feature
- **Insight auto-deduplication** (`insight_manager.py`): Automatic duplicate detection on new Insight creation
  - `find_duplicates()`: SHA-256 fingerprint exact match + title Jaccard similarity + tag overlap rate
  - `_content_key()`: Extract title+tags+body to generate content fingerprint
  - `insight add` command integrates dedup detection, blocks creation when duplicates found
  - `--force` flag to skip dedup detection and force creation
  - Similarity threshold configurable
- **Insight relationship graph** (`insight_manager.py`): Visualize derivation/association between Insights
  - `build_graph()`: Build global Insight relationship graph (nodes+edges+stats)
  - `_count_components()`: Union-Find algorithm to compute connected components
  - `to_mermaid()`: Generate Mermaid chart syntax for direct Markdown embedding
  - `vibecollab insight graph`: CLI command, supports `--format text/json/mermaid`
- **Cross-project Insight import/export** (`insight_manager.py`):
  - `export_insights()`: Export Insight Bundle (YAML format), supports full/selective export, optional registry inclusion
  - `import_insights()`: Import Insight Bundle, three conflict strategies (skip/rename/overwrite)
  - Auto-set `source.project` on import to mark source project
  - `vibecollab insight export [--ids] [--output] [--include-registry]`
  - `vibecollab insight import <file> [--strategy skip/rename/overwrite] [--json]`
- **MCP Server new 2 Tools** (`mcp_server.py`):
  - `insight_graph`: Get Insight relationship graph (json/text/mermaid)
  - `insight_export`: Export Insight Bundle

### Test
- 36 new unit tests (`test_insight_quality.py`):
  - TestFindDuplicates (7): empty/fingerprint/title_similarity/tag_similarity/no_dup/threshold/without_body
  - TestBuildGraph (5): empty/edges/isolated/components/node_data
  - TestToMermaid (2): output/empty
  - TestExportInsights (4): all/selected/with_registry/empty
  - TestImportInsights (7): to_empty/skip/rename/overwrite/invalid/source_project/with_registry
  - TestCLIGraph (3): text/json/mermaid
  - TestCLIExportImport (5): stdout/to_file/import/invalid/rename_strategy
  - TestCLIAddDedup (3): detect_duplicate/force_bypass/no_duplicate
- Full 1201 passed, zero regression

## v0.9.3 (2026-02-27) - Task/EventLog Core Workflow Integration

### New Feature
- **Task CLI three new commands** (`cli_task.py`): Complete TaskManager state management CLI entry points
  - `vibecollab task transition <ID> <STATUS>`: Advance task state (TODO→IN_PROGRESS→REVIEW→DONE)
  - `vibecollab task solidify <ID>`: Solidify task, mark DONE after passing validation gates
  - `vibecollab task rollback <ID>`: Roll back task to previous state
  - All commands support `--json` output and `--reason` parameter
- **onboard injects Task/EventLog** (`cli_guide.py`):
  - Active Task overview: Shows TODO/IN_PROGRESS/REVIEW task list and statistics
  - Recent EventLog event summary: Shows last 5 audit events
  - JSON output includes `task_summary` / `active_tasks` / `recent_events`
- **next recommends based on Tasks** (`cli_guide.py`):
  - REVIEW status tasks auto-recommend solidify action (P1 priority)
  - Dependency-blocked tasks hint (P2 priority)
  - TODO backlog hint (>3 pending triggers, P2 priority)
- **MCP Server new 2 Tools** (`mcp_server.py`):
  - `task_create`: AI IDE can directly create tasks (auto-link Insights)
  - `task_transition`: AI IDE can advance task state
  - `start_conversation` prompt tool list updated from 10 to 12
- **DECISION-016**: v0.9.3 prioritize Task/EventLog core workflow integration (S-level direction decision)

### Test
- 30 new unit tests (`test_task_workflow_integration.py`):
  - TestTransitionCommand (5): success / with_reason / illegal / not_found / json_output
  - TestSolidifyCommand (4): success / not_in_review / not_found / json_output
  - TestRollbackCommand (5): success / with_reason / from_todo / not_found / json_output
  - TestFullLifecycle (2): complete_lifecycle / rollback_and_retry
  - TestOnboardInjection (5): tasks_json / tasks_rich / no_tasks / events_json / events_rich
  - TestNextTaskRecommendations (2): with_review_tasks / no_tasks
  - TestMcpNewTools (3): task_create_tool / task_transition_tool / start_conversation_lists
  - TestCollectProjectContext (4): includes_tasks / includes_events / no_tasks / no_events
- Full 1164 passed, 1 skipped, zero regression

## v0.9.2 (2026-02-27) - Insight Solidification Signal Enhancement

### New Feature
- **Insight Signal Collector** (`src/vibecollab/insight_signal.py`): Structured signal-driven Insight candidate recommendation
  - `InsightSignalCollector`: Extract candidate Insights from git incremental commits, document change diffs, and Task changes
  - `SignalSnapshot`: Signal snapshot management, tracks last solidification timestamp and commit hash
  - `InsightCandidate`: Candidate Insight data structure (with confidence, source_signal)
  - 4 signal analysis strategies: git_feature / git_bugfix / git_refactor / git_large_change
  - 3 document signals: doc_decisions (0.8) / doc_roadmap (0.6) / doc_context (0.4)
  - Task completion signal: batch Task closure detection
  - Candidate deduplication: title Jaccard similarity > 0.6 auto-deduplicate
- **Session Store** (`src/vibecollab/session_store.py`): Conversation summary persistent storage
  - `SessionStore`: `.vibecollab/sessions/` directory management
  - `Session`: Conversation record data structure (summary / key_decisions / files_changed / tags)
  - CRUD: save / get / list_all / list_recent / list_since / delete / count
  - `get_summaries_text()`: Get recent session summary text for insight suggest
- **CLI `insight suggest`** (`cli_insight.py`): Interactive/automatic candidate recommendation command
  - `--json`: JSON output mode
  - `--auto-confirm`: Non-interactive mode auto-creates all candidates
  - Interactive mode supports index selection / all / q to quit
- **MCP Server new 2 Tools**:
  - `insight_suggest`: Signal-based Insight candidate recommendation
  - `session_save`: Save conversation session summary (supports decisions / files / tags)
- **`insight add` snapshot linkage**: Manual Insight creation auto-updates signal snapshot

### Test
- 60 new unit tests:
  - `test_insight_signal.py` (42 tests): SignalSnapshot / InsightCandidate / SnapshotCRUD / GitSignals / DocChanges / TaskChanges / Analysis / Suggest / Helpers
  - `test_session_store.py` (18 tests): Session / SessionStore CRUD / list / count / summaries
- Full 1134 passed, 1 skipped, zero regression

## v0.9.1 (2026-02-27) - MCP Server + AI IDE Integration

### New Feature
- **MCP Server** (`vibecollab mcp serve`): Standard Model Context Protocol Server implementation
  - 6 Resources: `contributing_ai`, `context`, `decisions`, `roadmap`, `changelog`, `insights/list`
  - 8 Tools: `insight_search`, `insight_add`, `check`, `onboard`, `next_step`, `task_list`, `project_prompt`, `developer_context`, `search_docs`
  - 1 Prompt: `start_conversation` (project info + CONTEXT summary + developer context)
  - Supports `stdio` / `sse` two transport modes
  - Optional dependency `pip install vibe-collab[mcp]`
- **MCP CLI command group** (`vibecollab mcp`):
  - `mcp serve` — Start MCP Server
  - `mcp config --ide cursor/cline/codebuddy` — Output IDE configuration content
  - `mcp inject --ide all` — Auto-inject config into IDE config files (merge existing)
- **CodeBuddy Rule**: `.codebuddy/rules/vibecollab-protocol.mdc` always rule, takes effect on project clone

### Decision
- **DECISION-015**: Cut v0.9.2 bootstrap + v0.10.1 Agent enhancement (S-level)
  - `bootstrap` insufficient value, `vibecollab ai` remains experimental frozen
  - Version chain simplified: v0.9.0(semantic search) → v0.9.1(MCP) → v0.9.2(signal-driven solidification) → v0.9.3(Insight lifecycle) → v0.10.0(release)

### Insight
- INS-013: Version planning should decisively cut low-value milestones
- INS-014: When features overlap, first check if external alternatives exist
- INS-015: Insight solidification needs structured signals, not pure LLM reasoning

### Test
- 35 MCP Server unit tests (34 passed, 1 skipped)
- Full 1074 passed, zero regression

## v0.8.0-dev (In Development) - Config Management System

### Architecture
- **Three-layer config architecture**: `Environment variables > ~/.vibecollab/config.yaml > Built-in defaults`
- Config file stored in user home directory (`~/.vibecollab/config.yaml`), not in git
- Lightweight .env parsing: self-implemented `parse_dotenv()`, extracts only `VIBECOLLAB_*` prefix variables
- **v0.9.0 Semantic Search Engine**:
  - `Embedder` module — Lightweight embedding abstraction layer, supports OpenAI / sentence-transformers / pure_python three backends
  - `VectorStore` module — SQLite persistent vector storage, pure Python cosine similarity
  - `Indexer` module — Project document + Insight YAML indexer (Markdown chunk splitting)
  - `vibecollab index` command — Incremental/rebuild indexing
  - `vibecollab search` command — Global semantic search
  - `vibecollab insight search --semantic` — Insight semantic search mode
  - Zero external dependency fallback: pure_python trigram hash embedding
  - Optional `pip install vibe-collab[embedding]` for sentence-transformers
  - `onboard` semantic enhancement — Extract task description from CONTEXT.md/developer context → vector search Top-N related Insights
    - Rich panel "Task-related Insights (semantic match)" + JSON `related_insights` field
    - Developer context prioritized over global CONTEXT.md as query text
    - 11 new unit tests (_search_related_insights + onboard integration)

### Decision
- **`vibecollab ai` command group marked experimental**: VibeCollab core positioning is protocol management tool, LLM communication and Tool Use delegated to Cline/Cursor/Aider etc. `ai ask/chat/agent` retained as lightweight alternative but no longer a primary development direction. Affected modules: `cli_ai.py`, `llm_client.py`, `agent_executor.py`, `config_manager.py` (all cleanly isolated, core features zero dependency)

### Refactor
- **Unified Windows GBK encoding compatibility layer** (`_compat.py`): Extract `is_windows_gbk()` / `EMOJI` / `BULLET` to shared module
  - Eliminated 4 duplicate definitions (cli.py / cli_ai.py / cli_lifecycle.py / cli_config.py)
  - Added missing GBK compatibility for cli_guide.py / cli_insight.py
  - Fixed 7 hardcoded emoji (📦 ⏳ ● •), preventing Windows GBK terminal UnicodeEncodeError
  - Unified cli_insight.py `sys.exit(1)` → `raise SystemExit(1)` (9 locations)
  - Removed no longer needed `import platform` / `import sys`
- **cli_insight.py `_load_insight_manager()` error handling**: Check `.vibecollab/` directory existence, provide friendly hints
- **Ruff lint full fix**: 68 errors → 0 (61 auto-fix + 7 manual fixes: E402 import position, F841 unused variable, F401 unused import, I001 import sorting, F541 empty f-string)

### New Feature
- **`vibecollab prompt` command**: Generate LLM-ready context prompt text
  - Auto-extract core protocol sections from CONTRIBUTING_AI.md (decision levels/dialogue flow/role definitions/Git conventions)
  - Inject current project state (CONTEXT.md / recent decisions / roadmap TODO / uncommitted changes)
  - Inject Insight experience summary + Insight workflow instructions
  - `--compact` minimal mode (protocol core + status only, omits roadmap and role definitions)
  - `--sections protocol,context,insight` selective injection
  - `--copy` directly copy to clipboard (Windows clip support)
  - `-d <developer>` include developer personal context
  - Replaces manually copying CONTRIBUTING_AI.md to LLM dialogue windows
- **`_collect_project_context()` shared function**: Extract data collection logic from `onboard`, reused by both `onboard` and `prompt`
- **`_extract_md_sections()` utility function**: Extract specific sections from Markdown by heading
- **`_build_prompt_text()` formatter**: Build pure Markdown format LLM prompt
- **Insight experience solidification workflow** (IDE dialogue mode integration):
  - Added `27_insight_workflow.md.j2` template section — Defines when/how to solidify experience
  - Dialogue end flow adds "experience solidification check" step (`06_dialogue_protocol.md.j2` updated)
  - `vibecollab next` command adds Insight solidification hints (auto-detection based on 5 signal types)
  - manifest.yaml registers `insight_workflow` section (enabled by default, disable via `insight.enabled: false`)
- **`vibecollab config setup`**: Interactive LLM configuration wizard
  - Provider selection (OpenAI / Anthropic)
  - API Key secure input (hidden input)
  - Base URL presets (OpenAI official / OpenRouter / DeepSeek / Alibaba Cloud Bailian / custom)
  - Optional model name setting
- **`vibecollab config show`**: View current config (three-layer merged result + source identification)
- **`vibecollab config set <key> <value>`**: Set individual config item
- **`vibecollab config path`**: Show config file path
- **`resolve_llm_config()`**: Unified three-layer config resolution function
- **`LLMConfig.__post_init__`**: Changed to three-layer priority (explicit params > env vars > config file > defaults)
- **Improved error messages**: `_ensure_llm_configured()` provides three configuration method guidance
- **`vibecollab check` key_files staleness check**: Supports `max_stale_days` config
  - `documentation.key_files` new optional `max_stale_days` field
  - File exists but exceeds configured days without update → report warning with `update_trigger` hint
  - `QA_TEST_CASES.md` configured with 7-day threshold, `ROADMAP.md` configured with 14-day threshold
  - 3 unit tests covering (triggered/not triggered/unconfigured)

### Bug Fix
- **CI/CD fix**: 
  - `__init__.py` version `0.5.9` → `0.8.0.dev0` (synced with pyproject.toml)
  - Python matrix `3.8-3.12` updated to `3.9-3.13` (3.8 EOL, `actions/setup-python@v5` unsupported)
  - `requires-python` from `>=3.8` to `>=3.9`
  - classifiers removed 3.8, added 3.13
- **Fixed OpenAI empty choices IndexError**: `_call_openai()` `data.get("choices", [{}])[0]` crashes when API returns empty `choices: []`, changed to safe retrieval
- **Fixed flaky test `test_onboard_basic`**: Windows `test_serve_lock_conflict` `SystemExit(1)` causes `subprocess.run` internal thread residual `KeyboardInterrupt`, contaminating subsequent `onboard` command's `_get_git_uncommitted()` call
  - Root cause: `KeyboardInterrupt` inherits from `BaseException` not `Exception`, original `except Exception` can't catch it
  - Fix: `cli_guide.py` `_get_git_uncommitted()` and `_get_git_diff_files()` exception handling changed from `except Exception` to `except BaseException`
  - Verified: Two consecutive full runs 779/779 passed
- **Fixed flaky test `test_whoami_basic`**: `developer.py` `_get_git_username()` similarly affected by `KeyboardInterrupt` residual
  - Fix: `except Exception` → `except BaseException`
  - Verified: Full 809/809 passed
- **Systematic fix for all subprocess-related `except Exception`**: Audited and batch-fixed 9 subprocess call exception handlers
  - `protocol_checker.py`: 5 git command calls
  - `git_utils.py`: 2 git init/status calls
  - `agent_executor.py`: 2 test execution/git commit calls
  - Unified from `except Exception` to `except BaseException`, preventing `KeyboardInterrupt` residual causing flaky tests

### Testing
- **Agent mode E2E tests**: 35 new tests covering agent_executor + cli_ai high-priority gaps
  - `test_agent_executor.py` (+21 tests): git_commit real git repo (success/no changes/no repo), run_tests timeout/exception/custom command, apply_changes write fail/delete nonexistent, validate invalid path, rollback fail/empty, full_cycle git fail/real git, parse_single_change edge input
  - `test_cli_ai.py` (+14 tests): serve circuit breaker trigger, adaptive backoff, memory threshold stop, pending-solidify wait, _execute_agent_cycle 5 branches (plan fail/exec fail/no changes/exception/success), run valid changes/plan fail, ask/chat/plan exception paths, status stale lock/invalid lock
  - Full 844/844 passed (two consecutive stable runs)
- **LLM Client mock integration tests**: 26 new tests covering dual provider + config file layer + edge cases
  - `test_llm_client.py` (+26 tests): Config file three-layer resolution (file fallback/env override/explicit override/exception degradation), OpenAI+Anthropic dual provider deep (URL concatenation/header verification/unknown provider degradation/empty choices/multi system messages/multi content blocks), build_project_context edge (tasks corrupted/events corrupted/empty files/all DONE), ask() paths (dual params/temperature/default construction)
  - Discovered and fixed OpenAI empty choices IndexError bug
  - Full 868/868 passed (two consecutive stable runs)
- **Agent stability stress tests**: 13 new tests covering long-running/concurrent/rollback/backoff
  - `test_agent_executor.py` (+13 tests): 100-cycle continuous apply, alternating success/failure cycles, multi-instance file operation isolation, PID lock acquire/release/stale takeover/active rejection, adaptive backoff max cap/success reset, rollback recovery/remove new files/multi-file rollback/invalid output/protected files
- **Insight system generality tests**: 20 new tests covering large-scale/decay/association/cycle protection
  - `test_insight_manager.py` (+20 tests): 100 Insights create/search/list/decay, multi-tag search, 10-level trace chain, 50-round decay convergence, decay+reward steady state, batch record_use growth, weight precision verification, deactivate→activate→re-decay, threshold boundary, Chinese tags, case-insensitive, partial overlap, empty tags, circular reference protection
  - Full 899/899 passed
- **Minimal/complex project boundary tests**: 15 new tests covering init+generate+check+health+validate
  - `TestMinimalProject` (7 tests): Minimal params init, minimal generate, minimal check/health/validate, empty YAML, project_name only
  - `TestComplexProject` (8 tests): Full config (multi-developer+lifecycle+documentation) generate/check/health/upgrade/validate/JSON output, all domain init
  - Full 914/914 passed
- **Insight workflow + next command tests**: 16 new tests covering Insight solidification hints + template rendering
  - `TestCheckInsightOpportunity` (11 tests): no changes/single file/multi-type+tests/tests only/config changes/large changes/first solidification/existing Insight/YAML extension/combined signals
  - `TestInsightWorkflowTemplate` (5 tests): manifest registration/default rendering/disabled/position/dialogue protocol integration
  - Full 929/929 passed
- **CLI E2E test full coverage**: 12 missing tests among 48 CLI commands all supplemented
  - `tests/test_cli_dev.py` (17 tests): dev command group 7 subcommands (whoami/list/status/sync/init/switch/conflicts)
  - `tests/test_cli.py` (+10 tests): Top-level commands (templates/export-template/version-info/check/health)
  - Full 809/809 passed
- **Test coverage 76% → 81%**: 128 new tests covering 6 low-coverage modules
  - `test_llmstxt.py` (17 tests): 68% → 97%
  - `test_templates.py` (13 tests): 60% → 91%
  - `test_git_utils.py` (21 tests): 52% → 100%
  - `test_lifecycle.py` (25 tests): 28% → 93%
  - `test_extension.py` (41 tests, rewritten): 64% → 100%
  - `test_cli_lifecycle.py` (11 tests): 23% → 92%
- **38 new unit tests** (`tests/test_config_manager.py`):
  - `TestConfigPaths` (2): Path correctness
  - `TestLoadSaveConfig` (5): File operations
  - `TestGetSetConfigValue` (5): Nested read/write
  - `TestParseDotenv` (8): .env parsing
  - `TestResolveLLMConfig` (7): Three-layer merge
  - `TestLLMConfigWithFile` (4): LLMConfig integration
  - `TestCLIConfig` (7): CLI command end-to-end

---

## v0.7.2 (2026-02-25) - README Comprehensive Update

### Documentation
- **README.md comprehensive rewrite**: Feature descriptions updated from v0.5.x to v0.7.1
  - Feature list reorganized into 5 categories (Knowledge Solidification/Collaboration Engine/Project Management/Multi-Developer/Infrastructure)
  - Workflow diagram added Task-Insight auto-link + Insight solidification + Agent guidance nodes
  - CLI commands added insight (13 subcommands) / task (4 subcommands) / onboard / next
  - Project structure added insight_manager / cli_insight / cli_task / cli_guide / insight.schema
  - Version history updated to v0.7.1
- PyPI project description synced (README.md as long_description)

---

## v0.7.1 (2026-02-25) - Task-Insight Auto-Link

### Architecture
- **DECISION-014 (A-level)**: Task-Insight unidirectional auto-link — Auto-search related Insights on Task creation
- **Zero-config integration**: InsightManager optionally injected, auto-degrades when absent, fully backward compatible

### New Feature
- **Task-Insight auto-link** (`src/vibecollab/task_manager.py`):
  - `TaskManager.__init__` new optional `insight_manager` parameter
  - `_extract_search_tags()`: Extract keywords from feature/description/role, filter stop words
  - `_find_related_insights()`: Jaccard × weight matching, results stored in `task.metadata["related_insights"]`
  - `suggest_insights()`: Recommend related Insights for existing tasks
  - EventLog auto-records `related_insights` in TASK_CREATED events
- **Task CLI commands** (`src/vibecollab/cli_task.py`):
  - `vibecollab task create --id --role --feature [--assignee] [--description] [--json]`
  - `vibecollab task list [--status] [--assignee] [--json]`
  - `vibecollab task show <id> [--json]`
  - `vibecollab task suggest <id> [-n limit] [--json]`

### Testing
- **28 new unit tests** (`tests/test_task_insight_integration.py`):
  - `TestExtractSearchTags` (8 tests): Keyword extraction (English/Chinese/stop words/dedup)
  - `TestInsightAutoLink` (7 tests): Auto-link (match/no match/no IM/score/event/persistence/description enhancement)
  - `TestSuggestInsights` (4 tests): Recommendation (exists/not exists/no IM/limit)
  - `TestBackwardCompatibility` (2 tests): Backward compatibility verification
  - `TestCLI` (7 tests): CLI end-to-end (create/show/list/suggest/invalid/empty/rich)

---

## v0.7.0 (2026-02-25) - Insight Solidification System + Agent Guidance

### Architecture
- **DECISION-012 (S-level)**: Cut Web UI, pivot to Insight solidification system
- **Two-layer separation architecture**: Insight body (portable knowledge package) + Registry (project-level usage state)
- **Tag-driven Developer description**: Open tag system replaces enum fields
- **Self-describing provenance protocol**: origin.context + source.description/url/project, ref demoted to hint
- **Linked document consistency check**: linked_groups three-level check (local_mtime / git_commit / release)
- **Agent guidance system**: onboard (onboarding) + next (action suggestions), evolving from passive diagnostics to proactive guidance

### New Feature
- **`schema/insight.schema.yaml`**: Insight three-part Schema (body + Registry + Developer Tag extension)
- **`src/vibecollab/insight_manager.py`**: Core management module
  - CRUD: create / get / list_all / update / delete
  - Registry: record_use / apply_decay / get_active_insights
  - Search: search_by_tags (Jaccard × weight) / search_by_category
  - Provenance: get_derived_tree (derivation tree)
  - Consistency check: check_consistency (5-item full check)
  - EventLog integration: all operations auto-record audit events
  - SHA-256 content fingerprint for tamper detection
- **Developer metadata extension** (`src/vibecollab/developer.py`):
  - tags / contributed / bookmarks CRUD methods
  - `_read_metadata()` / `_write_metadata()` internal helpers
  - `get_tags()` / `set_tags()` / `add_tag()` / `remove_tag()`
  - `get_contributed()` / `add_contributed()` / `remove_contributed()`
  - `get_bookmarks()` / `add_bookmark()` / `remove_bookmark()`
- **CLI command group** (`src/vibecollab/cli_insight.py` — `vibecollab insight`):
  - `insight list [--active-only] [--json]` — List all insights
  - `insight show <id>` — View insight details
  - `insight add --title --tags --category --scenario --approach [...]` — Create insight
  - `insight search --tags/--category` — Search insights
  - `insight use <id>` — Record usage, reward weight
  - `insight decay [--dry-run]` — Execute weight decay
  - `insight check [--json]` — Consistency check
  - `insight delete <id> [-y]` — Delete insight
  - `insight bookmark <id>` — Bookmark insight
  - `insight unbookmark <id>` — Remove bookmark
  - `insight trace <id> [--json]` — Provenance tree visualization (ASCII tree + JSON)
  - `insight who <id> [--json]` — View cross-developer usage info
  - `insight stats [--json]` — Cross-developer sharing statistics
- **Cross-developer sharing** (`src/vibecollab/insight_manager.py`):
  - `get_full_trace()`: Recursively expand upstream/downstream derivation tree
  - `get_insight_developers()`: Reverse lookup creators/users/bookmarkers/contributors
  - `get_cross_developer_stats()`: Aggregate cross-developer contribution/usage/bookmark statistics
- **Agent guidance commands** (`src/vibecollab/cli_guide.py`):
  - `vibecollab onboard [-d <developer>] [--json]` — AI onboarding guidance (project overview/progress/decisions/TODOs/reading list/developer perspective/key files)
  - `vibecollab next [--json]` — Action suggestions (linked doc sync P0/staleness check P1/commit suggestion P1/missing files P2/self-check P3)
- **Document consistency check enhancement** (`src/vibecollab/protocol_checker.py`):
  - `update_threshold_hours` from 24h → 0.25h (15min), configurable
  - `_check_document_consistency()`: linked_groups document group check
  - `_check_mtime_consistency()`: Local file modification time level check
  - `_check_git_commit_consistency()`: Git commit sync check
  - `_check_release_consistency()`: Version tag sync check
  - `key_files` declared file existence check

### Testing
- **266 new unit tests** (full 566 tests, zero regression):
  - `tests/test_developer.py` (88 tests): developer.py full coverage (including Tag extension)
  - `tests/test_insight_manager.py` (74 tests): insight_manager.py full coverage
  - `tests/test_cli_insight.py` (45 tests): cli_insight.py full coverage
  - `tests/test_protocol_checker.py` (21 tests): protocol_checker.py full coverage (including consistency checks)
  - `tests/test_cli_guide.py` (29 tests): cli_guide.py full coverage (onboard/next/helpers)

### Cleanup
- `.gitignore` added `Reference/` to exclude external reference repos
- Cleaned ROADMAP.md / DECISIONS.md external proprietary term references
- **protocol_checker multi-developer dynamic discovery**: `_check_multi_developer_protocol()` auto-scans developers from `docs/developers/` directory, no static `multi_developer.developers` config needed
- **CONTRIBUTING_AI.md command docs completed**: Added onboard/next/insight(13 subcommands)/health/check --insights to CLI command reference
- **ROADMAP.md synced**: Added v0.7.0 all completed items (consistency check/Agent guidance/tech debt/dynamic discovery)
- **Self-bootstrap full verification**: onboard → next → check → insight full chain working on the project itself

---

## v0.6.0 (2026-02-24) - Protocol Maturity + Test Coverage Enhancement

### Milestone Completion
This release completes all core objectives for the v0.6.0 milestone, marking VibeCollab protocol framework entering mature phase.

### Testing
- **Test coverage increase**: 58% → 68% (+10%)
- **74 new unit tests** (total 359 tests):
  - `test_conflict_detector.py` (38 tests): Conflict detection full coverage
  - `test_prd_manager.py` (36 tests): PRD management full coverage
- **Module coverage**:
  - `conflict_detector.py`: 0% → 99%
  - `prd_manager.py`: 0% → 92%

### Cleanup
- **Removed legacy files**:
  - `project.yaml.broken` (old config backup)
  - `check_protocol.py` (replaced by CLI)
  - `llm_example.txt` (example output file)
  - `test-vibe-project/` (empty test directory)
  - `test-project-1696446371/` (temporary test project)

### v0.6.0 Milestone Summary
- ✅ EventLog append-only audit trail
- ✅ TaskManager validate-solidify-rollback
- ✅ Pattern Engine + Template Overlay
- ✅ Legacy code removal (generator.py 1713→83 lines)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Health Signal Extractor
- ✅ Agent Executor
- ✅ Ruff lint full fix
- ✅ Test coverage increase (58%→68%)

---

## v0.5.9 (2026-02-24) - Pattern Engine + Health Signals + Agent Executor

### New Feature
- **PatternEngine** (`src/vibecollab/pattern_engine.py`):
  - Jinja2 template-driven CONTRIBUTING_AI.md generation engine
  - `manifest.yaml` controls section order, conditions, template mapping
  - 27 `.md.j2` template files replace hardcoded Python methods
  - Condition evaluation supports `|default` syntax (e.g., `config.x.enabled|true`)
  - `DEFAULT_STAGES` built-in stage definition fallback

- **Template Overlay** (local template override mechanism):
  - Projects can create custom templates in `.vibecollab/patterns/`
  - Jinja2 `ChoiceLoader` implements local-first, built-in-fallback template resolution
  - Local `manifest.yaml` support: override sections, insert new sections (`after` positioning), exclude sections (`exclude` list)
  - `list_patterns()` annotates `source: "local" | "builtin"`

- **Health Signal Extractor** (`src/vibecollab/health.py`):
  - Extract project health signals from ProtocolChecker + EventLog + TaskManager
  - Three-level signals: CRITICAL / WARNING / INFO
  - 10+ signal types: protocol compliance, log integrity, activity, conflicts, validation failure rate, task progress, backlog, review bottleneck, dependency blocking, load balancing
  - Scoring system: 0-100 score + A/B/C/D/F grade
  - CLI command `vibecollab health` (supports `--json` JSON output)

- **Agent Executor** (`src/vibecollab/agent_executor.py`):
  - Transform LLM plans into actual file changes (parse JSON → write files → run tests → git commit)
  - Safety measures: path traversal detection, protected file list, file size limits, max files per change
  - Auto-rollback on test failure (backup/restore mechanism)
  - `agent run` and `agent serve` now execute changes instead of just printing

### Refactor
- **Legacy code removal**: `generator.py` from 1713 lines down to 83 lines

### CI/CD
- **GitHub Actions** (`.github/workflows/ci.yml`):
  - Matrix testing: Python 3.8-3.12 × Ubuntu + Windows
  - Ruff lint + pytest + coverage
  - Build verification + artifact upload + Codecov integration

### Code Quality
- **Ruff lint full fix**: 908 auto-fixable errors fixed

### Architecture
- DECISION-011: Pattern Engine architecture (manifest-driven + template overlay + legacy removal)

### Testing
- 285 tests total (70 new):
  - 40 PatternEngine tests (including 8 Template Overlay)
  - 32 Health Signal tests
  - 38 Agent Executor tests
- Full zero regression

---

## v0.5.8 (2026-02-24) - AI CLI Command Layer (Three-Mode Architecture)

### New Feature
- **AI CLI commands** (`src/vibecollab/cli_ai.py`):
  - `vibecollab ai ask "question"` — Single-turn AI question with auto project context injection
  - `vibecollab ai chat` — Multi-turn dialogue mode, supports exit/quit/bye
  - `vibecollab ai agent plan` — Read-only analysis, generates action plan without execution
  - `vibecollab ai agent run` — Single Plan→Execute→Solidify cycle
  - `vibecollab ai agent serve -n 50` — Long-running Agent service (server deployment)
  - `vibecollab ai agent status` — View Agent running status

### Safety Gates
- **PID singleton lock**: Prevents multiple agent instances running simultaneously
- **pending-solidify gate**: REVIEW status tasks not solidified blocks new cycles
- **Max cycle count**: Default 50, configurable via `VIBECOLLAB_AGENT_MAX_CYCLES`
- **Adaptive sleep + exponential backoff**: Failed/too-fast cycles auto-backoff (2s→300s)
- **Fix-loop circuit breaker**: 3 consecutive failures → long wait then reset
- **RSS memory threshold**: Default 500MB, auto-stop when exceeded

### Architecture
- Three-mode coexistence: IDE dialogue / CLI human-machine interaction / Agent autonomous
- DECISION-010: Three-mode architecture decision record

### Testing
- 32 new unit tests (full coverage: config/PID lock/solidify gate/ask/chat/plan/run/serve/status)
- Full 174 tests, zero regression

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

## v0.5.4 (2026-02-24) - CLI Developer Switch

### New Feature
- **CLI developer switch** (`vibecollab dev switch`):
  - Switch current developer identity via CLI without modifying Git config or environment variables
  - `vibecollab dev switch alice` - Switch directly to specified developer
  - `vibecollab dev switch` - Interactive developer selection
  - `vibecollab dev switch --clear` - Clear switch setting, restore default identification strategy
  - Switch state persisted to `.vibecollab.local.yaml` (added to .gitignore)

### Improvement
- **`vibecollab dev whoami` enhancement**:
  - Shows identity source (CLI switch / environment variable / Git username / system username)
  - Clearer display of current developer identification method

### Technical Implementation
- `DeveloperManager` new methods:
  - `switch_developer(developer)` - Switch developer and persist
  - `clear_switch()` - Clear switch setting
  - `get_identity_source()` - Get identity source
  - `_get_local_developer()` - Read developer from local config
- Identity recognition priority: local config > environment variable > primary strategy > fallback strategy

### Documentation Update
- CONTRIBUTING_AI.md updated CLI command reference, added switch command description
- alice's CONTEXT.md updated work direction

---

## v0.5.1 (2026-02-10) - Cross-Developer Conflict Detection

### Major Feature
- **Cross-developer conflict detection** (v0.5.1):
  - Auto-detect work conflicts between multiple developers
  - Supports file conflict, task conflict, dependency conflict, naming conflict detection
  - Provides detailed conflict reports and resolution suggestions

### New Module
- `src/vibecollab/conflict_detector.py`:
  - `ConflictDetector`: Cross-developer conflict detector
  - `Conflict`: Conflict object representation
  - Supports file conflicts, task overlaps, circular dependencies, naming conflicts

### CLI Command Extension
- Added `vibecollab dev conflicts` command:
  - Detect conflicts between current developer and others
  - `--verbose`: Show detailed conflict information
  - `--between alice bob`: Detect conflicts between two specific developers
  - Auto-identify high/medium/low priority conflicts

### Documentation
- **CONTRIBUTING_AI.md new section**: 
  - "Multi-Developer/Agent Collaboration Protocol" complete section
  - Collaboration mode overview, directory structure, identity recognition
  - Context management, collaboration documents, dialogue flow adaptation
  - Conflict detection and prevention, CLI command reference, best practices
- **README.md update**:
  - Added multi-developer mode initialization examples
  - Shows single/multi-developer directory structure comparison
  - Added multi-developer related CLI command documentation

### Conflict Detection Algorithms
- File conflicts: Detect multiple developers modifying same files simultaneously
- Task conflicts: Similarity algorithm detects duplicate/overlapping tasks
- Dependency conflicts: DFS detects circular dependencies
- Naming conflicts: Detect class/function name duplicates in code blocks

### Backward Compatibility
- All v0.5.0 features unchanged
- Conflict detection is additive, does not affect existing usage

### Bug Fix
- **Enabled multi-developer mode on this project** (conversation 19):
  - project.yaml added multi_developer config (enabled: true)
  - Regenerated CONTRIBUTING_AI.md with complete multi-developer section
  - Practicing self-advocated collaboration features
- **upgrade command supports multi_developer config preservation**:
  - Fixed upgrade not preserving user multi_developer config
  - Added Tuple type import fixing NameError
  - Ensures old projects upgrading to v0.5.1 include multi-developer config (default disabled)

---

## v0.5.0 (2026-02-10) - Multi-Developer Support

### Major Feature
- **Multi-developer collaboration support** (DECISION-008):
  - Support multiple developers / multiple AI Agents collaborating on same project
  - Automatic developer identity recognition (based on Git username)
  - Independent developer context management (`docs/developers/{developer}/CONTEXT.md`)
  - Global context auto-aggregation (`docs/CONTEXT.md` auto-generated)
  - Developer collaboration document (`docs/developers/COLLABORATION.md`) records dependencies and handoffs

### New Module
- `src/vibecollab/developer.py`:
  - `DeveloperManager`: Developer identity recognition, directory management, metadata maintenance
  - `ContextAggregator`: Global context aggregation algorithm
  - `migrate_to_multi_developer()`: Single-developer project migration tool

### CLI Command Extension
- Added `vibecollab dev` command group:
  - `dev whoami`: Show current developer identity
  - `dev list`: List all developers and status
  - `dev status [developer]`: View developer detailed status
  - `dev sync`: Manually trigger global CONTEXT aggregation
  - `dev init [-d developer]`: Initialize developer context
- `vibecollab init` added `--multi-dev` option for multi-developer project initialization

### Config Extension
- `project.yaml` added `multi_developer` config section:
  - `identity`: Developer recognition strategy (git_username/system_user/manual)
  - `context`: Context management config (directory structure, aggregation rules)
  - `collaboration`: Collaboration management config (dependency tracking, handoff records)
  - `dialogue_protocol`: Multi-developer mode dialogue flow

### Decision Record
- DECISION-008: Multi-developer support architecture design (A-level)
  - CHANGELOG.md, DECISIONS.md remain globally unified
  - Added `initiator` and `participants` fields to mark participants
  - Git commit no extra marking, uses native author info

### Testing
- All core feature tests passed
- Developer identity recognition working correctly
- Context aggregation algorithm verified
- File generation structure correct

### Backward Compatibility
- Single-developer mode fully compatible
- Existing projects can seamlessly migrate to multi-developer mode

---

## v0.4.3 (2026-02-09)

### Bug Fix
- **Windows encoding fix** (conversation 16):
  - Fixed `vibecollab check` emoji encoding error in Windows GBK environment
  - Implemented `is_windows_gbk()` platform detection function
  - Added emoji character mapping (✅→OK, ⚠️→!, ❌→X, ℹ️→i)
  - Added bullet point mapping (•→-)
  - Fixed all emoji usage in `cli.py` and `cli_lifecycle.py`

### Config Improvement
- **Key file responsibility config completion**:
  - Added `llms.txt`, `DECISIONS.md`, `QA_TEST_CASES.md`, `ROADMAP.md` to documentation config
  - Ensures other repos generate complete key file responsibility descriptions (CONTRIBUTING_AI.md chapter 8)
  - Synced `project.yaml` and `default.project.yaml` template

### Release
- Built PyPI release package (dist/vibe_collab-0.4.3.tar.gz, vibe_collab-0.4.3-py3-none-any.whl)
- Pending upload to PyPI

---

## v0.4.2 (2026-01-21)

### New Feature
- **Protocol self-check mechanism**: 
  - Protocol checker module (`protocol_checker.py`), checks Git protocol, document updates, dialogue flow protocol
  - CLI command `vibecollab check` executes protocol check, supports strict mode
  - Added protocol self-check section in CONTRIBUTING_AI.md (chapter 10)
  - Supports trigger words during dialogue ("check protocol", etc.)
- **PRD document management**: 
  - PRD manager module (`prd_manager.py`), supports requirement creation, updates, status management
  - Requirement change history tracking
  - Auto-creates PRD.md template on project initialization
  - Added PRD management section in CONTRIBUTING_AI.md (chapter 11)
  - Supports trigger words for PRD management during dialogue

### Improvement
- Updated project config template, added `protocol_check` and `prd_management` config items
- Added PRD.md to documentation list
- Enhanced quick reference section with protocol self-check trigger words

### Documentation
- Created PRD.md documenting project requirements (REQ-001: Protocol self-check, REQ-002: PRD document management)

---

## v0.4.1 (2026-01-21)

### Improvement
- **Stage definition optimization**: 
  - Production stage added "establish release platform standards" principle
  - Commercial stage added "plugin-based incremental development" and "data hot-update" focus
- **Stage-based rule design optimization**: CONTRIBUTING_AI.md stage rules changed to type definitions and templates, specific current stage info moved to ROADMAP.md

---

## v0.4.0 (2026-01-21)

### New Feature
- **Git check and initialization**: Auto-check Git on project init, optional auto-init repo
- **Project lifecycle management**: Complete management system for 4 stages (demo/production/commercial/stable)
- **Stage-based collaboration rules**: CONTRIBUTING_AI.md contains all stage rules, current active stage annotated
- **ROADMAP integration**: Display project lifecycle stage info in ROADMAP.md
- **Lifecycle management commands**: `vibecollab lifecycle check` and `upgrade` commands

### Improvement
- Place lifecycle stage info in ROADMAP.md (PM-focused document)
- Demo stage early CI/CD involvement
- Establish performance specifications and code refactoring before Production stage
- Enhanced documentation system (DECISIONS.md, ROADMAP.md, QA_TEST_CASES.md)

### Refactor
- Global rename llm.txt to CONTRIBUTING_AI.md
- Updated all code, documentation, template references

---

## v0.3.0 (2026-01-20)

### New Feature
- **llms.txt standard integration**: Auto-detect and update llms.txt, add AI Collaboration section
- **llmstxt.py module**: Manage llms.txt creation and updates

### Refactor
- Renamed package to `vibe-collab`
- Renamed repository to `VibeCollab`

---

## v0.2.0 (2026-01-20)

### New Feature
- **Requirement clarification protocol**: Auto-transform vague user requirements into structured descriptions
- **upgrade command**: `llmcontext upgrade` seamlessly upgrade protocol to latest version, preserving user config
- **Git initialization constraint**: Protocol layer enforces Git repo initialization for new projects
- **Usage flow diagram**: README added complete workflow diagram

### Improvement
- README added complete section list, Cursor Skill instructions
- SKILL.md synced all protocol updates
- project_template.yaml added requirement clarification, quick acceptance, build config

---

## v0.1.1 (2026-01-20)

### Conversation 10: Requirement Clarification Protocol [FEAT]

**generator.py**:
- Added `_add_requirement_clarification()` method
- Transform vague user requirements into structured descriptions

**Structured requirement template**:
- Original description → Requirement analysis (goals/scenarios/users)
- Functional requirements → Acceptance criteria
- Pending confirmations → Decision levels

---

### Conversation 9: CONTRIBUTING_AI.md Self-Update + README Update [VIBE] [DOC]

- Added `project.yaml` - Project self-configuration
- `CONTRIBUTING_AI.md` self-updated using generator, includes all sections
- README added complete section list, Cursor Skill instructions

---

### Conversation 8: Add Missing Sections [FEAT]

**generator.py new methods**:
- `_add_iteration_protocols()` - Iteration suggestion management, version review, build packaging, config-level iteration
- `_add_qa_protocol()` - QA acceptance protocol, quick acceptance template
- `_add_prompt_engineering()` - Prompt engineering best practices
- `_add_decisions_summary()` - Confirmed decisions summary
- `_add_changelog()` - Documentation iteration log
- `_add_git_history_reference()` - Git history reference

---

### Conversation 7: Package as Cursor Skill [FEAT]

- Created `.cursor/skills/llmcontext/SKILL.md`
- Added references/project_template.yaml
- Added assets/CONTEXT_TEMPLATE.md, CHANGELOG_TEMPLATE.md
- Packaged as llmcontext-skill.zip

---

### Conversation 6: Clean Up Duplicate Templates [REFACTOR]

- Deleted root `templates/` (kept package internal)
- Updated pyproject.toml build config

---

### Conversation 5: Implement Extension Hook Processing [DEV]

- Added `extension.py`: Hook management, condition evaluation, context resolution
- Supports reference/template/file_list/computed four context types
- Integrated into generator.py for extension section generation
- Added 13 extension mechanism unit tests

---

## Conversation Log

### Conversation 16: Fix Windows Encoding Issues (2026-02-10) [FIX]

**Problem**:
- `vibecollab check` crashes due to emoji characters in Windows GBK environment
- UnicodeEncodeError: 'gbk' codec can't encode character

**Solution**:
- Implemented `is_windows_gbk()` platform detection function
- Added emoji and special character mapping table:
  - ✅ → OK, ❌ → X, ⚠️ → !, ℹ️ → i
  - • → -, 🔒 → [retained]
- Modified all CLI output to use EMOJI_MAP and BULLET

**Modified files**:
- `src/vibecollab/cli.py`: Added platform detection and character substitution (+80 lines)
- `src/vibecollab/cli_lifecycle.py`: Synced lifecycle management commands (+36 lines)

**Test results**:
- ✅ `vibecollab check` runs correctly on Windows GBK
- ✅ Display format good, readability not affected

**Technical debt**:
- ✅ **Resolved**: Windows console encoding issue (high priority)

### Conversation 15: Protocol Self-Check Execution (2026-02-10) [VIBE]

**Check results**:
- ✅ Git repository normal
- ⚠️ CHANGELOG.md not updated for 19 days
- ⚠️ CONTEXT.md not updated for 2 days
- Total 3 checks: 0 errors, 2 warnings, 1 info

**Issues found**:
- Windows console encoding: `vibecollab check` crashes due to emoji characters causing GBK encoding error
- Workaround: Directly invoke Python `ProtocolChecker` module

**Output**:
- Updated CONTEXT.md recording conversation 15
- Added missing records to CHANGELOG.md (conversation 14, v0.4.3)
- Recorded Windows encoding issue in technical debt

### Conversation 14: Complete Key File Responsibility Config (2026-02-09) [CONFIG]

**Background**:
- Pulled latest code from GitHub
- Found documentation.key_files config incomplete

**Improvements**:
- Added 4 key file configs: llms.txt, DECISIONS.md, QA_TEST_CASES.md, ROADMAP.md
- Synced project.yaml and templates/default.project.yaml

**Release**:
- Version upgraded to v0.4.3
- Built release package: `python -m build`

---

## Historical Versions

### Conversations 1-4: Project Initialization to Document Sync

- Project initialization, CLI implementation
- Schema design, generator core logic
- Domain template creation
