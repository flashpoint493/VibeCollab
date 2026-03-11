"""
Guide CLI commands -- AI Agent onboarding and action suggestions

Provides three core commands for AI Agents to understand and drive project development:

Commands:
    vibecollab onboard              Onboarding context guide for AI (Rich panel)
    vibecollab prompt               Generate LLM-ready context prompt text
    vibecollab next                 Next-step action suggestions after modifications
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import click
import yaml
from rich.panel import Panel
from rich.table import Table

from .._compat import BULLET, EMOJI, safe_console
from ..i18n import _

logger = logging.getLogger(__name__)

console = safe_console()


def _search_related_insights(
    project_root: Path, query_text: str, top_k: int = 5
) -> List[Dict]:
    """Search for Insights related to query text from vector index

    Returns [{id, title, tags, score}] list, or empty list if index does not exist.
    """
    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    if not db_path.exists():
        return []

    try:
        from ..insight.embedder import Embedder, EmbedderConfig
        from ..search.vector_store import VectorStore

        # Infer dimensions from existing DB
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT dimensions FROM vectors LIMIT 1"
        ).fetchone()
        conn.close()

        if not row:
            return []
        dimensions = row[0]

        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=dimensions))
        store = VectorStore(db_path=db_path, dimensions=dimensions)

        query_vector = embedder.embed_text(query_text)
        results = store.search(
            query_vector, top_k=top_k, source_type="insight"
        )
        store.close()

        related = []
        for r in results:
            meta = r.metadata or {}
            related.append({
                "id": r.doc_id.replace("insight:", ""),
                "title": meta.get("title", ""),
                "tags": meta.get("tags", []),
                "score": round(r.score, 3),
            })
        return related

    except Exception as e:
        logger.debug("Semantic search for Insight failed: %s", e)
        return []


def _safe_load_yaml(path: Path) -> Optional[dict]:
    """Safely load YAML, return None on failure"""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None


def _safe_read_text(path: Path, max_lines: int = 0) -> str:
    """Safely read a text file"""
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
        if max_lines > 0:
            lines = text.splitlines()
            return "\n".join(lines[:max_lines])
        return text
    except Exception:
        return ""


def _get_git_uncommitted(project_root: Path) -> List[str]:
    """Get list of uncommitted files"""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=project_root, capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return [line.strip() for line in result.stdout.strip().splitlines()]
        return []
    except BaseException:
        return []


def _get_git_diff_files(project_root: Path) -> List[str]:
    """Get list of git diff file names"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=project_root, capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()
        return []
    except BaseException:
        return []


def _get_recent_decisions(decisions_path: Path, count: int = 3) -> List[str]:
    """Extract the last N decision titles from DECISIONS.md"""
    text = _safe_read_text(decisions_path)
    if not text:
        return []
    decisions = []
    for line in text.splitlines():
        if line.startswith("### DECISION-"):
            decisions.append(line.replace("### ", "").strip())
    return decisions[-count:] if decisions else []


def _extract_pending_from_roadmap(roadmap_path: Path) -> List[str]:
    """Extract incomplete items (- [ ]) from ROADMAP.md"""
    text = _safe_read_text(roadmap_path)
    if not text:
        return []
    pending = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            pending.append(stripped[5:].strip())
    return pending


def _check_linked_groups_freshness(
    project_root: Path, config: dict
) -> List[Dict]:
    """Check freshness of linked document groups, return groups needing sync"""
    doc_config = config.get("documentation", {})
    consistency_config = doc_config.get("consistency", {})
    if not consistency_config.get("enabled", False):
        return []

    linked_groups = consistency_config.get("linked_groups", [])
    stale_groups = []

    for group in linked_groups:
        group_name = group.get("name", "")
        files = group.get("files", [])
        threshold_minutes = group.get("threshold_minutes", 15)

        if len(files) < 2:
            continue

        # Collect file mtimes
        mtimes = {}
        for f in files:
            full_path = project_root / f
            if full_path.exists():
                mtimes[f] = datetime.fromtimestamp(full_path.stat().st_mtime)

        if len(mtimes) < 2:
            continue

        sorted_files = sorted(mtimes.items(), key=lambda x: x[1], reverse=True)
        newest_file, newest_time = sorted_files[0]

        # Only care about groups modified within 24h
        hours_since = (datetime.now() - newest_time).total_seconds() / 3600
        if hours_since > 24:
            continue

        stale = []
        for f, t in sorted_files[1:]:
            diff_min = (newest_time - t).total_seconds() / 60
            if diff_min > threshold_minutes:
                stale.append((f, int(diff_min)))

        if stale:
            stale_groups.append({
                "group": group_name,
                "leader": newest_file,
                "stale": stale,
            })

    return stale_groups


def _get_read_files_list(config: dict) -> List[str]:
    """Get dialogue_protocol.on_start.read_files"""
    return config.get("dialogue_protocol", {}).get("on_start", {}).get("read_files", [])


def _get_update_files_list(config: dict) -> List[str]:
    """Get dialogue_protocol.on_end.update_files"""
    return config.get("dialogue_protocol", {}).get("on_end", {}).get("update_files", [])


def _suggest_commit_message(diff_files: List[str]) -> str:
    """Suggest commit message prefix based on diff file list"""
    has_src = any(f.startswith("src/") for f in diff_files)
    has_test = any(f.startswith("tests/") for f in diff_files)
    has_doc = any(
        f.startswith("docs/") or f.endswith(".md") or f == "llms.txt"
        for f in diff_files
    )
    has_config = any(
        f in ("project.yaml", "pyproject.toml", ".gitignore")
        for f in diff_files
    )
    has_schema = any(f.startswith("schema/") for f in diff_files)

    if has_src and has_test:
        return "feat:"
    elif has_test and not has_src:
        return "test:"
    elif has_doc and not has_src:
        return "docs:"
    elif has_config and not has_src:
        return "chore:"
    elif has_schema:
        return "design:"
    elif has_src:
        return "feat:"
    return "chore:"


def _collect_project_context(
    config_path: Path, developer: Optional[str] = None
) -> Dict:
    """Collect project context data (shared by onboard and prompt)

    Returns:
        Dict containing: project_root, project_name, project_version, project_desc,
        context_text, recent_decisions, pending_roadmap, uncommitted,
        read_files, developer_info, key_files, insight_count, top_insights,
        project_config
    """
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    project_config = _safe_load_yaml(config_path)
    if not project_config:
        return {}

    proj = project_config.get("project", {})

    # Developer info
    developer_info = None
    if developer:
        dev_context_path = project_root / "docs" / "developers" / developer / "CONTEXT.md"
        dev_meta_path = project_root / "docs" / "developers" / developer / ".metadata.yaml"
        developer_info = {
            "id": developer,
            "context": _safe_read_text(dev_context_path, max_lines=20),
            "metadata": _safe_load_yaml(dev_meta_path),
        }

    # Insight
    insight_count = 0
    top_insights: List[Dict] = []
    insights_dir = project_root / ".vibecollab" / "insights"
    if insights_dir.exists():
        insight_files = sorted(insights_dir.glob("INS-*.yaml"), reverse=True)
        insight_count = len(insight_files)
        for ins_file in insight_files[:5]:
            ins_data = _safe_load_yaml(ins_file)
            if ins_data:
                top_insights.append({
                    "id": ins_data.get("id", ins_file.stem),
                    "title": ins_data.get("title", ""),
                    "tags": ins_data.get("tags", []),
                })

    # Task overview
    active_tasks: List[Dict] = []
    task_summary: Dict = {"total": 0, "todo": 0, "in_progress": 0, "review": 0, "done": 0}
    try:
        from ..domain.task_manager import TaskManager
        tm = TaskManager(project_root=project_root)
        all_tasks = tm.list_tasks()
        task_summary["total"] = len(all_tasks)
        for t in all_tasks:
            status_key = t.status.lower()
            if status_key in task_summary:
                task_summary[status_key] += 1
            if t.status != "DONE":
                active_tasks.append({
                    "id": t.id,
                    "feature": t.feature,
                    "status": t.status,
                    "assignee": t.assignee or "-",
                })
    except Exception:
        pass

    # EventLog recent events
    recent_events: List[Dict] = []
    try:
        from ..domain.event_log import EventLog
        el = EventLog(project_root=project_root)
        for evt in el.read_recent(5):
            recent_events.append({
                "event_type": evt.event_type,
                "summary": evt.summary,
                "actor": evt.actor,
                "timestamp": evt.timestamp[:19] if evt.timestamp else "",
            })
    except Exception:
        pass

    # Semantic search: match related Insights from current task description
    context_text = _safe_read_text(project_root / "docs" / "CONTEXT.md", max_lines=30)
    related_insights: List[Dict] = []

    # Build query text: prefer developer context, otherwise use project CONTEXT.md
    query_text = ""
    if developer_info and developer_info.get("context"):
        query_text = developer_info["context"]
    elif context_text:
        query_text = context_text

    if query_text and insight_count > 0:
        related_insights = _search_related_insights(project_root, query_text)

    return {
        "project_root": project_root,
        "project_config": project_config,
        "project_name": proj.get("name", "Unknown"),
        "project_version": proj.get("version", "Unknown"),
        "project_desc": proj.get("description", ""),
        "context_text": context_text,
        "recent_decisions": _get_recent_decisions(project_root / "docs" / "DECISIONS.md", 3),
        "pending_roadmap": _extract_pending_from_roadmap(project_root / "docs" / "ROADMAP.md"),
        "uncommitted": _get_git_uncommitted(project_root),
        "read_files": _get_read_files_list(project_config),
        "developer_info": developer_info,
        "key_files": project_config.get("documentation", {}).get("key_files", []),
        "insight_count": insight_count,
        "top_insights": top_insights,
        "related_insights": related_insights,
        "active_tasks": active_tasks,
        "task_summary": task_summary,
        "recent_events": recent_events,
    }


# ============================================================
# vibecollab onboard
# ============================================================

@click.command()
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--developer", "-d", default=None, help=_("Developer ID"))
@click.option("--json", "as_json", is_flag=True, help=_("JSON output"))
def onboard(config: str, developer: Optional[str], as_json: bool):
    """Onboarding context guide for AI Agent

    Outputs project overview, current progress, TODOs, and files to read,
    so AI can understand project state without guessing and start working.

    Examples:

        vibecollab onboard                  # Standard onboarding

        vibecollab onboard -d dev            # Role-specific perspective

        vibecollab onboard --json           # Machine-readable output
    """
    config_path = Path(config)
    ctx = _collect_project_context(config_path, developer)
    if not ctx:
        console.print("[red]Error:[/red] Cannot load project.yaml")
        raise SystemExit(1)

    project_root = ctx["project_root"]
    project_name = ctx["project_name"]
    project_version = ctx["project_version"]
    project_desc = ctx["project_desc"]
    context_text = ctx["context_text"]
    recent_decisions = ctx["recent_decisions"]
    pending_roadmap = ctx["pending_roadmap"]
    uncommitted = ctx["uncommitted"]
    read_files = ctx["read_files"]
    developer_info = ctx["developer_info"]
    key_files = ctx["key_files"]
    insight_count = ctx["insight_count"]
    top_insights = ctx["top_insights"]
    related_insights = ctx.get("related_insights", [])
    active_tasks = ctx.get("active_tasks", [])
    task_summary = ctx.get("task_summary", {})
    recent_events = ctx.get("recent_events", [])

    # === Output ===
    if as_json:
        output = {
            "project": {"name": project_name, "version": project_version, "description": project_desc},
            "read_files": read_files,
            "recent_decisions": recent_decisions,
            "pending_roadmap": pending_roadmap,
            "uncommitted_changes": len(uncommitted),
            "insight_count": insight_count,
            "top_insights": top_insights,
            "related_insights": related_insights,
            "key_files": [kf.get("path", "") for kf in key_files],
            "task_summary": task_summary,
            "active_tasks": active_tasks,
            "recent_events": recent_events,
        }
        if developer_info:
            output["developer"] = {
                "id": developer_info["id"],
                "has_context": bool(developer_info["context"]),
                "has_metadata": developer_info["metadata"] is not None,
            }
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # Rich output
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{project_name}[/bold cyan] {project_version}\n"
        f"[dim]{project_desc}[/dim]",
        title="Project Overview",
    ))

    # Files to read
    console.print()
    console.print("[bold]Files you should read first:[/bold]")
    for f in read_files:
        full_path = project_root / f
        exists = full_path.exists()
        status = "[green]Exists[/green]" if exists else "[red]Missing[/red]"
        console.print(f"  {status}  {f}")

    # Current progress
    if context_text:
        console.print()
        console.print(Panel(context_text, title="Current Progress (docs/CONTEXT.md)", border_style="blue"))

    # Developer info
    if developer_info:
        console.print()
        if developer_info["context"]:
            console.print(Panel(
                developer_info["context"],
                title=f"Developer {developer} Context",
                border_style="cyan"
            ))
        if developer_info["metadata"]:
            meta = developer_info["metadata"]
            tags = meta.get("tags", [])
            contributed = meta.get("contributed", [])
            bookmarks = meta.get("bookmarks", [])
            if tags or contributed or bookmarks:
                console.print(f"  [dim]Tags:[/dim] {', '.join(tags[:10])}")
                console.print(f"  [dim]Contributed:[/dim] {', '.join(contributed[:5])}")
                console.print(f"  [dim]Bookmarks:[/dim] {', '.join(bookmarks[:5])}")

    # Recent decisions
    if recent_decisions:
        console.print()
        console.print("[bold]Recent Decisions:[/bold]")
        for d in recent_decisions:
            console.print(f"  {BULLET} {d}")

    # Roadmap TODOs
    if pending_roadmap:
        console.print()
        console.print("[bold yellow]Roadmap TODOs:[/bold yellow]")
        for item in pending_roadmap[:10]:
            console.print(f"  [ ] {item}")

    # Uncommitted changes
    if uncommitted:
        console.print()
        console.print(f"[bold yellow]Uncommitted Changes: {len(uncommitted)} file(s)[/bold yellow]")
        for line in uncommitted[:8]:
            console.print(f"  {line}")
        if len(uncommitted) > 8:
            console.print(f"  [dim]... {len(uncommitted) - 8} more[/dim]")

    # Insight stats + Top-N summary
    if insight_count > 0:
        console.print()
        console.print(f"[bold]Insight Distillation: {insight_count} entries[/bold]")
        if top_insights:
            for ins in top_insights:
                tags_str = ", ".join(ins["tags"][:4]) if ins["tags"] else ""
                tag_label = f" [dim]({tags_str})[/dim]" if tags_str else ""
                console.print(f"  {BULLET} {ins['id']}: {ins['title']}{tag_label}")
            if insight_count > 5:
                console.print(f"  [dim]... {insight_count - 5} more (vibecollab insight list)[/dim]")
        else:
            console.print(f"  [dim]vibecollab insight list to see all[/dim]")

    # Related Insights for current task (semantic match)
    if related_insights:
        console.print()
        ri_lines = []
        for ri in related_insights:
            tags_str = ", ".join(ri["tags"][:4]) if ri.get("tags") else ""
            tag_part = f" [dim]({tags_str})[/dim]" if tags_str else ""
            score_label = f"[dim]{ri['score']:.2f}[/dim]" if ri.get("score") else ""
            ri_lines.append(
                f"  {BULLET} [bold]{ri['id']}[/bold]: {ri.get('title', '')}{tag_part}  {score_label}"
            )
        console.print(Panel(
            "\n".join(ri_lines),
            title="Insights Related to Current Task (Semantic Match)",
            border_style="magenta",
        ))

    # Task overview
    total_tasks = task_summary.get("total", 0)
    if total_tasks > 0:
        console.print()
        ts = task_summary
        console.print(
            f"[bold]Task Overview:[/bold] "
            f"TODO={ts.get('todo', 0)} "
            f"IN_PROGRESS={ts.get('in_progress', 0)} "
            f"REVIEW={ts.get('review', 0)} "
            f"DONE={ts.get('done', 0)} "
            f"(total {total_tasks})"
        )
        if active_tasks:
            for at in active_tasks[:8]:
                status_style = {
                    "TODO": "dim", "IN_PROGRESS": "yellow", "REVIEW": "cyan",
                }.get(at["status"], "")
                console.print(
                    f"  {BULLET} {at['id']}  [{status_style}]{at['status']:12s}[/{status_style}]  "
                    f"{at['feature']}  (@{at['assignee']})"
                )
            if len(active_tasks) > 8:
                console.print(f"  [dim]... {len(active_tasks) - 8} more active tasks[/dim]")

    # Recent EventLog events
    if recent_events:
        console.print()
        evt_lines = []
        for evt in recent_events:
            evt_lines.append(
                f"  {BULLET} [dim]{evt['timestamp']}[/dim]  "
                f"{evt['summary']}  [dim](@{evt['actor']})[/dim]"
            )
        console.print(Panel(
            "\n".join(evt_lines),
            title="Recent Events (EventLog)",
            border_style="dim",
        ))

    # Key files list
    console.print()
    table = Table(title="Key Files", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Purpose")
    table.add_column("Status")
    for kf in key_files:
        path = kf.get("path", "")
        purpose = kf.get("purpose", "")
        exists = (project_root / path).exists()
        status = f"[green]{EMOJI['check']}[/green]" if exists else f"[red]{EMOJI['cross']}[/red]"
        table.add_row(path, purpose, status)
    console.print(table)

    # Final guidance suggestions
    console.print()
    suggestions = []
    if uncommitted:
        suggestions.append("Uncommitted changes found -> run `git status` to check if commit is needed")
    if pending_roadmap:
        suggestions.append(f"Roadmap has {len(pending_roadmap)} pending items -> check `docs/ROADMAP.md`")
    if not developer:
        suggestions.append("Use `vibecollab onboard -d <your-ID>` to see your personal context")

    suggestions.append("After modifying files, use `vibecollab next` for next-step suggestions")
    suggestions.append("Use `vibecollab check` to run consistency self-check (insights included by default)")

    console.print(Panel(
        "\n".join(f"  {BULLET} {s}" for s in suggestions),
        title="Suggested Next Steps",
        border_style="green"
    ))


# ============================================================
# vibecollab prompt -- Generate LLM context prompt
# ============================================================

# Protocol section to CONTRIBUTING_AI.md heading mapping
_SECTION_MAP = {
    "protocol": [
        "# I. Core Philosophy",
        "# III. Decision Classification System",
        "## 4.2 Standard Dialogue Flow",
    ],
    "context": [],       # Dynamically generated, not extracted from file
    "insight": [
        "# Insight Accumulation Workflow",
    ],
    "roles": [
        "# II. Role Definitions",
    ],
    "testing": [
        "# V. Testing System",
    ],
    "git": [
        "## 4.3 Git Collaboration Standards",
    ],
}

_ALL_SECTIONS = ["protocol", "context", "insight"]


def _extract_md_sections(text: str, start_headings: List[str]) -> str:
    """Extract content from Markdown text starting from specified headings to next same-level heading"""
    lines = text.splitlines()
    result_parts: List[str] = []

    for start_heading in start_headings:
        # Determine heading level
        heading_level = len(start_heading) - len(start_heading.lstrip("#"))
        capturing = False
        section_lines: List[str] = []

        for line in lines:
            if line.strip() == start_heading.strip():
                capturing = True
                section_lines = [line]
                continue

            if capturing:
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    line_level = len(stripped) - len(stripped.lstrip("#"))
                    if line_level <= heading_level:
                        break
                section_lines.append(line)

        if section_lines:
            result_parts.append("\n".join(section_lines))

    return "\n\n".join(result_parts)


def _build_prompt_text(
    ctx: Dict,
    sections: List[str],
    compact: bool = False,
) -> str:
    """Build LLM prompt plain text"""
    parts: List[str] = []
    project_root = ctx["project_root"]

    # Header
    parts.append(f"# Project Context: {ctx['project_name']} {ctx['project_version']}")
    parts.append(f"> {ctx['project_desc']}")
    parts.append("")

    # Protocol section -- extract key sections from CONTRIBUTING_AI.md
    if "protocol" in sections:
        contrib_path = project_root / "CONTRIBUTING_AI.md"
        if contrib_path.exists():
            contrib_text = _safe_read_text(contrib_path)
            headings = _SECTION_MAP["protocol"]
            if not compact:
                # Full mode: add more sections
                headings = headings + _SECTION_MAP.get("roles", []) + _SECTION_MAP.get("git", [])
            extracted = _extract_md_sections(contrib_text, headings)
            if extracted:
                parts.append("---")
                parts.append("## Collaboration Protocol")
                parts.append(extracted)
                parts.append("")

    # Context section
    if "context" in sections:
        parts.append("---")
        parts.append("## Current Status")
        parts.append("")

        if ctx["context_text"]:
            parts.append(ctx["context_text"])
            parts.append("")

        dev_info = ctx.get("developer_info")
        if dev_info and dev_info.get("context"):
            parts.append(f"### Developer: {dev_info['id']}")
            parts.append(dev_info["context"])
            parts.append("")

        if ctx["recent_decisions"]:
            parts.append("### Recent Decisions")
            for d in ctx["recent_decisions"]:
                parts.append(f"- {d}")
            parts.append("")

        if not compact and ctx["pending_roadmap"]:
            parts.append("### Roadmap TODOs")
            for item in ctx["pending_roadmap"][:10]:
                parts.append(f"- [ ] {item}")
            parts.append("")

        if ctx["uncommitted"]:
            parts.append(f"### Uncommitted Changes: {len(ctx['uncommitted'])} file(s)")
            parts.append("")

    # Insight section
    if "insight" in sections and ctx["top_insights"]:
        parts.append("---")
        parts.append(f"## Insight Distillation ({ctx['insight_count']} entries)")
        parts.append("")
        for ins in ctx["top_insights"]:
            tags_str = ", ".join(ins["tags"][:4]) if ins["tags"] else ""
            tag_part = f" ({tags_str})" if tags_str else ""
            parts.append(f"- **{ins['id']}**: {ins['title']}{tag_part}")
        if ctx["insight_count"] > 5:
            parts.append(f"- ... {ctx['insight_count'] - 5} more")
        parts.append("")
        parts.append("> Use `vibecollab insight search --tags <keyword>` to search related experiences")
        parts.append("")

        # In non-compact mode, append Insight workflow description
        if not compact:
            contrib_path = project_root / "CONTRIBUTING_AI.md"
            if contrib_path.exists():
                contrib_text = _safe_read_text(contrib_path)
                insight_section = _extract_md_sections(contrib_text, _SECTION_MAP["insight"])
                if insight_section:
                    parts.append(insight_section)
                    parts.append("")

    # Footer
    parts.append("---")
    parts.append("*Auto-generated by `vibecollab prompt`*")

    return "\n".join(parts)


@click.command("prompt")
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--developer", "-d", default=None, help=_("Developer ID"))
@click.option("--compact", is_flag=True, help=_("Compact mode (core protocol + state only)"))
@click.option(
    "--sections", "-s", default=None,
    help=_("Select sections, comma separated (protocol,context,insight,roles,testing,git)")
)
@click.option("--copy", "to_clipboard", is_flag=True, help=_("Copy to clipboard"))
def prompt_cmd(
    config: str,
    developer: Optional[str],
    compact: bool,
    sections: Optional[str],
    to_clipboard: bool,
):
    """Generate LLM-ready context prompt

    Outputs plain Markdown text containing collaboration protocol summary,
    project current status, Insight experiences, etc. Can be directly
    copied and pasted into any LLM conversation window.

    Examples:

        vibecollab prompt                     # Full prompt

        vibecollab prompt --compact           # Compact version

        vibecollab prompt --copy              # Copy directly to clipboard

        vibecollab prompt -d dev              # Include role context

        vibecollab prompt -s protocol,context # Only protocol + status
    """
    config_path = Path(config)
    ctx = _collect_project_context(config_path, developer)
    if not ctx:
        console.print("[red]Error:[/red] Cannot load project.yaml")
        raise SystemExit(1)

    # Parse sections
    if sections:
        selected = [s.strip() for s in sections.split(",") if s.strip()]
    else:
        selected = list(_ALL_SECTIONS)

    text = _build_prompt_text(ctx, selected, compact=compact)

    if to_clipboard:
        try:
            import subprocess as _sp
            process = _sp.Popen(["clip"], stdin=_sp.PIPE, shell=True)
            process.communicate(text.encode("utf-16-le"))
            token_estimate = len(text) // 4
            console.print(
                f"[green]OK[/green] Prompt copied to clipboard "
                f"(~{token_estimate} tokens, {len(text)} chars)"
            )
        except Exception:
            click.echo(text)
            console.print("[yellow]Warning: clipboard copy failed, output to stdout[/yellow]")
    else:
        click.echo(text)


# ============================================================
# Insight distillation prompt helper
# ============================================================

def _check_insight_opportunity(project_root: Path, diff_files: List[str]) -> Optional[str]:
    """Check if current workspace has signals worth distilling into an Insight.

    Returns a prompt reason string, or None if no prompt is needed.
    """
    if not diff_files:
        return None

    # Signal 1: Changes involve multiple file types -> possible cross-module integration experience
    extensions = {Path(f).suffix for f in diff_files if Path(f).suffix}
    multi_type = len(extensions) >= 3

    # Signal 2: Changes involve test files -> possible bug fix or new pattern discovery
    has_test_changes = any("test" in f.lower() for f in diff_files)

    # Signal 3: Changes involve config/CI files -> possible tool/workflow experience
    config_patterns = (".yml", ".yaml", ".toml", ".cfg", ".ini", ".json")
    has_config_changes = any(Path(f).suffix in config_patterns for f in diff_files)

    # Signal 4: Large number of changes -> possible important refactor or feature
    large_changeset = len(diff_files) >= 8

    # Signal 5: .vibecollab directory has no Insight yet -> guide first distillation
    insights_dir = project_root / ".vibecollab" / "insights"
    no_insights_yet = not insights_dir.exists() or not list(insights_dir.glob("INS-*.yaml"))

    reasons = []
    if no_insights_yet:
        reasons.append("No Insights in project yet, suggest starting to accumulate experiences")
    if multi_type and has_test_changes:
        reasons.append("Changes involve multiple file types + tests, may have debug/integration experience worth recording")
    elif has_test_changes:
        reasons.append("Changes involve test files, may have discovered a bug or new test pattern")
    elif multi_type:
        reasons.append("Changes involve multiple file types, may have cross-module integration experience")
    if has_config_changes:
        reasons.append("Changes involve config files, may have tool/workflow experience")
    if large_changeset and not reasons:
        reasons.append(f"This change involves {len(diff_files)} files, suggest reviewing for experiences worth distilling")

    if not reasons:
        return None

    return "; ".join(reasons)


# ============================================================
# vibecollab next
# ============================================================

@click.command()
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option("--json", "as_json", is_flag=True, help=_("JSON output"))
def next_step(config: str, as_json: bool):
    """Next-step action suggestions after modifications

    Based on current workspace state (git diff, file mtime, linked_groups config),
    generates specific action suggestions: which documents need syncing,
    suggested commit message, what to do next.

    Examples:

        vibecollab next                     # View action suggestions

        vibecollab next --json              # Machine-readable output
    """
    config_path = Path(config)
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    project_config = _safe_load_yaml(config_path)
    if not project_config:
        console.print("[red]Error:[/red] Cannot load project.yaml")
        raise SystemExit(1)

    # === 1. Git status ===
    uncommitted = _get_git_uncommitted(project_root)
    diff_files = _get_git_diff_files(project_root)

    # === 2. Linked document sync check ===
    stale_groups = _check_linked_groups_freshness(project_root, project_config)

    # === 3. Files to update at end of dialogue ===
    update_files = _get_update_files_list(project_config)
    check_config = project_config.get("protocol_check", {}).get("checks", {}).get("documentation", {})
    threshold_hours = check_config.get("update_threshold_hours", 0.25)
    overdue_update_files = []
    for f in update_files:
        full_path = project_root / f
        if full_path.exists():
            mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
            hours_since = (datetime.now() - mtime).total_seconds() / 3600
            if hours_since > threshold_hours:
                overdue_update_files.append((f, int(hours_since * 60)))

    # === 4. Commit message suggestion ===
    suggested_prefix = _suggest_commit_message(diff_files) if diff_files else None

    # === 5. Missing key files ===
    key_files = project_config.get("documentation", {}).get("key_files", [])
    missing_key_files = []
    for kf in key_files:
        path = kf.get("path", "")
        if path and not (project_root / path).exists():
            missing_key_files.append(path)

    # === 6. Build action list ===
    actions: List[Dict] = []
    priority = 0

    # P0: Linked document sync
    for group in stale_groups:
        for f, diff_min in group["stale"]:
            priority += 1
            actions.append({
                "priority": f"P0-{priority}",
                "type": "sync_document",
                "action": f"Sync update {f}",
                "reason": f"{group['leader']} modified, {f} is {diff_min} min behind",
                "group": group["group"],
            })

    # P1: Files to update at end of dialogue
    for f, minutes in overdue_update_files:
        priority += 1
        actions.append({
            "priority": f"P1-{priority}",
            "type": "update_document",
            "action": f"Update {f}",
            "reason": f"Protocol requires update at dialogue end, overdue by {minutes} min",
        })

    # P1: Uncommitted changes
    if uncommitted:
        priority += 1
        prefix = suggested_prefix or "feat:"
        actions.append({
            "priority": f"P1-{priority}",
            "type": "git_commit",
            "action": f"Commit changes ({len(uncommitted)} files)",
            "reason": "Uncommitted changes exist",
            "suggestion": f'git commit -m "{prefix} <description>"',
        })

    # P2: Missing key files
    for f in missing_key_files:
        priority += 1
        actions.append({
            "priority": f"P2-{priority}",
            "type": "create_file",
            "action": f"Create {f}",
            "reason": "Declared in documentation.key_files but does not exist",
        })

    # P1~P2: Task status recommended actions
    try:
        from ..domain.task_manager import TaskManager
        tm = TaskManager(project_root=project_root)
        all_tasks = tm.list_tasks()

        review_tasks = [t for t in all_tasks if t.status == "REVIEW"]
        if review_tasks:
            for t in review_tasks[:3]:
                priority += 1
                actions.append({
                    "priority": f"P1-{priority}",
                    "type": "task_solidify",
                    "action": f"Solidify task {t.id}: {t.feature}",
                    "reason": f"Task is in REVIEW status, can attempt solidification",
                    "suggestion": f"vibecollab task solidify {t.id}",
                })

        # Check tasks blocked by dependencies
        blocked_tasks = []
        for t in all_tasks:
            if t.status == "DONE":
                continue
            for dep_id in (t.dependencies or []):
                dep = tm.get_task(dep_id)
                if dep and dep.status != "DONE":
                    blocked_tasks.append((t, dep_id))
                    break
        if blocked_tasks:
            for t, dep_id in blocked_tasks[:2]:
                priority += 1
                actions.append({
                    "priority": f"P2-{priority}",
                    "type": "task_blocked",
                    "action": f"Task {t.id} blocked by {dep_id}",
                    "reason": f"Dependency {dep_id} not yet completed",
                    "suggestion": f"vibecollab task show {dep_id}",
                })

        # TODO backlog alert
        todo_count = sum(1 for t in all_tasks if t.status == "TODO")
        if todo_count > 3:
            priority += 1
            actions.append({
                "priority": f"P2-{priority}",
                "type": "task_backlog",
                "action": f"{todo_count} TODO tasks in backlog",
                "reason": "Suggest starting to process or split tasks",
                "suggestion": "vibecollab task list --status TODO",
            })
    except Exception:
        pass

    # P2: Insight distillation prompt
    insight_prompt = _check_insight_opportunity(project_root, diff_files)
    if insight_prompt:
        priority += 1
        actions.append({
            "priority": f"P2-{priority}",
            "type": "insight_review",
            "action": "Check if there are experiences worth distilling (Insight)",
            "reason": insight_prompt,
            "suggestion": 'vibecollab insight add --title "<title>" --tags "<tags>" --category <category> --body "<experience description>"',
        })

    # P3: Suggest running check
    if actions:
        priority += 1
        actions.append({
            "priority": f"P3-{priority}",
            "type": "run_check",
            "action": "Run vibecollab check",
            "reason": "Suggest running consistency self-check after completing above actions (insights included by default)",
        })

    # === Output ===
    if as_json:
        output = {
            "uncommitted_count": len(uncommitted),
            "diff_files": diff_files,
            "stale_groups": stale_groups,
            "overdue_update_files": [{"file": f, "minutes_overdue": m} for f, m in overdue_update_files],
            "suggested_commit_prefix": suggested_prefix,
            "missing_key_files": missing_key_files,
            "actions": actions,
        }
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    console.print()

    if not actions:
        console.print(Panel.fit(
            "[bold green]All clear, no additional actions needed[/bold green]\n\n"
            "[dim]Workspace clean, linked documents synced, no overdue files.[/dim]",
            title="Next Step"
        ))
        return

    console.print(Panel.fit(
        f"[bold]Found {len(actions)} pending items[/bold]",
        title="Next Step"
    ))
    console.print()

    # Display grouped by priority
    for action in actions:
        prio = action["priority"]
        if prio.startswith("P0"):
            style = "bold red"
            label = "URGENT"
        elif prio.startswith("P1"):
            style = "bold yellow"
            label = "IMPORTANT"
        elif prio.startswith("P2"):
            style = "yellow"
            label = "SUGGEST"
        else:
            style = "dim"
            label = "HINT"

        console.print(f"  [{style}][{label}][/{style}] {action['action']}")
        console.print(f"         [dim]Reason: {action['reason']}[/dim]")
        if "suggestion" in action:
            console.print(f"         [cyan]-> {action['suggestion']}[/cyan]")
        if "group" in action:
            console.print(f"         [dim]Linked group: {action['group']}[/dim]")
        console.print()

    # Diff files overview
    if diff_files:
        console.print("[bold]Changed files:[/bold]")
        for f in diff_files[:15]:
            console.print(f"  {f}")
        if len(diff_files) > 15:
            console.print(f"  [dim]... {len(diff_files) - 15} more[/dim]")

        if suggested_prefix:
            console.print()
            console.print(f"[dim]Suggested commit prefix: {suggested_prefix}[/dim]")
