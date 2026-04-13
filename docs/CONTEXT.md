# Context Markdown template - renders docs/context.yaml to docs/CONTEXT.md
# Project Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-02T16:00:00
> Aggregated from: architect, dev, insight_collector


## Project Overall Status
- **Version**: v0.12.4
- **Active roles**: 3 (architect, dev, insight_collector)
- **Milestone**: v0.12.0 YAML Data Layer + Workflows + Insight Automation — 25/25 items COMPLETE (v0.12.0 RELEASED)

## Role Work Status



### architect
- **Last updated**: 2026-04-13
- **Current task**: v0.12.4 RELEASED
- **Progress**: v0.12.4 RELEASED: Step-by-step workflow execution, EventLog path fix, Guard.yaml override support. All v0.12.x features complete.
- **Pending issues**: (None)
- **Next steps**: v0.13.0 planning or v1.0.0 release preparation


### dev
- **Last updated**: 2026-04-13
- **Current task**: v0.12.4 RELEASED
- **Progress**: v0.12.4 RELEASED: EventLog path nesting bug fixed, Guard.yaml override and exclude_patterns support added, insight-collect workflow enhanced with tags enumeration. All tests passing.
- **Pending issues**: MCP onboard timeout after IDE restart (moved to v0.13.0)
- **Next steps**: v0.13.0 Insight-First Ecosystem or v1.0.0 release engineering


### insight_collector
- **Last updated**: 2026-04-13
- **Current task**: v0.12.4 RELEASED
- **Progress**: v0.12.4 RELEASED: Insight-collect workflow enhanced with tags enumeration step. 60+ Insights indexed. Insight derivation chain fully operational.
- **Pending issues**: Cross-project import/export verification (v0.13.0 scope)
- **Next steps**: Insight marketplace planning for v0.13.0



## Cross-role Collaboration
See .vibecollab/roles/ for individual role contexts

## Global Technical Debt


- [dev] MCP `onboard` tool call timeout after IDE restart still needs investigation

- [dev] `README.zh-CN.md` project structure section is outdated

- [insight_collector] Semantic index staleness (no auto-update on Insight change)

- [insight_collector] Duplicate detection sensitivity threshold needs tuning



---
*This file is auto-aggregated from multi-role contexts*