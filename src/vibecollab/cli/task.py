"""
CLI commands for task management with Insight auto-linking.

Commands:
    vibecollab task create     — Create a task (auto-links related Insights)
    vibecollab task list       — List tasks with optional filters
    vibecollab task show       — Show task details including related Insights
    vibecollab task suggest    — Suggest related Insights for an existing task
    vibecollab task transition — Transition task status
    vibecollab task solidify   — Solidify (complete) a task through validation gate
    vibecollab task rollback   — Rollback task to previous status
"""

import json
from pathlib import Path

import click
import yaml

from ..i18n import _
from ..insight.manager import InsightManager
from ..domain.task_manager import TaskManager, TaskStatus


def _load_config(config_path: str) -> dict:
    """Load project config from YAML file."""
    p = Path(config_path)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_managers(config_path: str):
    """Create TaskManager + InsightManager pair."""
    project_root = Path(".")
    try:
        im = InsightManager(project_root=project_root)
    except Exception:
        im = None
    tm = TaskManager(project_root=project_root, insight_manager=im)
    return tm, im


@click.group("task")
def task_group():
    """Task management (with Insight auto-linking)"""
    pass


@task_group.command("create")
@click.option("--id", "task_id", required=True, help="Task ID (TASK-{ROLE}-{SEQ})")
@click.option("--role", required=True, help="Role code (DEV/PM/ARCH/...)")
@click.option("--feature", required=True, help="Feature description")
@click.option("--assignee", default=None, help="Assignee")
@click.option("--description", default="", help="Detailed description")
@click.option("--milestone", default="", help="Associated ROADMAP milestone (e.g. v0.9.3)")
@click.option("--config", "-c", default="project.yaml", help="Config file path")
@click.option("--json-output", "--json", is_flag=True, help="JSON output")
def create_task(task_id, role, feature, assignee, description, milestone, config, json_output):
    """Create a task and auto-search related Insights"""
    tm, im = _get_managers(config)

    try:
        task = tm.create_task(
            id=task_id, role=role, feature=feature,
            assignee=assignee, description=description,
            milestone=milestone,
            actor=assignee or "cli",
        )
    except ValueError as e:
        raise SystemExit(1)

    related = task.metadata.get("related_insights", [])

    if json_output:
        output = task.to_dict()
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    click.echo(f"Created: {task.id}  [{task.role}]  {task.feature}")
    if task.assignee:
        click.echo(f"  Assignee: {task.assignee}")
    if task.description:
        click.echo(f"  Description: {task.description}")

    if related:
        click.echo(f"\n  Related Insights ({len(related)}):")
        for r in related:
            click.echo(f"    - {r['id']}: {r['title']}  (score: {r['score']})")
    else:
        click.echo("\n  (No related Insights found)")


@task_group.command("list")
@click.option("--status", default=None, help=_("Filter by status (TODO/IN_PROGRESS/REVIEW/DONE)"))
@click.option("--assignee", default=None, help=_("Filter by assignee"))
@click.option("--milestone", default=None, help=_("Filter by milestone (e.g. v0.9.3)"))
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def list_tasks(status, assignee, milestone, config, json_output):
    """List tasks"""
    tm, _ = _get_managers(config)
    tasks = tm.list_tasks(status=status, assignee=assignee, milestone=milestone)

    if json_output:
        click.echo(json.dumps(
            [t.to_dict() for t in tasks],
            ensure_ascii=False, indent=2,
        ))
        return

    if not tasks:
        click.echo("(No tasks)")
        return

    for t in tasks:
        related_count = len(t.metadata.get("related_insights", []))
        related_hint = f"  [{related_count} insights]" if related_count else ""
        click.echo(
            f"  {t.id}  [{t.status:12s}]  {t.feature}"
            f"  (@{t.assignee or '-'}){related_hint}"
        )


@task_group.command("show")
@click.argument("task_id")
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def show_task(task_id, config, json_output):
    """View task details"""
    tm, _ = _get_managers(config)
    task = tm.get_task(task_id)

    if task is None:
        click.echo(f"Error: Task '{task_id}' does not exist", err=True)
        raise SystemExit(1)

    if json_output:
        click.echo(json.dumps(task.to_dict(), ensure_ascii=False, indent=2))
        return

    click.echo(f"ID:       {task.id}")
    click.echo(f"Role:       {task.role}")
    click.echo(f"Feature:    {task.feature}")
    click.echo(f"Status:     {task.status}")
    click.echo(f"Assignee:   {task.assignee or '-'}")
    if task.milestone:
        click.echo(f"Milestone:  {task.milestone}")
    if task.description:
        click.echo(f"Desc:       {task.description}")
    if task.output:
        click.echo(f"Output:     {task.output}")
    if task.dependencies:
        click.echo(f"Deps:       {', '.join(task.dependencies)}")
    click.echo(f"Created:    {task.created_at}")
    click.echo(f"Updated:    {task.updated_at}")

    related = task.metadata.get("related_insights", [])
    if related:
        click.echo(f"\nRelated Insights ({len(related)}):")
        for r in related:
            click.echo(f"  - {r['id']}: {r['title']}  (score: {r['score']})")


@task_group.command("suggest")
@click.argument("task_id")
@click.option("--limit", "-n", default=5, help="Max recommendations")
@click.option("--config", "-c", default="project.yaml", help="Config file path")
@click.option("--json-output", "--json", is_flag=True, help="JSON output")
def suggest_insights(task_id, limit, config, json_output):
    """Recommend related Insights for an existing task"""
    tm, _ = _get_managers(config)

    results = tm.suggest_insights(task_id, limit=limit)

    if json_output:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if not results:
        task = tm.get_task(task_id)
        if task is None:
            click.echo(f"Error: Task '{task_id}' does not exist", err=True)
            raise SystemExit(1)
        click.echo(f"No related Insights found for task {task_id}")
        return

    click.echo(f"Related Insight suggestions for task {task_id}:")
    for r in results:
        tags_str = ", ".join(r["tags"][:5])
        click.echo(f"  {r['id']}: {r['title']}  (score: {r['score']})")
        click.echo(f"          tags: {tags_str}")


VALID_STATUS_VALUES = ["TODO", "IN_PROGRESS", "REVIEW", "DONE"]


@task_group.command("transition")
@click.argument("task_id")
@click.argument("new_status", type=click.Choice(VALID_STATUS_VALUES, case_sensitive=False))
@click.option("--reason", "-r", default="", help=_("Reason for status change"))
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def transition_task(task_id, new_status, reason, config, json_output):
    """Transition task status

    Valid status transitions:
      TODO -> IN_PROGRESS
      IN_PROGRESS -> REVIEW / TODO
      REVIEW -> DONE / IN_PROGRESS

    Examples:

        vibecollab task transition TASK-DEV-001 IN_PROGRESS

        vibecollab task transition TASK-DEV-001 REVIEW -r "Code completed"
    """
    tm, _ = _get_managers(config)
    target = TaskStatus(new_status.upper())
    result = tm.transition(task_id, target, actor="cli", reason=reason)

    if json_output:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if result.ok:
        task = tm.get_task(task_id)
        click.echo(f"Transitioned: {task_id} -> {new_status.upper()}")
        if task:
            click.echo(f"  Feature: {task.feature}")
    else:
        for v in result.violations:
            click.echo(f"Error: {v}", err=True)
        raise SystemExit(1)


@task_group.command("solidify")
@click.argument("task_id")
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def solidify_task(task_id, config, json_output):
    """Solidify task -- mark as DONE after passing validation gate

    Requires the task to be in REVIEW status. Auto-runs validation checks:
    - Required field completeness
    - Whether all dependency tasks are completed
    - Whether output description is filled

    Examples:

        vibecollab task solidify TASK-DEV-001
    """
    tm, _ = _get_managers(config)
    result = tm.solidify(task_id, actor="cli")

    if json_output:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if result.ok:
        click.echo(f"Solidified: {task_id} -> DONE")
        if result.warnings:
            for w in result.warnings:
                click.echo(f"  Warning: {w}")
    else:
        click.echo(f"Solidify failed: {task_id}", err=True)
        for v in result.violations:
            click.echo(f"  Violation: {v}", err=True)
        raise SystemExit(1)


@task_group.command("rollback")
@click.argument("task_id")
@click.option("--reason", "-r", default="", help=_("Rollback reason"))
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def rollback_task(task_id, reason, config, json_output):
    """Rollback task to previous status

    Rollback rules:
      IN_PROGRESS -> TODO
      REVIEW -> IN_PROGRESS
      DONE status cannot be rolled back

    Examples:

        vibecollab task rollback TASK-DEV-001

        vibecollab task rollback TASK-DEV-001 -r "Needs redesign"
    """
    tm, _ = _get_managers(config)
    result = tm.rollback(task_id, actor="cli", reason=reason)

    if json_output:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if result.ok:
        task = tm.get_task(task_id)
        status = task.status if task else "?"
        click.echo(f"Rolled back: {task_id} -> {status}")
        if reason:
            click.echo(f"  Reason: {reason}")
    else:
        for v in result.violations:
            click.echo(f"Error: {v}", err=True)
        raise SystemE