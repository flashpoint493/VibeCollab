---
name: VibeCollab
description: VibeCollab AI collaboration protocol support for OpenClaw
author: flashpoint493
version: 0.10.0
tags:
  - protocol
  - collaboration
  - development
tools:
  - onboard
  - check
  - next_step
  - roadmap_status
  - roadmap_sync
  - insight_search
  - insight_add
  - task_list
  - task_create
  - task_transition
  - session_save
---

# VibeCollab protocol (OpenClaw edition)

This project uses **VibeCollab** AI collaboration protocol. Full rules: `CONTRIBUTING_AI.md`.

## Context recovery (start of conversation)

1. Read `CONTRIBUTING_AI.md` for collaboration rules.
2. Read `docs/CONTEXT.md` to restore current state.
3. Read `docs/DECISIONS.md` for confirmed and pending decisions.
4. Run `git log --oneline -10` to see recent progress.
5. Ask the user for this conversation's goal.

## Key files

| File | Purpose |
|------|--------|
| `CONTRIBUTING_AI.md` | AI collaboration rules (authoritative) |
| `llms.txt` | Project context summary (llmstxt.org standard) |
| `docs/CONTEXT.md` | Current development context |
| `docs/DECISIONS.md` | Important decision records |
| `docs/CHANGELOG.md` | Version changelog |
| `docs/QA_TEST_CASES.md` | Product QA test cases |
| `docs/PRD.md` | Product requirements document |
| `docs/ROADMAP.md` | Roadmap + iteration suggestions |

## OpenClaw-specific notes

### Tool availability
OpenClaw provides the following relevant tools (when configured):
- `read` - Read file contents
- `write` - Create/overwrite files
- `edit` - Make precise file edits
- `exec` - Run shell commands
- `web_search` - Search the web (if Brave API configured)
- `web_fetch` - Fetch and extract content from URLs

### Workspace
Your working directory is the repository root. Treat it as your workspace.

### Memory system
- Use `memory_search` for semantic search of MEMORY.md and memory/*.md
- Use `memory_get` to pull specific snippets after searching
- Record important decisions, context, and learnings in `docs/DECISIONS.md`

### Messaging
- Use `message` for proactive sends + channel actions
- For `action=send`, include `to` and `message`
- If multiple channels are configured, pass `channel` parameter

## MCP tools (when available)

| Tool | When to use |
|------|-------------|
| `onboard` | **Start of every conversation** — get project context |
| `check` | **End of every conversation** — verify protocol compliance |
| `next_step` | When unsure what to do next |
| `roadmap_status` | View milestone progress |
| `roadmap_sync` | Sync ROADMAP.md ↔ tasks.json |
| `insight_search` | Search past development experience |
| `insight_add` | Save a reusable insight |
| `task_list` / `task_create` / `task_transition` | Task management |
| `session_save` | **End of conversation** — save session summary |

## ROADMAP format

If the project has `docs/ROADMAP.md`, use this format so `roadmap_status` / `roadmap_sync` work:

- Milestones: `### vX.Y.Z - Title` (only H3; `####` or `##` are not parsed).
- Version must start with `v` (semantic versioning).
- Task IDs: `TASK-{ROLE}-{SEQ}` (e.g. `TASK-DEV-001`) in checklist lines.

## Daily workflow

Conversation start → call `onboard` (or read CONTEXT.md + DECISIONS.md + git log)
→ work on tasks
→ important decisions → record in `docs/DECISIONS.md`
→ conversation end → update `docs/CONTEXT.md` and `docs/CHANGELOG.md` → call `check` and `session_save` → suggest git commit.

## OpenClaw agent registration

Developers using OpenClaw should register their agent IDs to participate in the VibeCollab protocol:

1. Ensure your OpenClaw agent is properly configured
2. Your agent ID will be automatically detected from your session
3. Important: Update the project's developer registry when you first contribute

See `docs/DEVELOPERS.md` for more information about the developer registry.

## Using vibecollab CLI (OpenClaw)

The VibeCollab CLI provides automated context management. Run:

```bash
vibecollab onboard
```

This will display a Rich panel with:
- Project context
- Recent commits
- Pending roadmap items
- Uncommitted changes
- Related insights
- Suggested next steps

OpenClaw agents can use this command at the start of each conversation to quickly understand the project state.

## Automatic commit after onboard

After running `vibecollab onboard`, you should commit all uncommitted changes:

```bash
git add .
git commit -m "Update project context and insights"
```

This ensures that the project state is synchronized with the VibeCollab protocol.

## One-time setup with vibecollab

To initialize OpenClaw support for this project:

```bash
vibecollab setup --ide openclaw
```

This command automatically generates all necessary OpenClaw configuration files, including:
- SKILL.md with proper YAML frontmatter
- OpenClaw-specific configuration
- Protocol rules and skills
- MCP tools configuration (if available)
