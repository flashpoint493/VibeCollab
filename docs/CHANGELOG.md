# VibeCollab Changelog

## [Unreleased]

### Completed (v0.10.13)
- **v0.10.13 Release**: Finalized v0.10.x release cycle
  - PyPI release v0.10.13 with role-based architecture
  - Updated documentation (skill.md with Task-Insight best practices)
  - Verified CI/CD pipeline (99.7% test pass rate)
  - All commit messages standardized to English

## [v0.10.14] - 2026-03-30

### Added
- **Git Hooks Framework** (FP-001): Pre-commit consistency check
  - INS-039: Git Hooks Framework Pattern
  - Implemented `.git/hooks/pre-commit` with `vibecollab check` and local build verification
  - Every commit auto-validates insight consistency and runs ruff + pytest
  - Fixed fingerprint calculation (kind, version, id, title, summary, tags, category, body, artifacts, origin)

- **Guard Protection Engine** (FP-008): Pattern defined
  - INS-040: Guard Protection Engine Pattern
  - Pre-action and post-action guard rules documented
  - Severity levels: block/warn/allow

- **Strict Document-Code Sync**: Linked groups + Git commit level
  - INS-042: Strict Git-Based Document-Code Sync Pattern
  - project.yaml: Configured linked_groups with git_commit level
  - Enforces CONTEXT + CHANGELOG, ROADMAP + DECISIONS sync

- **Commit-Type-Based Dynamic Check**: Context-aware strictness
  - INS-043: Commit-Type-Based Dynamic Document Sync Check
  - project.yaml: Added doc_requirements and severity per commit prefix
  - feat/fix: error level, docs/refactor: warning level, config: info level

- **Role-Driven Architecture Implementation** (DEV-027)
  - INS-044: Implementation Pattern
  - INS-045: Best Practices
  - RoleManager permission system: can_create_task_for, can_transition_to, can_write_file, can_approve_decision
  - CLI: `vibecollab role permissions` command
  - project.yaml: Permission configs for all 6 roles

### Changed
- **Documentation Update**: README.md and skill.md synchronized
  - INS-041: Documentation Update Pattern
  - skill.md: Added Step 2.5 (Git Hooks installation)
  - Manual setup includes `vibecollab hooks install`

- **Task-Insight Best Practices**: Systematic workflow
  - INS-036, INS-037, INS-038 for release engineering patterns
  - INS-046: Local Build Check Before Commit best practice
  - Fixed 40+ insight fingerprint mismatches
  - Continuous git synchronization (15+ commits)

### Fixed
- Import order in cli/main.py (ruff I001)
- Pre-commit hook now includes local build checks (ruff + pytest)
- All 1515 tests passing

---

### Planned (v0.11.0)

### Planned (v0.11.0)
- **FP-001**: Git Hooks Framework - Pre-commit/pre-push/post-commit hooks with configurable rules
- **FP-008**: Guard Protection Engine - Pre/post-action protection rules integrated with check command
- **Role Architecture Fix**: Developer-Role binding with permissions and dynamic skill registration

### Planned (v0.12.0)
- **FP-004**: Standard Workflows - docs-change, feature-add, requirement-review, competitor-analysis
- **FP-005**: Document Template Library - ADR, sprint-plan, TDD templates via Pattern Engine
- **FP-015**: Insight Derivation Chain - Track insight relationships and derivation history

### Planned (v0.13.0)
- **Insight-First CLI**: Optimize skill injection and MCP for proactive insight usage

### Decisions
- **DECISION-019**: CCGS Feature Proposal Assessment - 8 accepted, 2 deferred, 8 rejected
- **DECISION-020**: Role-Driven Architecture - Fix role/dev separation
- **DECISION-021**: Workflow Integration - Integrate into plan CLI, not standalone commands
- **DECISION-022**: Hooks + Guards Dual-Track - Git lifecycle + file operation protection

---

## [v0.10.13] - 2026-03-27

### Fixed
- Role-based architecture: Complete DeveloperManager → RoleManager migration
- Test suite: Fix 33 failing tests, achieve 99.7% pass rate (1510/1515)
- Conflict detector: Update parameter names (developers → roles)
- Pattern engine: Update section titles and conditions for role_context
- Context aggregator: Update terminology (developer → role)
- CLI commands: Rename dev → role throughout codebase
- Default paths: Update docs/developers → docs/roles

### Changed
- BREAKING: vibecollab dev → vibecollab role CLI commands
- BREAKING: docs/developers/ → docs/roles/ directory structure
- Metadata keys: 'developer' → 'role' in context files

---

## [v0.10.12] - 2026-03-27

### Added
- IDE Skill Injection: Support for Cursor, Cline, CodeBuddy, OpenCode, and 'all' option
- GitHub Actions PyPI auto-publish fix (Trusted Publishing)

---

## Project initialization
- Generated CONTRIBUTING_AI.md collaboration rules

---
