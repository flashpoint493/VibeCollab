# VibeCollab — Setup Instructions for AI Assistants

You are helping a user set up VibeCollab in their project.
Execute the following steps in order. Stop and report if any step fails.

## Step 1: Install

```bash
pip install vibe-collab[mcp]
```

## Step 2: Initialize

Run in the user's project root directory:

```bash
vibecollab init -n "<PROJECT_NAME>" -d <DOMAIN>
```

- `<PROJECT_NAME>`: Ask the user for their project name
- `<DOMAIN>`: Ask the user to choose: `web` / `mobile` / `game` / `data` / `general`

This creates `project.yaml`, `CONTRIBUTING_AI.md`, and `docs/` directory with protocol documents.

## Step 3: One-shot IDE setup (MCP + rules)

Ask the user which IDE they use (Cursor / Cline / CodeBuddy), then run:

```bash
vibecollab setup --ide cursor   # or: cline / codebuddy / all
```

This injects **MCP config** and **protocol rules** in one command (no external deps):

| IDE       | MCP config                    | Rules |
|----------|-------------------------------|-------|
| Cursor   | `.cursor/mcp.json`            | `.cursor/rules/vibecollab.mdc` |
| Cline    | `.cline/mcp_settings.json`   | `.clinerules/vibecollab.md` |
| CodeBuddy| `.codebuddy/mcp.json`         | `.codebuddy/rules/vibecollab-protocol.mdc` |

Use `vibecollab setup --ide all` to target all supported editors. Restart or reload the IDE afterward.

This repo is self-bootstrapped: run `vibecollab setup --ide all` in the project root to inject MCP + rules for Cursor, Cline, and CodeBuddy (write once, native format per platform).

## Step 4: Verify

```bash
vibecollab check
```

Should return zero errors. Warnings about document staleness are normal for new projects.

## Setup Complete

VibeCollab is ready. You now have MCP tools available in your IDE:

| Tool | When to use |
|------|-------------|
| `onboard` | **Start of every conversation** — get project context |
| `check` | **End of every conversation** — verify protocol compliance |
| `next_step` | When unsure what to do next |
| `roadmap_status` | View milestone progress |
| `roadmap_sync` | Sync ROADMAP.md ↔ tasks.json |
| `insight_search` | Search past development experience |
| `insight_add` | Save a reusable insight |
| `task_list` | List current tasks |
| `task_create` | Create a new task |
| `task_transition` | Move task status (TODO → IN_PROGRESS → REVIEW → DONE) |
| `session_save` | **End of conversation** — save session summary |

## ROADMAP Format

If the project has a `docs/ROADMAP.md`, milestones must use this format for `roadmap_status` / `roadmap_sync` to work:

```markdown
### v0.1.0 - Milestone title

- [ ] Feature description (TASK-DEV-001)
- [x] Completed feature TASK-DEV-002
```

- Only `###` (H3) headers are recognized — `####` or `##` will not be parsed
- Version must start with `v` (semantic versioning)
- Task IDs follow `TASK-{ROLE}-{SEQ}` format (e.g., `TASK-DEV-001`)

## Daily Workflow

```
Conversation start → call onboard
                      ↓
                 Work on tasks
                      ↓
    Important decisions → record in docs/DECISIONS.md
                      ↓
    Conversation end → update docs/CONTEXT.md
                     → update docs/CHANGELOG.md
                     → call check
                     → call session_save
                     → git commit
```
