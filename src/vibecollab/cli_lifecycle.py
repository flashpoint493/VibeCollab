"""
项目生涯管理 CLI 命令
"""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import yaml
import sys
import platform

from .lifecycle import LifecycleManager, STAGE_ORDER

# 检测是否为 Windows 且使用 GBK 编码
def is_windows_gbk():
    """检测是否为 Windows 且使用 GBK 编码"""
    if platform.system() != "Windows":
        return False
    try:
        "✅⚠️❌ℹ️".encode(sys.stdout.encoding or "utf-8")
        return False
    except (UnicodeEncodeError, LookupError):
        return True

USE_EMOJI = not is_windows_gbk()
EMOJI_MAP = {
    "success": "OK" if not USE_EMOJI else "✅",
    "warning": "!" if not USE_EMOJI else "⚠️"
}

# bullet point 替代
BULLET = "-" if is_windows_gbk() else "•"

console = Console()


@click.group()
def lifecycle():
    """项目生涯管理命令组"""
    pass


@lifecycle.command()
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
def check(config: str):
    """检查当前项目生涯状态
    
    Examples:
    
        vibecollab lifecycle check
        vibecollab lifecycle check -c my-project.yaml
    """
    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    manager = LifecycleManager(project_config)
    current_stage = manager.get_current_stage()
    stage_info = manager.get_stage_info()
    stage_history = manager.get_stage_history()
    milestone_status = manager.check_milestone_completion()
    
    # 显示当前阶段信息
    console.print()
    console.print(Panel.fit(
        f"[bold]{stage_info.get('name', '未知')}[/bold] ({current_stage})\n\n"
        f"{stage_info.get('description', '')}",
        title="当前项目生涯阶段"
    ))
    
    # 显示阶段重点和原则
    console.print()
    console.print("[bold]阶段重点:[/bold]")
    for focus in stage_info.get('focus', []):
        console.print(f"  • {focus}")
    
    console.print()
    console.print("[bold]阶段原则:[/bold]")
    for principle in stage_info.get('principles', []):
        console.print(f"  • {principle}")
    
    # 显示里程碑状态
    if milestone_status['total'] > 0:
        console.print()
        console.print(f"[bold]里程碑进度:[/bold] {milestone_status['completed']}/{milestone_status['total']} 已完成")
        console.print(f"[dim]完成率:[/dim] {milestone_status['completion_rate']:.0%}")
        
        if milestone_status['pending'] > 0:
            console.print()
            console.print("[yellow]待完成的里程碑:[/yellow]")
            for milestone in milestone_status['milestones']:
                if not milestone.get('completed', False):
                    console.print(f"  ⏳ {milestone.get('name', '未命名里程碑')}")
    
    # 检查是否可以升级
    can_upgrade, next_stage, reason = manager.can_upgrade()
    if can_upgrade:
        console.print()
        console.print(f"[green]{EMOJI_MAP['success']} 可以升级到下一阶段![/green]")
        console.print(f"[dim]下一阶段:[/dim] {next_stage}")
        console.print()
        console.print("[bold]升级建议:[/bold]")
        suggestions = manager.get_upgrade_suggestions(next_stage)
        for suggestion in suggestions:
            console.print(f"  {BULLET} {suggestion}")
        console.print()
        console.print("[dim]运行 'vibecollab lifecycle upgrade' 进行升级[/dim]")
    elif reason:
        console.print()
        console.print(f"[yellow]{EMOJI_MAP['warning']} 暂不能升级:[/yellow] {reason}")
    
    # 显示阶段历史
    if stage_history:
        console.print()
        console.print("[bold]阶段历史:[/bold]")
        for entry in stage_history:
            stage = entry.get("stage", "unknown")
            started = entry.get("started_at", "未知")
            ended = entry.get("ended_at")
            
            if ended:
                console.print(f"  {BULLET} {stage}: {started} → {ended}")
            else:
                console.print(f"  {BULLET} {stage}: {started} [bold green](进行中)[/bold green]")


@lifecycle.command()
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option("--stage", "-s", type=click.Choice(STAGE_ORDER), help="指定目标阶段（默认升级到下一阶段）")
@click.option("--force", "-f", is_flag=True, help="强制升级（跳过检查）")
def upgrade(config: str, stage: Optional[str], force: bool):
    """升级项目到下一阶段或指定阶段
    
    Examples:
    
        vibecollab lifecycle upgrade
        vibecollab lifecycle upgrade --stage production
        vibecollab lifecycle upgrade --force
    """
    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    manager = LifecycleManager(project_config)
    current_stage = manager.get_current_stage()
    
    # 确定目标阶段
    if stage is None:
        can_upgrade, next_stage, reason = manager.can_upgrade()
        if not can_upgrade and not force:
            console.print(f"[red]错误:[/red] {reason}")
            console.print("[dim]使用 --force 强制升级（不推荐）[/dim]")
            raise SystemExit(1)
        target_stage = next_stage
    else:
        target_stage = stage
    
    # 执行升级
    success, error = manager.upgrade_to_stage(target_stage)
    if not success:
        console.print(f"[red]错误:[/red] {error}")
        raise SystemExit(1)
    
    # 保存配置
    project_config.update(manager.to_config_dict())
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            project_config,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False
        )
    
    # 显示升级成功信息
    target_info = manager.get_stage_info(target_stage)
    console.print()
    console.print(Panel.fit(
        f"[bold green]{EMOJI_MAP['success']} 项目已升级到 {target_info.get('name', target_stage)} 阶段[/bold green]",
        title="升级成功"
    ))
    
    # 显示升级建议
    suggestions = manager.get_upgrade_suggestions(target_stage)
    if suggestions:
        console.print()
        console.print("[bold]升级后需要关注的变化:[/bold]")
        for suggestion in suggestions:
            console.print(f"  {BULLET} {suggestion}")
    
    console.print()
    console.print("[bold]下一步:[/bold]")
    console.print("  1. 重新生成 CONTRIBUTING_AI.md: vibecollab generate -c project.yaml")
    console.print("  2. 更新 ROADMAP.md 中的阶段信息")
    console.print("  3. 根据新阶段的原则调整开发流程")


# 导出命令组
__all__ = ["lifecycle"]
