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
    """Task 管理（含 Insight 自动关联）"""
    pass


@task_group.command("create")
@click.option("--id", "task_id", required=True, help="Task ID (TASK-{ROLE}-{SEQ})")
@click.option("--role", required=True, help="角色代码 (DEV/PM/ARCH/...)")
@click.option("--feature", required=True, help="功能描述")
@click.option("--assignee", default=None, help="负责人")
@click.option("--description", default="", help="详细描述")
@click.option("--milestone", default="", help="关联的 ROADMAP 里程碑 (如 v0.9.3)")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def create_task(task_id, role, feature, assignee, description, milestone, config, json_output):
    """创建任务，自动搜索关联 Insight"""
    tm, im = _get_managers(config)

    try:
        task = tm.create_task(
            id=task_id, role=role, feature=feature,
            assignee=assignee, description=description,
            milestone=milestone,
            actor=assignee or "cli",
        )
    except ValueError as e:
        click.echo(f"错误: {e}", err=True)
        raise SystemExit(1)

    related = task.metadata.get("related_insights", [])

    if json_output:
        output = task.to_dict()
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    click.echo(f"已创建: {task.id}  [{task.role}]  {task.feature}")
    if task.assignee:
        click.echo(f"  负责人: {task.assignee}")
    if task.description:
        click.echo(f"  描述: {task.description}")

    if related:
        click.echo(f"\n  关联 Insight ({len(related)} 条):")
        for r in related:
            click.echo(f"    - {r['id']}: {r['title']}  (score: {r['score']})")
    else:
        click.echo("\n  (未找到关联 Insight)")


@task_group.command("list")
@click.option("--status", default=None, help="按状态筛选 (TODO/IN_PROGRESS/REVIEW/DONE)")
@click.option("--assignee", default=None, help="按负责人筛选")
@click.option("--milestone", default=None, help="按里程碑筛选 (如 v0.9.3)")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def list_tasks(status, assignee, milestone, config, json_output):
    """列出任务"""
    tm, _ = _get_managers(config)
    tasks = tm.list_tasks(status=status, assignee=assignee, milestone=milestone)

    if json_output:
        click.echo(json.dumps(
            [t.to_dict() for t in tasks],
            ensure_ascii=False, indent=2,
        ))
        return

    if not tasks:
        click.echo("(无任务)")
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
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def show_task(task_id, config, json_output):
    """查看任务详情"""
    tm, _ = _get_managers(config)
    task = tm.get_task(task_id)

    if task is None:
        click.echo(f"错误: 任务 '{task_id}' 不存在", err=True)
        raise SystemExit(1)

    if json_output:
        click.echo(json.dumps(task.to_dict(), ensure_ascii=False, indent=2))
        return

    click.echo(f"ID:       {task.id}")
    click.echo(f"角色:     {task.role}")
    click.echo(f"功能:     {task.feature}")
    click.echo(f"状态:     {task.status}")
    click.echo(f"负责人:   {task.assignee or '-'}")
    if task.milestone:
        click.echo(f"里程碑:   {task.milestone}")
    if task.description:
        click.echo(f"描述:     {task.description}")
    if task.output:
        click.echo(f"产出:     {task.output}")
    if task.dependencies:
        click.echo(f"依赖:     {', '.join(task.dependencies)}")
    click.echo(f"创建于:   {task.created_at}")
    click.echo(f"更新于:   {task.updated_at}")

    related = task.metadata.get("related_insights", [])
    if related:
        click.echo(f"\n关联 Insight ({len(related)} 条):")
        for r in related:
            click.echo(f"  - {r['id']}: {r['title']}  (score: {r['score']})")


@task_group.command("suggest")
@click.argument("task_id")
@click.option("--limit", "-n", default=5, help="最大推荐数")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def suggest_insights(task_id, limit, config, json_output):
    """为已有任务推荐关联 Insight"""
    tm, _ = _get_managers(config)

    results = tm.suggest_insights(task_id, limit=limit)

    if json_output:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if not results:
        task = tm.get_task(task_id)
        if task is None:
            click.echo(f"错误: 任务 '{task_id}' 不存在", err=True)
            raise SystemExit(1)
        click.echo(f"任务 {task_id} 未找到关联 Insight")
        return

    click.echo(f"任务 {task_id} 的关联 Insight 推荐:")
    for r in results:
        tags_str = ", ".join(r["tags"][:5])
        click.echo(f"  {r['id']}: {r['title']}  (score: {r['score']})")
        click.echo(f"          tags: {tags_str}")


VALID_STATUS_VALUES = ["TODO", "IN_PROGRESS", "REVIEW", "DONE"]


@task_group.command("transition")
@click.argument("task_id")
@click.argument("new_status", type=click.Choice(VALID_STATUS_VALUES, case_sensitive=False))
@click.option("--reason", "-r", default="", help="状态变更原因")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def transition_task(task_id, new_status, reason, config, json_output):
    """推进任务状态

    合法状态转换:
      TODO → IN_PROGRESS
      IN_PROGRESS → REVIEW / TODO
      REVIEW → DONE / IN_PROGRESS

    Examples:

        vibecollab task transition TASK-DEV-001 IN_PROGRESS

        vibecollab task transition TASK-DEV-001 REVIEW -r "代码已完成"
    """
    tm, _ = _get_managers(config)
    target = TaskStatus(new_status.upper())
    result = tm.transition(task_id, target, actor="cli", reason=reason)

    if json_output:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if result.ok:
        task = tm.get_task(task_id)
        click.echo(f"已转换: {task_id} → {new_status.upper()}")
        if task:
            click.echo(f"  功能: {task.feature}")
    else:
        for v in result.violations:
            click.echo(f"错误: {v}", err=True)
        raise SystemExit(1)


@task_group.command("solidify")
@click.argument("task_id")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def solidify_task(task_id, config, json_output):
    """固化任务 — 通过验证门控后标记为 DONE

    要求任务处于 REVIEW 状态。自动执行验证检查:
    - 必填字段完整性
    - 依赖任务是否全部完成
    - 产出描述是否填写

    Examples:

        vibecollab task solidify TASK-DEV-001
    """
    tm, _ = _get_managers(config)
    result = tm.solidify(task_id, actor="cli")

    if json_output:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if result.ok:
        click.echo(f"已固化: {task_id} → DONE")
        if result.warnings:
            for w in result.warnings:
                click.echo(f"  警告: {w}")
    else:
        click.echo(f"固化失败: {task_id}", err=True)
        for v in result.violations:
            click.echo(f"  违规: {v}", err=True)
        raise SystemExit(1)


@task_group.command("rollback")
@click.argument("task_id")
@click.option("--reason", "-r", default="", help="回滚原因")
@click.option("--config", "-c", default="project.yaml", help="配置文件路径")
@click.option("--json-output", "--json", is_flag=True, help="JSON 输出")
def rollback_task(task_id, reason, config, json_output):
    """回滚任务到上一个状态

    回滚规则:
      IN_PROGRESS → TODO
      REVIEW → IN_PROGRESS
      DONE 状态不可回滚

    Examples:

        vibecollab task rollback TASK-DEV-001

        vibecollab task rollback TASK-DEV-001 -r "需要重新设计"
    """
    tm, _ = _get_managers(config)
    result = tm.rollback(task_id, actor="cli", reason=reason)

    if json_output:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if result.ok:
        task = tm.get_task(task_id)
        status = task.status if task else "?"
        click.echo(f"已回滚: {task_id} → {status}")
        if reason:
            click.echo(f"  原因: {reason}")
    else:
        for v in result.violations:
            click.echo(f"错误: {v}", err=True)
        raise SystemExit(1)
