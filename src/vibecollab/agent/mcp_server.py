"""
VibeCollab MCP Server -- Model Context Protocol integration

Makes VibeCollab a "protocol backend" for AI IDEs like Cline/Cursor/CodeBuddy,
turning "manual copy-paste" into "IDE auto-reads protocol".

Features:
    - Tools: insight_search, insight_add, check, onboard, next, task_list
    - Resources: CONTRIBUTING_AI.md, CONTEXT.md, DECISIONS.md, ROADMAP.md, Insight YAML
    - Prompts: Context injection templates at conversation start

Dependencies:
    pip install vibe-collab

Usage:
    vibecollab mcp serve                # stdio mode (recommended, IDE direct connect)
    vibecollab mcp serve --transport sse # SSE mode (remote debug)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

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


def _get_managers(root: Path):
    """Lazy-initialize and return (InsightManager, TaskManager, EventLog)."""
    from ..domain.event_log import EventLog
    from ..domain.task_manager import TaskManager
    from ..insight.manager import InsightManager

    event_log = EventLog(root / ".vibecollab" / "events.jsonl")
    im = InsightManager(project_root=root, event_log=event_log)
    tm = TaskManager(project_root=root, event_log=event_log, insight_manager=im)
    return im, tm, event_log


def create_mcp_server(project_root: Optional[Path] = None):
    """Create and configure an MCP Server instance

    Args:
        project_root: Project root directory; auto-detected when None

    Returns:
        FastMCP instance
    """
    from mcp.server.fastmcp import FastMCP

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
    # Tools -- direct Python API calls (no subprocess)
    # ================================================================

    @mcp.tool()
    def insight_search(query: str, tags: str = "", semantic: bool = False) -> str:
        """Search Insight knowledge base

        Args:
            query: Search keywords or natural language description
            tags: Tag filter, comma-separated (e.g. "architecture,MCP")
            semantic: Whether to use semantic search (requires built vector index)
        """
        try:
            im, _, _ = _get_managers(root)

            if semantic:
                from ..search.indexer import Indexer
                try:
                    indexer = Indexer(project_root=root)
                    results = indexer.search(query, top_k=10, source_type="insight")
                    items = [{"doc_id": r.doc_id, "title": r.title, "score": round(r.score, 3),
                              "source_type": r.source_type} for r in results]
                    return json.dumps({"results": items, "count": len(items)}, ensure_ascii=False, indent=2)
                except Exception as e:
                    return json.dumps({"error": f"Semantic search failed: {e}",
                                       "hint": "Run 'vibecollab index' first"}, ensure_ascii=False)

            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
            if tag_list:
                results = im.search_by_tags(tag_list, active_only=True)
            else:
                all_insights = im.list_all()
                query_lower = query.lower()
                results = [ins for ins in all_insights
                           if query_lower in ins.title.lower()
                           or query_lower in ins.summary.lower()
                           or any(query_lower in t.lower() for t in ins.tags)]

            items = []
            for ins in results:
                items.append({
                    "id": ins.id, "title": ins.title, "tags": ins.tags,
                    "category": ins.category, "summary": ins.summary,
                })
            return json.dumps({"results": items, "count": len(items)}, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

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
        try:
            im, _, _ = _get_managers(root)
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            body = {"scenario": scenario, "approach": approach}

            insight = im.create(
                title=title,
                tags=tag_list,
                category=category,
                body=body,
                created_by="mcp",
                summary=summary,
                context=context,
            )
            return json.dumps({
                "status": "ok",
                "id": insight.id,
                "title": insight.title,
                "message": f"Insight {insight.id} created successfully",
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def check(strict: bool = False) -> str:
        """Check protocol compliance

        Args:
            strict: Whether to use strict mode (warnings also count as failures)
        """
        try:
            from ..core.protocol_checker import ProtocolChecker

            config = _safe_load_yaml(config_path)
            checker = ProtocolChecker(project_root=root, config=config)
            results = checker.check_all()
            summary = checker.get_summary(results)

            items = []
            for r in results:
                items.append({
                    "name": r.name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "suggestion": r.suggestion,
                })

            all_passed = summary["all_passed"]
            if strict:
                all_passed = summary["errors"] == 0 and summary["warnings"] == 0

            return json.dumps({
                "all_passed": all_passed,
                "total": summary["total"],
                "passed": summary["passed"],
                "errors": summary["errors"],
                "warnings": summary["warnings"],
                "infos": summary["infos"],
                "results": items,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def onboard(developer: str = "", output_json: bool = True) -> str:
        """Get project context guidance -- call at conversation start

        Args:
            developer: Developer ID (optional)
            output_json: Whether to output JSON format (default True)
        """
        try:
            from ..cli.guide import _collect_project_context

            ctx = _collect_project_context(config_path, developer=developer or None)

            if output_json:
                safe_ctx = {}
                for k, v in ctx.items():
                    if isinstance(v, Path):
                        safe_ctx[k] = str(v)
                    else:
                        safe_ctx[k] = v
                return json.dumps(safe_ctx, ensure_ascii=False, indent=2, default=str)

            # Build readable text
            parts = [f"# Project: {ctx.get('project_name', 'Unknown')} {ctx.get('project_version', '')}"]
            if ctx.get("project_desc"):
                parts.append(f"Description: {ctx['project_desc']}")
            parts.append("")
            if ctx.get("context_text"):
                parts.append("## Current Status")
                parts.append(ctx["context_text"][:2000])
                parts.append("")
            if ctx.get("active_tasks"):
                parts.append("## Active Tasks")
                for t in ctx["active_tasks"]:
                    parts.append(f"- [{t.get('status', '?')}] {t.get('id', '?')}: {t.get('feature', '?')}")
                parts.append("")
            return "\n".join(parts)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def next_step() -> str:
        """Get next action suggestions"""
        try:
            import subprocess as _sp
            from datetime import datetime

            from ..cli.guide import (
                _check_insight_opportunity,
                _check_linked_groups_freshness,
                _get_update_files_list,
                _suggest_commit_message,
            )
            from ..domain.task_manager import TaskManager

            project_config = _safe_load_yaml(config_path)

            # Git status
            try:
                r = _sp.run(["git", "status", "--porcelain"], cwd=str(root),
                            capture_output=True, text=True, timeout=10)
                uncommitted = [line.strip() for line in r.stdout.strip().split("\n") if line.strip()]
            except Exception:
                uncommitted = []

            try:
                r = _sp.run(["git", "diff", "--name-only", "HEAD"], cwd=str(root),
                            capture_output=True, text=True, timeout=10)
                diff_files = [line.strip() for line in r.stdout.strip().split("\n") if line.strip()]
            except Exception:
                diff_files = []

            # Linked doc sync
            stale_groups = _check_linked_groups_freshness(root, project_config)

            # Overdue files
            update_files = _get_update_files_list(project_config)
            check_cfg = project_config.get("protocol_check", {}).get("checks", {}).get("documentation", {})
            threshold_hours = check_cfg.get("update_threshold_hours", 0.25)
            overdue = []
            for f in update_files:
                fp = root / f
                if fp.exists():
                    hours = (datetime.now() - datetime.fromtimestamp(fp.stat().st_mtime)).total_seconds() / 3600
                    if hours > threshold_hours:
                        overdue.append({"file": f, "minutes_overdue": int(hours * 60)})

            # Commit suggestion
            suggested_prefix = _suggest_commit_message(diff_files) if diff_files else None

            # Missing key files
            key_files = project_config.get("documentation", {}).get("key_files", [])
            missing = [kf.get("path", "") for kf in key_files
                       if kf.get("path") and not (root / kf["path"]).exists()]

            # Task status
            actions: List[Dict[str, Any]] = []
            priority = 0

            for group in stale_groups:
                for f, diff_min in group.get("stale", []):
                    priority += 1
                    actions.append({"priority": f"P0-{priority}", "type": "sync_document",
                                    "action": f"Sync update {f}",
                                    "reason": f"{group['leader']} modified, {f} is {diff_min} min behind"})

            for item in overdue:
                priority += 1
                actions.append({"priority": f"P1-{priority}", "type": "update_document",
                                "action": f"Update {item['file']}",
                                "reason": f"Overdue by {item['minutes_overdue']} min"})

            if uncommitted:
                priority += 1
                actions.append({"priority": f"P1-{priority}", "type": "git_commit",
                                "action": f"Commit changes ({len(uncommitted)} files)",
                                "suggestion": f'git commit -m "{suggested_prefix or "feat:"} <description>"'})

            for f in missing:
                priority += 1
                actions.append({"priority": f"P2-{priority}", "type": "create_file",
                                "action": f"Create {f}", "reason": "Declared but missing"})

            try:
                tm = TaskManager(project_root=root)
                all_tasks = tm.list_tasks()
                review_tasks = [t for t in all_tasks if t.status == "REVIEW"]
                for t in review_tasks[:3]:
                    priority += 1
                    actions.append({"priority": f"P1-{priority}", "type": "task_solidify",
                                    "action": f"Solidify task {t.id}: {t.feature}"})
                todo_count = sum(1 for t in all_tasks if t.status == "TODO")
                if todo_count > 3:
                    priority += 1
                    actions.append({"priority": f"P2-{priority}", "type": "task_backlog",
                                    "action": f"{todo_count} TODO tasks in backlog"})
            except Exception:
                pass

            insight_prompt = _check_insight_opportunity(root, diff_files)
            if insight_prompt:
                priority += 1
                actions.append({"priority": f"P2-{priority}", "type": "insight_review",
                                "action": "Check for experiences worth distilling", "reason": insight_prompt})

            return json.dumps({
                "uncommitted_count": len(uncommitted),
                "diff_files": diff_files[:20],
                "suggested_commit_prefix": suggested_prefix,
                "actions": actions,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def task_list() -> str:
        """List current tasks"""
        try:
            _, tm, _ = _get_managers(root)
            tasks = tm.list_tasks()
            items = []
            for t in tasks:
                items.append({
                    "id": t.id, "role": t.role, "feature": t.feature,
                    "status": t.status, "assignee": t.assignee or "",
                    "milestone": t.milestone or "",
                })
            return json.dumps({"tasks": items, "count": len(items)}, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

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
        try:
            _, tm, _ = _get_managers(root)
            task = tm.create_task(
                id=task_id, role=role, feature=feature,
                assignee=assignee or None,
                description=description or None,
                actor="mcp",
            )
            result = {
                "status": "ok",
                "task": {
                    "id": task.id, "role": task.role, "feature": task.feature,
                    "status": task.status, "assignee": task.assignee or "",
                },
                "message": f"Task {task.id} created successfully",
            }
            related = task.metadata.get("related_insights", []) if task.metadata else []
            if related:
                result["related_insights"] = related
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

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
        try:
            from ..domain.task_manager import TaskStatus

            _, tm, _ = _get_managers(root)
            status_map = {s.value: s for s in TaskStatus}
            target = status_map.get(new_status.upper())
            if not target:
                return json.dumps({"status": "error",
                                   "message": f"Invalid status: {new_status}. Valid: {list(status_map.keys())}"},
                                  ensure_ascii=False)

            result = tm.transition(task_id, target, actor="mcp", reason=reason)
            return json.dumps({
                "status": "ok" if result.ok else "error",
                "task_id": task_id,
                "new_status": new_status.upper(),
                "message": result.message if not result.ok else f"Task {task_id} -> {new_status.upper()}",
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def project_prompt(developer: str = "", compact: bool = True) -> str:
        """Generate complete project context prompt text

        Args:
            developer: Developer ID (optional)
            compact: Whether to use compact mode (default True)
        """
        try:
            from ..cli.guide import _build_prompt_text, _collect_project_context

            ctx = _collect_project_context(config_path, developer=developer or None)
            sections = ["protocol", "context", "insight"]
            if not compact:
                sections = ["protocol", "roles", "context", "insight", "git"]
            return _build_prompt_text(ctx, sections, compact=compact)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

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
        try:
            from ..search.indexer import Indexer

            indexer = Indexer(project_root=root)
            results = indexer.search(
                query, top_k=10,
                source_type=doc_type or None,
                min_score=min_score,
            )
            items = [{"doc_id": r.doc_id, "title": r.title, "score": round(r.score, 3),
                       "source_type": r.source_type, "snippet": r.snippet[:200] if hasattr(r, "snippet") else ""}
                     for r in results]
            return json.dumps({"results": items, "count": len(items)}, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e),
                               "hint": "Run 'vibecollab index' first to build vector index"}, ensure_ascii=False)

    @mcp.tool()
    def insight_suggest(output_json: bool = True) -> str:
        """Recommend candidate Insights based on structured signals -- from git incremental/doc changes/Task changes

        Args:
            output_json: Whether to output JSON format (default True)
        """
        try:
            from ..insight.signal import InsightSignalCollector

            collector = InsightSignalCollector(project_root=root)
            candidates = collector.suggest()

            items = []
            for c in candidates:
                items.append({
                    "title": c.title,
                    "tags": c.tags,
                    "category": c.category,
                    "reason": c.reason,
                    "source_signal": c.source_signal,
                    "confidence": c.confidence,
                })
            return json.dumps({"candidates": items, "count": len(items)}, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

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
        try:
            im, _, _ = _get_managers(root)
            graph = im.build_graph()

            if output_format == "mermaid":
                return im.to_mermaid(graph)

            return json.dumps(graph, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def insight_export(ids: str = "", include_registry: bool = False) -> str:
        """Export Insights in YAML format

        Args:
            ids: IDs to export, comma-separated (default all)
            include_registry: Whether to include registry state
        """
        try:
            im, _, _ = _get_managers(root)
            id_list = [i.strip() for i in ids.split(",") if i.strip()] if ids else None
            bundle = im.export_insights(insight_ids=id_list, include_registry=include_registry)

            return yaml.dump(bundle, allow_unicode=True, sort_keys=False, default_flow_style=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

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
        try:
            from ..domain.roadmap_parser import RoadmapParser
            from ..domain.task_manager import TaskManager

            tm = TaskManager(project_root=root)
            parser = RoadmapParser(project_root=root, task_manager=tm)
            status = parser.status()

            result = {
                "milestones": status.milestones,
                "total_items": status.total_items,
                "total_done": status.total_done,
                "total_tasks_linked": status.total_tasks_linked,
                "unlinked_task_ids": status.unlinked_task_ids,
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

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
        try:
            from ..domain.roadmap_parser import RoadmapParser
            from ..domain.task_manager import TaskManager

            tm = TaskManager(project_root=root)
            parser = RoadmapParser(project_root=root, task_manager=tm)
            actions = parser.sync(direction=direction, dry_run=dry_run)

            items = [{"type": a.type, "task_id": a.task_id,
                       "milestone": a.milestone, "detail": a.detail}
                     for a in actions]
            return json.dumps({
                "actions": items,
                "count": len(items),
                "dry_run": dry_run,
                "direction": direction,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

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
