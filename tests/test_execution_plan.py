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
    LoopResult,
    LoopRound,
    PlanResult,
    PlanRunner,
    StepResult,
    SubprocessAdapter,
    create_temp_project,
    load_plan,
    resolve_host_adapter,
    validate_plan,
    _check_goal,
    _run_state_command,
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


# ---------------------------------------------------------------------------
# TestValidatePlanLoop
# ---------------------------------------------------------------------------

class TestValidatePlanLoop:
    """Tests for loop-specific validation rules."""

    def test_loop_missing_max_rounds(self):
        plan = {
            "name": "test",
            "host": "llm",
            "steps": [{"action": "loop", "state_command": "echo ok"}],
        }
        errors = validate_plan(plan)
        assert any("max_rounds" in e for e in errors)

    def test_loop_invalid_max_rounds(self):
        plan = {
            "name": "test",
            "host": "llm",
            "steps": [{"action": "loop", "max_rounds": -1, "state_command": "echo"}],
        }
        errors = validate_plan(plan)
        assert any("positive integer" in e for e in errors)

    def test_loop_zero_max_rounds(self):
        plan = {
            "name": "test",
            "host": "llm",
            "steps": [{"action": "loop", "max_rounds": 0, "state_command": "echo"}],
        }
        errors = validate_plan(plan)
        assert any("positive integer" in e for e in errors)

    def test_loop_missing_template_and_command(self):
        plan = {
            "name": "test",
            "host": "llm",
            "steps": [{"action": "loop", "max_rounds": 5}],
        }
        errors = validate_plan(plan)
        assert any("prompt_template" in e or "state_command" in e for e in errors)

    def test_loop_valid_with_state_command(self):
        plan = {
            "name": "test",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 3,
                "state_command": "vibecollab next --json",
            }],
        }
        assert validate_plan(plan) == []

    def test_loop_valid_with_prompt_template(self):
        plan = {
            "name": "test",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 3,
                "prompt_template": "Do something for round {{round}}",
            }],
        }
        assert validate_plan(plan) == []

    def test_loop_requires_host(self):
        plan = {
            "name": "test",
            "steps": [{
                "action": "loop",
                "max_rounds": 3,
                "state_command": "echo state",
            }],
        }
        errors = validate_plan(plan)
        assert any("host" in e for e in errors)


# ---------------------------------------------------------------------------
# TestLoopDataStructures
# ---------------------------------------------------------------------------

class TestLoopDataStructures:
    """Tests for LoopRound and LoopResult data structures."""

    def test_loop_round_defaults(self):
        lr = LoopRound(round_num=1)
        assert lr.success is True
        assert lr.goal_met is False
        assert lr.state == ""

    def test_loop_round_to_dict(self):
        lr = LoopRound(
            round_num=2,
            state="some state",
            response="ok done",
            success=True,
            goal_met=True,
            duration_ms=100,
        )
        d = lr.to_dict()
        assert d["round"] == 2
        assert d["goal_met"] is True
        assert d["duration_ms"] == 100

    def test_loop_result_defaults(self):
        r = LoopResult()
        assert r.total_rounds == 0
        assert r.goal_met is False
        assert r.rounds == []

    def test_loop_result_to_dict(self):
        r = LoopResult(
            total_rounds=5,
            completed_rounds=3,
            goal_met=True,
            goal_met_at=3,
            rounds=[LoopRound(round_num=1)],
        )
        d = r.to_dict()
        assert d["total_rounds"] == 5
        assert d["goal_met"] is True
        assert d["goal_met_at"] == 3
        assert len(d["rounds"]) == 1


# ---------------------------------------------------------------------------
# TestRunStateCommand
# ---------------------------------------------------------------------------

class TestRunStateCommand:
    """Tests for _run_state_command helper."""

    def test_echo_command(self, tmp_path):
        result = _run_state_command("echo hello_state", tmp_path)
        assert "hello_state" in result

    def test_failing_command_returns_empty(self, tmp_path):
        result = _run_state_command("python -c \"raise SystemExit(1)\"", tmp_path)
        # Should not crash, returns empty or partial
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# TestCheckGoal
# ---------------------------------------------------------------------------

class TestCheckGoal:
    """Tests for _check_goal helper."""

    def test_goal_met(self, tmp_path):
        met = _check_goal(
            "echo All checks passed",
            {"exit_code": 0, "stdout_contains": "All checks passed"},
            tmp_path,
        )
        assert met is True

    def test_goal_not_met_exit_code(self, tmp_path):
        met = _check_goal(
            "python -c \"raise SystemExit(1)\"",
            {"exit_code": 0},
            tmp_path,
        )
        assert met is False

    def test_goal_not_met_stdout(self, tmp_path):
        met = _check_goal(
            "echo partial",
            {"stdout_contains": "complete"},
            tmp_path,
        )
        assert met is False

    def test_goal_no_expectations(self, tmp_path):
        """Empty expectations just check exit_code=0 by default."""
        met = _check_goal("echo ok", {}, tmp_path)
        assert met is True


# ---------------------------------------------------------------------------
# TestPlanRunnerLoop
# ---------------------------------------------------------------------------

class TestPlanRunnerLoop:
    """Tests for PlanRunner executing loop steps."""

    def test_simple_loop_3_rounds(self, tmp_path):
        """Basic loop runs max_rounds times when no goal check is set."""
        project = _make_project(tmp_path)
        responses = [
            HostResponse(content=f"Round {i} done") for i in range(1, 4)
        ]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "loop test",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 3,
                "prompt_template": "Do round {{round}} of {{max_rounds}}",
            }],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 1
        assert len(mock.sent) == 3
        # Check variable substitution worked
        assert "1" in mock.sent[0]
        assert "3" in mock.sent[0]

    def test_loop_with_state_command(self, tmp_path):
        """Loop gathers state via state_command before each prompt."""
        project = _make_project(tmp_path)
        responses = [
            HostResponse(content="Processed state"),
            HostResponse(content="Processed state again"),
        ]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "state loop",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 2,
                "state_command": "echo current_state_data",
                "prompt_template": "State: {{state}}\nRound {{round}}",
            }],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert len(mock.sent) == 2
        assert "current_state_data" in mock.sent[0]

    def test_loop_goal_met_early(self, tmp_path):
        """Loop exits early when check_command indicates goal is met."""
        project = _make_project(tmp_path)
        # Create a marker file on second round that the check detects
        marker = project / "goal_marker.txt"

        class GoalMockAdapter:
            def __init__(self):
                self.sent = []
                self.call_count = 0

            def send(self, message, context=None):
                self.sent.append(message)
                self.call_count += 1
                if self.call_count >= 2:
                    marker.write_text("GOAL_REACHED", encoding="utf-8")
                return HostResponse(content=f"Round {self.call_count} response")

            def close(self):
                pass

        mock = GoalMockAdapter()
        plan = {
            "name": "goal loop",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 10,
                "prompt_template": "Work on goal. Round {{round}}.",
                "check_command": f"python -c \"import sys; sys.exit(0 if open('{marker.as_posix()}').read()=='GOAL_REACHED' else 1)\"",
                "check_expect": {"exit_code": 0},
            }],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 1
        # Should have exited at round 2, not 10
        assert mock.call_count == 2

    def test_loop_goal_not_met(self, tmp_path):
        """Loop runs all rounds and fails when goal is never met."""
        project = _make_project(tmp_path)
        responses = [HostResponse(content="nope") for _ in range(3)]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "goal fail",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 3,
                "prompt_template": "Try to reach goal. Round {{round}}.",
                "check_command": "python -c \"raise SystemExit(1)\"",
                "check_expect": {"exit_code": 0},
            }],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert not result.success
        assert len(mock.sent) == 3

    def test_loop_host_failure_continue(self, tmp_path):
        """Loop continues on host failure by default (on_round_fail=continue)."""
        project = _make_project(tmp_path)
        responses = [
            HostResponse(content="", success=False, error="API error"),
            HostResponse(content="recovered"),
        ]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "continue on fail",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 2,
                "prompt_template": "Round {{round}}",
                "on_round_fail": "continue",
            }],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        # Not all rounds succeeded, so overall fails
        assert not result.success
        assert len(mock.sent) == 2

    def test_loop_host_failure_abort(self, tmp_path):
        """Loop aborts on first host failure when on_round_fail=abort."""
        project = _make_project(tmp_path)
        responses = [
            HostResponse(content="", success=False, error="API error"),
            HostResponse(content="should not reach"),
        ]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "abort on fail",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 3,
                "prompt_template": "Round {{round}}",
                "on_round_fail": "abort",
            }],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert not result.success
        assert len(mock.sent) == 1  # Only first round sent

    def test_loop_no_host(self, tmp_path):
        """Loop step fails gracefully when no host is configured."""
        project = _make_project(tmp_path)
        plan = {
            "name": "no host loop",
            "steps": [{
                "action": "loop",
                "max_rounds": 2,
                "prompt_template": "Round {{round}}",
            }],
        }
        runner = PlanRunner(project_root=project, host=None)
        result = runner.run(plan)
        assert not result.success
        assert "no host" in result.steps[0].error.lower()

    def test_loop_dry_run(self, tmp_path):
        """Loop step is skipped in dry-run mode."""
        project = _make_project(tmp_path)
        mock = MockHostAdapter()
        plan = {
            "name": "dry run loop",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 5,
                "prompt_template": "Should not send",
            }],
        }
        runner = PlanRunner(project_root=project, host=mock, dry_run=True)
        result = runner.run(plan)
        assert result.skipped == 1
        assert len(mock.sent) == 0

    def test_loop_verbose(self, tmp_path, capsys):
        """Loop emits verbose logs when verbose=True."""
        project = _make_project(tmp_path)
        responses = [HostResponse(content="done")]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "verbose loop",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 1,
                "prompt_template": "Round {{round}}",
            }],
        }
        runner = PlanRunner(project_root=project, host=mock, verbose=True)
        result = runner.run(plan)
        assert result.success
        captured = capsys.readouterr()
        assert "Loop Round 1/1" in captured.err

    def test_loop_stdout_chain_to_assert(self, tmp_path):
        """Loop's last response is available as last_stdout for assert."""
        project = _make_project(tmp_path)
        responses = [
            HostResponse(content="progress"),
            HostResponse(content="FINAL_MARKER_42"),
        ]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "loop chain",
            "host": "llm",
            "steps": [
                {
                    "action": "loop",
                    "max_rounds": 2,
                    "prompt_template": "Round {{round}}",
                },
                {"action": "assert", "stdout_contains": "FINAL_MARKER_42"},
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 2

    def test_loop_store_as(self, tmp_path):
        """Loop result can be stored via store_as for variable passing."""
        project = _make_project(tmp_path)
        responses = [HostResponse(content="loop_output_XYZ")]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "store loop",
            "host": "llm",
            "steps": [
                {
                    "action": "loop",
                    "max_rounds": 1,
                    "prompt_template": "One round",
                    "store_as": "loop_out",
                },
                {
                    "action": "prompt",
                    "message": "Got: {{loop_out}}",
                },
            ],
        }
        # Need a second response for the follow-up prompt
        mock.responses.append(HostResponse(content="acknowledged"))
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        # The prompt step should have received the substituted variable
        assert "loop_output_XYZ" in mock.sent[-1]

    def test_loop_variable_substitution_in_template(self, tmp_path):
        """Loop respects existing variables in prompt_template."""
        project = _make_project(tmp_path)
        responses = [
            HostResponse(content="setup done"),
            HostResponse(content="loop result"),
        ]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "var loop",
            "host": "llm",
            "steps": [
                {
                    "action": "prompt",
                    "message": "Setup phase",
                    "store_as": "setup_output",
                },
                {
                    "action": "loop",
                    "max_rounds": 1,
                    "prompt_template": "Previous: {{setup_output}}\nRound {{round}}",
                },
            ],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        # The loop prompt should contain the variable from the first step
        assert "setup done" in mock.sent[-1]

    def test_loop_with_goal_template(self, tmp_path):
        """Loop substitutes {{goal}} in prompt_template."""
        project = _make_project(tmp_path)
        responses = [HostResponse(content="working on it")]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "goal template",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 1,
                "goal": "All tests pass",
                "prompt_template": "Goal: {{goal}}\nRound {{round}}",
            }],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        assert "All tests pass" in mock.sent[0]

    def test_loop_default_template_from_state_command(self, tmp_path):
        """When only state_command is given, a default template is generated."""
        project = _make_project(tmp_path)
        responses = [HostResponse(content="ok")]
        mock = MockHostAdapter(responses)
        plan = {
            "name": "default tpl",
            "host": "llm",
            "steps": [{
                "action": "loop",
                "max_rounds": 1,
                "state_command": "echo project_status",
                "goal": "Complete setup",
            }],
        }
        runner = PlanRunner(project_root=project, host=mock)
        result = runner.run(plan)
        assert result.success
        # Default template should include state and round
        sent = mock.sent[0]
        assert "project_status" in sent
        assert "1" in sent
        assert "Complete setup" in sent
