# Changelog Markdown template - renders docs/changelog.yaml to docs/CHANGELOG.md
# Project Changelog

## 2026-04-25 — Split Package Refactoring (Stage 1 & 2)

**Scope**: Extract 8 sub-packages from main monorepo, fix cross-package imports, validate local builds.

**Changes**:
- Created `scripts/fix_split_packages.py` automation script
- Copied source from `VibeCollab/src/vibecollab/` to all 8 sub-repos
- Rewrote all cross-package relative imports (`from ..x import ...`) to absolute imports (`from vibecollab_x.x import ...`)
- Generated `pyproject.toml` for each sub-package with correct inter-dependencies
- Restored `__init__.py` public API exports for backward compatibility
- Local wheel build + import validation: **8/8 passed**
- Pushed code to all 8 GitHub repos (`main` branch)

**Sub-Packages**:
- `vibecollab-core` — core logic, domain models, utils, i18n, contrib
- `vibecollab-insights` — insight manager, embedder, vector store, search
- `vibecollab-ide` — IDE adapters (Cursor, Windsurf, Cline, etc.)
- `vibecollab-mcp` — MCP server, LLM client, agent executor
- `vibecollab-patterns` — Jinja2 pattern templates (re-exports engine from core)
- `vibecollab-generator` — document templates & plans (re-exports generator from core)
- `vibecollab-tasks` — task manager, roadmap parser, PRD manager (domain re-export)
- `vibecollab-cli` — all CLI commands and `vibecollab` entrypoint

**Known Issues**:
- File duplication between `vibecollab-core` and `vibecollab-tasks` (5 domain modules)
- `vibecollab-patterns` and `vibecollab-generator` re-export from core instead of owning logic files

**Next Steps**:
- User local validation before PyPI upload
- Main repo `refactor/modular-deps` branch creation
- Combination validation (main package + sub-packages)

---
*This file is auto-generated from docs/changelog.yaml*
