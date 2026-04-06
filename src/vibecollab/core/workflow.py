"""
Workflow management module for pre-built execution plans.

This module provides functionality to discover, load, and manage
pre-built workflow YAML files stored in .vibecollab/workflows/.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class WorkflowInfo:
    """Information about a discovered workflow."""

    name: str
    description: str
    version: str
    category: str
    step_count: int
    path: Path
    raw: Dict[str, Any]

    @classmethod
    def from_file(cls, path: Path) -> Optional["WorkflowInfo"]:
        """Load workflow info from a YAML file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return None
            steps = data.get("steps", [])
            return cls(
                name=data.get("name", path.stem),
                description=data.get("description", ""),
                version=data.get("version", "unknown"),
                category=data.get("category", "general"),
                step_count=len(steps) if isinstance(steps, list) else 0,
                path=path,
                raw=data,
            )
        except Exception:
            return None


def get_workflows_dir(project_root: Optional[Path] = None) -> Path:
    """Get the workflows directory path.

    Args:
        project_root: Project root directory. If None, uses current directory.

    Returns:
        Path to the workflows directory.
    """
    if project_root is None:
        project_root = Path.cwd()
    return project_root / ".vibecollab" / "workflows"


def discover_workflows(project_root: Optional[Path] = None) -> List[WorkflowInfo]:
    """Discover all available workflows in the workflows directory.

    Args:
        project_root: Project root directory. If None, uses current directory.

    Returns:
        List of WorkflowInfo objects for all discovered workflows.
    """
    workflows_dir = get_workflows_dir(project_root)
    if not workflows_dir.exists():
        return []

    workflows = []
    for path in workflows_dir.glob("*.yaml"):
        info = WorkflowInfo.from_file(path)
        if info:
            workflows.append(info)

    # Sort by name for consistent ordering
    workflows.sort(key=lambda w: w.name)
    return workflows


def find_workflow(name: str, project_root: Optional[Path] = None) -> Optional[WorkflowInfo]:
    """Find a workflow by name.

    Args:
        name: Workflow name (with or without .yaml extension).
        project_root: Project root directory. If None, uses current directory.

    Returns:
        WorkflowInfo if found, None otherwise.
    """
    # Normalize name
    if not name.endswith(".yaml"):
        name = name + ".yaml"

    workflows_dir = get_workflows_dir(project_root)
    workflow_path = workflows_dir / name

    if workflow_path.exists():
        return WorkflowInfo.from_file(workflow_path)

    # Also try without .yaml suffix for name matching
    workflows = discover_workflows(project_root)
    for wf in workflows:
        if wf.name == name.replace(".yaml", ""):
            return wf

    return None


def get_workflow_plan(name: str, project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get the plan dictionary for a workflow.

    Args:
        name: Workflow name (with or without .yaml extension).
        project_root: Project root directory. If None, uses current directory.

    Returns:
        Plan dictionary ready for PlanRunner, or None if not found.
    """
    info = find_workflow(name, project_root)
    if info:
        return info.raw
    return None


def list_workflow_categories(workflows: List[WorkflowInfo]) -> Dict[str, List[WorkflowInfo]]:
    """Group workflows by category.

    Args:
        workflows: List of WorkflowInfo objects.

    Returns:
        Dictionary mapping category names to lists of workflows.
    """
    categories: Dict[str, List[WorkflowInfo]] = {}
    for wf in workflows:
        cat = wf.category or "general"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(wf)
    return categories
