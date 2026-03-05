# VibeCollab - ocarina's Work Context

## Current Status
- **Version**: v0.10.1-dev
- **Developer**: ocarina
- **Last updated**: 2026-03-04

## Current Tasks
- **DECISION-017**: v0.10.x release engineering plan confirmed (S-level)
- **v0.10.3**: Git history rewrite + Repository facade — IN PROGRESS
- **Coverage**: 89% (1409 tests passed) — exceeds 85% threshold

## Recently Completed
- ✅ **MCP path fix**: CodeBuddy MCP config path corrected from `.codebuddy/mcp.json` to `.mcp.json` (per official docs)
- ✅ **Git history cleanup**: `git filter-repo` removed `.vibecollab/`, `.cursor/`, `.codebuddy/` from all 218 commits
- ✅ **`.gitignore` update**: Added ignore rules for all AI IDE config dirs (`.cursor/`, `.cline/`, `.codebuddy/`, `.mcp.json`, `.openclaw/`, `.windsurf/`, `.roo/`, `.augment/`)
- ✅ **`vibecollab mcp inject` fix**: Updated `mcp.py` + tests + docs for new CodeBuddy path (7 tests passed)
- ✅ **Force push**: History rewritten, pushed to `origin/master`
- ✅ **Insight cache translation**: 16 Insight YAML files translated to English
- ✅ **Template translation (v0.10.3)**: `default.project.yaml`, 3 domain extensions
- ✅ **Docs English translation (v0.10.2)**: All 10 docs/ files translated
- ✅ **Code i18n (v0.10.1)**: Full English translation of 96 files

## Next Steps (DECISION-017)
1. ~~**v0.10.2** — Documentation bilingualization~~ ✅ DONE
2. **v0.10.3** — Git commit messages rewrite (97 commits → Conventional Commits English) + GitHub facade
3. **v1.0.0** — Official release

## Technical Debt
- cli_insight.py / cli_task.py not yet migrated to Rich output style (deferred to v1.0)
- `vibecollab index --watch` file change auto-rebuild indexing (deferred)
- README.zh-CN.md project structure section has outdated module layout
- MCP `onboard` tool call timeout — needs investigation after IDE restart

---
*This file is maintained by ocarina*
