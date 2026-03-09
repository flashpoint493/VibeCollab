"""
LLMContext CLI - Command line interface
"""

from pathlib import Path
from typing import Optional, Tuple

import click
import yaml
from rich.panel import Panel
from rich.table import Table

from .. import __version__
from .._compat import BULLET, EMOJI, is_windows_gbk, safe_console
from ..core.generator import LLMContextGenerator
from ..i18n import _, setup_locale
from ..utils.git import is_git_repo
from ..utils.llmstxt import LLMsTxtManager
from ..core.project import Project
from ..core.protocol_checker import ProtocolChecker
from ..core.templates import TemplateManager

# Backward compatible variable names
USE_EMOJI = not is_windows_gbk()
EMOJI_MAP = EMOJI

console = safe_console()

DOMAINS = ["generic", "game", "web", "data", "mobile", "infra"]


def _get_protocol_version() -> str:
    """Read protocol version from project.yaml, fallback to '1.0'."""
    try:
        config_path = Path("project.yaml")
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return config.get("project", {}).get("version", "v1.0")
    except Exception:
        pass
    return "v1.0"


def _safe_load_yaml(path: Path, label: str = "config file") -> dict:
    """Safely load a YAML file with friendly error messages.

    Handles: file not found, YAML syntax error, empty file.
    """
    if not path.exists():
        console.print(f"[red]{_('Error:')}[/red] {label} {_('not found:')} {path}")
        console.print(f"[dim]{_('Hint: run in the project directory or use -c to specify the path')}[/dim]")
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
        console.print(f"[red]{_('Error:')}[/red] {label} {_('has invalid format (expected YAML dict):')} {path}")
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
    "--domain", "-d",
    type=click.Choice(DOMAINS),
    default="generic",
    help=_("Business domain")
)
@click.option("--output", "-o", required=True, help=_("Output directory"))
@click.option("--force", "-f", is_flag=True, help=_("Force overwrite existing directory"))
@click.option("--no-git", is_flag=True, help=_("Skip automatic Git initialization"))
@click.option("--multi-dev", is_flag=True, help=_("Enable multi-developer mode"))
def init(name: str, domain: str, output: str, force: bool, no_git: bool, multi_dev: bool):
    """Initialize a new project

    Examples:

        vibecollab init -n "MyProject" -d web -o ./my-project

        vibecollab init -n "GameProject" -d game -o ./game --force

        vibecollab init -n "TeamProject" -o ./team --multi-dev
    """
    output_path = Path(output)

    if output_path.exists() and not force:
        if any(output_path.iterdir()):
            console.print(f"[red]{_('Error:')}[/red] {_('Directory {dir} already exists and is not empty. Use --force to overwrite.').format(dir=output)}")
            raise SystemExit(1)

    with console.status(f"[bold green]{_('Initializing project {name}...').format(name=name)}"):
        try:
            project = Project.create(name=name, domain=domain, output_dir=output_path, multi_dev=multi_dev)
            project.generate_all(auto_init_git=not no_git)
        except PermissionError as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Permission denied:')} {e}")
            raise SystemExit(1)
        except OSError as e:
            console.print(f"[red]{_('Error:')}[/red] {_('File system error (disk full/invalid path):')} {e}")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]{_('Error:')}[/red] {_('Project initialization failed:')} {e}")
            raise SystemExit(1)

    console.print()
    mode_text = _("multi-developer") if multi_dev else _("single-developer")
    console.print(Panel.fit(
        f"[bold green]{EMOJI_MAP['success']} {_('Project {name} initialized!').format(name=name)}[/bold green]\n\n"
        f"[dim]{_('Directory:')}[/dim] {output_path.absolute()}\n"
        f"[dim]{_('Domain:')}[/dim] {domain}\n"
        f"[dim]{_('Mode:')}[/dim] {mode_text}",
        title=_("Done")
    ))

    table = Table(title=_("Generated Files"), show_header=True)
    table.add_column(_("File"), style="cyan")
    table.add_column(_("Description"))
    table.add_row("CONTRIBUTING_AI.md", _("AI collaboration rules"))
    table.add_row("llms.txt", _("Project context (with collaboration rules reference)"))
    table.add_row("project.yaml", _("Project config (editable)"))

    if multi_dev:
        table.add_row("docs/CONTEXT.md", _("Global aggregated context (auto-generated)"))
        table.add_row("docs/developers/{dev}/CONTEXT.md", _("Per-developer context"))
        table.add_row("docs/developers/COLLABORATION.md", _("Collaboration document"))
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
        console.print(f"[green]{EMOJI_MAP['success']} {_('Git repository initialized automatically')}[/green]")
    elif git_warning:
        console.print()
        console.print(f"[yellow]{EMOJI_MAP['warning']} {git_warning}[/yellow]")
        console.print(f"[dim]{_('Hint: consider initializing a Git repository to track changes')}[/dim]")

    if multi_dev:
        from ..domain.developer import DeveloperManager
        dm = DeveloperManager(output_path, project.config)
        current_dev = dm.get_current_developer()

        console.print()
        console.print(f"[bold cyan]{_('Multi-developer mode enabled')}[/bold cyan]")
        console.print(f"  {BULLET} {_('Current developer:')} {current_dev}")
        cmd_hint = _("Use 'vibecollab dev' for related commands")
        console.print(f"  {BULLET} {cmd_hint}")

    console.print()
    console.print(f"[bold]{_('Next steps:')}[/bold]")
    console.print(f"  1. cd {output}")
    step = 2
    if not is_git_repo(output_path):
        console.print(f"  {step}. git init  # {_('Initialize Git repository')}")
        step += 1
    if multi_dev:
        console.print(f"  {step}. vibecollab dev whoami  # {_('Check current developer')}")
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
                project_desc = project_config.get("project", {}).get("description", "AI-assisted development project")

                updated, llmstxt_path = LLMsTxtManager.ensure_integration(
                    project_root,
                    project_name,
                    project_desc,
                    output_path
                )

                if updated:
                    if llmstxt_path and llmstxt_path.exists():
                        console.print(f"[green]{EMOJI_MAP['success']} {_('Updated:')}[/green] {llmstxt_path}")
                    else:
                        console.print(f"[green]{EMOJI_MAP['success']} {_('Created:')}[/green] {llmstxt_path}")
                else:
                    console.print(f"[dim]{_('Info: llms.txt already contains collaboration rules reference')}[/dim]")
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
        console.print(f"[red]{EMOJI_MAP['error']} {_('Found {n} issue(s):').format(n=len(errors))}[/red]")
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
@click.option("--template", "-t", default="default", help=_("Template name"))
@click.option("--output", "-o", default="project.yaml", help=_("Output file path"))
def export_template(template: str, output: str):
    """Export template configuration file

    Examples:

        vibecollab export-template -t default -o my-project.yaml

        vibecollab export-template -t game -o game-project.yaml
    """
    tm = TemplateManager()
    output_path = Path(output)

    try:
        content = tm.get_template(template)
        output_path.write_text(content, encoding="utf-8")
        console.print(f"[green]{EMOJI_MAP['success']} {_('Template exported:')}[/green] {output_path}")
    except FileNotFoundError:
        console.print(f"[red]{_('Error:')}[/red] {_('Template not found:')} {template}")
        hint = _("Use 'vibecollab templates' to view available templates")
        console.print(f"[dim]{hint}[/dim]")
        raise SystemExit(1)


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
        console.print(f"[dim]{_('Hint: Run in the project directory, or use -c to specify the config file path')}[/dim]")
        raise SystemExit(1)

    # Load user config
    user_config = _safe_load_yaml(config_path)

    # Get latest template
    tm = TemplateManager()
    try:
        latest_template = yaml.safe_load(tm.get_template("default"))
        if not isinstance(latest_template, dict):
            console.print(f"[red]{_('Error:')}[/red] {_('Built-in default template has invalid format')}")
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
        "multi_developer": user_config.get("multi_developer"),
    }

    # Deep merge: latest as base, user_preserved overrides
    merged = deep_merge(latest_template, {k: v for k, v in user_preserved.items() if v is not None})

    # Analyze changes
    new_sections = []
    for key in latest_template:
        if key not in user_config:
            new_sections.append(key)

    if dry_run:
        console.print(Panel.fit(
            f"[bold yellow]{_('Preview mode')}[/bold yellow] - {_('No files will be modified')}",
            title=_("Dry Run")
        ))
        console.print()

        if new_sections:
            console.print(f"[bold]{EMOJI['package']} {_('New config sections to be added:')}[/bold]")
            for section in new_sections:
                console.print(f"  [green]+ {section}[/green]")
        else:
            console.print(f"[dim]{_('No new config sections')}[/dim]")

        console.print()
        console.print(f"[bold]{EMOJI_MAP['lock']} {_('User config to be preserved:')}[/bold]")
        console.print(f"  {BULLET} project.name: {user_preserved['project'].get('name', _('(not set)'))}")
        console.print(f"  {BULLET} project.domain: {user_preserved['project'].get('domain', _('(not set)'))}")
        if user_preserved.get('roles'):
            console.print(f"  {BULLET} roles: {len(user_preserved['roles'])} {_('role(s)')}")
        if user_preserved.get('confirmed_decisions'):
            console.print(f"  {BULLET} confirmed_decisions: {len(user_preserved['confirmed_decisions'])} {_('decision(s)')}")

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
        config_path.parent,
        project_name,
        project_desc,
        contributing_ai_path
    )

    # Check and initialize multi-developer directory structure
    multi_dev_config = merged.get("multi_developer", {})
    if multi_dev_config.get("enabled", False):
        from datetime import datetime

        from ..domain.developer import ContextAggregator, DeveloperManager

        dm = DeveloperManager(config_path.parent, merged)
        developers_dir = config_path.parent / "docs" / "developers"

        # Check if initialization is needed
        initialized = False

        # Initialize each developer's context
        developers = multi_dev_config.get("developers", [])
        for dev in developers:
            dev_id = dev.get("id")
            if not dev_id:
                continue

            dev_dir = developers_dir / dev_id
            if not dev_dir.exists():
                dm.init_developer_context(dev_id)
                console.print(f"  [green]{EMOJI_MAP['sparkles']} {_('Initialized developer directory:')} docs/developers/{dev_id}/[/green]")
                initialized = True

        # Create COLLABORATION.md
        collab_config = multi_dev_config.get('collaboration', {})
        collab_file = config_path.parent / collab_config.get('file', 'docs/developers/COLLABORATION.md')

        if not collab_file.exists():
            collab_file.parent.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")

            collab_content = f"""# {project_name} Developer Collaboration Log

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
2. **Conflict Avoidance**: Check if other developers are editing shared documents before modifying
3. **Handoff Process**: Record handoff details in this document during task handoffs

## Handoff Records

(No handoff records yet)

---
*Last updated: {today}*
"""
            collab_file.write_text(collab_content, encoding='utf-8')
            console.print(f"  [green]{EMOJI_MAP['sparkles']} {_('Created collaboration document:')} {collab_config.get('file', 'docs/developers/COLLABORATION.md')}[/green]")
            initialized = True

        # Generate global aggregated CONTEXT.md
        aggregator = ContextAggregator(config_path.parent, merged)
        global_context = config_path.parent / "docs" / "CONTEXT.md"
        if not global_context.exists() or initialized:
            aggregator.generate_and_save()
            console.print(f"  [green]{EMOJI_MAP['sparkles']} {_('Generated global context aggregation:')} docs/CONTEXT.md[/green]")

    # Success message
    console.print()
    console.print(Panel.fit(
        f"[bold green]{EMOJI_MAP['success']} {_('Protocol upgraded to v{version}').format(version=__version__)}[/bold green]",
        title=_("Upgrade Complete")
    ))

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
def version_info():
    """Show version and protocol information"""
    console.print(Panel.fit(
        f"[bold]VibeCollab[/bold] v{__version__}\n\n"
        f"[dim]{_('Protocol version:')}[/dim] {_get_protocol_version()}\n"
        f"[dim]{_('Supported domains:')}[/dim] {', '.join(DOMAINS)}\n"
        f"[dim]Python:[/dim] 3.9+",
        title=_("Version Info")
    ))


@main.command()
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--strict", is_flag=True, help=_("Strict mode: treat warnings as failures"))
@click.option("--insights", is_flag=True, help=_("Also run Insight consistency check"))
def check(config: str, strict: bool, insights: bool):
    """Check protocol compliance

    Check whether the project follows the collaboration protocol defined in CONTRIBUTING_AI.md.

    Examples:

        vibecollab check                    # Check the project in current directory

        vibecollab check -c project.yaml    # Specify config file

        vibecollab check --strict           # Strict mode

        vibecollab check --insights         # Also check Insight consistency
    """
    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        console.print(f"[dim]{_('Hint: Run in the project directory, or use -c to specify the config file path')}[/dim]")
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
    console.print(Panel.fit(
        f"[bold]{_('Protocol Compliance Check')}[/bold]",
        title=_("Protocol Check")
    ))
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
        console.print(Panel.fit(
            f"[bold]{_('Schema Validation')}[/bold]",
            title=_("Schema Check")
        ))
        console.print()
        if schema_errors_list:
            console.print(f"[bold red]{EMOJI_MAP['error']} {_('Schema Errors:')}[/bold red]")
            for err in schema_errors_list:
                console.print(f"  {BULLET} {err}")
            console.print()
        if schema_warnings_list:
            console.print(f"[bold yellow]{EMOJI_MAP['warning']} {_('Schema Warnings:')}[/bold yellow]")
            for warn in schema_warnings_list:
                console.print(f"  {BULLET} {warn}")
            console.print()

    # Insight consistency check
    insight_errors = 0
    insight_warnings = 0
    if insights:
        console.print(Panel.fit(
            f"[bold]{_('Insight System Consistency Check')}[/bold]",
            title=_("Insight Consistency Check")
        ))
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
                console.print(f"[bold yellow]{EMOJI_MAP['warning']} {_('Insight Warnings:')}[/bold yellow]")
                for warn in report.warnings:
                    console.print(f"  {BULLET} {warn}")
                console.print()
            if report.ok and not report.warnings:
                console.print(f"  [green]{EMOJI_MAP['success']} {_('Insight consistency check passed')}[/green]")
                console.print()
        except Exception as e:
            console.print(f"  [yellow]{EMOJI_MAP['warning']} {_('Insight check skipped:')} {e}[/yellow]")
            console.print()

    # Merge statistics
    total_errors = len(errors) + insight_errors + len(schema_errors_list)
    total_warnings = len(warnings) + insight_warnings + len(schema_warnings_list)
    total_checks = summary["total"] + (1 if insights else 0) + (1 if schema_errors_list or schema_warnings_list else 0)

    # Display summary
    if total_errors == 0 and not (strict and total_warnings > 0):
        console.print(Panel.fit(
            f"[bold green]{EMOJI_MAP['success']} {_('All checks passed')}[/bold green]\n\n"
            f"{_('Total:')} {total_checks} {_('check(s)')}",
            title=_("Check Complete")
        ))
    else:
        status = _("Failed") if total_errors > 0 or (strict and total_warnings > 0) else _("Has Warnings")
        color = "red" if total_errors > 0 or (strict and total_warnings > 0) else "yellow"
        emoji = EMOJI_MAP['error'] if total_errors > 0 or (strict and total_warnings > 0) else EMOJI_MAP['warning']
        console.print(Panel.fit(
            f"[bold {color}]{emoji} {_('Check')} {status}[/bold {color}]\n\n"
            f"{_('Total:')} {total_checks} {_('check(s)')}\n"
            f"{_('Errors:')} {total_errors}\n"
            f"{_('Warnings:')} {total_warnings}",
            title=_("Check Complete")
        ))
        if strict and total_warnings > 0:
            console.print()
            console.print(f"[dim]{_('Hint: In --strict mode, warnings are treated as failures')}[/dim]")

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
    grade_color = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}.get(grade, "white")

    console.print(Panel(
        f"[bold {grade_color}]{_('Grade:')} {grade} ({score:.0f}/100)[/bold {grade_color}]\n"
        f"CRITICAL: {report.critical_count}  WARNING: {report.warning_count}  INFO: {report.info_count}",
        title=_("Project Health")
    ))

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

# Import AI commands (human-AI dialogue + Agent autonomous mode)
from .ai import ai as ai_group  # noqa: E402

main.add_command(ai_group)

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


# ============================================
# Pipeline commands (v0.10.2+)
# ============================================

@main.group("pipeline")
def pipeline_group():
    """Pipeline: schema validation, doc sync, action registry

    Structured chain-of-actions for document consistency and automation.
    """
    pass


@pipeline_group.command("validate")
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def pipeline_validate(config, json_output):
    """Validate project.yaml against schema rules"""
    import json as json_mod
    from ..core.pipeline import Pipeline

    project_root = Path(config).parent or Path(".")
    pipe = Pipeline(project_root, config_path=config)
    report = pipe.validate_config()

    if json_output:
        click.echo(json_mod.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    if report.ok and not report.warnings:
        console.print(f"[green]{EMOJI_MAP['success']} Schema validation passed[/green]")
    else:
        if report.errors:
            console.print(f"[bold red]{EMOJI_MAP['error']} Schema errors:[/bold red]")
            for err in report.errors:
                console.print(f"  {BULLET} {err}")
        if report.warnings:
            console.print(f"[bold yellow]{EMOJI_MAP['warning']} Schema warnings:[/bold yellow]")
            for warn in report.warnings:
                console.print(f"  {BULLET} {warn}")

    if not report.ok:
        raise SystemExit(1)


@pipeline_group.command("status")
@click.option("--config", "-c", default="project.yaml", help=_("Config file path"))
@click.option("--json-output", "--json", is_flag=True, help=_("JSON output"))
def pipeline_status(config, json_output):
    """Show pipeline status: pending actions, doc freshness, versions"""
    import json as json_mod
    from ..core.pipeline import Pipeline

    project_root = Path(config).parent or Path(".")
    pipe = Pipeline(project_root, config_path=config)

    versions = pipe.get_version()
    stale_docs = pipe.check_docs()
    pending = pipe.get_pending_actions()

    if json_output:
        click.echo(json_mod.dumps({
            "versions": versions,
            "stale_docs": stale_docs,
            "pending_actions": pending,
        }, ensure_ascii=False, indent=2))
        return

    console.print(Panel.fit(
        f"[bold]Pipeline Status[/bold]\n\n"
        f"Package version: {versions['package_version']}\n"
        f"Protocol version: {versions['protocol_version']}",
        title="VibeCollab Pipeline"
    ))

    if stale_docs:
        console.print(f"\n[yellow]{EMOJI_MAP['warning']} Stale documents:[/yellow]")
        for doc in stale_docs:
            status = doc['status']
            console.print(
                f"  {BULLET} {doc['downstream']} is {status} "
                f"(upstream: {doc['upstream']})"
            )

    if pending:
        console.print(f"\n[bold]Pending actions ({len(pending)}):[/bold]")
        for action in pending:
            pri = action['priority']
            color = "red" if pri == 1 else "yellow" if pri == 2 else "dim"
            cmd = action.get('command', '')
            console.print(
                f"  [{color}]P{pri}[/{color}] {action['message']}"
            )
            if cmd:
                console.print(f"      [dim]$ {cmd}[/dim]")
    else:
        console.print(f"\n[green]{EMOJI_MAP['success']} No pending actions[/green]")


@pipeline_group.command("actions")
@click.argument("event", required=False)
def pipeline_actions(event):
    """Show recommended CLI actions for a lifecycle event

    Events: task_completed, task_created, insight_added,
            milestone_completed, config_changed, docs_stale

    Examples:

        vibecollab pipeline actions                 # List all events

        vibecollab pipeline actions task_completed  # Show actions for event
    """
    from ..core.pipeline import ActionRegistry

    if event:
        actions = ActionRegistry.get_actions(event)
        if not actions:
            click.echo(f"No actions registered for event '{event}'")
            return
        click.echo(f"Actions for '{event}':")
        for cmd, desc, pri in actions:
            click.echo(f"  P{pri}: {cmd}")
            click.echo(f"       {desc}")
    else:
        events = ActionRegistry.get_all_events()
        click.echo("Registered lifecycle events:")
        for evt in events:
            actions = ActionRegistry.get_actions(evt)
            click.echo(f"\n  {evt} ({len(actions)} actions):")
            for cmd, desc, pri in actions:
                click.echo(f"    P{pri}: {cmd}")


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
@click.option("--host", default=None, help=_("Host adapter override (llm, subprocess:cmd)"))
def plan_run(plan_file, dry_run, json_output, timeout, host):
    """Execute a YAML automation plan

    Examples:

        vibecollab plan run my_plan.yaml

        vibecollab plan run my_plan.yaml --dry-run

        vibecollab plan run my_plan.yaml --json

        vibecollab plan run my_plan.yaml --host llm
    """
    import json as json_mod
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
        # CLI override: "llm" or "subprocess:command"
        if host.startswith("subprocess:"):
            from ..core.execution_plan import SubprocessAdapter
            host_adapter = SubprocessAdapter(
                command=host[len("subprocess:"):],
                cwd=Path(".").resolve(),
            )
        else:
            override_plan = {**plan, "host": host}
            host_adapter = resolve_host_adapter(override_plan, Path(".").resolve())

    runner = PlanRunner(
        project_root=Path(".").resolve(),
        timeout=timeout,
        event_log=event_log,
        dry_run=dry_run,
        host=host_adapter,
    )
    result = runner.run(plan)

    if json_output:
        click.echo(json_mod.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        # Rich output
        status_emoji = EMOJI_MAP['success'] if result.success else EMOJI_MAP['error']
        status_color = "green" if result.success else "red"

        console.print()
        console.print(Panel.fit(
            f"[bold]{result.name}[/bold]\n\n"
            f"Status: [{status_color}]{status_emoji} {'PASSED' if result.success else 'FAILED'}[/{status_color}]\n"
            f"Steps: {result.passed}/{result.total_steps} passed, "
            f"{result.failed} failed, {result.skipped} skipped\n"
            f"Duration: {result.duration_ms}ms",
            title="Plan Result"
        ))

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
# Multi-developer management commands (v0.5.0+)
# ============================================

@main.group()
def dev():
    """Multi-developer management commands

    Manage projects with multi-developer collaboration.
    """
    pass


@dev.command("whoami")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def dev_whoami(config: str):
    """Show current developer identity

    Examples:

        vibecollab dev whoami
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    dm = DeveloperManager(project_root, project_config)
    current_dev = dm.get_current_developer()
    identity_source = dm.get_identity_source()

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)

    # Friendly display for identity source
    source_display = {
        'local_switch': f'[green]{_("CLI switch")}[/green] (.vibecollab.local.yaml)',
        'env_var': f'[yellow]{_("Environment variable")}[/yellow] (VIBECOLLAB_DEVELOPER)',
        'git_username': _('Git username (git config user.name)'),
        'system_user': _('System username'),
    }.get(identity_source, identity_source)

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{current_dev}[/bold cyan]\n\n"
        f"{_('Multi-developer mode:')} {'[green]' + _('Enabled') + '[/green]' if multi_dev_enabled else '[yellow]' + _('Not enabled') + '[/yellow]'}\n"
        f"{_('Identity source:')} {source_display}",
        title=_("Current Developer")
    ))
    console.print()


@dev.command("list")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def dev_list(config: str):
    """List all developers

    Examples:

        vibecollab dev list
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} {_('Multi-developer mode is not enabled')}[/yellow]")
        console.print(f"[dim]{_('Set multi_developer.enabled: true in project.yaml')}[/dim]")
        raise SystemExit(1)

    dm = DeveloperManager(project_root, project_config)
    developers = dm.list_developers()
    current_dev = dm.get_current_developer()

    if not developers:
        console.print()
        console.print(f"[yellow]{_('No developers yet')}[/yellow]")
        hint = _("Use 'vibecollab init --multi-dev' to initialize a multi-developer project")
        console.print(f"[dim]{hint}[/dim]")
        console.print()
        return

    table = Table(title=_("Developer List"), show_header=True)
    table.add_column(_("Developer"), style="cyan")
    table.add_column(_("Status"))
    table.add_column(_("Last Updated"))
    table.add_column(_("Update Count"))

    for dev in developers:
        status_info = dm.get_developer_status(dev)
        is_current = f" ({_('current')})" if dev == current_dev else ""
        status = f"{EMOJI_MAP['success']} {_('Active')}{is_current}" if status_info['exists'] else f"{EMOJI_MAP['warning']} {_('Not initialized')}"
        last_updated = status_info.get('last_updated', '-') or '-'
        if last_updated != '-' and len(last_updated) > 19:
            last_updated = last_updated[:19]
        total_updates = str(status_info.get('total_updates', 0))

        table.add_row(dev, status, last_updated, total_updates)

    console.print()
    console.print(table)
    console.print()


@dev.command("status")
@click.argument("developer", required=False)
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def dev_status(developer: Optional[str], config: str):
    """View developer status

    Examples:

        vibecollab dev status           # View all developers

        vibecollab dev status dev       # View a specific role
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} {_('Multi-developer mode is not enabled')}[/yellow]")
        raise SystemExit(1)

    dm = DeveloperManager(project_root, project_config)

    if developer:
        developers = [developer]
    else:
        developers = dm.list_developers()

    if not developers:
        console.print()
        console.print(f"[yellow]{_('No developers yet')}[/yellow]")
        console.print()
        return

    for dev in developers:
        context_file = dm.get_developer_context_file(dev)
        if context_file.exists():
            console.print()
            console.print(Panel.fit(
                f"[bold]{dev}[/bold]",
                title=_("Developer Status")
            ))
            console.print()

            try:
                content = context_file.read_text(encoding='utf-8')
                lines = content.split('\n')[:20]
                console.print('\n'.join(lines))
                if len(content.split('\n')) > 20:
                    console.print(f"\n[dim]... ({_('more at')} {context_file})[/dim]")
            except Exception as e:
                console.print(f"[red]{_('Read failed:')}[/red] {e}")

            console.print()
        else:
            console.print(f"[yellow]{EMOJI_MAP['warning']} {_('Developer {name} not initialized').format(name=dev)}[/yellow]")


@dev.command("sync")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def dev_sync(config: str):
    """Manually trigger global CONTEXT aggregation

    Examples:

        vibecollab dev sync
    """
    from ..domain.developer import ContextAggregator

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} {_('Multi-developer mode is not enabled')}[/yellow]")
        raise SystemExit(1)

    console.print()
    console.print(f"[cyan]{_('Aggregating global CONTEXT...')}[/cyan]")

    try:
        aggregator = ContextAggregator(project_root, project_config)
        output_file = aggregator.generate_and_save()

        console.print(f"[green]{EMOJI_MAP['success']} {_('Aggregation complete:')}[/green] {output_file}")
        console.print()
    except Exception as e:
        console.print(f"[red]{_('Aggregation failed:')}[/red] {e}")
        raise SystemExit(1)


@dev.command("init")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--developer", "-d", help=_("Developer name (auto-detect if empty)"))
def dev_init(config: str, developer: Optional[str]):
    """Initialize current developer's context

    Examples:

        vibecollab dev init                 # Auto-detect current developer

        vibecollab dev init -d dev          # Initialize for dev role
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} {_('Multi-developer mode is not enabled')}[/yellow]")
        console.print(f"[dim]{_('Set multi_developer.enabled: true in project.yaml')}[/dim]")
        raise SystemExit(1)

    dm = DeveloperManager(project_root, project_config)

    if developer is None:
        developer = dm.get_current_developer()

    console.print()
    console.print(f"[cyan]{_('Initializing developer:')}[/cyan] {developer}")

    try:
        dm.init_developer_context(developer)
        context_file = dm.get_developer_context_file(developer)

        console.print(f"[green]{EMOJI_MAP['success']} {_('Initialization complete:')}[/green]")
        console.print(f"  {BULLET} {_('Context file:')} {context_file}")
        console.print()
    except Exception as e:
        console.print(f"[red]{_('Initialization failed:')}[/red] {e}")
        raise SystemExit(1)


@dev.command("switch")
@click.argument("developer", required=False)
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--clear", is_flag=True, help=_("Clear switch, restore default identity"))
def dev_switch(developer: Optional[str], config: str, clear: bool):
    """Switch current developer identity

    Select a developer context via CLI without modifying Git config or environment variables.
    The switch setting is persisted to the local config file (.vibecollab.local.yaml).

    Examples:

        vibecollab dev switch dev        # Switch to dev role

        vibecollab dev switch            # Interactive developer selection

        vibecollab dev switch --clear    # Clear switch, restore default identity
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]{_('Error:')}[/red] {_('Config file not found:')} {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} {_('Multi-developer mode is not enabled')}[/yellow]")
        console.print(f"[dim]{_('Set multi_developer.enabled: true in project.yaml')}[/dim]")
        raise SystemExit(1)

    dm = DeveloperManager(project_root, project_config)

    # Handle clear switch
    if clear:
        console.print()
        if dm.clear_switch():
            default_dev = dm.get_current_developer()
            console.print(f"[green]{EMOJI_MAP['success']} {_('Switch setting cleared')}[/green]")
            console.print(f"  {BULLET} {_('Current identity:')} [cyan]{default_dev}[/cyan] ({_('detected via default strategy')})")
        else:
            console.print(f"[red]{_('Clear failed')}[/red]")
            raise SystemExit(1)
        console.print()
        return

    # Get available developer list
    developers = dm.list_developers()
    current_dev = dm.get_current_developer()

    # If no developer specified, interactive selection
    if developer is None:
        if not developers:
            console.print()
            console.print(f"[yellow]{_('No developers yet')}[/yellow]")
            hint = _("Use 'vibecollab dev init -d <name>' to initialize a new developer")
            console.print(f"[dim]{hint}[/dim]")
            console.print()
            return

        console.print()
        console.print(f"[cyan]{_('Select a developer to switch to:')}[/cyan]")
        console.print()

        for i, dev in enumerate(developers, 1):
            status_info = dm.get_developer_status(dev)
            is_current = f" [green]({_('current')})[/green]" if dev == current_dev else ""
            last_update = status_info.get('last_updated', _('unknown'))
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

        if choice < 1 or choice > len(developers):
            console.print(f"[red]{_('Invalid choice:')} {choice}[/red]")
            raise SystemExit(1)

        developer = developers[choice - 1]

    # Normalize developer name
    identity_config = project_config.get('multi_developer', {}).get('identity', {})
    if identity_config.get('normalize', True):
        developer = dm._normalize_developer_name(developer)

    # Check if developer exists
    if developer not in developers:
        console.print()
        msg = _("Developer '{name}' does not exist").format(name=developer)
        console.print(f"[yellow]{EMOJI_MAP['warning']} {msg}[/yellow]")
        console.print()

        # Ask whether to initialize
        create = click.confirm(_("Initialize context for '{name}'?").format(name=developer), default=True)
        if create:
            dm.init_developer_context(developer)
            msg = _("Initialized context for '{name}'").format(name=developer)
            console.print(f"[green]{EMOJI_MAP['success']} {msg}[/green]")
        else:
            console.print(f"[dim]{_('Cancelled')}[/dim]")
            return

    # Execute switch
    console.print()
    if dm.switch_developer(developer):
        console.print(f"[green]{EMOJI_MAP['success']} {_('Switched to developer:')} [bold cyan]{developer}[/bold cyan][/green]")
        console.print()
        console.print(f"  {BULLET} {_('Context file:')} {dm.get_developer_context_file(developer)}")
        console.print(f"  {BULLET} {_('Persisted to:')} .vibecollab.local.yaml")
        console.print()
        hint = _("Hint: Use 'vibecollab dev switch --clear' to restore default identity")
        console.print(f"[dim]{hint}[/dim]")
    else:
        console.print(f"[red]{_('Switch failed')}[/red]")
        raise SystemExit(1)

    console.print()


@dev.command("conflicts")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--verbose", "-v", is_flag=True, help=_("Show detailed conflict info"))
@click.option("--between", nargs=2, help=_("Detect conflicts between two roles (e.g. --between dev qa)"))
def dev_conflicts(config: str, verbose: bool, between: Optional[Tuple[str, str]]):
    """Detect cross-developer work conflicts

    Detects potential conflicts between multiple developers, including file conflicts,
    task conflicts, dependency conflicts, etc.

    Examples:

        vibecollab dev conflicts                 # Detect all developer conflicts

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

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} {_('Multi-developer mode not enabled')}[/yellow]")
        console.print(f"[dim]{_('Set multi_developer.enabled: true in project.yaml')}[/dim]")
        raise SystemExit(1)

    console.print()
    console.print(f"[cyan]{_('Detecting cross-developer conflicts...')}[/cyan]")
    console.print()

    try:
        detector = ConflictDetector(project_root, project_config)

        conflicts = detector.detect_all_conflicts(
            target_developer=None,
            between_developers=between
        )

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




if __name__ == "__main__":
    main()
