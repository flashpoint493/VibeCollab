# VibeCollab Global Context

> ! **Auto-generated, do not edit manually**
> Last updated: 2026-03-09
> Aggregated from: dev

## Project Status
- **Version**: v0.10.6 (in development)
- **Previous release**: v0.9.7 (PyPI published)
- **Active roles**: 1 (DEV)
- **Tests**: 1413+ passed, 89% coverage
- **Current phase**: Execution Plan Phase 5 — Auto Driver (keyboard simulation for autonomous IDE control)

## Role Status

### DEV (Development)
- **Last updated**: 2026-03-09
- **Current task**: v0.10.6 Auto Driver self-test
- **Recently completed**:
  - **Auto Driver**: Keyboard simulation for autonomous IDE control (`vibecollab auto` command group)
  - **auto init**: Creates .bat launcher scripts for double-click automation
  - **Self-bootstrap test**: Successfully tested auto driver on VibeCollab itself
  - **FileExchangeAdapter**: File-based IDE AI communication for Cursor/Cline (`host: file_exchange`)
  - **Design alignment**: Clarified vibecollab as orchestrator, IDE AI as executor (has tool-use)
  - **Execution Plan Phase 3**: Autonomous loop engine (`loop` action), 31 new tests (101 total)
  - **Execution Plan Phase 2**: HostAdapter protocol, variable passing, 29 new tests (70 total)
  - **Execution Plan Phase 1**: PlanRunner, 4 step actions (cli/assert/wait/prompt), CLI, 41 tests

## Active Tasks

- v0.10.5: Code cleanup — remove LLMAdapter (no tool-use), update tests
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
