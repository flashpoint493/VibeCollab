"""
Rules inject CLI — vibecollab rules inject

Inject VibeCollab protocol summary into IDE rule/skill files so the protocol
is applied automatically without relying only on MCP tools or manual reads
of CONTRIBUTING_AI.md. No external dependencies.

Design: write once, adapt format per platform (ide_platforms). Single source
body (schema-driven or RULES_BODY); each IDE gets native format (cursor_mdc
vs plain_md) and optional skills_path (SKILL.md).
"""

from pathlib import Path

import click

from .ide_platforms import get_platform, list_platforms, rules_path_for, skills_path_for


# Rule content aligned with skill.md: context recovery, key files, Daily Workflow,
# MCP tools table, ROADMAP format. Full protocol remains in CONTRIBUTING_AI.md.
RULES_BODY = """# VibeCollab protocol (summary)

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
| `docs/CONTEXT.md` | Current dev context — update at conversation end |
| `docs/DECISIONS.md` | S/A-level decisions — update after decisions |
| `docs/CHANGELOG.md` | Change log — update after each effective conversation |

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
"""


def get_rules_body(root: Path) -> str:
    """Schema-driven body when project.yaml exists; else fallback to RULES_BODY."""
    project_yaml = root / "project.yaml"
    if not project_yaml.is_file():
        return RULES_BODY
    try:
        from .generator import LLMContextGenerator
        gen = LLMContextGenerator.from_file(project_yaml, root)
        return gen.generate_ide_rules_summary()
    except Exception:
        return RULES_BODY


def _rules_content_for_format(body: str, rules_format: str) -> str:
    """Build rule file content by platform format (cursor_mdc vs plain_md)."""
    if rules_format == "cursor_mdc":
        return f"""---
description: VibeCollab AI collaboration protocol summary; full protocol in CONTRIBUTING_AI.md
globs: "**"
alwaysApply: true
---

{body}
"""
    return body.strip()


def get_skills_body(root: Path) -> str:
    """Skills body: same as rules (single source)."""
    return get_rules_body(root)


@click.group("rules")
def rules_group():
    """Inject VibeCollab protocol into IDE rules and skills.

    Writes a short protocol summary so the AI follows context recovery and
    key file conventions. Platforms (vx-aligned): cursor, cline, codebuddy,
    windsurf, claude, opencode, roo, agents, kiro, trae.
    """
    pass


def _inject_to_ide(root: Path, platform_id: str, dry_run: bool) -> None:
    """Write rule file (and optional skill file) for one platform."""
    p = get_platform(platform_id)
    if not p or not p.get("rules_path"):
        return
    body = get_rules_body(root)
    rules_path = rules_path_for(root, platform_id)
    rules_fmt = p.get("rules_format", "plain_md")
    content = _rules_content_for_format(body, rules_fmt)

    if dry_run:
        click.echo(f"[dry-run] Would write: {rules_path}")
        click.echo("--- content preview (first 400 chars) ---")
        click.echo(content[:400] + ("..." if len(content) > 400 else ""))
        click.echo("---")
    else:
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        rules_path.write_text(content, encoding="utf-8")
        click.echo(f"Injected: {rules_path}")

    skills_path = skills_path_for(root, platform_id)
    if skills_path and not dry_run:
        skills_body = get_skills_body(root)
        skills_path.parent.mkdir(parents=True, exist_ok=True)
        skills_path.write_text(skills_body.strip(), encoding="utf-8")
        click.echo(f"Injected: {skills_path}")


def _rules_platform_choices():
    return list_platforms(with_rules=True) + ["all"]


@rules_group.command("inject")
@click.option(
    "--ide",
    type=click.Choice(_rules_platform_choices()),
    default="all",
    help="Target platform (default: all with rules)",
)
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Project root directory",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Only print paths and content preview, do not write files",
)
def inject(ide: str, project_root: Path, dry_run: bool):
    """Inject VibeCollab protocol into IDE rules (and skills when supported).

    Platforms (vx-aligned): cursor, cline, codebuddy, windsurf, claude, opencode,
    roo, agents, kiro, trae.
    """
    root = project_root or Path.cwd()
    supported = list_platforms(with_rules=True)
    ides = [ide] if ide != "all" else supported

    for target_ide in ides:
        _inject_to_ide(root, target_ide, dry_run)

    if not dry_run:
        click.echo("\nDone. Reload IDE rules (or restart IDE) for rules to take effect.")
    else:
        click.echo("\n[dry-run] No files written.")


def do_rules_inject(root: Path, ides: list, dry_run: bool = False) -> None:
    """Inject rule (and skill) files for given platforms. Used by rules inject and setup."""
    for target_ide in ides:
        if get_platform(target_ide) and rules_path_for(root, target_ide):
            _inject_to_ide(root, target_ide, dry_run)