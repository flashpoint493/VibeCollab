# VibeCollab Changelog

## [Unreleased]

### In Progress (v0.12.0)
- **YAML Schema Design** (TASK-DEV-030, DECISION-027): 6 document type schemas created
  - `schema/context.schema.yaml` — Global + role context (project status, tech debt)
  - `schema/changelog.schema.yaml` — Versioned releases with categorized entries
  - `schema/decisions.schema.yaml` — Decision records with levels, options, rationale
  - `schema/roadmap.schema.yaml` — Milestones, lifecycle stages, checklist items
  - `schema/prd.schema.yaml` — Requirements with lifecycle tracking
  - `schema/qa.schema.yaml` — QA test cases with steps, expected, status
  - All schemas follow `kind` + `version` envelope pattern (forward-compatible)
- **events.jsonl Bug Fix**: Root cause found — path was a directory not a file on Windows. Fixed by recreating as file.
- **Module Rewrites** (TASK-DEV-032): 3 core modules rewritten for YAML-first
  - `PRDManager`: YAML-first load/save, Markdown as fallback. `_load_yaml()` + `_generate_yaml_data()` new methods
  - `RoadmapParser`: YAML-first parse via `_parse_yaml()`, Markdown fallback via `_parse_markdown()`. Auto-resolves `roadmap.yaml` vs `ROADMAP.md`
  - `ContextAggregator`: Reads YAML role contexts, outputs both `context.yaml` (source of truth) and `CONTEXT.md` (view). `_generate_yaml_data()` new method
  - `RoleManager.get_role_context_file()`: Now returns `context.yaml` if exists, else `CONTEXT.md`
  - 89 tests passing (53 roadmap + 36 prd), 3 test fixes for YAML output expectations
- **Secondary Module Updates** (TASK-DEV-033): 5 modules made YAML-aware
  - `ProtocolChecker`: Role context checks accept both `context.yaml` and `CONTEXT.md`; PRD check supports `prd.yaml`
  - `InsightSignalCollector`: `key_docs` list includes both `.yaml` and `.md` variants; signal analysis merges both
  - `Indexer`: `DEFAULT_DOC_FILES` includes YAML paths; `_split_yaml_by_keys()` new splitter; YAML/MD deduplication
  - `cli/guide.py`: Role context path resolution prefers `context.yaml`
  - `mcp/server.py`: All 4 doc Resources prefer YAML; developer_context + start_conversation prompt prefer YAML
  - 119 additional tests passing (protocol_checker + signal + indexer), 1 test fix

## [v0.11.0] - 2026-04-02

### Added
- **Guard CLI Integration** (TASK-DEV-026): `vibecollab check --guards` implemented
  - `--guards/--no-guards` flag (default: on) in `check` command
  - Scans all git-tracked files against guard rules (defaults + project.yaml custom)
  - Displays BLOCK violations as errors, WARN as warnings
  - Integrated into check summary statistics and exit code
- **MCP Guard Tools** (TASK-DEV-026): Two new MCP tools added
  - `guard_check(operation, file_path)` — Pre-flight check for file operations
  - `guard_list_rules()` — List all configured guard rules
- **Role CLI Update**: Confirmed 8 subcommands already implemented (whoami/list/status/switch/permissions/init/sync/conflicts), ROADMAP updated
- **TaskManager Permission Enforcement**: RoleManager injected into create_task/transition
  - create_task raises PermissionError when role not allowed
  - transition returns ValidationResult(ok=False) when role not allowed
  - CLI and MCP both inject RoleManager for consistent enforcement
- **Guards + Hooks Config Validation**: SchemaValidator extended with guards/hooks schema
- **RoleManager Permission Tests** (TASK-DEV-029): 69 dedicated unit tests for role.py permission system
  - `test_role_permissions.py`: covers _load_permissions_config, get_developer_roles, get_primary_role
  - `can_create_task_for`, `can_transition_to`, `can_write_file`, `can_approve_decision` — all 5 roles verified
  - `get_role_permissions`, `get_effective_permissions` — structure + correctness
  - Edge cases: empty config, unknown devs, cache isolation, fnmatch glob, idempotency
  - v0.11.0 total: **151 tests** across 6 test files (guard, hooks, skills, permissions, triggers, role_permissions)
- **Project Self-Check**: `vibecollab check` all green (11 checks, 0 errors)
  - Fixed: created missing `docs/roles/ocarina/CONTEXT.md`
  - Guard check passed: 8 rules, 227 files scanned
  - Insight consistency passed
- **Documentation Update**: skill.md, README.md, README.pypi.md, README.zh-CN.md synchronized
  - MCP tools count updated 12 → 19 (added guard_check, guard_list_rules, role_context, insight_graph, insight_export, insight_import, task_solidify, role_list)
  - CLI Reference: `vibecollab dev` → `vibecollab role` migration, added hooks commands
  - Features section: added Git Hooks + Guard Protection, Multi-Role permissions
  - Version histories updated with v0.11.0 and v0.10.14 entries
  - Architecture tables: updated pillars to reflect Guard protection and role permissions
  - Tests badge: corrected 1520 → 151 passed

### Changed
- **Version bump**: 0.10.13 → 0.11.0
- **Test suite**: 1666 tests passing (was 151 in ROADMAP docs, actual test count grew with new modules)

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

- **Guard Protection Engine** (FP-008): Core engine implemented
  - INS-040: Guard Protection Engine Pattern
  - `GuardEngine` class with `check_operation()`, `check_batch()`, `list_rules()`, `test_path()`
  - `GuardSeverity` enum: block/warn/allow
  - `GuardRule` dataclass with glob pattern matching and operation filtering
  - 4 default rules: meta_protection, library_protection, insight_protection, temp_warning
  - Custom rules loadable from `project.yaml`
  - **Note**: CLI integration (`vibecollab check --guards`) pending

- **Git Hooks CLI Commands** (FP-001): Full CLI implemented
  - `HookManager` domain module with install/uninstall/run/status/list methods
  - `vibecollab hooks install [-t TYPE] [--force]` — Install Git hooks
  - `vibecollab hooks uninstall [-t TYPE] [--all]` — Remove hooks
  - `vibecollab hooks run <hook_type>` — Manual hook execution
  - `vibecollab hooks status [--json]` — Hook status overview
  - `vibecollab hooks list` — List installed vibecollab hooks
  - Windows PowerShell + Unix Bash dual template support
  - Supports 5 hook types: pre-commit, pre-push, post-commit, post-checkout, prepare-commit-msg

- **Dynamic Skill Registration** (DEV-027): Implemented
  - `SkillRegistry` module: Load skills dynamically from Insight YAML files
  - `RoleManager` integration: `get_skills_for_role()`, `format_skills_for_prompt()`, `find_skills_by_trigger()`
  - Skills cached per role, sorted by priority

- **Insight Trigger Registry**: New module + CLI
  - `TriggerRegistry` module: Discover triggers from insight tags
  - `vibecollab insight triggers [-l LIMIT] [-s SEARCH] [--json]` CLI command
  - Tag-based trigger discovery with search, stats, and formatted table output

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
- **FP-001**: Git Hooks Framework - ~~Pre-commit/pre-push/post-commit hooks with configurable rules~~ ✅ Core done; remaining: advanced hook type extensions
- **FP-008**: Guard Protection Engine - ~~Pre/post-action protection rules~~ ✅ Engine done; remaining: CLI integration (`vibecollab check --guards`), MCP `guard_check` tool
- **Role Architecture Fix**: ~~Developer-Role binding with permissions and dynamic skill registration~~ ✅ Permissions + Skill Registry done; remaining: `vibecollab role` CLI commands, permission enforcement in Task operations

### Planned (v0.12.0)
- **DECISION-025**: Docs Markdown → YAML Big-Bang Migration (S-level)
  - All docs/*.md → docs/*.yaml, YAML as source of truth
  - New CLI: `vibecollab docs render` for Markdown/JSON view generation
  - 12+ modules rewrite, 193+ test updates
  - No backward compatibility — clean break
- **FP-004**: Standard Workflows - docs-change, feature-add, requirement-review, competitor-analysis
- **FP-005**: Document Template Library - ADR, sprint-plan, TDD templates via Pattern Engine (YAML-native)
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
