"""
LLMContext CLI - Command line interface
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import click
import yaml
from rich.panel import Panel
from rich.table import Table

from .. import __version__
from .._compat import BULLET, EMOJI, is_windows_gbk, safe_console
from ..core.generator import LLMContextGenerator
from ..core.project import Project
from ..core.protocol_checker import ProtocolChecker
from ..core.templates import TemplateManager
from ..i18n import _, setup_locale
from ..utils.git import is_git_repo
from ..utils.llmstxt import LLMsTxtManager

# Backward compatible variable names
USE_EMOJI = not is_windows_gbk()
EMOJI_MAP = EMOJI

console = safe_console()


DOMAINS = ["generic", "game", "web", "data", "mobile", "infra"]


def _safe_load_yaml(path: Path, label: str = "config file") -> dict:
    """Safely load a YAML file with friendly error messages.

    Handles: file not found, YAML syntax error, empty file.
    """
    if not path.exists():
        console.print(f"[red]{_('Error:')}[/red] {label} {_('not found:')} {path}")
        console.print(
            f"[dim]{_('Hint: run in the project directory or use -c to specify the path')}[/dim]"
        )
        raise SystemExit(1)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        console.print(f"[red]{_('Error:')}[/red] {label} {_('has invalid YAML syntax:')} {path}")
        console.print(f"[dim]{e}[/dim]")
        raise SystemExit(1)
    except OSError as e:
        console.print(f"[red]{_('Error:')}[/red] {_('Cannot read')} {label}: {e}")
        raise SystemExit(1)
    if data is None:
        console.print(f"[red]{_('Error:')}[/red] {label} {_('is empty:')} {path}")
        raise SystemExit(1)
    if not isinstance(data, dict):
        console.print(
            f"[red]{_('Error:')}[/red] {label} {_('has invalid format (expected YAML dict):')} {path}"
        )
        raise SystemExit(1)
    return data


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts; override takes precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@click.group()
@click.version_option(version=__version__, prog_name="vibecollab")
@click.option(
    "--lang",
    envvar="VIBECOLLAB_LANG",
    default=None,
    hidden=True,
    help="Language for CLI output (en/zh). Default: en. Env: VIBECOLLAB_LANG",
)
def main(lang):
    """VibeCollab - AI Collaboration Protocol Generator

    Generate standardized AI collaboration protocol documents from YAML config,
    supporting Vibe Development philosophy for human-AI collaboration.
    Automatically integrates llms.txt standard.
    """
    setup_locale(lang)


@main.command()
@click.option("--name", "-n", required=True, help=_("Project name"))
@click.option(
    "--domain", "-d", type=click.Choice(DOMAINS), default="generic", help=_("Business domain")
)
@click.option(
    "--output", "-o", default=".", help=_("Output directory (default: current directory)")
)
@click.option("--force", "-f", is_flag=True, help=_("Force overwrite existing directory"))
@click.option("--no-git", is_flag=True, help=_("Skip automatic Git initialization"))
@click.option("--role-based", is_flag=True, help=_("Enable role-based mode"))
def init(name: str, domain: str, output: str, force: bool, no_git: bool, role_based: bool):
    """Initialize a new project

    Examples:

        vibecollab init -n "MyProject" -d web

        vibecollab init -n "MyProject" -d web -o ./my-project

        vibecollab init -n "GameProject" -d game --force

        vibecollab init -n "TeamProject" --role-based
    """
    output_path = Path(output)

    if output_path.exists() and not force:
        if any(output_path.iterdir()):
            console.print(
                f"[red]{_('Error:')}[/red] {_('Directory {dir} already exists and is not empty. Use --force to overwrite.').format(dir=output)}"
            )
            raise SystemExit(1)

    with console.status(f"[bold green]{_('Initializing project {name}...').format(name=name)}"):
        try:
            project = Project.create(
                name=name, domain=domain, output_dir=output_path, role_based=role_based
            )
            project.generate_all(auto_init_git=not no_git)
        except PermissionError as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Permission denied:')} {e}")
            raise SystemExit(1)
        except OSError as e:
            console.print(
                f"[red]{_('Error:')}[/red] {_('File system error (disk full/invalid path):')} {e}"
            )
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Project initialization failed:')} {e}")
            raise SystemExit(1)

    console.print()
    mode_text = _("role-based") if role_based else _("single-role")
    console.print(
        Panel.fit(
            f"[bold green]{EMOJI_MAP['success']} {_('Project {name} initialized!').format(name=name)}[/bold green]\n\n"
            f"[dim]{_('Directory:')}[/dim] {output_path.absolute()}\n"
            f"[dim]{_('Domain:')}[/dim] {domain}\n"
            f"[dim]{_('Mode:')}[/dim] {mode_text}",
            title=_("Done"),
        )
    )

    table = Table(title=_("Generated Files"), show_header=True)
    table.add_column(_("File"), style="cyan")
    table.add_column(_("Description"))
    table.add_row("CONTRIBUTING_AI.md", _("AI collaboration rules"))
    table.add_row("llms.txt", _("Project context (with collaboration rules reference)"))
    table.add_row("project.yaml", _("Project config (editable)"))

    if role_based:
        table.add_row("docs/CONTEXT.md", _("Global aggregated context (auto-generated)"))
        table.add_row("docs/roles/{dev}/CONTEXT.md", _("Per-role context"))
        table.add_row("docs/roles/COLLABORATION.md", _("Collaboration document"))
    else:
        table.add_row("docs/CONTEXT.md", _("Current context"))

    table.add_row("docs/DECISIONS.md", _("Decision records"))
    table.add_row("docs/CHANGELOG.md", _("Changelog"))
    table.add_row("docs/ROADMAP.md", _("Roadmap"))
    table.add_row("docs/QA_TEST_CASES.md", _("Test cases"))
    console.print(table)

    git_warning = project.config.get("_meta", {}).get("git_warning")
    git_auto_init = project.config.get("_meta", {}).get("git_auto_init", False)

    if git_auto_init:
        console.print()
        console.print(
            f"[green]{EMOJI_MAP['success']} {_('Git repository initialized automatically')}[/green]"
        )
    elif git_warning:
        console.print()
        console.print(f"[yellow]{EMOJI_MAP['warning']} {git_warning}[/yellow]")
        console.print(
            f"[dim]{_('Hint: consider initializing a Git repository to track changes')}[/dim]"
        )

    if role_based:
        from ..domain.role import RoleManager

        dm = RoleManager(output_path, project.config)
        current_dev = dm.get_current_role()

        console.print()
        console.print(f"[bold cyan]{_('Role-based mode enabled')}[/bold cyan]")
        console.print(f"  {BULLET} {_('Current role:')} {current_dev}")
        cmd_hint = _("Use 'vibecollab dev' for related commands")
        console.print(f"  {BULLET} {cmd_hint}")

    console.print()
    console.print(f"[bold]{_('Next steps:')}[/bold]")
    console.print(f"  1. cd {output}")
    step = 2
    if not is_git_repo(output_path):
        console.print(f"  {step}. git init  # {_('Initialize Git repository')}")
        step += 1
    if role_based:
        console.print(f"  {step}. vibecollab role whoami  # {_('Check current role')}")
        step += 1
    console.print(f"  {step}. {_('Edit project.yaml to customize configuration')}")
    step += 1
    console.print(f"  {step}. vibecollab generate -c project.yaml  # {_('Regenerate')}")
    step += 1
    console.print(f"  {step}. {_('Start your Vibe Development journey!')}")


@main.command()
@click.option("--config", "-c", required=True, help=_("YAML config file path"))
@click.option("--output", "-o", default="CONTRIBUTING_AI.md", help=_("Output file path"))
@click.option("--no-llmstxt", is_flag=True, help=_("Skip llms.txt integration"))
def generate(config: str, output: str, no_llmstxt: bool):
    """Generate AI collaboration rules document from config and integrate llms.txt

    Examples:

        vibecollab generate -c project.yaml -o CONTRIBUTING_AI.md

        vibecollab generate -c my-config.yaml --no-llmstxt
    """
    config_path = Path(config)
    output_path = Path(output)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with console.status(f"[bold green]{_('Generating collaboration rules document...')}"):
        try:
            generator = LLMContextGenerator.from_file(config_path, project_root)
            content = generator.generate()
            output_path.write_text(content, encoding="utf-8")

            # Integrate llms.txt (unless skipped)
            if not no_llmstxt:
                project_config = generator.config
                project_name = project_config.get("project", {}).get("name", "Project")
                project_desc = project_config.get("project", {}).get(
                    "description", "AI-assisted development project"
                )

                updated, llmstxt_path = LLMsTxtManager.ensure_integration(
                    project_root, project_name, project_desc, output_path
                )

                if updated:
                    if llmstxt_path and llmstxt_path.exists():
                        console.print(
                            f"[green]{EMOJI_MAP['success']} {_('Updated:')}[/green] {llmstxt_path}"
                        )
                    else:
                        console.print(
                            f"[green]{EMOJI_MAP['success']} {_('Created:')}[/green] {llmstxt_path}"
                        )
                else:
                    console.print(
                        f"[dim]{_('Info: llms.txt already contains collaboration rules reference')}[/dim]"
                    )
        except yaml.YAMLError as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Invalid YAML in config file:')} {e}")
            raise SystemExit(1)
        except FileNotFoundError as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Required file not found:')} {e}")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Document generation failed:')} {e}")
            raise SystemExit(1)

    console.print(f"[green]{EMOJI_MAP['success']} {_('Generated:')}[/green] {output_path}")
    console.print(f"[dim]{_('Config:')}[/dim] {config_path}")


@main.command()
@click.option("--config", "-c", required=True, help=_("YAML config file path"))
def validate(config: str):
    """Validate configuration file

    Examples:

        vibecollab validate -c project.yaml
    """
    config_path = Path(config)

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with console.status(f"[bold green]{_('Validating configuration...')}"):
        try:
            generator = LLMContextGenerator.from_file(config_path)
            errors = generator.validate()
        except yaml.YAMLError as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Invalid YAML in config file:')} {e}")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Config parsing failed:')} {e}")
            raise SystemExit(1)

    if errors:
        console.print(
            f"[red]{EMOJI_MAP['error']} {_('Found {n} issue(s):').format(n=len(errors))}[/red]"
        )
        for err in errors:
            console.print(f"  - {err}")
        raise SystemExit(1)
    else:
        console.print(f"[green]{EMOJI_MAP['success']} {_('Config valid:')}[/green] {config}")


@main.command()
def domains():
    """List supported business domains"""
    table = Table(title=_("Supported Domains"), show_header=True)
    table.add_column(_("Domain"), style="cyan")
    table.add_column(_("Description"))
    table.add_column(_("Features"))

    domain_info = {
        "generic": (_("General purpose"), _("Basic config")),
        "game": (_("Game development"), _("GM console, GDD docs")),
        "web": (_("Web application"), _("API docs, deployment env")),
        "data": (_("Data engineering"), _("ETL pipeline, data quality")),
        "mobile": (_("Mobile app"), _("Platform adaptation, release flow")),
        "infra": (_("Infrastructure"), _("IaC, monitoring & alerting")),
    }

    for domain in DOMAINS:
        desc, features = domain_info.get(domain, ("", ""))
        table.add_row(domain, desc, features)

    console.print(table)


@main.command()
def templates():
    """List available templates"""
    tm = TemplateManager()
    available = tm.list_templates()

    table = Table(title=_("Available Templates"), show_header=True)
    table.add_column(_("Template"), style="cyan")
    table.add_column(_("Type"))
    table.add_column(_("Path"))

    for tpl in available:
        table.add_row(tpl["name"], tpl["type"], str(tpl["path"]))

    console.print(table)


@main.command()
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--dry-run", is_flag=True, help=_("Dry run: show changes only"))
@click.option("--force", "-f", is_flag=True, help=_("Force upgrade without backup"))
def upgrade(config: str, dry_run: bool, force: bool):
    """Upgrade protocol to the latest version

    Smart merge: preserves user-customized configuration while applying latest protocol features.

    Examples:

        vibecollab upgrade                    # Upgrade the project in current directory

        vibecollab upgrade -c project.yaml    # Specify config file

        vibecollab upgrade --dry-run          # Preview changes
    """
    config_path = Path(config)

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        console.print(
            f"[dim]{_('Hint: Run in the project directory, or use -c to specify the config file path')}[/dim]"
        )
        raise SystemExit(1)

    # Load user config
    user_config = _safe_load_yaml(config_path)

    # Get latest template
    tm = TemplateManager()
    try:
        latest_template = yaml.safe_load(tm.get_template("default"))
        if not isinstance(latest_template, dict):
            console.print(
                f"[red]{_('Error:')}[/red] {_('Built-in default template has invalid format')}"
            )
            raise SystemExit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]{_('Error:')}[/red] {_('Built-in template parse failed:')} {e}")
        raise SystemExit(1)

    # Record user-customized key fields (should not be overwritten)
    user_preserved = {
        "project": user_config.get("project", {}),
        "roles": user_config.get("roles"),
        "confirmed_decisions": user_config.get("confirmed_decisions"),
        "domain_extensions": user_config.get("domain_extensions"),
        "role_context": user_config.get("role_context"),
    }

    # Deep merge: latest as base, user_preserved overrides
    merged = deep_merge(latest_template, {k: v for k, v in user_preserved.items() if v is not None})

    # Analyze changes
    new_sections = []
    for key in latest_template:
        if key not in user_config:
            new_sections.append(key)

    if dry_run:
        console.print(
            Panel.fit(
                f"[bold yellow]{_('Preview mode')}[/bold yellow] - {_('No files will be modified')}",
                title=_("Dry Run"),
            )
        )
        console.print()

        if new_sections:
            console.print(
                f"[bold]{EMOJI['package']} {_('New config sections to be added:')}[/bold]"
            )
            for section in new_sections:
                console.print(f"  [green]+ {section}[/green]")
        else:
            console.print(f"[dim]{_('No new config sections')}[/dim]")

        console.print()
        console.print(f"[bold]{EMOJI_MAP['lock']} {_('User config to be preserved:')}[/bold]")
        console.print(
            f"  {BULLET} project.name: {user_preserved['project'].get('name', _('(not set)'))}"
        )
        console.print(
            f"  {BULLET} project.domain: {user_preserved['project'].get('domain', _('(not set)'))}"
        )
        if user_preserved.get("roles"):
            console.print(f"  {BULLET} roles: {len(user_preserved['roles'])} {_('role(s)')}")
        if user_preserved.get("confirmed_decisions"):
            console.print(
                f"  {BULLET} confirmed_decisions: {len(user_preserved['confirmed_decisions'])} {_('decision(s)')}"
            )

        console.print()
        console.print(f"[dim]{_('Remove --dry-run to perform the actual upgrade')}[/dim]")
        return

    # Backup original config
    backup_path = None
    if not force:
        backup_path = config_path.with_suffix(".yaml.bak")
        try:
            config_path.rename(backup_path)
            console.print(f"[dim]{_('Original config backed up to:')} {backup_path}[/dim]")
        except OSError as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Backup failed:')} {e}")
            raise SystemExit(1)

    # Write merged config
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(merged, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except OSError as e:
        console.print(f"[red]{_('Error:')}[/red] {_('Failed to write config:')} {e}")
        if backup_path and backup_path.exists():
            backup_path.rename(config_path)
            console.print(f"[yellow]{_('Original config restored from backup')}[/yellow]")
        raise SystemExit(1)

    # Regenerate collaboration rules document and integrate llms.txt
    contributing_ai_path = config_path.parent / "CONTRIBUTING_AI.md"
    generator = LLMContextGenerator(merged, config_path.parent)
    contributing_ai_path.write_text(generator.generate(), encoding="utf-8")

    # Integrate llms.txt
    project_name = merged.get("project", {}).get("name", "Project")
    project_desc = merged.get("project", {}).get("description", "AI-assisted development project")
    LLMsTxtManager.ensure_integration(
        config_path.parent, project_name, project_desc, contributing_ai_path
    )

    # Check and initialize role-based directory structure
    role_based_config = merged.get("role_context", {})
    if role_based_config.get("enabled", False):
        from datetime import datetime

        from ..domain.role import ContextAggregator, RoleManager

        dm = RoleManager(config_path.parent, merged)
        roles_dir = config_path.parent / "docs" / "roles"

        # Check if initialization is needed
        initialized = False

        # Initialize each role's context
        roles = role_based_config.get("roles", [])
        for dev in roles:
            dev_id = dev.get("id")
            if not dev_id:
                continue

            dev_dir = roles_dir / dev_id
            if not dev_dir.exists():
                dm.init_role_context(dev_id)
                console.print(
                    f"  [green]{EMOJI_MAP['sparkles']} {_('Initialized role directory:')} docs/roles/{dev_id}/[/green]"
                )
                initialized = True

        # Create COLLABORATION.md
        collab_config = role_based_config.get("collaboration", {})
        collab_file = config_path.parent / collab_config.get("file", "docs/roles/COLLABORATION.md")

        if not collab_file.exists():
            collab_file.parent.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")

            collab_content = f"""# {project_name} Role Collaboration Log

## Current Collaboration

(No collaboration records yet)

## Task Assignment Matrix

| Task | Owner | Collaborator | Status | Dependencies |
|------|-------|--------------|--------|--------------|
| (Unassigned) | - | - | - | - |

## Milestone Tracking

(No milestones yet)

## Collaboration Rules

1. **Documentation**: Update your own CONTEXT.md after each task completion
2. **Conflict Avoidance**: Check if other roles are editing shared documents before modifying
3. **Handoff Process**: Record handoff details in this document during task handoffs

## Handoff Records

(No handoff records yet)

---
*Last updated: {today}*
"""
            collab_file.write_text(collab_content, encoding="utf-8")
            console.print(
                f"  [green]{EMOJI_MAP['sparkles']} {_('Created collaboration document:')} {collab_config.get('file', 'docs/roles/COLLABORATION.md')}[/green]"
            )
            initialized = True

        # Generate global aggregated CONTEXT.md
        aggregator = ContextAggregator(config_path.parent, merged)
        global_context = config_path.parent / "docs" / "CONTEXT.md"
        if not global_context.exists() or initialized:
            aggregator.generate_and_save()
            console.print(
                f"  [green]{EMOJI_MAP['sparkles']} {_('Generated global context aggregation:')} docs/CONTEXT.md[/green]"
            )

    # Success message
    console.print()
    console.print(
        Panel.fit(
            f"[bold green]{EMOJI_MAP['success']} {_('Protocol upgraded to v{version}').format(version=__version__)}[/bold green]",
            title=_("Upgrade Complete"),
        )
    )

    if new_sections:
        console.print()
        console.print(f"[bold]{EMOJI['package']} {_('New config sections:')}[/bold]")
        for section in new_sections:
            console.print(f"  [green]+ {section}[/green]")

    console.print()
    console.print(f"[bold]{_('Updated files:')}[/bold]")
    console.print(f"  {BULLET} {config_path}")
    console.print(f"  {BULLET} {contributing_ai_path}")

    console.print()
    console.print(f"[dim]{_('Hint: Use git diff to review specific changes')}[/dim]")


@main.command()
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--strict", is_flag=True, help=_("Strict mode: treat warnings as failures"))
@click.option(
    "--insights/--no-insights", default=True, help=_("Run Insight consistency check (default: on)")
)
@click.option(
    "--guards/--no-guards", default=True, help=_("Run Guard protection check (default: on)")
)
def check(config: str, strict: bool, insights: bool, guards: bool):
    """Check protocol compliance

    Check whether the project follows the collaboration protocol defined in CONTRIBUTING_AI.md.
    Insight consistency check is enabled by default (use --no-insights to skip).
    Guard protection check is enabled by default (use --no-guards to skip).

    Examples:

        vibecollab check                    # Check with Insight + Guards (default)

        vibecollab check -c project.yaml    # Specify config file

        vibecollab check --strict           # Strict mode

        vibecollab check --no-insights      # Skip Insight consistency check

        vibecollab check --no-guards        # Skip Guard protection check

        vibecollab check --guards --no-insights  # Guards only, no Insights
    """
    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        console.print(
            f"[dim]{_('Hint: Run in the project directory, or use -c to specify the config file path')}[/dim]"
        )
        raise SystemExit(1)

    # Load config
    project_config = _safe_load_yaml(config_path)

    # Run checks
    checker = ProtocolChecker(project_root, project_config)
    results = checker.check_all()
    summary = checker.get_summary(results)

    # Schema validation
    schema_errors_list = []
    schema_warnings_list = []
    try:
        from ..core.pipeline import Pipeline

        pipeline = Pipeline(project_root, config_path=config)
        schema_report = pipeline.validate_config()
        schema_errors_list = schema_report.errors
        schema_warnings_list = schema_report.warnings
    except Exception:
        pass

    # Display results
    console.print()
    console.print(
        Panel.fit(f"[bold]{_('Protocol Compliance Check')}[/bold]", title=_("Protocol Check"))
    )
    console.print()

    # Group by severity
    errors = [r for r in results if r.severity == "error"]
    warnings = [r for r in results if r.severity == "warning"]
    infos = [r for r in results if r.severity == "info"]

    if errors:
        console.print(f"[bold red]{EMOJI_MAP['error']} {_('Errors:')}[/bold red]")
        for result in errors:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]{_('Suggestion:')} {result.suggestion}[/dim]")
        console.print()

    if warnings:
        console.print(f"[bold yellow]{EMOJI_MAP['warning']} {_('Warnings:')}[/bold yellow]")
        for result in warnings:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]{_('Suggestion:')} {result.suggestion}[/dim]")
        console.print()

    if infos:
        console.print(f"[bold blue]{EMOJI_MAP['info']} {_('Info:')}[/bold blue]")
        for result in infos:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]{_('Suggestion:')} {result.suggestion}[/dim]")
        console.print()

    # Schema validation results
    if schema_errors_list or schema_warnings_list:
        console.print(Panel.fit(f"[bold]{_('Schema Validation')}[/bold]", title=_("Schema Check")))
        console.print()
        if schema_errors_list:
            console.print(f"[bold red]{EMOJI_MAP['error']} {_('Schema Errors:')}[/bold red]")
            for err in schema_errors_list:
                console.print(f"  {BULLET} {err}")
            console.print()
        if schema_warnings_list:
            console.print(
                f"[bold yellow]{EMOJI_MAP['warning']} {_('Schema Warnings:')}[/bold yellow]"
            )
            for warn in schema_warnings_list:
                console.print(f"  {BULLET} {warn}")
            console.print()

    # Insight consistency check
    insight_errors = 0
    insight_warnings = 0
    if insights:
        console.print(
            Panel.fit(
                f"[bold]{_('Insight System Consistency Check')}[/bold]",
                title=_("Insight Consistency Check"),
            )
        )
        console.print()
        try:
            from ..domain.event_log import EventLog
            from ..insight.manager import InsightManager

            event_log = EventLog(project_root / ".vibecollab" / "events.jsonl")
            mgr = InsightManager(project_root=project_root, event_log=event_log)
            report = mgr.check_consistency()

            if report.errors:
                insight_errors = len(report.errors)
                console.print(f"[bold red]{EMOJI_MAP['error']} {_('Insight Errors:')}[/bold red]")
                for err in report.errors:
                    console.print(f"  {BULLET} {err}")
                console.print()
            if report.warnings:
                insight_warnings = len(report.warnings)
                console.print(
                    f"[bold yellow]{EMOJI_MAP['warning']} {_('Insight Warnings:')}[/bold yellow]"
                )
                for warn in report.warnings:
                    console.print(f"  {BULLET} {warn}")
                console.print()
            if report.ok and not report.warnings:
                console.print(
                    f"  [green]{EMOJI_MAP['success']} {_('Insight consistency check passed')}[/green]"
                )
                console.print()
        except Exception as e:
            console.print(
                f"  [yellow]{EMOJI_MAP['warning']} {_('Insight check skipped:')} {e}[/yellow]"
            )
            console.print()

    # Guard protection check
    guard_blocks = 0
    guard_warnings = 0
    if guards:
        console.print(
            Panel.fit(
                f"[bold]{_('Guard Protection Check')}[/bold]",
                title=_("Guard Check"),
            )
        )
        console.print()
        try:
            from ..domain.guard import GuardEngine, GuardSeverity

            guard_config = project_config.get("guards", None)
            engine = GuardEngine(guard_config)

            if not engine.enabled:
                console.print(
                    f"  [dim]{EMOJI_MAP['info']} {_('Guards disabled in project config')}[/dim]"
                )
                console.print()
            else:
                # Scan project files for guard rule violations
                import subprocess

                try:
                    result = subprocess.run(
                        ["git", "ls-files"],
                        cwd=str(project_root),
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    tracked_files = [
                        f.strip() for f in result.stdout.splitlines() if f.strip()
                    ]
                except Exception:
                    # Fallback: scan common directories
                    tracked_files = []
                    for ext in ["*.py", "*.yaml", "*.yml", "*.md", "*.json", "*.meta"]:
                        tracked_files.extend(
                            str(p.relative_to(project_root))
                            for p in project_root.rglob(ext)
                            if ".git" not in str(p) and ".vibecollab" not in str(p)
                        )

                # Check each file against guard rules
                guard_violations = []
                for file_path in tracked_files:
                    matching_rules = engine.test_path(file_path)
                    for rule in matching_rules:
                        guard_violations.append((file_path, rule))

                blocks = [
                    (fp, r) for fp, r in guard_violations if r.severity == GuardSeverity.BLOCK
                ]
                warns = [
                    (fp, r) for fp, r in guard_violations if r.severity == GuardSeverity.WARN
                ]

                if blocks:
                    guard_blocks = len(blocks)
                    console.print(
                        f"[bold red]{EMOJI_MAP['error']} {_('Guard Violations (BLOCK):')}[/bold red]"
                    )
                    for fp, rule in blocks:
                        console.print(f"  {BULLET} {fp}")
                        console.print(
                            f"    [dim]{_('Rule:')} {rule.name} — {rule.message}[/dim]"
                        )
                    console.print()

                if warns:
                    guard_warnings = len(warns)
                    console.print(
                        f"[bold yellow]{EMOJI_MAP['warning']} {_('Guard Warnings (WARN):')}[/bold yellow]"
                    )
                    for fp, rule in warns:
                        console.print(f"  {BULLET} {fp}")
                        console.print(
                            f"    [dim]{_('Rule:')} {rule.name} — {rule.message}[/dim]"
                        )
                    console.print()

                if not blocks and not warns:
                    console.print(
                        f"  [green]{EMOJI_MAP['success']} {_('Guard check passed')} "
                        f"({len(engine.list_rules())} {_('rules')}, "
                        f"{len(tracked_files)} {_('files scanned')})[/green]"
                    )
                    console.print()
                else:
                    console.print(
                        f"  [dim]{_('Scanned')} {len(tracked_files)} {_('files against')} "
                        f"{len(engine.list_rules())} {_('guard rules')}[/dim]"
                    )
                    console.print()
        except Exception as e:
            console.print(
                f"  [yellow]{EMOJI_MAP['warning']} {_('Guard check skipped:')} {e}[/yellow]"
            )
            console.print()

    # Merge statistics
    total_errors = len(errors) + insight_errors + len(schema_errors_list) + guard_blocks
    total_warnings = len(warnings) + insight_warnings + len(schema_warnings_list) + guard_warnings
    total_checks = (
        summary["total"]
        + (1 if insights else 0)
        + (1 if guards else 0)
        + (1 if schema_errors_list or schema_warnings_list else 0)
    )

    # Display summary
    if total_errors == 0 and not (strict and total_warnings > 0):
        console.print(
            Panel.fit(
                f"[bold green]{EMOJI_MAP['success']} {_('All checks passed')}[/bold green]\n\n"
                f"{_('Total:')} {total_checks} {_('check(s)')}",
                title=_("Check Complete"),
            )
        )
    else:
        status = (
            _("Failed")
            if total_errors > 0 or (strict and total_warnings > 0)
            else _("Has Warnings")
        )
        color = "red" if total_errors > 0 or (strict and total_warnings > 0) else "yellow"
        emoji = (
            EMOJI_MAP["error"]
            if total_errors > 0 or (strict and total_warnings > 0)
            else EMOJI_MAP["warning"]
        )
        console.print(
            Panel.fit(
                f"[bold {color}]{emoji} {_('Check')} {status}[/bold {color}]\n\n"
                f"{_('Total:')} {total_checks} {_('check(s)')}\n"
                f"{_('Errors:')} {total_errors}\n"
                f"{_('Warnings:')} {total_warnings}",
                title=_("Check Complete"),
            )
        )
        if strict and total_warnings > 0:
            console.print()
            console.print(
                f"[dim]{_('Hint: In --strict mode, warnings are treated as failures')}[/dim]"
            )

    # Return exit code
    if total_errors > 0 or (strict and total_warnings > 0):
        raise SystemExit(1)


@main.command()
@click.option("-c", "--config", default="project.yaml", help=_("Config file path"))
@click.option("--json", "as_json", is_flag=True, help=_("Output in JSON format"))
def health(config: str, as_json: bool):
    """Project health signal check"""
    import json as json_mod

    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[red]{_('Config file not found:')} {config}[/red]")
        raise SystemExit(1)

    cfg = _safe_load_yaml(config_path)

    from ..core.health import HealthExtractor

    ext = HealthExtractor(config_path.parent, cfg)
    report = ext.extract()

    if as_json:
        click.echo(json_mod.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    grade = report.summary.get("grade", "?")
    score = report.score
    grade_color = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}.get(
        grade, "white"
    )

    console.print(
        Panel(
            f"[bold {grade_color}]{_('Grade:')} {grade} ({score:.0f}/100)[/bold {grade_color}]\n"
            f"CRITICAL: {report.critical_count}  WARNING: {report.warning_count}  INFO: {report.info_count}",
            title=_("Project Health"),
        )
    )

    level_style = {"critical": "red bold", "warning": "yellow", "info": "dim"}
    for signal in report.signals:
        style = level_style.get(signal.level.value, "")
        prefix = {"critical": "X", "warning": "!", "info": "-"}.get(signal.level.value, " ")
        console.print(f"  [{style}][{prefix}] {signal.message}[/{style}]")
        if signal.suggestion:
            console.print(f"      [dim]{BULLET} {signal.suggestion}[/dim]")

    if report.critical_count > 0:
        raise SystemExit(1)


# Import lifecycle management commands
from .lifecycle import lifecycle as lifecycle_group  # noqa: E402

main.add_command(lifecycle_group)


# Import Insight system commands
from .insight import insight as insight_group  # noqa: E402

main.add_command(insight_group)

# Import AI guidance commands (onboard + next + prompt)
from .guide import next_step, onboard, prompt_cmd  # noqa: E402

main.add_command(onboard)
main.add_command(next_step, name="next")
main.add_command(prompt_cmd, name="prompt")

# Import Task management commands (with Insight auto-linking, v0.7.1+)
from .task import task_group  # noqa: E402

main.add_command(task_group)

# Import config management commands (v0.8.0+)
from .config import config_group  # noqa: E402

main.add_command(config_group)

# Import semantic search commands (v0.9.0+)
from .index import index_cmd, search_cmd  # noqa: E402

main.add_command(index_cmd, name="index")
main.add_command(search_cmd, name="search")

# Import MCP Server commands (v0.9.1+)
from .mcp import mcp_group  # noqa: E402

main.add_command(mcp_group)

# Import Roadmap / Task integration commands (v0.10.0+)
from .roadmap import roadmap_group  # noqa: E402

main.add_command(roadmap_group)

# Import Skill management commands (v0.10.11+)
from .skill import skill_group  # noqa: E402

main.add_command(skill_group)


# ============================================
# Execution Plan commands (v0.10.4+)
# ============================================


@main.group("plan")
def plan_group():
    """Execution Plan: YAML-driven workflow automation

    Run multi-step automation plans for testing and protocol workflows.
    """
    pass


@plan_group.command("run")
@click.argument("plan_file", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help=_("Preview plan without executing"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
@click.option("--timeout", default=120, help=_("Step timeout in seconds"))
@click.option(
    "--host",
    default=None,
    help=_("Host adapter: file_exchange, subprocess:cmd, auto:cursor, auto:cline"),
)
@click.option("--verbose", "-v", is_flag=True, help=_("Verbose step-by-step logging"))
def plan_run(plan_file, dry_run, json_output, timeout, host, verbose):
    """Execute a YAML automation plan

    The unified execution engine for all VibeCollab automation workflows,
    including file-exchange based loops and keyboard-simulation based
    autonomous IDE driving.

    Examples:

        vibecollab plan run my_plan.yaml

        vibecollab plan run my_plan.yaml --dry-run

        vibecollab plan run my_plan.yaml --json

        vibecollab plan run my_plan.yaml --host file_exchange

        vibecollab plan run plans/dev-loop.yaml --host auto:cursor -v
    """
    import json as json_mod
    import os as _os
    import signal as _signal

    from ..core.execution_plan import PlanRunner, load_plan, resolve_host_adapter

    try:
        plan = load_plan(Path(plan_file))
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]{EMOJI_MAP['error']} {e}[/red]")
        raise SystemExit(1)

    # Optional EventLog integration
    event_log = None
    vibecollab_dir = Path(".vibecollab")
    if vibecollab_dir.exists():
        try:
            from ..domain.event_log import EventLog

            event_log = EventLog(Path("."))
        except Exception:
            pass

    # Resolve host adapter from CLI override or plan config
    host_adapter = None
    if host:
        # CLI override: "file_exchange", "subprocess:command", "auto:cursor", etc.
        if host.startswith("subprocess:"):
            from ..core.execution_plan import SubprocessAdapter

            host_adapter = SubprocessAdapter(
                command=host[len("subprocess:") :],
                cwd=Path(".").resolve(),
            )
        else:
            override_plan = {**plan, "host": host}
            host_adapter = resolve_host_adapter(
                override_plan,
                Path(".").resolve(),
                verbose=verbose,
            )

    # If using auto adapter, set up process state tracking and signal handlers
    auto_state = None
    is_auto = host and (host == "auto" or host.startswith("auto:"))

    if is_auto:
        try:
            from ..contrib.auto_driver import AutoDriverState, save_state

            ide_name = "cursor"
            if ":" in host:
                ide_name = host.split(":", 1)[1]

            # Extract max_rounds from plan
            max_rounds = 50
            for step in plan.get("steps", []):
                if step.get("action") == "loop":
                    max_rounds = step.get("max_rounds", max_rounds)
                    break

            auto_state = AutoDriverState(
                plan_path=str(plan_file),
                ide=ide_name,
                pid=_os.getpid(),
                started_at=datetime.now(timezone.utc).isoformat(),
                host_type=f"auto:{ide_name}",
                max_rounds=max_rounds,
            )
            save_state(auto_state)

            # Set up signal handler for graceful shutdown
            def _shutdown_handler(signum, frame):
                if auto_state:
                    auto_state.status = "stopped"
                    save_state(auto_state)
                raise SystemExit(0)

            _signal.signal(_signal.SIGINT, _shutdown_handler)
            _signal.signal(_signal.SIGTERM, _shutdown_handler)

            console.print("[bold]Starting Auto Driver[/bold]")
            console.print(f"  Plan: {plan_file}")
            console.print(f"  IDE: {ide_name}")
            console.print(f"  Host: auto:{ide_name}")
            console.print(f"  PID: {_os.getpid()}")
            console.print()
        except ImportError:
            pass  # auto_driver state tracking is optional

    runner = PlanRunner(
        project_root=Path(".").resolve(),
        timeout=timeout,
        event_log=event_log,
        dry_run=dry_run,
        host=host_adapter,
        verbose=verbose,
    )
    result = runner.run(plan)

    # Update auto state if tracking
    if auto_state:
        try:
            from ..contrib.auto_driver import save_state as _save

            auto_state.status = "completed" if result.success else "failed"
            if not result.success and result.abort_reason:
                auto_state.error = result.abort_reason
            _save(auto_state)
        except Exception:
            pass

    if json_output:
        click.echo(json_mod.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        # Rich output
        status_emoji = EMOJI_MAP["success"] if result.success else EMOJI_MAP["error"]
        status_color = "green" if result.success else "red"

        console.print()
        console.print(
            Panel.fit(
                f"[bold]{result.name}[/bold]\n\n"
                f"Status: [{status_color}]{status_emoji} {'PASSED' if result.success else 'FAILED'}[/{status_color}]\n"
                f"Steps: {result.passed}/{result.total_steps} passed, "
                f"{result.failed} failed, {result.skipped} skipped\n"
                f"Duration: {result.duration_ms}ms",
                title="Plan Result",
            )
        )

        if result.failed > 0 or result.aborted:
            console.print()
            for sr in result.steps:
                if not sr.success and not sr.skipped:
                    console.print(
                        f"  [red]{EMOJI_MAP['error']}[/red] Step {sr.step_index}: "
                        f"{sr.action} — {sr.error}"
                    )
            if result.abort_reason:
                console.print(f"\n  [red]Aborted: {result.abort_reason}[/red]")

        console.print()

    if not result.success:
        raise SystemExit(1)


@plan_group.command("validate")
@click.argument("plan_file", type=click.Path(exists=True))
def plan_validate(plan_file):
    """Validate a YAML plan file without executing

    Examples:

        vibecollab plan validate my_plan.yaml
    """
    from ..core.execution_plan import load_plan

    try:
        plan = load_plan(Path(plan_file))
        steps = len(plan.get("steps", []))
        console.print(
            f"[green]{EMOJI_MAP['success']} Plan '{plan.get('name', '?')}' "
            f"is valid ({steps} steps)[/green]"
        )
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]{EMOJI_MAP['error']} {e}[/red]")
        raise SystemExit(1)


# ============================================
# Auto Driver commands (v0.10.7+ — thin wrappers over plan run)
# ============================================


@main.group("auto")
def auto_group():
    """Autonomous IDE automation

    Drive your IDE AI through long-running automation workflows
    using keyboard simulation. Under the hood, 'auto start' delegates
    to 'plan run --host auto:<ide>' — the unified execution engine.

    Examples:

        vibecollab auto start plans/dev.yaml --ide cursor
        vibecollab auto status
        vibecollab auto stop
        vibecollab auto init --preset dev-loop
        vibecollab auto list
    """
    pass


@auto_group.command("start")
@click.argument("plan_file", type=click.Path(exists=True))
@click.option("--ide", default="cursor", help=_("IDE to drive (cursor, cline, codebuddy)"))
@click.option("--timeout", default=600, type=int, help=_("Response timeout in seconds"))
@click.option("--verbose", "-v", is_flag=True, help=_("Verbose output"))
def auto_start(plan_file, ide, timeout, verbose):
    """Start autonomous IDE automation

    Thin wrapper over 'plan run --host auto:<ide>'. Launches the unified
    execution engine with keyboard simulation as the host adapter.

    Examples:

        vibecollab auto start plans/dev.yaml
        vibecollab auto start plans/dev.yaml --ide cursor -v
    """
    # Delegate to plan run with auto host

    host_str = f"auto:{ide}"

    console.print(f"[dim]Delegating to: vibecollab plan run {plan_file} --host {host_str}[/dim]")
    console.print()

    # Invoke plan_run directly
    ctx = click.get_current_context()
    ctx.invoke(
        plan_run,
        plan_file=plan_file,
        dry_run=False,
        json_output=False,
        timeout=timeout,
        host=host_str,
        verbose=verbose,
    )


@auto_group.command("status")
def auto_status():
    """Show auto driver status

    Examples:

        vibecollab auto status
    """
    try:
        from ..contrib.auto_driver import get_status
    except ImportError:
        console.print("[red]Auto driver not available[/red]")
        raise SystemExit(1)

    status = get_status()
    if status is None:
        console.print("No auto driver running or no state file found")
        return

    console.print("[bold]Auto Driver Status[/bold]")
    console.print(f"  Plan: {status.get('plan_path')}")
    console.print(f"  IDE: {status.get('ide')}")
    console.print(f"  Host: {status.get('host_type', 'auto')}")
    console.print(f"  PID: {status.get('pid')}")
    console.print(f"  Status: {status.get('status')}")
    console.print(f"  Round: {status.get('current_round')}/{status.get('max_rounds')}")
    console.print(f"  Started: {status.get('started_at')}")
    if status.get("error"):
        console.print(f"  Error: [red]{status.get('error')}[/red]")


@auto_group.command("stop")
def auto_stop():
    """Stop running auto driver

    Sends a termination signal to the running auto driver process.

    Examples:

        vibecollab auto stop
    """
    try:
        from ..contrib.auto_driver import stop_driver
    except ImportError:
        console.print("[red]Auto driver not available[/red]")
        raise SystemExit(1)

    if stop_driver():
        console.print(f"[green]{EMOJI_MAP['success']} Stop signal sent[/green]")
    else:
        console.print("[yellow]No auto driver running or cannot stop[/yellow]")


@auto_group.command("init")
@click.argument("plan_file", type=click.Path(exists=False))  # Allow non-existing for presets
@click.option("--ide", default="cursor", help=_("IDE to drive (cursor, cline, codebuddy)"))
@click.option("--output", "-o", default=None, help=_("Output path for .bat file"))
@click.option(
    "--preset", "-p", is_flag=True, help=_("Treat plan_file as preset name (e.g., dev-loop)")
)
def auto_init(plan_file, ide, output, preset):
    """Create a .bat launcher script for autonomous automation

    Generates a .bat file that users can double-click to start the
    auto driver without needing to use the command line.

    The generated .bat uses 'vibecollab plan run --host auto:<ide>'
    as the unified execution entry point.

    Examples:

        vibecollab auto init plans/dev.yaml
        vibecollab auto init --preset dev-loop
        vibecollab auto init plans/dev.yaml -o start_auto.bat
    """
    import importlib.resources

    project_root = Path.cwd()

    # Handle preset plans
    if preset or not Path(plan_file).exists():
        # Try to copy from package
        preset_name = plan_file.replace(".yaml", "") + ".yaml"
        if not preset_name.endswith(".yaml"):
            preset_name += ".yaml"

        try:
            if hasattr(importlib.resources, "files"):
                plans_path = importlib.resources.files("vibecollab") / "plans"
                source_plan = plans_path / preset_name
                if source_plan.is_file():
                    # Copy to local plans directory
                    local_plans = project_root / "plans"
                    local_plans.mkdir(exist_ok=True)
                    dest_plan = local_plans / preset_name

                    dest_plan.write_text(source_plan.read_text(encoding="utf-8"), encoding="utf-8")
                    console.print(
                        f"[green]{EMOJI_MAP['success']} Copied preset plan to: {dest_plan}[/green]"
                    )
                    plan_file = str(dest_plan)
                else:
                    console.print(
                        f"[red]{EMOJI_MAP['error']} Preset plan not found: {preset_name}[/red]"
                    )
                    console.print("[dim]Run 'vibecollab auto list' to see available presets[/dim]")
                    raise SystemExit(1)
        except Exception as e:
            if "not found" not in str(e).lower():
                console.print(f"[yellow]Warning: Could not copy preset: {e}[/yellow]")
            if not Path(plan_file).exists():
                console.print(f"[red]{EMOJI_MAP['error']} Plan file not found: {plan_file}[/red]")
                raise SystemExit(1)

    plan_path = Path(plan_file).resolve()

    # Default output name
    if output is None:
        plan_name = plan_path.stem
        output = f"auto_{plan_name}.bat"

    output_path = project_root / output

    # Generate .bat content using the refactored generator
    try:
        from ..contrib.auto_driver import generate_bat_content

        bat_content = generate_bat_content(plan_file, ide, project_root)
    except ImportError:
        # Fallback if auto_driver can't be imported (shouldn't happen)
        bat_content = f'''@echo off
REM VibeCollab Auto Driver Launcher
cd /d "{project_root}"
vibecollab plan run "{plan_file}" --host auto:{ide} -v
pause
'''

    # Write .bat file
    output_path.write_text(bat_content, encoding="utf-8")

    console.print(f"[green]{EMOJI_MAP['success']} Created: {output_path}[/green]")
    console.print()
    console.print("[bold]Usage:[/bold]")
    console.print(f"  1. Double-click [cyan]{output}[/cyan] to start automation")
    console.print(f"  2. Keep {ide.capitalize()} window visible")
    console.print(f"  3. The script will send instructions to {ide.capitalize()} automatically")
    console.print("  4. Close the cmd window or run 'vibecollab auto stop' to stop")
    console.print()
    console.print(f"[dim]Execution: vibecollab plan run {plan_file} --host auto:{ide} -v[/dim]")
    console.print("[dim]Note: Make sure the IDE is running before starting.[/dim]")


@auto_group.command("list")
def auto_list():
    """List available preset automation plans

    Shows the built-in plans that come with VibeCollab.

    Examples:

        vibecollab auto list
    """
    import importlib.resources

    console.print()
    console.print(f"[bold cyan]{EMOJI_MAP['info']} Preset Automation Plans[/bold cyan]")
    console.print()

    # Try to find plans in package
    try:
        if hasattr(importlib.resources, "files"):
            # Python 3.9+
            plans_path = importlib.resources.files("vibecollab") / "plans"
            if plans_path.is_dir():
                plans = []
                for item in plans_path.iterdir():
                    if item.name.endswith(".yaml") and not item.name.startswith("self-test"):
                        # Read plan to get description
                        content = item.read_text(encoding="utf-8")
                        plan_data = yaml.safe_load(content)
                        name = plan_data.get("name", item.name)
                        host = plan_data.get("host", "file_exchange")
                        steps = plan_data.get("steps", [])
                        max_rounds = 0
                        for step in steps:
                            if step.get("action") == "loop":
                                max_rounds = step.get("max_rounds", 0)
                                break
                        plans.append(
                            {"file": item.name, "name": name, "host": host, "rounds": max_rounds}
                        )

                if plans:
                    table_data = [
                        ("Plan File", "Description", "Host", "Rounds"),
                        *[
                            (f"[cyan]{p['file']}[/cyan]", p["name"], p["host"], str(p["rounds"]))
                            for p in sorted(plans, key=lambda x: x["file"])
                        ],
                    ]

                    for i, row in enumerate(table_data):
                        if i == 0:
                            console.print(f"  {'─' * 85}")
                            console.print(f"  {row[0]:<28} {row[1]:<32} {row[2]:<15} {row[3]}")
                            console.print(f"  {'─' * 85}")
                        else:
                            console.print(f"  {row[0]:<28} {row[1]:<32} {row[2]:<15} {row[3]}")

                    console.print()
                    console.print("[bold]Usage:[/bold]")
                    console.print("  # Create .bat launcher from preset")
                    console.print("  vibecollab auto init --preset dev-loop")
                    console.print()
                    console.print("  # Or run directly")
                    console.print("  vibecollab plan run plans/dev-loop.yaml --host auto:cursor -v")
                    return
    except Exception as e:
        console.print(f"[yellow]Could not read bundled plans: {e}[/yellow]")

    # Fallback: show expected plans
    console.print("[dim]Bundled plans not found. Available plan templates:[/dim]")
    console.print()
    preset_info = [
        ("dev-loop.yaml", "Full development cycle", "file_exchange", "50"),
        ("feature-dev.yaml", "Feature implementation from ROADMAP", "file_exchange", "30"),
        ("quick-fix.yaml", "Rapid check-fix-commit loop", "file_exchange", "10"),
        ("doc-sync.yaml", "Documentation synchronization", "file_exchange", "5"),
        ("insight-harvest.yaml", "Knowledge capture & insights", "file_exchange", "10"),
    ]
    for fname, desc, host, rounds in preset_info:
        console.print(f"  [cyan]{fname:<24}[/cyan] {desc:<40} {host:<15} {rounds} rounds")
    console.print()
    console.print("[dim]Copy these from the VibeCollab repository: src/vibecollab/plans/[/dim]")


# ============================================
# Role-based context management commands
# =======================================


@main.group()
def role():
    """Role-based context management commands

    Manage projects with role-based collaboration.
    Each role (dev, insight_collector, architect) has its own context and configuration.
    """
    pass


@role.command("whoami")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def role_whoami(config: str):
    """Show current role identity

    Examples:

        vibecollab role whoami
    """
    from ..domain.role import RoleManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    dm = RoleManager(project_root, project_config)
    current_dev = dm.get_current_role()
    identity_source = dm.get_identity_source()

    role_based_enabled = project_config.get("role_context", {}).get("enabled", False)

    # Friendly display for identity source
    source_display = {
        "local_switch": f"[green]{_('CLI switch')}[/green] (.vibecollab.local.yaml)",
        "env_var": f"[yellow]{_('Environment variable')}[/yellow] (VIBECOLLAB_DEVELOPER)",
        "git_username": _("Git username (git config user.name)"),
        "system_user": _("System username"),
    }.get(identity_source, identity_source)

    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]{current_dev}[/bold cyan]\n\n"
            f"{_('Role-based mode:')} {'[green]' + _('Enabled') + '[/green]' if role_based_enabled else '[yellow]' + _('Not enabled') + '[/yellow]'}\n"
            f"{_('Identity source:')} {source_display}",
            title=_("Current Role"),
        )
    )
    console.print()


@role.command("list")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def role_list(config: str):
    """List all roles

    Examples:

        vibecollab role list
    """
    from ..domain.role import RoleManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    dm = RoleManager(project_root, project_config)
    roles = dm.list_roles()
    current_dev = dm.get_current_role()

    # In single-role mode, show current role only
    role_based_enabled = project_config.get("role_context", {}).get("enabled", False)
    if not role_based_enabled:
        if not roles:
            # Show current role from identity detection
            console.print()
            console.print(f"[cyan]{current_dev}[/cyan] {_('(Single-role mode)')}")
            console.print()
            return

    if not roles:
        console.print()
        console.print(f"[yellow]{_('No roles yet')}[/yellow]")
        hint = _("Use 'vibecollab init --role-based' to initialize a role-based project")
        console.print(f"[dim]{hint}[/dim]")
        console.print()
        return

    table = Table(title=_("Role List"), show_header=True)
    table.add_column(_("Role"), style="cyan")
    table.add_column(_("Status"))
    table.add_column(_("Last Updated"))
    table.add_column(_("Update Count"))

    for dev in roles:
        status_info = dm.get_role_status(dev)
        is_current = f" ({_('current')})" if dev == current_dev else ""
        status = (
            f"{EMOJI_MAP['success']} {_('Active')}{is_current}"
            if status_info["exists"]
            else f"{EMOJI_MAP['warning']} {_('Not initialized')}"
        )
        last_updated = status_info.get("last_updated", "-") or "-"
        if last_updated != "-" and len(last_updated) > 19:
            last_updated = last_updated[:19]
        total_updates = str(status_info.get("total_updates", 0))

        table.add_row(dev, status, last_updated, total_updates)

    console.print()
    console.print(table)
    console.print()


@role.command("status")
@click.argument("role", required=False)
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def role_status(role: Optional[str], config: str):
    """View role status

    Examples:

        vibecollab dev status           # View all roles

        vibecollab dev status dev       # View a specific role
    """
    from ..domain.role import RoleManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    dm = RoleManager(project_root, project_config)
    current_dev = dm.get_current_role()

    # Handle single-role mode
    role_based_enabled = project_config.get("role_context", {}).get("enabled", False)
    if not role_based_enabled:
        if role and role != current_dev:
            console.print(
                f"[yellow]{_('Single-role mode: only {dev} is available').format(dev=current_dev)}[/yellow]"
            )
            return
        # Show current role status
        roles = [current_dev]
    elif role:
        roles = [role]
    else:
        roles = dm.list_roles()

    if not roles:
        console.print()
        console.print(f"[yellow]{_('No roles yet')}[/yellow]")
        console.print()
        return

    for dev in roles:
        context_file = dm.get_role_context_file(dev)
        if context_file.exists():
            console.print()
            console.print(Panel.fit(f"[bold]{dev}[/bold]", title=_("Role Status")))
            console.print()

            try:
                content = context_file.read_text(encoding="utf-8")
                lines = content.split("\n")[:20]
                console.print("\n".join(lines))
                if len(content.split("\n")) > 20:
                    console.print(f"\n[dim]... ({_('more at')} {context_file})[/dim]")
            except Exception as e:
                console.print(f"[red]{_('Read failed:')}[/red] {e}")

            console.print()
        else:
            console.print(
                f"[yellow]{EMOJI_MAP['warning']} {_('Role {name} not initialized').format(name=dev)}[/yellow]"
            )


@role.command("sync")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def role_sync(config: str):
    """Manually trigger global CONTEXT aggregation

    Examples:

        vibecollab dev sync
    """
    from ..domain.role import ContextAggregator

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    role_based_enabled = project_config.get("role_context", {}).get("enabled", False)
    if not role_based_enabled:
        console.print(
            f"[yellow]{EMOJI_MAP['warning']} {_('Role-based mode is not enabled')}[/yellow]"
        )
        raise SystemExit(1)

    console.print()
    console.print(f"[cyan]{_('Aggregating global CONTEXT...')}[/cyan]")

    try:
        aggregator = ContextAggregator(project_root, project_config)
        output_file = aggregator.generate_and_save()

        console.print(
            f"[green]{EMOJI_MAP['success']} {_('Aggregation complete:')}[/green] {output_file}"
        )
        console.print()
    except Exception as e:
        console.print(f"[red]{_('Aggregation failed:')}[/red] {e}")
        raise SystemExit(1)


@role.command("init")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--role", "-d", help=_("Role name (auto-detect if empty)"))
def role_init(config: str, role: Optional[str]):
    """Initialize current role's context

    Examples:

        vibecollab dev init                 # Auto-detect current role

        vibecollab dev init -d dev          # Initialize for dev role
    """
    from ..domain.role import RoleManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    dm = RoleManager(project_root, project_config)

    if role is None:
        role = dm.get_current_role()

    # In single-role mode, just show warning but allow init
    role_based_enabled = project_config.get("role_context", {}).get("enabled", False)
    if not role_based_enabled:
        console.print(f"[dim]{_('Single-role mode: initializing current identity')}[/dim]")

    console.print()
    console.print(f"[cyan]{_('Initializing role:')}[/cyan] {role}")

    try:
        dm.init_role_context(role)
        context_file = dm.get_role_context_file(role)

        console.print(f"[green]{EMOJI_MAP['success']} {_('Initialization complete:')}[/green]")
        console.print(f"  {BULLET} {_('Context file:')} {context_file}")
        console.print()
    except Exception as e:
        console.print(f"[red]{_('Initialization failed:')}[/red] {e}")
        raise SystemExit(1)


@role.command("switch")
@click.argument("role", required=False)
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--clear", is_flag=True, help=_("Clear switch, restore default identity"))
def role_switch(role: Optional[str], config: str, clear: bool):
    """Switch current role identity

    Select a role context via CLI without modifying Git config or environment variables.
    The switch setting is persisted to the local config file (.vibecollab.local.yaml).

    Examples:

        vibecollab dev switch dev        # Switch to dev role

        vibecollab dev switch            # Interactive role selection

        vibecollab dev switch --clear    # Clear switch, restore default identity
    """
    from ..domain.role import RoleManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    dm = RoleManager(project_root, project_config)

    # Handle single-role mode
    role_based_enabled = project_config.get("role_context", {}).get("enabled", False)
    if not role_based_enabled:
        console.print()
        current_dev = dm.get_current_role()
        console.print(f"[yellow]{_('Single-role mode: cannot switch identity')}[/yellow]")
        console.print(f"  {BULLET} {_('Current identity:')} [cyan]{current_dev}[/cyan]")
        console.print(f"  {BULLET} {_('Enable role_context in project.yaml to switch')}")
        console.print()
        return

    # Handle clear switch
    if clear:
        console.print()
        if dm.clear_switch():
            default_dev = dm.get_current_role()
            console.print(f"[green]{EMOJI_MAP['success']} {_('Switch setting cleared')}[/green]")
            console.print(
                f"  {BULLET} {_('Current identity:')} [cyan]{default_dev}[/cyan] ({_('detected via default strategy')})"
            )
        else:
            console.print(f"[red]{_('Clear failed')}[/red]")
            raise SystemExit(1)
        console.print()
        return

    # Get available role list
    roles = dm.list_roles()
    current_dev = dm.get_current_role()

    # If no role specified, interactive selection
    if role is None:
        if not roles:
            console.print()
            console.print(f"[yellow]{_('No roles yet')}[/yellow]")
            hint = _("Use 'vibecollab dev init -d <name>' to initialize a new role")
            console.print(f"[dim]{hint}[/dim]")
            console.print()
            return

        console.print()
        console.print(f"[cyan]{_('Select a role to switch to:')}[/cyan]")
        console.print()

        for i, dev in enumerate(roles, 1):
            status_info = dm.get_role_status(dev)
            is_current = f" [green]({_('current')})[/green]" if dev == current_dev else ""
            last_update = status_info.get("last_updated", _("unknown"))
            console.print(f"  {i}. [bold]{dev}[/bold]{is_current}")
            console.print(f"     {_('Last updated:')} {last_update}")

        console.print()
        console.print(f"  0. [dim]{_('Cancel')}[/dim]")
        console.print()

        # Read user selection
        try:
            choice = click.prompt(_("Enter number"), type=int, default=0)
        except click.Abort:
            console.print(f"\n[dim]{_('Cancelled')}[/dim]")
            return

        if choice == 0:
            console.print(f"[dim]{_('Cancelled')}[/dim]")
            return

        if choice < 1 or choice > len(roles):
            console.print(f"[red]{_('Invalid choice:')} {choice}[/red]")
            raise SystemExit(1)

        role = roles[choice - 1]

    # Normalize role name
    identity_config = project_config.get("role_context", {}).get("identity", {})
    if identity_config.get("normalize", True):
        role = dm._normalize_role_name(role)

    # Check if role exists
    if role not in roles:
        console.print()
        msg = _("Role '{name}' does not exist").format(name=role)
        console.print(f"[yellow]{EMOJI_MAP['warning']} {msg}[/yellow]")
        console.print()

        # Ask whether to initialize
        create = click.confirm(
            _("Initialize context for '{name}'?").format(name=role), default=True
        )
        if create:
            dm.init_role_context(role)
            msg = _("Initialized context for '{name}'").format(name=role)
            console.print(f"[green]{EMOJI_MAP['success']} {msg}[/green]")
        else:
            console.print(f"[dim]{_('Cancelled')}[/dim]")
            return

    # Execute switch
    console.print()
    if dm.switch_role(role):
        console.print(
            f"[green]{EMOJI_MAP['success']} {_('Switched to role:')} [bold cyan]{role}[/bold cyan][/green]"
        )
        console.print()
        console.print(f"  {BULLET} {_('Context file:')} {dm.get_role_context_file(role)}")
        console.print(f"  {BULLET} {_('Persisted to:')} .vibecollab.local.yaml")
        console.print()
        hint = _("Hint: Use 'vibecollab dev switch --clear' to restore default identity")
        console.print(f"[dim]{hint}[/dim]")
    else:
        console.print(f"[red]{_('Switch failed')}[/red]")
        raise SystemExit(1)

    console.print()


@role.command("conflicts")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--verbose", "-v", is_flag=True, help=_("Show detailed conflict info"))
@click.option(
    "--between", nargs=2, help=_("Detect conflicts between two roles (e.g. --between dev qa)")
)
def role_conflicts(config: str, verbose: bool, between: Optional[Tuple[str, str]]):
    """Detect cross-role work conflicts

    Detects potential conflicts between multiple roles, including file conflicts,
    task conflicts, dependency conflicts, etc.

    Examples:

        vibecollab dev conflicts                 # Detect all role conflicts

        vibecollab dev conflicts -v              # Show detailed info

        vibecollab dev conflicts --between dev qa    # Detect conflicts between two specific roles
    """
    from ..domain.conflict_detector import ConflictDetector

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    role_based_enabled = project_config.get("role_context", {}).get("enabled", False)

    console.print()

    # In single-role mode, no conflicts possible
    if not role_based_enabled:
        from ..domain.role import RoleManager

        dm = RoleManager(project_root, project_config)
        current_dev = dm.get_current_role()
        console.print(
            f"[green]{EMOJI_MAP['success']} {_('Single-role mode: no conflicts possible')}[/green]"
        )
        console.print(f"  {BULLET} {_('Current role:')} {current_dev}")
        console.print()
        return

    console.print(f"[cyan]{_('Detecting cross-role conflicts...')}[/cyan]")
    console.print()

    try:
        detector = ConflictDetector(project_root, project_config)

        conflicts = detector.detect_all_conflicts(target_role=None, between_roles=between)

        report = detector.generate_conflict_report(conflicts, verbose=verbose)
        console.print(report)

        if conflicts:
            raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]{_('Conflict detection failed:')}[/red] {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise SystemExit(1)


@role.command("permissions")
@click.option("-c", "--config", default="project.yaml", help="Project config file path")
@click.option(
    "-r", "--role", "role_code", help="Show permissions for specific role (default: current)"
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def role_permissions(config: str, role_code: Optional[str], as_json: bool):
    """Show effective permissions for current or specified role

    Displays the permission settings including:
    - Assigned roles and primary role
    - File pattern access rights
    - Task creation permissions
    - Status transition permissions
    - Decision approval levels

    Examples:

        vibecollab role permissions              # Show current role permissions

        vibecollab role permissions -r DEV       # Show DEV role permissions

        vibecollab role permissions --json       # Output as JSON for scripting
    """
    import json as json_module

    from ..domain.role import RoleManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    dm = RoleManager(project_root, project_config)

    # Get target role
    if role_code is None:
        role_code = dm.get_current_role()
        source = dm.get_identity_source()
    else:
        source = "manual_specified"

    # Get effective permissions
    effective = dm.get_effective_permissions(role_code)

    if as_json:
        console.print(json_module.dumps(effective, indent=2, ensure_ascii=False))
        return

    # Display in formatted table
    console.print()
    console.print(f"[cyan]{_('Role Permissions')}[/cyan]")
    console.print()

    # Basic info
    console.print(f"  {_('Developer:')} [bold]{effective['developer']}[/bold]")
    console.print(f"  {_('Primary Role:')} [bold cyan]{effective['primary_role']}[/bold cyan]")
    console.print(f"  {_('All Roles:')} {', '.join(effective['all_roles'])}")
    console.print(f"  {_('Identity Source:')} {source}")
    console.print()

    # Permissions
    perms = effective["permissions"]
    if not perms:
        console.print(f"  [yellow]{_('No permissions configured (permissive mode)')}[/yellow]")
        console.print(f"  [dim]{_('All operations allowed by default')}[/dim]")
    else:
        console.print(f"  [bold]{_('Permissions:')}[/bold]")

        # File patterns
        patterns = perms.get("file_patterns", [])
        if patterns:
            console.print(f"    {_('File Access:')}")
            for pattern in patterns:
                console.print(f"      • {pattern}")

        # Task creation
        can_create = perms.get("can_create_task_for", [])
        if can_create:
            console.print(f"    {_('Can Create Tasks For:')} {', '.join(can_create)}")

        # Status transitions
        can_transition = perms.get("can_transition_to", [])
        if can_transition:
            console.print(f"    {_('Can Transition To:')} {', '.join(can_transition)}")

        # Decision approval
        can_approve = perms.get("can_approve_decisions", [])
        if can_approve:
            console.print(f"    {_('Can Approve Decisions:')} {', '.join(can_approve)}")

    console.print()

    # Quick check examples
    console.print(f"  [dim]{_('Quick Checks:')}[/dim]")
    test_roles = ["DEV", "ARCH", "QA"]
    for test_role in test_roles:
        can_create = dm.can_create_task_for(test_role, role_code)
        status = "✓" if can_create else "✗"
        color = "green" if can_create else "red"
        console.print(f"    [{color}]{status}[/{color}] {_('Create tasks for')} {test_role}")

    console.print()


# Git Hooks Management Commands
@main.group("hooks")
def hooks():
    """Manage Git hooks for the project

    Install, uninstall, and run Git hooks to enforce quality checks
    at various points in the Git workflow.

    Examples:

        vibecollab hooks install                    # Install pre-commit hook

        vibecollab hooks install -t pre-push        # Install pre-push hook

        vibecollab hooks uninstall --all            # Remove all hooks

        vibecollab hooks run pre-commit             # Manually run pre-commit

        vibecollab hooks status                     # Show hook status
    """
    pass


@hooks.command("install")
@click.option("-t", "--type", "hook_type", default="pre-commit", help="Hook type to install")
@click.option("-c", "--config", default="project.yaml", help="Project config file path")
@click.option("-f", "--force", is_flag=True, help="Overwrite existing hook")
def hooks_install(hook_type: str, config: str, force: bool):
    """Install Git hooks"""
    from pathlib import Path

    from ..domain.hook_manager import HookManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    import yaml

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    hook_config = project_config.get("hooks", {})
    manager = HookManager(project_root, hook_config)

    if not manager.is_git_repo():
        console.print("[red]Error:[/red] Not a Git repository")
        raise SystemExit(1)

    success = manager.install(hook_type, force=force)

    if success:
        console.print(f"[green]✅ Installed {hook_type} hook[/green]")
    else:
        if (project_root / ".git" / "hooks" / hook_type).exists() and not force:
            console.print(
                f"[yellow]⚠️  {hook_type} hook already exists (use --force to overwrite)[/yellow]"
            )
        else:
            console.print(f"[red]❌ Failed to install {hook_type} hook[/red]")
        raise SystemExit(1)


@hooks.command("uninstall")
@click.option("-t", "--type", "hook_type", help="Hook type to uninstall")
@click.option("-c", "--config", default="project.yaml", help="Project config file path")
@click.option("--all", "uninstall_all", is_flag=True, help="Uninstall all hooks")
def hooks_uninstall(hook_type: Optional[str], config: str, uninstall_all: bool):
    """Uninstall Git hooks"""
    from pathlib import Path

    from ..domain.hook_manager import HookManager

    config_path = Path(config)
    project_root = config_path.parent

    import yaml

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    hook_config = project_config.get("hooks", {})
    manager = HookManager(project_root, hook_config)

    if not manager.is_git_repo():
        console.print("[red]Error:[/red] Not a Git repository")
        raise SystemExit(1)

    if uninstall_all:
        count = manager.uninstall_all()
        console.print(f"[green]✅ Uninstalled {count} hooks[/green]")
    elif hook_type:
        success = manager.uninstall(hook_type)
        if success:
            console.print(f"[green]✅ Uninstalled {hook_type} hook[/green]")
        else:
            console.print(
                f"[yellow]⚠️  {hook_type} hook not found or not managed by vibecollab[/yellow]"
            )
    else:
        console.print("[yellow]Please specify --type or --all[/yellow]")
        raise SystemExit(1)


@hooks.command("run")
@click.argument("hook_type")
@click.option("-c", "--config", default="project.yaml", help="Project config file path")
def hooks_run(hook_type: str, config: str):
    """Run hooks manually"""
    from pathlib import Path

    from ..domain.hook_manager import HookManager

    config_path = Path(config)
    project_root = config_path.parent

    import yaml

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    hook_config = project_config.get("hooks", {})
    manager = HookManager(project_root, hook_config)

    console.print(f"[cyan]Running {hook_type} hooks...[/cyan]")
    exit_code = manager.run(hook_type)

    if exit_code == 0:
        console.print(f"[green]✅ {hook_type} hooks passed[/green]")
    else:
        console.print(f"[red]❌ {hook_type} hooks failed[/red]")
        raise SystemExit(exit_code)


@hooks.command("status")
@click.option("-c", "--config", default="project.yaml", help="Project config file path")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def hooks_status(config: str, as_json: bool):
    """Show hooks status"""
    import json as json_module
    from pathlib import Path

    from ..domain.hook_manager import HookManager

    config_path = Path(config)
    project_root = config_path.parent

    import yaml

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    hook_config = project_config.get("hooks", {})
    manager = HookManager(project_root, hook_config)

    status = manager.status()

    if as_json:
        console.print(json_module.dumps(status, indent=2))
        return

    console.print()
    console.print("[cyan]Git Hooks Status[/cyan]")
    console.print()

    if not status["is_git_repo"]:
        console.print("[red]Not a Git repository[/red]")
        return

    console.print(f"  Hooks enabled: {status['enabled']}")
    console.print()

    for hook_type, info in status["hooks"].items():
        if info["installed"]:
            icon = "🟢" if info["is_vibecollab"] else "🟡"
            source = "vibecollab" if info["is_vibecollab"] else "custom"
            console.print(f"  {icon} {hook_type}: installed ({source})")
        else:
            console.print(f"  ⚪ {hook_type}: not installed")

    console.print()


@hooks.command("list")
@click.option("-c", "--config", default="project.yaml", help="Project config file path")
def hooks_list(config: str):
    """List installed vibecollab hooks"""
    from pathlib import Path

    from ..domain.hook_manager import HookManager

    config_path = Path(config)
    project_root = config_path.parent

    import yaml

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    hook_config = project_config.get("hooks", {})
    manager = HookManager(project_root, hook_config)

    installed = manager.list_hooks()

    if installed:
        console.print("[cyan]Installed vibecollab hooks:[/cyan]")
        for hook in installed:
            console.print(f"  • {hook}")
    else:
        console.print("[dim]No vibecollab hooks installed[/dim]")


if __name__ == "__main__":
    main()
