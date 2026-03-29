# VibeCollab Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-03-29
> Aggregated from: dev, insight_collector, architect

## Project Overall Status

- **Version**: v0.10.14 (In Progress)
- **Active Roles**: 3 (dev, insight_collector, architect)
- **Total Insights**: 39 indexed (341 vectors)
- **Current Focus**: Git Hooks + Dynamic Document Sync

## Recent Milestones

### v0.10.14 (In Progress) - Git Hooks + Dynamic Check

**Completed:**
- ✅ Pre-commit hook: Auto-runs `vibecollab check` before every commit
- ✅ Linked groups: Git commit level consistency check (core_context, planning_docs, qa_sync)
- ✅ Commit-type-based dynamic check: Context-aware document requirements
  - feat/fix/arch: error level (blocks commit if docs missing)
  - docs/refactor: warning level
  - config/chore: info level (no docs required)
- ✅ 39 insights created (INS-036 ~ INS-043)
- ✅ Documentation: README.md, skill.md, CHANGELOG.md, ROADMAP.md all updated

**Active Tasks:**
- TASK-DEV-025: Git Hooks Framework (Core Implementation ✅)
- TASK-DEV-026: Guard Protection Engine (Pattern Defined ✅)
- TASK-DEV-027: Role-Driven Architecture Fix (Waiting)
- TASK-DEV-028: v0.10.x Release Engineering (Documentation ✅)

## Role Work Status

### dev
- **Last updated**: 2026-03-29
- **Current task**: Git Hooks Framework implementation and dynamic check system
- **Progress**: Pre-commit hooks working, commit-type rules configured
- **Pending issues**: Windows file lock on events.jsonl
- **Next steps**: Role-driven architecture implementation

### insight_collector
- **Last updated**: 2026-03-29
- **Current task**: Knowledge capture and insight indexing
- **Progress**: 39 insights indexed (341 vectors)
- **Pending issues**: None
- **Next steps**: Continue insight accumulation

### architect
- **Last updated**: 2026-03-29
- **Current task**: System design for role-driven architecture
- **Progress**: Migration pattern defined (INS-038)
- **Pending issues**: None
- **Next steps**: Implement role-based permission system

## Cross-role Collaboration

- **Linked Groups**: 3 groups configured for git commit sync
  - core_context: CONTEXT + CHANGELOG (strict sync)
  - planning_docs: ROADMAP + DECISIONS (strict sync)
  - qa_sync: QA_TEST_CASES (feature sync)

- **Commit Rules**: 10 prefixes configured with doc requirements
  - feat: CONTEXT + CHANGELOG + QA (error)
  - fix: CHANGELOG + QA (error)
  - arch: ROADMAP + DECISIONS + CONTEXT (error)
  - docs/refactor: warning level
  - config/chore: info level

## Technical Debt

### High Priority
- [dev] Windows file lock issue on events.jsonl
- [dev] MCP onboard tool timeout after IDE restart

### Medium Priority
- [docs] README.zh-CN.md project structure section outdated
- [dev] dev role .metadata.yaml missing

### Low Priority
- [dev] CONTEXT.md auto-aggregation refresh needed

## Recent Commits (Last 5)

1. `6069757` - feat: Implement commit-type-based dynamic document sync check
2. `3046397` - docs: Add Git Hooks documentation and update setup flow
3. `d7b58b7` - docs: Demonstrate error blocking in pre-commit hook
4. `17a0826` - fix: Correct fingerprint calculation for all INS-001~INS-040
5. `5e9159c` - feat: INS-039 Git Hooks Framework + pre-commit implementation

---
*This file is auto-aggregated from multi-role contexts*
*Updated: 2026-03-29*
