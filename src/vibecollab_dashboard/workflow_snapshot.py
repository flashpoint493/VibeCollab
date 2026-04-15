"""
Workflow Snapshot - Runtime data aggregation for development cockpit.

This module aggregates data from various sources to provide a unified view
of the current project state, workflow health, roadmap progress, active plans,
role requests, and prompt suggestions.
"""

import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Use absolute imports for testing compatibility
from vibecollab.core.workflow import discover_workflows, get_workflow_plan
from vibecollab.domain.task_manager import TaskManager
from vibecollab.domain.event_log import EventLog
from vibecollab.core.project import Project
from vibecollab.domain.role import RoleManager
from vibecollab.core.execution_plan import PlanRunner
from vibecollab.utils.git import is_git_repo, get_git_status
from vibecollab.utils.llmstxt import LLMsTxtManager


@dataclass
class ProjectStatus:
    """Project-level status information."""
    name: str
    version: str
    milestone: str
    git_dirty: bool
    git_changed_files: int
    recent_event_time: Optional[str]
    current_role: Optional[str]


@dataclass
class WorkflowHealth:
    """Workflow health assessment."""
    status: str  # ok / warning / error
    prompt_action_host_configured: bool
    workflow_interrupted: bool
    state_recoverable: bool
    roadmap_task_context_synced: bool
    issues: List[Dict[str, Any]]


@dataclass
class RoadmapTasks:
    """Roadmap and tasks overview."""
    milestone_pending_count: int
    todo_count: int
    in_progress_count: int
    review_count: int
    done_count: int
    current_main_task: Optional[str]
    role_request_entry_hint: str


@dataclass
class ActivePlan:
    """Information about an active execution plan."""
    plan_name: str
    status: str
    current_step_index: int
    total_steps: int
    step_statuses: List[Dict[str, Any]]
    recent_step_output: str
    resumable: bool


@dataclass
class RoleRequest:
    """Role context and pending requests."""
    current_role: str
    role_context_summary: str
    pending_requests: List[str]
    recent_role_switch: Optional[str]
    insight_trigger_suggestions: List[str]


@dataclass
class PromptSuggestion:
    """Prompt suggestions for next actions."""
    next_command: str
    ai_prompt: str
    documents_to_update: List[str]


@dataclass
class WorkflowSnapshot:
    """Complete snapshot of workflow runtime state."""
    kind: str = "workflow_snapshot"
    generated_at: Optional[str] = None
    project: Optional[ProjectStatus] = None
    git: Optional[Dict[str, Any]] = None
    role: Optional[Dict[str, Any]] = None
    roadmap: Optional[RoadmapTasks] = None
    tasks: Optional[Dict[str, Any]] = None
    plans: Optional[Dict[str, Any]] = None
    workflows: Optional[Dict[str, Any]] = None
    validate: Optional[Dict[str, Any]] = None
    suggestions: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary for JSON serialization."""
        result = {
            "kind": self.kind,
            "generated_at": self.generated_at or datetime.now(timezone.utc).isoformat(),
        }
        
        if self.project:
            result["project"] = asdict(self.project)
        if self.git:
            result["git"] = self.git
        if self.role:
            result["role"] = self.role
        if self.roadmap:
            result["roadmap"] = asdict(self.roadmap)
        if self.tasks:
            result["tasks"] = self.tasks
        if self.plans:
            result["plans"] = self.plans
        if self.workflows:
            result["workflows"] = self.workflows
        if self.validate:
            result["validate"] = self.validate
        if self.suggestions:
            result["suggestions"] = self.suggestions
            
        return result


class WorkflowSnapshotGenerator:
    """Generates workflow snapshots by aggregating data from various sources."""

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.project_config = self._load_project_config()

    def _load_project_config(self) -> Dict[str, Any]:
        """Load project.yaml configuration."""
        config_path = self.project_root / "project.yaml"
        if not config_path.exists():
            return {}
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _get_git_status(self) -> Tuple[bool, int]:
        """Get git dirty status and changed file count."""
        if not is_git_repo(self.project_root):
            return False, 0
        
        try:
            status = get_git_status(self.project_root)
            dirty = status.get("dirty", False)
            changed_files = len(status.get("changed_files", []))
            return dirty, changed_files
        except Exception:
            return False, 0

    def _get_current_role(self) -> Optional[str]:
        """Get current active role from role context."""
        try:
            # Check for role context files
            role_context_path = self.project_root / ".vibecollab" / "roles" / "current"
            if role_context_path.exists():
                with open(role_context_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception:
            pass
        return None

    def _get_recent_event_time(self) -> Optional[str]:
        """Get timestamp of most recent event."""
        try:
            event_log = EventLog(self.project_root)
            recent_events = event_log.read_recent(1)
            if recent_events:
                return recent_events[0].timestamp
        except Exception:
            pass
        return None

    def _get_task_summary(self) -> Dict[str, Any]:
        """Get task manager summary."""
        try:
            task_manager = TaskManager(self.project_root)
            all_tasks = task_manager.list_tasks()
            
            summary = {
                "todo": 0,
                "in_progress": 0,
                "review": 0,
                "done": 0,
                "total": len(all_tasks)
            }
            
            active_tasks = []
            for task in all_tasks:
                status_key = task.status.lower()
                if status_key in summary:
                    summary[status_key] += 1
                
                if task.status != "DONE":
                    active_tasks.append({
                        "id": task.id,
                        "status": task.status,
                        "feature": task.feature,
                        "assignee": task.assignee or "-"
                    })
            
            return {
                "summary": summary,
                "active": active_tasks[:10]  # Limit to top 10
            }
        except Exception:
            return {"summary": {}, "active": []}

    def _get_active_plans(self) -> List[ActivePlan]:
        """Get information about active execution plans."""
        active_plans = []
        
        # Check for plan state files
        plan_state_dir = self.project_root / ".vibecollab" / "plan_state"
        if plan_state_dir.exists():
            for state_file in plan_state_dir.glob("*.json"):
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                    
                    plan_name = state_data.get("plan_name", state_file.stem)
                    current_step = state_data.get("current_step_index", 0)
                    total_steps = state_data.get("total_steps", 0)
                    
                    active_plans.append(ActivePlan(
                        plan_name=plan_name,
                        status="running",
                        current_step_index=current_step,
                        total_steps=total_steps,
                        step_statuses=[],  # Would need more detailed state parsing
                        recent_step_output="",
                        resumable=True
                    ))
                except Exception:
                    continue
        
        return active_plans

    def _get_workflow_discovery(self) -> Dict[str, Any]:
        """Discover available workflows."""
        try:
            workflows = discover_workflows(self.project_root)
            return {
                "discovered": [
                    {
                        "name": wf.name,
                        "category": wf.category,
                        "description": wf.description
                    }
                    for wf in workflows
                ]
            }
        except Exception:
            return {"discovered": []}

    def generate_snapshot(self) -> WorkflowSnapshot:
        """Generate a complete workflow snapshot."""
        # Get basic project info
        project_config = self.project_config.get("project", {})
        git_dirty, changed_files = self._get_git_status()
        current_role = self._get_current_role()
        recent_event_time = self._get_recent_event_time()
        
        # Build project status
        project_status = ProjectStatus(
            name=project_config.get("name", "Unknown"),
            version=project_config.get("version", "Unknown"),
            milestone=project_config.get("milestone", "Unknown"),
            git_dirty=git_dirty,
            git_changed_files=changed_files,
            recent_event_time=recent_event_time,
            current_role=current_role
        )
        
        # Build git info
        git_info = {
            "dirty": git_dirty,
            "changed_files": changed_files
        }
        
        # Build role info
        role_info = {
            "current": current_role or "Unknown",
            "active_roles": self._get_active_roles()
        }
        
        # Build roadmap and tasks
        task_summary = self._get_task_summary()
        roadmap_tasks = RoadmapTasks(
            milestone_pending_count=self._get_milestone_pending_count(),
            todo_count=task_summary["summary"].get("todo", 0),
            in_progress_count=task_summary["summary"].get("in_progress", 0),
            review_count=task_summary["summary"].get("review", 0),
            done_count=task_summary["summary"].get("done", 0),
            current_main_task=self._get_current_main_task(task_summary["active"]),
            role_request_entry_hint="Use 'vibecollab role switch <role>' to change context"
        )
        
        # Build active plans
        active_plans = self._get_active_plans()
        plans_info = {
            "active": [asdict(plan) for plan in active_plans]
        }
        
        # Build workflows
        workflows_info = self._get_workflow_discovery()
        
        # Generate validation status
        validate_info = self._generate_validation_status()
        
        # Generate suggestions
        suggestions_info = self._generate_suggestions()
        
        return WorkflowSnapshot(
            generated_at=datetime.now(timezone.utc).isoformat(),
            project=project_status,
            git=git_info,
            role=role_info,
            roadmap=roadmap_tasks,
            tasks=task_summary,
            plans=plans_info,
            workflows=workflows_info,
            validate=validate_info,
            suggestions=suggestions_info
        )

    def _get_active_roles(self) -> List[str]:
        """Get list of active roles."""
        roles_dir = self.project_root / ".vibecollab" / "roles"
        if not roles_dir.exists():
            return []
        
        active_roles = []
        for role_dir in roles_dir.iterdir():
            if role_dir.is_dir() and role_dir.name != "current":
                active_roles.append(role_dir.name)
        
        return active_roles

    def _get_milestone_pending_count(self) -> int:
        """Get count of pending roadmap items."""
        roadmap_path = self.project_root / "docs" / "ROADMAP.md"
        if not roadmap_path.exists():
            return 0
        
        try:
            content = roadmap_path.read_text(encoding="utf-8")
            # Simple count of - [ ] items
            return content.count("- [ ]")
        except Exception:
            return 0

    def _get_current_main_task(self, active_tasks: List[Dict[str, Any]]) -> Optional[str]:
        """Get current main task from active tasks."""
        if not active_tasks:
            return None
        
        # Prefer IN_PROGRESS tasks
        for task in active_tasks:
            if task.get("status") == "IN_PROGRESS":
                return f"{task['id']}: {task['feature']}"
        
        # Fallback to first TODO task
        for task in active_tasks:
            if task.get("status") == "TODO":
                return f"{task['id']}: {task['feature']}"
        
        return None

    def _generate_validation_status(self) -> Dict[str, Any]:
        """Generate workflow validation status."""
        # This would be more comprehensive in the validator module
        # For now, provide basic status
        return {
            "status": "ok",  # Would be determined by validator
            "issues": []
        }

    def _generate_suggestions(self) -> Dict[str, Any]:
        """Generate prompt suggestions."""
        return {
            "next_commands": [
                "vibecollab workflow panel --watch",
                "vibecollab plan status daily-sync"
            ],
            "prompt_hints": [
                "Update docs/CONTEXT.md after plan completion"
            ]
        }


def save_snapshot(snapshot: WorkflowSnapshot, output_path: Path) -> None:
    """Save snapshot to file in JSON format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)


def load_snapshot(input_path: Path) -> Optional[WorkflowSnapshot]:
    """Load snapshot from file."""
    if not input_path.exists():
        return None
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Convert back to WorkflowSnapshot object
        # This is a simplified version - would need proper reconstruction
        return WorkflowSnapshot(**data)
    except Exception:
        return None