# VibeCollab Global Context

> ! **Auto-generated, do not edit manually**
> Last updated: 2026-03-05
> Aggregated from: dev

## Project Status
- **Version**: v0.10.4-dev (in development)
- **Previous release**: v0.9.7 (PyPI published)
- **Active roles**: 1 (DEV)
- **Tests**: 1413 passed, 89% coverage
- **Current phase**: ExecutionLoop design + docs format audit complete + QA completeness verified

## Role Status

### DEV (Development)
- **Last updated**: 2026-03-05
- **Current task**: v0.10.4 Execution Plan — YAML-driven multi-round automation — DESIGN COMPLETE
- **Recently completed**:
  - **QA completeness**: 34 new test cases added (93→127), covering v0.1.0~v0.10.1 all versions
  - **Docs format audit**: CHANGELOG/ROADMAP/DECISIONS format inconsistencies fixed
  - **Developer→Role refactoring**: person-name refs → role codes across all source/docs
  - **DECISION-018**: Execution Plan architecture design confirmed (single-file, lightweight)

## Active Tasks

- v0.10.4: Execution Plan core module (core/execution_plan.py, CLI, E2E test fixtures)
- v0.10.3: Git history rewrite + GitHub facade (pending)
- v0.10.0: External project QA validation (Phase 11 TC-E2E-001~010)

## Architecture (v0.9.7+)

### Role-Based Developer System (v0.11.0)
- Directory: `docs/developers/{role_code}/` (e.g., `dev/`, `arch/`, `pm/`)
- `.metadata.yaml`: includes `role:` section with code, name, focus, triggers, is_gatekeeper
- `vibecollab dev switch`: switches active role, loads role-specific rules context
- Roles defined in `project.yaml` → `roles` section (DESIGN/ARCH/DEV/PM/QA/TEST)

### Directory Structure
36 flat modules reorganized into 7 sub-packages:
- `cli/` (11 files) — CLI commands
- `core/` (9 files) — Core business (including execution_plan.py)
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
- MCP `onboard` tool call timeout — needs investigation after IDE restart

---
*This file is auto-aggregated from role contexts*
