"""
VibeCollab MCP Server -- Model Context Protocol integration

Makes VibeCollab a "protocol backend" for AI IDEs like Cline/Cursor/CodeBuddy,
turning "manual copy-paste" into "IDE auto-reads protocol".

Features:
    - Tools: insight_search, insight_add, check, onboard, next, task_list
    - Resources: CONTRIBUTING_AI.md, CONTEXT.md, DECISIONS.md, ROADMAP.md, Insight YAML
    - Prompts: Context injection templates at conversation start

Dependencies:
    pip install vibe-collab[mcp]

Usage:
    vibecollab mcp serve                # stdio mode (recommended, IDE direct connect)
    vibecollab mcp serve --transport sse # SSE mode (remote debug)
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _find_project_root(start: Optional[Path] = None) -> Path:
    """Search upward for a directory containing project.yaml"""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "project.yaml").exists():
            return parent
    return current


def _safe_read_text(path: Path, encoding: str = "utf-8") -> str:
    """Safely read file text; returns empty string if file does not exist"""
    try:
        return path.read_text(encoding=encoding)
    except (OSError, UnicodeDecodeError):
        return ""


def _safe_load_yaml(path: Path) -> Dict:
    """Safely load a YAML file"""
    try:
        import yaml

        text = path.read_text(encoding="utf-8")
        return yaml.safe_load(text) or {}
    except Exception:
        return {}


def _get_insight_files(project_root: Path) -> List[Path]:
    """Get all Insight files, sorted by ID descending"""
    insights_dir = project_root / ".vibecollab" / "insights"
    if not insights_dir.exists():
        return []
    return sorted(insights_dir.glob("INS-*.yaml"), reverse=True)


def create_mcp_server(project_root: Optional[Path] = None):
    """Create and configure an MCP Server instance

    Args:
        project_root: Project root directory; auto-detected when None

    Returns:
        FastMCP instance
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "MCP Server requires the mcp dependency. Install: pip install vibe-collab[mcp]"
        )

    root = project_root or _find_project_root()
    config_path = root / "project.yaml"

    mcp = FastMCP(
        "vibecollab",
        instructions=(
            "VibeCollab protocol management tool. Provides project protocol doc reading, "
            "Insight experience search and distillation, protocol compliance checking, "
            "dev guidance, and more. At conversation start, read contributing_ai and context resources first."
        ),
    )

    # ================================================================
    # Resources -- protocol document exposure
    # ================================================================

    @mcp.resource("vibecollab://docs/contributing_ai")
    def get_contributing_ai() -> str:
        """Project AI collaboration protocol (CONTRIBUTING_AI.md) -- must read at conversation start"""
        return _safe_read_text(root / "CONTRIBUTING_AI.md")

    @mcp.resource("vibecollab://docs/context")
    def get_context() -> str:
        """Project current state (docs/CONTEXT.md) -- must read at conversation start"""
        return _safe_read_text(root / "docs" / "CONTEXT.md")

    @mcp.resource("vibecollab://docs/decisions")
    def get_decisions() -> str:
        """Decision records (docs/DECISIONS.md)"""
        return _safe_read_text(root / "docs" / "DECISIONS.md")

    @mcp.resource("vibecollab://docs/roadmap")
    def get_roadmap() -> str:
        """Project roadmap (docs/ROADMAP.md)"""
        return _safe_read_text(root / "docs" / "ROADMAP.md")

    @mcp.resource("vibecollab://docs/changelog")
    def get_changelog() -> str:
        """Changelog (docs/CHANGELOG.md)"""
        return _safe_read_text(root / "docs" / "CHANGELOG.md")

    @mcp.resource("vibecollab://insights/list")
    def get_insights_list() -> str:
        """All Insight entries list (ID + title + tags)"""
        files = _get_insight_files(root)
        if not files:
            return json.dumps({"insights": [], "count": 0}, ensure_ascii=False)

        insights = []
        for f in files:
            data = _safe_load_yaml(f)
            if data:
                insights.append({
                    "id": data.get("id", f.stem),
                    "title": data.get("title", ""),
                    "tags": data.get("tags", []),
                    "category": data.get("category", ""),
                })
        return json.dumps({"insights": insights, "count": len(insights)}, ensure_ascii=False)

    # ================================================================
    # Tools -- feature exposure
    # ================================================================

    @mcp.tool()
    def insight_search(query: str, tags: str = "", semantic: bool = False) -> str:
        """Search Insight knowledge base

        Args:
            query: Search keywords or natural language description
            tags: Tag filter, comma-separated (e.g. "architecture,MCP")
            semantic: Whether to use semantic search (requires built vector index)
        """
        cmd = ["vibecollab", "insight", "search"]
        if tags:
            cmd.extend(["--tags", tags])
        if semantic:
            cmd.append("--semantic")
        cmd.append(query)

        result = _run_cli(cmd, root)
        return result

    @mcp.tool()
    def insight_add(
        title: str,
        tags: str,
        category: str,
        scenario: str,
        approach: str,
        summary: str = "",
        context: str = "",
    ) -> str:
        """Add a new Insight

        Args:
            title: Insight title
            tags: Tags, comma-separated
            category: Category (technique/workflow/decision/debug/tool/integration)
            scenario: Applicable scenario description
            approach: Method/steps description
            summary: One-line summary (optional)
            context: Creation background (optional)
        """
        cmd = [
            "vibecollab", "insight", "add",
            "-t", title,
            "--tags", tags,
            "-c", category,
            "-s", scenario,
            "-a", approach,
        ]
        if summary:
            cmd.extend(["--summary", summary])
        if context:
            cmd.extend(["--context", context])

        return _run_cli(cmd, root)

    @mcp.tool()
    def check(strict: bool = False) -> str:
        """Check protocol compliance

        Args:
            strict: Whether to use strict mode (warnings also count as failures)
        """
        cmd = ["vibecollab", "check"]
        if strict:
            cmd.append("--strict")
        return _run_cli(cmd, root)

    @mcp.tool()
    def onboard(developer: str = "", output_json: bool = True) -> str:
        """Get project context guidance -- call at conversation start

        Args:
            developer: Developer ID (optional)
            output_json: Whether to output JSON format (default True)
        """
        cmd = ["vibecollab", "onboard"]
        if developer:
            cmd.extend(["-d", developer])
        if output_json:
            cmd.append("--json")
        return _run_cli(cmd, root)

    @mcp.tool()
    def next_step() -> str:
        """Get next action suggestions"""
        return _run_cli(["vibecollab", "next"], root)

    @mcp.tool()
    def task_list() -> str:
        """List current tasks"""
        return _run_cli(["vibecollab", "task", "list"], root)

    @mcp.tool()
    def task_create(
        task_id: str,
        role: str,
        feature: str,
        assignee: str = "",
        description: str = "",
    ) -> str:
        """Create a new task (auto-links Insights)

        Args:
            task_id: Task ID, format TASK-{ROLE}-{SEQ} (e.g. TASK-DEV-001)
            role: Role code (DEV/PM/ARCH/...)
            feature: Feature description
            assignee: Assignee (optional)
            description: Detailed description (optional)
        """
        cmd = [
            "vibecollab", "task", "create",
            "--id", task_id,
            "--role", role,
            "--feature", feature,
        ]
        if assignee:
            cmd.extend(["--assignee", assignee])
        if description:
            cmd.extend(["--description", description])
        cmd.append("--json")
        return _run_cli(cmd, root)

    @mcp.tool()
    def task_transition(
        task_id: str,
        new_status: str,
        reason: str = "",
    ) -> str:
        """Advance task status

        Valid transitions: TODO->IN_PROGRESS, IN_PROGRESS->REVIEW/TODO, REVIEW->DONE/IN_PROGRESS

        Args:
            task_id: Task ID
            new_status: Target status (TODO/IN_PROGRESS/REVIEW/DONE)
            reason: Change reason (optional)
        """
        cmd = [
            "vibecollab", "task", "transition",
            task_id, new_status.upper(),
            "--json",
        ]
        if reason:
            cmd.extend(["--reason", reason])
        return _run_cli(cmd, root)

    @mcp.tool()
    def project_prompt(developer: str = "", compact: bool = True) -> str:
        """Generate complete project context prompt text

        Args:
            developer: Developer ID (optional)
            compact: Whether to use compact mode (default True)
        """
        cmd = ["vibecollab", "prompt"]
        if developer:
            cmd.extend(["-d", developer])
        if compact:
            cmd.append("--compact")
        return _run_cli(cmd, root)

    @mcp.tool()
    def developer_context(developer: str) -> str:
        """Get context info for a specific developer

        Args:
            developer: Developer ID
        """
        dev_dir = root / "docs" / "developers" / developer
        if not dev_dir.exists():
            return json.dumps(
                {"error": f"Developer '{developer}' does not exist"},
                ensure_ascii=False,
            )

        context_text = _safe_read_text(dev_dir / "CONTEXT.md")
        metadata = _safe_load_yaml(dev_dir / ".metadata.yaml")

        return json.dumps(
            {
                "developer": developer,
                "context": context_text,
                "metadata": metadata,
            },
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    def search_docs(query: str, doc_type: str = "", min_score: float = 0.0) -> str:
        """Semantic search across project documents and Insights

        Args:
            query: Search content (natural language)
            doc_type: Filter by source type (insight/document, empty for all)
            min_score: Minimum relevance threshold (0.0-1.0)
        """
        cmd = ["vibecollab", "search", query]
        if doc_type:
            cmd.extend(["--type", doc_type])
        if min_score > 0:
            cmd.extend(["--min-score", str(min_score)])
        return _run_cli(cmd, root)

    @mcp.tool()
    def insight_suggest(output_json: bool = True) -> str:
        """Recommend candidate Insights based on structured signals -- from git incremental/doc changes/Task changes

        Args:
            output_json: Whether to output JSON format (default True)
        """
        cmd = ["vibecollab", "insight", "suggest"]
        if output_json:
            cmd.append("--json")
        return _run_cli(cmd, root)

    @mcp.tool()
    def session_save(
        summary: str,
        developer: str = "",
        key_decisions: str = "",
        files_changed: str = "",
        insights_added: str = "",
        tags: str = "",
    ) -> str:
        """Save conversation session summary -- call at conversation end

        Args:
            summary: Conversation summary text (required)
            developer: Developer ID (optional)
            key_decisions: Key decisions, comma-separated (optional)
            files_changed: Files involved, comma-separated (optional)
            insights_added: New Insight IDs, comma-separated (optional)
            tags: Tags, comma-separated (optional)
        """
        try:
            from ..domain.session_store import Session, SessionStore

            store = SessionStore(root)
            session = Session(
                developer=developer,
                summary=summary,
                key_decisions=[
                    d.strip() for d in key_decisions.split(",") if d.strip()
                ] if key_decisions else [],
                files_changed=[
                    f.strip() for f in files_changed.split(",") if f.strip()
                ] if files_changed else [],
                insights_added=[
                    i.strip() for i in insights_added.split(",") if i.strip()
                ] if insights_added else [],
                tags=[
                    t.strip() for t in tags.split(",") if t.strip()
                ] if tags else [],
            )
            store.save(session)
            return json.dumps(
                {"status": "ok", "session_id": session.session_id,
                 "message": f"Session saved: {session.session_id}"},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"status": "error", "message": str(e)},
                ensure_ascii=False,
            )

    @mcp.tool()
    def insight_graph(output_format: str = "json") -> str:
        """Get Insight relationship graph

        Args:
            output_format: Output format (json/mermaid)
        """
        fmt_flag = "json" if output_format == "json" else output_format
        cmd = ["vibecollab", "insight", "graph", "--format", fmt_flag]
        return _run_cli(cmd, root)

    @mcp.tool()
    def insight_export(ids: str = "", include_registry: bool = False) -> str:
        """Export Insights in YAML format

        Args:
            ids: IDs to export, comma-separated (default all)
            include_registry: Whether to include registry state
        """
        cmd = ["vibecollab", "insight", "export"]
        if ids:
            cmd.extend(["--ids", ids])
        if include_registry:
            cmd.append("--include-registry")
        return _run_cli(cmd, root)

    @mcp.tool()
    def roadmap_status(output_json: bool = True) -> str:
        """Get ROADMAP milestone progress overview

        ROADMAP.md milestone format requirements (strict):
          ### vX.Y.Z - Title description
          - [ ] Feature description (TASK-DEV-001)
          - [x] Completed feature TASK-DEV-002

        Notes:
          - Only ### (H3) headers are recognized; #### or ## will not be parsed
          - Version must start with 'v' as semantic version (e.g. v0.1.0, v1.0)
          - Task ID format: TASK-{ROLE}-{SEQ} (e.g. TASK-DEV-001)
          - If zero milestones returned, ROADMAP.md format doesn't match; rewrite per above format

        Args:
            output_json: Whether to output JSON format (default True)
        """
        cmd = ["vibecollab", "roadmap", "status"]
        if output_json:
            cmd.append("--json")
        return _run_cli(cmd, root)

    @mcp.tool()
    def roadmap_sync(direction: str = "both", dry_run: bool = False) -> str:
        """Sync ROADMAP.md <-> tasks.json

        Prerequisite: ROADMAP.md must use the following format:
          ### vX.Y.Z - Title description
          - [ ] Feature description (TASK-DEV-001)

        Sync links via Task ID references in checkbox lines, not inferred from text.
        If empty result, first use roadmap_status to check format correctness.

        Args:
            direction: Sync direction (both/roadmap_to_tasks/tasks_to_roadmap)
            dry_run: Whether to preview only (default False)
        """
        cmd = ["vibecollab", "roadmap", "sync", "-d", direction, "--json"]
        if dry_run:
            cmd.append("--dry-run")
        return _run_cli(cmd, root)

    # ================================================================
    # Prompts -- conversation templates
    # ================================================================

    @mcp.prompt()
    def start_conversation(developer: str = "") -> str:
        """Context injection template at conversation start -- called automatically by IDE"""
        parts = [
            "# VibeCollab Protocol Context",
            "",
            "You are participating in a project managed by the VibeCollab protocol. Please follow these rules:",
            "",
            "## Protocol Requirements",
            "1. Conversation start: Read CONTRIBUTING_AI.md and CONTEXT.md first to understand collaboration rules and project state",
            "2. During conversation: Follow decision-level system; record important decisions to DECISIONS.md",
            "3. Conversation end: Update CONTEXT.md + CHANGELOG.md, check for Insights worth distilling, run git commit",
            "",
            "## Available Tools",
            "- `insight_search`: Search existing Insights",
            "- `insight_add`: Add new Insight",
            "- `insight_suggest`: Recommend candidate Insights based on structured signals",
            "- `check`: Check protocol compliance",
            "- `onboard`: Get full project context",
            "- `next_step`: Get next step suggestions",
            "- `search_docs`: Semantic search project documents",
            "- `task_list`: List current tasks",
            "- `task_create`: Create new task",
            "- `task_transition`: Advance task status",
            "- `insight_graph`: View Insight relationship graph",
            "- `insight_export`: Export Insights",
            "- `roadmap_status`: View ROADMAP milestone progress",
            "- `roadmap_sync`: Sync ROADMAP <-> tasks.json",
            "- `session_save`: Save conversation session (call at conversation end)",
            "",
        ]

        # Inject project basic info
        config = _safe_load_yaml(root / "project.yaml")
        proj = config.get("project", {})
        if proj:
            parts.extend([
                f"## Current Project: {proj.get('name', 'Unknown')} {proj.get('version', '')}",
                f"Description: {proj.get('description', '')}",
                "",
            ])

        # Inject current state summary
        context_text = _safe_read_text(root / "docs" / "CONTEXT.md")
        if context_text:
            lines = context_text.strip().split("\n")[:20]
            parts.extend([
                "## Current Project Status (CONTEXT.md Summary)",
                *lines,
                "",
            ])

        # Developer context
        if developer:
            dev_context = _safe_read_text(
                root / "docs" / "developers" / developer / "CONTEXT.md"
            )
            if dev_context:
                dev_lines = dev_context.strip().split("\n")[:15]
                parts.extend([
                    f"## Developer {developer}'s Context",
                    *dev_lines,
                    "",
                ])

        return "\n".join(parts)

    return mcp


def _run_cli(cmd: List[str], cwd: Path) -> str:
    """Run vibecollab CLI command and return output"""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        output = result.stdout
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return output
    except subprocess.TimeoutExpired:
        return "[Error] Command execution timed out (30s)"
    except FileNotFoundError:
        return "[Error] vibecollab command not found. Please install: pip install vibe-collab"
    except Exception as e:
        return f"[Error] {e}"


def run_server(
    project_root: Optional[Path] = None,
    transport: str = "stdio",
):
    """Start MCP Server

    Args:
        project_root: Project root directory
        transport: Transport mode ("stdio" or "sse")
    """
    server = create_mcp_server(project_root)
    server.run(transport=transport)
