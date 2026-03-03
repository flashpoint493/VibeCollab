"""
Pipeline - Structured chain-of-actions for document consistency and task automation.

This module implements the "structured chain pipeline" concept:
- Schema validation ensures data contracts
- Task lifecycle hooks trigger downstream actions automatically
- Document sync keeps all docs consistent when upstream changes occur

Design:
    Pipeline connects Schema (validation) → CLI (execution) → Docs (output)
    by registering hooks on TaskManager events and providing a unified
    validate-and-sync entry point.

Key capabilities:
1. Schema-driven validation: validate project.yaml against schema rules
2. Task completion hooks: auto-sync roadmap, suggest insights on task DONE
3. Document freshness check: detect stale docs and recommend updates
4. Action registry: map events to CLI commands for AI agents
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# Schema Validator
# ---------------------------------------------------------------------------

class SchemaValidator:
    """Validate project.yaml against schema/project.schema.yaml rules.

    Unlike JSON Schema libraries, this is a lightweight purpose-built validator
    that checks VibeCollab-specific constraints directly.
    """

    def __init__(self, schema_path: Optional[Path] = None):
        self._schema: Optional[Dict] = None
        if schema_path and schema_path.exists():
            with open(schema_path, encoding="utf-8") as f:
                self._schema = yaml.safe_load(f)

    def validate(self, config: Dict[str, Any]) -> "ValidationReport":
        """Validate a project config dict against schema rules.

        Returns:
            ValidationReport with errors and warnings.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # --- project section (required) ---
        project = config.get("project", {})
        if not project.get("name"):
            errors.append("project.name is required")
        version = project.get("version", "")
        if version and not re.match(r"^v\d+\.\d+(\.\d+)?$", version):
            warnings.append(
                f"project.version '{version}' does not match vX.Y or vX.Y.Z pattern"
            )

        # --- roles section ---
        roles = config.get("roles", [])
        for i, role in enumerate(roles):
            if not role.get("code"):
                errors.append(f"roles[{i}].code is required")
            elif not re.match(r"^[A-Z]+$", role["code"]):
                warnings.append(
                    f"roles[{i}].code '{role['code']}' should be uppercase"
                )
            if not role.get("name"):
                errors.append(f"roles[{i}].name is required")

        # --- decision_levels section ---
        levels = config.get("decision_levels", [])
        valid_levels = {"S", "A", "B", "C"}
        for i, lvl in enumerate(levels):
            if lvl.get("level") not in valid_levels:
                warnings.append(
                    f"decision_levels[{i}].level '{lvl.get('level')}' "
                    f"not in {valid_levels}"
                )

        # --- task_unit section ---
        task_unit = config.get("task_unit", {})
        if task_unit:
            id_pattern = task_unit.get("id_pattern", "")
            if id_pattern and "TASK-" not in id_pattern:
                warnings.append("task_unit.id_pattern should contain 'TASK-'")
            statuses = task_unit.get("statuses", [])
            required_statuses = {"TODO", "IN_PROGRESS", "REVIEW", "DONE"}
            if statuses and not required_statuses.issubset(set(statuses)):
                missing = required_statuses - set(statuses)
                warnings.append(
                    f"task_unit.statuses missing: {missing}"
                )

        # --- documentation section ---
        docs = config.get("documentation", {})
        key_files = docs.get("key_files", [])
        for i, kf in enumerate(key_files):
            if not kf.get("path"):
                errors.append(f"documentation.key_files[{i}].path is required")

        # --- git_workflow section ---
        git = config.get("git_workflow", {})
        if git:
            prefixes = git.get("commit_prefixes", [])
            if prefixes:
                prefix_values = [p.get("prefix", "") for p in prefixes]
                if not any("FEAT" in p.upper() or "FIX" in p.upper()
                           for p in prefix_values):
                    warnings.append(
                        "git_workflow.commit_prefixes should include "
                        "FEAT and FIX types"
                    )

        return ValidationReport(errors=errors, warnings=warnings)


class ValidationReport:
    """Result of schema validation."""

    def __init__(self, errors: List[str] = None, warnings: List[str] = None):
        self.errors = errors or []
        self.warnings = warnings or []

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


# ---------------------------------------------------------------------------
# Action Registry — maps events to CLI commands
# ---------------------------------------------------------------------------

class ActionRegistry:
    """Maps lifecycle events to recommended CLI commands.

    This is the "skill" layer that tells AI agents what CLI commands
    to execute when certain events occur.
    """

    # Event → list of (command, description, priority)
    _ACTIONS: Dict[str, List[Tuple[str, str, int]]] = {
        "task_completed": [
            ("vibecollab roadmap sync", "Sync ROADMAP.md with task status", 1),
            ("vibecollab insight suggest", "Check for insight candidates", 2),
            ("vibecollab dev sync", "Update global CONTEXT.md", 3),
        ],
        "task_created": [
            ("vibecollab roadmap sync --dry-run",
             "Preview ROADMAP sync impact", 3),
        ],
        "insight_added": [
            ("vibecollab check --insights", "Verify insight consistency", 2),
            ("vibecollab dev sync", "Update global CONTEXT.md", 3),
        ],
        "milestone_completed": [
            ("vibecollab roadmap status", "Review milestone progress", 1),
            ("vibecollab insight suggest", "Solidify milestone learnings", 1),
            ("vibecollab check", "Run full protocol check", 2),
        ],
        "config_changed": [
            ("vibecollab generate -c project.yaml",
             "Regenerate CONTRIBUTING_AI.md", 1),
            ("vibecollab check", "Validate protocol compliance", 2),
        ],
        "docs_stale": [
            ("vibecollab dev sync", "Regenerate global CONTEXT.md", 1),
            ("vibecollab next", "Get document update suggestions", 2),
        ],
    }

    @classmethod
    def get_actions(cls, event: str) -> List[Tuple[str, str, int]]:
        """Get recommended actions for an event, sorted by priority."""
        actions = cls._ACTIONS.get(event, [])
        return sorted(actions, key=lambda x: x[2])

    @classmethod
    def get_all_events(cls) -> List[str]:
        """List all registered event types."""
        return list(cls._ACTIONS.keys())

    @classmethod
    def register_action(cls, event: str, command: str,
                        description: str, priority: int = 5) -> None:
        """Register a custom action for an event."""
        if event not in cls._ACTIONS:
            cls._ACTIONS[event] = []
        cls._ACTIONS[event].append((command, description, priority))

    @classmethod
    def format_action_hints(cls, event: str) -> str:
        """Format action hints as human-readable text for AI agents."""
        actions = cls.get_actions(event)
        if not actions:
            return ""
        lines = [f"Recommended actions for '{event}':"]
        for cmd, desc, pri in actions:
            lines.append(f"  P{pri}: {cmd}")
            lines.append(f"       {desc}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Document Sync Checker
# ---------------------------------------------------------------------------

class DocSyncChecker:
    """Check document freshness and consistency.

    Detects when upstream documents have been modified but downstream
    documents haven't been updated to match.
    """

    # Dependency graph: upstream → [downstream]
    _DOC_DEPS: Dict[str, List[str]] = {
        "project.yaml": [
            "CONTRIBUTING_AI.md",
        ],
        "docs/CONTEXT.md": [
            "docs/CHANGELOG.md",
        ],
        ".vibecollab/tasks.json": [
            "docs/ROADMAP.md",
        ],
    }

    def __init__(self, project_root: Path):
        self.root = project_root

    def check_freshness(self) -> List[Dict[str, Any]]:
        """Check all doc dependencies for staleness.

        Returns:
            List of stale document reports.
        """
        results = []
        for upstream, downstreams in self._DOC_DEPS.items():
            up_path = self.root / upstream
            if not up_path.exists():
                continue
            up_mtime = up_path.stat().st_mtime

            for downstream in downstreams:
                down_path = self.root / downstream
                if not down_path.exists():
                    results.append({
                        "upstream": upstream,
                        "downstream": downstream,
                        "status": "missing",
                        "action": ActionRegistry.get_actions("docs_stale"),
                    })
                    continue

                down_mtime = down_path.stat().st_mtime
                if up_mtime > down_mtime:
                    delta_hours = (up_mtime - down_mtime) / 3600
                    results.append({
                        "upstream": upstream,
                        "downstream": downstream,
                        "status": "stale",
                        "hours_behind": round(delta_hours, 1),
                        "action": ActionRegistry.get_actions("docs_stale"),
                    })
        return results


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------

class Pipeline:
    """Orchestrates validation, sync, and automation.

    This is the main entry point that connects:
    - SchemaValidator (data contracts)
    - TaskManager hooks (lifecycle automation)
    - DocSyncChecker (document consistency)
    - ActionRegistry (AI agent guidance)

    Usage:
        pipeline = Pipeline(project_root=Path("."))
        # Validate config
        report = pipeline.validate_config()
        # Check document freshness
        stale = pipeline.check_docs()
        # Register task hooks for automation
        pipeline.register_task_hooks(task_manager)
        # Get next actions for AI agent
        actions = pipeline.get_pending_actions()
    """

    def __init__(self, project_root: Path,
                 config_path: Optional[str] = "project.yaml"):
        self.root = Path(project_root)
        self.config_path = config_path
        self._config: Optional[Dict] = None
        self._load_config()

        schema_path = self.root / "schema" / "project.schema.yaml"
        self.validator = SchemaValidator(schema_path)
        self.doc_checker = DocSyncChecker(self.root)

    def _load_config(self) -> None:
        """Load project.yaml config."""
        if self.config_path:
            cfg_path = self.root / self.config_path
            if cfg_path.exists():
                with open(cfg_path, encoding="utf-8") as f:
                    self._config = yaml.safe_load(f)

    def validate_config(self) -> ValidationReport:
        """Validate project.yaml against schema rules."""
        if not self._config:
            return ValidationReport(
                errors=["project.yaml not found or empty"])
        return self.validator.validate(self._config)

    def check_docs(self) -> List[Dict[str, Any]]:
        """Check document freshness across dependency graph."""
        return self.doc_checker.check_freshness()

    def register_task_hooks(self, task_manager: Any) -> None:
        """Register lifecycle hooks on a TaskManager instance.

        When tasks complete, automatically:
        1. Log completion actions for AI agent guidance
        2. Store action hints in the event payload
        """
        def on_task_complete(task: Any) -> None:
            actions = ActionRegistry.get_actions("task_completed")
            hints = ActionRegistry.format_action_hints("task_completed")
            # Store hints as metadata for AI agents to read
            if hasattr(task, 'metadata') and isinstance(task.metadata, dict):
                task.metadata["_pipeline_actions"] = [
                    {"command": cmd, "description": desc, "priority": pri}
                    for cmd, desc, pri in actions
                ]

        if hasattr(task_manager, 'on_complete'):
            task_manager.on_complete(on_task_complete)

    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Collect all pending actions from various sources.

        Returns:
            Sorted list of pending actions with commands and priorities.
        """
        actions: List[Dict[str, Any]] = []

        # 1. Config validation issues
        if self._config:
            report = self.validate_config()
            if not report.ok:
                for err in report.errors:
                    actions.append({
                        "source": "schema_validation",
                        "priority": 1,
                        "message": err,
                        "command": "vibecollab validate -c project.yaml",
                    })
            for warn in report.warnings:
                actions.append({
                    "source": "schema_validation",
                    "priority": 3,
                    "message": warn,
                    "command": None,
                })

        # 2. Document freshness
        stale_docs = self.check_docs()
        for stale in stale_docs:
            status = stale["status"]
            actions.append({
                "source": "doc_freshness",
                "priority": 1 if status == "missing" else 2,
                "message": (
                    f"{stale['downstream']} is {status} "
                    f"(upstream: {stale['upstream']})"
                ),
                "command": stale["action"][0][0] if stale["action"] else None,
            })

        return sorted(actions, key=lambda x: x["priority"])

    def get_version(self) -> Dict[str, str]:
        """Get all version numbers from their canonical sources.

        Returns dict with:
        - package_version: from __init__.py (__version__)
        - protocol_version: from project.yaml project.version
        """
        from .. import __version__
        protocol_version = "v1.0"
        if self._config:
            protocol_version = self._config.get(
                "project", {}).get("version", "v1.0")
        return {
            "package_version": __version__,
            "protocol_version": protocol_version,
        }
