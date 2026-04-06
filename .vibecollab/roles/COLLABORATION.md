# VibeCollab Project Collaboration Document

> This document records role assignments, task workflows, and collaboration rules between AI agents

**Last updated**: 2026-03-05
**Active roles**: DEV (primary), ARCH, PM, QA, TEST, DESIGN (available)

---

## Role Registry

| Role Code | Name | Focus | Gatekeeper | Status |
|-----------|------|-------|------------|--------|
| DEV | Development | implementation, bug fixing | No | Active |
| ARCH | Architecture | infrastructure, performance, extensibility | No | Available |
| PM | Project Management | milestones, priorities, progress | No | Available |
| QA | Quality Assurance | acceptance testing, UX validation, edge cases | Yes | Available |
| TEST | Unit Testing | code testing, coverage, automated testing | No | Available |
| DESIGN | Product Design | requirements, experience, interaction | No | Available |

> Roles are loaded from `project.yaml` → `roles` section. Each role directory under `docs/developers/{code}/` contains a `CONTEXT.md` and `.metadata.yaml` with role-specific rules.

---

## Task Workflow

Agents switch roles via `vibecollab dev switch {role_code}` to adopt the corresponding focus areas, triggers, and gatekeeper rules. The role's `.metadata.yaml` provides context for task routing:

1. **DEV** handles implementation tasks (TASK-DEV-*)
2. **QA** gates acceptance — is_gatekeeper=true means QA approval is required before DONE
3. **PM** manages milestones and priorities
4. **ARCH** reviews architecture decisions (S/A level)
5. **TEST** ensures code coverage and automated testing
6. **DESIGN** clarifies requirements and interaction design

---

## Collaboration Agreements

### Communication Rules
1. **API interface changes**: Must be recorded in COLLABORATION.md
2. **Architecture decisions**: Must be recorded in docs/DECISIONS.md
3. **Task dependencies**: Check dependency tasks from other roles before completing

### Code Standards
1. **Pre-commit check**: Run `pytest tests/` to ensure tests pass
2. **Context sync**: Run `vibecollab dev sync` at end of each conversation

### Documentation Maintenance
1. **Role CONTEXT.md**: Maintained by each role agent individually
2. **Global CONTEXT.md**: Auto-aggregated by the system, do not edit manually
3. **COLLABORATION.md**: Records role collaboration relationships

---

*This document is maintained by the team, recording collaboration relationships between roles*
