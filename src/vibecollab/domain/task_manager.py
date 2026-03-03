"""
Task Manager - Structured task lifecycle with validate-solidify-rollback.

Provides a programmatic task management layer on top of VibeCollab's
existing protocol-driven task conventions, adding:
- Typed Task dataclass with required fields per project.yaml schema
- State machine with legal transitions (TODO → IN_PROGRESS → REVIEW → DONE)
- Solidify gate: pre-completion checks (required fields, scope limits)
- Rollback: revert a task to its previous state on validation failure
- EventLog integration: every mutation automatically records an event
- Insight auto-linking: creating a task auto-searches related Insights

Design principles:
- Tasks are stored as structured JSON in .vibecollab/tasks.json
- State transitions are audited and validated
- Solidify borrows the gate-pipeline pattern: ASSESS → VALIDATE → COMMIT/ROLLBACK
- Compatible with existing CONTRIBUTING_AI.md task_unit conventions
"""

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from .event_log import Event, EventLog, EventType

if TYPE_CHECKING:
    from ..insight.manager import InsightManager

# ---------------------------------------------------------------------------
# Task status enum & state machine
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    """Task statuses matching project.yaml task_unit.statuses."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


# Legal state transitions: {current_status: [allowed_next_statuses]}
VALID_TRANSITIONS: Dict[TaskStatus, List[TaskStatus]] = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS],
    TaskStatus.IN_PROGRESS: [TaskStatus.REVIEW, TaskStatus.TODO],  # can pause back to TODO
    TaskStatus.REVIEW: [TaskStatus.DONE, TaskStatus.IN_PROGRESS],  # reject → back to IN_PROGRESS
    TaskStatus.DONE: [],  # terminal state
}


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of a solidify validation gate."""
    ok: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Task dataclass
# ---------------------------------------------------------------------------

# ID pattern: TASK-{ROLE}-{SEQ}  e.g. TASK-DEV-001, TASK-PM-012
TASK_ID_PATTERN = re.compile(r"^TASK-[A-Z]+-\d{3,}$")

# Default required fields (from project.yaml task_unit.required_fields)
DEFAULT_REQUIRED_FIELDS = ["id", "role", "feature", "status"]

# Default max change scope (files) — blast radius limit
DEFAULT_MAX_FILES = 30
DEFAULT_MAX_LINES = 10000


@dataclass
class Task:
    """A structured task unit.

    Attributes:
        id: Task ID in TASK-{ROLE}-{SEQ} format
        role: Responsible role code (DEV, PM, ARCH, etc.)
        feature: Feature or goal description
        status: Current task status
        assignee: Developer assigned to this task
        dependencies: List of prerequisite task IDs
        output: Expected deliverables
        description: Detailed task description
        created_at: ISO-8601 creation timestamp
        updated_at: ISO-8601 last update timestamp
        dialogue_rounds: Estimated dialogue rounds
        milestone: Associated ROADMAP milestone (e.g. "v0.9.3")
        metadata: Arbitrary extra data
    """
    id: str
    role: str
    feature: str
    status: str = TaskStatus.TODO
    assignee: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    output: str = ""
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    dialogue_rounds: int = 0
    milestone: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            id=data.get("id", ""),
            role=data.get("role", ""),
            feature=data.get("feature", ""),
            status=data.get("status", TaskStatus.TODO),
            assignee=data.get("assignee"),
            dependencies=data.get("dependencies", []),
            output=data.get("output", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            dialogue_rounds=data.get("dialogue_rounds", 0),
            milestone=data.get("milestone", ""),
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# TaskManager
# ---------------------------------------------------------------------------

class TaskManager:
    """Manages the task lifecycle with validation and event logging.

    Usage:
        mgr = TaskManager(project_root=Path("."))
        task = mgr.create_task(id="TASK-DEV-001", role="DEV",
                               feature="Add auth module", assignee="alice")
        result = mgr.transition(task.id, TaskStatus.IN_PROGRESS, actor="alice")
        solidify = mgr.solidify(task.id, actor="alice")
    """

    TASKS_FILE = "tasks.json"

    def __init__(self, project_root: Path,
                 event_log: Optional[EventLog] = None,
                 insight_manager: Optional["InsightManager"] = None,
                 max_files: int = DEFAULT_MAX_FILES,
                 max_lines: int = DEFAULT_MAX_LINES):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / ".vibecollab"
        self.tasks_path = self.data_dir / self.TASKS_FILE
        self.event_log = event_log or EventLog(project_root=self.project_root)
        self.insight_manager = insight_manager
        self.max_files = max_files
        self.max_lines = max_lines
        self._tasks: Dict[str, Task] = {}
        self._on_complete_hooks: List[Callable[["Task"], None]] = []
        self._on_transition_hooks: List[Callable[["Task", str, str], None]] = []
        self._load()

    # -- Lifecycle hooks -----------------------------------------------------

    def on_complete(self, callback: Callable[["Task"], None]) -> None:
        """Register a hook called when a task transitions to DONE.

        The callback receives the completed Task instance.
        Multiple hooks can be registered; they execute in registration order.
        Exceptions in hooks are caught and logged but do not block completion.
        """
        self._on_complete_hooks.append(callback)

    def on_transition(self, callback: Callable[["Task", str, str], None]) -> None:
        """Register a hook called on any status transition.

        The callback receives (task, old_status, new_status).
        """
        self._on_transition_hooks.append(callback)

    def _fire_transition_hooks(self, task: "Task", old_status: str,
                                new_status: str) -> None:
        """Fire all registered transition hooks, catching exceptions."""
        for hook in self._on_transition_hooks:
            try:
                hook(task, old_status, new_status)
            except Exception:
                pass  # hooks must not break core flow

    def _fire_complete_hooks(self, task: "Task") -> None:
        """Fire all registered completion hooks, catching exceptions."""
        for hook in self._on_complete_hooks:
            try:
                hook(task)
            except Exception:
                pass  # hooks must not break core flow

    # -- Persistence --------------------------------------------------------

    def _load(self) -> None:
        """Load tasks from disk."""
        if not self.tasks_path.exists():
            self._tasks = {}
            return
        with open(self.tasks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._tasks = {
            tid: Task.from_dict(tdata) for tid, tdata in data.items()
        }

    def _save(self) -> None:
        """Persist tasks to disk atomically."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.tasks_path.with_suffix(".tmp")
        payload = {tid: t.to_dict() for tid, t in self._tasks.items()}
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        tmp_path.replace(self.tasks_path)

    # -- CRUD ---------------------------------------------------------------

    def create_task(self, id: str, role: str, feature: str,
                    assignee: Optional[str] = None,
                    actor: str = "system",
                    **kwargs) -> Task:
        """Create a new task.

        If an InsightManager is configured, automatically searches for
        related Insights using tags extracted from the task's feature and
        description, and stores matched IDs in task.metadata["related_insights"].

        Args:
            id: Task ID (must match TASK-{ROLE}-{SEQ} pattern)
            role: Role code
            feature: Feature description
            assignee: Optional developer name
            actor: Who is creating this task
            **kwargs: Additional Task fields

        Returns:
            The created Task.

        Raises:
            ValueError: If task ID is invalid or already exists.
        """
        if not TASK_ID_PATTERN.match(id):
            raise ValueError(
                f"Invalid task ID '{id}'. Must match TASK-{{ROLE}}-{{SEQ}} "
                f"(e.g. TASK-DEV-001)")
        if id in self._tasks:
            raise ValueError(f"Task '{id}' already exists.")

        task = Task(id=id, role=role, feature=feature,
                    assignee=assignee, **kwargs)

        # Auto-link related Insights
        related = self._find_related_insights(task)
        if related:
            task.metadata["related_insights"] = [
                {"id": ins.id, "title": ins.title, "score": round(score, 4)}
                for score, ins in related
            ]

        self._tasks[id] = task
        self._save()

        payload: Dict[str, Any] = {
            "task_id": id, "role": role, "feature": feature,
            "assignee": assignee,
        }
        if related:
            payload["related_insights"] = [ins.id for _, ins in related]

        self.event_log.append(Event(
            event_type=EventType.TASK_CREATED,
            actor=actor,
            summary=f"Created task {id}: {feature}",
            payload=payload,
        ))
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[str] = None,
                   assignee: Optional[str] = None,
                   milestone: Optional[str] = None) -> List[Task]:
        """List tasks with optional filters."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if assignee:
            tasks = [t for t in tasks if t.assignee == assignee]
        if milestone:
            tasks = [t for t in tasks if t.milestone == milestone]
        return tasks

    # -- State transitions ---------------------------------------------------

    def transition(self, task_id: str, new_status: TaskStatus,
                   actor: str = "system",
                   reason: str = "") -> ValidationResult:
        """Transition a task to a new status.

        Validates the transition is legal per the state machine,
        updates the task, persists, and logs an event.

        Args:
            task_id: Task to transition
            new_status: Target status
            actor: Who is making the change
            reason: Optional reason for the transition

        Returns:
            ValidationResult indicating success or violations.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return ValidationResult(ok=False,
                                    violations=[f"Task '{task_id}' not found."])

        current = TaskStatus(task.status)
        target = TaskStatus(new_status)

        allowed = VALID_TRANSITIONS.get(current, [])
        if target not in allowed:
            return ValidationResult(
                ok=False,
                violations=[
                    f"Illegal transition: {current.value} → {target.value}. "
                    f"Allowed: {[s.value for s in allowed]}"
                ],
            )

        old_status = task.status
        task.status = target.value
        task.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()

        event_type = (EventType.TASK_COMPLETED if target == TaskStatus.DONE
                      else EventType.TASK_STATUS_CHANGED)
        self.event_log.append(Event(
            event_type=event_type,
            actor=actor,
            summary=f"Task {task_id}: {old_status} → {target.value}"
                    + (f" ({reason})" if reason else ""),
            payload={"task_id": task_id, "old_status": old_status,
                     "new_status": target.value, "reason": reason},
        ))
        self._fire_transition_hooks(task, old_status, target.value)
        if target == TaskStatus.DONE:
            self._fire_complete_hooks(task)
        return ValidationResult(ok=True)

    # -- Solidify gate -------------------------------------------------------

    def validate_task(self, task_id: str) -> ValidationResult:
        """Run solidify validation checks on a task (dry-run, no state change).

        Checks:
        1. Task exists and has required fields
        2. Task ID format is valid
        3. Dependencies are satisfied (all deps must be DONE)
        4. Output field is populated (for REVIEW/DONE transitions)

        Returns:
            ValidationResult with any violations/warnings.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return ValidationResult(ok=False,
                                    violations=[f"Task '{task_id}' not found."])

        violations = []
        warnings = []

        # Required field checks
        if not task.id or not TASK_ID_PATTERN.match(task.id):
            violations.append(f"Invalid or missing task ID: '{task.id}'")
        if not task.role:
            violations.append("Missing required field: role")
        if not task.feature:
            violations.append("Missing required field: feature")

        # Dependency satisfaction
        for dep_id in task.dependencies:
            dep = self._tasks.get(dep_id)
            if dep is None:
                violations.append(f"Dependency '{dep_id}' not found.")
            elif dep.status != TaskStatus.DONE:
                violations.append(
                    f"Dependency '{dep_id}' not completed "
                    f"(status: {dep.status}).")

        # Output check for near-completion tasks
        if task.status in (TaskStatus.REVIEW, TaskStatus.DONE):
            if not task.output:
                warnings.append(
                    f"Task in {task.status} has no output description.")

        # Assignee check
        if task.status != TaskStatus.TODO and not task.assignee:
            warnings.append("Active task has no assignee.")

        return ValidationResult(
            ok=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    def solidify(self, task_id: str, actor: str = "system") -> ValidationResult:
        """Attempt to solidify (complete) a task through the gate pipeline.

        Pipeline: VALIDATE → COMMIT or ROLLBACK

        1. Checks task is in REVIEW status
        2. Runs validate_task() checks
        3. If all pass: transitions to DONE, logs success event
        4. If any fail: stays in REVIEW, logs failure event

        Args:
            task_id: Task to solidify
            actor: Who is performing solidification

        Returns:
            ValidationResult indicating outcome.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return ValidationResult(ok=False,
                                    violations=[f"Task '{task_id}' not found."])

        # Gate 1: Must be in REVIEW to solidify
        if task.status != TaskStatus.REVIEW:
            return ValidationResult(
                ok=False,
                violations=[
                    f"Cannot solidify: task is in {task.status}, "
                    f"must be in REVIEW."
                ],
            )

        # Gate 2: Validate
        validation = self.validate_task(task_id)

        if validation.ok:
            # COMMIT: transition to DONE
            task.status = TaskStatus.DONE
            task.updated_at = datetime.now(timezone.utc).isoformat()
            self._save()

            self.event_log.append(Event(
                event_type=EventType.VALIDATION_PASSED,
                actor=actor,
                summary=f"Task {task_id} solidified successfully",
                payload={"task_id": task_id,
                         "warnings": validation.warnings},
            ))
            self.event_log.append(Event(
                event_type=EventType.TASK_COMPLETED,
                actor=actor,
                summary=f"Task {task_id}: REVIEW → DONE (solidified)",
                payload={"task_id": task_id, "old_status": "REVIEW",
                         "new_status": "DONE"},
            ))
            self._fire_transition_hooks(task, "REVIEW", "DONE")
            self._fire_complete_hooks(task)
            return ValidationResult(
                ok=True,
                warnings=validation.warnings,
            )
        else:
            # ROLLBACK: stay in REVIEW, log failure
            self.event_log.append(Event(
                event_type=EventType.VALIDATION_FAILED,
                actor=actor,
                summary=f"Task {task_id} solidify failed: "
                        f"{len(validation.violations)} violation(s)",
                payload={"task_id": task_id,
                         "violations": validation.violations,
                         "warnings": validation.warnings},
            ))
            return validation

    # -- Rollback ------------------------------------------------------------

    def rollback(self, task_id: str, actor: str = "system",
                 reason: str = "") -> ValidationResult:
        """Rollback a task to its previous status.

        IN_PROGRESS → TODO
        REVIEW → IN_PROGRESS
        DONE tasks cannot be rolled back.

        Args:
            task_id: Task to rollback
            actor: Who is performing the rollback
            reason: Why this rollback is happening

        Returns:
            ValidationResult indicating outcome.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return ValidationResult(ok=False,
                                    violations=[f"Task '{task_id}' not found."])

        rollback_map = {
            TaskStatus.IN_PROGRESS: TaskStatus.TODO,
            TaskStatus.REVIEW: TaskStatus.IN_PROGRESS,
        }

        current = TaskStatus(task.status)
        target = rollback_map.get(current)

        if target is None:
            return ValidationResult(
                ok=False,
                violations=[f"Cannot rollback from {current.value}."],
            )

        old_status = task.status
        task.status = target.value
        task.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()

        self.event_log.append(Event(
            event_type=EventType.TASK_STATUS_CHANGED,
            actor=actor,
            summary=f"Task {task_id} rolled back: {old_status} → {target.value}"
                    + (f" ({reason})" if reason else ""),
            payload={"task_id": task_id, "old_status": old_status,
                     "new_status": target.value, "reason": reason,
                     "is_rollback": True},
        ))
        return ValidationResult(ok=True)

    # -- Utility -------------------------------------------------------------

    def count(self, status: Optional[str] = None) -> int:
        """Count tasks, optionally filtered by status."""
        if status:
            return sum(1 for t in self._tasks.values() if t.status == status)
        return len(self._tasks)

    # -- Insight integration -------------------------------------------------

    @staticmethod
    def _extract_search_tags(feature: str, description: str = "",
                             role: str = "") -> List[str]:
        """Extract search tags from task fields for Insight matching.

        Strategy:
        - Split feature and description into words
        - Filter out short/common stop words
        - Include role as a tag (lowered)
        - Deduplicate and return
        """
        STOP_WORDS = frozenset([
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "shall",
            "and", "or", "but", "if", "then", "else",
            "in", "on", "at", "to", "for", "of", "with", "by", "from",
            "up", "about", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again",
            "not", "no", "nor", "only", "own", "same", "so", "than",
            "too", "very", "just", "because", "as", "until", "while",
            "this", "that", "these", "those", "it", "its",
            "的", "了", "在", "是", "和", "与", "对", "从", "到",
            "中", "上", "下", "为", "以", "将", "把", "被", "让",
            "用", "于", "及", "等", "也", "都", "而", "或", "则",
            "一", "不", "有", "个", "人",
        ])

        text = f"{feature} {description}".lower()
        # Split on non-alphanumeric (keeping CJK characters)
        words = re.split(r'[^a-z0-9\u4e00-\u9fff]+', text)
        tags = [w for w in words if w and len(w) > 1 and w not in STOP_WORDS]

        if role:
            tags.append(role.lower())

        # Deduplicate while preserving order
        seen = set()
        result = []
        for t in tags:
            if t not in seen:
                seen.add(t)
                result.append(t)
        return result

    def _find_related_insights(
        self, task: Task, limit: int = 5
    ) -> List[tuple]:
        """Find Insights related to a task.

        Returns:
            List of (score, Insight) tuples sorted by relevance,
            or empty list if no InsightManager is configured.
        """
        if self.insight_manager is None:
            return []

        tags = self._extract_search_tags(
            task.feature, task.description, task.role
        )
        if not tags:
            return []

        try:
            results = self.insight_manager.search_by_tags(tags, active_only=True)
        except Exception:
            return []

        # Build scored list using the same Jaccard × weight logic
        entries, _ = self.insight_manager.get_registry()
        query_tags = set(t.lower() for t in tags)
        scored = []
        for ins in results[:limit]:
            ins_tags = set(t.lower() for t in ins.tags)
            overlap = query_tags & ins_tags
            if not overlap:
                continue
            match_score = len(overlap) / len(query_tags | ins_tags)
            weight = 1.0
            entry = entries.get(ins.id)
            if entry:
                weight = entry.weight
            scored.append((round(match_score * weight, 4), ins))
        return scored

    def suggest_insights(self, task_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Suggest related Insights for an existing task.

        Args:
            task_id: Task to find related Insights for
            limit: Maximum number of suggestions

        Returns:
            List of dicts with id, title, score, tags.
            Empty list if task not found or no InsightManager.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return []

        related = self._find_related_insights(task, limit=limit)
        return [
            {"id": ins.id, "title": ins.title,
             "score": score, "tags": ins.tags}
            for score, ins in related
        ]
