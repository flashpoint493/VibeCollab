# VibeCollab Test Cases Manual

## Test Case Format

```
### TC-{MODULE}-{SEQ}: {Test Name}
- **Related**: TASK-XXX
- **Prerequisites**: {Prerequisites}
- **Steps**:
  1. {Step 1}
  2. {Step 2}
- **Expected**: {Expected results}
- **Status**: 🟢/🟡/🔴/⚪
```

## Phase 1 Test Cases

### TC-CLI-001: Project Initialization
- **Related**: Core feature
- **Prerequisites**: vibe-collab installed
- **Steps**:
  1. Run `vibecollab init -n "TestProject" -d generic -o ./test-project`
  2. Check generated files
- **Expected**: 
  - Generates CONTRIBUTING_AI.md
  - Generates project.yaml
  - Generates docs/ directory with all documents
  - Auto-initializes Git repository (if available)
- **Status**: 🟢

### TC-CLI-002: Generate Collaboration Rules Document
- **Related**: Core feature
- **Prerequisites**: project.yaml config file exists
- **Steps**:
  1. Run `vibecollab generate -c project.yaml`
  2. Check generated CONTRIBUTING_AI.md
- **Expected**: 
  - Generates complete collaboration rules document
  - Contains all configured sections
  - Auto-integrates llms.txt (if exists)
- **Status**: 🟢

### TC-CLI-003: llms.txt Integration
- **Related**: DECISION-002
- **Prerequisites**: llms.txt already exists in project directory
- **Steps**:
  1. Run `vibecollab generate -c project.yaml`
  2. Check llms.txt file
- **Expected**: 
  - AI Collaboration section added to llms.txt
  - References CONTRIBUTING_AI.md
  - No duplicate additions (multiple runs)
- **Status**: 🟢

### TC-CLI-004: Create New llms.txt
- **Related**: DECISION-002
- **Prerequisites**: No llms.txt in project directory
- **Steps**:
  1. Run `vibecollab generate -c project.yaml`
  2. Check if llms.txt created
- **Expected**: 
  - Creates llmstxt.org standard compliant llms.txt
  - Contains project basic info and AI Collaboration section
- **Status**: 🟢

### TC-GIT-001: Git Auto-Initialization
- **Related**: DECISION-007
- **Prerequisites**: Git installed, project directory is not a Git repo
- **Steps**:
  1. Run `vibecollab init -n "TestProject" -d generic -o ./test-project`
  2. Check .git directory
- **Expected**: 
  - Auto-initializes Git repository
  - Creates initial commit
  - Shows success message
- **Status**: 🟢

### TC-GIT-002: Git Check Prompt
- **Related**: DECISION-007
- **Prerequisites**: Git not installed or project is not a Git repo
- **Steps**:
  1. Run `vibecollab generate -c project.yaml`
  2. Check output messages
- **Expected**: 
  - Shows Git status warning or prompt
  - Suggests initializing Git repository
- **Status**: 🟢

### TC-LIFECYCLE-001: Project Lifecycle Check
- **Related**: DECISION-004
- **Prerequisites**: Project initialized with lifecycle config
- **Steps**:
  1. Run `vibecollab lifecycle check`
  2. Check output
- **Expected**: 
  - Shows current stage info
  - Shows stage focus and principles
  - Shows milestone status
  - Shows upgrade eligibility
- **Status**: 🟢

### TC-LIFECYCLE-002: Project Lifecycle Upgrade
- **Related**: DECISION-004
- **Prerequisites**: Project in demo stage, meets upgrade conditions
- **Steps**:
  1. Run `vibecollab lifecycle upgrade`
  2. Check project.yaml updates
  3. Check stage history records
- **Expected**: 
  - Updates current_stage to production
  - Adds new stage history record
  - Shows upgrade suggestions
- **Status**: 🟡 (needs manual testing)

### TC-ROADMAP-001: ROADMAP Contains Stage Info
- **Related**: DECISION-004
- **Prerequisites**: Project initialized
- **Steps**:
  1. Check docs/ROADMAP.md
  2. View stage information
- **Expected**: 
  - Contains current project lifecycle stage section
  - Shows stage focus and principles
  - Shows stage history
- **Status**: 🟢

### TC-CONTRIBUTING-001: CONTRIBUTING_AI.md Contains Stage-Based Rules
- **Related**: DECISION-004
- **Prerequisites**: CONTRIBUTING_AI.md generated
- **Steps**:
  1. Check CONTRIBUTING_AI.md
  2. Find stage-based collaboration rules section
- **Expected**: 
  - Contains "Stage-Based Collaboration Rules" section
  - Shows currently active stage
  - Lists rules for all stages
- **Status**: 🟢

### TC-UPGRADE-001: Protocol Upgrade Command
- **Related**: Core feature
- **Prerequisites**: Old version project config exists
- **Steps**:
  1. Run `vibecollab upgrade -c project.yaml`
  2. Check config merge results
- **Expected**: 
  - Preserves user custom config
  - Adds new config items
  - Regenerates CONTRIBUTING_AI.md
- **Status**: 🟢

### TC-DOMAIN-001: Domain Extension Loading
- **Related**: Core feature
- **Prerequisites**: Project initialized with domain template
- **Steps**:
  1. Run `vibecollab init -n "GameProject" -d game -o ./game-project`
  2. Check generated documents
- **Expected**: 
  - Loads game domain extension
  - Generates domain-specific sections
  - Contains domain-specific roles and processes
- **Status**: 🟢

## Phase 1a Test Cases (v0.4.2 — Protocol Check + PRD Management)

### TC-CHECK-001: Protocol Self-Check
- **Related**: v0.4.2
- **Prerequisites**: Project initialized with Git
- **Steps**:
  1. Run `vibecollab check`
  2. Run `vibecollab check --strict`
  3. Run `vibecollab check --json`
- **Expected**:
  - Checks Git protocol, document updates, dialogue flow protocol
  - `--strict` mode: warnings also count as failures (non-zero exit code)
  - `--json` outputs structured JSON report
  - Reports error/warning/info counts
- **Status**: 🟢 (unit test covered)

### TC-PRD-001: PRD Document Management
- **Related**: v0.4.2
- **Prerequisites**: Project initialized
- **Steps**:
  1. Check `docs/PRD.md` exists after `vibecollab init`
  2. Verify PRD contains requirement tracking structure
- **Expected**:
  - PRD.md auto-created on project initialization
  - Contains requirement status management structure
- **Status**: 🟢 (unit test covered)

---

## Phase 1b Test Cases (v0.5.0 — Multi-Developer Support)

### TC-DEV-001: Developer Identity Recognition
- **Related**: v0.5.0
- **Prerequisites**: Project initialized with multi-developer mode
- **Steps**:
  1. Run `vibecollab dev whoami`
  2. Set `VIBECOLLAB_DEVELOPER` environment variable, run again
- **Expected**:
  - Shows current developer identity (Git username / system user / env var)
  - Shows identity source
  - Environment variable overrides Git username
- **Status**: 🟢 (unit test covered)

### TC-DEV-002: Developer List and Status
- **Related**: v0.5.0
- **Prerequisites**: Multi-developer project with at least 2 developers
- **Steps**:
  1. Run `vibecollab dev list`
  2. Run `vibecollab dev status dev`
- **Expected**:
  - list: Shows all developers and their status
  - status: Shows developer detailed status (active tasks, recent activity)
- **Status**: 🟢 (unit test covered)

### TC-DEV-003: Developer Context Init and Sync
- **Related**: v0.5.0
- **Prerequisites**: Multi-developer project
- **Steps**:
  1. Run `vibecollab dev init -d newdev`
  2. Check `docs/developers/newdev/CONTEXT.md` exists
  3. Run `vibecollab dev sync`
  4. Check `docs/CONTEXT.md` for aggregated content
- **Expected**:
  - init creates developer context directory and CONTEXT.md
  - sync aggregates all developer contexts into global CONTEXT.md
- **Status**: 🟢 (unit test covered)

### TC-DEV-004: Multi-Developer Project Init
- **Related**: v0.5.0
- **Prerequisites**: vibe-collab installed
- **Steps**:
  1. Run `vibecollab init -n "MultiProject" -d generic --multi-dev`
  2. Check directory structure
- **Expected**:
  - Creates `docs/developers/` directory structure
  - project.yaml contains `multi_developer` config section
  - CONTRIBUTING_AI.md includes multi-developer collaboration protocol
- **Status**: 🟢 (unit test covered)

---

## Phase 1c Test Cases (v0.5.1 — Cross-Developer Conflict Detection)

### TC-CONFLICT-001: File Conflict Detection
- **Related**: v0.5.1
- **Prerequisites**: Multi-developer project, multiple developers have modified same files
- **Steps**:
  1. Run `vibecollab dev conflicts`
  2. Run `vibecollab dev conflicts --verbose`
- **Expected**:
  - Detects file conflicts between current developer and others
  - `--verbose` shows detailed conflict information
  - Identifies high/medium/low priority conflicts
- **Status**: 🟢 (unit test covered, 38 tests)

### TC-CONFLICT-002: Cross-Developer Conflict Detection
- **Related**: v0.5.1
- **Prerequisites**: Multi-developer project
- **Steps**:
  1. Run `vibecollab dev conflicts --between dev arch`
- **Expected**:
  - Detects conflicts between two specified developers
  - Reports file conflicts, task overlaps, dependency conflicts, naming conflicts
- **Status**: 🟢 (unit test covered)

### TC-CONFLICT-003: Dependency Circular Reference Detection
- **Related**: v0.5.1
- **Prerequisites**: Tasks with dependency chain
- **Steps**:
  1. Create tasks with circular dependencies
  2. Run `vibecollab dev conflicts`
- **Expected**:
  - DFS detects circular dependencies
  - Reports circular reference path
- **Status**: 🟢 (unit test covered)

---

## Phase 1d Test Cases (v0.5.4 — CLI Developer Switch)

### TC-SWITCH-001: Developer Switch Direct
- **Related**: v0.5.4
- **Prerequisites**: Multi-developer project
- **Steps**:
  1. Run `vibecollab dev switch dev`
  2. Run `vibecollab dev whoami`
- **Expected**:
  - Switch succeeds, persisted to `.vibecollab.local.yaml`
  - whoami shows switched identity with source "CLI switch"
- **Status**: 🟢 (unit test covered)

### TC-SWITCH-002: Developer Switch Interactive
- **Related**: v0.5.4
- **Prerequisites**: Multi-developer project
- **Steps**:
  1. Run `vibecollab dev switch` (no argument)
  2. Select developer from list
- **Expected**:
  - Shows interactive developer selection
  - Switch persisted after selection
- **Status**: 🟢 (unit test covered)

### TC-SWITCH-003: Developer Switch Clear
- **Related**: v0.5.4
- **Prerequisites**: Developer switch active
- **Steps**:
  1. Run `vibecollab dev switch --clear`
  2. Run `vibecollab dev whoami`
- **Expected**:
  - Clears switch setting from `.vibecollab.local.yaml`
  - whoami reverts to default identification strategy (Git/env/system)
- **Status**: 🟢 (unit test covered)

---

## Phase 2 Test Cases (v0.5.5 ~ v0.5.8)

### TC-EVENTLOG-001: EventLog Append and Read
- **Related**: v0.5.5
- **Prerequisites**: Project initialized
- **Steps**:
  1. Create `EventLog(project_root)`
  2. Call `event_log.append(Event(event_type=..., summary=..., actor=..., payload=...))`
  3. Call `event_log.read_all()`
- **Expected**:
  - Events persisted to `.vibecollab/events.jsonl`
  - Read returns all appended events
- **Status**: 🟢 (unit test covered)

### TC-TASK-001: TaskManager Lifecycle
- **Related**: v0.5.6
- **Prerequisites**: Project initialized
- **Steps**:
  1. Create `TaskManager(project_root, event_log)`
  2. `create_task(id=..., role=..., feature=...)`
  3. `transition_task(id, "validate")` → `transition_task(id, "solidify")`
- **Expected**:
  - Task state transitions IN_PROGRESS→REVIEW→DONE
  - Illegal transitions raise exceptions
- **Status**: 🟢 (unit test covered)

### TC-LLM-001: LLMClient Config and Call
- **Related**: v0.5.7
- **Prerequisites**: `VIBECOLLAB_LLM_API_KEY` environment variable set
- **Steps**:
  1. Create `LLMConfig()` reading environment variables
  2. Create `LLMClient(config)` and call `client.ask("test")`
- **Expected**:
  - Correctly parses provider/model/endpoint
  - API call returns response (or mock verifies request format)
- **Status**: 🟢 (unit test covered)

### TC-AI-001: AI Ask Single-Turn Question
- **Related**: v0.5.8
- **Prerequisites**: LLM config set
- **Steps**:
  1. Run `vibecollab ai ask "What's the project status?"`
- **Expected**:
  - Auto-injects project context
  - Returns LLM response
  - Records event to EventLog
- **Status**: 🟢 (unit test covered)

### TC-AI-002: AI Chat Multi-Turn Dialogue
- **Related**: v0.5.8
- **Prerequisites**: LLM config set
- **Steps**:
  1. Run `vibecollab ai chat`
  2. Enter questions, view responses
  3. Enter "exit" to quit
- **Expected**:
  - Maintains conversation history
  - Supports exit/quit/bye to quit
- **Status**: 🟢 (unit test covered)

### TC-AI-003: Agent Plan Read-Only Analysis
- **Related**: v0.5.8
- **Prerequisites**: LLM config set
- **Steps**:
  1. Run `vibecollab ai agent plan`
- **Expected**:
  - Outputs action plan
  - Does not execute any changes
- **Status**: 🟢 (unit test covered)

### TC-AI-004: Agent Run Single Cycle Execution
- **Related**: v0.5.8
- **Prerequisites**: LLM config set
- **Steps**:
  1. Run `vibecollab ai agent run`
  2. Run `vibecollab ai agent run --dry-run`
- **Expected**:
  - Completes Plan→Execute→Solidify single cycle
  - `--dry-run` only outputs plan without execution
  - pending-solidify gate blocks execution
- **Status**: 🟢 (unit test covered)

### TC-AI-005: Agent Serve Safety Gates
- **Related**: v0.5.8
- **Prerequisites**: LLM config set
- **Steps**:
  1. Run `vibecollab ai agent serve -n 1`
  2. Try running a second instance simultaneously
- **Expected**:
  - PID lock prevents multiple instances
  - Max cycle count limit enforced
  - RSS memory threshold check
  - Adaptive backoff + circuit breaker
- **Status**: 🟢 (unit test covered)

### TC-AI-006: Agent Status View
- **Related**: v0.5.8
- **Prerequisites**: None
- **Steps**:
  1. Run `vibecollab ai agent status`
- **Expected**:
  - Shows PID lock status
  - Shows LLM config
  - Shows task statistics and recent events
- **Status**: 🟢 (unit test covered)

---

## Phase 3 Test Cases (v0.5.9)

### TC-PATTERN-001: PatternEngine Basic Rendering
- **Related**: v0.5.9
- **Prerequisites**: Project initialized, project.yaml exists
- **Steps**:
  1. Create `PatternEngine(config, project_root)`
  2. Call `engine.render()`
- **Expected**:
  - Generates complete CONTRIBUTING_AI.md content
  - Contains all enabled sections defined in manifest.yaml
  - Section order matches manifest
- **Status**: 🟢 (unit test covered)

### TC-PATTERN-002: Manifest Condition Evaluation
- **Related**: v0.5.9
- **Prerequisites**: Config includes/excludes specific features
- **Steps**:
  1. Set `protocol_check.enabled: false`
  2. Render document
- **Expected**:
  - Sections with false conditions don't appear in output
  - `|default` syntax correctly handles missing config (default enabled)
- **Status**: 🟢 (unit test covered)

### TC-PATTERN-003: Template Overlay Local Override
- **Related**: v0.5.9
- **Prerequisites**: `.vibecollab/patterns/` directory exists in project
- **Steps**:
  1. Create custom templates in `.vibecollab/patterns/`
  2. Create local `manifest.yaml` (override/insert/exclude)
  3. Render document
- **Expected**:
  - Local templates take priority over built-in templates
  - Manifest merge correct: override, after-positioned insert, exclude
  - `list_patterns()` correctly annotates source: "local" / "builtin"
- **Status**: 🟢 (unit test covered, 8 overlay tests)

### TC-PATTERN-004: External Project Compatibility
- **Related**: v0.5.9
- **Prerequisites**: Using non-VibeCollab project's project.yaml
- **Steps**:
  1. Use test-project's project.yaml config
  2. Render CONTRIBUTING_AI.md
- **Expected**:
  - Correctly handles missing config items (lifecycle, multi_developer, etc.)
  - Output more complete than legacy (DEFAULT_STAGES fallback, |true defaults)
- **Status**: 🟢 (test_generate_full_config verified)

### TC-PATTERN-005: Legacy Removal Compatibility
- **Related**: v0.5.9
- **Prerequisites**: Using generator.py public API
- **Steps**:
  1. `generator = LLMContextGenerator.from_file(path)`
  2. `output = generator.generate()`
- **Expected**:
  - API unchanged, callers need no modification
  - Output generated by PatternEngine
  - cli.py, project.py etc. callers work normally
- **Status**: 🟢 (unit test covered)

### TC-HEALTH-001: HealthExtractor Basic Extraction
- **Related**: v0.5.9
- **Prerequisites**: Project initialized
- **Steps**:
  1. Create `HealthExtractor(project_root, config)`
  2. Call `extractor.extract()`
- **Expected**:
  - Returns `HealthReport` with signals list, score (0-100), summary
  - Extracts signals from ProtocolChecker / EventLog / TaskManager three data sources
- **Status**: 🟢 (unit test covered, 32 tests)

### TC-HEALTH-002: Health Score and Grade
- **Related**: v0.5.9
- **Prerequisites**: HealthReport contains different level signals
- **Steps**:
  1. Construct report with CRITICAL / WARNING / INFO signals
  2. Calculate score
- **Expected**:
  - CRITICAL -25 points, WARNING -10 points, INFO no deduction
  - Score floor 0, ceiling 100
  - Grade: A(90+) / B(80+) / C(70+) / D(60+) / F(<60)
- **Status**: 🟢 (unit test covered, 10 scoring tests)

### TC-HEALTH-003: Health Check CLI Command
- **Related**: v0.5.9
- **Prerequisites**: Project initialized
- **Steps**:
  1. Run `vibecollab health`
  2. Run `vibecollab health --json`
- **Expected**:
  - Shows health score and signal list
  - `--json` outputs JSON format
- **Status**: 🟢 (unit test covered)

### TC-EXECUTOR-001: AgentExecutor JSON Parsing
- **Related**: v0.5.9
- **Prerequisites**: LLM returns text with JSON code block
- **Steps**:
  1. Create `AgentExecutor(project_root)`
  2. Call `executor.parse_changes(llm_output)`
- **Expected**:
  - Supports three JSON formats: single object, array, `{"changes": [...]}`
  - Extracts from markdown ```json blocks
  - Returns `FileChange` list
- **Status**: 🟢 (unit test covered, 9 parse tests)

### TC-EXECUTOR-002: AgentExecutor Safety Checks
- **Related**: v0.5.9
- **Prerequisites**: Change list contains path traversal or protected files
- **Steps**:
  1. Submit changes with `../` path traversal
  2. Submit changes targeting `.git/` and other protected files
  3. Submit changes exceeding MAX_FILES_PER_CYCLE
- **Expected**:
  - Path traversal rejected
  - Protected files (.git/, .env, project.yaml, pyproject.toml) rejected
  - Over-limit changes rejected
- **Status**: 🟢 (unit test covered, 5 validation tests)

### TC-EXECUTOR-003: AgentExecutor Full Cycle
- **Related**: v0.5.9
- **Prerequisites**: LLM outputs valid changes
- **Steps**:
  1. Call `executor.execute_full_cycle(llm_output, commit_message, test_command)`
- **Expected**:
  - Parse → Validate → Apply → Test → Commit full flow
  - Auto-rollback on test failure
  - Returns git hash on success
- **Status**: 🟢 (unit test covered, 5 full cycle tests)

### TC-EXECUTOR-004: Agent Run Actual Execution Integration
- **Related**: v0.5.9
- **Prerequisites**: LLM config set
- **Steps**:
  1. Run `vibecollab ai agent run`
  2. LLM returns JSON change plan
- **Expected**:
  - AgentExecutor parses and executes changes
  - Auto git commit after tests pass
  - Rollback and report error on failure
- **Status**: 🟢 (unit test covered)

---

## Phase 4 Test Cases (v0.7.0 — Insight Solidification System)

### TC-INSIGHT-001: InsightManager CRUD
- **Related**: v0.7.0
- **Prerequisites**: Project initialized
- **Steps**:
  1. Create `InsightManager(project_root)`
  2. `create(title=..., tags=[...], category=..., body={...}, created_by=...)`
  3. `get(insight_id)`, `list_all()`, `update(insight_id, ...)`, `delete(insight_id, ...)`
- **Expected**:
  - Insight files persisted to `.vibecollab/insights/INS-xxx.yaml`
  - Registry auto-maintained `registry.yaml`
  - All operations record EventLog audit events
- **Status**: 🟢 (11 unit tests covered)

### TC-INSIGHT-002: Registry Weight Decay and Use Reward
- **Related**: v0.7.0
- **Prerequisites**: At least 1 insight created
- **Steps**:
  1. `record_use(insight_id, used_by=...)` — Use reward
  2. `apply_decay()` — Weight decay
  3. `get_active_insights()` — View active list
- **Expected**:
  - Use: weight +0.1, used_count +1
  - Decay: weight *= 0.95
  - weight < 0.1: auto active=false
- **Status**: 🟢 (8 unit tests covered)

### TC-INSIGHT-003: Tag Search (Jaccard × Weight)
- **Related**: v0.7.0
- **Prerequisites**: Multiple insights with different tags
- **Steps**:
  1. `search_by_tags(["python", "refactor"])`
  2. `search_by_category("workflow")`
- **Expected**:
  - Sorted by Jaccard similarity × registry weight
  - No match returns empty list
- **Status**: 🟢 (6 unit tests covered)

### TC-INSIGHT-004: Provenance derived_from
- **Related**: v0.7.0
- **Prerequisites**: Insights with derivation relationships
- **Steps**:
  1. Create INS-001, then INS-002 (derived_from: [INS-001])
  2. `get_derived_tree("INS-001")`
- **Expected**:
  - derived_from returns upstream IDs
  - derived_by returns downstream IDs
- **Status**: 🟢 (3 unit tests covered)

### TC-INSIGHT-005: Consistency Check (5-Item Full)
- **Related**: v0.7.0
- **Prerequisites**: Insight system has data
- **Steps**:
  1. `check_consistency()`
  2. Construct various inconsistency scenarios for testing
- **Expected**:
  - Registry ↔ file bidirectional consistency check
  - derived_from reference integrity check
  - Developer metadata reference integrity check
  - SHA-256 fingerprint consistency check
  - Low-weight active insights trigger warning
- **Status**: 🟢 (7 unit tests covered)

### TC-INSIGHT-006: Developer Tag Extension
- **Related**: v0.7.0
- **Prerequisites**: Developer metadata initialized
- **Steps**:
  1. `dm.set_tags(["arch", "python"], "dev")`
  2. `dm.add_contributed("INS-001", "dev")`
  3. `dm.add_bookmark("INS-002", "dev")`
- **Expected**:
  - tags/contributed/bookmarks correctly written to .metadata.yaml
  - Does not affect existing developer/created_at/total_updates fields
  - Dedup: duplicate adds return False
- **Status**: 🟢 (21 unit tests covered)

### TC-INSIGHT-007: CLI insight list/show/add/search
- **Related**: v0.7.0
- **Prerequisites**: Project initialized
- **Steps**:
  1. `vibecollab insight list [--active-only] [--json]`
  2. `vibecollab insight show INS-001`
  3. `vibecollab insight add --title ... --tags ... --category ... --scenario ... --approach ...`
  4. `vibecollab insight search --tags python`
- **Expected**:
  - list: Correctly lists/filters/JSON output
  - show: Shows details with body, registry state
  - add: Creates and records contributed
  - search: Matches and sorts by weight
- **Status**: 🟢 (12 unit tests covered)

### TC-INSIGHT-008: CLI insight use/decay/check/delete
- **Related**: v0.7.0
- **Prerequisites**: At least 1 insight
- **Steps**:
  1. `vibecollab insight use INS-001`
  2. `vibecollab insight decay [--dry-run]`
  3. `vibecollab insight check [--json]`
  4. `vibecollab insight delete INS-001 -y`
- **Expected**:
  - use: Weight reward +0.1
  - decay: Decay or preview
  - check: Consistency check report
  - delete: Removes file and registry entry
- **Status**: 🟢 (9 unit tests covered)

### TC-INSIGHT-009: vibecollab check --insights Integration
- **Related**: v0.7.0
- **Prerequisites**: Project initialized
- **Steps**:
  1. Run `vibecollab check --insights`
- **Expected**:
  - Protocol check + Insight consistency check executed jointly
  - Merged error/warning counts
  - Insight errors count toward exit code
- **Status**: 🟢 (needs manual verification)

### TC-INSIGHT-010: CLI insight bookmark/unbookmark/trace
- **Related**: v0.7.0
- **Prerequisites**: At least 1 insight
- **Steps**:
  1. `vibecollab insight bookmark INS-001`
  2. `vibecollab insight bookmark INS-001` (duplicate bookmark)
  3. `vibecollab insight unbookmark INS-001`
  4. `vibecollab insight trace INS-001 [--json]`
- **Expected**:
  - bookmark: Bookmark succeeds, duplicate shows already exists
  - unbookmark: Remove bookmark succeeds
  - trace: Shows ASCII provenance tree (upstream + current + downstream)
- **Status**: 🟢 (9 unit tests covered)

### TC-INSIGHT-011: CLI insight who/stats (Cross-Developer Sharing)
- **Related**: v0.7.0
- **Prerequisites**: Multi-developer environment + at least 1 insight
- **Steps**:
  1. `vibecollab insight who INS-001 [--json]`
  2. `vibecollab insight stats [--json]`
- **Expected**:
  - who: Shows creator/users/bookmarkers/contributors
  - stats: Aggregates total insights, total developers, usage count, most used/most shared
- **Status**: 🟢 (6 unit tests covered)

---

## Phase 5 Test Cases (v0.7.1 — Task-Insight Auto-Link)

### TC-TASKINS-001: Task Creation Auto-Links Insights
- **Related**: v0.7.1
- **Prerequisites**: InsightManager has created Insights
- **Steps**:
  1. Create `TaskManager(project_root, event_log, insight_manager=im)`
  2. `create_task(id=..., feature="refactor cache layer", description="optimize performance")`
- **Expected**:
  - Auto-extracts search tags from feature/description
  - Jaccard × weight matches related Insights
  - Results stored in `task.metadata["related_insights"]`
  - EventLog records link info
- **Status**: 🟢 (unit test covered, 28 tests)

### TC-TASKINS-002: Task Suggest Recommendations
- **Related**: v0.7.1
- **Prerequisites**: Existing Task + Insight data
- **Steps**:
  1. `vibecollab task suggest TASK-001`
- **Expected**:
  - Shows recommended related Insight list
  - Sorted by match score
- **Status**: 🟢 (unit test covered)

### TC-TASKINS-003: Backward Compatibility (No InsightManager)
- **Related**: v0.7.1
- **Prerequisites**: InsightManager not initialized
- **Steps**:
  1. Create `TaskManager(project_root, event_log)` (no insight_manager)
  2. `create_task(id=..., feature=...)`
- **Expected**:
  - Creates Task normally, no exception
  - `metadata["related_insights"]` is empty list
- **Status**: 🟢 (unit test covered)

---

## Phase 6 Test Cases (v0.8.0 — Config Management + Quality Hardening)

### TC-CONFIG-001: Config Setup Interactive Wizard
- **Related**: v0.8.0
- **Prerequisites**: vibe-collab installed
- **Steps**:
  1. Run `vibecollab config setup`
  2. Select Provider / Enter API Key / Select Base URL
- **Expected**:
  - Config written to `~/.vibecollab/config.yaml`
  - API Key securely stored
- **Status**: 🟢 (unit test covered, 38 tests)

### TC-CONFIG-002: Config Show View Configuration
- **Related**: v0.8.0
- **Prerequisites**: Config exists
- **Steps**:
  1. Run `vibecollab config show`
- **Expected**:
  - Shows three-layer merged result
  - Identifies source of each item (env/config/default)
  - API Key masked
- **Status**: 🟢 (unit test covered)

### TC-CONFIG-003: Config Set Single Item
- **Related**: v0.8.0
- **Prerequisites**: Config file exists
- **Steps**:
  1. Run `vibecollab config set llm.provider anthropic`
  2. Run `vibecollab config show` to verify
- **Expected**:
  - Corresponding key updated in config file
  - show output reflects new value
- **Status**: 🟢 (unit test covered)

### TC-CONFIG-004: Three-Layer Config Priority
- **Related**: v0.8.0
- **Prerequisites**: Both environment variable and config file set
- **Steps**:
  1. Set `VIBECOLLAB_LLM_PROVIDER=anthropic` environment variable
  2. Config file sets `llm.provider: openai`
  3. Call `resolve_llm_config()`
- **Expected**:
  - Environment variable wins: result is anthropic
  - Priority: env > config file > defaults
- **Status**: 🟢 (unit test covered)

### TC-FLAKY-001: test_onboard_basic Stability
- **Related**: v0.8.0 Bug Fix
- **Prerequisites**: Full test environment
- **Steps**:
  1. Run `python -m pytest` full test suite (2 consecutive times)
- **Expected**:
  - 779/779 passed
  - `test_onboard_basic` no longer fails due to `test_serve_lock_conflict` contamination
- **Status**: 🟢 (fix verified)

### TC-COV-001: Test Coverage ≥ 80%
- **Related**: v0.8.0
- **Prerequisites**: Full test environment
- **Steps**:
  1. Run `python -m pytest --cov=vibecollab --cov-report=term`
- **Expected**:
  - Total coverage ≥ 80% (current 81%)
  - Key modules: git_utils 100%, extension 100%, llmstxt 97%, lifecycle 93%, cli_lifecycle 92%, templates 91%
- **Status**: 🟢

### TC-PROMPT-001: Prompt Command Full Output
- **Related**: v0.8.0
- **Prerequisites**: Project initialized + CONTRIBUTING_AI.md generated
- **Steps**:
  1. Run `vibecollab prompt`
  2. Run `vibecollab prompt --compact`
  3. Run `vibecollab prompt --sections protocol,context`
- **Expected**:
  - Full output includes protocol sections, project state, Insight summary
  - `--compact` omits roadmap and role definitions
  - `--sections` selectively outputs only specified sections
- **Status**: ⚪ (pending verification)

### TC-PROMPT-002: Prompt Copy to Clipboard
- **Related**: v0.8.0
- **Prerequisites**: Project initialized (Windows environment)
- **Steps**:
  1. Run `vibecollab prompt --copy`
  2. Paste from clipboard
- **Expected**:
  - Content copied to clipboard via Windows `clip` command
  - Clipboard content matches terminal output
- **Status**: ⚪ (pending verification)

### TC-PROMPT-003: Prompt with Developer Context
- **Related**: v0.8.0
- **Prerequisites**: Multi-developer project
- **Steps**:
  1. Run `vibecollab prompt -d dev`
- **Expected**:
  - Output includes developer personal context from `docs/developers/dev/CONTEXT.md`
  - Developer-specific Insights prioritized
- **Status**: ⚪ (pending verification)

### TC-CHECK-002: Key Files Staleness Detection
- **Related**: v0.8.0
- **Prerequisites**: project.yaml configured `documentation.key_files` with `max_stale_days`
- **Steps**:
  1. Configure `QA_TEST_CASES.md` with `max_stale_days: 7`
  2. Ensure file not updated for >7 days
  3. Run `vibecollab check`
- **Expected**:
  - Reports warning for stale file with `update_trigger` hint
  - Files within threshold show no warning
  - Files without `max_stale_days` config are not checked
- **Status**: 🟢 (unit test covered, 3 tests)

---

## Phase 7 Test Cases (v0.9.0 — Semantic Search Engine)

### TC-INDEX-001: Document Indexing (Incremental)
- **Related**: v0.9.0
- **Prerequisites**: Project initialized, CONTRIBUTING_AI.md / CONTEXT.md / DECISIONS.md etc. exist
- **Steps**:
  1. Run `vibecollab index`
  2. Check if `.vibecollab/vectors/` has database files
  3. Run `vibecollab index` again
- **Expected**:
  - First run indexes all documents and Insight YAML
  - Outputs indexed document count and chunk count
  - Second run is incremental update (unchanged files skipped)
- **Status**: ⚪ (pending verification)

### TC-INDEX-002: Document Indexing (Rebuild)
- **Related**: v0.9.0
- **Prerequisites**: Existing index data
- **Steps**:
  1. Run `vibecollab index --rebuild`
- **Expected**:
  - Clears old index then rebuilds
  - Outputs "clearing old index" message
  - Search works normally after rebuild
- **Status**: ⚪ (pending verification)

### TC-INDEX-003: Backend Selection
- **Related**: v0.9.0
- **Prerequisites**: vibe-collab installed
- **Steps**:
  1. Run `vibecollab index --backend pure_python`
  2. Run `vibecollab index --backend auto` (auto-fallback without sentence-transformers)
- **Expected**:
  - `pure_python` uses trigram hash embedding (zero external dependencies)
  - `auto` falls back to pure_python without sentence-transformers
  - Both backends can complete indexing and subsequent search
- **Status**: ⚪ (pending verification)

### TC-SEARCH-001: Global Semantic Search
- **Related**: v0.9.0
- **Prerequisites**: `vibecollab index` has been run
- **Steps**:
  1. Run `vibecollab search "protocol check"`
  2. Run `vibecollab search "decision records" --type insight`
  3. Run `vibecollab search "task" --min-score 0.5`
- **Expected**:
  - Returns results sorted by relevance
  - Each result includes source (document/Insight) and relevance score
  - `--type` filters source type
  - `--min-score` filters low-score results
- **Status**: ⚪ (pending verification)

### TC-SEARCH-002: Insight Semantic Search
- **Related**: v0.9.0
- **Prerequisites**: `vibecollab index` run, Insight data exists
- **Steps**:
  1. Run `vibecollab insight search --semantic --tags "architecture"`
- **Expected**:
  - Vector cosine similarity based Insight search
  - Results include ID / title / score
- **Status**: ⚪ (pending verification)

---

## Phase 8 Test Cases (v0.9.1 — MCP Server + AI IDE Integration)

### TC-MCP-001: MCP Server Start (stdio)
- **Related**: v0.9.1
- **Prerequisites**: `pip install vibe-collab` with mcp dependency installed
- **Steps**:
  1. Run `vibecollab mcp serve`
  2. Send MCP initialize request via stdin
- **Expected**:
  - Server starts in stdio mode
  - Responds to MCP initialize handshake
  - Lists 14 Tools / 6 Resources / 1 Prompt
- **Status**: ⚪ (pending verification)

### TC-MCP-002: MCP Config Output
- **Related**: v0.9.1
- **Prerequisites**: vibe-collab installed
- **Steps**:
  1. Run `vibecollab mcp config --ide cursor`
  2. Run `vibecollab mcp config --ide cline`
  3. Run `vibecollab mcp config --ide codebuddy`
- **Expected**:
  - cursor: Outputs `.cursor/mcp.json` format JSON config
  - cline: Outputs Cline MCP config format
  - codebuddy: Outputs `.mcp.json` format
  - Config contains correct command / args / env
- **Status**: ⚪ (pending verification)

### TC-MCP-003: MCP Inject Auto-Injection
- **Related**: v0.9.1
- **Prerequisites**: vibe-collab installed
- **Steps**:
  1. Run `vibecollab mcp inject --ide codebuddy`
  2. Check `.mcp.json` file
- **Expected**:
  - Auto-creates/merges IDE config file
  - Existing config not overwritten (merge strategy)
  - Injects vibecollab MCP Server config
- **Status**: ⚪ (pending verification)

### TC-MCP-004: MCP Tool — onboard
- **Related**: v0.9.1
- **Prerequisites**: MCP Server running
- **Steps**:
  1. Call MCP tool `onboard`
- **Expected**:
  - Returns project overview, current progress, active tasks, recent events, Insight experience
  - Contains structured JSON data
- **Status**: ⚪ (pending verification)

### TC-MCP-005: MCP Tool — check
- **Related**: v0.9.1
- **Prerequisites**: MCP Server running
- **Steps**:
  1. Call MCP tool `check`
- **Expected**:
  - Returns protocol check report
  - Contains error / warning / info statistics
- **Status**: ⚪ (pending verification)

### TC-MCP-006: MCP Tool — insight_search
- **Related**: v0.9.1
- **Prerequisites**: MCP Server running, Insight data exists
- **Steps**:
  1. Call MCP tool `insight_search` with tags="architecture"
- **Expected**:
  - Returns matching Insight list
  - Sorted by weight
- **Status**: ⚪ (pending verification)

### TC-MCP-007: MCP Tool — search_docs
- **Related**: v0.9.1
- **Prerequisites**: MCP Server running, index built
- **Steps**:
  1. Call MCP tool `search_docs` with query="project deployment"
- **Expected**:
  - Returns semantic search results
  - Contains source file and score
- **Status**: ⚪ (pending verification)

### TC-MCP-008: MCP Resource Read
- **Related**: v0.9.1
- **Prerequisites**: MCP Server running
- **Steps**:
  1. Read Resource `contributing_ai`
  2. Read Resource `context`
  3. Read Resource `insights/list`
- **Expected**:
  - Returns full content of corresponding documents
  - insights/list returns YAML list of all Insights
- **Status**: ⚪ (pending verification)

### TC-MCP-009: MCP Prompt — start_conversation
- **Related**: v0.9.1
- **Prerequisites**: MCP Server running
- **Steps**:
  1. Call Prompt `start_conversation`
- **Expected**:
  - Returns system prompt with project info, CONTEXT summary, developer context
  - Lists available 14 MCP Tools
- **Status**: ⚪ (pending verification)

---

## Phase 9 Test Cases (v0.9.2 ~ v0.9.3 — Insight Signals + Task Workflow)

### TC-SIGNAL-001: Insight Suggest Candidate Recommendation
- **Related**: v0.9.2
- **Prerequisites**: Project has git commit history
- **Steps**:
  1. Ensure several git commits (with feat/fix/refactor keywords)
  2. Run `vibecollab insight suggest --json`
- **Expected**:
  - Extracts candidates from git commits, document changes, Task changes
  - Each candidate has title / tags / confidence / source_signal
  - JSON output contains candidates array
- **Status**: ⚪ (pending verification)

### TC-SIGNAL-002: Insight Suggest Interactive Mode
- **Related**: v0.9.2
- **Prerequisites**: Candidate Insights exist
- **Steps**:
  1. Run `vibecollab insight suggest`
  2. Enter number to select candidate
- **Expected**:
  - Lists candidate Insights
  - Auto-calls `insight add` on selection
  - Signal snapshot updated
- **Status**: ⚪ (pending verification)

### TC-SIGNAL-003: Insight Add Snapshot Linkage
- **Related**: v0.9.2
- **Prerequisites**: Project initialized
- **Steps**:
  1. Run `vibecollab insight add --title "Test" --tags test --category workflow --scenario "Test scenario" --approach "Test approach"`
  2. Check `.vibecollab/insight_signal.json`
- **Expected**:
  - Insight created successfully
  - Signal snapshot auto-updated (records current time and commit hash)
- **Status**: ⚪ (pending verification)

### TC-SESSION-001: MCP Session Save
- **Related**: v0.9.2
- **Prerequisites**: MCP Server running
- **Steps**:
  1. Call MCP tool `session_save` with summary="Completed feature X development"
- **Expected**:
  - Session saved to `.vibecollab/sessions/`
  - Returns session ID
- **Status**: ⚪ (pending verification)

### TC-TASK-CLI-001: Task Transition State Advance
- **Related**: v0.9.3
- **Prerequisites**: Task exists in TODO state
- **Steps**:
  1. `vibecollab task create --id TASK-QA-001 --role QA --feature "test feature"`
  2. `vibecollab task transition TASK-QA-001 IN_PROGRESS`
  3. `vibecollab task transition TASK-QA-001 REVIEW`
  4. `vibecollab task list --json`
- **Expected**:
  - State transitions correctly TODO → IN_PROGRESS → REVIEW
  - Illegal state jumps rejected (e.g., TODO → DONE)
  - list output correctly shows current state
- **Status**: ⚪ (pending verification)

### TC-TASK-CLI-002: Task Solidify
- **Related**: v0.9.3
- **Prerequisites**: Task in REVIEW state
- **Steps**:
  1. `vibecollab task solidify TASK-QA-001`
- **Expected**:
  - REVIEW → DONE solidification succeeds
  - Non-REVIEW state solidify rejected
  - EventLog records solidify event
- **Status**: ⚪ (pending verification)

### TC-TASK-CLI-003: Task Rollback
- **Related**: v0.9.3
- **Prerequisites**: Task in IN_PROGRESS or REVIEW state
- **Steps**:
  1. `vibecollab task transition TASK-QA-001 IN_PROGRESS`
  2. `vibecollab task rollback TASK-QA-001 --reason "needs redesign"`
- **Expected**:
  - IN_PROGRESS → TODO rollback succeeds
  - REVIEW → IN_PROGRESS rollback succeeds
  - TODO state cannot rollback
  - reason recorded to EventLog
- **Status**: ⚪ (pending verification)

### TC-ONBOARD-001: Onboard Command Full Output
- **Related**: v0.9.3
- **Prerequisites**: Project initialized with Task and EventLog data
- **Steps**:
  1. Run `vibecollab onboard --json`
- **Expected**:
  - JSON contains: project_info / current_status / active_tasks / task_summary / recent_events / insights / related_insights
  - Active Task overview with TODO/IN_PROGRESS/REVIEW statistics
  - Recent EventLog event summary
- **Status**: ⚪ (pending verification)

### TC-NEXT-001: Next Command Action Suggestions
- **Related**: v0.9.3
- **Prerequisites**: Project has various pending states
- **Steps**:
  1. Create several TODO and REVIEW state Tasks
  2. Run `vibecollab next --json`
- **Expected**:
  - REVIEW tasks recommend solidify (P1)
  - TODO backlog >3 triggers hint (P2)
  - Suggestions sorted by priority
- **Status**: ⚪ (pending verification)

---

## Phase 9a Test Cases (v0.9.5 — ROADMAP ↔ Task Integration)

### TC-ROADMAP-002: Roadmap Status Overview
- **Related**: v0.9.5
- **Prerequisites**: Project with ROADMAP.md containing `### vX.Y.Z` milestones and Task data
- **Steps**:
  1. Run `vibecollab roadmap status`
  2. Run `vibecollab roadmap status --json`
- **Expected**:
  - Shows per-milestone progress bar and Task status distribution
  - Detects orphan Tasks not linked to any ROADMAP item
  - JSON output contains milestones array with total/done/progress_pct/task_breakdown
- **Status**: ⚪ (pending verification)

### TC-ROADMAP-003: Roadmap Parse Structure
- **Related**: v0.9.5
- **Prerequisites**: ROADMAP.md with `### vX.Y.Z - Title` format milestones
- **Steps**:
  1. Run `vibecollab roadmap parse`
  2. Run `vibecollab roadmap parse --json`
- **Expected**:
  - Extracts milestones and checklist items from ROADMAP.md
  - Parses `TASK-{ROLE}-{SEQ}` ID references from checklist lines
  - JSON output contains parsed milestone structure
- **Status**: ⚪ (pending verification)

### TC-ROADMAP-004: Roadmap Sync Bidirectional
- **Related**: v0.9.5
- **Prerequisites**: ROADMAP.md + tasks.json with matching Task IDs
- **Steps**:
  1. Run `vibecollab roadmap sync --dry-run`
  2. Run `vibecollab roadmap sync -d both`
  3. Run `vibecollab roadmap sync -d roadmap_to_tasks`
  4. Run `vibecollab roadmap sync -d tasks_to_roadmap`
- **Expected**:
  - `--dry-run` previews changes without modifying files
  - `both`: ROADMAP `[x]` → Task DONE and Task DONE → ROADMAP `[x]`
  - Directional sync only applies changes in specified direction
  - Tasks get `milestone` field assigned from ROADMAP
- **Status**: ⚪ (pending verification)

### TC-ROADMAP-005: Task Milestone Field
- **Related**: v0.9.5
- **Prerequisites**: Project initialized
- **Steps**:
  1. `vibecollab task create --id TASK-DEV-010 --role DEV --feature "test feature" --milestone v0.9.5`
  2. `vibecollab task list --milestone v0.9.5`
  3. `vibecollab task show TASK-DEV-010`
- **Expected**:
  - Task created with milestone field
  - `--milestone` filter returns only matching tasks
  - show displays milestone field
- **Status**: ⚪ (pending verification)

### TC-ROADMAP-006: MCP Roadmap Tools
- **Related**: v0.9.5
- **Prerequisites**: MCP Server running
- **Steps**:
  1. Call MCP tool `roadmap_status`
  2. Call MCP tool `roadmap_sync` with dry_run=true
- **Expected**:
  - roadmap_status returns milestone progress overview
  - roadmap_sync returns sync preview results
- **Status**: ⚪ (pending verification)

---

## Phase 10 Test Cases (v0.9.4 — Insight Quality & Lifecycle)

### TC-DEDUP-001: Insight Auto-Dedup Detection
- **Related**: v0.9.4
- **Prerequisites**: Existing Insight data
- **Steps**:
  1. Run `vibecollab insight add --title "Existing Title" --tags existing,tag --category workflow --scenario "..." --approach "..."` (high title/tag overlap with existing Insight)
- **Expected**:
  - Duplicate detected, outputs similar Insight info
  - Creation blocked, suggests using `--force` to skip
- **Status**: ⚪ (pending verification)

### TC-DEDUP-002: Insight Force Create (Skip Dedup)
- **Related**: v0.9.4
- **Prerequisites**: Dedup detection would trigger
- **Steps**:
  1. Run `vibecollab insight add --title "Duplicate Title" --tags dup --category workflow --scenario "..." --approach "..." --force`
- **Expected**:
  - Skips dedup detection
  - Successfully creates Insight
- **Status**: ⚪ (pending verification)

### TC-GRAPH-001: Insight Relationship Graph (Text)
- **Related**: v0.9.4
- **Prerequisites**: Multiple Insights with derived_from relationships
- **Steps**:
  1. Run `vibecollab insight graph`
  2. Run `vibecollab insight graph --format json`
  3. Run `vibecollab insight graph --format mermaid`
- **Expected**:
  - Default text: Shows nodes/edges/statistics
  - JSON: Contains nodes / edges / stats (total_nodes / total_edges / isolated / components)
  - Mermaid: Outputs `graph LR` syntax, pasteable into Markdown for rendering
- **Status**: ⚪ (pending verification)

### TC-EXPORT-001: Insight Export
- **Related**: v0.9.4
- **Prerequisites**: Insight data exists
- **Steps**:
  1. Run `vibecollab insight export` (stdout)
  2. Run `vibecollab insight export -o insights_bundle.yaml`
  3. Run `vibecollab insight export --ids INS-001,INS-002`
  4. Run `vibecollab insight export --include-registry`
- **Expected**:
  - Outputs YAML format Insight Bundle
  - `-o` writes to file
  - `--ids` selective export
  - `--include-registry` includes registry state (weight/used_count/active)
- **Status**: ⚪ (pending verification)

### TC-IMPORT-001: Insight Import (skip strategy)
- **Related**: v0.9.4
- **Prerequisites**: Exported YAML bundle file
- **Steps**:
  1. Export project A's Insights: `vibecollab insight export -o bundle.yaml`
  2. Import in project B: `vibecollab insight import bundle.yaml`
  3. Import same file again
- **Expected**:
  - First import succeeds, shows import count
  - Second import: existing IDs skipped (default strategy)
  - Imported Insights auto-set `source.project` marking source
- **Status**: ⚪ (pending verification)

### TC-IMPORT-002: Insight Import (rename/overwrite strategies)
- **Related**: v0.9.4
- **Prerequisites**: Exported YAML bundle file, target project has same-ID Insights
- **Steps**:
  1. `vibecollab insight import bundle.yaml --strategy rename`
  2. `vibecollab insight import bundle.yaml --strategy overwrite`
- **Expected**:
  - rename: Conflicting IDs auto-assigned new IDs (INS-xxx)
  - overwrite: Overwrites existing Insights
- **Status**: ⚪ (pending verification)

---

## Phase 10a Test Cases (v0.9.7 — Directory Restructure + GBK Encoding Fix)

### TC-COMPAT-001: Sub-Package Import Compatibility
- **Related**: v0.9.7
- **Prerequisites**: vibe-collab installed
- **Steps**:
  1. `from vibecollab import LLMContextGenerator, TaskManager, EventLog`
  2. `from vibecollab.core.pattern_engine import PatternEngine`
  3. `from vibecollab.domain.task_manager import TaskManager`
  4. `from vibecollab.insight.manager import InsightManager`
- **Expected**:
  - Public API imports from `__init__.py` work unchanged
  - New sub-package paths (`core/`, `domain/`, `insight/`, `cli/`, `agent/`, `search/`, `utils/`) all importable
  - No ImportError for any documented API
- **Status**: 🟢 (unit test covered, 1344 tests)

### TC-COMPAT-002: GBK Terminal Encoding Safety
- **Related**: v0.9.7
- **Prerequisites**: Windows PowerShell/CMD with GBK (cp936) encoding
- **Steps**:
  1. Run `vibecollab check` (contains emoji output)
  2. Run `vibecollab roadmap status` (contains progress bar characters)
  3. Run `vibecollab health` (contains grade emoji)
- **Expected**:
  - No `UnicodeEncodeError` on any command
  - Emoji gracefully degraded to ASCII substitutes (✅→OK, ❌→X, etc.)
  - `ensure_safe_stdout()` reconfigures stdout errors mode to `replace`
  - Rich Console uses `safe_console()` factory
- **Status**: 🟢 (E2E verified, 36 CLI scenarios)

### TC-COMPAT-003: Strict Milestone Format
- **Related**: v0.9.7
- **Prerequisites**: ROADMAP.md with various heading formats
- **Steps**:
  1. Create ROADMAP.md with `### v0.1.0` (valid) and `#### v0.2.0` (invalid) headings
  2. Run `vibecollab roadmap status`
- **Expected**:
  - Only `### vX.Y.Z` level-3 headings recognized as milestones
  - `####` or `##` headings ignored
  - Zero milestones found → outputs `MILESTONE_FORMAT_HINT`
- **Status**: 🟢 (unit test covered)

---

## Phase 10b Test Cases (v0.10.1-dev — i18n + Pipeline + MCP Refactor)

### TC-I18N-001: CLI Language Switch
- **Related**: v0.10.1
- **Prerequisites**: vibe-collab installed with zh_CN locale
- **Steps**:
  1. Run `vibecollab --lang zh insight add --help`
  2. Run `VIBECOLLAB_LANG=zh vibecollab task list --help`
  3. Run `vibecollab insight add --help` (no lang flag)
- **Expected**:
  - `--lang zh` shows Chinese help text for all parameters
  - `VIBECOLLAB_LANG` environment variable also triggers Chinese
  - Without lang specification, defaults to English
  - Priority: `--lang` > `VIBECOLLAB_LANG` > English fallback
- **Status**: ⚪ (pending verification)

### TC-I18N-002: i18n String Coverage
- **Related**: v0.10.1
- **Prerequisites**: Source code and .pot file
- **Steps**:
  1. Check `src/vibecollab/i18n/locales/vibecollab.pot` for entry count
  2. Check `zh_CN/LC_MESSAGES/vibecollab.po` for translation count
  3. Verify `.mo` binary file exists
- **Expected**:
  - .pot contains 316 unique translatable strings
  - zh_CN .po has 131 key strings translated
  - .mo file compiled and included in wheel builds
- **Status**: ⚪ (pending verification)

### TC-PIPELINE-001: Pipeline Module Validation
- **Related**: v0.10.1
- **Prerequisites**: Project initialized
- **Steps**:
  1. Create `SchemaValidator` and validate project.yaml against schema
  2. Create `ActionRegistry` and register/execute actions
  3. Create `DocSyncChecker` and check document sync status
  4. Create `Pipeline` orchestrator and run full validation
- **Expected**:
  - SchemaValidator reports schema violations
  - ActionRegistry registers and executes named actions
  - DocSyncChecker detects out-of-sync documents
  - Pipeline orchestrates all validators in sequence
- **Status**: 🟢 (unit test covered, 69 tests)

### TC-MCP-010: MCP Direct API Performance
- **Related**: v0.10.1
- **Prerequisites**: MCP Server running
- **Steps**:
  1. Call any MCP tool (e.g., `onboard`, `check`)
  2. Measure response time
- **Expected**:
  - Tools respond via direct Python API calls (not subprocess)
  - No 10-30s latency from Python process startup
  - `_get_managers()` lazy initialization creates managers in-process
- **Status**: ⚪ (pending verification)

### TC-TASK-HOOK-001: Task Lifecycle Hooks
- **Related**: v0.10.1
- **Prerequisites**: Project initialized with tasks
- **Steps**:
  1. Create task and transition through TODO → IN_PROGRESS → REVIEW → DONE
  2. Check for `on_transition()` callback execution
  3. Check for `on_complete()` callback on DONE transition
- **Expected**:
  - `on_transition()` fires on each state change
  - `on_complete()` fires when task reaches DONE
  - Completion action hints displayed in CLI output
- **Status**: ⚪ (pending verification)

---

## Phase 11 — End-to-End Integration Tests (External Project Full Validation)

> The following test cases are for validating complete workflows on **real external projects other than VibeCollab itself**.

### TC-E2E-001: Fresh Project Init + Generate + Check
- **Related**: All versions
- **Prerequisites**: An existing code project with Git
- **Steps**:
  1. `cd /path/to/external-project`
  2. `pip install vibe-collab`
  3. `vibecollab init -n "ProjectName" -d generic`
  4. `vibecollab generate -c project.yaml`
  5. `vibecollab check`
  6. `vibecollab health`
  7. `vibecollab health --json`
- **Expected**:
  - init generates project.yaml + docs/ + .vibecollab/
  - generate creates CONTRIBUTING_AI.md + llms.txt
  - check no errors (warnings acceptable)
  - health outputs score and signals
  - No Python traceback / no UnicodeEncodeError
- **Status**: ⚪ (pending verification)

### TC-E2E-002: Insight Full Chain (Create→Search→Decay→Export→Import)
- **Related**: All versions
- **Prerequisites**: Project initialized
- **Steps**:
  1. `vibecollab insight add --title "Cache Strategy Selection" --tags cache,architecture --category architecture --scenario "High concurrency" --approach "Redis + local L2 cache"`
  2. `vibecollab insight add --title "API Error Handling Standard" --tags api,error-handling --category workflow --scenario "REST API" --approach "Unified ErrorResponse structure"`
  3. `vibecollab insight list`
  4. `vibecollab insight search --tags cache`
  5. `vibecollab insight use INS-001`
  6. `vibecollab insight decay --dry-run`
  7. `vibecollab insight graph`
  8. `vibecollab insight export -o /tmp/insights_backup.yaml`
  9. `vibecollab insight check`
- **Expected**:
  - Full chain no errors
  - search returns matching results
  - use increases weight
  - decay --dry-run doesn't actually modify
  - graph shows node info
  - export outputs valid YAML
  - check consistency passes
- **Status**: ⚪ (pending verification)

### TC-E2E-003: Task Full Chain (Create→Advance→Solidify)
- **Related**: All versions
- **Prerequisites**: Project initialized
- **Steps**:
  1. `vibecollab task create --id TASK-DEV-001 --role DEV --feature "User authentication module"`
  2. `vibecollab task list`
  3. `vibecollab task transition TASK-DEV-001 IN_PROGRESS`
  4. `vibecollab task transition TASK-DEV-001 REVIEW`
  5. `vibecollab task solidify TASK-DEV-001`
  6. `vibecollab task list --status DONE --json`
- **Expected**:
  - Creation succeeds, list shows TODO status
  - State transitions TODO → IN_PROGRESS → REVIEW → DONE
  - After solidify, list --status DONE returns this Task
  - --json outputs valid JSON
- **Status**: ⚪ (pending verification)

### TC-E2E-004: Onboard + Next Guidance Flow
- **Related**: All versions
- **Prerequisites**: Project has Task and Insight data
- **Steps**:
  1. `vibecollab onboard`
  2. `vibecollab onboard --json`
  3. `vibecollab next`
  4. `vibecollab next --json`
- **Expected**:
  - onboard: Shows project overview, current progress, active tasks, Insight summary
  - next: Shows action suggestions (sorted by priority)
  - --json outputs valid JSON
  - Empty project doesn't crash (graceful handling)
- **Status**: ⚪ (pending verification)

### TC-E2E-005: Index + Search Full Chain
- **Related**: v0.9.0+
- **Prerequisites**: Project initialized + generated
- **Steps**:
  1. `vibecollab index`
  2. `vibecollab search "project overview"`
  3. `vibecollab search "decision" --type insight`
  4. `vibecollab insight search --semantic --tags "architecture"`
- **Expected**:
  - index completes successfully (pure Python fallback available)
  - search returns results with source and score
  - semantic search returns Insights
- **Status**: ⚪ (pending verification)

### TC-E2E-006: MCP Server End-to-End (CodeBuddy/Cursor Integration)
- **Related**: v0.9.1+
- **Prerequisites**: `pip install vibe-collab`
- **Steps**:
  1. `vibecollab mcp config --ide codebuddy` (verify output format)
  2. `vibecollab mcp inject --ide codebuddy`
  3. Restart CodeBuddy/Cursor, confirm MCP Server connection
  4. Trigger `onboard` / `check` / `insight_search` tools in AI dialogue
- **Expected**:
  - config outputs valid JSON
  - inject generates correct config file
  - IDE connects to MCP Server successfully
  - Tool calls return project context
- **Status**: ⚪ (pending verification)

### TC-E2E-007: Prompt Command Generate LLM Context
- **Related**: v0.8.0+
- **Prerequisites**: Project initialized + generated
- **Steps**:
  1. `vibecollab prompt`
  2. `vibecollab prompt --compact`
  3. `vibecollab prompt --sections protocol,context`
  4. `vibecollab prompt --copy` (Windows verification)
- **Expected**:
  - Outputs Markdown format LLM prompt
  - --compact minimal version omits roadmap and role definitions
  - --sections selective output
  - --copy copies to clipboard
- **Status**: ⚪ (pending verification)

### TC-E2E-008: Cross-Project Insight Migration
- **Related**: v0.9.4
- **Prerequisites**: Two independent VibeCollab projects
- **Steps**:
  1. In project A: `vibecollab insight export -o /tmp/insights_a.yaml`
  2. In project B: `vibecollab insight import /tmp/insights_a.yaml --json`
  3. In project B: `vibecollab insight list`
  4. In project B: `vibecollab insight check`
- **Expected**:
  - Export contains vibecollab_version / exported_at / insights array
  - After import, Insights available in B
  - source.project marks source project
  - Consistency check passes
- **Status**: ⚪ (pending verification)

### TC-E2E-009: Windows Compatibility Verification
- **Related**: All versions
- **Prerequisites**: Windows PowerShell/CMD environment
- **Steps**:
  1. Run all TC-E2E-001 ~ 008 commands above
  2. Pay special attention to outputs with emoji/Chinese/special characters
- **Expected**:
  - All commands no UnicodeEncodeError
  - GBK terminal correctly degrades (emoji → ASCII substitutes)
  - Path separators handled correctly
- **Status**: ⚪ (pending verification)

### TC-E2E-010: Empty Project / Minimal Config Boundary Test
- **Related**: All versions
- **Prerequisites**: Empty directory + `vibecollab init` (minimal params)
- **Steps**:
  1. `mkdir empty-test && cd empty-test`
  2. `vibecollab init -n "EmptyProject" -d generic`
  3. `vibecollab check`
  4. `vibecollab onboard`
  5. `vibecollab next`
  6. `vibecollab task list`
  7. `vibecollab insight list`
  8. `vibecollab insight suggest --json`
- **Expected**:
  - All commands gracefully handle empty data
  - No traceback / no KeyError / no FileNotFoundError
  - Empty lists return friendly messages instead of errors
- **Status**: ⚪ (pending verification)

---

## Known Issues

### 🔴 High Priority Issues
(None)

### 🟡 Medium Priority Issues
(None — Windows GBK compatibility resolved via `_compat.py` unified layer)

### ⚪ Low Priority Issues (Deferred to v1.0)
- Large projects (100+ files) generation speed can be optimized
- `cli_insight.py` / `cli_task.py` not yet migrated to Rich output style (functional, only visual inconsistency)

---

*Last updated: 2026-03-05 (v0.10.1-dev) — 127 test cases covering v0.1.0 ~ v0.10.1*
