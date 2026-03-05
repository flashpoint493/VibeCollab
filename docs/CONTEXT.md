# VibeCollab Global Context

> ! **Auto-generated, do not edit manually**
> Last updated: 2026-03-04
> Aggregated from: alice, ocarina

## Project Status
- **Version**: v0.10.1-dev (in development)
- **Previous release**: v0.9.7 (PyPI published)
- **Active developers**: 2 (alice, ocarina)
- **Tests**: 1409 passed, 89% coverage
- **Current phase**: MCP path fix completed; IDE config files removed from git history; v0.10.3 in progress

## Developer Status

### alice
- **Last updated**: 2026-02-25
- **Activity**: Paused (last active at v0.5.4)
- **Completed**: CLI developer switch (TASK-DEV-004), switch command tests and docs (TASK-DEV-005)
- **No pending tasks**

### ocarina
- **Last updated**: 2026-03-04
- **Current task**: v0.10.3 Git history rewrite + GitHub facade — IN PROGRESS
- **Recently completed**:
  - **MCP path fix**: CodeBuddy config path `.codebuddy/mcp.json` → `.mcp.json` (per official docs)
  - **Git history cleanup**: `git filter-repo` removed `.vibecollab/`, `.cursor/`, `.codebuddy/` from 218 commits + force push
  - **`.gitignore` update**: All AI IDE config dirs ignored (`.cursor/`, `.cline/`, `.codebuddy/`, `.mcp.json`, `.openclaw/`, `.windsurf/`, `.roo/`, `.augment/`)
  - **Insight cache translation**: 16 Insight YAML files (INS-001~017) translated to English
  - **Template translation (v0.10.3)**: `default.project.yaml`, 3 domain extensions
  - **Docs English translation (v0.10.2)**: All 10 docs/ files translated (~4000+ lines)
  - **Code i18n (v0.10.1)**: Full English translation of 96 files (62 source + 34 tests)
  - **i18n framework**: gettext-based CLI localization, 316 translatable strings

## Active Tasks

- v0.10.3: Git commit messages rewrite (97 commits → Conventional Commits English) + GitHub facade
- README.zh-CN.md project structure section modernization
- MCP `onboard` tool call timeout investigation

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
- README.zh-CN.md project structure section has outdated module layout
- MCP `onboard` tool call timeout — needs investigation after IDE restart

---
*This file is auto-aggregated from multi-developer contexts*
