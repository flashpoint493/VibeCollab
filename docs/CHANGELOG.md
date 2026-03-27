# VibeCollab Changelog

## [Unreleased]

### Completed (v0.10.13)
- **v0.10.13 Release**: Finalized v0.10.x release cycle
  - PyPI release v0.10.13 with role-based architecture
  - Updated documentation (skill.md with Task-Insight best practices)
  - Verified CI/CD pipeline (99.7% test pass rate)
  - All commit messages standardized to English

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
