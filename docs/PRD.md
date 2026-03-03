# VibeCollab Product Requirements Document (PRD)

This document records original requirements and requirement change history.

## Requirements List

## REQ-001: Protocol Self-Check Mechanism

**Original Description**:
> When using the protocol, we often find that during conversations we miss things — like forgetting to commit to git, or forgetting to sync a corresponding document. I think we need a skill and underlying functionality to let agents using this framework self-check whether all required protocols are fully activated, and also add trigger words for users.

**Current Description**:
> Implement protocol self-check mechanism, including:
> 1. Protocol checker module, checking Git protocol, document updates, dialogue flow protocol
> 2. CLI command `vibecollab check` to execute protocol check
> 3. Add protocol self-check section in CONTRIBUTING_AI.md
> 4. Support trigger words during dialogue for self-check

**Status**: completed
**Priority**: high
**Created**: 2026-01-21
**Updated**: 2026-01-21

**Requirement Change History**:
- **2026-01-21**: Requirement implementation completed
  - From: Original requirement description
  - To: Current description
  - Reason: Requirement implemented, including protocol checker, CLI command, documentation section, and trigger word support

---

## REQ-002: PRD Document Management

**Original Description**:
> Although we use an exploratory dialogue approach where requirements evolve through conversation, we currently lack a PRD.md to record original requirements and changes. I believe project requirements grow and change with conversations.

**Current Description**:
> Implement PRD document management system, including:
> 1. PRD manager module supporting requirement creation, updates, status management
> 2. Requirement change history tracking
> 3. Auto-create PRD.md template on project initialization
> 4. Add PRD management section in CONTRIBUTING_AI.md
> 5. Support trigger words for PRD management during dialogue

**Status**: completed
**Priority**: high
**Created**: 2026-01-21
**Updated**: 2026-01-21

**Requirement Change History**:
- **2026-01-21**: Requirement implementation completed
  - From: Original requirement description
  - To: Current description
  - Reason: Requirement implemented, including PRD manager, document template, documentation section, and trigger word support

---

## REQ-003: Event Audit Log

**Current Description**:
> Implement an append-only JSONL format event log system for tracking all project operations:
> 1. `EventLog` module supporting append + read_all
> 2. `Event` dataclass (event_type, summary, actor, payload, timestamp)
> 3. Persisted to `.vibecollab/events.jsonl`
> 4. Supports custom event types (TASK_CREATED, TASK_TRANSITIONED, DECISION, CUSTOM, etc.)

**Status**: completed
**Priority**: high
**Created**: 2026-02-24
**Updated**: 2026-02-24

---

## REQ-004: Task Lifecycle Management

**Current Description**:
> Implement task state machine management system:
> 1. `TaskManager` module supporting create/transition/list/get
> 2. State transitions: IN_PROGRESS → REVIEW → DONE, supports rollback
> 3. Change scope control (max file count/line limits)
> 4. All state changes auto-recorded to EventLog

**Status**: completed
**Priority**: high
**Created**: 2026-02-24
**Updated**: 2026-02-24

---

## REQ-005: LLM Client Integration

**Current Description**:
> Implement provider-agnostic LLM client:
> 1. `LLMClient` module supporting OpenAI-compatible API and Anthropic Claude
> 2. Environment variable config (`VIBECOLLAB_LLM_*`), zero hardcoded API keys
> 3. `build_project_context()` auto-assembles project context
> 4. Single-turn ask() + multi-turn chat() API

**Status**: completed
**Priority**: high
**Created**: 2026-02-24
**Updated**: 2026-02-24

---

## REQ-006: Three-Mode AI CLI

**Current Description**:
> Implement CLI command layer for three AI usage modes:
> 1. `vibecollab ai ask/chat` — Human-machine interaction mode
> 2. `vibecollab ai agent plan/run/serve/status` — Agent autonomous mode
> 3. Safety gates: PID singleton lock, pending-solidify check, max cycle count, adaptive backoff, circuit breaker, RSS memory limit
> 4. Coexists with IDE dialogue mode (reads CONTRIBUTING_AI.md)

**Status**: completed
**Priority**: high
**Created**: 2026-02-24
**Updated**: 2026-02-24

---

## REQ-007: Pattern Engine (Template-Driven Document Generation)

**Current Description**:
> Implement Jinja2 template-driven CONTRIBUTING_AI.md generation engine, replacing 27 hardcoded Python methods:
> 1. `PatternEngine` module, `manifest.yaml` declarative section control
> 2. 27 `.md.j2` template files, each section independently maintainable
> 3. Template Overlay mechanism: Users can customize templates and manifest in `.vibecollab/patterns/`
> 4. Condition evaluation supports `|default` syntax, manifest merge supports override/insert/exclude
> 5. Remove all legacy code from generator.py (1713 → 83 lines)

**Status**: completed
**Priority**: high
**Created**: 2026-02-24
**Updated**: 2026-02-24

---

## REQ-008: Project Health Signal Extraction

**Current Description**:
> Implement automated project health detection and scoring system:
> 1. `HealthExtractor` module extracting signals from ProtocolChecker / EventLog / TaskManager three data sources
> 2. `Signal` dataclass (name, level, category, value, message, suggestion)
> 3. `HealthReport` with score (0-100) and grade (A-F)
> 4. 10+ signal types: protocol compliance, log integrity, activity, conflicts, validation failure rate, task progress, backlog, review bottleneck, dependency blocking, load imbalance
> 5. CLI command `vibecollab health` + `--json` output

**Status**: completed
**Priority**: medium
**Created**: 2026-02-24
**Updated**: 2026-02-24

---

## REQ-009: Agent Executor (LLM Output → Actual Changes)

**Current Description**:
> Implement Agent autonomous execution capability, bridging LLM plan output to filesystem operations:
> 1. `AgentExecutor` module supporting parse → validate → apply → test → commit/rollback full cycle
> 2. JSON parsing: Extract from markdown code blocks, supports single object/array/wrapper three formats
> 3. Safety checks: Path traversal protection, protected file list, file count/size limits
> 4. Backup rollback mechanism: Auto-restore all changed files on test failure
> 5. Integrated into `agent run` and `agent serve` commands, replacing text-only output

**Status**: completed
**Priority**: high
**Created**: 2026-02-24
**Updated**: 2026-02-24

---

## REQ-010: Insight Solidification System

**Current Description**:
> Implement a solidification system that extracts reusable knowledge units from development practice (DECISION-012, S-level):
> 1. Two-layer separation architecture: Insight body (portable knowledge package) + Registry (project-level usage state)
> 2. `InsightManager` module: CRUD, Registry (weight decay/use reward), search (Jaccard × weight), provenance, consistency check
> 3. Schema definition: `schema/insight.schema.yaml` (body + Registry + Developer Tag three parts)
> 4. Developer metadata extension: tags/contributed/bookmarks written to .metadata.yaml
> 5. CLI command group `vibecollab insight`: list/show/add/search/use/decay/check/delete/bookmark/unbookmark/trace/who/stats
> 6. Consistency check integrated into `vibecollab check --insights`
> 7. SHA-256 content fingerprint + EventLog audit integration
> 8. Cross-developer sharing: get_insight_developers / get_cross_developer_stats
> 9. Provenance CLI visualization: get_full_trace + ASCII tree rendering

**Status**: completed
**Priority**: high
**Created**: 2026-02-25
**Updated**: 2026-02-25

---

## REQ-011: AI Agent Onboarding Guidance and Action Suggestions

**Current Description**:
> Implement automated guidance for AI Agent project onboarding and next-step suggestions after modifications:
> 1. `vibecollab onboard` — Output project overview, current progress, TODOs, reading list for new Agents
> 2. `vibecollab next` — Generate action suggestions based on workspace state (git diff, file mtime, linked_groups)
> 3. Evolve from passive diagnostics (check) to proactive guidance (onboard + next)
> 4. Enable Agent-mode AI to autonomously understand projects and drive development

**Status**: completed
**Priority**: high
**Created**: 2026-02-25
**Updated**: 2026-02-25

---

## REQ-012: Task-Insight Auto-Link

**Current Description**:
> Auto-search related Insight solidifications when creating Tasks, establishing direct knowledge-task links:
> 1. TaskManager.create_task() new optional insight_manager parameter
> 2. Extract keywords from feature/description/role, invoke search_by_tags for matching
> 3. Match results stored in task.metadata["related_insights"], EventLog synced
> 4. New suggest_insights() method for manual queries
> 5. New `vibecollab task create/list/show/suggest` CLI commands
> 6. Fully backward compatible (auto-skips when no InsightManager)

**Status**: completed
**Priority**: high
**Created**: 2026-02-25
**Updated**: 2026-02-25

---

## Requirements Summary

| Status | Count |
|--------|-------|
| draft | 0 |
| confirmed | 0 |
| in_progress | 0 |
| completed | 12 |
| cancelled | 0 |

---

*Last updated: 2026-02-25*
