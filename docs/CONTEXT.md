# VibeCollab Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-06 17:03
> Aggregated from: architect, dev, insight_collector

## Project Overall Status
- **Version**: v1.0
- **Active roles**: 3 (architect, dev, insight_collector)

## Role Work Status

### architect
- **Last updated**: 2026-04-06
- **Current task**: v0.12.0 收尾：合并变更并提交
- **Progress**: 
  - ✅ 14 个 IDE 适配器已完成 (TASK-DEV-040/041/042/043)
  - ✅ INS-061 已创建
  - ✅ YAML Data Layer 迁移完成 (docs/ → .vibecollab/)
  - ✅ 角色目录迁移完成 (docs/roles/ → .vibecollab/roles/)
- **Pending issues**: TASK-DEV-045/046 待后续继续
- **Next steps**: 完成 v0.12.0 提交，准备发布

### dev
- **Last updated**: 2026-04-06
- **Current task**: v0.12.0 YAML Data Layer migration (DECISION-025/027): Docs Markdown → YAML Big-Bang
- **Progress**: 
  - ✅ 完成 docs/changelog.yaml → docs/CHANGELOG.md 渲染
  - ✅ 完成角色目录隔离 (docs/roles/ → .vibecollab/roles/)
  - ✅ 39 个文件变更已整理 (740+ 新增, 2353- 删除)
- **Pending issues**: MCP onboard timeout after IDE restart still needs investigation
- **Next steps**: 提交变更

### insight_collector
- **Last updated**: 2026-04-06
- **Current task**: Insight System Hardening — 持续积累
- **Progress**: 
  - Total Insights: 63 (target: 100+)
  - INS-066: 角色目录迁移经验已记录
  - INS-065: YAML Docs 目录隔离经验已记录
- **Pending issues**: Cross-project import/export verification not started
- **Next steps**: 持续监控并提炼新经验

## Cross-developer Collaboration
(See docs/developers/COLLABORATION.md for details)

## Global Technical Debt
- [dev] - MCP `onboard` tool call timeout after IDE restart still needs investigation
- [dev] - `README.zh-CN.md` project structure section is outdated
- [insight_collector] - Semantic index staleness (no auto-update on Insight change)
- [insight_collector] - Duplicate detection sensitivity threshold needs tuning
- [insight_collector] - Import fingerprint mismatch on rename strategy

---
*This file is auto-aggregated from multi-role contexts*