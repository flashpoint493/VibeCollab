"""
Project Health Signal Extractor

Extract project health signals from EventLog, TaskManager, ProtocolChecker,
generate structured health reports for project evolution decisions and automated monitoring.

DECISION-009 Iteration 4: Auto-evolution — Signal extraction pattern.

Signal levels:
  - CRITICAL: Must be handled immediately (integrity breach, severe protocol violation)
  - WARNING:  Needs attention (backlog, bottleneck, outdated docs)
  - INFO:     Reference information (activity, progress, trends)
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..domain.event_log import EventLog, EventType
from ..domain.task_manager import TaskManager
from .protocol_checker import ProtocolChecker


class SignalLevel(str, Enum):
    """Signal severity level"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Signal:
    """Single health signal"""
    name: str
    level: SignalLevel
    category: str
    value: Any
    message: str
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["level"] = self.level.value
        return d


@dataclass
class HealthReport:
    """Project health report"""
    timestamp: str = ""
    signals: List[Signal] = field(default_factory=list)
    score: float = 0.0
    summary: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def critical_count(self) -> int:
        return sum(1 for s in self.signals if s.level == SignalLevel.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for s in self.signals if s.level == SignalLevel.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for s in self.signals if s.level == SignalLevel.INFO)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "score": round(self.score, 1),
            "critical": self.critical_count,
            "warnings": self.warning_count,
            "infos": self.info_count,
            "signals": [s.to_dict() for s in self.signals],
            "summary": self.summary,
        }


class HealthExtractor:
    """Project health signal extractor

    Extracts signals from three data sources:
      1. ProtocolChecker — Protocol compliance check
      2. EventLog — Audit log analysis (activity, integrity, conflicts)
      3. TaskManager — Task progress and quality
    """

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        self.project_root = Path(project_root)
        self.config = config

    def extract(self) -> HealthReport:
        """Execute full signal extraction and return health report"""
        report = HealthReport()

        self._extract_protocol_signals(report)
        self._extract_eventlog_signals(report)
        self._extract_task_signals(report)

        report.score = self._calculate_score(report)
        report.summary = {
            "score": round(report.score, 1),
            "grade": self._score_to_grade(report.score),
            "critical": report.critical_count,
            "warnings": report.warning_count,
            "infos": report.info_count,
            "total_signals": len(report.signals),
        }
        return report

    # ── Protocol Checker Signals ──────────────────────────────

    def _extract_protocol_signals(self, report: HealthReport):
        """Extract protocol compliance signals from ProtocolChecker"""
        try:
            checker = ProtocolChecker(self.project_root, self.config)
            results = checker.check_all()
            summary = checker.get_summary(results)
        except Exception:
            report.signals.append(Signal(
                name="protocol_checker_unavailable",
                level=SignalLevel.WARNING,
                category="protocol",
                value=None,
                message="Protocol checker initialization failed",
                suggestion="Check if project configuration is complete",
            ))
            return

        errors = summary.get("errors", 0)
        warnings = summary.get("warnings", 0)

        if errors > 0:
            report.signals.append(Signal(
                name="protocol_errors",
                level=SignalLevel.CRITICAL,
                category="protocol",
                value=errors,
                message=f"Found {errors} protocol violation error(s)",
                suggestion="Run `vibecollab check` for details and fix",
            ))

        if warnings > 0:
            report.signals.append(Signal(
                name="protocol_warnings",
                level=SignalLevel.WARNING,
                category="protocol",
                value=warnings,
                message=f"Found {warnings} protocol warning(s)",
                suggestion="Check if documents need updating",
            ))

        if summary.get("all_passed", False):
            report.signals.append(Signal(
                name="protocol_compliance",
                level=SignalLevel.INFO,
                category="protocol",
                value=True,
                message="All protocol checks passed",
            ))

    # ── EventLog Signals ──────────────────────────────────────

    def _extract_eventlog_signals(self, report: HealthReport):
        """Extract audit log signals from EventLog"""
        try:
            log = EventLog(self.project_root)
        except Exception:
            return

        # Signal 1: Log integrity
        try:
            violations = log.verify_integrity()
            if violations:
                report.signals.append(Signal(
                    name="log_integrity",
                    level=SignalLevel.CRITICAL,
                    category="integrity",
                    value=len(violations),
                    message=f"Event log has {len(violations)} integrity issue(s)",
                    suggestion="Check if .vibecollab/events.jsonl was tampered with",
                ))
            else:
                report.signals.append(Signal(
                    name="log_integrity",
                    level=SignalLevel.INFO,
                    category="integrity",
                    value=0,
                    message="Event log integrity verification passed",
                ))
        except Exception:
            pass

        # Signal 2: Project activity
        try:
            total_events = log.count()
            report.signals.append(Signal(
                name="total_events",
                level=SignalLevel.INFO,
                category="activity",
                value=total_events,
                message=f"Total {total_events} event records",
            ))

            seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            recent = log.query(since=seven_days_ago)
            if len(recent) == 0 and total_events > 0:
                report.signals.append(Signal(
                    name="project_inactive",
                    level=SignalLevel.WARNING,
                    category="activity",
                    value=0,
                    message="No project activity in the past 7 days",
                    suggestion="Check if the project is stalled",
                ))
        except Exception:
            pass

        # Signal 3: Unresolved conflicts
        try:
            conflicts_detected = log.query(event_type=EventType.CONFLICT_DETECTED.value)
            conflicts_resolved = log.query(event_type=EventType.CONFLICT_RESOLVED.value)
            unresolved = len(conflicts_detected) - len(conflicts_resolved)
            if unresolved > 0:
                report.signals.append(Signal(
                    name="unresolved_conflicts",
                    level=SignalLevel.WARNING,
                    category="collaboration",
                    value=unresolved,
                    message=f"{unresolved} unresolved conflict(s)",
                    suggestion="Run `vibecollab dev conflicts` for conflict details",
                ))
        except Exception:
            pass

        # Signal 4: Validation failure rate
        try:
            failures = log.query(event_type=EventType.VALIDATION_FAILED.value)
            passes = log.query(event_type=EventType.VALIDATION_PASSED.value)
            total_validations = len(failures) + len(passes)
            if total_validations > 0:
                fail_rate = len(failures) / total_validations
                level = (SignalLevel.WARNING if fail_rate > 0.3
                         else SignalLevel.INFO)
                report.signals.append(Signal(
                    name="validation_fail_rate",
                    level=level,
                    category="quality",
                    value=round(fail_rate, 2),
                    message=f"Validation failure rate {fail_rate:.0%} ({len(failures)}/{total_validations})",
                    suggestion="Check task quality and solidification process" if fail_rate > 0.3 else None,
                ))
        except Exception:
            pass

    # ── Task Manager Signals ──────────────────────────────────

    def _extract_task_signals(self, report: HealthReport):
        """Extract task progress signals from TaskManager"""
        try:
            mgr = TaskManager(self.project_root)
        except Exception:
            return

        total = mgr.count()
        if total == 0:
            report.signals.append(Signal(
                name="no_tasks",
                level=SignalLevel.INFO,
                category="tasks",
                value=0,
                message="No task records",
            ))
            return

        done = mgr.count(status="DONE")
        todo = mgr.count(status="TODO")
        in_progress = mgr.count(status="IN_PROGRESS")
        in_review = mgr.count(status="REVIEW")

        # Signal 1: Task completion rate
        completion_rate = done / total
        report.signals.append(Signal(
            name="task_completion_rate",
            level=SignalLevel.INFO,
            category="tasks",
            value=round(completion_rate, 2),
            message=f"Task completion rate {completion_rate:.0%} ({done}/{total})",
        ))

        # Signal 2: Backlog detection
        if todo > 5:
            report.signals.append(Signal(
                name="task_backlog",
                level=SignalLevel.WARNING,
                category="tasks",
                value=todo,
                message=f"{todo} backlog TODO tasks",
                suggestion="Consider prioritizing or splitting tasks",
            ))

        # Signal 3: Review bottleneck
        active = in_progress + in_review + todo
        if active > 0 and in_review / active > 0.5:
            report.signals.append(Signal(
                name="review_bottleneck",
                level=SignalLevel.WARNING,
                category="tasks",
                value=in_review,
                message=f"{in_review} tasks awaiting review ({in_review/active:.0%} of active tasks)",
                suggestion="Speed up review process to avoid blocking",
            ))

        # Signal 4: Task distribution
        report.signals.append(Signal(
            name="task_distribution",
            level=SignalLevel.INFO,
            category="tasks",
            value={"todo": todo, "in_progress": in_progress, "review": in_review, "done": done},
            message=f"Task distribution: TODO={todo} IN_PROGRESS={in_progress} REVIEW={in_review} DONE={done}",
        ))

        # Signal 5: Dependency blocking
        try:
            all_tasks = mgr.list_tasks()
            blocked = []
            for task in all_tasks:
                if task.status == "DONE":
                    continue
                for dep_id in (task.dependencies or []):
                    dep = mgr.get_task(dep_id)
                    if dep and dep.status != "DONE":
                        blocked.append(task.id)
                        break

            if blocked:
                report.signals.append(Signal(
                    name="dependency_blocked",
                    level=SignalLevel.WARNING,
                    category="tasks",
                    value=len(blocked),
                    message=f"{len(blocked)} task(s) blocked by dependencies: {', '.join(blocked[:5])}",
                    suggestion="Prioritize completing prerequisite tasks in the blocking chain",
                ))
        except Exception:
            pass

        # Signal 6: Load balancing
        try:
            from collections import Counter
            active_tasks = [t for t in mgr.list_tasks() if t.status != "DONE" and t.assignee]
            if len(active_tasks) >= 2:
                load = Counter(t.assignee for t in active_tasks)
                values = list(load.values())
                avg = sum(values) / len(values)
                if len(values) > 1:
                    variance = sum((v - avg) ** 2 for v in values) / len(values)
                    std_dev = variance ** 0.5
                    if std_dev > avg * 0.5 and avg > 0:
                        report.signals.append(Signal(
                            name="load_imbalance",
                            level=SignalLevel.WARNING,
                            category="collaboration",
                            value=dict(load),
                            message=f"Load imbalance: {dict(load)}",
                            suggestion="Consider reassigning tasks",
                        ))
        except Exception:
            pass

    # ── Scoring ───────────────────────────────────────────────

    @staticmethod
    def _calculate_score(report: HealthReport) -> float:
        """Calculate health score based on signals (0-100)

        Scoring rules:
          - Base score 100
          - Each CRITICAL: -25
          - Each WARNING: -10
          - Minimum 0
        """
        score = 100.0
        score -= report.critical_count * 25
        score -= report.warning_count * 10
        return max(0.0, min(100.0, score))

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert score to grade"""
        if score >= 90:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"
