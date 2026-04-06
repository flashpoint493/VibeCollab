# VibeCollab Global Context

> ⚠️ **This file is auto-generated, do not edit manually**
> Last updated: 2026-04-02 23:47:05
> Aggregated from: architect, dev, insight_collector

## Project Overall Status
- **Version**: v1.0
- **Active roles**: 3 (architect, dev, insight_collector)

## Role Work Status

### architect
- **Last updated**: 2026-04-02
- **Current task**: TASK-DEV-045/046: KimiCode 适配器实现 + OpenCode 验证增强 (多 Agent 并行)
- **Progress**: v0.12.0 Universal IDE Adapter 当前状态：
- ✅ 14 个 IDE 适配器已完成 (TASK-DEV-040/041/042/043)
- ✅ INS-061 已创建 (
- **Pending issues**: TASK-DEV-045 IN_PROGRESS: KimiCode 适配器实现 (research + dev); TASK-DEV-046 IN_PROGRESS: OpenCode 适配器验证增强
- **Next steps**: (None)

### dev
- **Last updated**: 2026-04-02
- **Current task**: v0.12.0 YAML Data Layer migration (DECISION-025/027): Docs Markdown → YAML Big-Bang
- **Progress**: (None)
- **Pending issues**: MCP onboard timeout after IDE restart still needs investigation
- **Next steps**: (None)

### insight_collector
- **Last updated**: 2026-04-01
- **Current task**: Insight System Hardening — External project validation pending
- **Progress**: Key Metrics:
- Total Insights: 55 (target: 100+)
- Avg Weight: 0.95 (target: > 1.0)
- Semantic Cover
- **Pending issues**: Cross-project import/export verification not started; External project A/B/C validation not started
- **Next steps**: (None)

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