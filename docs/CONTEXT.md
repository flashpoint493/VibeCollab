# Context Markdown template - renders docs/context.yaml to docs/CONTEXT.md
# Project Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-25T14:30:00
> Aggregated from: architect, dev, insight_collector


## Project Overall Status
- **Version**: v0.12.6
- **Active roles**: 3 (architect, dev, insight_collector)
- **Milestone**: v0.12.0 YAML Data Layer + Workflows + Insight Automation — 25/25 items COMPLETE (v0.12.0 RELEASED)

## Role Work Status



### architect
- **Last updated**: 2026-04-25
- **Current task**: Package split architecture validation
- **Progress**: Split package structure finalized. Cross-package dependency graph resolved. Core retains domain/models/utils/i18n/contrib; insights owns search+insight; cli owns all CLI entrypoints.
- **Pending issues**: (None)
- **Next steps**: After user validation, approve PyPI publish + main repo modular-deps branch


### dev
- **Last updated**: 2026-04-25
- **Current task**: Split package build & import fix
- **Progress**: Automated script scripts/fix_split_packages.py created. All relative imports rewritten. All 8 packages build and import successfully. Code pushed to GitHub.
- **Pending issues**: Local validation by user before PyPI upload
- **Next steps**: Await validation feedback, then proceed to main repo branch switch


### insight_collector
- **Last updated**: 2026-04-13
- **Current task**: v0.12.4 RELEASED
- **Progress**: v0.12.4 RELEASED: Insight-collect workflow enhanced with tags enumeration step. 60+ Insights indexed. Insight derivation chain fully operational.
- **Pending issues**: Cross-project import/export verification (v0.13.0 scope)
- **Next steps**: Insight marketplace planning for v0.13.0



## Cross-role Collaboration
See .vibecollab/roles/ for individual role contexts

## Global Technical Debt


- [dev] MCP onboard tool call timeout after IDE restart still needs investigation

- [dev] README.zh-CN.md project structure section is outdated

- [dev] Sub-package code duplication between vibecollab-core and vibecollab-tasks (task_manager, event_log, role, roadmap_parser, prd_manager) — acceptable for backward compat during transition

- [insight_collector] Semantic index staleness (no auto-update on Insight change)

- [insight_collector] Duplicate detection sensitivity threshold needs tuning



---
*This file is auto-aggregated from multi-role contexts*