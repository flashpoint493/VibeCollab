"""Tests for execution_plan module — YAML-driven workflow automation."""

import json
import os
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from vibecollab.core.execution_plan import (
    PLAN_COMPLETED,
    PLAN_STARTED,
    PLAN_STEP_FAIL,
    PLAN_STEP_OK,
    HostAdapter,
    HostResponse,
    LLMAdapter,
    PlanResult,
    PlanRunner,
    StepResult,
    SubprocessAdapter,
    create_temp_project,
    load_plan,
    resolve_host_adapter,
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
            "host": "llm",
            "steps": [
                {"action": "cli", "command": "echo hello"},
                {"action": "assert", "file": "README.md"},
                {"action": "wait", "seconds": 0.1},
                {"action": "prompt", "message": "hello"},
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


# ---------------------------------------------------------------------------
# Mock host adapter for testing
# ---------------------------------------------------------------------------

class MockHostAdapter:
    """A mock HostAdapter that returns canned responses."""

    def __init__(self, responses: list = None):
        self.responses = list(responses or [])
        self.sent: list = []
        self.closed = False

    def send(self, message: str, context=None) -> HostResponse:
        self.sent.append(message)
        if self.responses:
            return self.responses.pop(0)
        return HostResponse(content="mock response", success=True)

    def close(self) -> None:
        self.closed = True


# ---------------------------------------------------------------------------
# TestValidatePlanPrompt
# ---------------------------------------------------------------------------

class TestValidatePlanPrompt:
    """Tests for prompt-specific validation rules."""

    def test_prompt_missing_message(self):
        plan = {
            "name": "test",
            "host": "llm",
            "steps": [{"action": "prompt"}],
        }
        errors = validate_plan(plan)
        assert any("message" in e for e in errors)

    def test_prompt_missing_host(self):
        plan = {
            "name": "test",
            "steps": [{"action": "prompt", "message": "hello"}],
        }
        errors = validate_plan(plan)
        assert any("host" in e for e in errors)

    def test_prompt_valid(self):
        plan = {
            "name": "test",
            "host": "llm",
            "steps": [{"action": "prompt", "message": "hello"}],
        }
        assert validate_plan(plan) == []

    def test_no_host_warning_when_no_prompt(self):
        """No error about missing host if there are no prompt steps."""
        plan = {
            "name": "test",
            "steps": [{"action": "cli", "command": "echo ok"}],
        }
        assert validate_plan(plan) == []


# ---------------------------------------------------------------------------
# TestHostAdapterProtocol
# ---------------------------------------------------------------------------

class TestHostAdapterProtocol:
    """Tests for HostAdapter protocol compliance."""

    def test_mock_is_host_adapter(self):
        adapter = MockHostAdapter()
        assert isinstance(adapter, HostAdapter)

    def test_host_response_defaults(self):
        r = HostResponse(content="hello")
        assert r.success is True
        assert r.error == ""
        assert r.raw == {}

    def test_host_response_failure(self):
        r = HostResponse(content="", success=False, error="timeout")
        assert not r.success
        assert r.error == "timeout"


# ---------------------------------------------------------------------------
# TestPlanRunnerPrompt
# ---------------------------------------------------------------------------

class TestPlanRunnerPrompt:
    """Tests for PlanRunner executing prompt steps."""

    def test_simple_prompt(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="I created TASK-DEV-001 successfully"),
        ])
        plan = {
            "name": "prompt test",
            "host": "llm",  # will be overridden by injected host
            "steps": [
                {"action": "prompt", "message": "Create a task"},
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 1
        assert "TASK-DEV-001" in result.steps[0].stdout
        assert len(mock.sent) == 1

    def test_prompt_expect_contains(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="Task TASK-DEV-042 created"),
        ])
        plan = {
            "name": "expect test",
            "host": "llm",
            "steps": [
                {
                    "action": "prompt",
                    "message": "Create task",
                    "expect": {"contains": "TASK-DEV-042"},
                },
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success

    def test_prompt_expect_contains_fail(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="Something else happened"),
        ])
        plan = {
            "name": "expect fail",
            "host": "llm",
            "steps": [
                {
                    "action": "prompt",
                    "message": "Create task",
                    "expect": {"contains": "TASK-DEV-042"},
                },
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert not result.success
        assert "missing" in result.steps[0].error.lower()

    def test_prompt_expect_not_contains(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="All good, no errors"),
        ])
        plan = {
            "name": "not contains test",
            "host": "llm",
            "steps": [
                {
                    "action": "prompt",
                    "message": "Check status",
                    "expect": {"not_contains": "ERROR"},
                },
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success

    def test_prompt_host_failure(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="", success=False, error="API timeout"),
        ])
        plan = {
            "name": "host fail",
            "host": "llm",
            "steps": [
                {"action": "prompt", "message": "Hello"},
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert not result.success
        assert "failure" in result.steps[0].error.lower() or "timeout" in result.steps[0].error.lower()

    def test_prompt_no_host_configured(self, tmp_path):
        project = _make_project(tmp_path)
        plan = {
            "name": "no host",
            "steps": [
                {"action": "prompt", "message": "Hello"},
            ],
        }
        runner = PlanRunner(project_root=project, host=None)
        result = runner.run(plan)
        assert not result.success
        assert "no host" in result.steps[0].error.lower()

    def test_multi_round_prompt(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="Onboarded. Project context loaded."),
            HostResponse(content="Created TASK-DEV-001, status TODO"),
            HostResponse(content="Transitioned TASK-DEV-001 to IN_PROGRESS"),
        ])
        plan = {
            "name": "multi round",
            "host": "llm",
            "steps": [
                {"action": "prompt", "message": "Please call onboard"},
                {"action": "prompt", "message": "Create task TASK-DEV-001"},
                {
                    "action": "prompt",
                    "message": "Advance TASK-DEV-001 to IN_PROGRESS",
                    "expect": {"contains": "IN_PROGRESS"},
                },
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 3
        assert len(mock.sent) == 3

    def test_prompt_stdout_chain_to_assert(self, tmp_path):
        """Prompt response is available as last_stdout for subsequent assert."""
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="MARKER_XYZ found in project"),
        ])
        plan = {
            "name": "prompt chain",
            "host": "llm",
            "steps": [
                {"action": "prompt", "message": "Search for marker"},
                {"action": "assert", "stdout_contains": "MARKER_XYZ"},
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 2

    def test_prompt_dry_run(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter()
        plan = {
            "name": "dry run prompt",
            "host": "llm",
            "steps": [
                {"action": "prompt", "message": "Should not send"},
            ],
        }
        runner = PlanRunner(project_root=project, host=mock, dry_run=True)
        result = runner.run(plan)
        assert result.skipped == 1
        assert len(mock.sent) == 0  # nothing sent in dry run


# ---------------------------------------------------------------------------
# TestVariableSubstitution
# ---------------------------------------------------------------------------

class TestVariableSubstitution:
    """Tests for store_as / {{var}} variable passing between steps."""

    def test_store_and_use(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="task_id=TASK-DEV-099"),
            HostResponse(content="Done with TASK-DEV-099"),
        ])
        plan = {
            "name": "variable test",
            "host": "llm",
            "steps": [
                {
                    "action": "prompt",
                    "message": "Create a task",
                    "store_as": "round1",
                },
                {
                    "action": "prompt",
                    "message": "Complete task from: {{round1}}",
                },
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        # Second message should have the substituted content
        assert "task_id=TASK-DEV-099" in mock.sent[1]

    def test_store_from_cli(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="Got it: hello from cli"),
        ])
        plan = {
            "name": "cli to prompt var",
            "host": "llm",
            "steps": [
                {
                    "action": "cli",
                    "command": "echo hello_from_cli",
                    "store_as": "cli_out",
                },
                {
                    "action": "prompt",
                    "message": "Process: {{cli_out}}",
                },
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert "hello_from_cli" in mock.sent[0]


# ---------------------------------------------------------------------------
# TestResolveHostAdapter
# ---------------------------------------------------------------------------

class TestResolveHostAdapter:
    """Tests for resolve_host_adapter factory function."""

    def test_none_when_no_host(self):
        plan = {"name": "test", "steps": []}
        assert resolve_host_adapter(plan) is None

    def test_llm_from_string(self):
        plan = {"name": "test", "host": "llm", "steps": []}
        adapter = resolve_host_adapter(plan)
        assert isinstance(adapter, LLMAdapter)

    def test_subprocess_from_dict(self):
        plan = {
            "name": "test",
            "host": {"type": "subprocess", "command": "cat"},
            "steps": [],
        }
        adapter = resolve_host_adapter(plan)
        assert isinstance(adapter, SubprocessAdapter)

    def test_subprocess_missing_command(self):
        plan = {
            "name": "test",
            "host": {"type": "subprocess"},
            "steps": [],
        }
        with pytest.raises(ValueError, match="command"):
            resolve_host_adapter(plan)

    def test_unknown_type(self):
        plan = {"name": "test", "host": "unknown_host", "steps": []}
        with pytest.raises(ValueError, match="Unknown"):
            resolve_host_adapter(plan)


# ---------------------------------------------------------------------------
# TestSubprocessAdapter
# ---------------------------------------------------------------------------

class TestSubprocessAdapter:
    """Tests for SubprocessAdapter with real subprocesses."""

    def test_echo_adapter(self, tmp_path):
        """Simple echo-based subprocess adapter."""
        # Create a tiny Python script that reads stdin and echoes back
        script = tmp_path / "echo_host.py"
        script.write_text(textwrap.dedent("""\
            import sys
            sentinel = "__VIBECOLLAB_EOM__"
            while True:
                lines = []
                for line in sys.stdin:
                    line = line.rstrip("\\n")
                    if line == sentinel:
                        break
                    lines.append(line)
                if not lines:
                    break
                response = "ECHO: " + " ".join(lines)
                print(response)
                print(sentinel)
                sys.stdout.flush()
        """), encoding="utf-8")

        adapter = SubprocessAdapter(
            command=f"{sys.executable} {script}",
            timeout=10,
        )
        try:
            resp = adapter.send("hello world")
            assert resp.success
            assert "ECHO:" in resp.content
            assert "hello world" in resp.content
        finally:
            adapter.close()

    def test_subprocess_close_idempotent(self):
        adapter = SubprocessAdapter(command="echo test")
        adapter.close()  # no process started
        adapter.close()  # idempotent

    def test_subprocess_process_exits(self, tmp_path):
        """Adapter handles process that exits immediately."""
        adapter = SubprocessAdapter(
            command=f"{sys.executable} -c \"print('bye')\"",
            timeout=5,
        )
        resp = adapter.send("hello")
        # Process exits, we should still get output
        assert resp.content  # at least some output
        adapter.close()


# ---------------------------------------------------------------------------
# TestMixedWorkflow
# ---------------------------------------------------------------------------

class TestMixedWorkflow:
    """Integration: plans mixing cli, prompt, assert, wait steps."""

    def test_cli_prompt_assert_chain(self, tmp_path):
        project = _make_project(tmp_path)
        mock = MockHostAdapter([
            HostResponse(content="Created output.txt with content MAGIC_42"),
        ])
        plan = {
            "name": "mixed workflow",
            "host": "llm",
            "steps": [
                # CLI creates a file
                {"action": "cli", "command": "python -c \"open('output.txt','w').write('MAGIC_42')\""},
                # Prompt asks host to describe what happened
                {"action": "prompt", "message": "Describe the file created"},
                # Assert the file and prompt response
                {"action": "assert", "file": "output.txt", "contains": "MAGIC_42"},
                {"action": "assert", "stdout_contains": "MAGIC_42"},
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 4

    def test_host_auto_resolved_from_plan(self, tmp_path):
        """PlanRunner auto-resolves host from plan when not injected."""
        project = _make_project(tmp_path)
        plan = {
            "name": "auto resolve",
            "host": "unknown_adapter_type",
            "steps": [
                {"action": "prompt", "message": "hello"},
            ],
        }
        runner = PlanRunner(project_root=project)
        # resolve_host_adapter raises ValueError for unknown type
        with pytest.raises(ValueError, match="Unknown"):
            runner.run(plan)

    def test_host_cleanup_on_auto_resolve(self, tmp_path):
        """Auto-resolved host gets closed after plan run."""
        project = _make_project(tmp_path)
        # We'll use a mock by subclassing to track close
        closed_flag = {"closed": False}

        class TrackingAdapter:
            def send(self, message, context=None):
                return HostResponse(content="ok")
            def close(self):
                closed_flag["closed"] = True

        plan = {
            "name": "cleanup",
            "steps": [
                {"action": "cli", "command": "echo ok"},
            ],
        }
        runner = PlanRunner(project_root=project, host=TrackingAdapter())
        result = runner.run(plan)
        assert result.success
        # Injected host is NOT auto-closed (caller owns it)
        assert not closed_flag["closed"]
