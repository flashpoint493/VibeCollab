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
    help="Transport mode: stdio (IDE direct) or sse (remote debugging)",
)
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Project root directory (default: auto-find project.yaml)",
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
    try:
        from ..agent.mcp_server import run_server
    except ImportError:
        click.echo(
            "Error: MCP Server requires mcp dependency.\n"
            "Install: pip install vibe-collab[mcp]",
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"Starting VibeCollab MCP Server (transport={transport})", err=True)
    if project_root:
        click.echo(f"Project root: {project_root}", err=True)

    run_server(project_root=project_root, transport=transport)


@mcp_group.command("config")
@click.option(
    "--ide",
    type=click.Choice(["cursor", "cline", "codebuddy"]),
    default="cursor",
    help="Target IDE",
)
def config(ide: str):
    """Output IDE MCP configuration content

    Copy the output to the corresponding IDE config file to enable VibeCollab MCP.
    """
    import json as json_mod

    configs = {
        "cursor": {
            "path": ".cursor/mcp.json",
            "content": {
                "mcpServers": {
                    "vibecollab": {
                        "command": "vibecollab",
                        "args": ["mcp", "serve"],
                    }
                }
            },
        },
        "cline": {
            "path": ".cline/mcp_settings.json",
            "content": {
                "mcpServers": {
                    "vibecollab": {
                        "command": "vibecollab",
                        "args": ["mcp", "serve"],
                        "disabled": False,
                    }
                }
            },
        },
        "codebuddy": {
            "path": ".codebuddy/mcp.json",
            "content": {
                "mcpServers": {
                    "vibecollab": {
                        "command": "vibecollab",
                        "args": ["mcp", "serve"],
                    }
                }
            },
        },
    }

    cfg = configs[ide]
    click.echo(f"# Write the following content to {cfg['path']}:\n")
    click.echo(json_mod.dumps(cfg["content"], indent=2, ensure_ascii=False))


@mcp_group.command("inject")
@click.option(
    "--ide",
    type=click.Choice(["cursor", "cline", "codebuddy", "all"]),
    default="all",
    help="Target IDE (default: all)",
)
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Project root directory",
)
def inject(ide: str, project_root: Path):
    """Auto-inject MCP config into IDE configuration files

    Automatically create/update IDE MCP config files, no manual copy-paste needed.
    """
    import json as json_mod

    root = project_root or Path.cwd()

    targets = {
        "cursor": root / ".cursor" / "mcp.json",
        "cline": root / ".cline" / "mcp_settings.json",
        "codebuddy": root / ".codebuddy" / "mcp.json",
    }

    vibecollab_entry = {
        "command": "vibecollab",
        "args": ["mcp", "serve"],
    }

    ides = [ide] if ide != "all" else list(targets.keys())

    for target_ide in ides:
        config_path = targets[target_ide]
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing config or create new
        existing = {}
        if config_path.exists():
            try:
                existing = json_mod.loads(config_path.read_text(encoding="utf-8"))
            except (json_mod.JSONDecodeError, OSError):
                existing = {}

        # Merge vibecollab config
        if "mcpServers" not in existing:
            existing["mcpServers"] = {}

        if target_ide == "cline":
            vibecollab_entry_copy = {**vibecollab_entry, "disabled": False}
        else:
            vibecollab_entry_copy = vibecollab_entry

        existing["mcpServers"]["vibecollab"] = vibecollab_entry_copy

        config_path.write_text(
            json_mod.dumps(existing, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        click.echo(f"Injected: {config_path}")

    click.echo(f"\nDone! VibeCollab MCP Server will take effect after restarting IDE.")
