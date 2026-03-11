# VibeCollab Global Context

> ! **Auto-generated, do not edit manually**
> Last updated: 2026-03-11
> Aggregated from: dev

## Project Status
- **Version**: v0.10.8
- **Previous release**: v0.10.7 (PyPI published)
- **Active roles**: 1 (DEV)
- **Tests**: 1520 passed, 85% coverage
- **CI/CD**: 8-matrix (Ubuntu + Windows × Python 3.10-3.13), bash shell default
- **Current phase**: README facade + OpenClaw integration + documentation cleanup

## Role Status

### DEV (Development)
- **Last updated**: 2026-03-11
- **Current task**: README facade decoration + OpenClaw integration + i18n sync
- **Recently completed**:
  - **README facade (v0.10.8)**: Centered header, rich badges (CI/Tests/Platform), Before/After table, design philosophy blockquotes
  - **OpenClaw integration (v0.10.8)**: Added OpenClaw to MCP Server feature description, IDE integration section, skill.md
  - **i18n sync (v0.10.8)**: Chinese README fully synchronized with English changes
  - **CI/CD fix (v0.10.7)**: Resolved 4 cross-platform test failures, switched Windows CI to bash shell
  - **Python 3.9 dropped**: `requires-python >= 3.10`, `mcp` requires 3.10+

## Active Tasks

- Documentation: Temp files cleaned, ready for v0.10.8 release
- v0.10.3: Git history rewrite + GitHub facade (pending)
- v0.10.0: External project QA validation (Phase 11 TC-E2E-001~010)

## Architecture (v0.10.8)

### Role-Based Developer System (v0.11.0)
- Directory: `docs/developers/{role_code}/` (e.g., `dev/`, `arch/`, `pm/`)
- `.metadata.yaml`: includes `role:` section with code, name, focus, triggers, is_gatekeeper
- `vibecollab dev switch`: switches active role, loads role-specific rules context
- Roles defined in `project.yaml` → `roles` section (DESIGN/ARCH/DEV/PM/QA/TEST)

### Directory Structure
36 flat modules reorganized into 7 sub-packages:
- `cli/` (11 files) — CLI commands
- `core/` (9 files) — Core business (including execution_plan.py: 5 step actions + HostAdapter + loop engine)
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
