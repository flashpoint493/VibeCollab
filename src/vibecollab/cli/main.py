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


def _safe_load_yaml(path: Path, label: str = "config file") -> dict:
    """Safely load a YAML file with friendly error messages.

    Handles: file not found, YAML syntax error, empty file.
    """
    if not path.exists():
        console.print(f"[red]Error:[/red] {label} not found: {path}")
        console.print("[dim]Hint: run in the project directory or use -c to specify the path[/dim]")
        raise SystemExit(1)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        console.print(f"[red]Error:[/red] {label} has invalid YAML syntax: {path}")
        console.print(f"[dim]{e}[/dim]")
        raise SystemExit(1)
    except OSError as e:
        console.print(f"[red]Error:[/red] Cannot read {label}: {e}")
        raise SystemExit(1)
    if data is None:
        console.print(f"[red]Error:[/red] {label} is empty: {path}")
        raise SystemExit(1)
    if not isinstance(data, dict):
        console.print(f"[red]Error:[/red] {label} has invalid format (expected YAML dict): {path}")
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
def main():
    """VibeCollab - AI Collaboration Protocol Generator

    Generate standardized AI collaboration protocol documents from YAML config,
    supporting Vibe Development philosophy for human-AI collaboration.
    Automatically integrates llms.txt standard.
    """
    pass


@main.command()
@click.option("--name", "-n", required=True, help="Project name")
@click.option(
    "--domain", "-d",
    type=click.Choice(DOMAINS),
    default="generic",
    help="Business domain"
)
@click.option("--output", "-o", required=True, help="Output directory")
@click.option("--force", "-f", is_flag=True, help="Force overwrite existing directory")
@click.option("--no-git", is_flag=True, help="Skip automatic Git initialization")
@click.option("--multi-dev", is_flag=True, help="Enable multi-developer mode")
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
            console.print(f"[red]Error:[/red] Directory {output} already exists and is not empty. Use --force to overwrite.")
            raise SystemExit(1)

    with console.status(f"[bold green]Initializing project {name}..."):
        try:
            project = Project.create(name=name, domain=domain, output_dir=output_path, multi_dev=multi_dev)
            project.generate_all(auto_init_git=not no_git)
        except PermissionError as e:
            console.print(f"[red]Error:[/red] Permission denied: {e}")
            raise SystemExit(1)
        except OSError as e:
            console.print(f"[red]Error:[/red] File system error (disk full/invalid path): {e}")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]Error:[/red] Project initialization failed: {e}")
            raise SystemExit(1)

    console.print()
    mode_text = "multi-developer" if multi_dev else "single-developer"
    console.print(Panel.fit(
        f"[bold green]{EMOJI_MAP['success']} Project {name} initialized![/bold green]\n\n"
        f"[dim]Directory:[/dim] {output_path.absolute()}\n"
        f"[dim]Domain:[/dim] {domain}\n"
        f"[dim]Mode:[/dim] {mode_text}",
        title="Done"
    ))

    table = Table(title="Generated Files", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Description")
    table.add_row("CONTRIBUTING_AI.md", "AI collaboration rules")
    table.add_row("llms.txt", "Project context (with collaboration rules reference)")
    table.add_row("project.yaml", "Project config (editable)")

    if multi_dev:
        table.add_row("docs/CONTEXT.md", "Global aggregated context (auto-generated)")
        table.add_row("docs/developers/{dev}/CONTEXT.md", "Per-developer context")
        table.add_row("docs/developers/COLLABORATION.md", "Collaboration document")
    else:
        table.add_row("docs/CONTEXT.md", "Current context")

    table.add_row("docs/DECISIONS.md", "Decision records")
    table.add_row("docs/CHANGELOG.md", "Changelog")
    table.add_row("docs/ROADMAP.md", "Roadmap")
    table.add_row("docs/QA_TEST_CASES.md", "Test cases")
    console.print(table)

    git_warning = project.config.get("_meta", {}).get("git_warning")
    git_auto_init = project.config.get("_meta", {}).get("git_auto_init", False)

    if git_auto_init:
        console.print()
        console.print(f"[green]{EMOJI_MAP['success']} Git repository initialized automatically[/green]")
    elif git_warning:
        console.print()
        console.print(f"[yellow]{EMOJI_MAP['warning']} {git_warning}[/yellow]")
        console.print("[dim]Hint: consider initializing a Git repository to track changes[/dim]")

    if multi_dev:
        from ..domain.developer import DeveloperManager
        dm = DeveloperManager(output_path, project.config)
        current_dev = dm.get_current_developer()

        console.print()
        console.print("[bold cyan]Multi-developer mode enabled[/bold cyan]")
        console.print(f"  {BULLET} Current developer: {current_dev}")
        console.print(f"  {BULLET} Use 'vibecollab dev' for related commands")

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. cd {output}")
    step = 2
    if not is_git_repo(output_path):
        console.print(f"  {step}. git init  # Initialize Git repository")
        step += 1
    if multi_dev:
        console.print(f"  {step}. vibecollab dev whoami  # Check current developer")
        step += 1
    console.print(f"  {step}. Edit project.yaml to customize configuration")
    step += 1
    console.print(f"  {step}. vibecollab generate -c project.yaml  # Regenerate")
    step += 1
    console.print(f"  {step}. Start your Vibe Development journey!")


@main.command()
@click.option("--config", "-c", required=True, help="YAML config file path")
@click.option("--output", "-o", default="CONTRIBUTING_AI.md", help="Output file path")
@click.option("--no-llmstxt", is_flag=True, help="Skip llms.txt integration")
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
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with console.status("[bold green]Generating collaboration rules document..."):
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
                        console.print(f"[green]{EMOJI_MAP['success']} Updated:[/green] {llmstxt_path}")
                    else:
                        console.print(f"[green]{EMOJI_MAP['success']} Created:[/green] {llmstxt_path}")
                else:
                    console.print("[dim]Info: llms.txt already contains collaboration rules reference[/dim]")
        except yaml.YAMLError as e:
            console.print(f"[red]Error:[/red] Invalid YAML in config file: {e}")
            raise SystemExit(1)
        except FileNotFoundError as e:
            console.print(f"[red]Error:[/red] Required file not found: {e}")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]Error:[/red] Document generation failed: {e}")
            raise SystemExit(1)

    console.print(f"[green]{EMOJI_MAP['success']} Generated:[/green] {output_path}")
    console.print(f"[dim]Config:[/dim] {config_path}")


@main.command()
@click.option("--config", "-c", required=True, help="YAML config file path")
def validate(config: str):
    """Validate configuration file

    Examples:

        vibecollab validate -c project.yaml
    """
    config_path = Path(config)

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with console.status("[bold green]Validating configuration..."):
        try:
            generator = LLMContextGenerator.from_file(config_path)
            errors = generator.validate()
        except yaml.YAMLError as e:
            console.print(f"[red]Error:[/red] Invalid YAML in config file: {e}")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]Error:[/red] Config parsing failed: {e}")
            raise SystemExit(1)

    if errors:
        console.print(f"[red]{EMOJI_MAP['error']} Found {len(errors)} issue(s):[/red]")
        for err in errors:
            console.print(f"  - {err}")
        raise SystemExit(1)
    else:
        console.print(f"[green]{EMOJI_MAP['success']} Config valid:[/green] {config}")


@main.command()
def domains():
    """List supported business domains"""
    table = Table(title="Supported Domains", show_header=True)
    table.add_column("Domain", style="cyan")
    table.add_column("Description")
    table.add_column("Features")

    domain_info = {
        "generic": ("General purpose", "Basic config"),
        "game": ("Game development", "GM console, GDD docs"),
        "web": ("Web application", "API docs, deployment env"),
        "data": ("Data engineering", "ETL pipeline, data quality"),
        "mobile": ("Mobile app", "Platform adaptation, release flow"),
        "infra": ("Infrastructure", "IaC, monitoring & alerting"),
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

    table = Table(title="Available Templates", show_header=True)
    table.add_column("Template", style="cyan")
    table.add_column("Type")
    table.add_column("Path")

    for tpl in available:
        table.add_row(tpl["name"], tpl["type"], str(tpl["path"]))

    console.print(table)


@main.command()
@click.option("--template", "-t", default="default", help="Template name")
@click.option("--output", "-o", default="project.yaml", help="Output file path")
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
        console.print(f"[green]{EMOJI_MAP['success']} Template exported:[/green] {output_path}")
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Template not found: {template}")
        console.print("[dim]Use 'vibecollab templates' to view available templates[/dim]")
        raise SystemExit(1)


@main.command()
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
@click.option("--dry-run", is_flag=True, help="Dry run: show changes only")
@click.option("--force", "-f", is_flag=True, help="Force upgrade without backup")
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
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        console.print("[dim]Hint: Run in the project directory, or use -c to specify the config file path[/dim]")
        raise SystemExit(1)

    # Load user config
    user_config = _safe_load_yaml(config_path)

    # Get latest template
    tm = TemplateManager()
    try:
        latest_template = yaml.safe_load(tm.get_template("default"))
        if not isinstance(latest_template, dict):
            console.print("[red]Error:[/red] Built-in default template has invalid format")
            raise SystemExit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]Error:[/red] Built-in template parse failed: {e}")
        raise SystemExit(1)

    # Record user-customized key fields (should not be overwritten)
    user_preserved = {
        "project": user_config.get("project", {}),
        "roles": user_config.get("roles"),
        "confirmed_decisions": user_config.get("confirmed_decisions"),
        "domain_extensions": user_config.get("domain_extensions"),
        "multi_developer": user_config.get("multi_developer"),  # v0.5.0+ preserve multi-developer config
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
            "[bold yellow]Preview mode[/bold yellow] - No files will be modified",
            title="Dry Run"
        ))
        console.print()

        if new_sections:
            console.print(f"[bold]{EMOJI['package']} New config sections to be added:[/bold]")
            for section in new_sections:
                console.print(f"  [green]+ {section}[/green]")
        else:
            console.print("[dim]No new config sections[/dim]")

        console.print()
        console.print(f"[bold]{EMOJI_MAP['lock']} User config to be preserved:[/bold]")
        console.print(f"  {BULLET} project.name: {user_preserved['project'].get('name', '(not set)')}")
        console.print(f"  {BULLET} project.domain: {user_preserved['project'].get('domain', '(not set)')}")
        if user_preserved.get('roles'):
            console.print(f"  {BULLET} roles: {len(user_preserved['roles'])} role(s)")
        if user_preserved.get('confirmed_decisions'):
            console.print(f"  {BULLET} confirmed_decisions: {len(user_preserved['confirmed_decisions'])} decision(s)")

        console.print()
        console.print("[dim]Remove --dry-run to perform the actual upgrade[/dim]")
        return

    # Backup original config
    backup_path = None
    if not force:
        backup_path = config_path.with_suffix(".yaml.bak")
        try:
            config_path.rename(backup_path)
            console.print(f"[dim]Original config backed up to: {backup_path}[/dim]")
        except OSError as e:
            console.print(f"[red]Error:[/red] Backup failed: {e}")
            raise SystemExit(1)

    # Write merged config
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(merged, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except OSError as e:
        console.print(f"[red]Error:[/red] Failed to write config: {e}")
        if backup_path and backup_path.exists():
            backup_path.rename(config_path)
            console.print("[yellow]Original config restored from backup[/yellow]")
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
                console.print(f"  [green]{EMOJI_MAP['sparkles']} Initialized developer directory: docs/developers/{dev_id}/[/green]")
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
            console.print(f"  [green]{EMOJI_MAP['sparkles']} Created collaboration document: {collab_config.get('file', 'docs/developers/COLLABORATION.md')}[/green]")
            initialized = True

        # Generate global aggregated CONTEXT.md
        aggregator = ContextAggregator(config_path.parent, merged)
        global_context = config_path.parent / "docs" / "CONTEXT.md"
        if not global_context.exists() or initialized:
            aggregator.generate_and_save()
            console.print(f"  [green]{EMOJI_MAP['sparkles']} Generated global context aggregation: docs/CONTEXT.md[/green]")

    # Success message
    console.print()
    console.print(Panel.fit(
        f"[bold green]{EMOJI_MAP['success']} Protocol upgraded to v{__version__}[/bold green]",
        title="Upgrade Complete"
    ))

    if new_sections:
        console.print()
        console.print(f"[bold]{EMOJI['package']} New config sections:[/bold]")
        for section in new_sections:
            console.print(f"  [green]+ {section}[/green]")

    console.print()
    console.print("[bold]Updated files:[/bold]")
    console.print(f"  {BULLET} {config_path}")
    console.print(f"  {BULLET} {contributing_ai_path}")

    console.print()
    console.print("[dim]Hint: Use git diff to review specific changes[/dim]")


@main.command()
def version_info():
    """Show version and protocol information"""
    console.print(Panel.fit(
        f"[bold]LLMContext[/bold] v{__version__}\n\n"
        f"[dim]Protocol version:[/dim] 1.0\n"
        f"[dim]Supported domains:[/dim] {', '.join(DOMAINS)}\n"
        f"[dim]Python:[/dim] 3.8+",
        title="Version Info"
    ))


@main.command()
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
@click.option("--strict", is_flag=True, help="Strict mode: treat warnings as failures")
@click.option("--insights", is_flag=True, help="Also run Insight consistency check")
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
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        console.print("[dim]Hint: Run in the project directory, or use -c to specify the config file path[/dim]")
        raise SystemExit(1)

    # Load config
    project_config = _safe_load_yaml(config_path)

    # Run checks
    checker = ProtocolChecker(project_root, project_config)
    results = checker.check_all()
    summary = checker.get_summary(results)

    # Display results
    console.print()
    console.print(Panel.fit(
        "[bold]Protocol Compliance Check[/bold]",
        title="Protocol Check"
    ))
    console.print()

    # Group by severity
    errors = [r for r in results if r.severity == "error"]
    warnings = [r for r in results if r.severity == "warning"]
    infos = [r for r in results if r.severity == "info"]

    if errors:
        console.print(f"[bold red]{EMOJI_MAP['error']} Errors:[/bold red]")
        for result in errors:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]Suggestion: {result.suggestion}[/dim]")
        console.print()

    if warnings:
        console.print(f"[bold yellow]{EMOJI_MAP['warning']} Warnings:[/bold yellow]")
        for result in warnings:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]Suggestion: {result.suggestion}[/dim]")
        console.print()

    if infos:
        console.print(f"[bold blue]{EMOJI_MAP['info']} Info:[/bold blue]")
        for result in infos:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]Suggestion: {result.suggestion}[/dim]")
        console.print()

    # Insight consistency check
    insight_errors = 0
    insight_warnings = 0
    if insights:
        console.print(Panel.fit(
            "[bold]Insight System Consistency Check[/bold]",
            title="Insight Consistency Check"
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
                console.print(f"[bold red]{EMOJI_MAP['error']} Insight Errors:[/bold red]")
                for err in report.errors:
                    console.print(f"  {BULLET} {err}")
                console.print()
            if report.warnings:
                insight_warnings = len(report.warnings)
                console.print(f"[bold yellow]{EMOJI_MAP['warning']} Insight Warnings:[/bold yellow]")
                for warn in report.warnings:
                    console.print(f"  {BULLET} {warn}")
                console.print()
            if report.ok and not report.warnings:
                console.print(f"  [green]{EMOJI_MAP['success']} Insight consistency check passed[/green]")
                console.print()
        except Exception as e:
            console.print(f"  [yellow]{EMOJI_MAP['warning']} Insight check skipped: {e}[/yellow]")
            console.print()

    # Merge statistics
    total_errors = len(errors) + insight_errors
    total_warnings = len(warnings) + insight_warnings
    total_checks = summary["total"] + (1 if insights else 0)

    # Display summary
    if total_errors == 0 and not (strict and total_warnings > 0):
        console.print(Panel.fit(
            f"[bold green]{EMOJI_MAP['success']} All checks passed[/bold green]\n\n"
            f"Total: {total_checks} check(s)",
            title="Check Complete"
        ))
    else:
        status = "Failed" if total_errors > 0 or (strict and total_warnings > 0) else "Has Warnings"
        color = "red" if total_errors > 0 or (strict and total_warnings > 0) else "yellow"
        emoji = EMOJI_MAP['error'] if total_errors > 0 or (strict and total_warnings > 0) else EMOJI_MAP['warning']
        console.print(Panel.fit(
            f"[bold {color}]{emoji} Check {status}[/bold {color}]\n\n"
            f"Total: {total_checks} check(s)\n"
            f"Errors: {total_errors}\n"
            f"Warnings: {total_warnings}",
            title="Check Complete"
        ))
        if strict and total_warnings > 0:
            console.print()
            console.print("[dim]Hint: In --strict mode, warnings are treated as failures[/dim]")

    # Return exit code
    if total_errors > 0 or (strict and total_warnings > 0):
        raise SystemExit(1)


@main.command()
@click.option("-c", "--config", default="project.yaml", help="Config file path")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format")
def health(config: str, as_json: bool):
    """Project health signal check"""
    import json as json_mod

    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[red]Config file not found: {config}[/red]")
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
        f"[bold {grade_color}]Grade: {grade} ({score:.0f}/100)[/bold {grade_color}]\n"
        f"CRITICAL: {report.critical_count}  WARNING: {report.warning_count}  INFO: {report.info_count}",
        title="Project Health"
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
# Multi-developer management commands (v0.5.0+)
# ============================================

@main.group()
def dev():
    """Multi-developer management commands

    Manage projects with multi-developer collaboration.
    """
    pass


@dev.command("whoami")
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
def dev_whoami(config: str):
    """Show current developer identity

    Examples:

        vibecollab dev whoami
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    dm = DeveloperManager(project_root, project_config)
    current_dev = dm.get_current_developer()
    identity_source = dm.get_identity_source()

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)

    # Friendly display for identity source
    source_display = {
        'local_switch': '[green]CLI switch[/green] (.vibecollab.local.yaml)',
        'env_var': '[yellow]Environment variable[/yellow] (VIBECOLLAB_DEVELOPER)',
        'git_username': 'Git username (git config user.name)',
        'system_user': 'System username',
    }.get(identity_source, identity_source)

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{current_dev}[/bold cyan]\n\n"
        f"Multi-developer mode: {'[green]Enabled[/green]' if multi_dev_enabled else '[yellow]Not enabled[/yellow]'}\n"
        f"Identity source: {source_display}",
        title="Current Developer"
    ))
    console.print()


@dev.command("list")
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
def dev_list(config: str):
    """List all developers

    Examples:

        vibecollab dev list
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} Multi-developer mode is not enabled[/yellow]")
        console.print("[dim]Set multi_developer.enabled: true in project.yaml[/dim]")
        raise SystemExit(1)

    dm = DeveloperManager(project_root, project_config)
    developers = dm.list_developers()
    current_dev = dm.get_current_developer()

    if not developers:
        console.print()
        console.print("[yellow]No developers yet[/yellow]")
        console.print("[dim]Use 'vibecollab init --multi-dev' to initialize a multi-developer project[/dim]")
        console.print()
        return

    table = Table(title="Developer List", show_header=True)
    table.add_column("Developer", style="cyan")
    table.add_column("Status")
    table.add_column("Last Updated")
    table.add_column("Update Count")

    for dev in developers:
        status_info = dm.get_developer_status(dev)
        is_current = " (current)" if dev == current_dev else ""
        status = f"{EMOJI_MAP['success']} Active{is_current}" if status_info['exists'] else f"{EMOJI_MAP['warning']} Not initialized"
        last_updated = status_info.get('last_updated', '-') or '-'
        if last_updated != '-' and len(last_updated) > 19:
            last_updated = last_updated[:19]  # Trim to datetime portion
        total_updates = str(status_info.get('total_updates', 0))

        table.add_row(dev, status, last_updated, total_updates)

    console.print()
    console.print(table)
    console.print()


@dev.command("status")
@click.argument("developer", required=False)
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
def dev_status(developer: Optional[str], config: str):
    """View developer status

    Examples:

        vibecollab dev status           # View all developers

        vibecollab dev status alice     # View a specific developer
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} Multi-developer mode is not enabled[/yellow]")
        raise SystemExit(1)

    dm = DeveloperManager(project_root, project_config)

    if developer:
        # Show specific developer
        developers = [developer]
    else:
        # Show all developers
        developers = dm.list_developers()

    if not developers:
        console.print()
        console.print("[yellow]No developers yet[/yellow]")
        console.print()
        return

    for dev in developers:
        context_file = dm.get_developer_context_file(dev)
        if context_file.exists():
            console.print()
            console.print(Panel.fit(
                f"[bold]{dev}[/bold]",
                title="Developer Status"
            ))
            console.print()

            # Read and display CONTEXT.md summary
            try:
                content = context_file.read_text(encoding='utf-8')
                # Show first 20 lines
                lines = content.split('\n')[:20]
                console.print('\n'.join(lines))
                if len(content.split('\n')) > 20:
                    console.print(f"\n[dim]... (more at {context_file})[/dim]")
            except Exception as e:
                console.print(f"[red]Read failed:[/red] {e}")

            console.print()
        else:
            console.print(f"[yellow]{EMOJI_MAP['warning']} Developer {dev} not initialized[/yellow]")


@dev.command("sync")
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
def dev_sync(config: str):
    """Manually trigger global CONTEXT aggregation

    Examples:

        vibecollab dev sync
    """
    from ..domain.developer import ContextAggregator

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} Multi-developer mode is not enabled[/yellow]")
        raise SystemExit(1)

    console.print()
    console.print("[cyan]Aggregating global CONTEXT...[/cyan]")

    try:
        aggregator = ContextAggregator(project_root, project_config)
        output_file = aggregator.generate_and_save()

        console.print(f"[green]{EMOJI_MAP['success']} Aggregation complete:[/green] {output_file}")
        console.print()
    except Exception as e:
        console.print(f"[red]Aggregation failed:[/red] {e}")
        raise SystemExit(1)


@dev.command("init")
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
@click.option("--developer", "-d", help="Developer name (auto-detect if empty)")
def dev_init(config: str, developer: Optional[str]):
    """Initialize current developer's context

    Examples:

        vibecollab dev init                 # Auto-detect current developer

        vibecollab dev init -d alice        # Initialize for alice
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} Multi-developer mode is not enabled[/yellow]")
        console.print("[dim]Set multi_developer.enabled: true in project.yaml[/dim]")
        raise SystemExit(1)

    dm = DeveloperManager(project_root, project_config)

    if developer is None:
        developer = dm.get_current_developer()

    console.print()
    console.print(f"[cyan]Initializing developer:[/cyan] {developer}")

    try:
        dm.init_developer_context(developer)
        context_file = dm.get_developer_context_file(developer)

        console.print(f"[green]{EMOJI_MAP['success']} Initialization complete:[/green]")
        console.print(f"  {BULLET} Context file: {context_file}")
        console.print()
    except Exception as e:
        console.print(f"[red]Initialization failed:[/red] {e}")
        raise SystemExit(1)


@dev.command("switch")
@click.argument("developer", required=False)
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
@click.option("--clear", is_flag=True, help="Clear switch, restore default identity")
def dev_switch(developer: Optional[str], config: str, clear: bool):
    """Switch current developer identity

    Select a developer context via CLI without modifying Git config or environment variables.
    The switch setting is persisted to the local config file (.vibecollab.local.yaml).

    Examples:

        vibecollab dev switch alice      # Switch to alice

        vibecollab dev switch            # Interactive developer selection

        vibecollab dev switch --clear    # Clear switch, restore default identity
    """
    from ..domain.developer import DeveloperManager

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} Multi-developer mode is not enabled[/yellow]")
        console.print("[dim]Set multi_developer.enabled: true in project.yaml[/dim]")
        raise SystemExit(1)

    dm = DeveloperManager(project_root, project_config)

    # Handle clear switch
    if clear:
        console.print()
        if dm.clear_switch():
            default_dev = dm.get_current_developer()
            console.print(f"[green]{EMOJI_MAP['success']} Switch setting cleared[/green]")
            console.print(f"  {BULLET} Current identity: [cyan]{default_dev}[/cyan] (detected via default strategy)")
        else:
            console.print("[red]Clear failed[/red]")
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
            console.print("[yellow]No developers yet[/yellow]")
            console.print("[dim]Use 'vibecollab dev init -d <name>' to initialize a new developer[/dim]")
            console.print()
            return

        console.print()
        console.print("[cyan]Select a developer to switch to:[/cyan]")
        console.print()

        for i, dev in enumerate(developers, 1):
            status_info = dm.get_developer_status(dev)
            is_current = " [green](current)[/green]" if dev == current_dev else ""
            last_update = status_info.get('last_updated', 'unknown')
            console.print(f"  {i}. [bold]{dev}[/bold]{is_current}")
            console.print(f"     Last updated: {last_update}")

        console.print()
        console.print("  0. [dim]Cancel[/dim]")
        console.print()

        # Read user selection
        try:
            choice = click.prompt("Enter number", type=int, default=0)
        except click.Abort:
            console.print("\n[dim]Cancelled[/dim]")
            return

        if choice == 0:
            console.print("[dim]Cancelled[/dim]")
            return

        if choice < 1 or choice > len(developers):
            console.print(f"[red]Invalid choice: {choice}[/red]")
            raise SystemExit(1)

        developer = developers[choice - 1]

    # Normalize developer name
    identity_config = project_config.get('multi_developer', {}).get('identity', {})
    if identity_config.get('normalize', True):
        developer = dm._normalize_developer_name(developer)

    # Check if developer exists
    if developer not in developers:
        console.print()
        console.print(f"[yellow]{EMOJI_MAP['warning']} Developer '{developer}' does not exist[/yellow]")
        console.print()

        # Ask whether to initialize
        create = click.confirm(f"Initialize context for '{developer}'?", default=True)
        if create:
            dm.init_developer_context(developer)
            console.print(f"[green]{EMOJI_MAP['success']} Initialized context for '{developer}'[/green]")
        else:
            console.print("[dim]Cancelled[/dim]")
            return

    # Execute switch
    console.print()
    if dm.switch_developer(developer):
        console.print(f"[green]{EMOJI_MAP['success']} Switched to developer: [bold cyan]{developer}[/bold cyan][/green]")
        console.print()
        console.print(f"  {BULLET} Context file: {dm.get_developer_context_file(developer)}")
        console.print(f"  {BULLET} Persisted to: .vibecollab.local.yaml")
        console.print()
        console.print("[dim]Hint: Use 'vibecollab dev switch --clear' to restore default identity[/dim]")
    else:
        console.print("[red]Switch failed[/red]")
        raise SystemExit(1)

    console.print()


@dev.command("conflicts")
@click.option("--config", "-c", default="project.yaml", help="Project config file path")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed conflict info")
@click.option("--between", nargs=2, help="Detect conflicts between two developers (e.g. --between alice bob)")
def dev_conflicts(config: str, verbose: bool, between: Optional[Tuple[str, str]]):
    """Detect cross-developer work conflicts

    Detects potential conflicts between multiple developers, including file conflicts,
    task conflicts, dependency conflicts, etc.

    Examples:

        vibecollab dev conflicts                 # Detect all developer conflicts

        vibecollab dev conflicts -v              # Show detailed info

        vibecollab dev conflicts --between alice bob  # Detect conflicts between two specific developers
    """
    from ..domain.conflict_detector import ConflictDetector

    config_path = Path(config)
    project_root = config_path.parent

    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} Multi-developer mode not enabled[/yellow]")
        console.print("[dim]Set multi_developer.enabled: true in project.yaml[/dim]")
        raise SystemExit(1)

    console.print()
    console.print("[cyan]Detecting cross-developer conflicts...[/cyan]")
    console.print()

    try:
        detector = ConflictDetector(project_root, project_config)

        # Execute conflict detection
        conflicts = detector.detect_all_conflicts(
            target_developer=None,
            between_developers=between
        )

        # Generate and display report
        report = detector.generate_conflict_report(conflicts, verbose=verbose)
        console.print(report)

        # Return non-zero exit code if conflicts found
        if conflicts:
            raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]Conflict detection failed:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise SystemExit(1)




if __name__ == "__main__":
    main()
