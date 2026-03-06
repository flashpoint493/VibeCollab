# VibeCollab Decision Records

## Pending Decisions

(None)

## Confirmed Decisions

### DECISION-017: v0.10.x Release Engineering — From "Working" to "Professional Open Source Project"
- **Level**: S
- **Role**: [PM] [ARCH]
- **Problem**: Project features are essentially complete (v0.9.4, 1201 tests, 36 .py files, ~15K LOC), but three major issues hinder open-source adoption: (1) Code/CLI/docs entirely in Chinese, international audience cannot use (2) 97 git commits mixed Chinese/English, unprofessional (3) README/GitHub facade lacks standard open-source project elements
- **Decision**: Complete in 5 incremental versions, **strict sequential execution, no steps may be skipped**

#### Version Plan

**v0.10.0 — Final Business Logic + Stability Gate**
> Ensure all business logic is closed-loop before feature freeze, establish release quality gate
- External project QA full validation (Phase 11 TC-E2E-001~010)
- Test coverage ≥ 85% ✅ (reached 85%)
- `vibecollab check` all green
- MCP Server validated in Cursor/CodeBuddy
- Fix all bugs found during QA
- Project file structure review — ensure src/ directory organization is clean and readable (split large files, introduce sub-packages if necessary)
- **Feature freeze**: No new business features after this version

**v0.10.1 — Code Internationalization (Code i18n)**
> Code-level full English translation, ensure non-Chinese native developers can read
- **Scope 1: docstring/comment** — Translate Chinese comments/docstrings in 36 .py files to English (~2055 lines)
- **Scope 2: CLI help** — Translate 62+ `help=` parameters to English
- **Scope 3: Runtime output** — Translate Chinese prompts in `click.echo` / `console.print` to English
- **Scope 4: Error messages** — Translate error messages to English
- **Not changed**: Generated CONTRIBUTING_AI.md template content remains Chinese (needed for Chinese-facing projects)
- **Reference templates**: `event_log.py`, `llm_client.py`, `config_manager.py`, `task_manager.py` (already in English)
- Full test suite must pass, coverage must not decrease

**v0.10.2 — Documentation Bilingualization (Doc Bilingual)**
> README and core docs provide English versions
- README.md rewritten in English (as primary README)
- README_CN.md preserves Chinese version
- CHANGELOG.md organized in English
- pyproject.toml description in English
- docs/ internal development documents remain Chinese (developer self-use)

**v0.10.3 — Git History Rewrite + Repository Facade**
> This is a destructive operation, must be executed last
- `git filter-branch` or `git-filter-repo` rewrite all 97+ commit messages to standard English
  - Maintain Conventional Commits format: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `release:`
  - Preserve key info (version numbers, test counts, decision numbers)
  - One-time force push (irreversible)
- Git commit vectorization index — `vibecollab index` supports indexing git commit messages as semantic search context
  - Commit messages are core input signals for insight suggest / onboard etc.
  - Englishified commits have higher quality, greater vectorization value
- GitHub repository facade:
  - About description + Topics tags
  - Issue / PR template
  - CONTRIBUTING.md (English, for external contributors)
  - CODE_OF_CONDUCT.md
  - GitHub Release (from v0.10.3 onward)
  - Badge: PyPI / CI / Coverage / License / Python Version

**v1.0.0 — Official Release**
> Mark stable version
- Clean up all .dev0 markers
- PyPI v1.0.0 release
- GitHub Release v1.0.0
- Publicity preparation

#### Core Principles
1. **Feature freeze first, then polish** — No new features after v0.10.0
2. **Code English first, then docs English** — Code is fundamental, docs follow
3. **Git history rewrite goes last** — Avoid force push then continue committing Chinese commits
4. **Each version is self-contained and independently releasable to PyPI** — Any version is a releasable state
5. **Full test suite is the iron gate** — Each version must have 1201+ tests passed, 0 regression

#### Effort Estimate

| Version | Core Work | Estimated Effort |
|---------|-----------|-----------------|
| v0.10.0 | QA validation + bug fix + coverage | 2-3 sessions |
| v0.10.1 | 36 files code English translation (~2055 Chinese lines) | 3-4 sessions |
| v0.10.2 | README English rewrite + CHANGELOG cleanup | 1-2 sessions |
| v0.10.3 | 97 commits rewrite + GitHub facade | 1-2 sessions |
| v1.0.0 | Version number + Release + publicity | 1 session |

- **Date**: 2026-02-27
- **Status**: CONFIRMED
- **Impact**: Critical path for the entire project's transition from demo to production phase

### DECISION-001: Rename llm.txt to CONTRIBUTING_AI.md
- **Level**: A
- **Role**: [ARCH]
- **Problem**: What name should the output file use?
- **Decision**: Use `CONTRIBUTING_AI.md` as the primary output file
- **Rationale**: 
  - More aligned with GitHub community conventions (similar to CONTRIBUTING.md)
  - Clearly indicates this is an AI collaboration guide
  - Avoids confusion with llms.txt standard
- **Date**: 2026-01-20
- **Status**: CONFIRMED
- **Impact**: All references in code, docs, and templates need updating

### DECISION-002: Integrate llms.txt Standard
- **Level**: A
- **Role**: [ARCH]
- **Problem**: How to integrate with the llmstxt.org standard?
- **Decision**: Add an AI Collaboration section in llms.txt, referencing CONTRIBUTING_AI.md
- **Rationale**:
  - llms.txt is a more widely adopted standard
  - Context7 and similar tools natively support it
  - Future AI training/inference prioritizes reading it
  - Separation of concerns: llms.txt describes the project, CONTRIBUTING_AI.md defines collaboration rules
- **Date**: 2026-01-20
- **Status**: CONFIRMED
- **Impact**: Added llmstxt.py module, auto-detect and update llms.txt

### DECISION-003: Rename Package to vibe-collab
- **Level**: A
- **Role**: [ARCH]
- **Problem**: What should the package be called?
- **Decision**: Use `vibe-collab` as package name and repository name
- **Rationale**:
  - Embodies Vibe Development philosophy
  - Emphasizes collaboration feature
  - Avoids conflicts with existing PyPI package names
  - Simpler, more memorable
- **Date**: 2026-01-20
- **Status**: CONFIRMED
- **Impact**: Package name, repository name, all documentation references need updating

### DECISION-004: Place Project Lifecycle Stage Info in ROADMAP.md
- **Level**: B
- **Role**: [PM]
- **Problem**: Where should project lifecycle stage information be placed?
- **Decision**: In ROADMAP.md, not CONTRIBUTING_AI.md
- **Rationale**:
  - ROADMAP is a PM-focused document
  - Lifecycle stage management better fits project management scope
  - Keep CONTRIBUTING_AI.md focused on collaboration rules
- **Date**: 2026-01-21
- **Status**: CONFIRMED
- **Impact**: ROADMAP.md template needs to include stage information

### DECISION-005: Early CI/CD Involvement in Demo Stage
- **Level**: B
- **Role**: [ARCH]
- **Problem**: At which stage should CI/CD be established?
- **Decision**: CI/CD should be established during the Demo stage
- **Rationale**:
  - Early CI/CD avoids migration costs later
  - Automated testing and deployment aids rapid iteration
  - Aligns with modern development best practices
- **Date**: 2026-01-21
- **Status**: CONFIRMED
- **Impact**: Updated demo stage principles, added "establish CI/CD"

### DECISION-006: Establish Performance Specs and Code Refactoring Before Production Stage
- **Level**: A
- **Role**: [ARCH]
- **Problem**: When should performance specifications and code refactoring happen?
- **Decision**: Should start before entering Production stage
- **Rationale**:
  - Stable code structure needed before mass production
  - Performance standards should be defined before scaling
  - Full code review can identify architecture issues early
- **Date**: 2026-01-21
- **Status**: CONFIRMED
- **Impact**: Updated production stage principles

### DECISION-007: Automatic Git Check and Initialization
- **Level**: B
- **Role**: [DEV]
- **Problem**: Should Git repos be auto-initialized?
- **Decision**: Auto-check during project init, optionally auto-initialize
- **Rationale**:
  - Ensure projects use version control from the start
  - Reinforce Git sync habits in subsequent conversations
  - Provide `--no-git` option for users who don't need it
- **Date**: 2026-01-21
- **Status**: CONFIRMED
- **Impact**: Added git_utils.py module, integrated into project initialization flow

### DECISION-008: Multi-Developer Support Architecture Design
- **Initiator**: user
- **Participants**: user, AI
- **Level**: A
- **Role**: [ARCH]
- **Problem**: How to support multiple developers / multiple AI Agents collaborating?
- **Options**:
  - A: Each developer independent CONTEXT.md, no global view
  - B: Keep single CONTEXT.md, add developer markers
  - C: Independent developer CONTEXT.md + global aggregated view (chosen)
- **Decision**: Option C — Independent developer contexts + global auto-aggregation
- **Rationale**:
  - **Isolation**: Each developer maintains their own work context, avoiding conflicts
  - **Global view**: Auto-aggregation provides project-wide status for coordination
  - **Extensible**: Easy to add new developers without restructuring
  - **Backward compatible**: Single-developer projects can seamlessly migrate to multi-developer mode
- **Technical approach**:
  - Developer identity recognition: Git username auto-recognition (`git config user.name`)
  - Directory structure: `docs/developers/{role_code}/CONTEXT.md`
  - Global aggregation: `docs/CONTEXT.md` auto-generated from all developer contexts (read-only)
  - Collaboration management: Added `docs/developers/COLLABORATION.md` for dependencies and handoffs
  - CHANGELOG.md: Remains globally unified (version history should be unified)
  - DECISIONS.md: Added `initiator` and `participants` fields to mark participants
  - Git commit: No extra marking, uses Git native author info
- **Date**: 2026-02-10
- **Status**: CONFIRMED
- **Impact**: 
  - Added `src/vibecollab/developer.py` module (DeveloperManager, ContextAggregator)
  - Extended `project.yaml` schema (multi_developer config)
  - Added CLI commands (`vibecollab dev *`)
  - Updated project initialization logic (supports `--multi-dev` option)
  - Version upgraded to v0.5.0

### DECISION-009: Borrow architectural patterns for protocol maturity
- **Initiator**: user
- **Participants**: user, AI
- **Level**: A
- **Role**: [ARCH]
- **Problem**: How to improve VibeCollab's protocol maturity and structural robustness?
- **Options**:
  - A: Full-scale architecture overhaul (high risk, high disruption)
  - B: Selective pattern borrowing with gradual introduction (chosen)
  - C: Minimal changes, only fix bugs
- **Decision**: Direction B — Selectively adopt 10 proven architectural patterns, mapped to VibeCollab-native concepts, introduced incrementally with unit tests per iteration.
- **Rationale**:
  - Incremental approach reduces risk and allows validation at each step
  - Patterns are renamed and adapted to VibeCollab's project-centric philosophy
  - Each iteration is independently testable and committable
  - Avoids coupling to any external framework's proprietary terminology
- **Borrowed patterns**:
  1. State separation (mutable JSON + immutable JSONL) → multi-file split (High)
  2. Append-only event log → EventLog events.jsonl (High)
  3. Validate-solidify-rollback loop → Task solidify check (High)
  4. Atomic write → Python atomic_write (Medium)
  5. Content-addressable hashing → SHA-256 fingerprint (Medium)
  6. Signal extraction → Project health signals (Medium)
  7. Experience reuse patterns → Project Pattern / Template (Medium)
  8. Blast radius control → Task max change scope (Medium)
  9. Defense-in-depth safety → Multi-level validation guards (Low)
  10. Asset sharing protocol → Cross-project template sharing (Low)
- **Date**: 2026-02-24
- **Status**: CONFIRMED
- **Impact**:
  - Iteration 1: EventLog module (event_log.py) — COMPLETED
  - Iteration 2: TaskManager module (task_manager.py) — COMPLETED
  - Iteration 3: PatternEngine module (pattern_engine.py) — COMPLETED
  - Iteration 4: Health Signals (health.py) + Agent Executor (agent_executor.py) — COMPLETED

### DECISION-010: Three-Mode AI Architecture (IDE + CLI + Agent)
- **Initiator**: user
- **Participants**: user, AI
- **Level**: A
- **Role**: [ARCH]
- **Problem**: How should VibeCollab support different AI interaction scenarios?
- **Options**:
  - A: Keep only IDE dialogue mode (existing)
  - B: Add CLI human-machine interaction + IDE (two modes)
  - C: IDE + CLI human-machine interaction + Agent autonomous (three modes, chosen)
- **Decision**: Option C — Three-mode coexistence
- **Rationale**:
  - **IDE dialogue**: Developers collaborate directly in Cursor/CodeBuddy, reading CONTRIBUTING_AI.md (existing)
  - **CLI human-machine**: `vibecollab ai ask/chat`, collaborate with AI without IDE
  - **Agent autonomous**: `vibecollab ai agent run/serve`, server deployment, API Key driven development
  - Three modes cover the complete spectrum from local development to server deployment
  - Agent mode has built-in safety gates (PID lock, pending-solidify, max cycles, adaptive backoff, circuit breaker)
- **Technical approach**:
  - Added `cli_ai.py` as command layer, registered to main CLI (`vibecollab ai`)
  - Reuses `LLMClient` + `build_project_context()` + `TaskManager` + `EventLog`
  - Agent serve loop: Plan→Execute→Solidify, each cycle independent
  - Environment variable config: `VIBECOLLAB_AGENT_MAX_CYCLES`, `VIBECOLLAB_AGENT_*`
- **Date**: 2026-02-24
- **Status**: CONFIRMED
- **Impact**:
  - Added `src/vibecollab/cli_ai.py` (870+ lines)
  - Added `tests/test_cli_ai.py` (32 tests)
  - Version upgraded to v0.5.8

### DECISION-011: Pattern Engine Architecture (Manifest-Driven Template Engine)
- **Initiator**: user
- **Participants**: user, AI
- **Level**: A
- **Role**: [ARCH]
- **Problem**: How to replace 27 hardcoded `_add_*()` methods in generator.py with a maintainable, extensible document generation system?
- **Options**:
  - A: Keep hardcoded Python methods, gradually optimize
  - B: Jinja2 templates + manifest.yaml declarative engine (chosen)
  - C: Pure Markdown concatenation, no template engine
- **Decision**: Option B — Manifest-driven Jinja2 template engine + local override mechanism
- **Rationale**:
  - **Maintainability**: Each section is an independent `.md.j2` template, modifications don't affect other sections
  - **Declarative control**: `manifest.yaml` defines section order, conditions, template mapping — configuration not code
  - **Extensibility**: Template Overlay allows users to customize templates and manifest in `.vibecollab/patterns/`
  - **Code reduction**: generator.py from 1713 lines to 83 lines, reducing maintenance cost
  - **Condition syntax**: Supports `config.x.enabled|true` default value syntax, more flexible than hardcoded if/else
- **Technical approach**:
  - `PatternEngine`: Jinja2 Environment + ChoiceLoader (local-first → built-in fallback)
  - `manifest.yaml`: 27 section definitions (id, template, condition, chapter_title)
  - `_merge_manifests()`: Supports override/insert(after)/exclude three merge operations
  - `_evaluate_condition()`: Supports `|default` syntax condition evaluation
  - 27 `.md.j2` template files + `DEFAULT_STAGES` built-in stage definitions
- **Date**: 2026-02-24
- **Status**: CONFIRMED
- **Impact**:
  - `src/vibecollab/pattern_engine.py` enhanced (~290 lines)
  - `src/vibecollab/generator.py` reduced (1713 → 83 lines)
  - `tests/test_pattern_engine.py` (40 tests)
  - Added `Jinja2>=3.0` dependency
  - Added `src/vibecollab/patterns/` directory (27 templates + manifest.yaml)

### DECISION-012: Cut Web UI, Pivot to Insight Solidification System
- **Initiator**: user
- **Participants**: user, AI
- **Level**: S
- **Role**: [ARCH] [PM]
- **Problem**: What should v0.7.0 deliver? Web UI or solidification system?
- **Options**:
  - A: v0.7.0 builds Web UI (project status visualization, conflict graph, real-time monitoring)
  - B: Cut Web UI, v0.7.0 builds Insight solidification system (chosen)
- **Decision**: Cut Web UI, v0.7.0 fully focused on Insight solidification system
- **Rationale**:
  - Web UI is not VibeCollab's core competency, low ROI
  - Solidification system directly enhances AI collaboration quality, core differentiator
  - Successful development steps and experiences should be fixed, reusable, shareable across developers
  - Future solidifications can be not just YAML knowledge, but also associated tools/scripts/templates (Artifacts), cross-project reusable
- **Core architecture: Body and Registry separation**:
  - **Insight body** (`INS-xxx.yaml`): Portable knowledge package with title/summary/tags/category/body/artifacts/origin/fingerprint
  - **Registry** (`registry.yaml`): Project-level usage state with weight/used_count/last_used_at/active + decay settings
  - Body is **cross-project reusable** pure knowledge; Registry records **this project's** usage weight and lifecycle
  - Storage path: `.vibecollab/insights/INS-xxx.yaml` + `.vibecollab/insights/registry.yaml`
- **Tag-driven Developer description**:
  - Developers use open tag system (replaces enum fields), stored in `.metadata.yaml`
  - Specific tags can influence decision behavior (e.g., `prefers:conservative` affects risk assessment)
  - Developers can record contributed (created Insights) and bookmarks (bookmarked Insights)
- **Search and provenance**:
  - Tag search: Jaccard similarity × registry weight ranking
  - Category search: Exact match + weight ranking
  - Provenance chain: `origin.derived_from` tracks derivation, `get_derived_tree()` builds upstream/downstream relations
  - **Self-describing provenance protocol**: origin.source structure doesn't depend on project internal ID system
    - `context`: Natural language description of creation background
    - `source.description`: Self-description of source (required when source exists), cross-project readable
    - `source.ref`: Source project internal ID (demoted to optional hint)
    - `source.url`: Externally accessible link (optional)
    - `source.project`: Source project name (optional)
- **Weight decay mechanism**:
  - `decay_rate` × periodic decay, `use_reward` usage reward, `deactivate_threshold` auto-deactivation
  - Lifecycle state (weight/used_count/active) fully belongs to project-level registry, not to the insight body
- **Consistency check** (5-item full check):
  - Registry ↔ file bidirectional consistency
  - `derived_from` reference integrity
  - Developer metadata reference integrity
  - SHA-256 content fingerprint verification
  - All CRUD operations auto-record EventLog audit events
- **Design principles**:
  - Oriented toward collaborative solidification, not Agent self-evolution
  - Tag-driven open descriptions, not rigid enum fields
  - Integrated with VibeCollab's own symbol system (decision levels S/A/B/C, SHA-256 fingerprint, EventLog audit), not borrowing external terminology
  - Insight body is minimal and portable; future abstraction as packages via package manager registration
- **Date**: 2026-02-25
- **Status**: CONFIRMED
- **Impact**:
  - ROADMAP.md updated: v0.7.0 objectives changed
  - `schema/insight.schema.yaml` — Insight body + Registry + Developer Tag three-part Schema ✅
  - `src/vibecollab/insight_manager.py` — Core module (CRUD/Registry/search/provenance/consistency check) ✅
  - `tests/test_insight_manager.py` — 62 unit tests ✅
  - `tests/test_developer.py` — developer.py full coverage, 88 unit tests (including Tag extension) ✅
  - Developer metadata extension — tags/contributed/bookmarks CRUD ✅
  - `src/vibecollab/cli_insight.py` — CLI command group (list/show/add/search/use/decay/check/delete) ✅
  - `tests/test_cli_insight.py` — 21 unit tests ✅
  - Consistency check integrated into `vibecollab check --insights` ✅
  - Cross-developer sharing + provenance CLI visualization (bookmark/unbookmark/trace/who/stats) ✅
  - InsightManager extension: get_full_trace / get_insight_developers / get_cross_developer_stats ✅

### DECISION-013: AI Agent Onboarding Guidance and Action Suggestion System
- **Initiator**: user
- **Participants**: user, AI
- **Level**: A
- **Role**: [ARCH]
- **Problem**: How does an AI Agent understand the full project picture after onboarding? How does it know what to do next after modifying files?
- **Options**:
  - A: Rely solely on CONTRIBUTING_AI.md documentation (current, passive)
  - B: Add onboard + next commands for proactive guidance (chosen)
- **Decision**: Add two core commands: `vibecollab onboard` and `vibecollab next`
- **Rationale**:
  - **onboard**: Solves "AI doesn't know where to start" — provides project overview/progress/decisions/TODOs/reading list
  - **next**: Solves "modified files, don't know next step" — generates action suggestions based on git diff + mtime + linked_groups
  - Evolves from passive diagnostics (check tells you what's wrong) to proactive guidance (onboard/next tells you what to do)
  - Simultaneously enhances document consistency check: linked_groups three-level check (local_mtime/git_commit/release)
- **Date**: 2026-02-25
- **Status**: CONFIRMED
- **Impact**:
  - Added `src/vibecollab/cli_guide.py` (~570 lines)
  - Added `tests/test_cli_guide.py` (29 tests)
  - `protocol_checker.py` enhanced: _check_document_consistency() + three-level check methods
  - `project.yaml` added `documentation.consistency` config block
  - update_threshold_hours from 24h → 15min

---

### DECISION-014: Task-Insight Auto-Link System
- **Initiator**: user
- **Participants**: user, AI
- **Level**: A
- **Role**: [ARCH]
- **Problem**: Insight solidification and Task system only have indirect association via metadata annotation, how to establish direct knowledge-task links?
- **Options**:
  - A: Keep indirect association (only origin.source_type="task" metadata)
  - B: Auto-search related Insights on Task creation, store in metadata (chosen)
  - C: Full bidirectional binding (Insight reverse-references Task)
- **Decision**: B — Unidirectional auto-link (Task → Insight)
- **Rationale**:
  - Zero-config: InsightManager optionally injected, auto-degrades when absent
  - Low intrusion: Only appends metadata in create_task(), doesn't change return type or existing API
  - High value: Agent creating Tasks automatically gets knowledge context, reducing duplicate work
  - Extract keywords from feature/description + Jaccard × weight matching, reuses existing search logic
- **Date**: 2026-02-25
- **Status**: CONFIRMED
- **Impact**:
  - `task_manager.py` enhanced: insight_manager parameter + _find_related_insights() + suggest_insights()
  - Added `src/vibecollab/cli_task.py` (task create/list/show/suggest)
  - Added `tests/test_task_insight_integration.py` (28 tests)
  - Fully backward compatible

---

### DECISION-015: Cut Bootstrap (v0.9.2) and Agent Enhancement (v0.10.1), Focus on MCP + Release
- **Initiator**: user
- **Participants**: user, AI
- **Level**: S
- **Role**: [PM]
- **Problem**: Are v0.9.2 bootstrap and v0.10.1 Agent enhancement worth continued investment? What should v0.10 focus on?
- **Options**:
  - A: Follow original plan v0.9.2 bootstrap → v0.10.0 unsupervised → v0.10.1 Agent
  - B: Cut bootstrap and Agent, proceed to release preparation after MCP (chosen)
  - C: Only cut Agent, keep bootstrap
- **Decision**: B — Cut v0.9.2 and v0.10.1, change v0.10.0 to release preparation (docs/Wiki/README/PyPI)
- **Rationale**:
  - `bootstrap` insufficient value: already have handwritten CONTRIBUTING_AI.md (1488 lines), auto-generation would overwrite with lower quality
  - `ContextBuilder` refactoring can happen on-demand during MCP development, no need for separate version
  - Agent self-build conflicts with MCP + external IDE (Cline/Cursor/CodeBuddy) roadmap; `vibecollab ai` already marked experimental frozen in DECISION-012
  - Unsupervised operation (Git Hook/CI/CD) demoted to future planning, lower priority than product release
  - v0.10.0 focuses on documentation + PyPI official release, critical step toward v1.0
- **Date**: 2026-02-27
- **Status**: CONFIRMED
- **Impact**:
  - ROADMAP version chain simplified: v0.9.0(semantic search) → v0.9.1(MCP) → v0.10.0(release preparation)
  - v0.9.2 bootstrap, v0.10.1 Agent marked ❌ cut
  - Original v0.10.0 unsupervised operation demoted to "future planning"
  - v1.0.0 prerequisites simplified

---

### DECISION-016: v0.9.3 Prioritize Task/EventLog Core Workflow Integration
- **Initiator**: user
- **Participants**: user, AI
- **Level**: S
- **Role**: [PM, ARCH]
- **Problem**: TaskManager (53 tests) and EventLog (23 tests) are well-implemented, but completely disconnected from user daily workflow. tasks.json is empty, events.jsonl only has Insight operation events. onboard/next/check three core commands don't read Task/EventLog data. HealthExtractor implemented but not connected to CLI. What should v0.9.3/v0.9.4 deliver?
- **Options**:
  - A: Accept status quo — Task/EventLog exist as low-level API, wait for users to manually use
  - B: Connect core workflow — onboard injects Task overview, next recommends based on Tasks, MCP exposes task_create/transition, CLI adds transition/solidify/rollback (chosen)
  - C: Cut TaskManager — Code is verified, but unused code is waste, better to delete and reduce maintenance cost
- **Decision**: B — v0.9.3 prioritize connecting Task/EventLog to core workflow, Insight quality pushed to v0.9.4
- **Rationale**:
  - TaskManager/EventLog are well-designed and thoroughly tested; the issue is missing integration, not code quality
  - onboard/next are high-frequency user commands; injecting Task/EventLog data lets users perceive these modules' value
  - MCP exposing task_create/transition enables AI IDE to auto-manage tasks, completing the loop
  - CLI missing transition/solidify/rollback prevents users from manually operating task states
  - health command already connected to HealthExtractor, but onboard/check lack EventLog visibility
  - Insight quality (dedup/graph/cross-project) lower priority than core workflow integration
- **Date**: 2026-02-27
- **Status**: CONFIRMED
- **Impact**:
  - v0.9.3 changed from "Insight Quality & Lifecycle" to "Task/EventLog Core Workflow Integration"
  - v0.9.4 added "Insight Quality & Lifecycle"
  - Task CLI added transition/solidify/rollback three commands
  - onboard injects active Task overview
  - next recommends actions based on Task status
  - MCP added task_create / task_transition Tools
  - EventLog data visible in onboard

---
*Decision record format defined in CONTRIBUTING_AI.md*
