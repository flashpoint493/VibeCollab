"""
CLI Config commands -- LLM configuration management

Provides interactive setup wizard and config view/modify features:
- vibecollab config setup    -- Interactive setup wizard
- vibecollab config show     -- View current configuration
- vibecollab config set K V  -- Set a single config item
- vibecollab config path     -- Show config file path
"""


import click
from rich.panel import Panel
from rich.table import Table

from .._compat import EMOJI, safe_console
from ..i18n import _

# Short alias (compatible with this module's original _E variable name)
_E = EMOJI

console = safe_console()

# Provider options
PROVIDERS = {
    "1": ("openai", "OpenAI / OpenAI-compatible (OpenRouter, DeepSeek, etc.)"),
    "2": ("anthropic", "Anthropic Claude"),
}

# Common base_url presets
BASE_URL_PRESETS = {
    "1": ("", "OpenAI Official (api.openai.com)"),
    "2": ("https://openrouter.ai/api/v1", "OpenRouter (openrouter.ai)"),
    "3": ("https://api.deepseek.com/v1", "DeepSeek (api.deepseek.com)"),
    "4": ("https://dashscope.aliyuncs.com/compatible-mode/v1",
          "Alibaba Cloud Bailian (dashscope)"),
    "5": ("custom", "Custom URL"),
}


@click.group("config")
def config_group():
    """LLM Configuration Management

    Manage VibeCollab's LLM API configuration, stored in ~/.vibecollab/config.yaml.
    """
    pass


@config_group.command("setup")
def config_setup():
    """Interactive setup wizard

    Guide you through LLM API configuration, including Provider, API Key, Model, etc.
    Configuration is saved to ~/.vibecollab/config.yaml (not tracked by git).

    Examples:

        vibecollab config setup
    """
    from ..core.config_manager import load_config, save_config

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{_E['gear']} VibeCollab LLM Setup Wizard[/bold cyan]\n\n"
        "[dim]Configuration will be saved to ~/.vibecollab/config.yaml (not tracked by git)[/dim]",
        border_style="cyan",
    ))
    console.print()

    # Load existing config
    existing = load_config()
    llm = existing.get("llm", {})
    if not isinstance(llm, dict):
        llm = {}

    # Step 1: Provider
    console.print("[bold]1. Select Provider:[/bold]")
    for key, (_, desc) in PROVIDERS.items():
        marker = " [green](current)[/green]" if llm.get("provider") == PROVIDERS[key][0] else ""
        console.print(f"   {key}. {desc}{marker}")
    console.print()

    default_choice = "1"
    if llm.get("provider") == "anthropic":
        default_choice = "2"
    choice = click.prompt("  Select", default=default_choice, show_default=True)
    provider_info = PROVIDERS.get(choice, PROVIDERS["1"])
    provider = provider_info[0]
    console.print(f"  -> [cyan]{provider}[/cyan]")
    console.print()

    # Step 2: API Key
    console.print("[bold]2. API Key:[/bold]")
    current_key = llm.get("api_key", "")
    if current_key:
        masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
        console.print(f"   [dim]Current: {masked}[/dim]")
    api_key = click.prompt(
        "  Enter API Key (leave empty to keep current)" if current_key else "  Enter API Key",
        default="" if current_key else None,
        show_default=False,
        hide_input=True,
    )
    if not api_key and current_key:
        api_key = current_key
    if not api_key:
        console.print(f"  [red]{_E['err']} API Key cannot be empty[/red]")
        raise SystemExit(1)
    console.print(f"  -> [cyan]{api_key[:8]}...{api_key[-4:]}[/cyan]" if len(api_key) > 12 else "  -> [cyan]***[/cyan]")
    console.print()

    # Step 3: Base URL (for OpenAI provider)
    base_url = ""
    if provider == "openai":
        console.print("[bold]3. API Endpoint:[/bold]")
        for key, (_, desc) in BASE_URL_PRESETS.items():
            marker = ""
            if llm.get("base_url") and llm["base_url"] == BASE_URL_PRESETS[key][0]:
                marker = " [green](current)[/green]"
            console.print(f"   {key}. {desc}{marker}")
        console.print()

        default_url_choice = "1"
        # Detect existing base_url match
        for k, (url, _) in BASE_URL_PRESETS.items():
            if llm.get("base_url") == url:
                default_url_choice = k
                break

        url_choice = click.prompt("  Select", default=default_url_choice,
                                  show_default=True)
        preset = BASE_URL_PRESETS.get(url_choice, BASE_URL_PRESETS["1"])
        if preset[0] == "custom":
            base_url = click.prompt("  Enter custom URL",
                                    default=llm.get("base_url", ""))
        else:
            base_url = preset[0]

        if base_url:
            console.print(f"  -> [cyan]{base_url}[/cyan]")
        else:
            console.print("  -> [cyan]OpenAI official default[/cyan]")
        console.print()

    # Step 4: Model (optional)
    console.print(f"[bold]{'4' if provider == 'openai' else '3'}. Model (optional):[/bold]")
    default_model = llm.get("model", "")
    if provider == "openai":
        console.print("   [dim]Common: gpt-4o, gpt-4o-mini, deepseek-chat, "
                       "deepseek/deepseek-chat-v3-0324[/dim]")
    else:
        console.print("   [dim]Common: claude-sonnet-4-20250514, "
                       "claude-opus-4-20250514[/dim]")
    model = click.prompt("  Model name (leave empty for default)",
                         default=default_model, show_default=False)
    if model:
        console.print(f"  -> [cyan]{model}[/cyan]")
    else:
        from ..agent.llm_client import DEFAULT_MODEL_ANTHROPIC, DEFAULT_MODEL_OPENAI
        default = (DEFAULT_MODEL_ANTHROPIC if provider == "anthropic"
                   else DEFAULT_MODEL_OPENAI)
        console.print(f"  -> [cyan]{default}[/cyan] (default)")
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
        f"[green]{_E['ok']} Configuration saved![/green]\n\n"
        f"File: [cyan]{path}[/cyan]\n\n"
        f"You can now use:\n"
        f"  vibecollab ai ask \"Hello\"\n"
        f"  vibecollab ai chat\n"
        f"  vibecollab config show",
        border_style="green",
    ))
    console.print()


@config_group.command("show")
def config_show():
    """View current LLM configuration

    Shows the merged result from all configuration sources (environment variables, config file, defaults).

    Examples:

        vibecollab config show
    """
    from ..core.config_manager import get_config_path, load_config, resolve_llm_config

    console.print()

    # Show config file status
    config_path = get_config_path()
    if config_path.exists():
        console.print(f"Config file: [cyan]{config_path}[/cyan]")
    else:
        console.print(f"Config file: [yellow]Not created[/yellow] ({config_path})")
        console.print("[dim]Run 'vibecollab config setup' to create configuration[/dim]")
    console.print()

    # Parse merged config
    resolved = resolve_llm_config()

    # Read raw values from config file
    file_config = load_config().get("llm", {})
    if not isinstance(file_config, dict):
        file_config = {}

    import os
    table = Table(title="LLM Configuration", show_header=True)
    table.add_column("Config Item", style="cyan", min_width=12)
    table.add_column("Current Value", min_width=20)
    table.add_column("Source", style="dim", min_width=12)

    fields = [
        ("provider", "VIBECOLLAB_LLM_PROVIDER", "openai"),
        ("api_key", "VIBECOLLAB_LLM_API_KEY", "(not set)"),
        ("model", "VIBECOLLAB_LLM_MODEL", "(auto)"),
        ("base_url", "VIBECOLLAB_LLM_BASE_URL", "(default)"),
        ("max_tokens", "VIBECOLLAB_LLM_MAX_TOKENS", "4096"),
    ]

    for config_key, env_key, default_display in fields:
        env_val = os.environ.get(env_key)
        file_val = file_config.get(config_key)
        resolved_val = resolved.get(config_key)

        # Determine display value and source
        if env_val:
            source = f"Env var ({env_key})"
            display_val = env_val
        elif file_val is not None and str(file_val).strip():
            source = "Config file"
            display_val = str(file_val)
        elif resolved_val:
            source = "Default"
            display_val = resolved_val
        else:
            source = "-"
            display_val = default_display

        # Mask API key
        if config_key == "api_key" and display_val and display_val != "(not set)":
            if len(display_val) > 12:
                display_val = display_val[:8] + "..." + display_val[-4:]
            else:
                display_val = "***"

        # Color coding
        if source == "-" and config_key == "api_key":
            display_val = f"[red]{display_val}[/red]"
        elif display_val not in ("(not set)", "(default)", "(auto)"):
            display_val = f"[green]{display_val}[/green]"

        table.add_row(config_key, display_val, source)

    console.print(table)
    console.print()

    # Status check
    if resolved.get("api_key"):
        console.print(f"{_E['ok']} LLM configured, you can use `vibecollab ai ask` command")
    else:
        console.print(f"{_E['warn']} LLM not configured, run `vibecollab config setup` to start")
    console.print()


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a single configuration item

    Supports dot path: llm.provider, llm.api_key, llm.model, llm.base_url

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
        console.print(f"[yellow]{_E['warn']} Unknown config item: {key}[/yellow]")
        console.print(f"[dim]Known config items: {', '.join(sorted(known_keys))}[/dim]")
        # Still allow setting it
        if not click.confirm("Set anyway?", default=False):
            raise SystemExit(0)

    path = set_config_value(key, value)

    # Mask api_key in display
    display_val = value
    if "api_key" in key and len(value) > 12:
        display_val = value[:8] + "..." + value[-4:]

    console.print(f"{_E['ok']} {key} = [cyan]{display_val}[/cyan]")
    console.print(f"[dim]Saved to {path}[/dim]")


@config_group.command("path")
def config_path():
    """Show config file path

    Examples:

        vibecollab config path
    """
    from ..core.config_manager import get_config_path

    path = get_config_path()
    console.print(str(path))
    if path.exists():
        console.print(f"[dim]File exists ({path.stat().st_size} bytes)[/dim]")
    else:
        console.print("[dim]File does not exist, run 'vibecollab config setup' to create[/dim]")