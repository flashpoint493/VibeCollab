# Context Markdown template - renders docs/context.yaml to docs/CONTEXT.md
# Project Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-25T14:00:00
> Aggregated from: architect, dev, insight_collector


## Project Overall Status
- **Version**: v0.12.6
- **Active roles**: 3 (architect, dev, insight_collector)
- **Milestone**: v0.12.0 YAML Data Layer + Workflows + Insight Automation — 25/25 items COMPLETE (v0.12.0 RELEASED)

## Split Package Refactoring Status

> **In Progress**: Monorepo split validation — Stage 2/3

### Completed
- [x] All 8 sub-packages extracted from main repo source (v0.12.6)
- [x] Cross-package relative imports rewritten to absolute imports
- [x] pyproject.toml generated for each sub-package with correct dependencies
- [x] Local wheel build + import validation passed for all packages
- [x] Sub-package code pushed to GitHub (main branch)

### Sub-Packages
| Package | Status | Version | PyPI Status |
|---------|--------|---------|-------------|
| vibecollab-core | ✅ Code ready | 0.12.6 | Pending local validation |
| vibecollab-insights | ✅ Code ready | 0.12.6 | Pending local validation |
| vibecollab-ide | ✅ Code ready | 0.12.6 | Pending local validation |
| vibecollab-mcp | ✅ Code ready | 0.12.6 | Pending local validation |
| vibecollab-patterns | ✅ Code ready | 0.12.6 | Pending local validation |
| vibecollab-generator | ✅ Code ready | 0.12.6 | Pending local validation |
| vibecollab-tasks | ✅ Code ready | 0.12.6 | Pending local validation |
| vibecollab-cli | ✅ Code ready | 0.12.6 | Pending local validation |

### Pending
- [ ] Local user validation of sub-package functionality
- [ ] PyPI release of v0.12.6 sub-packages
- [ ] Main repo branch switch (`refactor/modular-deps`)
- [ ] Main package dependency switch + combination validation
- [ ] Main repo v0.12.6+ release

## Role Work Status

### architect
- **Last updated**: 2026-04-25
- **Current task**: Package split architecture validation
- **Progress**: Split package structure finalized. Cross-package dependency graph resolved. Core retains domain/models/utils/i18n/contrib; insights owns search+insight; cli owns all CLI entrypoints.
- **Pending issues**: None
- **Next steps**: After user validation, approve PyPI publish + main repo modular-deps branch

### dev
- **Last updated**: 2026-04-25
- **Current task**: Split package build & import fix
- **Progress**: Automated script `scripts/fix_split_packages.py` created. All relative imports rewritten. All 8 packages build and import successfully.
- **Pending issues**: Local validation by user before PyPI upload
- **Next steps**: Await validation feedback, then proceed to main repo branch switch

### insight_collector
- **Last updated**: 2026-04-13
- **Current task**: v0.12.4 RELEASED
- **Progress**: v0.12.4 RELEASED
- **Pending issues**: Cross-project import/export verification (v0.13.0 scope)
- **Next steps**: Insight marketplace planning for v0.13.0

## Cross-role Collaboration
See .vibecollab/roles/ for individual role contexts

## Global Technical Debt

- [dev] MCP `onboard` tool call timeout after IDE restart still needs investigation
- [dev] `README.zh-CN.md` project structure section is outdated
- [dev] Sub-package code duplication between vibecollab-core and vibecollab-tasks (task_manager, event_log, role, roadmap_parser, prd_manager) — acceptable for backward compat during transition
- [insight_collector] Semantic index staleness (no auto-update on Insight change)
- [insight_collector] Duplicate detection sensitivity threshold needs tuning

---
*This file is auto-aggregated from multi-role contexts*
