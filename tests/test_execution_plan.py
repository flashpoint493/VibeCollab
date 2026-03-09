"""Tests for execution_plan module — YAML-driven workflow automation."""

import json
import os
import textwrap
from pathlib import Path

import pytest
import yaml

from vibecollab.core.execution_plan import (
    PLAN_COMPLETED,
    PLAN_STARTED,
    PLAN_STEP_FAIL,
    PLAN_STEP_OK,
    PlanResult,
    PlanRunner,
    StepResult,
    create_temp_project,
    load_plan,
    validate_plan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_plan(tmp_path: Path, plan: dict) -> Path:
    """Write a plan dict to a YAML file and return the path."""
    plan_file = tmp_path / "plan.yaml"
    plan_file.write_text(yaml.dump(plan, allow_unicode=True), encoding="utf-8")
    return plan_file


def _make_project(tmp_path: Path) -> Path:
    """Create a minimal project directory for testing."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("# Test", encoding="utf-8")
    return project


# ---------------------------------------------------------------------------
# TestValidatePlan
# ---------------------------------------------------------------------------

class TestValidatePlan:
    """Tests for plan YAML validation."""

    def test_valid_plan(self):
        plan = {
            "name": "test",
            "steps": [
                {"action": "cli", "command": "echo hello"},
            ],
        }
        assert validate_plan(plan) == []

    def test_missing_name(self):
        plan = {"steps": [{"action": "cli", "command": "echo"}]}
        errors = validate_plan(plan)
        assert any("name" in e for e in errors)

    def test_missing_steps(self):
        plan = {"name": "test"}
        errors = validate_plan(plan)
        assert any("steps" in e for e in errors)

    def test_empty_steps(self):
        plan = {"name": "test", "steps": []}
        errors = validate_plan(plan)
        assert any("empty" in e for e in errors)

    def test_invalid_action(self):
        plan = {
            "name": "test",
            "steps": [{"action": "invalid_action"}],
        }
        errors = validate_plan(plan)
        assert any("invalid action" in e for e in errors)

    def test_cli_missing_command(self):
        plan = {
            "name": "test",
            "steps": [{"action": "cli"}],
        }
        errors = validate_plan(plan)
        assert any("command" in e for e in errors)

    def test_assert_missing_target(self):
        plan = {
            "name": "test",
            "steps": [{"action": "assert"}],
        }
        errors = validate_plan(plan)
        assert any("file" in e for e in errors)

    def test_wait_missing_seconds(self):
        plan = {
            "name": "test",
            "steps": [{"action": "wait"}],
        }
        errors = validate_plan(plan)
        assert any("seconds" in e for e in errors)

    def test_invalid_on_fail(self):
        plan = {
            "name": "test",
            "steps": [{"action": "cli", "command": "echo", "on_fail": "explode"}],
        }
        errors = validate_plan(plan)
        assert any("on_fail" in e for e in errors)

    def test_valid_all_actions(self):
        plan = {
            "name": "test",
            "steps": [
                {"action": "cli", "command": "echo hello"},
                {"action": "assert", "file": "README.md"},
                {"action": "wait", "seconds": 0.1},
            ],
        }
        assert validate_plan(plan) == []


# ---------------------------------------------------------------------------
# TestLoadPlan
# ---------------------------------------------------------------------------

class TestLoadPlan:
    """Tests for plan file loading."""

    def test_load_valid(self, tmp_path):
        plan_file = _write_plan(tmp_path, {
            "name": "test",
            "steps": [{"action": "cli", "command": "echo ok"}],
        })
        plan = load_plan(plan_file)
        assert plan["name"] == "test"
        assert len(plan["steps"]) == 1

    def test_load_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_plan(tmp_path / "nonexistent.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        plan_file = tmp_path / "bad.yaml"
        plan_file.write_text("not: a: valid: yaml: [", encoding="utf-8")
        with pytest.raises(Exception):
            load_plan(plan_file)

    def test_load_validation_error(self, tmp_path):
        plan_file = _write_plan(tmp_path, {"steps": []})
        with pytest.raises(ValueError, match="validation failed"):
            load_plan(plan_file)


# ---------------------------------------------------------------------------
# TestPlanRunner — CLI steps
# ---------------------------------------------------------------------------

class TestPlanRunnerCli:
    """Tests for PlanRunner executing CLI steps."""

    def test_simple_echo(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "echo test",
            "steps": [
                {"action": "cli", "command": "echo hello"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 1
        assert result.failed == 0
        assert "hello" in result.steps[0].stdout

    def test_exit_code_check(self, tmp_path):
        project = _make_project(tmp_path)
        cmd = "python -c \"raise SystemExit(42)\""
        plan = {
            "name": "exit code",
            "steps": [
                {"action": "cli", "command": cmd, "expect": {"exit_code": 42}},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success
        assert result.steps[0].exit_code == 42

    def test_nonzero_exit_fails(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "fail",
            "steps": [
                {"action": "cli", "command": "python -c \"raise SystemExit(1)\""},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert not result.success
        assert result.failed == 1

    def test_stdout_contains(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "stdout check",
            "steps": [
                {
                    "action": "cli",
                    "command": "echo vibecollab",
                    "expect": {"stdout_contains": "vibecollab"},
                },
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success

    def test_stdout_contains_missing(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "stdout miss",
            "steps": [
                {
                    "action": "cli",
                    "command": "echo hello",
                    "expect": {"exit_code": 0, "stdout_contains": "MISSING"},
                },
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert not result.success
        assert "stdout missing" in result.steps[0].error

    def test_timeout(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "timeout",
            "steps": [
                {"action": "cli", "command": "python -c \"import time; time.sleep(10)\""},
            ],
        }
        runner = PlanRunner(project_root=project, timeout=1)
        result = runner.run(plan)
        assert not result.success
        assert "Timeout" in result.steps[0].error


# ---------------------------------------------------------------------------
# TestPlanRunner — Assert steps
# ---------------------------------------------------------------------------

class TestPlanRunnerAssert:
    """Tests for PlanRunner executing assert steps."""

    def test_file_exists(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "assert exists",
            "steps": [{"action": "assert", "file": "README.md"}],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success

    def test_file_not_found(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "assert missing",
            "steps": [{"action": "assert", "file": "NONEXISTENT.md"}],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert not result.success
        assert "not found" in result.steps[0].error.lower()

    def test_file_contains(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "assert contains",
            "steps": [{"action": "assert", "file": "README.md", "contains": "Test"}],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success

    def test_file_not_contains(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "assert not contains",
            "steps": [
                {"action": "assert", "file": "README.md", "not_contains": "MISSING"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success

    def test_file_contains_fail(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "assert contains fail",
            "steps": [
                {"action": "assert", "file": "README.md", "contains": "NONEXISTENT"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert not result.success

    def test_stdout_from_previous(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "stdout chain",
            "steps": [
                {"action": "cli", "command": "echo MARKER_123"},
                {"action": "assert", "stdout_contains": "MARKER_123"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 2


# ---------------------------------------------------------------------------
# TestPlanRunner — Wait + flow control
# ---------------------------------------------------------------------------

class TestPlanRunnerFlow:
    """Tests for wait steps and on_fail flow control."""

    def test_wait_step(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "wait",
            "steps": [{"action": "wait", "seconds": 0.01}],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success

    def test_abort_on_fail(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "abort test",
            "steps": [
                {"action": "cli", "command": "python -c \"raise SystemExit(1)\""},
                {"action": "cli", "command": "echo should not run"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert not result.success
        assert result.aborted
        assert result.failed == 1
        assert result.skipped == 1
        assert result.steps[1].skipped

    def test_skip_on_fail(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "skip test",
            "steps": [
                {
                    "action": "cli",
                    "command": "python -c \"raise SystemExit(1)\"",
                    "on_fail": "skip",
                },
                {"action": "cli", "command": "echo continued"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert not result.success  # still has failures
        assert not result.aborted
        assert result.failed == 1
        assert result.passed == 1  # second step ran

    def test_continue_on_fail(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "continue test",
            "on_fail": "continue",
            "steps": [
                {"action": "cli", "command": "python -c \"raise SystemExit(1)\""},
                {"action": "cli", "command": "echo ok"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.passed == 1
        assert result.failed == 1
        assert not result.aborted

    def test_dry_run(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "dry run",
            "steps": [
                {"action": "cli", "command": "echo should not execute"},
                {"action": "cli", "command": "echo nor this"},
            ],
        }
        runner = PlanRunner(project_root=project, dry_run=True)
        result = runner.run(plan)
        assert result.skipped == 2
        assert result.passed == 0
        assert all(s.skipped for s in result.steps)


# ---------------------------------------------------------------------------
# TestPlanResult
# ---------------------------------------------------------------------------

class TestPlanResult:
    """Tests for PlanResult data structures."""

    def test_success_property(self):
        r = PlanResult(name="t", total_steps=1, passed=1)
        assert r.success

    def test_failure_property(self):
        r = PlanResult(name="t", total_steps=1, failed=1)
        assert not r.success

    def test_aborted_property(self):
        r = PlanResult(name="t", total_steps=1, aborted=True)
        assert not r.success

    def test_to_dict(self):
        r = PlanResult(name="t", total_steps=2, passed=1, failed=1)
        d = r.to_dict()
        assert d["name"] == "t"
        assert d["passed"] == 1
        assert d["failed"] == 1
        assert "success" in d

    def test_summary(self):
        r = PlanResult(name="my plan", total_steps=3, passed=2, failed=1, duration_ms=500)
        s = r.summary()
        assert "my plan" in s
        assert "FAILED" in s
        assert "500ms" in s

    def test_step_result_to_dict(self):
        sr = StepResult(
            step_index=0, action="cli", success=True,
            exit_code=0, stdout="hello", duration_ms=10,
        )
        d = sr.to_dict()
        assert d["action"] == "cli"
        assert d["success"] is True
        assert d["exit_code"] == 0


# ---------------------------------------------------------------------------
# TestEventLogIntegration
# ---------------------------------------------------------------------------

class TestEventLogIntegration:
    """Tests for optional EventLog recording."""

    def test_events_recorded(self, tmp_path):
        project = _make_project(tmp_path)
        vibecollab_dir = project / ".vibecollab"
        vibecollab_dir.mkdir()

        from vibecollab.domain.event_log import EventLog

        event_log = EventLog(project)

        plan = {
            "name": "event test",
            "steps": [{"action": "cli", "command": "echo ok"}],
        }
        runner = PlanRunner(project_root=project, event_log=event_log)
        result = runner.run(plan)
        assert result.success

        events = event_log.read_all()
        event_types = [e.event_type for e in events]
        assert PLAN_STARTED in event_types
        assert PLAN_STEP_OK in event_types
        assert PLAN_COMPLETED in event_types

    def test_no_event_log(self, tmp_path):
        """PlanRunner works fine without EventLog."""
        project = _make_project(tmp_path)
        plan = {
            "name": "no log",
            "steps": [{"action": "cli", "command": "echo ok"}],
        }
        runner = PlanRunner(project_root=project, event_log=None)
        result = runner.run(plan)
        assert result.success


# ---------------------------------------------------------------------------
# TestMultiStepWorkflow
# ---------------------------------------------------------------------------

class TestMultiStepWorkflow:
    """Integration test: multi-step workflows resembling real usage."""

    def test_create_file_then_assert(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "file workflow",
            "steps": [
                {"action": "cli", "command": "python -c \"open('output.txt','w').write('result42')\""},
                {"action": "assert", "file": "output.txt", "contains": "result42"},
                {"action": "assert", "file": "output.txt", "not_contains": "ERROR"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 3

    def test_chain_with_wait(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "chain",
            "steps": [
                {"action": "cli", "command": "echo step1"},
                {"action": "wait", "seconds": 0.01},
                {"action": "cli", "command": "echo step2"},
                {"action": "assert", "stdout_contains": "step2"},
            ],
        }
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 4
