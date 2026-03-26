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
@click.argument("ide", type=click.Choice(["opencode", "cursor", "cline"]))
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
    import json as json_mod
    import shutil

    root = project_root or Path.cwd()

    if ide == "opencode":
        _inject_opencode_skill(root, force)
    elif ide == "cursor":
        click.echo(_("Cursor skill injection not yet implemented"))
    elif ide == "cline":
        click.echo(_("Cline skill injection not yet implemented"))


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
vibecollab session_save --summary "What was accomplished" --developer <role>
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

## Multi-Developer Mode

If the project has `multi_developer.enabled: true`:

- Each developer has their own context in `docs/developers/{id}/`
- Check current identity with `vibecollab dev whoami`
- Collaboration tracked in `docs/developers/COLLABORATION.md`

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


@skill_group.command("list")
def list_skills():
    """List available skills and their status"""
    click.echo(_("Available Skills:"))
    click.echo("  - opencode: VibeCollab protocol for OpenCode IDE")
    click.echo("  - cursor: VibeCollab protocol for Cursor IDE (coming soon)")
    click.echo("  - cline: VibeCollab protocol for Cline IDE (coming soon)")
