"""
Skill management CLI Commands -- vibecollab skill

Manage AI assistant skill files for various IDEs (OpenCode, etc.)
to provide project-specific guidance and protocols.

Usage:
    vibecollab skill inject opencode        # Inject VibeCollab skill into OpenCode
    vibecollab skill list                   # List available skills
"""

from pathlib import Path

import click

from ..i18n import _


@click.group("skill")
def skill_group():
    """Skill management for AI assistants (v0.10.11+)

    Inject project-specific skills into AI IDEs to provide
    contextual guidance and protocol enforcement.
    """
    pass


@skill_group.command("inject")
@click.argument("ide", type=click.Choice(["opencode", "cursor", "cline", "codebuddy", "all"]))
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help=_("Project root directory (default: current directory)"),
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help=_("Force overwrite existing skill files"),
)
def inject(ide: str, project_root: Path, force: bool):
    """Inject VibeCollab skill into target IDE

    Automatically creates/upgrades IDE-specific skill configuration
    to enable VibeCollab protocol support.

    Examples:

        vibecollab skill inject opencode

        vibecollab skill inject opencode -p ./my-project

        vibecollab skill inject opencode --force
    """
    root = project_root or Path.cwd()

    if ide == "all":
        ides = ["opencode", "cursor", "cline", "codebuddy"]
    else:
        ides = [ide]

    for target_ide in ides:
        if target_ide == "opencode":
            _inject_opencode_skill(root, force)
        elif target_ide == "cursor":
            _inject_cursor_skill(root, force)
        elif target_ide == "cline":
            _inject_cline_skill(root, force)
        elif target_ide == "codebuddy":
            _inject_codebuddy_skill(root, force)


def _inject_opencode_skill(project_root: Path, force: bool = False):
    """Inject VibeCollab skill into OpenCode configuration.

    Creates:
    - .opencode/package.json - Plugin dependencies
    - .opencode/skills/vibecollab.md - Skill definition
    """
    import json as json_mod

    opencode_dir = project_root / ".opencode"
    skills_dir = opencode_dir / "skills"
    package_file = opencode_dir / "package.json"
    skill_file = skills_dir / "vibecollab.md"

    # Create directories
    opencode_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Package.json content
    package_content = {"dependencies": {"@opencode-ai/plugin": "1.3.2"}}

    # Check if package.json exists
    if package_file.exists() and not force:
        try:
            existing = json_mod.loads(package_file.read_text(encoding="utf-8"))
            if existing.get("dependencies", {}).get("@opencode-ai/plugin"):
                click.echo(f"[dim]OpenCode already configured: {package_file}[/dim]")
            else:
                # Merge with existing
                existing["dependencies"] = existing.get("dependencies", {})
                existing["dependencies"]["@opencode-ai/plugin"] = "1.3.2"
                package_file.write_text(
                    json_mod.dumps(existing, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                click.echo(f"Updated: {package_file}")
        except (json_mod.JSONDecodeError, OSError):
            # Write new file if corrupt
            package_file.write_text(
                json_mod.dumps(package_content, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            click.echo(f"Created: {package_file}")
    else:
        package_file.write_text(
            json_mod.dumps(package_content, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        click.echo(f"Created: {package_file}")

    # Skill file content
    skill_content = """# VibeCollab Skill for OpenCode

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
vibecollab session_save --summary "What was accomplished" --role <role>
```

### Task Management Commands

```bash
# Create a new task
vibecollab task create --role DEV --feature "Implement login" --output "auth.py"

# List current tasks
vibecollab task list

# Mark task as started
vibecollab task start <task_id>

# Complete a task (auto-updates context)
vibecollab task done <task_id>
```

### Insight System Commands

```bash
# Record a new insight
vibecollab insight add --category pattern --content "Found that using X approach reduces Y by 50%"

# Search insights by tag
vibecollab insight search --tag performance

# Semantic search across insights
vibecollab insight semantic "how to handle errors"

# List recent insights
vibecollab insight list --limit 10
```

### Roadmap Commands

```bash
# View current milestone status
vibecollab roadmap status

# List all milestones
vibecollab roadmap list

# Create task from ROADMAP
vibecollab roadmap task <milestone_id>
```

## Protocol Guidelines

### At Start of Conversation

1. Run `vibecollab onboard` to get full project context
2. Check `docs/CONTEXT.md` for current state
3. Review any assigned tasks from previous sessions

### During Development

1. Create task before implementing: `vibecollab task create`
2. Run `vibecollab check` periodically to verify compliance
3. Record insights when discovering useful patterns: `vibecollab insight add`
4. Update task status as you progress

### At End of Conversation

1. Save session summary: `vibecollab session_save`
2. Mark completed tasks: `vibecollab task done`
3. Update CHANGELOG.md with what was accomplished
4. Ensure all decisions are recorded in docs/DECISIONS.md

## Key Files

- `project.yaml` - Project configuration and protocol settings
- `CONTRIBUTING_AI.md` - Full AI collaboration rules
- `docs/CONTEXT.md` - Current development context
- `docs/ROADMAP.md` - Project roadmap and milestones
- `docs/DECISIONS.md` - Important decision records
- `docs/CHANGELOG.md` - Development changelog
- `.vibecollab/events.jsonl` - Event log for Insight generation

## Multi-Role Mode

If the project has `role_context.enabled: true`:

- Each role has their own context in `docs/roles/{id}/`
- Check current identity with `vibecollab dev whoami`
- Collaboration tracked in `docs/roles/COLLABORATION.md`

## Best Practices

1. **Always onboard first** - Get context before starting work
2. **One task at a time** - Focus on single task completion
3. **Record insights immediately** - Don't wait, capture knowledge while fresh
4. **Update context continuously** - Keep docs/CONTEXT.md current
5. **Follow decision levels** - S/A decisions need confirmation, B/C can proceed
6. **Git commit regularly** - Each task completion should have a commit
"""

    # Check if skill file exists
    if skill_file.exists() and not force:
        click.echo(f"[dim]Skill file already exists: {skill_file} (use --force to overwrite)[/dim]")
    else:
        skill_file.write_text(skill_content, encoding="utf-8")
        action = "Updated" if skill_file.exists() else "Created"
        click.echo(f"{action}: {skill_file}")

    click.echo(f"\n{_('OpenCode skill injection complete!')}")
    click.echo(_('Restart OpenCode or run "opencode" to activate the skill.'))


def _inject_cursor_skill(project_root: Path, force: bool = False):
    """Inject VibeCollab skill into Cursor configuration.

    Creates:
    - .cursor/rules/vibecollab.mdc - Cursor Rules file
    """
    cursor_dir = project_root / ".cursor"
    rules_dir = cursor_dir / "rules"
    skill_file = rules_dir / "vibecollab.mdc"

    # Create directories
    cursor_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)

    skill_content = """---
description: VibeCollab Protocol Rules
globs: "**/*"
alwaysApply: true
---

# VibeCollab AI Collaboration Protocol

You are assisting with a VibeCollab-managed project. Follow these guidelines:

## At Start of Conversation

1. Run `vibecollab onboard` to get full project context
2. Read `docs/CONTEXT.md` for current development state
3. Check `docs/ROADMAP.md` for current milestone
4. Review assigned tasks from previous sessions

## During Development

1. **Create task before implementing**: `vibecollab task create --role DEV --feature "X"`
2. **Check protocol compliance**: `vibecollab check`
3. **Record insights**: `vibecollab insight add --category pattern --content "..."`
4. **Update task status**: `vibecollab task transition <id> <status>`

## At End of Conversation

1. **Save session**: `vibecollab session_save --summary "..." --role <role>`
2. **Complete tasks**: `vibecollab task solidify <id>`
3. **Update CHANGELOG.md**
4. **Record decisions** in `docs/DECISIONS.md`
5. **Git commit** all changes

## Key Files

- `project.yaml` - Project configuration
- `CONTRIBUTING_AI.md` - Full collaboration rules
- `docs/CONTEXT.md` - Current context
- `docs/DECISIONS.md` - Decision records
- `docs/ROADMAP.md` - Milestones and tasks
- `docs/CHANGELOG.md` - Change history

## Decision Levels

- **S (Strategic)**: Overall direction - requires human approval
- **A (Architecture)**: System design - human review required
- **B (Implementation)**: Specific approach - quick confirm
- **C (Detail)**: Naming, params - AI decides autonomously
"""

    _write_skill_file(skill_file, skill_content, force, "Cursor")


def _inject_cline_skill(project_root: Path, force: bool = False):
    """Inject VibeCollab skill into Cline configuration.

    Creates:
    - .cline/skills/vibecollab.md - Cline Skill file
    """
    cline_dir = project_root / ".cline"
    skills_dir = cline_dir / "skills"
    skill_file = skills_dir / "vibecollab.md"

    # Create directories
    cline_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    skill_content = """# VibeCollab Skill for Cline

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
vibecollab session_save --summary "What was accomplished" --role <role>
```

### Task Management Commands

```bash
# Create a new task
vibecollab task create --role DEV --feature "Implement login" --output "auth.py"

# List current tasks
vibecollab task list

# Mark task as started
vibecollab task start <task_id>

# Complete a task (auto-updates context)
vibecollab task done <task_id>
```

### Insight System Commands

```bash
# Record a new insight
vibecollab insight add --category pattern --content "Found that using X approach reduces Y by 50%"

# Search insights by tag
vibecollab insight search --tag performance

# Semantic search across insights
vibecollab insight semantic "how to handle errors"

# List recent insights
vibecollab insight list --limit 10
```

### Roadmap Commands

```bash
# View current milestone status
vibecollab roadmap status

# List all milestones
vibecollab roadmap list

# Create task from ROADMAP
vibecollab roadmap task <milestone_id>
```

## Protocol Guidelines

### At Start of Conversation

1. Run `vibecollab onboard` to get full project context
2. Check `docs/CONTEXT.md` for current state
3. Review any assigned tasks from previous sessions

### During Development

1. Create task before implementing: `vibecollab task create`
2. Run `vibecollab check` periodically to verify compliance
3. Record insights when discovering useful patterns: `vibecollab insight add`
4. Update task status as you progress

### At End of Conversation

1. Save session summary: `vibecollab session_save`
2. Mark completed tasks: `vibecollab task done`
3. Update CHANGELOG.md with what was accomplished
4. Ensure all decisions are recorded in docs/DECISIONS.md

## Key Files

- `project.yaml` - Project configuration and protocol settings
- `CONTRIBUTING_AI.md` - Full AI collaboration rules
- `docs/CONTEXT.md` - Current development context
- `docs/ROADMAP.md` - Project roadmap and milestones
- `docs/DECISIONS.md` - Important decision records
- `docs/CHANGELOG.md` - Development changelog
- `.vibecollab/events.jsonl` - Event log for Insight generation

## Multi-Role Mode

If the project has `role_context.enabled: true`:

- Each role has their own context in `docs/roles/{id}/`
- Check current identity with `vibecollab dev whoami`
- Collaboration tracked in `docs/roles/COLLABORATION.md`

## Best Practices

1. **Always onboard first** - Get context before starting work
2. **One task at a time** - Focus on single task completion
3. **Record insights immediately** - Don't wait, capture knowledge while fresh
4. **Update context continuously** - Keep docs/CONTEXT.md current
5. **Follow decision levels** - S/A decisions need confirmation, B/C can proceed
6. **Git commit regularly** - Each task completion should have a commit
"""

    _write_skill_file(skill_file, skill_content, force, "Cline")


def _inject_codebuddy_skill(project_root: Path, force: bool = False):
    """Inject VibeCollab skill into CodeBuddy configuration.

    Creates:
    - .codebuddy/skills/vibecollab.md - CodeBuddy Skill file
    """
    codebuddy_dir = project_root / ".codebuddy"
    skills_dir = codebuddy_dir / "skills"
    skill_file = skills_dir / "vibecollab.md"

    # Create directories
    codebuddy_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    skill_content = """# VibeCollab Skill for CodeBuddy

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
vibecollab session_save --summary "What was accomplished" --role <role>
```

### Task Management Commands

```bash
# Create a new task
vibecollab task create --role DEV --feature "Implement login" --output "auth.py"

# List current tasks
vibecollab task list

# Mark task as started
vibecollab task start <task_id>

# Complete a task (auto-updates context)
vibecollab task done <task_id>
```

### Insight System Commands

```bash
# Record a new insight
vibecollab insight add --category pattern --content "Found that using X approach reduces Y by 50%"

# Search insights by tag
vibecollab insight search --tag performance

# Semantic search across insights
vibecollab insight semantic "how to handle errors"

# List recent insights
vibecollab insight list --limit 10
```

### Roadmap Commands

```bash
# View current milestone status
vibecollab roadmap status

# List all milestones
vibecollab roadmap list

# Create task from ROADMAP
vibecollab roadmap task <milestone_id>
```

## Protocol Guidelines

### At Start of Conversation

1. Run `vibecollab onboard` to get full project context
2. Check `docs/CONTEXT.md` for current state
3. Review any assigned tasks from previous sessions

### During Development

1. Create task before implementing: `vibecollab task create`
2. Run `vibecollab check` periodically to verify compliance
3. Record insights when discovering useful patterns: `vibecollab insight add`
4. Update task status as you progress

### At End of Conversation

1. Save session summary: `vibecollab session_save`
2. Mark completed tasks: `vibecollab task done`
3. Update CHANGELOG.md with what was accomplished
4. Ensure all decisions are recorded in docs/DECISIONS.md

## Key Files

- `project.yaml` - Project configuration and protocol settings
- `CONTRIBUTING_AI.md` - Full AI collaboration rules
- `docs/CONTEXT.md` - Current development context
- `docs/ROADMAP.md` - Project roadmap and milestones
- `docs/DECISIONS.md` - Important decision records
- `docs/CHANGELOG.md` - Development changelog
- `.vibecollab/events.jsonl` - Event log for Insight generation

## Multi-Role Mode

If the project has `role_context.enabled: true`:

- Each role has their own context in `docs/roles/{id}/`
- Check current identity with `vibecollab dev whoami`
- Collaboration tracked in `docs/roles/COLLABORATION.md`

## Best Practices

1. **Always onboard first** - Get context before starting work
2. **One task at a time** - Focus on single task completion
3. **Record insights immediately** - Don't wait, capture knowledge while fresh
4. **Update context continuously** - Keep docs/CONTEXT.md current
5. **Follow decision levels** - S/A decisions need confirmation, B/C can proceed
6. **Git commit regularly** - Each task completion should have a commit
"""

    _write_skill_file(skill_file, skill_content, force, "CodeBuddy")


def _write_skill_file(skill_file: Path, content: str, force: bool, ide_name: str):
    """Helper to write skill file with proper messaging."""
    if skill_file.exists() and not force:
        click.echo(
            f"  [dim]{ide_name} skill already exists: {skill_file} (use --force to overwrite)[/dim]"
        )
    else:
        skill_file.write_text(content, encoding="utf-8")
        action = "Updated" if skill_file.exists() else "Created"
        click.echo(f"  {action}: {skill_file}")


@skill_group.command("list")
def list_skills():
    """List available skills and their status"""
    click.echo(_("Available Skills:"))
    click.echo("  - opencode: VibeCollab protocol for OpenCode IDE")
    click.echo("  - cursor: VibeCollab protocol for Cursor IDE (.cursor/rules/)")
    click.echo("  - cline: VibeCollab protocol for Cline IDE (.cline/skills/)")
    click.echo("  - codebuddy: VibeCollab protocol for CodeBuddy IDE (.codebuddy/skills/)")
