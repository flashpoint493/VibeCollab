# VibeCollab Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-02 13:11:00
> Aggregated from: architect, dev, insight_collector

## Project Overall Status
- **Version**: v0.12.0-dev
- **Active roles**: 3 (architect, dev, insight_collector)
- **Previous milestone**: v0.11.0 Role-Driven Architecture + Git Hooks + Guards — **32/32 items complete** ✅
- **Current milestone**: v0.12.0 YAML Data Layer + Workflows + Insight Automation — **1/40 items** (TASK-DEV-030 schema design done)

## Role Work Status

### architect
- **Last updated**: 2026-04-02
- **Current task**: v0.12.0 YAML Data Layer architecture (DECISION-025/027)
- **Progress**: Schema design principles confirmed, 6 schemas created
- **Pending issues**: (None)
- **Next steps**: Review module rewrite sequence for v0.12.0

### dev
- **Last updated**: 2026-04-02
- **Current task**: v0.12.0 Docs Markdown → YAML migration
- **Progress**: TASK-DEV-030 DONE (6 YAML schemas: context, changelog, decisions, roadmap, prd, qa). events.jsonl bug fixed (was directory, now file).
- **Pending issues**: MCP onboard timeout after IDE restart
- **Next steps**: `docs/*.md` → `docs/*.yaml` full migration, then module rewrites (ContextAggregator, RoadmapParser, PRDManager)

### insight_collector
- **Last updated**: 2026-04-01
- **Current task**: Insight System Hardening — External project validation pending
- **Progress**: 55 Insights indexed (INS-055: YAML Schema Design Pattern), Trigger Registry + Skill Registry operational
- **Pending issues**: Cross-project import/export verification not started
- **Next steps**: External project A/B/C validation

## Cross-role Collaboration
(See docs/roles/ for individual role contexts)

## Global Technical Debt
- [dev] MCP `onboard` tool call timeout after IDE restart still needs investigation
- [dev] `README.zh-CN.md` project structure section is outdated
- [insight_collector] Semantic index staleness (no auto-update on Insight change)
- [insight_collector] Duplicate detection sensitivity threshold needs tuning
- ~~[dev] `events.jsonl` Windows file lock~~ — **RESOLVED** (root cause: path was a directory not file)

---
*This file is auto-aggregated from multi-role contexts*
