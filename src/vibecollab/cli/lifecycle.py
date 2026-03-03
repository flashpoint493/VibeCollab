"""
Project lifecycle management CLI commands
"""

from pathlib import Path
from typing import Optional

import click
import yaml
from rich.panel import Panel

from .._compat import BULLET, EMOJI, safe_console
from ..domain.lifecycle import STAGE_ORDER, LifecycleManager

console = safe_console()


@click.group()
def lifecycle():
    """Project lifecycle management command group"""
    pass


@lifecycle.command()
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
def check(config: str):
    """Check current project lifecycle status

    Examples:

        vibecollab lifecycle check
        vibecollab lifecycle check -c my-project.yaml
    """
    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file does not exist: {config}")
        raise SystemExit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    manager = LifecycleManager(project_config)
    current_stage = manager.get_current_stage()
    stage_info = manager.get_stage_info()
    stage_history = manager.get_stage_history()
    milestone_status = manager.check_milestone_completion()

    # Display current stage info
    console.print()
    console.print(Panel.fit(
        f"[bold]{stage_info.get('name', 'Unknown')}[/bold] ({current_stage})\n\n"
        f"{stage_info.get('description', '')}",
        title="Current Project Lifecycle Stage"
    ))

    # Display stage focus and principles
    console.print()
    console.print("[bold]Stage Focus:[/bold]")
    for focus in stage_info.get('focus', []):
        console.print(f"  {BULLET} {focus}")

    console.print()
    console.print("[bold]Stage Principles:[/bold]")
    for principle in stage_info.get('principles', []):
        console.print(f"  {BULLET} {principle}")

    # Display milestone status
    if milestone_status['total'] > 0:
        console.print()
        console.print(f"[bold]Milestone Progress:[/bold] {milestone_status['completed']}/{milestone_status['total']} completed")
        console.print(f"[dim]Completion rate:[/dim] {milestone_status['completion_rate']:.0%}")

        if milestone_status['pending'] > 0:
            console.print()
            console.print("[yellow]Pending milestones:[/yellow]")
            for milestone in milestone_status['milestones']:
                if not milestone.get('completed', False):
                    console.print(f"  {EMOJI['hourglass']} {milestone.get('name', 'Unnamed milestone')}")

    # Check if upgrade is possible
    can_upgrade, next_stage, reason = manager.can_upgrade()
    if can_upgrade:
        console.print()
        console.print(f"[green]{EMOJI['success']} Ready to upgrade to next stage![/green]")
        console.print(f"[dim]Next stage:[/dim] {next_stage}")
        console.print()
        console.print("[bold]Upgrade suggestions:[/bold]")
        suggestions = manager.get_upgrade_suggestions(next_stage)
        for suggestion in suggestions:
            console.print(f"  {BULLET} {suggestion}")
        console.print()
        console.print("[dim]Run 'vibecollab lifecycle upgrade' to proceed[/dim]")
    elif reason:
        console.print()
        console.print(f"[yellow]{EMOJI['warning']} Cannot upgrade yet:[/yellow] {reason}")

    # Display stage history
    if stage_history:
        console.print()
        console.print("[bold]Stage History:[/bold]")
        for entry in stage_history:
            stage = entry.get("stage", "unknown")
            started = entry.get("started_at", "Unknown")
            ended = entry.get("ended_at")

            if ended:
                console.print(f"  {BULLET} {stage}: {started} -> {ended}")
            else:
                console.print(f"  {BULLET} {stage}: {started} [bold green](in progress)[/bold green]")


@lifecycle.command()
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
@click.option("--stage", "-s", type=click.Choice(STAGE_ORDER), help="Target stage (default: upgrade to next stage)")
@click.option("--force", "-f", is_flag=True, help="Force upgrade (skip checks)")
def upgrade(config: str, stage: Optional[str], force: bool):
    """Upgrade project to next or specified stage

    Examples:

        vibecollab lifecycle upgrade
        vibecollab lifecycle upgrade --stage production
        vibecollab lifecycle upgrade --force
    """
    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file does not exist: {config}")
        raise SystemExit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    manager = LifecycleManager(project_config)
    manager.get_current_stage()

    # Determine target stage
    if stage is None:
        can_upgrade, next_stage, reason = manager.can_upgrade()
        if not can_upgrade and not force:
            console.print(f"[red]Error:[/red] {reason}")
            console.print("[dim]Use --force to force upgrade (not recommended)[/dim]")
            raise SystemExit(1)
        target_stage = next_stage
    else:
        target_stage = stage

    # Execute upgrade
    success, error = manager.upgrade_to_stage(target_stage)
    if not success:
        console.print(f"[red]Error:[/red] {error}")
        raise SystemExit(1)

    # Save config
    project_config.update(manager.to_config_dict())
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            project_config,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False
        )

    # Display upgrade success info
    target_info = manager.get_stage_info(target_stage)
    console.print()
    console.print(Panel.fit(
        f"[bold green]{EMOJI['success']} Project upgraded to {target_info.get('name', target_stage)} stage[/bold green]",
        title="Upgrade Successful"
    ))

    # Display upgrade suggestions
    suggestions = manager.get_upgrade_suggestions(target_stage)
    if suggestions:
        console.print()
        console.print("[bold]Changes to note after upgrade:[/bold]")
        for suggestion in suggestions:
            console.print(f"  {BULLET} {suggestion}")

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Regenerate CONTRIBUTING_AI.md: vibecollab generate -c project.yaml")
    console.print("  2. Update stage info in ROADMAP.md")
    console.print("  3. Adjust development workflow according to new stage principles")


# Export command group
__all__ = ["lifecycle"]
