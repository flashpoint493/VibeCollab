"""
Roadmap Parser — ROADMAP.md ↔ TaskManager bidirectional integration.

Provides:
- Parse ROADMAP.md to extract milestone headers and inline Task ID references
- Sync ROADMAP checkbox state ↔ tasks.json status (bidirectional)
- Per-milestone progress aggregation

Design:
- Task IDs in ROADMAP.md follow the pattern TASK-{ROLE}-{SEQ} (regex)
- Milestones are identified by ### (H3) headers with version patterns (strictly)
- Checkbox state [x]/[ ] maps to DONE / not-DONE
- No vector/embedding dependency — pure deterministic ID matching
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .task_manager import TaskManager, TaskStatus

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Regex to match milestone headers: strictly ### (H3) with semantic version.
# e.g. "### v0.9.3 - Title" or "### v0.9.3 ✅"
# H2/H4/H5 are NOT accepted — users must use ### to define milestones.
MILESTONE_HEADER_RE = re.compile(
    r"^###\s+(v\d+\.\d+(?:\.\d+)?)\s*(?:-\s*(.+?))?(?:\s*[✅❌])?\s*$"
)

# Human-readable format hint for error messages
MILESTONE_FORMAT_HINT = """\
期望的里程碑标题格式:
  ### v0.1.0 - 标题描述
  ### v0.1.0 - 标题描述 ✅

Checkbox 行可通过 Task ID 关联任务:
  - [ ] 功能描述 (TASK-DEV-001)
  - [x] 已完成功能 TASK-DEV-002"""

# Regex to match Task ID references anywhere in text
TASK_ID_RE = re.compile(r"TASK-[A-Z]+-\d{3,}")

# Regex to match a checkbox line: "- [x] description" or "- [ ] description"
CHECKBOX_RE = re.compile(r"^(\s*-\s*\[)([ xX])(\]\s*.+)$")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MilestoneItem:
    """A single checklist item within a milestone."""
    line_number: int
    text: str
    checked: bool
    task_ids: List[str] = field(default_factory=list)


@dataclass
class Milestone:
    """A parsed milestone from ROADMAP.md."""
    version: str
    title: str
    line_number: int
    items: List[MilestoneItem] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def done(self) -> int:
        return sum(1 for item in self.items if item.checked)

    @property
    def progress_pct(self) -> float:
        if self.total == 0:
            return 0.0
        return round(self.done / self.total * 100, 1)


@dataclass
class SyncAction:
    """A single sync action to be applied."""
    type: str  # "task_to_done", "task_from_done", "checkbox_check", "checkbox_uncheck"
    task_id: str
    milestone: str
    detail: str


@dataclass
class RoadmapStatus:
    """Aggregated status report for all milestones."""
    milestones: List[Dict[str, Any]]
    total_items: int
    total_done: int
    total_tasks_linked: int
    unlinked_task_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestones": self.milestones,
            "total_items": self.total_items,
            "total_done": self.total_done,
            "total_tasks_linked": self.total_tasks_linked,
            "unlinked_task_ids": self.unlinked_task_ids,
        }


# ---------------------------------------------------------------------------
# RoadmapParser
# ---------------------------------------------------------------------------

class RoadmapParser:
    """Parse and sync ROADMAP.md with TaskManager.

    Usage:
        parser = RoadmapParser(project_root=Path("."))
        milestones = parser.parse()
        actions = parser.sync(direction="both")
        status = parser.status()
    """

    DEFAULT_ROADMAP = "docs/ROADMAP.md"

    def __init__(
        self,
        project_root: Path,
        task_manager: Optional[TaskManager] = None,
        roadmap_path: Optional[str] = None,
    ):
        self.project_root = Path(project_root)
        self.roadmap_file = self.project_root / (roadmap_path or self.DEFAULT_ROADMAP)
        self.task_manager = task_manager
        self._milestones: Optional[List[Milestone]] = None

    # -- Parsing ------------------------------------------------------------

    def parse(self) -> List[Milestone]:
        """Parse ROADMAP.md and extract milestones with their items.

        Returns:
            List of Milestone objects.
        """
        if not self.roadmap_file.exists():
            return []

        lines = self.roadmap_file.read_text(encoding="utf-8").splitlines()
        milestones: List[Milestone] = []
        current_milestone: Optional[Milestone] = None

        for i, line in enumerate(lines):
            # Check for milestone header
            m = MILESTONE_HEADER_RE.match(line)
            if m:
                current_milestone = Milestone(
                    version=m.group(1),
                    title=m.group(2).strip() if m.group(2) else "",
                    line_number=i + 1,
                )
                milestones.append(current_milestone)
                continue

            # Any header of level 1-3 that is NOT a milestone ends the current block
            if re.match(r"^#{1,3}\s+", line) and not MILESTONE_HEADER_RE.match(line):
                current_milestone = None
                continue

            # Check for checkbox item within a milestone
            if current_milestone is not None:
                cb = CHECKBOX_RE.match(line)
                if cb:
                    checked = cb.group(2).lower() == "x"
                    task_ids = TASK_ID_RE.findall(line)
                    item = MilestoneItem(
                        line_number=i + 1,
                        text=line.strip(),
                        checked=checked,
                        task_ids=task_ids,
                    )
                    current_milestone.items.append(item)

        self._milestones = milestones
        return milestones

    # -- Sync ---------------------------------------------------------------

    def sync(self, direction: str = "both", dry_run: bool = False) -> List[SyncAction]:
        """Synchronize ROADMAP.md ↔ tasks.json.

        Direction:
            "roadmap_to_tasks" — Checkbox [x] in ROADMAP → mark task as DONE
            "tasks_to_roadmap" — Task DONE status → check checkbox in ROADMAP
            "both" — bidirectional (tasks_to_roadmap wins on conflict)

        Args:
            direction: Sync direction
            dry_run: If True, compute actions but don't apply

        Returns:
            List of SyncAction describing what was/would be changed.
        """
        if self.task_manager is None:
            return []

        milestones = self._milestones or self.parse()
        actions: List[SyncAction] = []

        # Collect all task_id → (milestone_version, item, checked) mappings
        roadmap_tasks: Dict[str, Tuple[str, MilestoneItem]] = {}
        for ms in milestones:
            for item in ms.items:
                for tid in item.task_ids:
                    roadmap_tasks[tid] = (ms.version, item)

        # --- Direction: roadmap → tasks ---
        if direction in ("roadmap_to_tasks", "both"):
            for tid, (version, item) in roadmap_tasks.items():
                task = self.task_manager.get_task(tid)
                if task is None:
                    continue
                if item.checked and task.status != TaskStatus.DONE:
                    actions.append(SyncAction(
                        type="task_to_done",
                        task_id=tid,
                        milestone=version,
                        detail=f"ROADMAP [x] → task {tid} to DONE",
                    ))
                    if not dry_run:
                        # Force transition to DONE (skip intermediate states)
                        task.status = TaskStatus.DONE
                        task.milestone = version
                        self.task_manager._save()
                elif not item.checked and task.status == TaskStatus.DONE:
                    # Only in roadmap_to_tasks mode, uncheck means un-done
                    if direction == "roadmap_to_tasks":
                        actions.append(SyncAction(
                            type="task_from_done",
                            task_id=tid,
                            milestone=version,
                            detail=f"ROADMAP [ ] → task {tid} back to REVIEW",
                        ))
                        if not dry_run:
                            task.status = TaskStatus.REVIEW
                            self.task_manager._save()

        # --- Direction: tasks → roadmap ---
        if direction in ("tasks_to_roadmap", "both"):
            lines = self.roadmap_file.read_text(encoding="utf-8").splitlines()
            modified = False

            for tid, (version, item) in roadmap_tasks.items():
                task = self.task_manager.get_task(tid)
                if task is None:
                    continue

                # Update milestone field on task
                if task.milestone != version and not dry_run:
                    task.milestone = version
                    self.task_manager._save()

                if task.status == TaskStatus.DONE and not item.checked:
                    actions.append(SyncAction(
                        type="checkbox_check",
                        task_id=tid,
                        milestone=version,
                        detail=f"Task {tid} DONE → ROADMAP [x]",
                    ))
                    if not dry_run:
                        idx = item.line_number - 1
                        if idx < len(lines):
                            lines[idx] = CHECKBOX_RE.sub(
                                lambda m: m.group(1) + "x" + m.group(3),
                                lines[idx],
                            )
                            modified = True
                elif task.status != TaskStatus.DONE and item.checked:
                    # Only in tasks_to_roadmap mode, un-done task unchecks box
                    if direction == "tasks_to_roadmap":
                        actions.append(SyncAction(
                            type="checkbox_uncheck",
                            task_id=tid,
                            milestone=version,
                            detail=f"Task {tid} not DONE → ROADMAP [ ]",
                        ))
                        if not dry_run:
                            idx = item.line_number - 1
                            if idx < len(lines):
                                lines[idx] = CHECKBOX_RE.sub(
                                    lambda m: m.group(1) + " " + m.group(3),
                                    lines[idx],
                                )
                                modified = True

            if modified and not dry_run:
                self.roadmap_file.write_text(
                    "\n".join(lines) + "\n", encoding="utf-8"
                )

        return actions

    # -- Status -------------------------------------------------------------

    def status(self) -> RoadmapStatus:
        """Generate per-milestone progress report.

        Returns:
            RoadmapStatus with aggregated metrics.
        """
        milestones = self._milestones or self.parse()

        # Collect all task IDs referenced in ROADMAP
        roadmap_task_ids: set = set()
        milestone_data = []

        for ms in milestones:
            ms_task_ids = set()
            for item in ms.items:
                ms_task_ids.update(item.task_ids)
            roadmap_task_ids.update(ms_task_ids)

            # Per-milestone task status breakdown
            task_breakdown: Dict[str, int] = {}
            if self.task_manager:
                for tid in ms_task_ids:
                    task = self.task_manager.get_task(tid)
                    if task:
                        task_breakdown[task.status] = task_breakdown.get(task.status, 0) + 1

            milestone_data.append({
                "version": ms.version,
                "title": ms.title,
                "total_items": ms.total,
                "done_items": ms.done,
                "progress_pct": ms.progress_pct,
                "linked_tasks": len(ms_task_ids),
                "task_breakdown": task_breakdown,
            })

        # Find tasks in tasks.json NOT referenced in any ROADMAP milestone
        unlinked: List[str] = []
        if self.task_manager:
            all_tasks = self.task_manager.list_tasks()
            for t in all_tasks:
                if t.id not in roadmap_task_ids:
                    unlinked.append(t.id)

        total_items = sum(ms.total for ms in milestones)
        total_done = sum(ms.done for ms in milestones)

        return RoadmapStatus(
            milestones=milestone_data,
            total_items=total_items,
            total_done=total_done,
            total_tasks_linked=len(roadmap_task_ids),
            unlinked_task_ids=unlinked,
        )
