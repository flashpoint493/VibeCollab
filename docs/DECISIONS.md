# Decisions Markdown template - renders docs/decisions.yaml to docs/DECISIONS.md
# VibeCollab Decision Record

## Pending Decisions



(None)


## Confirmed Decisions




### DECISION-027: v0.12.0 YAML Schema Design Strategy
- **Level**: S
- **Status**: confirmed
- **Date**: 2026-04-01
- **Context**: v0.12.0 requires YAML schemas for all doc types. User confirmed three key design principles.
- **Problem**: Need schema design for 6 document types to enable Markdown → YAML migration
- **Decision**: 1. Big-Bang migration (confirmed from DECISION-025). Only CONTRIBUTING_AI.md, skill.md, README.md remain as Markdown.
2. YAML docs can be aggregated back to Markdown via `vibecollab docs render`. Descriptive content stays descriptive in YAML.
3. Follow insight.schema.yaml pattern (kind + version top-level). Design must be robust and forward-compatible.

- **Rationale**: YAML is more effective for AI consumption. Descriptive content in YAML still serves both AI parsing and human rendering via Markdown view generation.


- **Related Tasks**: TASK-DEV-030



### DECISION-026: v0.11.0 Milestone Completion Validation
- **Level**: B
- **Status**: confirmed
- **Date**: 2026-04-01
- **Context**: v0.11.0 milestone (Role-Driven Architecture + Git Hooks + Guards) reached 32/32 items complete.
- **Problem**: Final validation needed before declaring milestone closed
- **Decision**: v0.11.0 milestone is officially complete. Ready for PyPI release and v0.12.0 planning.
- **Rationale**: All checks passed: 151 tests, vibecollab check all green, Guard (8 rules, 227 files), Insight consistency passed.

- **Validation**:

  - Unit Tests: pass (151 passed across 6 test files, 0 failures)

  - vibecollab check: pass (11 checks, 0 errors)

  - Protocol Compliance: pass (Fixed missing docs/roles/ocarina/CONTEXT.md)

  - Documentation: pass (skill.md, README.md, README.pypi.md, README.zh-CN.md all synced)

  - Task-Insight Cycle: pass (TASK-DEV-029 + INS-054)





### DECISION-025: Docs Markdown → YAML Big-Bang Migration (v0.12.0)
- **Level**: S
- **Status**: confirmed
- **Date**: 2026-04-01
- **Context**: All 7 docs/ files are Markdown. 12+ code modules parse them via fragile regex. This blocks structured Insight automation and reliable workflow integration.
- **Problem**: Fragile regex-based Markdown parsing in 12+ modules prevents structured automation
- **Decision**: Big-bang migration (Option B). YAML is source of truth, Markdown generated on demand by vibecollab docs render.
- **Rationale**: Clean cut, no dual-format maintenance overhead. User base is small, clean migration preferred.




### DECISION-024: v0.11.0 Implementation Strategy (3/30 Sprint)
- **Level**: B
- **Status**: confirmed
- **Date**: 2026-03-30
- **Context**: 
- **Problem**: v0.11.0 has three major features (FP-001, FP-008, Role Fix). Need to decide implementation order and scope for sprint.
- **Decision**: 1. Guard Engine: Implement as standalone domain module first, defer CLI integration.
2. Hooks CLI: Implement full CLI immediately since HookManager is self-contained.
3. Role Permissions: Implement in RoleManager directly (not separate PermissionManager).
4. Skill Registry: Create as standalone module, bridge via RoleManager.
5. Trigger Registry: Extract triggers from Insight tags (not role_skills section).

- **Rationale**: Maximize independent testable modules, defer integration that requires refactoring.




### DECISION-023: Commit-Type-Based Dynamic Document Sync
- **Level**: A
- **Status**: confirmed
- **Date**: 2026-03-29
- **Context**: 
- **Problem**: Current vibecollab check only verifies file modification time (24h threshold), allowing docs to drift from actual code state.
- **Decision**: Three-layer document-code synchronization:
1. Linked Groups (Git Commit Level) — CONTEXT+CHANGELOG, ROADMAP+DECISIONS must sync at commit level
2. Commit-Type-Based Requirements — feat/fix require doc updates (error), docs/refactor (warning), config (info)
3. Dynamic Severity — Block/warn/allow based on commit prefix

- **Rationale**: Context-aware, workflow-aligned, progressive enforcement.




### DECISION-022: Hooks and Guards Integration
- **Level**: A
- **Status**: confirmed
- **Date**: 2026-03-27
- **Context**: 
- **Problem**: Need constraint system for both git lifecycle and file operations
- **Decision**: Dual-track constraint system:
- Git Hooks (FP-001): Install to .git/hooks/, enforce hard constraints (pre-commit, pre-push)
- Guards (FP-008): Integrate into vibecollab check, file operation protection via MCP guard_check
Both use project.yaml configuration. Hooks = Git lifecycle, Guards = File operations.

- **Rationale**: Different trigger points serve different purposes; unified config keeps it simple.




### DECISION-021: Workflow Integration Strategy
- **Level**: A
- **Status**: confirmed
- **Date**: 2026-03-27
- **Context**: 
- **Problem**: How to integrate new workflows (docs-change, feature-add, requirement-review)
- **Decision**: Integrate into existing plan CLI (vibecollab plan run <workflow>.yaml), NOT separate commands.
- **Rationale**: Avoid command proliferation, leverage existing PlanRunner infrastructure, YAML-driven matches philosophy.




### DECISION-020: Role-Driven Architecture Fix
- **Level**: S
- **Status**: confirmed
- **Date**: 2026-03-27
- **Context**: 
- **Problem**: Current architecture separates developer identity from role. No true role-driven routing or permission system.
- **Decision**: Implement role-driven architecture:
1. Developer-Role Binding in project.yaml (name, roles, primary_role)
2. Role Permissions (file_patterns, can_create_task_for, can_transition_to, can_approve_decision)
3. Auto-Delegation via dev switch + dynamic skill registration from Insights

- **Rationale**: Fix fundamental separation, enable permission-based access without over-engineering.




### DECISION-019: CCGS Feature Proposal Assessment
- **Level**: S
- **Status**: confirmed
- **Date**: 2026-03-27
- **Context**: 
- **Problem**: 17 Feature Proposals (FP-001~FP-017) submitted based on CCGS framework analysis. Need strategic review.
- **Decision**: Accepted (7): FP-001 Git Hooks (P0), FP-002 Agent Orchestration Lite (P1), FP-004 Workflow Definition (P1),
FP-005 Document Template Library (P2), FP-008 Guard Protection Engine (P0), FP-015 Insight Derivation Chain (P2),
Role Fix (P0).
Deferred (2): FP-014 Adversarial Code Review, FP-017 6-Dimension Audit.
Rejected (8): FP-003, FP-006, FP-007, FP-009, FP-010, FP-011, FP-012, FP-016.

- **Rationale**: Strategic principles: Insight-Centric, Plan-YAML Integration, No LLM Runtime,
Simplify Project.yaml, Skill over Preset.







---
*Decision record format: see CONTRIBUTING_AI.md*