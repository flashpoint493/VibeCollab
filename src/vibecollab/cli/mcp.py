"""
MCP Server CLI Commands -- vibecollab mcp serve

Provides MCP Server startup commands for AI IDEs (Cursor/Cline/CodeBuddy)
to auto-connect to VibeCollab protocol via Model Context Protocol.

Usage:
    vibecollab mcp serve                # stdio mode (IDE direct connect)
    vibecollab mcp serve --transport sse # SSE mode (remote debugging)
    vibecollab mcp config               # Output IDE config file content
"""

from pathlib import Path

import click

from ..i18n import _


@click.group("mcp")
def mcp_group():
    """MCP Server management (v0.9.1+)

    Let AI IDEs automatically connect to VibeCollab protocol via Model Context Protocol.
    """
    pass


@mcp_group.command("serve")
@click.option(
    "--transport",
    "-t",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help=_("Transport mode: stdio (IDE direct) or sse (remote debugging)"),
)
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help=_("Project root directory (default: auto-find project.yaml)"),
)
def serve(transport: str, project_root: Path):
    """Start MCP Server

    stdio mode (default): Communicates via stdin/stdout, suitable for IDE direct invocation.
    sse mode: Communicates via HTTP Server-Sent Events, suitable for remote debugging.

    \b
    IDE configuration example (Cursor .cursor/mcp.json):
      {
        "mcpServers": {
          "vibecollab": {
            "command": "vibecollab",
            "args": ["mcp", "serve"]
          }
        }
      }
    """
    from ..agent.mcp_server import run_server

    click.echo(_("Starting VibeCollab MCP Server (transport={transport})").format(transport=transport), err=True)
    if project_root:
        click.echo(f"Project root: {project_root}", err=True)

    run_server(project_root=project_root, transport=transport)


@mcp_group.command("config")
@click.option(
    "--ide",
    type=click.Choice(["cursor", "cline", "codebuddy"]),
    default="cursor",
    help=_("Target IDE"),
)
def config(ide: str):
    """Output IDE MCP configuration content

    Copy the output to the corresponding IDE config file to enable VibeCollab MCP.
    """
    import json as json_mod
    import shutil

    from ..ide_adapter import get_adapter

    # Resolve full path to vibecollab executable
    vibecollab_cmd = shutil.which("vibecollab")
    if vibecollab_cmd:
        # Normalize path separators for cross-platform compatibility
        vibecollab_cmd = vibecollab_cmd.replace("\\", "/")
    else:
        vibecollab_cmd = "vibecollab"  # fallback to bare name

    adapter = get_adapter(ide)
    mcp_config = adapter.get_mcp_config(vibecollab_cmd, ["mcp", "serve"])

    click.echo(f"# Write the following content to {adapter.mcp_config_path}:\n")
    click.echo(json_mod.dumps(mcp_config, indent=2, ensure_ascii=False))


@mcp_group.command("inject")
@click.option(
    "--ide",
    type=click.Choice(["cursor", "cline", "codebuddy", "all"]),
    default="all",
    help=_("Target IDE (default: all)"),
)
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help=_("Project root directory"),
)
def inject(ide: str, project_root: Path):
    """Auto-inject MCP config into IDE configuration files

    Automatically create/update IDE MCP config files, no manual copy-paste needed.
    """
    import shutil

    from ..ide_adapter import get_adapter, list_adapters

    root = project_root or Path.cwd()

    # Resolve full path to vibecollab executable
    vibecollab_cmd = shutil.which("vibecollab")
    if vibecollab_cmd:
        vibecollab_cmd = vibecollab_cmd.replace("\\", "/")
    else:
        vibecollab_cmd = "vibecollab"

    if ide == "all":
        ides = [a.ide_type.value for a in list_adapters(mcp=True)]
    else:
        ides = [ide]

    for target_ide in ides:
        adapter = get_adapter(target_ide)
        result = adapter.inject_mcp_config(
            root,
            command=vibecollab_cmd,
            args=["mcp", "serve"]
        )

        # 输出操作结果
        for op in result.operations:
            if op.action == "skipped":
                click.echo(f"  [dim]{adapter.display_name}: {op.message}[/dim]")
            else:
                click.echo(f"  {op.action.capitalize()}: {op.path}")

    click.echo(f"\n{_('Done! VibeCollab MCP Server will take effect after restarting IDE.')}")


# 向后兼容的函数
def _get_mcp_config(ide: str, command: str, args: list) -> dict:
    """向后兼容：获取 MCP 配置。

    Deprecated: 使用 ide_adapter.get_adapter(ide).get_mcp_config() 替代。
    """
    from ..ide_adapter import get_adapter
    adapter = get_adapter(ide)
    return adapter.get_mcp_config(command, args)
