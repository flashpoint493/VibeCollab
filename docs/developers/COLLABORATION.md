# VibeCollab Project Collaboration Document

> This document records collaboration relationships, task assignments, and dependencies between multiple developers

**Last updated**: 2026-03-04
**Active developers**: ocarina (lead), alice (paused)

---

## Developer Status

| Developer | Status | Last Active | Focus Area |
|-----------|--------|-------------|------------|
| ocarina | Active | 2026-03-04 | v0.10.3 release engineering, MCP, i18n |
| alice | Paused | 2026-02-25 | CLI developer switch (v0.5.4) |

---

## Completed Milestones

| Milestone | Version | Lead | Status |
|-----------|---------|------|--------|
| Multi-developer support | v0.5.0 | ocarina | ✅ |
| Conflict detection | v0.5.1 | ocarina | ✅ |
| CLI developer switch | v0.5.4 | alice | ✅ |
| Insight solidification system | v0.7.0 | ocarina | ✅ |
| MCP Server + IDE integration | v0.9.1 | ocarina | ✅ |
| ROADMAP ↔ Task integration | v0.9.5 | ocarina | ✅ |
| Code i18n | v0.10.1 | ocarina | ✅ |
| Docs bilingual | v0.10.2 | ocarina | ✅ |

---

## Collaboration Agreements

### Communication Rules
1. **API interface changes**: Must be recorded in COLLABORATION.md and all relevant developers notified
2. **Architecture decisions**: Must be recorded in docs/DECISIONS.md
3. **Task dependencies**: Check for dependency tasks from other developers before completing a task

### Code Standards
1. **Pre-commit check**: Run `pytest tests/` to ensure tests pass
2. **Conflict detection**: Run `vibecollab dev conflicts` to check for potential conflicts
3. **Context sync**: Run `vibecollab dev sync` at the end of each conversation

### Documentation Maintenance
1. **Personal CONTEXT.md**: Maintained by each developer individually
2. **Global CONTEXT.md**: Auto-aggregated by the system, do not edit manually
3. **COLLABORATION.md**: Maintained jointly by the team, records collaboration relationships

---

*This document is jointly maintained by the team, recording collaboration relationships between developers*
