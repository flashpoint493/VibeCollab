"""Tests for the TaskManager module."""

import json
from pathlib import Path

import pytest

from vibecollab.event_log import EventLog, EventType
from vibecollab.task_manager import (
    Task, TaskManager, TaskStatus, ValidationResult,
    TASK_ID_PATTERN, VALID_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# Task dataclass tests
# ---------------------------------------------------------------------------

class TestTask:
    """Tests for the Task dataclass."""

    def test_task_defaults(self):
        """Task fills defaults for timestamps and status."""
        t = Task(id="TASK-DEV-001", role="DEV", feature="Add auth")
        assert t.status == TaskStatus.TODO
        assert t.created_at != ""
        assert t.updated_at != ""
        assert t.dependencies == []
        assert t.metadata == {}

    def test_task_explicit_fields(self):
        """Explicit fields are preserved."""
        t = Task(id="TASK-PM-002", role="PM", feature="Write PRD",
                 status=TaskStatus.IN_PROGRESS, assignee="bob",
                 output="PRD.md", dialogue_rounds=3)
        assert t.assignee == "bob"
        assert t.output == "PRD.md"
        assert t.dialogue_rounds == 3

    def test_task_roundtrip(self):
        """to_dict → from_dict preserves data."""
        t = Task(id="TASK-DEV-003", role="DEV", feature="Fix bug",
                 assignee="alice", dependencies=["TASK-DEV-001"],
                 metadata={"priority": "high"})
        d = t.to_dict()
        restored = Task.from_dict(d)
        assert restored.id == t.id
        assert restored.dependencies == ["TASK-DEV-001"]
        assert restored.metadata == {"priority": "high"}

    def test_task_id_pattern_valid(self):
        """Valid task IDs match the pattern."""
        assert TASK_ID_PATTERN.match("TASK-DEV-001")
        assert TASK_ID_PATTERN.match("TASK-PM-012")
        assert TASK_ID_PATTERN.match("TASK-ARCH-1000")

    def test_task_id_pattern_invalid(self):
        """Invalid task IDs do not match."""
        assert not TASK_ID_PATTERN.match("TASK-dev-001")    # lowercase
        assert not TASK_ID_PATTERN.match("TASK-DEV-01")     # too few digits
        assert not TASK_ID_PATTERN.match("task-DEV-001")    # lowercase prefix
        assert not TASK_ID_PATTERN.match("DEV-001")         # missing TASK prefix
        assert not TASK_ID_PATTERN.match("")


# ---------------------------------------------------------------------------
# State machine tests
# ---------------------------------------------------------------------------

class TestStateMachine:
    """Tests for VALID_TRANSITIONS."""

    def test_todo_can_start(self):
        assert TaskStatus.IN_PROGRESS in VALID_TRANSITIONS[TaskStatus.TODO]

    def test_in_progress_can_review_or_pause(self):
        allowed = VALID_TRANSITIONS[TaskStatus.IN_PROGRESS]
        assert TaskStatus.REVIEW in allowed
        assert TaskStatus.TODO in allowed

    def test_review_can_complete_or_reject(self):
        allowed = VALID_TRANSITIONS[TaskStatus.REVIEW]
        assert TaskStatus.DONE in allowed
        assert TaskStatus.IN_PROGRESS in allowed

    def test_done_is_terminal(self):
        assert VALID_TRANSITIONS[TaskStatus.DONE] == []


# ---------------------------------------------------------------------------
# ValidationResult tests
# ---------------------------------------------------------------------------

class TestValidationResult:

    def test_ok_result(self):
        r = ValidationResult(ok=True)
        assert r.ok
        assert r.violations == []

    def test_failed_result(self):
        r = ValidationResult(ok=False, violations=["bad field"])
        assert not r.ok
        assert "bad field" in r.violations

    def test_to_dict(self):
        r = ValidationResult(ok=True, warnings=["minor issue"])
        d = r.to_dict()
        assert d["ok"] is True
        assert d["warnings"] == ["minor issue"]


# ---------------------------------------------------------------------------
# TaskManager tests
# ---------------------------------------------------------------------------

class TestTaskManager:
    """Tests for TaskManager lifecycle."""

    @pytest.fixture
    def mgr(self, tmp_path):
        """Create a fresh TaskManager with EventLog in temp dir."""
        return TaskManager(project_root=tmp_path)

    # -- Create ---

    def test_create_task(self, mgr):
        """Create a task and verify it persists."""
        task = mgr.create_task(id="TASK-DEV-001", role="DEV",
                               feature="Add auth", assignee="alice",
                               actor="ocarina")
        assert task.id == "TASK-DEV-001"
        assert task.status == TaskStatus.TODO
        assert task.assignee == "alice"

        # Verify persistence
        loaded = mgr.get_task("TASK-DEV-001")
        assert loaded is not None
        assert loaded.feature == "Add auth"

    def test_create_duplicate_raises(self, mgr):
        """Creating a task with duplicate ID raises ValueError."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        with pytest.raises(ValueError, match="already exists"):
            mgr.create_task(id="TASK-DEV-001", role="DEV", feature="B")

    def test_create_invalid_id_raises(self, mgr):
        """Creating a task with invalid ID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid task ID"):
            mgr.create_task(id="bad-id", role="DEV", feature="X")

    def test_create_logs_event(self, mgr):
        """Creating a task logs a TASK_CREATED event."""
        mgr.create_task(id="TASK-DEV-001", role="DEV",
                        feature="Add auth", actor="alice")
        events = mgr.event_log.read_all()
        assert len(events) == 1
        assert events[0].event_type == EventType.TASK_CREATED
        assert events[0].actor == "alice"
        assert "TASK-DEV-001" in events[0].summary

    # -- List / Get ---

    def test_list_tasks(self, mgr):
        """list_tasks returns all tasks."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.create_task(id="TASK-DEV-002", role="DEV", feature="B")
        assert len(mgr.list_tasks()) == 2

    def test_list_tasks_filter_status(self, mgr):
        """list_tasks filters by status."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.create_task(id="TASK-DEV-002", role="DEV", feature="B")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="x")
        assert len(mgr.list_tasks(status=TaskStatus.TODO)) == 1
        assert len(mgr.list_tasks(status=TaskStatus.IN_PROGRESS)) == 1

    def test_list_tasks_filter_assignee(self, mgr):
        """list_tasks filters by assignee."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A",
                        assignee="alice")
        mgr.create_task(id="TASK-DEV-002", role="DEV", feature="B",
                        assignee="bob")
        assert len(mgr.list_tasks(assignee="alice")) == 1

    def test_get_task_not_found(self, mgr):
        """get_task returns None for unknown ID."""
        assert mgr.get_task("TASK-NONE-999") is None

    # -- Transition ---

    def test_transition_todo_to_in_progress(self, mgr):
        """Legal transition: TODO → IN_PROGRESS."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        result = mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS,
                                actor="alice")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.IN_PROGRESS

    def test_transition_in_progress_to_review(self, mgr):
        """Legal transition: IN_PROGRESS → REVIEW."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        result = mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        assert result.ok

    def test_transition_review_to_done(self, mgr):
        """Legal transition: REVIEW → DONE."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        result = mgr.transition("TASK-DEV-001", TaskStatus.DONE, actor="a")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.DONE

    def test_transition_illegal_todo_to_done(self, mgr):
        """Illegal transition: TODO → DONE is rejected."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        result = mgr.transition("TASK-DEV-001", TaskStatus.DONE, actor="a")
        assert not result.ok
        assert "Illegal transition" in result.violations[0]

    def test_transition_illegal_done_to_anything(self, mgr):
        """DONE is terminal — no transitions allowed."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.DONE, actor="a")
        result = mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS,
                                actor="a")
        assert not result.ok

    def test_transition_not_found(self, mgr):
        """Transition on nonexistent task returns violation."""
        result = mgr.transition("TASK-NONE-001", TaskStatus.DONE, actor="a")
        assert not result.ok
        assert "not found" in result.violations[0]

    def test_transition_logs_event(self, mgr):
        """Transitions log TASK_STATUS_CHANGED events."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS,
                        actor="alice", reason="starting work")
        events = mgr.event_log.query(
            event_type=EventType.TASK_STATUS_CHANGED)
        assert len(events) == 1
        assert events[0].payload["old_status"] == "TODO"
        assert events[0].payload["new_status"] == "IN_PROGRESS"

    def test_transition_to_done_logs_completed(self, mgr):
        """Transitioning to DONE logs TASK_COMPLETED event."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.DONE, actor="a")
        events = mgr.event_log.query(event_type=EventType.TASK_COMPLETED)
        assert len(events) == 1

    def test_transition_pause_back_to_todo(self, mgr):
        """IN_PROGRESS → TODO (pause) is allowed."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        result = mgr.transition("TASK-DEV-001", TaskStatus.TODO,
                                actor="a", reason="blocked")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.TODO

    def test_transition_reject_review(self, mgr):
        """REVIEW → IN_PROGRESS (reject) is allowed."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        result = mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS,
                                actor="a", reason="needs rework")
        assert result.ok

    # -- Validate ---

    def test_validate_valid_task(self, mgr):
        """Valid task passes validation."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A",
                        assignee="alice")
        result = mgr.validate_task("TASK-DEV-001")
        assert result.ok

    def test_validate_missing_dependency(self, mgr):
        """Task with unsatisfied dependency fails validation."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A",
                        dependencies=["TASK-DEV-999"])
        result = mgr.validate_task("TASK-DEV-001")
        assert not result.ok
        assert any("TASK-DEV-999" in v for v in result.violations)

    def test_validate_incomplete_dependency(self, mgr):
        """Task with non-DONE dependency fails validation."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="Dep")
        mgr.create_task(id="TASK-DEV-002", role="DEV", feature="Main",
                        dependencies=["TASK-DEV-001"])
        result = mgr.validate_task("TASK-DEV-002")
        assert not result.ok
        assert any("not completed" in v for v in result.violations)

    def test_validate_satisfied_dependency(self, mgr):
        """Task with DONE dependency passes validation."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="Dep")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.DONE, actor="a")
        mgr.create_task(id="TASK-DEV-002", role="DEV", feature="Main",
                        dependencies=["TASK-DEV-001"], assignee="bob")
        result = mgr.validate_task("TASK-DEV-002")
        assert result.ok

    def test_validate_warns_no_output_in_review(self, mgr):
        """Task in REVIEW with no output gets a warning."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A",
                        assignee="alice")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        result = mgr.validate_task("TASK-DEV-001")
        assert result.ok  # warnings don't block
        assert len(result.warnings) > 0

    def test_validate_not_found(self, mgr):
        """Validating nonexistent task fails."""
        result = mgr.validate_task("TASK-NONE-001")
        assert not result.ok

    # -- Solidify ---

    def test_solidify_success(self, mgr):
        """Solidify succeeds for valid task in REVIEW."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A",
                        assignee="alice", output="auth.py")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        result = mgr.solidify("TASK-DEV-001", actor="alice")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.DONE

    def test_solidify_logs_validation_passed_and_completed(self, mgr):
        """Successful solidify logs both VALIDATION_PASSED and TASK_COMPLETED."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A",
                        assignee="alice", output="auth.py")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        mgr.solidify("TASK-DEV-001", actor="alice")

        passed = mgr.event_log.query(event_type=EventType.VALIDATION_PASSED)
        completed = mgr.event_log.query(event_type=EventType.TASK_COMPLETED)
        assert len(passed) == 1
        assert len(completed) == 1
        assert "solidified" in completed[0].summary

    def test_solidify_fails_not_in_review(self, mgr):
        """Solidify fails if task is not in REVIEW."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        result = mgr.solidify("TASK-DEV-001", actor="a")
        assert not result.ok
        assert "must be in REVIEW" in result.violations[0]

    def test_solidify_fails_with_unsatisfied_deps(self, mgr):
        """Solidify fails if dependencies are not DONE."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="Dep")
        mgr.create_task(id="TASK-DEV-002", role="DEV", feature="Main",
                        dependencies=["TASK-DEV-001"], assignee="bob")
        mgr.transition("TASK-DEV-002", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-002", TaskStatus.REVIEW, actor="a")
        result = mgr.solidify("TASK-DEV-002", actor="a")
        assert not result.ok
        assert mgr.get_task("TASK-DEV-002").status == TaskStatus.REVIEW

    def test_solidify_failure_logs_validation_failed(self, mgr):
        """Failed solidify logs VALIDATION_FAILED event."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="Dep")
        mgr.create_task(id="TASK-DEV-002", role="DEV", feature="Main",
                        dependencies=["TASK-DEV-001"])
        mgr.transition("TASK-DEV-002", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-002", TaskStatus.REVIEW, actor="a")
        mgr.solidify("TASK-DEV-002", actor="a")

        failed = mgr.event_log.query(event_type=EventType.VALIDATION_FAILED)
        assert len(failed) == 1
        assert "violation" in failed[0].summary

    def test_solidify_not_found(self, mgr):
        """Solidify on nonexistent task fails."""
        result = mgr.solidify("TASK-NONE-001", actor="a")
        assert not result.ok

    # -- Rollback ---

    def test_rollback_in_progress_to_todo(self, mgr):
        """Rollback IN_PROGRESS → TODO."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        result = mgr.rollback("TASK-DEV-001", actor="a", reason="blocked")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.TODO

    def test_rollback_review_to_in_progress(self, mgr):
        """Rollback REVIEW → IN_PROGRESS."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        result = mgr.rollback("TASK-DEV-001", actor="a", reason="rework")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.IN_PROGRESS

    def test_rollback_done_fails(self, mgr):
        """Cannot rollback from DONE."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="a")
        mgr.transition("TASK-DEV-001", TaskStatus.DONE, actor="a")
        result = mgr.rollback("TASK-DEV-001", actor="a")
        assert not result.ok

    def test_rollback_todo_fails(self, mgr):
        """Cannot rollback from TODO."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        result = mgr.rollback("TASK-DEV-001", actor="a")
        assert not result.ok

    def test_rollback_logs_event(self, mgr):
        """Rollback logs event with is_rollback flag."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        mgr.rollback("TASK-DEV-001", actor="a", reason="blocked")
        events = mgr.event_log.query(
            event_type=EventType.TASK_STATUS_CHANGED)
        rollback_events = [e for e in events
                           if e.payload.get("is_rollback")]
        assert len(rollback_events) == 1
        assert rollback_events[0].payload["reason"] == "blocked"

    def test_rollback_not_found(self, mgr):
        """Rollback on nonexistent task fails."""
        result = mgr.rollback("TASK-NONE-001", actor="a")
        assert not result.ok

    # -- Persistence ---

    def test_persistence_across_instances(self, tmp_path):
        """Tasks survive TaskManager reload."""
        mgr1 = TaskManager(project_root=tmp_path)
        mgr1.create_task(id="TASK-DEV-001", role="DEV", feature="A",
                         assignee="alice")
        mgr1.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")

        # Create new instance, should load from disk
        mgr2 = TaskManager(project_root=tmp_path)
        task = mgr2.get_task("TASK-DEV-001")
        assert task is not None
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.assignee == "alice"

    def test_count(self, mgr):
        """count returns correct numbers."""
        assert mgr.count() == 0
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="A")
        mgr.create_task(id="TASK-DEV-002", role="DEV", feature="B")
        assert mgr.count() == 2
        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="a")
        assert mgr.count(status=TaskStatus.TODO) == 1
        assert mgr.count(status=TaskStatus.IN_PROGRESS) == 1

    # -- Full lifecycle ---

    def test_full_lifecycle(self, mgr):
        """Exercise the complete task lifecycle: create → start → review → solidify."""
        # Create
        task = mgr.create_task(id="TASK-DEV-001", role="DEV",
                               feature="Implement auth module",
                               assignee="alice", output="auth.py",
                               actor="ocarina")
        assert task.status == TaskStatus.TODO

        # Start
        result = mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS,
                                actor="alice", reason="starting implementation")
        assert result.ok

        # Review
        result = mgr.transition("TASK-DEV-001", TaskStatus.REVIEW,
                                actor="alice", reason="ready for review")
        assert result.ok

        # Solidify
        result = mgr.solidify("TASK-DEV-001", actor="ocarina")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.DONE

        # Verify full event trail
        all_events = mgr.event_log.read_all()
        event_types = [e.event_type for e in all_events]
        assert EventType.TASK_CREATED in event_types
        assert EventType.TASK_STATUS_CHANGED in event_types
        assert EventType.VALIDATION_PASSED in event_types
        assert EventType.TASK_COMPLETED in event_types

    def test_full_lifecycle_with_rejection(self, mgr):
        """Lifecycle with reject: create → start → review → reject → rework → review → solidify."""
        mgr.create_task(id="TASK-DEV-001", role="DEV", feature="Auth",
                        assignee="alice", output="auth.py")

        mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="alice")
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="alice")

        # Reject
        result = mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS,
                                actor="reviewer", reason="needs tests")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.IN_PROGRESS

        # Rework and re-submit
        mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="alice")

        # Solidify succeeds this time
        result = mgr.solidify("TASK-DEV-001", actor="reviewer")
        assert result.ok
        assert mgr.get_task("TASK-DEV-001").status == TaskStatus.DONE

    def test_unicode_feature(self, mgr):
        """Unicode in feature and output fields is preserved."""
        task = mgr.create_task(id="TASK-DEV-001", role="DEV",
                               feature="实现用户认证模块",
                               output="认证服务代码")
        assert task.feature == "实现用户认证模块"
        # Reload
        mgr._load()
        assert mgr.get_task("TASK-DEV-001").feature == "实现用户认证模块"
