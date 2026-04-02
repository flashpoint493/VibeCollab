# Context Markdown template - renders docs/context.yaml to docs/CONTEXT.md
# VibeCollab Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-02T14:00:00
> Aggregated from: architect, dev, insight_collector


## Project Overall Status
- **Version**: v0.12.0-dev
- **Active roles**: 3 (architect, dev, insight_collector)
- **Milestone**: v0.12.0 YAML Data Layer + Workflows + Insight Automation — 12/25 items (core infrastructure done)

## Role Work Status



### architect
- **Last updated**: 2026-04-02
- **Current task**: v0.12.0 YAML Data Layer architecture (DECISION-025/027)
- **Progress**: v0.12.0 core infrastructure complete, reviewing remaining work
- **Pending issues**: (None)
- **Next steps**: Review module rewrite sequence for v0.12.0


### dev
- **Last updated**: 2026-04-02
- **Current task**: v0.12.0 YAML Data Layer implementation (TASK-DEV-030~034)
- **Progress**: TASK-DEV-030~034 DONE. YAML Data Layer core complete. 1677 tests passing.
- **Pending issues**: MCP onboard timeout after IDE restart
- **Next steps**: docs/*.md → docs/*.yaml full migration, then module rewrites (ContextAggregator, RoadmapParser, PRDManager)


### insight_collector
- **Last updated**: 2026-04-01
- **Current task**: Insight System Hardening — External project validation pending
- **Progress**: 55 Insights indexed, Trigger Registry + Skill Registry operational
- **Pending issues**: Cross-project import/export verification not started
- **Next steps**: External project A/B/C validation



## Cross-role Collaboration
See docs/roles/ for individual role contexts

## Global Technical Debt


- [dev] MCP `onboard` tool call timeout after IDE restart still needs investigation

- [dev] `README.zh-CN.md` project structure section is outdated

- [insight_collector] Semantic index staleness (no auto-update on Insight change)

- [insight_collector] Duplicate detection sensitivity threshold needs tuning



---
*This file is auto-aggregated from multi-role contexts*