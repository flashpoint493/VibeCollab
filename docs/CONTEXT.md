# VibeCollab Global Context

> ! **Auto-generated, do not edit manually**
> Last updated: 2026-03-03
> Aggregated from: alice, ocarina

## Project Status
- **Version**: v0.10.1-dev (in development)
- **Previous release**: v0.9.7 (PyPI published)
- **Active developers**: 2 (alice, ocarina)
- **Tests**: 1344 passed, 89% coverage
- **Current phase**: Code i18n (v0.10.1), progressing toward v0.10.0 feature freeze

## Developer Status

### alice
- **Last updated**: 2026-02-25
- **Activity**: Paused (last active at v0.5.4)
- **Completed**: CLI developer switch (TASK-DEV-004), switch command tests and docs (TASK-DEV-005)
- **No pending tasks**

### ocarina
- **Last updated**: 2026-03-03
- **Current task**: Code i18n — translate all Chinese text to English
- **Recently completed**:
  - **Code i18n (v0.10.1)**: Full English translation of 96 files (62 source + 34 test files)
    - All source .py files: docstrings, comments, error messages, CLI output strings
    - All 27 .j2 template files + manifest.yaml
    - All 34 test files: assertions, comments, docstrings (preserving functional Chinese test data)
    - Fixed 2 source code truncation bugs (health.py, vector_store.py)
    - Fixed previous session leftover Chinese in test_cli_insight.py, test_insight_quality.py, test_insight_manager.py
    - 1344 tests all passing, zero regression
  - Directory restructure: 36 flat .py files reorganized into 7 sub-packages
  - GBK encoding fix: 3-layer defense system
  - v0.9.5 ROADMAP/Task integration
  - PyPI v0.9.5/v0.9.6/v0.9.7 releases

## Active Tasks

- CLI i18n architecture: implement locale-based CLI output (default English, optional Chinese)

## Architecture (v0.9.7+)

### Directory Structure
36 flat modules reorganized into 7 sub-packages:
- `cli/` (11 files) — CLI commands (main, ai, guide, config, lifecycle, insight, task, roadmap, mcp, index)
- `core/` (8 files) — Core business (generator, project, templates, pattern_engine, extension, health, protocol_checker)
- `domain/` (8 files) — Domain models (task_manager, event_log, developer, lifecycle, roadmap_parser, conflict_detector, prd_manager, session_store)
- `insight/` (3 files) — Insight solidification system (manager, signal)
- `search/` (3 files) — Semantic search (embedder, indexer, vector_store)
- `agent/` (3 files) — Agent/LLM/MCP (llm_client, agent_executor, mcp_server)
- `utils/` (2 files) — Utilities (git, llmstxt)

### GBK Encoding 3-Layer Defense
- Layer 1: `ensure_safe_stdout()` — reconfigure stdout/stderr errors='replace' at CLI startup
- Layer 2: `safe_console()` — Rich Console factory function
- Layer 3: EMOJI mapping expansion — check/cross/arrow/bar_fill/bar_empty/severity etc.

## Cross-Developer Collaboration
(See docs/developers/COLLABORATION.md)

## Technical Debt
- External QA validation (Phase 11 TC-E2E-001~010) pending
- events.jsonl Windows file lock issue needs investigation
- CLI i18n localization framework (default English, optional Chinese) — next step

---
*This file is auto-aggregated from multi-developer contexts*
