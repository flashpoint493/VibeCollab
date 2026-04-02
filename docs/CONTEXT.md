# Context Markdown template - renders docs/context.yaml to docs/CONTEXT.md
# VibeCollab Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-02T15:30:00
> Aggregated from: architect, dev, insight_collector


## Project Overall Status
- **Version**: v0.12.0-dev
- **Active roles**: 3 (architect, dev, insight_collector)
- **Milestone**: v0.12.0 YAML Data Layer + Workflows + Insight Automation — 22/25 items (88% complete, remaining: test updates)

## Role Work Status



### architect
- **Last updated**: 2026-04-02
- **Current task**: v0.12.0 YAML Data Layer architecture review (DECISION-025/027)
- **Progress**: All major features implemented. 22/25 items complete. Template migration, Workflow Integration, Insight Derivation Chain all done.
- **Pending issues**: (None)
- **Next steps**: Final review and v0.12.0 release preparation


### dev
- **Last updated**: 2026-04-02
- **Current task**: v0.12.0 completion (TASK-DEV-030~036)
- **Progress**: TASK-DEV-030~036 DONE. 24 YAML templates created, Workflow Integration with 3 pre-built workflows, Insight Derivation Chain with graph visualization. 1731 tests passing.
- **Pending issues**: MCP onboard timeout after IDE restart
- **Next steps**: Final test updates and v0.12.0 release


### insight_collector
- **Last updated**: 2026-04-02
- **Current task**: Insight Derivation Chain implementation (FP-015)
- **Progress**: FP-015 complete: derived_from field, insight graph --show-derivation, automatic derivation detection. 58 Insights indexed.
- **Pending issues**: Cross-project import/export verification not started
- **Next steps**: Insight quality validation for v0.12.0



## Cross-role Collaboration
See docs/roles/ for individual role contexts

## Global Technical Debt


- [dev] MCP `onboard` tool call timeout after IDE restart still needs investigation

- [dev] `README.zh-CN.md` project structure section is outdated

- [insight_collector] Semantic index staleness (no auto-update on Insight change)

- [insight_collector] Duplicate detection sensitivity threshold needs tuning



---
*This file is auto-aggregated from multi-role contexts*