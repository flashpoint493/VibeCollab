# VibeCollab Roadmap

## Current Project Lifecycle Stage

**Stage**: Prototype Validation (demo)
**Start Date**: 2026-01-20
**Stage Description**: Rapidly validate core concepts and feasibility

### Stage Focus
- Rapid iteration
- Concept validation
- Core features

### Stage Principles
- Fail fast, adjust fast
- Prioritize core features, defer optimization
- Technical debt acceptable, but must be documented
- Detailed Git development iteration records
- Record important decisions in DECISIONS.md
- Establish CI/CD

### Current Stage Milestones
- v0.4.3 (completed)
- v0.5.0 (completed) - Multi-developer support
- v0.5.1 (completed) - Conflict detection
- v0.5.4 (completed) - CLI developer switch
- v0.5.5 (completed) - EventLog audit trail
- v0.5.6 (completed) - TaskManager validate-solidify-rollback
- v0.5.7 (completed) - LLM Client (CLI + API Key)
- v0.5.8 (completed) - AI CLI three-mode architecture (ask/chat/agent)
- v0.5.9 (completed) - Pattern Engine + Template Overlay
- v0.6.0 (completed) - Protocol maturity + test coverage enhancement

---

## Completed Milestones

### Phase 2 - Multi-Developer Support (v0.5.0 - v0.5.1)

#### v0.5.9 - Pattern Engine + Template Overlay (2026-02-24)
- [x] PatternEngine: Jinja2 templates + manifest.yaml declarative engine
- [x] 27 .md.j2 templates replace hardcoded _add_*() methods
- [x] Template Overlay: .vibecollab/patterns/ local override mechanism
- [x] Legacy removal: generator.py 1713→83 lines
- [x] DECISION-011: Pattern Engine architecture
- [x] 40 PatternEngine tests (including 8 Overlay tests), full 215 tests zero regression

#### v0.5.8 - AI CLI Three-Mode Architecture (2026-02-24)
- [x] vibecollab ai ask / chat — Human-machine interaction CLI
- [x] vibecollab ai agent plan / run / serve — Agent autonomous mode
- [x] Safety gates: PID lock, pending-solidify, max cycles, adaptive backoff, circuit breaker, memory threshold
- [x] DECISION-010: Three-mode architecture
- [x] 32 unit tests, full 174 tests zero regression

#### v0.5.7 - LLM Client (2026-02-24)
- [x] LLMClient: OpenAI + Anthropic dual provider support
- [x] Environment variable config (VIBECOLLAB_LLM_*)
- [x] build_project_context() auto context assembly
- [x] httpx optional dependency (pip install vibe-collab[llm])
- [x] 30 unit tests, full 142 tests zero regression

#### v0.5.6 - TaskManager Validate-Solidify-Rollback (2026-02-24)
- [x] Task dataclass + TaskStatus state machine
- [x] TaskManager: CRUD + transition + validate + solidify + rollback
- [x] EventLog integration: every operation auto-logs events
- [x] Atomic JSON persistence (.vibecollab/tasks.json)
- [x] 53 unit tests, full 112 tests zero regression
- [x] Cross-module integration verification (TaskManager + EventLog)

#### v0.5.5 - EventLog Audit Trail (2026-02-24)
- [x] Append-only JSONL event log (event_log.py)
- [x] 17 event types, SHA-256 content fingerprint
- [x] Atomic append, query API, integrity verification
- [x] 24 unit tests, full 59 tests zero regression
- [x] DECISION-009 architectural pattern borrowing confirmed (Direction B)

#### v0.5.4 - CLI Developer Switch (2026-02-24)
- [x] `vibecollab dev switch` command
- [x] Persistent switch state (.vibecollab.local.yaml)
- [x] `vibecollab dev whoami` shows identity source

#### v0.5.1 - Conflict Detection (2026-02-10)
- [x] Cross-developer conflict detection algorithm
- [x] CLI command `vibecollab dev conflicts`
- [x] CONTRIBUTING_AI.md multi-developer collaboration protocol section
- [x] Documentation and usage examples

#### v0.5.0 - Multi-Developer Support (2026-02-10)
- [x] Architecture design and decision confirmed (DECISION-008)
- [x] Automatic developer identity recognition (Git username)
- [x] Independent developer CONTEXT.md management
- [x] Global CONTEXT.md auto-aggregation
- [x] Developer collaboration document (COLLABORATION.md)
- [x] CLI command extension (`vibecollab dev *`)
- [x] Project config extension (multi_developer)
- [x] Single-developer project migration support
- [x] Complete unit test verification

### Phase 1 - Core Feature Completion (v0.1.0 - v0.4.3)

#### Objectives
- [x] Project initialization and CLI implementation
- [x] YAML config-driven generation
- [x] Domain extension mechanism
- [x] Decision level system
- [x] Requirement clarification protocol
- [x] Git check and initialization
- [x] Project lifecycle management
- [x] Protocol self-check mechanism
- [x] PRD document management
- [x] Windows encoding compatibility

#### Completion Date
2026-01-20 to 2026-02-10

---

## Completed Milestone: v0.6.0 - Protocol Maturity + CI/CD ✅

### Objective
Borrow mature architectural patterns to enhance protocol robustness, improve development processes (DECISION-009)

### Core Features
- [x] EventLog append-only audit trail (Iteration 1 ✅)
- [x] TaskManager validate-solidify-rollback (Iteration 2 ✅)
- [x] Pattern Engine — Jinja2 template-driven + Template Overlay (Iteration 3 ✅)
- [x] Legacy code removal — generator.py 1713→83 lines (Iteration 3 ✅)
- [x] Establish CI/CD pipeline (GitHub Actions) ✅
- [x] Health Signal Extractor — Project health signal extraction (Iteration 4 ✅)
- [x] Agent Executor — LLM plan actual execution (file write/test/git commit) ✅
- [x] Ruff lint full fix ✅
- [x] Automated test coverage reporting ✅
- [x] Test coverage increase (58%→68%, +74 tests) ✅

### Completion Date
2026-02-24

---

## Future Milestones

### ~~v0.7.0 - Web UI~~ ❌ Cut (DECISION-012)
> Decision: Web UI is not a core competency, no resources invested. Resources redirected to experience system.

### v0.7.0 - Insight Solidification System (Completed ✅)
- [x] Insight Schema design (body + Registry + Developer Tag three parts) ✅
- [x] InsightManager core module (CRUD / Registry / search / provenance / consistency check) ✅
- [x] InsightManager unit tests (62 tests) ✅
- [x] developer.py unit test completion (67 tests) ✅
- [x] Developer metadata extension (tags / contributed / bookmarks + 21 tests) ✅
- [x] CLI command encapsulation (`vibecollab insight list/show/add/search/use/decay/check/delete` + 21 tests) ✅
- [x] Cross-developer sharing + provenance CLI visualization (bookmark/unbookmark/trace/who/stats + 24 tests) ✅
- [x] Consistency check integrated into `vibecollab check --insights` ✅
- [x] Document consistency check enhancement (linked_groups three-level check + configurable threshold) ✅
- [x] Agent guidance commands `vibecollab onboard` + `vibecollab next` ✅
- [x] Technical debt cleanup (version number unification v0.7.0-dev, project name VibeCollab, REQ-010→completed) ✅
- [x] protocol_checker multi-developer dynamic discovery (filesystem scan replaces static config) ✅

### v0.7.1 - Task-Insight Auto-Link (Completed ✅)
- [x] TaskManager.create_task() auto-searches related Insights ✅
- [x] _extract_search_tags(): Extract keywords from feature/description/role ✅
- [x] _find_related_insights(): Jaccard × weight matching + metadata storage ✅
- [x] suggest_insights(): Insight recommendations for existing tasks ✅
- [x] CLI `vibecollab task create/list/show/suggest` ✅
- [x] EventLog records linked Insights ✅
- [x] Backward compatible (auto-skips when no InsightManager) ✅
- [x] 28 unit tests (including CLI + integration + backward compatibility) ✅

### v0.8.0 - Stability Verification + Generality Stress Testing (In Development)
> Objective: Before v1.0, broadly test and harden advanced features in real-world scenarios

#### Config Management System ✅
- [x] Three-layer config architecture (env > ~/.vibecollab/config.yaml > defaults) ✅
- [x] `vibecollab config setup` interactive wizard ✅
- [x] `vibecollab config show/set/path` commands ✅
- [x] `resolve_llm_config()` unified resolution + LLMConfig three-layer integration ✅
- [x] Lightweight .env parsing (VIBECOLLAB_* prefix) ✅
- [x] 38 unit tests ✅

#### Test Coverage Increase
- [x] Full test coverage ≥ 80% (81% ✅)
- [x] Agent mode E2E tests (35 tests: executor + cli_ai full chain ✅)
- [x] LLM Client mock integration tests (26 tests: OpenAI + Anthropic dual provider ✅)
- [x] CLI command full E2E tests (48/48 subcommands CliRunner coverage ✅)

#### Agent Mode Stability ✅
- [x] agent serve long-running stress test (100+ cycles, backoff/circuit breaker/memory threshold) ✅
- [x] Concurrency safety verification (PID lock, file lock contention) ✅
- [x] agent run failure recovery scenarios (test rollback, network timeout, LLM rejection) ✅
- [x] Adaptive backoff algorithm boundary condition tests ✅

#### Insight System Generality ✅
- [x] Large-scale Insight stress test (100+ insights search/decay performance) ✅
- [ ] Cross-project Insight portability verification (export→import→maintain integrity) — Deferred, needs export/import API
- [x] Task-Insight link accuracy assessment (Chinese/English mixed, long text, boundary input) ✅
- [x] Decay/reward long-running simulation (weight distribution reasonableness after multiple decay rounds) ✅

#### Insight Integration into IDE Dialogue Mode ✅
- [x] `27_insight_workflow.md.j2` experience solidification workflow template section ✅
- [x] Dialogue end flow adds "experience solidification check" step ✅
- [x] `vibecollab next` command adds Insight solidification hints (5 signal types) ✅
- [x] manifest.yaml registration + condition switch (`insight.enabled|true`) ✅
- [x] 16 unit tests (solidification hint logic 11 + template rendering 5) ✅

#### Human-Machine Interaction Quality
- [x] vibecollab ai ask/chat Unicode compatibility across terminal environments ✅ `_compat.py` unified compatibility layer
- [x] **`vibecollab prompt` command** ✅ — LLM context prompt generator, replaces manually copying CONTRIBUTING_AI.md
  - `_collect_project_context()` shared function + `_extract_md_sections()` + `_build_prompt_text()`
  - `--compact` / `--copy` / `--sections` / `-d` four modes
  - 23 unit tests, 956/956 passed
- [x] **Protocol Checker watch_files mechanism** ✅ — DECISIONS.md/PRD.md follow-up check + max_inactive_hours configurable
- [ ] Rich panel rendering verification on Windows PowerShell/CMD/WSL — Needs manual testing
- [ ] onboard/next output quality on large projects (multi-developer, many files) — Needs manual testing
- [x] Error message friendliness audit (all CLI command exception paths) ✅ Audit complete + insight error handling enhanced

#### Generality Verification
- [ ] Run `vibecollab init` + `generate` + `check` on 3+ real external projects
- [ ] Different Python version compatibility (3.9 / 3.10 / 3.11 / 3.12 / 3.13) — CI configured, pending push verification
- [ ] Different OS compatibility (Windows / macOS / Linux)
- [x] Minimal project (empty project.yaml) and complex project (full config) boundary tests ✅ 15 tests

#### Documentation & Quality
- [ ] QA_TEST_CASES.md full update (covering v0.7.x new features)
- [x] README.md update (install/quickstart/feature list sync) ✅ Project structure/test counts/version history synced
- [x] Known issues zeroed or marked deferred ✅

#### Positioning Decisions
- [x] **`vibecollab ai` marked experimental** ✅ — VibeCollab positioned as protocol management tool, not building LLM runtime. Tool Use delegated to Cline/Cursor/Aider. `ai ask/chat/agent` retained but frozen, no further investment
- [x] **Insight read path planning** ✅ — Not injected in `build_project_context()`, instead guided via protocol (CONTRIBUTING_AI.md) for Cline/Cursor to call `vibecollab insight search` at the right time

## v0.8.x+ Subsequent Development Plan

> **Core direction**: VibeCollab positioned as **protocol management tool + structured knowledge engine**, not building LLM runtime.
> Subsequent versions focus on two main lines: **MCP/IDE integration** and **documentation & release**.

### v0.9.0 - Semantic Search Engine (Insight/Document Vectorization)

> Objective: Enable semantic search for Insights and project documents, replacing pure tag Jaccard matching

#### Document/Code Vectorization
- [x] `Embedder` module — Lightweight embedding abstraction layer ✅
  - Supports OpenAI `text-embedding-3-small` / local `sentence-transformers` dual backend
  - Pure Python trigram hash fallback (zero external dependencies)
  - Optional dependency `pip install vibe-collab[embedding]`
- [x] `VectorStore` module — Local persistent vector storage ✅
  - SQLite + pure Python cosine similarity (zero external dependency approach)
  - struct pack/unpack vector blob storage
  - Storage path `.vibecollab/vectors/`
- [x] `vibecollab index` command — Index project documents ✅
  - Incremental indexing of `CONTRIBUTING_AI.md`, `CONTEXT.md`, `DECISIONS.md`, `ROADMAP.md`, `PRD.md`, `CHANGELOG.md`
  - Insight YAML full indexing (title + body + tags, supports structured dict body)
  - `--rebuild` mode: Clear old index then rebuild
  - `--backend` select embedding backend
  - Code file optional indexing (docstring / function signatures) — Deferred
  - `--watch` mode: Auto-rebuild on file changes — Deferred

#### Semantic Search Integration
- [x] `vibecollab insight search --semantic` enhancement ✅
  - Vector cosine similarity based Insight semantic search
  - Pure tag search remains default (zero dependency compatible)
  - Hybrid retrieval (tag Jaccard + vector cosine → weighted fusion ranking) — Deferred
- [x] `vibecollab search` new command — Global semantic search ✅
  - Cross Insight / document unified search
  - Output includes source and relevance score
  - `--type` filter source type, `--min-score` threshold filter
- [x] `onboard` enhancement — Semantically match current task related Insights ✅
  - Extract current task description from CONTEXT.md / developer context → vector search Top-N related Insights
  - Rich panel + JSON output dual format support
  - 11 unit tests

### v0.9.1 - MCP Server + AI IDE Integration

> Objective: Make VibeCollab the "protocol backend" for Cline/Cursor/CodeBuddy etc.,
> from "manual copy-paste" to "IDE auto-reads protocol"

#### MCP Server (Model Context Protocol) ✅
- [x] `vibecollab mcp serve` — Standard MCP Server implementation ✅
  - Tool exposure: `insight_search`, `insight_add`, `task_list`, `check`, `next`, `onboard`, `search_docs`, `project_prompt`, `developer_context`
  - Resource exposure: `CONTRIBUTING_AI.md`, `CONTEXT.md`, `DECISIONS.md`, `ROADMAP.md`, `CHANGELOG.md`, Insight list
  - Prompt exposure: `start_conversation` dialogue start context injection template
- [x] MCP CLI command group ✅
  - `vibecollab mcp config --ide cursor/cline/codebuddy` output config
  - `vibecollab mcp inject --ide all` auto-inject IDE config files
  - Supports `stdio` and `sse` two transport modes
- [x] PyPI v0.9.1 release ✅ — `pip install vibe-collab`
- [x] CodeBuddy Rule integration ✅ — `.codebuddy/rules/vibecollab-protocol.mdc`
- [x] 35 unit tests, 1074 full passed ✅

#### IDE Adaptation (To Be Completed)
- [ ] Cursor Skill auto-generation — `vibecollab export cursor-skill`
  - Auto-generate `.cursor/skills/vibecollab/SKILL.md` from `project.yaml` + `CONTRIBUTING_AI.md`
  - Auto-regenerate on project config changes
- [ ] Cline Custom Instructions adaptation — `vibecollab export cline`
  - Generate `.cline/custom_instructions.md`
- [ ] CodeBuddy Rule adaptation — `vibecollab export codebuddy`
  - Generate `.codebuddy/rules/vibecollab.md`

### v0.9.2 - Insight Solidification Signal Enhancement

> Objective: Transform Insight solidification from "pure LLM reasoning" to "structured signal-driven", providing reliable solidification context

#### Solidification Signal Collection
- [x] `vibecollab insight suggest` — Structured signal-based Insight candidate recommendation ✅
  - Git commit history analysis since last `insight add`
  - CONTEXT.md / DECISIONS.md change diff detection
  - New/closed Task extraction
  - Output candidate Insight list, manually confirm before creation
- [x] Signal snapshot — `.vibecollab/insight_signal.json` ✅
  - Record last insight solidification timestamp and commit hash
  - `insight add` auto-updates snapshot
  - `insight suggest` extracts incremental signals from snapshot to HEAD

#### Conversation Persistence (L1 Cache)
- [x] Conversation summary storage — `.vibecollab/sessions/` ✅
  - AI IDE conversation end summary persistence (manual or MCP auto-trigger)
  - Serves as input signal for `insight suggest`
  - MCP `session_save` tool exposes write interface
- [x] MCP Server enhancement ✅
  - `insight_suggest` tool: Signal-based Insight candidate recommendation
  - `session_save` tool: Save conversation session summary
- [x] 60 unit tests (insight_signal + session_store) ✅
  - Full 1134 passed, 1 skipped, zero regression

### v0.9.3 - Task/EventLog Core Workflow Integration

> Objective: Transform TaskManager and EventLog from "low-level API" to user-perceivable daily features (DECISION-016)

#### Task CLI Completion
- [x] `vibecollab task transition` — Manually advance task state (TODO→IN_PROGRESS→REVIEW→DONE) ✅
- [x] `vibecollab task solidify` — Solidify task (REVIEW→DONE, through validation gates) ✅
- [x] `vibecollab task rollback` — Roll back task state ✅

#### Core Command Injection
- [x] `onboard` injects active Task overview — Shows current TODO/IN_PROGRESS/REVIEW tasks ✅
- [x] `onboard` injects recent EventLog event summary ✅
- [x] `next` recommends actions based on Task status — Priority hints for timeout/blocked/pending solidify tasks ✅

#### MCP Server Enhancement
- [x] `task_create` tool — AI IDE can directly create tasks ✅
- [x] `task_transition` tool — AI IDE can advance task state ✅

#### Test & Decision
- [x] 30 unit tests, full 1164 passed, zero regression ✅
- [x] DECISION-016: v0.9.3 direction decision (S-level) ✅

### v0.9.4 - Insight Quality & Lifecycle (Completed ✅)

> Objective: Improve solidification quality, establish complete Insight lifecycle from creation to retirement

- [x] Insight auto-deduplication — Fingerprint+title+tag similarity check on creation, prevent duplicates ✅
- [x] Insight relationship graph — `vibecollab insight graph` visualize derivation/association (text/json/mermaid) ✅
- [x] Cross-project Insight portability — `insight export` / `insight import` (YAML format, three conflict strategies) ✅
- [x] MCP Server added `insight_graph` / `insight_export` two Tools ✅
- [x] 36 unit tests, full 1201 passed, zero regression ✅

### v0.9.5 - ROADMAP ↔ Task Integration (Completed ✅)

> Objective: Bidirectional linkage between ROADMAP.md and TaskManager, structured milestone progress tracking

- [x] RoadmapParser module — Parse ROADMAP.md milestones + checklist + inline Task ID references ✅
- [x] Bidirectional sync — ROADMAP `[x]` ↔ Task DONE status, three directions (both/roadmap_to_tasks/tasks_to_roadmap) ✅
- [x] Task `milestone` field — Task dataclass new milestone association, `list_tasks(milestone=)` filter ✅
- [x] CLI `vibecollab roadmap status/sync/parse` command group ✅
- [x] CLI `vibecollab task create --milestone` / `task list --milestone` enhancement ✅
- [x] MCP Server added `roadmap_status` / `roadmap_sync` two Tools ✅
- [x] README bilingual restructure (English main README + Chinese README.zh-CN.md) ✅
- [x] 40 unit tests, full 1331 passed, 89% coverage, zero regression ✅

### v0.9.7 - Roadmap Parser Format Guidance (In Development)

> Objective: Resolve lack of hints when user ROADMAP format doesn't match, strict ### format constraint + clear error guidance

- [x] Strict ### milestone format — Only accepts `### vX.Y.Z`, rejects `####` and other levels TASK-DEV-008
- [x] Zero milestone format hint — CLI outputs expected format + Task ID association syntax TASK-DEV-008
- [x] sync zero milestone distinction — No longer false-reports "synced" TASK-DEV-008
- [x] MCP Tool description enhancement — AI IDE can guide users to modify ROADMAP based on this TASK-DEV-008
- [x] init template compatibility — Generated ROADMAP is parseable out-of-box TASK-DEV-008
- [x] v0.9.7 PyPI release

### v0.9.6 - PyPI Adaptation + Documentation Quality (Completed ✅)

> Objective: PyPI release page usability optimization, project documentation timeliness maintenance

- [x] README.pypi.md — PyPI-specific README (remove Mermaid + absolute URLs) TASK-DEV-006
- [x] pyproject.toml readme field points to README.pypi.md TASK-DEV-006
- [x] CONTEXT.md stale task cleanup (TASK-DEV-005 marked completed) TASK-DEV-007
- [x] v0.9.6 PyPI release

### v0.10.0 - Feature Freeze + Stability Gate (DECISION-017)

> Objective: Ensure all business logic is closed-loop before feature freeze, establish release quality gate. No new business features after this version.

#### External Project QA Validation
- [ ] Run Phase 11 TC-E2E-001~010 on 3+ real external projects
- [ ] Fix all bugs found during QA

#### Quality Gate
- [ ] Test coverage ≥ 85%
- [ ] `vibecollab check` all green
- [ ] MCP Server validated in Cursor/CodeBuddy
- [ ] Feature freeze declaration

### v0.10.1 - Code Internationalization (Code i18n) (Completed ✅)

> Objective: Code-level full English translation, ensure non-Chinese native developers can read

- [x] Translate Chinese docstring/comment in 36 .py files to English (~2055 lines)
- [x] Translate 62+ CLI `help=` parameters to English
- [x] Runtime output text (`click.echo` / `console.print`) English translation
- [x] Error message English translation
- [x] Full 1201+ tests passed, coverage must not decrease

### v0.10.2 - Documentation Bilingualization (Doc Bilingual) (Completed ✅)

> Objective: README and core docs provide English versions

- [x] README.md rewritten in English (as primary README)
- [x] README_CN.md preserves Chinese version
- [x] CHANGELOG.md organized in English
- [x] pyproject.toml description in English

### v0.10.3 - Git History Rewrite + Repository Facade (In Progress)

> Objective: One-time rewrite of all commit messages to standard English + GitHub facade professionalization
> Note: Template/config English translation and Insight cache translation completed as part of i18n effort

- [ ] `git-filter-repo` rewrite 97+ commit messages to Conventional Commits English format
- [ ] force push (irreversible, ensure this is the last history-breaking operation)
- [ ] GitHub About description + Topics tags
- [ ] Issue / PR template
- [ ] CONTRIBUTING.md (English, for external contributors)
- [ ] CODE_OF_CONDUCT.md
- [ ] GitHub Release (v0.10.3+)
- [ ] Badge: PyPI / CI / Coverage / License / Python Version

### v1.0.0 - Official Release

> Objective: Mark stable version, PyPI + GitHub Release

- [ ] Clean up all .dev0 markers
- [ ] PyPI v1.0.0 release
- [ ] GitHub Release v1.0.0

### ~~v0.9.2(old) - Bootstrap~~ ❌ Cut (DECISION-015)
> Decision: `bootstrap` insufficient value (already have handwritten CONTRIBUTING_AI.md), `ContextBuilder` refactoring can happen on-demand during MCP development, no separate version needed.

### ~~v0.10.1(old) - Agent Stability Enhancement~~ ❌ Cut (DECISION-015)
> Decision: MCP + external IDE (Cline/Cursor/CodeBuddy) already covers Agent scenarios, no further investment in self-built Agent capabilities. `vibecollab ai` remains experimental frozen.

---

## Stage History

- **demo**: 2026-01-20 (in progress → upgrade to production after v1.0.0)

---

## Future Planning

### Unsupervised Operation (TBD)
> Demoted from v0.10.0 to future planning (DECISION-015)

- Git Hook integration (`vibecollab hook install`)
- CI/CD unsupervised mode (`vibecollab ci check/report/gate`)
- GitHub Action (`vibecollab-action`)
- Scheduled tasks (`vibecollab cron`)

### Production Stage
**Estimated timeline**: After v1.0.0 release
**Prerequisites**: 
- v0.10.x all completed
- Test coverage 85%+
- Code/docs fully English
- GitHub facade professionalized

**Key tasks**:
- Community operations + external contributor onboarding
- Plugin ecosystem (custom Patterns / domain extensions)
- Performance optimization (large-scale projects)
- i18n framework (multi-language CLI output)

### Commercial Stage
**Estimated timeline**: TBD
**Focus**:
- User experience optimization
- Market adaptation
- Extensibility improvement

### Stable Stage
**Estimated timeline**: TBD
**Focus**:
- Stability maintenance
- Maintenance cost reduction
- Long-term planning

---

*Last updated: 2026-03-03 (v0.10.1-dev)*
