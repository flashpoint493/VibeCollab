# VibeCollab Skill for OpenCode

## Overview

VibeCollab is a configurable AI collaboration protocol framework with built-in knowledge capture (Insight) and task management. Use it to maintain structured context across conversations.

## When to Use

- Starting a new conversation on a VibeCollab-managed project
- Need to search past development experiences (Insights)
- Want to capture reusable knowledge from current work
- Need to check project protocol compliance
- Managing tasks and roadmap items

## Available Commands

### Core Workflow Commands

```bash
# Start of conversation - get full project context
vibecollab onboard

# Check protocol compliance (includes Insight consistency by default)
vibecollab check

# Get next action suggestions based on project state
vibecollab next

# Save conversation summary at the end
vibecollab session_save --summary "What was accomplished" --developer <role>
```

### Insight Knowledge System

```bash
# Search existing Insights
vibecollab insight search "<query>" [--tags <tag1,tag2>]

# Add a new Insight
vibecollab insight add --title "<title>" --tags "<tag1,tag2>" --category <technique|workflow|decision|debug|tool|integration>

# Get AI-suggested Insights based on recent changes
vibecollab insight suggest

# List all Insights
vibecollab insight list

# Show specific Insight details
vibecollab insight show <INS-XXX>
```

### Task Management

```bash
# List current tasks
vibecollab task list

# Create a new task
vibecollab task create --id TASK-DEV-001 --role DEV --feature "Feature description"

# Transition task status
vibecollab task transition TASK-DEV-001 --status <TODO|IN_PROGRESS|REVIEW|DONE> --reason "Why"

# Solidify completed task
vibecollab task solidify TASK-DEV-001
```

### Documentation & Search

```bash
# Index documents for semantic search
vibecollab index [--rebuild]

# Semantic search across docs and Insights
vibecollab search "<query>"

# View ROADMAP status
vibecollab roadmap status

# Sync ROADMAP with tasks
vibecollab roadmap sync
```

### Project Health

```bash
# Get project health score (0-100)
vibecollab health [--json]

# Validate project configuration
vibecollab validate -c project.yaml
```

## Standard Conversation Flow

### At Conversation Start

1. Check if project uses VibeCollab (look for `project.yaml` or `CONTRIBUTING_AI.md`)
2. If yes, run: `vibecollab onboard` to get full context
3. Review `docs/CONTEXT.md` for current state
4. Review `docs/DECISIONS.md` for important decisions
5. Search relevant Insights: `vibecollab insight search "<current topic>"`
6. List active tasks: `vibecollab task list`

### During Conversation

- When encountering reusable knowledge → `vibecollab insight add ...`
- When making important decisions → Update `docs/DECISIONS.md`
- When creating new work items → `vibecollab task create ...`
- When finishing work → `vibecollab task transition ... --status DONE`

### At Conversation End

1. Update `docs/CONTEXT.md` with current state
2. Update `docs/CHANGELOG.md` with changes made
3. Check for Insights to capture: `vibecollab insight suggest`
4. Run compliance check: `vibecollab check`
5. Save session: `vibecollab session_save --summary "..."`
6. Suggest git commit if there are uncommitted changes

## Project Structure

A VibeCollab project has these key files:

```
project-root/
├── project.yaml              # Main configuration file
├── CONTRIBUTING_AI.md        # AI collaboration protocol rules
├── llms.txt                  # Project context (llmstxt.org standard)
└── docs/
    ├── CONTEXT.md            # Current project state (updated per session)
    ├── DECISIONS.md          # Decision records (S/A/B/C tiers)
    ├── CHANGELOG.md          # Session-level changelog
    ├── ROADMAP.md            # Milestones and tasks
    └── QA_TEST_CASES.md      # Test cases (if applicable)
```

## Decision Tiers

When recording decisions in `docs/DECISIONS.md`:

| Tier | Type | Scope | Review |
|------|------|-------|--------|
| **S** | Strategic | Overall direction | Must have human approval |
| **A** | Architecture | System design | Human review |
| **B** | Implementation | Specific approach | Quick confirm |
| **C** | Detail | Naming, params | AI decides autonomously |

## Multi-Role Support

For projects with multiple roles (DEV, QA, ARCH, PM, etc.):

```bash
# Check current role context
vibecollab dev whoami

# Switch to different role
vibecollab dev switch <role>

# View role-specific context
vibecollab onboard -d <role>
```

## Best Practices

1. **Always onboard first** - Get context before starting work
2. **Capture Insights continuously** - Don't wait until the end
3. **Use semantic search** - For finding relevant past experiences
4. **Tag Insights well** - Makes future searches easier
5. **Solidify tasks** - Mark completed work as solidified
6. **Keep CONTEXT fresh** - Update it every session
7. **Run check regularly** - Ensures protocol compliance

## Common Patterns

### Pattern 1: Starting Work on a Feature

```bash
vibecollab onboard                    # Get context
vibecollab insight search "<feature>" # Find relevant Insights
vibecollab task list                  # See active tasks
# ... do work ...
vibecollab task transition TASK-XXX --status DONE
vibecollab check                      # Verify compliance
vibecollab session_save --summary "..."
```

### Pattern 2: Debugging with Insights

```bash
vibecollab insight search "<error>" --semantic  # Search past solutions
# ... debug ...
vibecollab insight add --title "Fixed <issue>" --tags "debug,<component>" --category debug
```

### Pattern 3: Code Review Preparation

```bash
vibecollab check --strict             # Strict compliance check
vibecollab insight suggest            # See if anything worth capturing
vibecollab next                       # Get recommended next steps
```

## Notes

- All vibecollab commands work offline (no LLM API key needed)
- The `check` command includes Insight consistency checks by default
- Use `--no-insights` flag with `check` to skip Insight validation
- Semantic search requires running `vibecollab index` first
