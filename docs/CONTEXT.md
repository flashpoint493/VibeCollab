# VibeCollab Global Context

> ! **Auto-generated, do not edit manually**
> Last updated: 2026-03-03
> Aggregated from: alice, ocarina

## Project Status
- **Version**: v0.10.1-dev (in development)
- **Previous release**: v0.9.7 (PyPI published)
- **Active developers**: 2 (alice, ocarina)
- **Tests**: 1344 passed, 89% coverage
- **Current phase**: CLI i18n framework implemented, progressing toward v0.10.2

## Developer Status

### alice
- **Last updated**: 2026-02-25
- **Activity**: Paused (last active at v0.5.4)
- **Completed**: CLI developer switch (TASK-DEV-004), switch command tests and docs (TASK-DEV-005)
- **No pending tasks**

### ocarina
- **Last updated**: 2026-03-03
- **Current task**: CLI i18n — runtime output string wrapping (remaining files)
- **Recently completed**:
  - **CLI i18n framework (v0.10.1)**: gettext-based i18n infrastructure
    - Created `src/vibecollab/i18n/` module with `_()`, `setup_locale()`, `ngettext()`
    - Pre-parse `--lang` from sys.argv before Click loads (solves Click help= timing issue)
    - Language priority: `--lang` CLI option > `VIBECOLLAB_LANG` env var > English fallback
    - Wrapped 316 unique `_()` strings across all 11 CLI files
    - All `help=` parameters wrapped in all CLI files (62+ strings via batch script)
    - Created `.pot` template (316 strings), `zh_CN .po` (131 translations), compiled `.mo`
    - `pyproject.toml` artifacts updated to include `.mo` files in wheel builds
    - Fixed 7 f-string backslash escaping SyntaxErrors
    - 1344 tests all passing, zero regression
  - **Code i18n (v0.10.1)**: Full English translation of 96 files (62 source + 34 test files)
  - Directory restructure: 36 flat .py files reorganized into 7 sub-packages
  - GBK encoding fix: 3-layer defense system

## Active Tasks

- CLI i18n: wrap remaining runtime output strings in config.py, roadmap.py, task.py, ai.py, guide.py, insight.py
- Create `.pot` extraction + `.mo` compilation tooling script

## Architecture (v0.9.7+)

### i18n Architecture
- Module: `src/vibecollab/i18n/__init__.py`
- Locale files: `src/vibecollab/i18n/locales/{lang}/LC_MESSAGES/vibecollab.po/.mo`
- Pattern: `from ..i18n import _` → `help=_("text")`, `click.echo(_("text"))`
- Click help= solution: `_pre_parse_lang()` reads `--lang` from sys.argv at module import time
- No lazy string needed — locale is set before Click decorators evaluate

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
- CLI i18n: runtime output strings in 6 files still need `_()` wrapping
- CLI i18n: remaining 185 untranslated strings in zh_CN .po file

---
*This file is auto-aggregated from multi-developer contexts*
