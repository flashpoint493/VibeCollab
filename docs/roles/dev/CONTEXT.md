# VibeCollab - DEV Role Context

## Current Status
- **Version**: v0.12.0-dev
- **Role**: DEV (Development)
- **Last updated**: 2026-04-02

## Current Tasks
- **v0.12.0 YAML Data Layer migration** (DECISION-025/027): Docs Markdown → YAML Big-Bang
- **Next up**: `docs/*.md` → `docs/*.yaml` content migration using new schemas
- **Then**: Module rewrites (ContextAggregator, RoadmapParser, PRDManager, ProtocolChecker)

## Recently Completed
- ✅ 2026-04-02: TASK-DEV-030 — 6 YAML schemas designed and created (context, changelog, decisions, roadmap, prd, qa)
- ✅ 2026-04-02: DECISION-027 — YAML Schema Design Strategy confirmed (S-level)
- ✅ 2026-04-01: events.jsonl bug fixed (root cause: path was directory not file on Windows)
- ✅ 2026-04-01: v0.11.0 milestone complete — 32/32 items, 151 tests, all checks green
- ✅ 2026-04-01: docs/roles/ocarina/ spurious directory removed
- ✅ 2026-04-01: All v0.11.0 tasks (DEV-025~029) transitioned to DONE

## Next Steps
1. **Docs migration** — Convert docs/*.md to docs/*.yaml using schema v1
2. **ContextAggregator rewrite** — YAML in/out with typed schema
3. **RoadmapParser rewrite** — YAML native (remove regex parsing)
4. **`vibecollab docs render`** — New CLI command for YAML → Markdown view generation

## Technical Debt
- MCP `onboard` tool call timeout after IDE restart still needs investigation
- `README.zh-CN.md` project structure section is outdated

---
*This file is maintained by the DEV role agent*
