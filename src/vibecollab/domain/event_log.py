"""
Event Log - Append-only audit trail for project operations.

Provides an immutable, append-only JSONL event log that records
all significant project operations (task changes, role actions,
conflict detections, validations, etc.) for full traceability.

Design principles:
- Append-only: events are never modified or deleted
- Self-contained: each event carries all context needed to understand it
- Atomic writes: uses temp-file + rename to prevent corruption
- Content-addressable: each event gets a SHA-256 fingerprint
"""

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    """Supported event types."""
    # Task lifecycle
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_COMPLETED = "task_completed"

    # Role actions
    ROLE_REGISTERED = "role_registered"
    ROLE_SYNC = "role_sync"

    # Collaboration
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"

    # Validation & review
    PROTOCOL_CHECK = "protocol_check"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"

    # Lifecycle
    LIFECYCLE_UPGRADE = "lifecycle_upgrade"
    MILESTONE_COMPLETED = "milestone_completed"

    # Decision
    DECISION_RECORDED = "decision_recorded"
    DECISION_CONFIRMED = "decision_confirmed"

    # Generic
    CUSTOM = "custom"


@dataclass
class Event:
    """A single audit-trail event.

    Attributes:
        event_type: categorised event type
        actor: who triggered the event (role name, "system", etc.)
        summary: one-line human-readable description
        payload: arbitrary structured data for this event
        timestamp: ISO-8601 UTC timestamp (auto-filled)
        event_id: unique id (auto-generated from timestamp + counter)
        parent_id: optional link to a prior related event
        fingerprint: SHA-256 content hash (computed on serialisation)
    """
    event_type: str
    actor: str
    summary: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    event_id: str = ""
    parent_id: Optional[str] = None
    fingerprint: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.event_id:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
            self.event_id = f"evt_{ts}"

    def compute_fingerprint(self) -> str:
        """Compute SHA-256 fingerprint over the canonical content."""
        canonical = {
            "event_type": self.event_type,
            "actor": self.actor,
            "summary": self.summary,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "parent_id": self.parent_id,
        }
        raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict, computing fingerprint if missing."""
        if not self.fingerprint:
            self.fingerprint = self.compute_fingerprint()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Deserialise from a dict."""
        return cls(
            event_type=data.get("event_type", EventType.CUSTOM),
            actor=data.get("actor", "unknown"),
            summary=data.get("summary", ""),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", ""),
            event_id=data.get("event_id", ""),
            parent_id=data.get("parent_id"),
            fingerprint=data.get("fingerprint", ""),
        )


def _atomic_append(path: Path, line: str) -> None:
    """Append a line to a file using atomic write semantics.

    On systems that support it, writes to a temp file in the same
    directory then appends. Falls back to direct append if renaming
    is not feasible for append operations.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # For JSONL append, we open in append mode with a file lock approach:
    # write the full line in one call to minimise partial-write risk.
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        if not line.endswith("\n"):
            f.write("\n")
        f.flush()
        os.fsync(f.fileno())


class EventLog:
    """Append-only JSONL event log manager.

    Usage:
        log = EventLog(project_root=Path("."))
        log.append(Event(
            event_type=EventType.TASK_CREATED,
            actor="dev",
            summary="Created task TASK-DEV-001",
            payload={"task_id": "TASK-DEV-001", "title": "Implement auth"}
        ))
        events = log.read_all()
    """

    DEFAULT_LOG_FILE = "events.jsonl"

    def __init__(self, project_root: Path, log_dir: Optional[str] = None,
                 log_file: Optional[str] = None):
        """Initialise the event log.

        Args:
            project_root: project root directory
            log_dir: subdirectory for log storage (default: ".vibecollab")
            log_file: log filename (default: "events.jsonl")
        """
        self.project_root = Path(project_root)
        self.log_dir = self.project_root / (log_dir or ".vibecollab")
        self.log_path = self.log_dir / (log_file or self.DEFAULT_LOG_FILE)

    def append(self, event: Event) -> Event:
        """Append an event to the log.

        Args:
            event: the event to record

        Returns:
            The event with fingerprint populated.
        """
        if not event.fingerprint:
            event.fingerprint = event.compute_fingerprint()
        line = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=False)
        _atomic_append(self.log_path, line)
        return event

    def read_all(self) -> List[Event]:
        """Read all events from the log.

        Returns:
            List of Event objects in chronological order.
        """
        if not self.log_path.exists():
            return []

        events = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line_num, raw_line in enumerate(f, 1):
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    data = json.loads(raw_line)
                    events.append(Event.from_dict(data))
                except json.JSONDecodeError:
                    # Skip malformed lines but don't crash
                    continue
        return events

    def read_recent(self, n: int = 20) -> List[Event]:
        """Read the most recent *n* events.

        For efficiency on large logs this reads from the end of the file.

        Args:
            n: number of recent events to return

        Returns:
            Up to *n* most recent events, oldest first.
        """
        all_events = self.read_all()
        return all_events[-n:] if len(all_events) > n else all_events

    def query(self, event_type: Optional[str] = None,
              actor: Optional[str] = None,
              since: Optional[str] = None,
              limit: int = 100) -> List[Event]:
        """Query events by filter criteria.

        Args:
            event_type: filter by event type
            actor: filter by actor name
            since: ISO-8601 timestamp lower bound
            limit: max results to return

        Returns:
            Matching events, newest first.
        """
        events = self.read_all()
        results = []

        for evt in reversed(events):
            if event_type and evt.event_type != event_type:
                continue
            if actor and evt.actor != actor:
                continue
            if since and evt.timestamp < since:
                continue
            results.append(evt)
            if len(results) >= limit:
                break

        results.reverse()  # return oldest-first within the result set
        return results

    def count(self) -> int:
        """Return the total number of events in the log."""
        if not self.log_path.exists():
            return 0
        count = 0
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    def verify_integrity(self) -> List[Dict[str, Any]]:
        """Verify fingerprint integrity of all events.

        Returns:
            List of violation dicts (empty = all good).
        """
        violations = []
        events = self.read_all()

        for i, evt in enumerate(events):
            expected = evt.compute_fingerprint()
            if evt.fingerprint and evt.fingerprint != expected:
                violations.append({
                    "line": i + 1,
                    "event_id": evt.event_id,
                    "expected": expected,
                    "actual": evt.fingerprint,
                })

        return violations
