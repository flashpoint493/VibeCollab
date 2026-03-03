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
- `<DOMAIN>`: Ask the user to choose: `web` / `mobile` / `game` / `data` / `generic`

This creates `project.yaml`, `CONTRIBUTING_AI.md`, and `docs/` directory with protocol documents.

## Step 3: Connect MCP to IDE

```bash
vibecollab mcp inject --ide auto
```

This auto-detects the user's IDE (Cursor / Cline / CodeBuddy) and injects MCP Server config.

If auto-detection fails, ask the user which IDE they use and run:

```bash
vibecollab mcp inject --ide cursor   # or: cline / codebuddy
```

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
| `insight_search` | Search past development experience |
| `insight_add` | Save a reusable insight |
| `insight_suggest` | Get signal-driven insight recommendations |
| `insight_graph` | View insight relationship graph |
| `insight_export` | Export insights in YAML format |
| `search_docs` | Semantic search across project documents |
| `task_list` | List current tasks |
| `task_create` | Create a new task (auto-links insights) |
| `task_transition` | Move task status (TODO → IN_PROGRESS → REVIEW → DONE) |
| `developer_context` | Get a specific developer's context |
| `project_prompt` | Generate full context prompt |
| `roadmap_status` | View milestone progress |
| `roadmap_sync` | Sync ROADMAP.md ↔ tasks.json |
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
