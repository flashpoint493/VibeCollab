"""
CLI commands for ROADMAP / Task integration.

Commands:
    vibecollab roadmap status  — Show per-milestone progress
    vibecollab roadmap sync    — Sync ROADMAP / tasks.json
    vibecollab roadmap parse   — Parse and display ROADMAP structure
"""

import json
from pathlib import Path

import click

from .._compat import EMOJI
from ..i18n import _
from ..insight.manager import InsightManager
from ..domain.roadmap_parser import MILESTONE_FORMAT_HINT, RoadmapParser
from ..domain.task_manager import TaskManager


def _get_parser(config: str) -> RoadmapParser:
    """Create RoadmapParser with TaskManager."""
    project_root = Path(".")
    try:
        im = InsightManager(project_root=project_root)
    except Exception:
        im = None
    tm = TaskManager(project_root=project_root, insight_manager=im)
    return RoadmapParser(project_root=project_root, task_manager=tm)


@click.group("roadmap")
def roadmap_group():
    """ROADMAP / Task integration management"""
    pass


@roadmap_group.command("status")
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def roadmap_status(config, json_output):
    """View per-milestone progress overview"""
    parser = _get_parser(config)
    report = parser.status()

    if json_output:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    if not report.milestones:
        click.echo("(No milestones found in ROADMAP.md)")
        click.echo()
        click.echo(MILESTONE_FORMAT_HINT)
        return

    click.echo("ROADMAP Progress Overview")
    click.echo("=" * 60)

    for ms in report.milestones:
        version = ms["version"]
        title = ms.get("title", "")
        total = ms["total_items"]
        done = ms["done_items"]
        pct = ms["progress_pct"]
        linked = ms["linked_tasks"]
        breakdown = ms.get("task_breakdown", {})

        # Progress bar
        bar_len = 20
        filled = int(bar_len * pct / 100) if total > 0 else 0
        bar = EMOJI["bar_fill"] * filled + EMOJI["bar_empty"] * (bar_len - filled)

        header = f"{version}"
        if title:
            header += f" - {title}"
        click.echo(f"\n  {header}")
        click.echo(f"    [{bar}] {pct:.0f}%  ({done}/{total} items)")

        if linked > 0:
            click.echo(f"    Linked Tasks: {linked}", nl=False)
            if breakdown:
                parts = [f"{s}: {c}" for s, c in sorted(breakdown.items())]
                click.echo(f"  ({', '.join(parts)})")
            else:
                click.echo()

    click.echo(f"\n{'=' * 60}")
    click.echo(f"  Total: {report.total_done}/{report.total_items} items completed")
    click.echo(f"  Linked Tasks: {report.total_tasks_linked}")

    if report.unlinked_task_ids:
        click.echo(f"\n  Tasks not linked to milestones ({len(report.unlinked_task_ids)}):")
        for tid in report.unlinked_task_ids:
            click.echo(f"    - {tid}")


@roadmap_group.command("sync")
@click.option("--direction", "-d",
              type=click.Choice(["both", "roadmap_to_tasks", "tasks_to_roadmap"]),
              default="both", help=_("Sync direction"))
@click.option("--dry-run", is_flag=True, help=_("Preview only, no actual changes"))
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def roadmap_sync(direction, dry_run, config, json_output):
    """Sync ROADMAP.md / tasks.json

    ROADMAP.md milestone format:
      ### v0.1.0 - Title description

    Checkbox linked to Task ID:
      - [ ] Feature description (TASK-DEV-001)

    Sync directions:
      both              -- Bidirectional sync (tasks.json takes priority on conflict)
      roadmap_to_tasks  -- ROADMAP [x] -> task DONE
      tasks_to_roadmap  -- task DONE -> ROADMAP [x]

    Examples:

        vibecollab roadmap sync                    # Bidirectional sync

        vibecollab roadmap sync --dry-run          # Preview sync actions

        vibecollab roadmap sync -d tasks_to_roadmap  # Only sync from tasks to ROADMAP
    """
    parser = _get_parser(config)
    milestones = parser.parse()
    if not milestones:
        if json_output:
            click.echo(json.dumps([], ensure_ascii=False))
        else:
            click.echo("(No milestones found in ROADMAP.md, cannot sync)")
            click.echo()
            click.echo(MILESTONE_FORMAT_HINT)
        return
    actions = parser.sync(direction=direction, dry_run=dry_run)

    if json_output:
        output = [
            {"type": a.type, "task_id": a.task_id,
             "milestone": a.milestone, "detail": a.detail}
            for a in actions
        ]
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if not actions:
        click.echo("Already synced, no changes needed.")
        return

    prefix = "[DRY-RUN] " if dry_run else ""
    click.echo(f"{prefix}Sync actions ({len(actions)}):")
    for a in actions:
        icon = {
            "task_to_done": "->",
            "task_from_done": "<-",
            "checkbox_check": "[x]",
            "checkbox_uncheck": "[ ]",
        }.get(a.type, "?")
        click.echo(f"  {icon} {a.detail}")

    if dry_run:
        click.echo(f"\n(Preview mode, no changes applied. Remove --dry-run to execute sync)")


@roadmap_group.command("parse")
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def roadmap_parse(config, json_output):
    """Parse ROADMAP.md structure

    Expected milestone format: ### vX.Y.Z - Title
    """
    parser = _get_parser(config)
    milestones = parser.parse()

    if json_output:
        output = []
        for ms in milestones:
            output.append({
                "version": ms.version,
                "title": ms.title,
                "line_number": ms.line_number,
                "total_items": ms.total,
                "done_items": ms.done,
                "items": [
                    {
                        "line_number": item.line_number,
                        "checked": item.checked,
                        "task_ids": item.task_ids,
                        "text": item.text,
                    }
                    for item in ms.items
                ],
            })
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if not milestones:
        click.echo("(No milestones found in ROADMAP.md)")
        click.echo()
        click.echo(MILESTONE_FORMAT_HINT)
        return

    for ms in milestones:
        header = f"{ms.version}"
        if ms.title:
            header += f" - {ms.title}"
        click.echo(f"\n{header}  ({ms.done}/{ms.total})")

        for item in ms.items:
            check = "x" if item.checked else " "
            task_hint = f"  [{', '.join(item.task_ids)}]" if item.task_ids else ""
            # Trim the original markdown prefix for display
            display_text = item.text
            if display_text.startswith("- ["):
                display_text = display_text[6:]  # Remove "- [x] " or "- [ ] "
            click.echo(f"  [{check}] {display_text}{task_hint}")
