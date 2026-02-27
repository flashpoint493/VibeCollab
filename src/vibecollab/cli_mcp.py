"""
MCP Server CLI 命令 — vibecollab mcp serve

提供 MCP Server 启动命令，让 AI IDE (Cursor/Cline/CodeBuddy) 通过
Model Context Protocol 自动接入 VibeCollab 协议。

使用:
    vibecollab mcp serve                # stdio 模式 (IDE 直连)
    vibecollab mcp serve --transport sse # SSE 模式 (远程调试)
    vibecollab mcp config               # 输出 IDE 配置文件内容
"""

from pathlib import Path

import click


@click.group("mcp")
def mcp_group():
    """MCP Server 管理 (v0.9.1+)

    通过 Model Context Protocol 让 AI IDE 自动接入 VibeCollab 协议。
    """
    pass


@mcp_group.command("serve")
@click.option(
    "--transport",
    "-t",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="传输模式: stdio (IDE直连) 或 sse (远程调试)",
)
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="项目根目录 (默认: 自动查找 project.yaml)",
)
def serve(transport: str, project_root: Path):
    """启动 MCP Server

    stdio 模式 (默认): 通过标准输入/输出通信，适合 IDE 直接调用。
    sse 模式: 通过 HTTP Server-Sent Events 通信，适合远程调试。

    \b
    IDE 配置示例 (Cursor .cursor/mcp.json):
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
        from .mcp_server import run_server
    except ImportError:
        click.echo(
            "错误: MCP Server 需要 mcp 依赖。\n"
            "请安装: pip install vibe-collab[mcp]",
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"启动 VibeCollab MCP Server (transport={transport})", err=True)
    if project_root:
        click.echo(f"项目根目录: {project_root}", err=True)

    run_server(project_root=project_root, transport=transport)


@mcp_group.command("config")
@click.option(
    "--ide",
    type=click.Choice(["cursor", "cline", "codebuddy"]),
    default="cursor",
    help="目标 IDE",
)
def config(ide: str):
    """输出 IDE 的 MCP 配置内容

    将输出内容复制到对应 IDE 的配置文件中即可启用 VibeCollab MCP。
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
    click.echo(f"# 将以下内容写入 {cfg['path']}:\n")
    click.echo(json_mod.dumps(cfg["content"], indent=2, ensure_ascii=False))


@mcp_group.command("inject")
@click.option(
    "--ide",
    type=click.Choice(["cursor", "cline", "codebuddy", "all"]),
    default="all",
    help="目标 IDE (默认: all)",
)
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="项目根目录",
)
def inject(ide: str, project_root: Path):
    """自动注入 MCP 配置到 IDE 配置文件

    自动创建/更新 IDE 的 MCP 配置文件，无需手动复制粘贴。
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

        # 读取已有配置或创建新的
        existing = {}
        if config_path.exists():
            try:
                existing = json_mod.loads(config_path.read_text(encoding="utf-8"))
            except (json_mod.JSONDecodeError, OSError):
                existing = {}

        # 合并 vibecollab 配置
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
        click.echo(f"已注入: {config_path}")

    click.echo(f"\n完成! 重启 IDE 后 VibeCollab MCP Server 将自动生效。")
