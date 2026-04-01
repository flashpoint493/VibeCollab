# VibeCollab Decision Record

## Pending Decisions

(None)

## Confirmed Decisions

### DECISION-019: CCGS Feature Proposal Assessment

**Date**: 2026-03-27
**Type**: S-level (Strategic)
**Status**: Confirmed

**Background**:
TKGO project user submitted 17 Feature Proposals (FP-001~FP-017) based on CCGS framework analysis. After review, the following decisions have been made:

**Accepted Features**:

| FP | Proposal | Status | Notes |
|----|----------|--------|-------|
| **FP-001** | Git Hooks Framework | ✅ **Accepted - P0** | Must integrate with existing git support |
| **FP-002** | Agent Orchestration (Lite) | ✅ **Accepted - P1** | Auto-delegation via `vibecollab dev` + roles, dynamic skill registration from Insights |
| **FP-004** | Workflow Definition | ✅ **Accepted - P1** | Integrate into `plan` CLI with YAML configs, NOT standalone MCP commands |
| **FP-005** | Document Template Library | ✅ **Accepted - P2** | Simple template addition via Pattern Engine |
| **FP-008** | Guard Protection Engine | ✅ **Accepted - P0** | Integrate into `vibecollab check`, different audit dimensions per workflow |
| **FP-015** | Insight Derivation Chain | ✅ **Accepted - P2** | Small feature, enhance existing insight graph |
| **Role Fix** | Role-Driven Architecture | ✅ **Accepted - P0** | Fix current role/dev separation, implement permission-based access |

**Deferred Features**:

| FP | Proposal | Status | Notes |
|----|----------|--------|-------|
| **FP-014** | Adversarial Code Review | ⏳ **Deferred** | Interesting but schedule after template examples project |
| **FP-017** | 6-Dimension Audit | ⏳ **Deferred** | Postpone to later phase |

**Rejected Features**:

| FP | Proposal | Status | Reason |
|----|----------|--------|--------|
| **FP-003** | Path-scoped Rules | ❌ **Rejected** | Game industry specific, should be Insight/skill not core |
| **FP-006** | Structured Introspection | ❌ **Rejected** | Current insight suggest is sufficient, prioritize insight integration |
| **FP-007** | Behavior Mode Tags | ❌ **Rejected** | Game specific, out of scope |
| **FP-009** | Quality Gate Checker | ❌ **Rejected** | Duplicate of task solidify, optimize existing first |
| **FP-010** | Smart Probe | ❌ **Rejected** | LLM runtime behavior, out of scope |
| **FP-011** | Scale-adaptive Workflow | ❌ **Rejected** | Over-complex, conflicts with simplicity principle |
| **FP-012** | Project Stage Auto-detect | ❌ **Rejected** | Duplicate of roadmap status |
| **FP-016** | Domain Extension Packages | ❌ **Rejected** | Not needed at current stage |

**Strategic Principles Established**:

1. **Insight-Centric**: All new features must strengthen Insight integration into CLI workflow
2. **Plan-YAML Integration**: Workflows must integrate into existing `plan` CLI, not create new command groups
3. **No LLM Runtime**: Reject any features that control AI behavior/thinking patterns
4. **Simplify Project.yaml**: Reject features that increase project.yaml complexity (path_rules, etc.)
5. **Skill over Preset**: Prefer dynamic skill registration from Insights over hardcoded presets

---

### DECISION-020: Role-Driven Architecture Fix

**Date**: 2026-03-27
**Type**: S-level (Strategic)
**Status**: Confirmed

**Problem**:
Current architecture separates "developer identity" (git_username) from "role" (DEV/DESIGN/ARCH). Task has `role` field but there's no true role-driven routing or permission system.

**Solution**:
Implement role-driven architecture with the following components:

1. **Developer-Role Binding**:
   ```yaml
   developers:
     - name: "ocarmihe"
       roles: [DEV, ARCH]
       primary_role: DEV
   ```

2. **Role Permissions**:
   ```yaml
   roles:
     - code: DEV
       permissions:
         file_patterns: ["src/**", "tests/**"]
         can_create_task_for: [DEV, TEST]
         can_transition_to: [REVIEW]
   ```

3. **Auto-Delegation via dev switch + Insights**:
   - When task completes, use `vibecollab dev` to switch to next role
   - Dynamically register skills from Insights based on current role
   - No hardcoded 48-agent preset, fully dynamic

**Non-Goals**:
- ❌ 3-tier hierarchy (Director→Lead→Specialist)
- ❌ 48-agent preset configurations
- ❌ Automatic AI delegation without human confirmation

---

### DECISION-021: Workflow Integration Strategy

**Date**: 2026-03-27
**Type**: A-level (Architecture)
**Status**: Confirmed

**Decision**:
New workflows (docs-change, feature-add, requirement-review, competitor-analysis) must be integrated into existing `plan` CLI:

```bash
# NOT separate commands
vibecollab workflow run docs-change  # ❌ Rejected

# Integrate into plan
vibecollab plan run docs-change.yaml   # ✅ Accepted
vibecollab plan run feature-add.yaml   # ✅ Accepted
```

**Rationale**:
- Avoid command proliferation
- Leverage existing PlanRunner infrastructure
- YAML-driven configuration matches VibeCollab philosophy

---

### DECISION-022: Hooks and Guards Integration

**Date**: 2026-03-27
**Type**: A-level (Architecture)
**Status**: Confirmed

**Decision**:
Implement dual-track constraint system:

**Git Hooks (FP-001)**:
- Install to `.git/hooks/`
- Trigger: pre-commit, pre-push, post-commit
- Use: Enforce hard constraints (JSON validity, TODO format, branch protection)
- CLI: `vibecollab hooks install/uninstall/run`

**Guards (FP-008)**:
- Integrate into `vibecollab check`
- Trigger: file operations (via MCP guard_check tool)
- Use: Pre/post-action protection (.meta files, Library/, Debug.Log cleanup)
- Configurable audit dimensions per project type

**Integration Point**:
Both use `project.yaml` configuration but serve different purposes:
- Hooks = Git lifecycle interception
- Guards = File operation protection

---

### DECISION-023: Commit-Type-Based Dynamic Document Sync

**Date**: 2026-03-29
**Type**: A-level (Architecture)
**Status**: Confirmed

**Problem**:
Current `vibecollab check` only verifies file modification time (24h threshold), allowing:
- Docs to drift from actual code state
- Silent inconsistencies between CONTEXT and committed features
- No enforcement that ROADMAP/DECISIONS reflect committed work

**Solution**:
Implement three-layer document-code synchronization:

**1. Linked Groups (Git Commit Level)**:
```yaml
documentation:
  consistency:
    linked_groups:
      - name: core_context
        level: git_commit  # Check commit hash sync
        files: [CONTEXT.md, CHANGELOG.md]
      - name: planning_docs
        level: git_commit
        files: [ROADMAP.md, DECISIONS.md]
```

**2. Commit-Type-Based Requirements**:
```yaml
git_workflow:
  commit_prefixes:
    - prefix: 'feat:'
      doc_requirements: [CONTEXT.md, CHANGELOG.md, QA_TEST_CASES.md]
      severity: error
    - prefix: 'config:'
      doc_requirements: []  # No docs required
      severity: info
```

**3. Dynamic Severity**:
- `error`: Block commit (feat, fix, arch)
- `warning`: Allow but warn (docs, refactor, test)
- `info`: No enforcement (config, chore)

**Rationale**:
- Context-aware: Different rules for different change types
- Workflow-aligned: Matches actual git usage patterns
- Progressive: Can bypass with `--no-verify` if needed
- Clear feedback: Explains WHY docs are required

**Implementation**:
- Pre-commit hook auto-detects prefix from staged files
- `vibecollab check` validates linked groups
- Future: `vibecollab check --strict` enforces commit-type rules

---

### DECISION-024: v0.11.0 Implementation Strategy (3/30 Sprint)

**Date**: 2026-03-30
**Type**: B-level (Implementation)
**Status**: Confirmed

**Context**:
v0.11.0 has three major features (FP-001, FP-008, Role Fix). Sprint on 3/30 implemented core modules first, deferring CLI integration for some.

**Decisions Made**:

1. **Guard Engine**: Implement `GuardEngine` as standalone domain module (`domain/guard.py`) first, defer CLI integration to next sprint. Rationale: Engine logic is independent and testable; CLI wiring requires `protocol_checker.py` refactoring.

2. **Hooks CLI**: Implement full CLI (`hooks install/uninstall/run/status/list`) immediately since `HookManager` domain module is self-contained. Both Bash and PowerShell templates generated.

3. **Role Permissions**: Implement permission methods directly in `RoleManager` (not a separate PermissionManager). Rationale: Permissions are tightly coupled to role identity; separate class would add indirection without benefit.

4. **Skill Registry**: Create `SkillRegistry` as standalone module, bridge via `RoleManager.get_skills_for_role()`. Rationale: Skill loading logic is complex enough to warrant separation, but access should be through role context.

5. **Trigger Registry**: Create `TriggerRegistry` to extract triggers from Insight tags (not from `role_skills` section). Rationale: Tags are universal and already maintained; `role_skills` requires per-insight manual curation.

**Non-goals for this sprint**:
- ❌ `vibecollab check --guards` integration
- ❌ `vibecollab role` CLI command group
- ❌ Permission enforcement in `task_manager.py`

---

### DECISION-025: Docs Markdown → YAML Big-Bang Migration (v0.12.0)

**Date**: 2026-04-01
**Type**: S-level (Strategic)
**Status**: Confirmed

**Problem**:
All 7 docs/ files (CONTEXT.md, CHANGELOG.md, DECISIONS.md, ROADMAP.md, PRD.md, QA_TEST_CASES.md, role CONTEXT.md) are Markdown. 12+ code modules parse them via fragile regex. This blocks structured Insight automation and reliable workflow integration.

**Analysis**:
Full dependency audit completed. Key findings:
- `ContextAggregator.aggregate()` returns `str` (Markdown), no schema, only 8 tests
- `RoadmapParser` already has `Milestone` dataclass — most migration-ready
- `PRDManager` already has YAML fallback in `_load()` — low risk
- `signal.py`, `indexer.py`, `protocol_checker.py` all do regex-based Markdown parsing
- Existing YAML schemas (`insight.schema.yaml`, `project.schema.yaml`) provide proven pattern

**Decision**: Big-Bang migration (Option B)

**Key Choices**:

| Item | Decision | Rationale |
|------|----------|-----------|
| Strategy | **Big-bang** (all docs at once) | Clean cut, no dual-format maintenance overhead |
| Human readability | **CLI aggregation command** — YAML is source of truth, Markdown generated on demand by `vibecollab docs render` | YAML for machines, Markdown as a view layer |
| `vibecollab init` | **Direct YAML** — init generates `.yaml` docs, no more `.md` templates | Clean break, no legacy baggage |
| ROADMAP scope | **Added to v0.12.0** — prerequisite for Workflow + Insight Automation | Structured data enables structured workflows |
| MCP Resources | **Return YAML** | Consumers get parseable structured data |
| Backward compat | **None** — breaking change, major version bump within v0.12.0 | User base is small, clean migration preferred |

**Affected Modules** (12+):
1. `domain/role.py` — ContextAggregator + RoleManager (R/W CONTEXT)
2. `domain/roadmap_parser.py` — RoadmapParser (R/W ROADMAP)
3. `domain/prd_manager.py` — PRDManager (R/W PRD)
4. `core/protocol_checker.py` — ProtocolChecker (R all docs)
5. `insight/signal.py` — InsightSignalCollector (R 4 docs via git diff)
6. `search/indexer.py` — Indexer (R 6 docs)
7. `cli/guide.py` — onboard/prompt (R role CONTEXT)
8. `cli/main.py` — CLI commands
9. `mcp/server.py` — MCP Resources
10. `templates/*.md.j2` — Pattern Engine templates
11. `schema/` — New YAML schemas required
12. `tests/` — 193+ tests need updating

**YAML Schema Design Principles**:
- Every doc file has `kind` + `version` top-level fields (following insight.schema.yaml pattern)
- Schema files in `schema/` directory
- Validation via existing YAML loading infrastructure

**Execution**: Deferred to v0.12.0 sprint. v0.11.0 completion is prerequisite.

---

### DECISION-026: v0.11.0 Milestone Completion Validation

**Date**: 2026-04-01
**Type**: B-level (Implementation)
**Status**: Confirmed

**Context**:
v0.11.0 milestone (Role-Driven Architecture + Git Hooks + Guards) reached 32/32 items complete. Final validation needed before declaring milestone closed.

**Validation Results**:

| Check | Result | Details |
|-------|--------|---------|
| Unit Tests | ✅ **151 passed** | 6 test files: guard (14), hooks (30), skills (10), permission_enforcement (14), triggers (9), role_permissions (69), 0 failures |
| `vibecollab check` | ✅ **All green** | 11 checks, 0 errors, Guard (8 rules, 227 files), Insight consistency passed |
| Protocol Compliance | ✅ **Fixed** | Created missing `docs/roles/ocarina/CONTEXT.md` |
| Documentation | ✅ **Synchronized** | skill.md, README.md, README.pypi.md, README.zh-CN.md, ROADMAP.md, CHANGELOG.md all updated |
| Task-Insight Cycle | ✅ **Complete** | TASK-DEV-029 + INS-054 (Permission testing pattern) |

**Decision**: v0.11.0 milestone is **officially complete**. Ready for PyPI release and v0.12.0 planning.

**Remaining Low-Priority Items**:
- Hook types: pre-push, post-commit (advanced extensions) — deferred, not blocking
- External QA on 3+ real projects — tracked in v0.10.0/v0.8.0 milestones

---

## Decision Archive

(None)

---
*Decision record format: see CONTRIBUTING_AI.md*
