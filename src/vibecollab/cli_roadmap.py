"""
CLI commands for ROADMAP ↔ Task integration.

Commands:
    vibecollab roadmap status  — Show per-milestone progress
    vibecollab roadmap sync    — Sync ROADMAP.md ↔ tasks.json
    vibecollab roadmap parse   — Parse and display ROADMAP structure
"""

import json
from pathlib import Path

import click

from .insight_manager import InsightManager
from .roadmap_parser import MILESTONE_FORMAT_HINT, RoadmapParser
from .task_manager import TaskManager


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
    """ROADMAP ↔ Task 集成管理"""
    pass


@roadmap_group.command("status")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def roadmap_status(config, json_output):
    """查看各里程碑进度概览"""
    parser = _get_parser(config)
    report = parser.status()

    if json_output:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    if not report.milestones:
        click.echo("(未在 ROADMAP.md 中发现里程碑)")
        click.echo()
        click.echo(MILESTONE_FORMAT_HINT)
        return

    click.echo("ROADMAP 进度概览")
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
        bar = "█" * filled + "░" * (bar_len - filled)

        header = f"{version}"
        if title:
            header += f" - {title}"
        click.echo(f"\n  {header}")
        click.echo(f"    [{bar}] {pct:.0f}%  ({done}/{total} items)")

        if linked > 0:
            click.echo(f"    关联 Task: {linked} 个", nl=False)
            if breakdown:
                parts = [f"{s}: {c}" for s, c in sorted(breakdown.items())]
                click.echo(f"  ({', '.join(parts)})")
            else:
                click.echo()

    click.echo(f"\n{'=' * 60}")
    click.echo(f"  总计: {report.total_done}/{report.total_items} items 完成")
    click.echo(f"  关联 Task: {report.total_tasks_linked} 个")

    if report.unlinked_task_ids:
        click.echo(f"\n  未关联里程碑的 Task ({len(report.unlinked_task_ids)}):")
        for tid in report.unlinked_task_ids:
            click.echo(f"    - {tid}")


@roadmap_group.command("sync")
@click.option("--direction", "-d",
              type=click.Choice(["both", "roadmap_to_tasks", "tasks_to_roadmap"]),
              default="both", help="同步方向")
@click.option("--dry-run", is_flag=True, help="仅预览，不实际修改")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def roadmap_sync(direction, dry_run, config, json_output):
    """同步 ROADMAP.md ↔ tasks.json

    ROADMAP.md 里程碑格式:
      ### v0.1.0 - 标题描述

    Checkbox 关联 Task ID:
      - [ ] 功能描述 (TASK-DEV-001)

    同步方向:
      both              — 双向同步 (冲突时 tasks.json 优先)
      roadmap_to_tasks  — ROADMAP [x] → 任务 DONE
      tasks_to_roadmap  — 任务 DONE → ROADMAP [x]

    Examples:

        vibecollab roadmap sync                    # 双向同步

        vibecollab roadmap sync --dry-run          # 预览同步动作

        vibecollab roadmap sync -d tasks_to_roadmap  # 仅从 tasks 同步到 ROADMAP
    """
    parser = _get_parser(config)
    milestones = parser.parse()
    if not milestones:
        if json_output:
            click.echo(json.dumps([], ensure_ascii=False))
        else:
            click.echo("(未在 ROADMAP.md 中发现里程碑，无法同步)")
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
        click.echo("已同步，无需变更。")
        return

    prefix = "[DRY-RUN] " if dry_run else ""
    click.echo(f"{prefix}同步动作 ({len(actions)} 项):")
    for a in actions:
        icon = {
            "task_to_done": "→",
            "task_from_done": "←",
            "checkbox_check": "☑",
            "checkbox_uncheck": "☐",
        }.get(a.type, "?")
        click.echo(f"  {icon} {a.detail}")

    if dry_run:
        click.echo("\n(预览模式，未实际修改。移除 --dry-run 执行同步)")


@roadmap_group.command("parse")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def roadmap_parse(config, json_output):
    """解析 ROADMAP.md 结构

    期望的里程碑格式: ### vX.Y.Z - 标题
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
        click.echo("(未在 ROADMAP.md 中发现里程碑)")
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
