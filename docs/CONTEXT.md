# VibeCollab Global Context

> ! **Auto-generated, do not edit manually**
> Last updated: 2026-03-05
> Aggregated from: dev

## Project Status
- **Version**: v0.10.3-dev (in development)
- **Previous release**: v0.9.7 (PyPI published)
- **Active roles**: 1 (DEV)
- **Tests**: 1409 passed, 89% coverage
- **Current phase**: Developer → Role refactoring; git history fully rewritten to English

## Role Status

### DEV (Development)
- **Last updated**: 2026-03-05
- **Current task**: v0.11.0 Developer → Role refactoring — IN PROGRESS
- **Recently completed**:
  - **Git commit rewrite**: All 220 commits → English Conventional Commits via `git filter-repo`
  - **MCP path fix**: CodeBuddy config path `.codebuddy/mcp.json` → `.mcp.json`
  - **Git history cleanup**: removed IDE config dirs from all commits + force push
  - **Template/docs/code i18n**: v0.10.1~v0.10.3 all completed

## Active Tasks

- v0.11.0: Developer → Role refactoring (directories, metadata with role schema, CLI integration)
- README.zh-CN.md project structure section modernization
- MCP `onboard` tool call timeout investigation

## Architecture (v0.9.7+)

### Role-Based Developer System (v0.11.0)
- Directory: `docs/developers/{role_code}/` (e.g., `dev/`, `arch/`, `pm/`)
- `.metadata.yaml`: includes `role:` section with code, name, focus, triggers, is_gatekeeper
- `vibecollab dev switch`: switches active role, loads role-specific rules context
- Roles defined in `project.yaml` → `roles` section (DESIGN/ARCH/DEV/PM/QA/TEST)

### Directory Structure
36 flat modules reorganized into 7 sub-packages:
- `cli/` (11 files) — CLI commands
- `core/` (8 files) — Core business
- `domain/` (8 files) — Domain models
- `insight/` (3 files) — Insight solidification system
- `search/` (3 files) — Semantic search
- `agent/` (3 files) — Agent/LLM/MCP
- `utils/` (2 files) — Utilities

## Cross-Role Collaboration
(See docs/developers/COLLABORATION.md)

## Technical Debt
- External QA validation (Phase 11 TC-E2E-001~010) pending
- events.jsonl Windows file lock issue needs investigation
- README.zh-CN.md project structure section has outdated module layout
- MCP `onboard` tool call timeout — needs investigation after IDE restart

---
*This file is auto-aggregated from role contexts*
