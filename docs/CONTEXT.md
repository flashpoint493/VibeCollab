# VibeCollab Global Context

> Last updated: 2026-03-13
> Aggregated from: dev

## Project Status
- **Version**: v0.10.9
- **Previous release**: v0.10.9 (PyPI published)
- **Active roles**: 1 (DEV)
- **Tests**: 1520 passed, 89% coverage
- **CI/CD**: 8-matrix (Ubuntu + Windows × Python 3.10-3.13), bash shell default
- **Current phase**: Bug fixes from user testing + release engineering

## Role Status

### DEV (Development)
- **Last updated**: 2026-03-13
- **Current task**: User feedback bug fixes + version tooling + roadmap re-planning

### Recently completed (this session)
- **Version alignment**: Fixed 4 stale version references (README.pypi.md, llms.txt, CONTEXT.md ×2)
- **bump_version.py**: One-command version sync tool (check / sync / bump to N)
- **Bug fix: init -o required**: Changed `-o/--output` from required to optional (default: `.`)
- **Bug fix: MCP config path**: `mcp config/inject` now resolves full executable path via `shutil.which()`
- **Bug fix: skill.md `--ide auto`**: Fixed to `--ide cursor` (auto was never a valid option)
- **Revert**: Reverted 18 local-only commits (Scheduler + Examples Market + Self-Iterate), recorded in local_changes_backup.md

### Decisions made (this session)
- **D1: Scheduler** — CUT. VibeCollab is a protocol tool, not an AI runtime.
- **D2: Examples Market** — NOT in this package. Init templates will be enhanced instead.
- **D3: Git History Rewrite** — Only fix the one non-compliant commit (`"v0.10.9"` → `chore(release): v0.10.9`)
- **D4: External QA** — Keep as-is in ROADMAP, no simplification
- **D5: Version numbering** — Continue v0.10.x, no premature major version bump

## Active Tasks

- Fix commit message `"v0.10.9"` → `chore(release): v0.10.9` (amend + force push)
- v0.10.0: External project QA validation (Phase 11 TC-E2E-001~010)
- GitHub facade: Issue/PR templates, CONTRIBUTING.md, Badge, About/Topics

## Architecture (v0.10.9)

### Directory Structure
36 flat modules reorganized into 7 sub-packages:
- `cli/` (11 files) — CLI commands
- `core/` (9 files) — Core business (including execution_plan.py: 5 step actions + HostAdapter + loop engine)
- `domain/` (8 files) — Domain models
- `insight/` (3 files) — Insight solidification system
- `search/` (3 files) — Semantic search
- `agent/` (3 files) — Agent/LLM/MCP
- `utils/` (2 files) — Utilities
- `scripts/` — Dev tools (bump_version.py)

## Technical Debt
- External QA validation (Phase 11 TC-E2E-001~010) pending
- events.jsonl Windows file lock issue needs investigation
- MCP `onboard` tool call timeout — needs investigation after IDE restart
- Commit `"v0.10.9"` needs amend to conventional format

---
*This file is auto-aggregated from role contexts*
