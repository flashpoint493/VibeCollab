# VibeCollab Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-01 14:44:00
> Aggregated from: architect, dev, insight_collector

## Project Overall Status
- **Version**: v0.11.0
- **Active roles**: 3 (architect, dev, insight_collector)
- **Milestone**: v0.11.0 Role-Driven Architecture + Git Hooks + Guards — **32/32 items complete** ✅

## Role Work Status

### architect
- **Last updated**: 2026-04-01
- **Current task**: Role-Driven Architecture design (DECISION-020) — Core implemented ✅
- **Progress**: v0.11.0 architecture decisions complete (DECISION-019~025)
- **Pending issues**: Guard + Hooks unified configuration design refinement
- **Next steps**: v0.12.0 YAML Data Layer architecture (DECISION-025)

### dev
- **Last updated**: 2026-04-01
- **Current task**: v0.11.0 milestone completion — All 32/32 items done ✅
- **Progress**: 151 tests across 6 test files, `vibecollab check` all green
- **Pending issues**: events.jsonl Windows file lock, MCP onboard timeout after IDE restart
- **Next steps**: External QA on 3+ real projects, UX verification on Windows

### insight_collector
- **Last updated**: 2026-04-01
- **Current task**: Insight System Hardening — External project validation pending
- **Progress**: 54 Insights indexed, Trigger Registry + Skill Registry operational
- **Pending issues**: Cross-project import/export verification not started
- **Next steps**: External project A/B/C validation (TASK-INS-001~005)

### ocarina
- **Last updated**: 2026-04-01
- **Current task**: No active tasks
- **Progress**: Protocol compliance resolved (CONTEXT.md created)
- **Pending issues**: (None)
- **Next steps**: (None)

## Cross-role Collaboration
(See docs/roles/ for individual role contexts)

## Global Technical Debt
- [dev] `events.jsonl` Windows file lock issue still needs investigation
- [dev] MCP `onboard` tool call timeout after IDE restart still needs investigation
- [dev] `README.zh-CN.md` project structure section is outdated
- [insight_collector] Semantic index staleness (no auto-update on Insight change)
- [insight_collector] Duplicate detection sensitivity threshold needs tuning

---
*This file is auto-aggregated from multi-role contexts*