"""Tests for the EventLog module."""

import json

import pytest

from vibecollab.domain.event_log import Event, EventLog, EventType, _atomic_append

# ---------------------------------------------------------------------------
# Event dataclass tests
# ---------------------------------------------------------------------------

class TestEvent:
    """Tests for the Event dataclass."""

    def test_event_auto_fields(self):
        """Event auto-generates timestamp and event_id."""
        evt = Event(
            event_type=EventType.TASK_CREATED,
            actor="alice",
            summary="Created task",
        )
        assert evt.timestamp != ""
        assert evt.event_id.startswith("evt_")
        assert evt.fingerprint == ""  # not computed until to_dict

    def test_event_explicit_fields(self):
        """Explicit timestamp and event_id are preserved."""
        evt = Event(
            event_type=EventType.TASK_CREATED,
            actor="bob",
            summary="test",
            timestamp="2026-01-01T00:00:00+00:00",
            event_id="evt_custom_001",
        )
        assert evt.timestamp == "2026-01-01T00:00:00+00:00"
        assert evt.event_id == "evt_custom_001"

    def test_event_fingerprint_deterministic(self):
        """Same content always produces the same fingerprint."""
        evt = Event(
            event_type=EventType.TASK_CREATED,
            actor="alice",
            summary="test",
            timestamp="2026-01-01T00:00:00+00:00",
            event_id="evt_001",
        )
        fp1 = evt.compute_fingerprint()
        fp2 = evt.compute_fingerprint()
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex length

    def test_event_fingerprint_changes_with_content(self):
        """Different content produces different fingerprints."""
        base = dict(
            event_type=EventType.TASK_CREATED,
            actor="alice",
            summary="test",
            timestamp="2026-01-01T00:00:00+00:00",
            event_id="evt_001",
        )
        evt1 = Event(**base)
        evt2 = Event(**{**base, "summary": "different"})
        assert evt1.compute_fingerprint() != evt2.compute_fingerprint()

    def test_event_to_dict(self):
        """to_dict includes all fields and computes fingerprint."""
        evt = Event(
            event_type=EventType.TASK_ASSIGNED,
            actor="bob",
            summary="Assigned task",
            payload={"task_id": "TASK-DEV-001"},
            timestamp="2026-01-01T00:00:00+00:00",
            event_id="evt_002",
        )
        d = evt.to_dict()
        assert d["event_type"] == "task_assigned"
        assert d["actor"] == "bob"
        assert d["payload"]["task_id"] == "TASK-DEV-001"
        assert d["fingerprint"] != ""

    def test_event_roundtrip(self):
        """from_dict(to_dict(evt)) preserves data."""
        evt = Event(
            event_type=EventType.CONFLICT_DETECTED,
            actor="system",
            summary="File conflict detected",
            payload={"files": ["api.py"]},
            parent_id="evt_parent",
        )
        d = evt.to_dict()
        restored = Event.from_dict(d)
        assert restored.event_type == evt.event_type
        assert restored.actor == evt.actor
        assert restored.summary == evt.summary
        assert restored.payload == evt.payload
        assert restored.parent_id == evt.parent_id
        assert restored.fingerprint == evt.fingerprint


# ---------------------------------------------------------------------------
# Atomic append tests
# ---------------------------------------------------------------------------

class TestAtomicAppend:
    """Tests for _atomic_append."""

    def test_append_creates_file(self, tmp_path):
        """Appending to a non-existent file creates it."""
        target = tmp_path / "subdir" / "log.jsonl"
        _atomic_append(target, '{"test": 1}')
        assert target.exists()
        assert target.read_text(encoding="utf-8").strip() == '{"test": 1}'

    def test_append_preserves_existing(self, tmp_path):
        """Appending does not overwrite existing content."""
        target = tmp_path / "log.jsonl"
        _atomic_append(target, "line1")
        _atomic_append(target, "line2")
        lines = target.read_text(encoding="utf-8").strip().split("\n")
        assert lines == ["line1", "line2"]

    def test_append_adds_newline(self, tmp_path):
        """Each append ends with a newline."""
        target = tmp_path / "log.jsonl"
        _atomic_append(target, "no-newline")
        content = target.read_text(encoding="utf-8")
        assert content.endswith("\n")


# ---------------------------------------------------------------------------
# EventLog tests
# ---------------------------------------------------------------------------

class TestEventLog:
    """Tests for the EventLog class."""

    @pytest.fixture
    def log(self, tmp_path):
        """Create a fresh EventLog in a temp directory."""
        return EventLog(project_root=tmp_path)

    def test_append_and_read(self, log):
        """Append an event and read it back."""
        evt = Event(
            event_type=EventType.TASK_CREATED,
            actor="alice",
            summary="Created task TASK-DEV-001",
            payload={"task_id": "TASK-DEV-001"},
        )
        returned = log.append(evt)
        assert returned.fingerprint != ""

        events = log.read_all()
        assert len(events) == 1
        assert events[0].event_type == EventType.TASK_CREATED
        assert events[0].actor == "alice"
        assert events[0].payload["task_id"] == "TASK-DEV-001"

    def test_append_multiple(self, log):
        """Multiple appends produce ordered event list."""
        for i in range(5):
            log.append(Event(
                event_type=EventType.TASK_STATUS_CHANGED,
                actor="bot",
                summary=f"Status change {i}",
                payload={"index": i},
            ))

        events = log.read_all()
        assert len(events) == 5
        for i, evt in enumerate(events):
            assert evt.payload["index"] == i

    def test_read_empty(self, log):
        """Reading an empty / non-existent log returns empty list."""
        assert log.read_all() == []

    def test_read_recent(self, log):
        """read_recent returns only the last N events."""
        for i in range(10):
            log.append(Event(
                event_type=EventType.CUSTOM,
                actor="test",
                summary=f"Event {i}",
                payload={"i": i},
            ))

        recent = log.read_recent(n=3)
        assert len(recent) == 3
        assert recent[0].payload["i"] == 7
        assert recent[2].payload["i"] == 9

    def test_query_by_type(self, log):
        """query filters by event_type."""
        log.append(Event(event_type=EventType.TASK_CREATED, actor="a", summary="t"))
        log.append(Event(event_type=EventType.CONFLICT_DETECTED, actor="b", summary="c"))
        log.append(Event(event_type=EventType.TASK_CREATED, actor="c", summary="t2"))

        results = log.query(event_type=EventType.TASK_CREATED)
        assert len(results) == 2
        assert all(e.event_type == EventType.TASK_CREATED for e in results)

    def test_query_by_actor(self, log):
        """query filters by actor."""
        log.append(Event(event_type=EventType.CUSTOM, actor="alice", summary="a"))
        log.append(Event(event_type=EventType.CUSTOM, actor="bob", summary="b"))
        log.append(Event(event_type=EventType.CUSTOM, actor="alice", summary="a2"))

        results = log.query(actor="alice")
        assert len(results) == 2

    def test_query_with_limit(self, log):
        """query respects limit parameter."""
        for i in range(20):
            log.append(Event(event_type=EventType.CUSTOM, actor="x", summary=f"e{i}"))

        results = log.query(limit=5)
        assert len(results) == 5

    def test_query_by_since(self, log):
        """query filters by since timestamp."""
        log.append(Event(
            event_type=EventType.CUSTOM, actor="a", summary="old",
            timestamp="2025-01-01T00:00:00+00:00",
        ))
        log.append(Event(
            event_type=EventType.CUSTOM, actor="a", summary="new",
            timestamp="2026-06-01T00:00:00+00:00",
        ))

        results = log.query(since="2026-01-01T00:00:00+00:00")
        assert len(results) == 1
        assert results[0].summary == "new"

    def test_count(self, log):
        """count returns correct number of events."""
        assert log.count() == 0
        log.append(Event(event_type=EventType.CUSTOM, actor="a", summary="1"))
        log.append(Event(event_type=EventType.CUSTOM, actor="a", summary="2"))
        assert log.count() == 2

    def test_verify_integrity_clean(self, log):
        """verify_integrity returns no violations for untampered log."""
        log.append(Event(event_type=EventType.TASK_CREATED, actor="a", summary="ok"))
        log.append(Event(event_type=EventType.TASK_COMPLETED, actor="b", summary="done"))

        violations = log.verify_integrity()
        assert violations == []

    def test_verify_integrity_tampered(self, log):
        """verify_integrity detects tampered fingerprints."""
        log.append(Event(event_type=EventType.CUSTOM, actor="a", summary="original"))

        # Tamper with the log file
        lines = log.log_path.read_text(encoding="utf-8").strip().split("\n")
        data = json.loads(lines[0])
        data["fingerprint"] = "0" * 64  # fake fingerprint
        log.log_path.write_text(
            json.dumps(data, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        violations = log.verify_integrity()
        assert len(violations) == 1
        assert violations[0]["actual"] == "0" * 64

    def test_malformed_lines_skipped(self, log):
        """Malformed JSONL lines are skipped without crashing."""
        log.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log.log_path, "w", encoding="utf-8") as f:
            f.write("not-json\n")
            f.write('{"event_type":"custom","actor":"a","summary":"ok"}\n')

        events = log.read_all()
        assert len(events) == 1
        assert events[0].summary == "ok"

    def test_parent_id_linkage(self, log):
        """Events can reference a parent event."""
        parent = log.append(Event(
            event_type=EventType.TASK_CREATED,
            actor="alice",
            summary="Created task",
        ))

        log.append(Event(
            event_type=EventType.TASK_ASSIGNED,
            actor="alice",
            summary="Assigned task",
            parent_id=parent.event_id,
        ))

        events = log.read_all()
        assert events[1].parent_id == events[0].event_id

    def test_log_file_location(self, tmp_path):
        """Log file is created in the expected directory."""
        log = EventLog(project_root=tmp_path, log_dir="my_logs", log_file="audit.jsonl")
        log.append(Event(event_type=EventType.CUSTOM, actor="a", summary="t"))

        expected_path = tmp_path / "my_logs" / "audit.jsonl"
        assert expected_path.exists()

    def test_unicode_payload(self, log):
        """Unicode content in payload is preserved correctly."""
        log.append(Event(
            event_type=EventType.DECISION_RECORDED,
            actor="ocarina",
            summary="Recorded decision",
            payload={"title": "多开发者支持架构设计", "choice": "方案 C"},
        ))

        events = log.read_all()
        assert events[0].payload["title"] == "多开发者支持架构设计"
        assert events[0].payload["choice"] == "方案 C"
