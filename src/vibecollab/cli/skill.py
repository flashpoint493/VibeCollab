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


def _echo_operation(path: Path, action: str, ide_name: str = "") -> None:
    """输出文件操作信息。"""
    prefix = f"  {ide_name}: " if ide_name else "  "
    if action == "skipped":
        click.echo(f"{prefix}[dim]Skill file already exists: {path} (use --force to overwrite)[/dim]")
    else:
        click.echo(f"{prefix}{action.capitalize()}: {path}")


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
    from ..ide_adapter import get_adapter, list_adapters

    root = project_root or Path.cwd()

    if ide == "all":
        ides = [a.ide_type.value for a in list_adapters(skill=True)]
    else:
        ides = [ide]

    for target_ide in ides:
        adapter = get_adapter(target_ide)
        result = adapter.inject_skill(root, force=force)

        # 输出操作结果
        for op in result.operations:
            _echo_operation(op.path, op.action, adapter.display_name)

        if result.message:
            click.echo(f"  {result.message}")

    click.echo(f"\n{_('Skill injection complete!')}")


@skill_group.command("list")
def list_skills():
    """List available skills and their status"""
    from ..ide_adapter import get_adapter_info

    click.echo(_("Available Skills:"))

    for info in get_adapter_info():
        if info["supports_skill"]:
            click.echo(f"  - {info['type']}: VibeCollab protocol for {info['name']} IDE")
            if info['skill_path']:
                click.echo(f"    Path: {info['skill_path']}")


# 保留旧版函数以保持向后兼容
def _inject_opencode_skill(project_root: Path, force: bool = False):
    """向后兼容：注入 OpenCode Skill。

    Deprecated: 使用 ide_adapter.get_adapter('opencode').inject_skill() 替代。
    """
    from ..ide_adapter import get_adapter
    adapter = get_adapter("opencode")
    return adapter.inject_skill(project_root, force=force)


def _inject_cursor_skill(project_root: Path, force: bool = False):
    """向后兼容：注入 Cursor Skill。

    Deprecated: 使用 ide_adapter.get_adapter('cursor').inject_skill() 替代。
    """
    from ..ide_adapter import get_adapter
    adapter = get_adapter("cursor")
    return adapter.inject_skill(project_root, force=force)


def _inject_cline_skill(project_root: Path, force: bool = False):
    """向后兼容：注入 Cline Skill。

    Deprecated: 使用 ide_adapter.get_adapter('cline').inject_skill() 替代。
    """
    from ..ide_adapter import get_adapter
    adapter = get_adapter("cline")
    return adapter.inject_skill(project_root, force=force)


def _inject_codebuddy_skill(project_root: Path, force: bool = False):
    """向后兼容：注入 CodeBuddy Skill。

    Deprecated: 使用 ide_adapter.get_adapter('codebuddy').inject_skill() 替代。
    """
    from ..ide_adapter import get_adapter
    adapter = get_adapter("codebuddy")
    return adapter.inject_skill(project_root, force=force)


def _write_skill_file(skill_file: Path, content: str, force: bool, ide_name: str):
    """向后兼容：写入 Skill 文件。

    Deprecated: 使用适配器的 inject_skill() 方法替代。
    """
    if skill_file.exists() and not force:
        click.echo(
            f"  [dim]{ide_name} skill already exists: {skill_file} (use --force to overwrite)[/dim]"
        )
    else:
        skill_file.write_text(content, encoding="utf-8")
        action = "Updated" if skill_file.exists() else "Created"
        click.echo(f"  {action}: {skill_file}")
