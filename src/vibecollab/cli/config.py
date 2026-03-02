"""
CLI Config 命令 — LLM 配置管理

提供交互式配置向导和配置查看/修改功能:
- vibecollab config setup    — 交互式配置向导
- vibecollab config show     — 查看当前配置
- vibecollab config set K V  — 设置单个配置项
- vibecollab config path     — 显示配置文件路径
"""


import click
from rich.panel import Panel
from rich.table import Table

from .._compat import EMOJI, safe_console

# 短别名（兼容此模块原有 _E 变量名）
_E = EMOJI

console = safe_console()

# Provider 选项
PROVIDERS = {
    "1": ("openai", "OpenAI / OpenAI-compatible (OpenRouter, DeepSeek, etc.)"),
    "2": ("anthropic", "Anthropic Claude"),
}

# 常用 base_url 预设
BASE_URL_PRESETS = {
    "1": ("", "OpenAI 官方 (api.openai.com)"),
    "2": ("https://openrouter.ai/api/v1", "OpenRouter (openrouter.ai)"),
    "3": ("https://api.deepseek.com/v1", "DeepSeek (api.deepseek.com)"),
    "4": ("https://dashscope.aliyuncs.com/compatible-mode/v1",
          "阿里云百炼 (dashscope)"),
    "5": ("custom", "自定义 URL"),
}


@click.group("config")
def config_group():
    """LLM 配置管理

    管理 VibeCollab 的 LLM API 配置，存储在 ~/.vibecollab/config.yaml。
    """
    pass


@config_group.command("setup")
def config_setup():
    """交互式配置向导

    引导你完成 LLM API 配置，包括 Provider、API Key、Model 等。
    配置保存到 ~/.vibecollab/config.yaml（不会进入 git）。

    Examples:

        vibecollab config setup
    """
    from ..core.config_manager import load_config, save_config

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{_E['gear']} VibeCollab LLM 配置向导[/bold cyan]\n\n"
        "[dim]配置将保存到 ~/.vibecollab/config.yaml（不会进入 git）[/dim]",
        border_style="cyan",
    ))
    console.print()

    # 加载已有配置
    existing = load_config()
    llm = existing.get("llm", {})
    if not isinstance(llm, dict):
        llm = {}

    # Step 1: Provider
    console.print("[bold]1. 选择 Provider:[/bold]")
    for key, (_, desc) in PROVIDERS.items():
        marker = " [green](当前)[/green]" if llm.get("provider") == PROVIDERS[key][0] else ""
        console.print(f"   {key}. {desc}{marker}")
    console.print()

    default_choice = "1"
    if llm.get("provider") == "anthropic":
        default_choice = "2"
    choice = click.prompt("  选择", default=default_choice, show_default=True)
    provider_info = PROVIDERS.get(choice, PROVIDERS["1"])
    provider = provider_info[0]
    console.print(f"  -> [cyan]{provider}[/cyan]")
    console.print()

    # Step 2: API Key
    console.print("[bold]2. API Key:[/bold]")
    current_key = llm.get("api_key", "")
    if current_key:
        masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
        console.print(f"   [dim]当前: {masked}[/dim]")
    api_key = click.prompt(
        "  输入 API Key (留空保持不变)" if current_key else "  输入 API Key",
        default="" if current_key else None,
        show_default=False,
        hide_input=True,
    )
    if not api_key and current_key:
        api_key = current_key
    if not api_key:
        console.print(f"  [red]{_E['err']} API Key 不能为空[/red]")
        raise SystemExit(1)
    console.print(f"  -> [cyan]{api_key[:8]}...{api_key[-4:]}[/cyan]" if len(api_key) > 12 else "  -> [cyan]***[/cyan]")
    console.print()

    # Step 3: Base URL (for OpenAI provider)
    base_url = ""
    if provider == "openai":
        console.print("[bold]3. API 端点:[/bold]")
        for key, (_, desc) in BASE_URL_PRESETS.items():
            marker = ""
            if llm.get("base_url") and llm["base_url"] == BASE_URL_PRESETS[key][0]:
                marker = " [green](当前)[/green]"
            console.print(f"   {key}. {desc}{marker}")
        console.print()

        default_url_choice = "1"
        # 检测已有 base_url 匹配
        for k, (url, _) in BASE_URL_PRESETS.items():
            if llm.get("base_url") == url:
                default_url_choice = k
                break

        url_choice = click.prompt("  选择", default=default_url_choice,
                                  show_default=True)
        preset = BASE_URL_PRESETS.get(url_choice, BASE_URL_PRESETS["1"])
        if preset[0] == "custom":
            base_url = click.prompt("  输入自定义 URL",
                                    default=llm.get("base_url", ""))
        else:
            base_url = preset[0]

        if base_url:
            console.print(f"  -> [cyan]{base_url}[/cyan]")
        else:
            console.print("  -> [cyan]OpenAI 官方默认[/cyan]")
        console.print()

    # Step 4: Model (optional)
    console.print(f"[bold]{'4' if provider == 'openai' else '3'}. 模型 (可选):[/bold]")
    default_model = llm.get("model", "")
    if provider == "openai":
        console.print("   [dim]常用: gpt-4o, gpt-4o-mini, deepseek-chat, "
                       "deepseek/deepseek-chat-v3-0324[/dim]")
    else:
        console.print("   [dim]常用: claude-sonnet-4-20250514, "
                       "claude-opus-4-20250514[/dim]")
    model = click.prompt("  模型名称 (留空使用默认)",
                         default=default_model, show_default=False)
    if model:
        console.print(f"  -> [cyan]{model}[/cyan]")
    else:
        from ..agent.llm_client import DEFAULT_MODEL_ANTHROPIC, DEFAULT_MODEL_OPENAI
        default = (DEFAULT_MODEL_ANTHROPIC if provider == "anthropic"
                   else DEFAULT_MODEL_OPENAI)
        console.print(f"  -> [cyan]{default}[/cyan] (默认)")
    console.print()

    # Save
    config = existing.copy()
    config["llm"] = {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
    }

    path = save_config(config)

    console.print(Panel.fit(
        f"[green]{_E['ok']} 配置已保存![/green]\n\n"
        f"文件: [cyan]{path}[/cyan]\n\n"
        f"现在可以使用:\n"
        f"  vibecollab ai ask \"你好\"\n"
        f"  vibecollab ai chat\n"
        f"  vibecollab config show",
        border_style="green",
    ))
    console.print()


@config_group.command("show")
def config_show():
    """查看当前 LLM 配置

    显示所有配置来源（环境变量、配置文件、默认值）的合并结果。

    Examples:

        vibecollab config show
    """
    from ..core.config_manager import get_config_path, load_config, resolve_llm_config

    console.print()

    # 显示配置文件状态
    config_path = get_config_path()
    if config_path.exists():
        console.print(f"配置文件: [cyan]{config_path}[/cyan]")
    else:
        console.print(f"配置文件: [yellow]未创建[/yellow] ({config_path})")
        console.print("[dim]运行 'vibecollab config setup' 创建配置[/dim]")
    console.print()

    # 解析合并后的配置
    resolved = resolve_llm_config()

    # 从配置文件读取原始值
    file_config = load_config().get("llm", {})
    if not isinstance(file_config, dict):
        file_config = {}

    import os
    table = Table(title="LLM 配置", show_header=True)
    table.add_column("配置项", style="cyan", min_width=12)
    table.add_column("当前值", min_width=20)
    table.add_column("来源", style="dim", min_width=12)

    fields = [
        ("provider", "VIBECOLLAB_LLM_PROVIDER", "openai"),
        ("api_key", "VIBECOLLAB_LLM_API_KEY", "(未设置)"),
        ("model", "VIBECOLLAB_LLM_MODEL", "(自动)"),
        ("base_url", "VIBECOLLAB_LLM_BASE_URL", "(默认)"),
        ("max_tokens", "VIBECOLLAB_LLM_MAX_TOKENS", "4096"),
    ]

    for config_key, env_key, default_display in fields:
        env_val = os.environ.get(env_key)
        file_val = file_config.get(config_key)
        resolved_val = resolved.get(config_key)

        # Determine display value and source
        if env_val:
            source = f"环境变量 ({env_key})"
            display_val = env_val
        elif file_val is not None and str(file_val).strip():
            source = "配置文件"
            display_val = str(file_val)
        elif resolved_val:
            source = "默认值"
            display_val = resolved_val
        else:
            source = "-"
            display_val = default_display

        # Mask API key
        if config_key == "api_key" and display_val and display_val != "(未设置)":
            if len(display_val) > 12:
                display_val = display_val[:8] + "..." + display_val[-4:]
            else:
                display_val = "***"

        # Color coding
        if source == "-" and config_key == "api_key":
            display_val = f"[red]{display_val}[/red]"
        elif display_val not in ("(未设置)", "(默认)", "(自动)"):
            display_val = f"[green]{display_val}[/green]"

        table.add_row(config_key, display_val, source)

    console.print(table)
    console.print()

    # Status check
    if resolved.get("api_key"):
        console.print(f"{_E['ok']} LLM 已配置，可以使用 `vibecollab ai ask` 命令")
    else:
        console.print(f"{_E['warn']} LLM 未配置，运行 `vibecollab config setup` 开始配置")
    console.print()


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """设置单个配置项

    支持 dot 路径: llm.provider, llm.api_key, llm.model, llm.base_url

    Examples:

        vibecollab config set llm.provider openai

        vibecollab config set llm.model gpt-4o-mini

        vibecollab config set llm.base_url https://openrouter.ai/api/v1
    """
    from ..core.config_manager import set_config_value

    # Validate known keys
    known_keys = {
        "llm.provider", "llm.api_key", "llm.model",
        "llm.base_url", "llm.max_tokens",
    }
    if key not in known_keys:
        console.print(f"[yellow]{_E['warn']} 未知配置项: {key}[/yellow]")
        console.print(f"[dim]已知配置项: {', '.join(sorted(known_keys))}[/dim]")
        # Still allow setting it
        if not click.confirm("仍然设置?", default=False):
            raise SystemExit(0)

    path = set_config_value(key, value)

    # Mask api_key in display
    display_val = value
    if "api_key" in key and len(value) > 12:
        display_val = value[:8] + "..." + value[-4:]

    console.print(f"{_E['ok']} {key} = [cyan]{display_val}[/cyan]")
    console.print(f"[dim]已保存到 {path}[/dim]")


@config_group.command("path")
def config_path():
    """显示配置文件路径

    Examples:

        vibecollab config path
    """
    from ..core.config_manager import get_config_path

    path = get_config_path()
    console.print(str(path))
    if path.exists():
        console.print(f"[dim]文件存在 ({path.stat().st_size} bytes)[/dim]")
    else:
        console.print("[dim]文件不存在，运行 'vibecollab config setup' 创建[/dim]")
