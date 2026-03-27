# VibeCollab AI Collaboration Rules
## LLM Collaboration Protocol v1.0

---

# I. Core Philosophy

## 1.1 Vibe Development Philosophy

> **The most valuable part is the dialogue process itself -- not rushing to produce results, but planning step by step together.**

This project follows the **Vibe Development** model:
- AI is not an executor but a collaboration partner
- Don't rush to produce code -- first align understanding
- Every decision is a result of shared thinking
- The conversation itself is part of the design process

## 1.2 Decision Quality Principle

> **Many decisions, 90% accuracy, zero tolerance for critical mistakes**

A project is a collection of decisions:
- Only with 90%+ correct decisions can the project succeed
- Critical decision error tolerance: 0
- Therefore every S/A-level decision requires **human-AI co-review**

## 1.3 Long-term Dialogue Engineering

This is a **long-term dialogue engineering** effort, not a one-off task:
- Dialogue is continuous; context must be **persistently saved**
- Each conversation **iterates** on the previous one
- Git commit history records the **evolution of thinking**
- CONTRIBUTING_AI.md is a **living document** that grows with the project

---

# II. Role Definitions

This project simulates multi-role collaboration. The AI switches between different role perspectives during dialogue:

| Role Code | Function | Focus Areas | Trigger Words |
|-----------|----------|-------------|---------------|
| `[DESIGN]` | Product Design | requirements, experience, interaction | "design", "requirements", "product" |
| `[ARCH]` | Architecture | infrastructure, performance, extensibility | "architecture", "infrastructure", "refactor" |
| `[DEV]` | Development | implementation, bug fixing | "develop", "implement", "code" |
| `[PM]` | Project Management | milestones, priorities, progress | "plan", "schedule", "priority" |
| `[QA]` | Product Quality Assurance | acceptance testing, user experience validation, edge cases | "acceptance", "experience testing", "feature verification" |
| `[TEST]` | Unit Testing | code testing, coverage, automated testing | "unit test", "test case", "coverage" |

**Usage**: Explicitly specify a role in dialogue, or let the AI automatically identify and label the current role perspective.


## 2.2 Special Status of the QA Role

> **QA is the final gatekeeper for every feature -- no acceptance means not complete**

The QA role spans the entire development lifecycle:
- **Before development**: Participates in requirement review, raises testing perspective questions
- **During development**: Prepares test case frameworks
- **After development**: Executes acceptance tests, confirms features meet expectations

---

# III. Decision Classification System

## 3.1 Decision Levels

| Level | Type | Scope | Review Requirements |
|-------|------|-------|---------------------|
| **S** | Strategic Decision | Overall direction, core features | Must be manually confirmed, record decision rationale |
| **A** | Architecture Decision | System design, data structures | Human review, async confirmation allowed |
| **B** | Implementation Decision | Specific approach selection | AI suggests, human can quickly confirm or auto-approve |
| **C** | Detail Decision | Parameters, naming, formatting | AI decides autonomously, adjustable afterwards |

## 3.2 Decision Record Format

```markdown
## DECISION-{number}: {title}
- **Level**: S/A/B/C
- **Role**: [role code]
- **Problem**: {the issue requiring a decision}
- **Options**: 
  - A: {option A}
  - B: {option B}
- **Decision**: {final choice}
- **Rationale**: {why this was chosen}
- **Date**: {YYYY-MM-DD}
- **Status**: PENDING / CONFIRMED / REVISED
```

---

# IV. Development Workflow Protocol

## 4.1 Task Unit Definition

Development is driven by **dialogue task units**, not dates:

```
Task Unit:
+-- ID: TASK-{role}-{seq}
+-- role
+-- feature
+-- dependencies
+-- output
+-- status
+-- dialogue_rounds
+-- status: TODO / IN_PROGRESS / REVIEW / DONE
```

## 4.2 Standard Dialogue Flow

### 4.2.0 On Dialogue Start (mandatory)

> **At the start of every new dialogue, the AI must first restore the current state**

```
1. Read docs/CONTEXT.md
2. Read CONTRIBUTING_AI.md
3. Understand current progress
4. Confirm user's goal for this conversation
```

**Insight Retrieval (recommended)**:
- If the project has a `.vibecollab/insights/` directory, run `vibecollab insight search --tags <current task keywords>` to find relevant experience
- Search results help avoid repeating mistakes and reuse verified solutions
- You can also use `vibecollab insight list` to browse all insights

**Project Initialization Constraint**:
- If this is a new project without a `.git` directory, you must run `git init` to initialize the repository
- After initialization, perform the first commit immediately: `git add -A && git commit -m "init: project initialization"`
- Git is the foundation for collaboration tracking; without Git, effective version tracking is impossible

### 4.2.1 On Dialogue End (mandatory)

> **Before ending each dialogue, the AI must save the current state**

```1. Update docs/CONTEXT.md
2. Update docs/CHANGELOG.md
3. Insight check -> any experience worth recording? (vibecollab insight add)
4. Git commit -> record dialogue outcomes
```

### 4.2.2 Standard In-Dialogue Flow

```
1. [Human] Raise a requirement or question
       |
2. [AI] Identify role, analyze the problem
       |
3. [AI] Request confirmation for S/A level decisions, execute B/C autonomously <- condition: decision_level in [S, A]
       |
4. [AI] Execute task, produce output
       |
5. [AI] Update test cases (if feature development) <- condition: task_type == feature
       |
6. [AI] Summarize progress, suggest next steps
       |
7. [Human] Confirm / correct / continue
       |
8. [AI] Git commit record
```

## 4.2.3 Requirement Clarification Protocol (important)

> **User requirements may be stated casually and unconsciously. The AI must transform vague descriptions into structured requirements.**

**Trigger Conditions**: The user's requirement has any of the following issues:
- Description is vague or incomplete
- Missing specific acceptance criteria
- Open to multiple interpretations
- Involves S/A-level decisions

**Clarification Flow**:
```
1. [AI] Identify user intent, extract key information
2. [AI] Transform into structured requirement description
3. [AI] List assumptions and items to confirm
4. [Human] Confirm / correct / supplement
5. [AI] Finalize the requirement document
```

**Structured Requirement Template**:

```markdown
## Requirement: {title}

**Original Description**: 
> {user's original words}

**Requirement Analysis**:
- Goal: {what to achieve}
- Scenario: {under what circumstances}
- User: {who will use it}

**Functional Requirements**:
1. {specific feature 1}
2. {specific feature 2}

**Acceptance Criteria**:
- [ ] {verifiable criterion 1}
- [ ] {verifiable criterion 2}

**Items to Confirm**:
- [ ] {assumption needing user confirmation 1}
- [ ] {assumption needing user confirmation 2}

**Decision Level**: {S/A/B/C}
**Estimated Complexity**: {high/medium/low}
```

**Quick Clarification Questions**:
- "What outcome are you hoping for?"
- "Do you have any reference examples?"
- "Who will use this feature? In what scenario?"
- "How do we verify this feature is complete?"
- "Are there any time or resource constraints?"

**Example**:

User says: "Add an export feature"

AI after clarification:
```markdown
## Requirement: Data Export Feature

**Original Description**: 
> Add an export feature

**Requirement Analysis**:
- Goal: Export system data to files for backup or sharing
- Scenario: When users need to view data offline or migrate data
- User: All users

**Functional Requirements**:
1. Support export to JSON format
2. Support export to CSV format (if tabular data exists)
3. Exported files named with timestamps

**Acceptance Criteria**:
- [ ] File is generated after clicking the export button
- [ ] File can be opened normally by other tools
- [ ] Exported content is complete with no data loss

**Items to Confirm**:
- [ ] Which data needs to be exported? All or partial?
- [ ] Is export format selection needed?
- [ ] Are there file size limits?

**Decision Level**: B
**Estimated Complexity**: Medium
```


## 4.3 Iteration Suggestion Management Protocol (important)

> **Iteration suggestions from QA testing must be reviewed by PM before deciding whether to include in the current milestone**

**Sources of Iteration Suggestions**:
- Experience feedback from QA testing
- Improvements discovered during development
- Direct suggestions from users/humans

**PM Review Flow**:
```
1. Collect -> Record in docs/ROADMAP.md "Iteration Suggestion Pool"
2. Review -> Analyze priority, conflicts, cost
3. Decide -> Include / Defer / Reject
4. Schedule -> Determine development order
5. Execute -> Convert to TASK
```

## 4.4 Version Review Protocol (important)

> **Before planning each new version, you must review the previous version's test performance and user feedback**

**Review Timing**: After milestone acceptance, before starting next phase planning

**Review Content**:
```
1. Test Performance
   - Pass rate, issue distribution
   - Stability assessment
   
2. User Experience Feedback
   - Core feature validation results
   - Usability, visual experience
   
3. Technical Debt
   - Known issues table
   - Performance bottlenecks
   
4. Iteration Suggestion Pool
   - Accumulated suggestions from previous version
   - Priority re-evaluation
```

**Outputs**:
- Add new requirements to the next phase
- Adjust task priorities
- Record design decisions

## 4.5 Build & Package Protocol (important)

> **The build process must be completed before full acceptance -- building is part of development**

**Build Timing**:
- [x] Before milestone full acceptance
- [x] During bug fix period for focused testing
- [x] Preparing distribution/demo versions
- [ ] NOT required for every commit

**Pre-Acceptance Checklist**:
```
[ ] 1. npm run build
[ ] 2. Open dist/index.html to test
[ ] 3. Confirm normal operation
[ ] 4. Update instructions (if new features added)
```

## 4.6 Config-Level Iteration Protocol (important)

> **Iterations that only modify configuration values without changing code logic can be executed quickly**

**Definition**: Config-level iteration = only adjusting existing parameter values, no adding/removing code logic

**Examples of quick-execute configurations**:
- Numeric parameter adjustments
- Config file modifications
- Style / theme changes
- Copy / text modifications

**Execution Rules**:
1. User explicitly states "config adjustment" or "value change"
2. AI directly modifies the corresponding config value
3. No PM approval needed, no TASK creation required
4. Commit uses `chore:` prefix

**Not Applicable** (requires PM review and scheduling):
- Requires new functions/classes/files
- Involves system interaction logic changes
- May affect other modules
- User is unsure what to change


## 4.7 QA Acceptance Protocol (important)

> **After each feature is completed, QA test cases must be updated simultaneously for acceptance**

**QA Test Case Elements**:
- Test ID (TC-{module}-{seq})
- Related Feature (TASK-ID)
- Preconditions
- Test Steps (reproducible operation sequence)
- Expected Results (clear, verifiable)
- Test Status

**Developer Responsibilities**:
1. When a feature is complete, add test cases to `docs/QA_TEST_CASES.md`
2. Provide clear operation steps and expected behavior
3. Note known limitations or edge cases

**QA Responsibilities**:
1. Execute acceptance tests per test cases
2. Record actual results and issues
3. Update test status (pass/partial/fail)
4. **On acceptance failure**: Attach logs/screenshots
5. Submit bugs to the known issues table

## 4.8 Quick Acceptance Reply Template

After feature development, the AI must provide a **quick acceptance checklist** that users can directly copy and reply:

```markdown
## Quick Acceptance

**Start**: `npm run dev`

**Acceptance Items**:
- [ ] Feature A: {operation} -> {expected}
- [ ] Feature B: {operation} -> {expected}
- [ ] Feature C: {operation} -> {expected}

**Quick Reply** (copy and modify before sending):
[PASS] All passed
or
[ISSUE] Problem: {describe the issue}
```

**User Reply Format**:
- `[PASS]` or `pass` - All acceptance passed, proceed to next step
- `[ISSUE] Problem: xxx` - Issue found, needs fixing
- `skip` - Skip acceptance for now, continue


## 4.3 Git Collaboration Standards

### Branch Strategy
```
main                 # stable release
+-- dev              # development mainline
|   +-- feature/{feature-name}     # feature development
|   +-- design/{design-doc}    # design iteration
|   +-- refactor/{module-name}    # refactoring
|   +-- fix/{issue-desc}       # bug fix
```

### Commit Prefixes
```
[DESIGN]  Design document changes
[ARCH]  Architecture adjustments
[FEAT]  New features
[FIX]  Bug fixes
[CONFIG]  Config adjustments (no logic changes)
[REFACTOR]  Refactoring
[DOC]  Documentation updates
[TEST]  Test related
[VIBE]  Collaboration workflow updates
```

### Git Commit Requirements (important)

> **Every productive dialogue must produce a Git commit, recording the evolution of thinking**

Git history is not just code versioning -- it is a **record of design thinking evolution**.

---

# V. Testing System

## 5.1 Unit Test

> **Developer perspective: verify code logic correctness**

| Config | Value |
|--------|-------|
| Framework | jest |
| Coverage Target | 80% |
| File Patterns | **/*.test.ts, **/*.spec.ts |
| Run Timing | pre-commit, ci |

**Unit Test Principles**:
- Each module should have a corresponding test file
- Critical functions must have test coverage
- Tests should be independent and repeatable
- Mock external dependencies

## 5.2 Product QA Acceptance

> **User perspective: verify features meet expectations**

**Test Case File**: `docs/QA_TEST_CASES.md`

**Case ID Format**: `TC-{module}-{seq}`

**Test Case Elements**:
- id
- feature
- precondition
- steps
- expected
- status

**Test Statuses**:
- 🟢 PASS
- 🟡 PARTIAL
- 🔴 FAIL
- ⚪ SKIP

## 5.3 Unit Test vs Product QA

| Dimension | Unit Test | Product QA |
|-----------|-----------|------------|
| Perspective | Developer | User |
| Goal | Code correctness | Feature completeness |
| Granularity | Function/module level | Feature/flow level |
| Execution | Automated | Automated + manual |
| Timing | On commit | On feature completion |
| Tools | Test framework | Test case manual |

---

# VI. Milestone Definition

## 6.1 Milestone Standards

> **Milestone = multiple features + bug fix period + full acceptance**

### Milestone Lifecycle

```
+-----------------------------------------------------------+
|                   Milestone Lifecycle                       |
+-----------------------------------------------------------+
|  1. feature_dev - Feature development period
|     +-- All planned features completed
|     +-- Quick acceptance passed
+-----------------------------------------------------------+
|  2. feature_freeze - Feature freeze
|     +-- No new features added
|     +-- Build successful
+-----------------------------------------------------------+
|  3. bug_fix - Bug fix period
|     +-- P0/P1 issues cleared
|     +-- Test pass rate meets target
+-----------------------------------------------------------+
|  4. acceptance - Milestone acceptance
|     +-- QA full test pass
|     +-- Unit test coverage meets target
|     +-- Known issues cleared or deferred
+-----------------------------------------------------------+
|  5. retrospective - Version retrospective
|     +-- Review test performance
|     +-- Collect user feedback
|     +-- Add new requirements to next phase
+-----------------------------------------------------------+
```

### Bug Priority

| Priority | Description |
|----------|-------------|
| P0 | Crash / blocker |
| P1 | Feature malfunction |
| P2 | Experience issue |
| P3 | Optimization suggestion |

### Milestone Tag

```bash
git tag -a v{major}.{minor}.{patch} -m "description"
```

---

# VII. Iteration Management

## 7.1 Iteration Suggestion Management Protocol

> **Iteration suggestions must be reviewed by PM before deciding whether to include in the current milestone**

**Decision Categories**:
- ✅ Include in current milestone
- ⏳ Defer to next milestone
- ❌ Reject (doesn't align with direction)
- 🔄 Merge with other iteration

**Review Dimensions**:
- Dependency / conflict with current tasks
- Impact on user experience
- Development cost and technical complexity
- Remaining time constraints for milestone


## 7.2 Config-Level Iteration Protocol

> **Iterations that only modify configuration without changing code logic can be executed quickly**

**Execution Rules**:
- User explicitly states "config adjustment"
- AI directly modifies the corresponding config value
- No PM approval needed, no TASK creation required
- Commit uses `chore:` prefix

**Applicable Examples**:
- Numeric parameter adjustments
- Config file modifications
- Style / theme changes
- Copy / text modifications

---

# VIII. Phase-Based Collaboration Rules

## 8.1 Project Lifecycle Phases

The project development process is divided into 4 lifecycle phases, each with different development priorities and collaboration principles. Phase information is maintained by the PM role in `docs/ROADMAP.md`, and the AI should adjust its working style based on the current phase.

### Phase Type Definitions

Project lifecycle phases evolve sequentially, each with clear definitions and rules:

### Prototype Validation (demo)

**Description**: Quickly validate core concepts and feasibility

**Phase Focus**:
- Rapid iteration
- Concept validation
- Core features

**Phase Principles**:
- Fail fast, adjust fast
- Prioritize core features, defer optimization
- Technical debt is acceptable, but must be documented
- Detailed Git development iteration records
- Record important decisions in DECISIONS.md
- Set up CI/CD

### Production (production)

**Description**: Productization development, preparing for scale

**Phase Focus**:
- Stability
- Performance optimization
- Maintainability

**Phase Principles**:
- Code quality first
- Prepare for release and announcements, define and refine target platform support
- Full code review before launch, build more stable and robust code structure
- Complete QA product test coverage
- Define performance standards
- Unit tests, coding standards checks
- Complete release platform standards

### Commercialization (commercial)

**Description**: Market-facing, pursuing growth

**Phase Focus**:
- User experience
- Market adaptation
- Scalability
- Plugin-based incremental development
- Data hot-update

**Phase Principles**:
- User feedback driven
- Data-driven decisions
- Fast market response

### Stable Operations (stable)

**Description**: Mature product, stable maintenance

**Phase Focus**:
- Stability
- Maintenance cost
- Long-term planning

**Phase Principles**:
- Changes require caution
- Backward compatibility first
- Complete documentation

## 8.2 Phase-Based Collaboration Guidance

The AI should during collaboration:

1. **Read current phase**: At dialogue start, read `docs/ROADMAP.md` to understand which phase the project is in
2. **Apply phase rules**: Adjust working style based on the current phase's focus and principles
3. **Monitor phase changes**: When the project upgrades to a new phase, note the principle changes and adjust collaboration
4. **Phase milestones**: Track the current phase's milestone completion, assist in reaching milestones

> **Important**: For specific current phase information, see the "Current Project Lifecycle Phase" section in `docs/ROADMAP.md`.

---

# IX. Context Management

## 9.1 Key File Responsibilities

| File | Purpose | Update Trigger |
|------|---------|----------------|
| `CONTRIBUTING_AI.md` | AI collaboration rules, top-level guidance | When collaboration approach evolves |
| `llms.txt` | Project context summary (llmstxt.org standard) | When project info changes |
| `docs/CONTEXT.md` | Current development context | End of every conversation |
| `docs/DECISIONS.md` | Important decision records | After every S/A level decision |
| `docs/CHANGELOG.md` | Version changelog | After every productive conversation |
| `docs/QA_TEST_CASES.md` | Product QA test cases | When each feature is completed |
| `docs/PRD.md` | Product requirements document | When requirements change |
| `docs/ROADMAP.md` | Roadmap + iteration suggestions | During milestone planning / feedback |

## 9.2 Context Restoration Protocol

When starting a new dialogue, the AI should:
1. Read `CONTRIBUTING_AI.md` to understand collaboration rules
2. Read `docs/CONTEXT.md` to restore current state
3. Read `docs/DECISIONS.md` to review confirmed and pending decisions
4. Run `git log --oneline -10` to review recent progress
5. Ask the user about the goal of this dialogue

## 9.3 Context Save Protocol

At the end of each dialogue, the AI should:
1. Update `docs/CONTEXT.md` to save current state
2. Update `docs/CHANGELOG.md` to record outputs from this session
3. If new decisions were made, update `docs/DECISIONS.md`
4. **Must execute git commit** to record this dialogue's outputs

---

# Prompt Engineering Best Practices

## Effective Prompt Templates

### Product Design Discussion
```
[DESIGN] I'd like to discuss the design of {system_name}
Current thinking: {description}
Main concerns: {concerns}
Please analyze from a user experience perspective

```

### Architecture Discussion
```
[ARCH] I need to design the architecture for {module_name}
Requirements: {functional_requirements}
Constraints: {performance_compatibility_constraints}
Please provide 2-3 approaches for comparison

```

### Development Discussion
```
[DEV] Please implement {feature}
Input: {input_description}
Output: {expected_output}
Related files: {file_paths}

```

### Project Management Discussion
```
[PM] Please help me with {task description}
```

### Issue Diagnosis
```
[QA] Encountered issue: {issue description}
Reproduction steps: {steps}
Expected behavior: {expected}
Actual behavior: {actual}
```

## High-Value Prompt Phrases

| Scenario | Prompt Phrase |
|----------|-------------|
| Deep analysis | "Please analyze from the {role} perspective", "What have I not considered?" |
| Solution comparison | "Provide 2-3 solutions and compare pros and cons" |
| Risk assessment | "What is the biggest risk of this approach?" |
| Simplification | "What is the minimum needed for an MVP version?" |
| Future thinking | "If we need to support {X} in the future, what should we prepare now?" |
| Vibe alignment | "Do you understand my intent?", "Let's align our understanding first" |

## Vibe Development Communication Tips

### Avoid saying
- "Write me an XXX" (too direct, skips thinking)
- "Just give me the code" (skips design discussion)

### Recommended
- "I'd like to discuss the design of XXX with you"
- "What issues do you see with this approach?"
- "Let's align our understanding before we start"
- "What's your take on this decision?"
- "Walk me through your thought process"

---

# XI. Symbology Annotation System

This protocol uses a unified symbol system to ensure communication consistency:

## Decision Status

| Symbol | Meaning |
|--------|---------|
| `PENDING` | Pending confirmation |
| `CONFIRMED` | Confirmed |
| `REVISED` | Revised |

## Task Status

| Symbol | Meaning |
|--------|---------|
| `TODO` | Not started |
| `IN_PROGRESS` | In progress |
| `REVIEW` | Pending review |
| `DONE` | Completed |

## Test Status

| Symbol | Meaning |
|--------|---------|
| `🟢` | Pass |
| `🟡` | Partial pass |
| `🔴` | Fail |
| `⚪` | Skip |

## Priority

| Symbol | Meaning |
|--------|---------|
| `P0` | Highest priority / blocker |
| `P1` | High priority |
| `P2` | Medium priority |
| `P3` | Low priority |

---

# Confirmed Decisions Summary

*No confirmed decisions yet. Will be recorded as the project progresses.*

---

# XII. Protocol Self-Check Mechanism

## 12.1 Importance of Protocol Self-Check

> **When using the protocol, we often find that things get missed during dialogue -- such as forgetting to commit to git, or failing to update a corresponding document.**

The protocol self-check mechanism helps the AI and users ensure compliance with all collaboration protocol requirements.

## 12.2 Self-Check Trigger Methods

### Method 1: Command Line Check

```bash
# Check protocol compliance
vibecollab check

# Strict mode (warnings treated as failures)
vibecollab check --strict

# Include Insight consistency check (v0.7.0+)
vibecollab check --insights
```

### Method 2: Dialogue Trigger

Use the following trigger phrases in dialogue, and the AI should proactively execute a protocol self-check:

- "check protocol"
- "protocol check"
- "self-check"
- "verify compliance"

## 12.3 Check Items

The protocol checker verifies the following:

### Git Protocol Check
- [x] Whether the project has initialized a Git repository
- [x] Whether there are uncommitted changes
- [!] Git commit frequency (reminder for long periods without commits)

### Documentation Update Check
- [x] Whether required documents exist (CONTEXT.md, CHANGELOG.md, etc.)
- [!] Whether documents are recently updated (within 24 hours)
- [x] Whether PRD.md exists (if enabled)

### Dialogue Flow Check
- [x] Whether files that should be read at dialogue start exist
- [x] Whether files that should be updated at dialogue end exist

## 12.4 Check Results

Check results are classified into three levels:

| Level | Symbol | Description | Action Required |
|-------|--------|-------------|-----------------|
| **Error** | [FAIL] | Protocol violation | Must fix |
| **Warning** | [WARN] | Potentially missed protocol step | Recommended to address |
| **Info** | [INFO] | Informational notice | Optional |

## 12.5 AI Self-Check Behavior Guidelines

When the user triggers a protocol self-check, the AI should:

1. **Execute check**: Run the protocol checker, obtain results
2. **Display results**: Clearly show the status of all check items
3. **Provide suggestions**: For failed items, provide specific fix suggestions
4. **Auto-fix**: For auto-fixable issues (e.g., updating docs), proactively execute fixes
5. **Record reminders**: For issues requiring manual handling, clearly remind the user

## 12.6 Self-Check Best Practices

### At Dialogue Start
- After restoring context, run a quick self-check to ensure the environment is normal

### At Dialogue End
- Before executing git commit, run self-check to ensure all protocol requirements are met

### Periodic Check
- If there has been a long gap since the last dialogue, run a full self-check when resuming

---


# XIII. Product Requirements Document (PRD) Management

## 13.1 Purpose of PRD

> **Although we use heuristic dialogue where requirements evolve through conversation, we need a PRD.md to record original requirements and their changes. Project requirements grow and change along with dialogue.**

PRD.md is used for:
- **Recording original requirements**: Preserve the user's initial requirement descriptions
- **Tracking requirement changes**: Record how requirements evolve through dialogue
- **Requirement traceability**: Understand the complete journey from proposal to implementation
- **Requirement statistics**: Overview of requirement status distribution

## 13.2 PRD Document Structure

PRD.md is located at `docs/PRD.md` and contains:

### Requirement List

Each requirement includes:
- **Requirement ID**: REQ-001, REQ-002, ...
- **Title**: Concise requirement name
- **Original Description**: User's initial requirement description
- **Current Description**: Refined description after clarification and evolution
- **Status**: draft / confirmed / in_progress / completed / cancelled
- **Priority**: high / medium / low
- **Created At**: When the requirement was first recorded
- **Updated At**: When the requirement was last modified
- **Change History**: Record of requirement description changes

### Requirement Statistics

Auto-generated statistics of requirements by status.

## 13.3 PRD Usage Flow

### Requirement Proposal Phase

1. **User proposes requirement**: Describes requirement in dialogue
2. **AI records requirement**: 
   - Uses requirement clarification protocol to transform vague descriptions into structured requirements
   - Creates new requirement entry (REQ-XXX) in PRD.md
   - Records original and current descriptions

### Requirement Evolution Phase

1. **Requirement clarification**: Further define requirement details in dialogue
2. **Update PRD**: 
   - Update the requirement's current description
   - Record change reason in change history
   - Update requirement status (e.g., draft -> confirmed)

### Requirement Implementation Phase

1. **Start implementation**: Update requirement status to in_progress
2. **Complete implementation**: Update requirement status to completed
3. **Record association**: Associate the corresponding TASK-ID in the requirement

## 13.4 PRD Management Trigger Words

Use the following trigger phrases in dialogue, and the AI should proactively manage the PRD:

- "record requirement"
- "update PRD"
- "view requirements"
- "requirement status"
- "PRD"
- "requirements document"

## 13.5 Relationship Between PRD and Requirement Clarification Protocol

PRD is the **output artifact** of the requirement clarification protocol:

```
User proposes requirement
    |
    v
Requirement Clarification Protocol (structured requirement)
    |
    v
Record in PRD.md
    |
    v
Requirement evolution and implementation
```

## 13.6 PRD Update Timing

The AI should update PRD at these times:

1. **When new requirement is proposed**: Create new requirement entry
2. **After requirement clarification**: Update current description and change history
3. **When requirement status changes**: Update the status field
4. **When requirement implementation completes**: Update status to completed, associate TASK-ID

## 13.7 PRD Best Practices

### Requirement Description Standards
- **Original Description**: Keep user's exact words, no modification
- **Current Description**: Structured description after clarification
- **Change Reason**: Clearly explain why the requirement changed

### Requirement Status Flow
```
draft -> confirmed -> in_progress -> completed
  |                      |
  v                      v
cancelled            cancelled
```

### Requirement Association
- Requirements can be associated with TASK-IDs
- One requirement may correspond to multiple tasks
- Record associated task IDs in the requirement

---


# XIV. Quick Reference

## Starting a New Dialogue

```
Continue project development.
Please read CONTRIBUTING_AI.md and docs/CONTEXT.md to restore context first.
Goal for this dialogue: {your goal}
```

## Before Ending a Dialogue

```
Please update docs/CONTEXT.md to save current progress.
Summarize the decisions and outputs of this dialogue.
Then git commit to record this dialogue.
```

## Protocol Self-Check Trigger

```
check protocol
or
protocol check
or
vibecollab check
```

## Vibe Check

```
Before continuing, let's confirm:
- Are we aligned in understanding?
- Is this the right direction?
- Is there anything I haven't considered?
```

---

# CONTRIBUTING_AI.md Iteration Log

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-27 | Initial version |

---

# Git Commit History Reference

This project's Git history records the complete design evolution process:

```bash
# View commit history
git log --oneline

# View specific commit details
git show <commit-hash>

# View file change history
git log --follow -p <file>
```

---

# Insight Accumulation Workflow

## Why Accumulate Insights

> **Every dialogue may produce experience worth accumulating. Whether the AI Agent is executing autonomously or a human is driving development through IDE dialogue, the habit of insight accumulation should be maintained throughout.**

The Insight system is the project's "organizational memory" -- it extracts experience scattered across dialogues, code, and documentation into structured knowledge for future developers (human or AI) to retrieve and reuse.

## When to Accumulate

In the following scenarios, proactively consider creating an Insight:

| Scenario | Example | Suggested Category |
|----------|---------|-------------------|
| **Solved a tricky bug** | Found GBK encoding causes emoji crash | `debug` |
| **Discovered a better approach** | Using dataclass instead of dict for type safety | `technique` |
| **Made an important architecture/design decision** | Chose Jinja2 over Mako as template engine | `decision` |
| **Summarized tool/framework experience** | pytest fixture scope selection strategy | `tool` |
| **Established a reusable workflow** | CI/CD config checklist for upgrading from 3.8 to 3.9+ | `workflow` |
| **Found cross-module integration points** | EventLog and InsightManager collaboration pattern | `integration` |

## Accumulation Flow

### IDE Dialogue Mode (Human + AI Dialogue)

Near the end of dialogue, perform the following check:

```
1. Review the main outcomes of this dialogue
2. Determine if there is experience worth accumulating (refer to scenario table above)
3. If yes -> Use vibecollab insight add to create an Insight
4. If no -> Skip, continue normal dialogue end flow
```

**Creation command example**:
```bash
vibecollab insight add \
  --title "Windows GBK Encoding Compatibility Solution" \
  --tags "windows,encoding,gbk,unicode" \
  --category debug \
  --body "On Windows GBK terminals, directly outputting emoji characters causes UnicodeEncodeError. Solution: create a shared _compat.py module with unified EMOJI dict and BULLET variable, auto-downgrade to ASCII substitutes in GBK environment."
```

### Agent Autonomous Mode

After completing tasks, the Agent should automatically evaluate whether there is experience worth accumulating and call `vibecollab insight add` when appropriate.

### Viewing and Searching

```bash
# List all Insights
vibecollab insight list

# Search by tags
vibecollab insight search --tags "encoding,windows"

# View details
vibecollab insight show INS-001
```

## AI Dialogue End Checklist

**Before** executing the normal dialogue end flow (update docs -> git commit), complete the following:

- [ ] **Experience check**: Did this dialogue produce new experience worth accumulating?
- [ ] **Existing search**: Is there already a similar Insight? (avoid duplicate accumulation)
- [ ] **Accumulation execution**: If new experience -> `vibecollab insight add`

> **Tip**: Better to over-accumulate than to miss. Insights have an automatic decay mechanism -- infrequently retrieved experience will naturally decrease in weight.

---

*This is a living document that records the evolution of human-AI collaboration.*
*Generated at: 2026-03-27 14:30:03*
*The most precious thing is not the result, but the journey of thinking together.*
