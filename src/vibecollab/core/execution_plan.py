"""
Execution Plan - YAML-driven multi-round workflow automation.

A lightweight plan runner that reads a YAML execution plan and drives
steps through existing VibeCollab CLI commands, domain APIs, and host
adapters (LLM / subprocess / MCP).

Design principles:
- Single file, not a sub-package
- Zero new dependencies: subprocess (stdlib) + PyYAML (existing)
- Declarative: plans are human-written YAML, not LLM-generated
- Protocol-aware: understands VibeCollab's task/insight/event model
- Reuses existing modules: EventLog for audit, TaskManager for state

Step actions:
  cli     — Run a shell command via subprocess.run
  assert  — Check file existence / content / previous stdout
  wait    — time.sleep(seconds)
  prompt  — Send a message to a HostAdapter and check the response
  loop    — Autonomous multi-round dialogue with dynamic state feedback

Host adapters (for 'prompt' and 'loop' steps):
  HostAdapter is a minimal Protocol (send + close). Built-in adapters:
  - LLMAdapter:        Calls LLM API directly (reuses llm_client.py)
  - SubprocessAdapter: Drives any stdin/stdout CLI tool as host

Plan format examples:

  Linear plan:
    name: "Multi-round task workflow"
    host: llm
    steps:
      - action: prompt
        message: "Please call onboard, then create task TASK-DEV-001"
        expect:
          contains: "TASK-DEV-001"

  Autonomous loop:
    name: "Iterate project 50 rounds"
    host: llm
    steps:
      - action: loop
        max_rounds: 50
        goal: "All vibecollab check items pass"
        state_command: "vibecollab next --json"
        prompt_template: |
          Current project state:
          {{state}}
          Round {{round}} of {{max_rounds}}.
          Follow the recommended next steps.
        check_command: "vibecollab check"
        check_expect:
          exit_code: 0
          stdout_contains: "All checks passed"

See DECISION-018 for architecture rationale.
"""

import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Python 3.9 compat: runtime_checkable Protocol
try:
    from typing import Protocol, runtime_checkable
except ImportError:
    from typing_extensions import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Event types for plan execution (extend EventLog.EventType)
# ---------------------------------------------------------------------------

PLAN_STARTED = "plan_started"
PLAN_STEP_OK = "plan_step_ok"
PLAN_STEP_FAIL = "plan_step_fail"
PLAN_COMPLETED = "plan_completed"
PLAN_ABORTED = "plan_aborted"


# ---------------------------------------------------------------------------
# Host Adapter — protocol for driving external hosts
# ---------------------------------------------------------------------------

@dataclass
class HostResponse:
    """Response from a host adapter."""
    content: str
    success: bool = True
    error: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class HostAdapter(Protocol):
    """Minimal protocol for driving an external host.

    A host is anything that can receive a text message and return a text
    response: an LLM API, a subprocess CLI tool, an MCP client, etc.
    """

    def send(self, message: str, context: Optional[Dict[str, Any]] = None) -> HostResponse:
        """Send a message and block until a response is received."""
        ...

    def close(self) -> None:
        """Release resources (connections, processes, etc.)."""
        ...


class LLMAdapter:
    """Host adapter that calls an LLM API via llm_client.

    Lazily imports llm_client so that LLM dependencies (httpx) are only
    required when actually using this adapter.

    The adapter maintains a conversation history so that multi-round
    prompt steps share context within a single plan run.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        system_prompt: str = "",
        **llm_kwargs: Any,
    ):
        self._project_root = project_root
        self._system_prompt = system_prompt
        self._llm_kwargs = llm_kwargs
        self._client = None
        self._messages: list = []  # conversation history

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        from vibecollab.agent.llm_client import (
            LLMClient, LLMConfig, Message, build_project_context,
        )
        self._Message = Message
        config = LLMConfig(**self._llm_kwargs) if self._llm_kwargs else LLMConfig()
        self._client = LLMClient(config=config)

        # Build system message with project context
        system = self._system_prompt or (
            "You are an AI assistant working on a VibeCollab-managed project. "
            "Follow the project's collaboration protocol. "
            "Use the available VibeCollab CLI commands and MCP tools as needed."
        )
        if self._project_root:
            ctx = build_project_context(self._project_root)
            system += f"\n\n# Project Context\n\n{ctx}"
        self._messages.append(self._Message(role="system", content=system))

    def send(self, message: str, context: Optional[Dict[str, Any]] = None) -> HostResponse:
        self._ensure_client()
        self._messages.append(self._Message(role="user", content=message))
        try:
            resp = self._client.chat(self._messages, temperature=0.3)
            self._messages.append(self._Message(role="assistant", content=resp.content))
            return HostResponse(
                content=resp.content,
                success=resp.ok,
                raw=resp.raw,
            )
        except Exception as e:
            return HostResponse(content="", success=False, error=str(e))

    def close(self) -> None:
        self._messages.clear()
        self._client = None


class SubprocessAdapter:
    """Host adapter that drives a subprocess via stdin/stdout.

    Starts a long-running process (e.g. ``claude``, ``aider``, or any
    interactive CLI) and communicates through its stdin/stdout pipes.

    The adapter sends a message followed by an end-of-message sentinel,
    then reads lines until it sees the sentinel echoed back or the
    process exits.

    Args:
        command: Shell command to start the host process.
        sentinel: Marker string to delimit message boundaries.
            Defaults to ``"__VIBECOLLAB_EOM__"``.
        timeout: Max seconds to wait for a response.
        cwd: Working directory for the subprocess.
    """

    def __init__(
        self,
        command: str,
        sentinel: str = "__VIBECOLLAB_EOM__",
        timeout: int = 120,
        cwd: Optional[Path] = None,
    ):
        self._command = command
        self._sentinel = sentinel
        self._timeout = timeout
        self._cwd = str(cwd) if cwd else None
        self._proc: Optional[subprocess.Popen] = None

    def _ensure_proc(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            return
        self._proc = subprocess.Popen(
            self._command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self._cwd,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def send(self, message: str, context: Optional[Dict[str, Any]] = None) -> HostResponse:
        self._ensure_proc()
        assert self._proc is not None and self._proc.stdin and self._proc.stdout

        try:
            # Write message + sentinel
            self._proc.stdin.write(message + "\n" + self._sentinel + "\n")
            self._proc.stdin.flush()

            # Read until sentinel or timeout
            lines: List[str] = []
            deadline = time.monotonic() + self._timeout
            while time.monotonic() < deadline:
                if self._proc.poll() is not None:
                    # Process exited; drain remaining output
                    rest = self._proc.stdout.read()
                    if rest:
                        lines.append(rest)
                    break
                # Non-blocking read attempt with small timeout
                line = self._proc.stdout.readline()
                if not line:
                    time.sleep(0.05)
                    continue
                if self._sentinel in line:
                    break
                lines.append(line)
            else:
                return HostResponse(
                    content="".join(lines),
                    success=False,
                    error=f"Timeout after {self._timeout}s",
                )

            content = "".join(lines).strip()
            return HostResponse(content=content, success=True)

        except Exception as e:
            return HostResponse(content="", success=False, error=str(e))

    def close(self) -> None:
        if self._proc is not None:
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
            self._proc = None


# Adapter factory — resolve 'host' field from YAML plan
ADAPTER_REGISTRY: Dict[str, type] = {
    "llm": LLMAdapter,
    "subprocess": SubprocessAdapter,
}


def resolve_host_adapter(
    plan: Dict[str, Any],
    project_root: Optional[Path] = None,
) -> Optional["HostAdapter"]:
    """Create a HostAdapter from a plan's 'host' configuration.

    The 'host' field can be:
      - A string: adapter type name (e.g. "llm", "subprocess")
      - A dict:   {"type": "subprocess", "command": "claude", ...}
      - Absent:   returns None (plan has no prompt steps)
    """
    host_cfg = plan.get("host")
    if host_cfg is None:
        return None

    if isinstance(host_cfg, str):
        host_type = host_cfg
        host_opts: Dict[str, Any] = {}
    elif isinstance(host_cfg, dict):
        host_type = host_cfg.get("type", "")
        host_opts = {k: v for k, v in host_cfg.items() if k != "type"}
    else:
        return None

    if host_type == "llm":
        return LLMAdapter(project_root=project_root, **host_opts)
    elif host_type == "subprocess":
        command = host_opts.pop("command", "")
        if not command:
            raise ValueError("SubprocessAdapter requires 'command' in host config")
        return SubprocessAdapter(command=command, cwd=project_root, **host_opts)
    else:
        raise ValueError(
            f"Unknown host adapter type: '{host_type}'. "
            f"Available: {sorted(ADAPTER_REGISTRY.keys())}"
        )


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    """Result of a single plan step execution."""
    step_index: int
    action: str
    success: bool
    duration_ms: int = 0
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    skipped: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "step_index": self.step_index,
            "action": self.action,
            "success": self.success,
            "duration_ms": self.duration_ms,
        }
        if self.exit_code is not None:
            d["exit_code"] = self.exit_code
        if self.stdout:
            d["stdout"] = self.stdout[:500]  # truncate for readability
        if self.stderr:
            d["stderr"] = self.stderr[:500]
        if self.error:
            d["error"] = self.error
        if self.skipped:
            d["skipped"] = True
        return d


@dataclass
class PlanResult:
    """Aggregate result of an entire plan execution."""
    name: str
    total_steps: int
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_ms: int = 0
    steps: List[StepResult] = field(default_factory=list)
    aborted: bool = False
    abort_reason: str = ""

    @property
    def success(self) -> bool:
        return self.failed == 0 and not self.aborted

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "success": self.success,
            "total_steps": self.total_steps,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_ms": self.duration_ms,
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
            "steps": [s.to_dict() for s in self.steps],
        }

    def summary(self) -> str:
        status = "PASSED" if self.success else "FAILED"
        return (
            f"Plan '{self.name}': {status} "
            f"({self.passed}/{self.total_steps} passed, "
            f"{self.failed} failed, {self.skipped} skipped) "
            f"in {self.duration_ms}ms"
        )


# ---------------------------------------------------------------------------
# Plan validation
# ---------------------------------------------------------------------------

VALID_ACTIONS = {"cli", "assert", "wait", "prompt", "loop"}
VALID_ON_FAIL = {"abort", "skip", "continue"}


def validate_plan(plan: Dict[str, Any]) -> List[str]:
    """Validate a plan dict structure. Returns list of error messages."""
    errors: List[str] = []

    if "name" not in plan:
        errors.append("Plan missing required field: 'name'")
    if "steps" not in plan:
        errors.append("Plan missing required field: 'steps'")
        return errors
    if not isinstance(plan["steps"], list):
        errors.append("'steps' must be a list")
        return errors
    if len(plan["steps"]) == 0:
        errors.append("'steps' must not be empty")

    has_prompt = False
    for i, step in enumerate(plan["steps"]):
        prefix = f"Step {i}"
        if not isinstance(step, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue
        action = step.get("action")
        if action not in VALID_ACTIONS:
            errors.append(
                f"{prefix}: invalid action '{action}', "
                f"must be one of {sorted(VALID_ACTIONS)}"
            )
        if action == "cli" and "command" not in step:
            errors.append(f"{prefix}: 'cli' action requires 'command'")
        if action == "assert" and "file" not in step and "stdout_contains" not in step:
            errors.append(
                f"{prefix}: 'assert' action requires 'file' or 'stdout_contains'"
            )
        if action == "wait" and "seconds" not in step:
            errors.append(f"{prefix}: 'wait' action requires 'seconds'")
        if action == "prompt":
            has_prompt = True
            if "message" not in step:
                errors.append(f"{prefix}: 'prompt' action requires 'message'")
        if action == "loop":
            has_prompt = True
            if "max_rounds" not in step:
                errors.append(f"{prefix}: 'loop' action requires 'max_rounds'")
            elif not isinstance(step["max_rounds"], int) or step["max_rounds"] < 1:
                errors.append(f"{prefix}: 'max_rounds' must be a positive integer")
            if "prompt_template" not in step and "state_command" not in step:
                errors.append(
                    f"{prefix}: 'loop' action requires at least "
                    f"'prompt_template' or 'state_command'"
                )

        on_fail = step.get("on_fail", "abort")
        if on_fail not in VALID_ON_FAIL:
            errors.append(
                f"{prefix}: invalid on_fail '{on_fail}', "
                f"must be one of {sorted(VALID_ON_FAIL)}"
            )

    # If plan uses prompt steps, it should declare a host adapter
    if has_prompt and "host" not in plan:
        errors.append(
            "Plan uses 'prompt' steps but missing 'host' field. "
            "Set host to 'llm', 'subprocess', or a config dict."
        )

    return errors


def load_plan(path: Path) -> Dict[str, Any]:
    """Load and validate a YAML plan file.

    Raises:
        FileNotFoundError: if plan file does not exist
        ValueError: if plan has validation errors
    """
    if not path.exists():
        raise FileNotFoundError(f"Plan file not found: {path}")
    with open(path, encoding="utf-8") as f:
        plan = yaml.safe_load(f)
    if not isinstance(plan, dict):
        raise ValueError("Plan file must contain a YAML mapping")
    errors = validate_plan(plan)
    if errors:
        raise ValueError(
            f"Plan validation failed ({len(errors)} errors):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
    return plan


# ---------------------------------------------------------------------------
# Step executors
# ---------------------------------------------------------------------------

def _exec_cli(
    step: Dict[str, Any],
    project_root: Path,
    timeout: int,
) -> StepResult:
    """Execute a CLI command step."""
    command = step["command"]
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            encoding="utf-8",
            errors="replace",
        )
        # Check expectations
        expect = step.get("expect", {})
        success = True
        error_parts: List[str] = []

        expected_exit = expect.get("exit_code")
        if expected_exit is not None and result.returncode != expected_exit:
            success = False
            error_parts.append(
                f"exit_code: expected {expected_exit}, got {result.returncode}"
            )
        elif expected_exit is None and result.returncode != 0:
            success = False
            error_parts.append(f"exit_code: {result.returncode}")

        stdout_contains = expect.get("stdout_contains")
        if stdout_contains and stdout_contains not in result.stdout:
            success = False
            error_parts.append(f"stdout missing: '{stdout_contains}'")

        stderr_contains = expect.get("stderr_contains")
        if stderr_contains and stderr_contains not in result.stderr:
            success = False
            error_parts.append(f"stderr missing: '{stderr_contains}'")

        return StepResult(
            step_index=0,  # filled by caller
            action="cli",
            success=success,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            error="; ".join(error_parts) if error_parts else "",
        )
    except subprocess.TimeoutExpired:
        return StepResult(
            step_index=0,
            action="cli",
            success=False,
            error=f"Timeout after {timeout}s",
        )
    except BaseException as e:
        return StepResult(
            step_index=0,
            action="cli",
            success=False,
            error=str(e),
        )


def _exec_assert(
    step: Dict[str, Any],
    project_root: Path,
    last_stdout: str,
) -> StepResult:
    """Execute a file/content assertion step."""
    error_parts: List[str] = []

    # File existence + content check
    file_path = step.get("file")
    if file_path:
        full_path = project_root / file_path
        if not full_path.exists():
            error_parts.append(f"File not found: {file_path}")
        else:
            contains = step.get("contains")
            if contains:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                if contains not in content:
                    error_parts.append(
                        f"File '{file_path}' does not contain '{contains}'"
                    )

            not_contains = step.get("not_contains")
            if not_contains:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                if not_contains in content:
                    error_parts.append(
                        f"File '{file_path}' unexpectedly contains '{not_contains}'"
                    )

    # Stdout from previous step
    stdout_contains = step.get("stdout_contains")
    if stdout_contains and stdout_contains not in (last_stdout or ""):
        error_parts.append(f"Previous stdout missing: '{stdout_contains}'")

    return StepResult(
        step_index=0,
        action="assert",
        success=len(error_parts) == 0,
        error="; ".join(error_parts) if error_parts else "",
    )


def _exec_wait(step: Dict[str, Any]) -> StepResult:
    """Execute a wait/delay step."""
    seconds = step.get("seconds", 1)
    time.sleep(seconds)
    return StepResult(
        step_index=0,
        action="wait",
        success=True,
    )


def _exec_prompt(
    step: Dict[str, Any],
    host: "HostAdapter",
    variables: Dict[str, str],
) -> StepResult:
    """Execute a prompt step via a HostAdapter.

    Sends the message to the host, checks response against expectations,
    and optionally stores the response for later steps.
    """
    message = step["message"]

    # Simple variable substitution: {{var_name}} → stored value
    for key, value in variables.items():
        message = message.replace("{{" + key + "}}", value)

    try:
        resp = host.send(message)
    except Exception as e:
        return StepResult(
            step_index=0,
            action="prompt",
            success=False,
            stdout=str(e),
            error=f"Host send failed: {e}",
        )

    if not resp.success:
        return StepResult(
            step_index=0,
            action="prompt",
            success=False,
            stdout=resp.content,
            error=resp.error or "Host returned failure",
        )

    # Check expectations
    expect = step.get("expect", {})
    error_parts: List[str] = []

    contains = expect.get("contains")
    if contains and contains not in resp.content:
        error_parts.append(f"Response missing: '{contains}'")

    not_contains = expect.get("not_contains")
    if not_contains and not_contains in resp.content:
        error_parts.append(f"Response unexpectedly contains: '{not_contains}'")

    return StepResult(
        step_index=0,
        action="prompt",
        success=len(error_parts) == 0,
        stdout=resp.content,
        error="; ".join(error_parts) if error_parts else "",
    )


# ---------------------------------------------------------------------------
# Loop result — tracks per-round detail for autonomous loop steps
# ---------------------------------------------------------------------------

@dataclass
class LoopRound:
    """Result of a single round within a loop step."""
    round_num: int
    state: str = ""
    prompt_sent: str = ""
    response: str = ""
    success: bool = True
    goal_met: bool = False
    error: str = ""
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round": self.round_num,
            "success": self.success,
            "goal_met": self.goal_met,
            "duration_ms": self.duration_ms,
            "state_preview": self.state[:200] if self.state else "",
            "response_preview": self.response[:200] if self.response else "",
            "error": self.error,
        }


@dataclass
class LoopResult:
    """Aggregate result of a loop step execution."""
    total_rounds: int = 0
    completed_rounds: int = 0
    goal_met: bool = False
    goal_met_at: int = 0
    rounds: List[LoopRound] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rounds": self.total_rounds,
            "completed_rounds": self.completed_rounds,
            "goal_met": self.goal_met,
            "goal_met_at": self.goal_met_at,
            "error": self.error,
            "rounds": [r.to_dict() for r in self.rounds],
        }


def _run_state_command(
    command: str,
    project_root: Path,
    timeout: int = 30,
) -> str:
    """Run a state-gathering command and return its stdout."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _check_goal(
    check_command: str,
    check_expect: Dict[str, Any],
    project_root: Path,
    timeout: int = 30,
) -> bool:
    """Run a goal-check command and verify expectations."""
    try:
        result = subprocess.run(
            check_command,
            shell=True,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            encoding="utf-8",
            errors="replace",
        )
        # Check exit code
        expected_exit = check_expect.get("exit_code")
        if expected_exit is not None and result.returncode != expected_exit:
            return False
        elif expected_exit is None and result.returncode != 0:
            return False

        # Check stdout
        stdout_contains = check_expect.get("stdout_contains")
        if stdout_contains and stdout_contains not in result.stdout:
            return False

        return True
    except Exception:
        return False


def _exec_loop(
    step: Dict[str, Any],
    host: "HostAdapter",
    variables: Dict[str, str],
    project_root: Path,
    timeout: int = 120,
    vlog=None,
) -> StepResult:
    """Execute an autonomous multi-round loop step.

    Each round:
      1. Run state_command (if configured) → capture project state
      2. Compose prompt from prompt_template with {{state}}, {{round}}, etc.
      3. Send prompt to host via HostAdapter
      4. Optionally run check_command to test if goal is met
      5. Repeat until goal met or max_rounds reached

    The loop shares the host's conversation history, so each round
    builds on the previous context.
    """
    max_rounds = step.get("max_rounds", 10)
    state_command = step.get("state_command", "")
    prompt_template = step.get("prompt_template", "")
    goal = step.get("goal", "")
    check_command = step.get("check_command", "")
    check_expect = step.get("check_expect", {})
    on_round_fail = step.get("on_round_fail", "continue")  # continue | abort
    state_timeout = step.get("state_timeout", 30)

    # Default prompt template if only state_command is provided
    if not prompt_template and state_command:
        prompt_template = (
            "Current project state:\n{{state}}\n\n"
            "Round {{round}} of {{max_rounds}}."
        )
        if goal:
            prompt_template += f"\nGoal: {goal}"
        prompt_template += "\nFollow the recommended next steps and make progress."

    loop_result = LoopResult(total_rounds=max_rounds)

    for round_num in range(1, max_rounds + 1):
        round_start = time.monotonic()
        lr = LoopRound(round_num=round_num)

        if vlog:
            vlog(f"")
            vlog(f"  ┌── Loop Round {round_num}/{max_rounds} ──")

        # 1. Gather state
        state = ""
        if state_command:
            # Variable substitution in state_command
            cmd = state_command
            for key, value in variables.items():
                cmd = cmd.replace("{{" + key + "}}", value)
            state = _run_state_command(cmd, project_root, timeout=state_timeout)
            lr.state = state
            if vlog:
                preview = state[:150].replace("\n", " | ")
                vlog(f"  │ state: {preview}")

        # 2. Compose prompt
        prompt = prompt_template
        for key, value in variables.items():
            prompt = prompt.replace("{{" + key + "}}", value)
        prompt = prompt.replace("{{state}}", state)
        prompt = prompt.replace("{{round}}", str(round_num))
        prompt = prompt.replace("{{max_rounds}}", str(max_rounds))
        if goal:
            prompt = prompt.replace("{{goal}}", goal)
        lr.prompt_sent = prompt

        if vlog:
            preview = prompt[:100].replace("\n", " ")
            vlog(f"  │ prompt: {preview}...")

        # 3. Send to host
        try:
            resp = host.send(prompt)
        except Exception as e:
            lr.error = f"Host send failed: {e}"
            lr.success = False
            lr.duration_ms = int((time.monotonic() - round_start) * 1000)
            loop_result.rounds.append(lr)
            if vlog:
                vlog(f"  │ [FAIL] {lr.error}")
                vlog(f"  └── Round {round_num} FAILED ({lr.duration_ms}ms)")
            if on_round_fail == "abort":
                loop_result.error = lr.error
                break
            continue

        lr.response = resp.content
        lr.success = resp.success

        if not resp.success:
            lr.error = resp.error or "Host returned failure"
            lr.duration_ms = int((time.monotonic() - round_start) * 1000)
            loop_result.rounds.append(lr)
            if vlog:
                vlog(f"  │ [FAIL] host error: {lr.error}")
                vlog(f"  └── Round {round_num} FAILED ({lr.duration_ms}ms)")
            if on_round_fail == "abort":
                loop_result.error = lr.error
                break
            continue

        if vlog:
            preview = resp.content[:150].replace("\n", " | ")
            vlog(f"  │ response: {preview}")

        # 4. Check goal
        if check_command:
            goal_met = _check_goal(check_command, check_expect, project_root, timeout=state_timeout)
            lr.goal_met = goal_met
            if vlog:
                vlog(f"  │ goal check: {'MET' if goal_met else 'not yet'}")
            if goal_met:
                lr.duration_ms = int((time.monotonic() - round_start) * 1000)
                loop_result.rounds.append(lr)
                loop_result.goal_met = True
                loop_result.goal_met_at = round_num
                loop_result.completed_rounds = round_num
                if vlog:
                    vlog(f"  └── GOAL MET at round {round_num}! ({lr.duration_ms}ms)")
                break

        lr.duration_ms = int((time.monotonic() - round_start) * 1000)
        loop_result.rounds.append(lr)
        loop_result.completed_rounds = round_num

        if vlog:
            vlog(f"  └── Round {round_num} OK ({lr.duration_ms}ms)")

    # Determine overall success
    # Success = all rounds succeeded AND (goal met if check_command is set)
    all_rounds_ok = all(r.success for r in loop_result.rounds)
    if check_command:
        overall_success = all_rounds_ok and loop_result.goal_met
    else:
        overall_success = all_rounds_ok

    total_duration = sum(r.duration_ms for r in loop_result.rounds)

    # Build stdout summary
    summary_lines = [
        f"Loop completed: {loop_result.completed_rounds}/{max_rounds} rounds",
    ]
    if goal:
        summary_lines.append(f"Goal: {goal}")
    if loop_result.goal_met:
        summary_lines.append(f"Goal met at round {loop_result.goal_met_at}")
    elif check_command:
        summary_lines.append("Goal NOT met")

    # Last response as the "stdout" for downstream assert steps
    last_response = loop_result.rounds[-1].response if loop_result.rounds else ""

    return StepResult(
        step_index=0,
        action="loop",
        success=overall_success,
        stdout=last_response,
        stderr="\n".join(summary_lines),
        duration_ms=total_duration,
        error=loop_result.error,
    )


# ---------------------------------------------------------------------------
# Plan Runner
# ---------------------------------------------------------------------------

class PlanRunner:
    """Execute a YAML plan against a project directory.

    Usage:
        plan = load_plan(Path("my_plan.yaml"))
        runner = PlanRunner(project_root=Path("/path/to/project"))
        result = runner.run(plan)
        print(result.summary())

    With a host adapter for prompt steps:
        runner = PlanRunner(
            project_root=Path("."),
            host=LLMAdapter(project_root=Path(".")),
        )
    """

    def __init__(
        self,
        project_root: Path,
        timeout: int = 120,
        event_log: Optional[Any] = None,
        dry_run: bool = False,
        host: Optional["HostAdapter"] = None,
        verbose: bool = False,
    ):
        self.project_root = project_root.resolve()
        self.timeout = timeout
        self.event_log = event_log
        self.dry_run = dry_run
        self.host = host
        self.verbose = verbose
        self._variables: Dict[str, str] = {}  # store_as → response content

    def _vlog(self, msg: str) -> None:
        """Print verbose log message to stderr (never interferes with stdout)."""
        if self.verbose:
            import sys as _sys
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[plan:{ts}] {msg}", file=_sys.stderr, flush=True)

    def run(self, plan: Dict[str, Any]) -> PlanResult:
        """Execute all steps in a plan sequentially.

        Returns:
            PlanResult with per-step results and aggregate stats.
        """
        name = plan.get("name", "unnamed")
        steps = plan.get("steps", [])
        default_on_fail = plan.get("on_fail", "abort")

        # Auto-resolve host adapter from plan if not injected
        host = self.host
        if host is None and plan.get("host"):
            host = resolve_host_adapter(plan, self.project_root)

        result = PlanResult(name=name, total_steps=len(steps))
        plan_start = time.monotonic()

        self._log_event(PLAN_STARTED, {"name": name, "steps": len(steps)})
        self._variables.clear()

        self._vlog(f"{'='*60}")
        self._vlog(f"PLAN START: '{name}' ({len(steps)} steps)")
        self._vlog(f"  project_root: {self.project_root}")
        if host:
            self._vlog(f"  host adapter: {type(host).__name__}")
        if self.dry_run:
            self._vlog(f"  mode: DRY RUN")
        self._vlog(f"{'='*60}")

        last_stdout = ""

        for i, step in enumerate(steps):
            action = step.get("action", "")
            on_fail = step.get("on_fail", default_on_fail)
            description = step.get(
                "description",
                step.get("command", step.get("message", action)[:80] if step.get("message") else action),
            )

            self._vlog(f"")
            self._vlog(f"--- Step {i}/{len(steps)-1}: [{action}] {description[:60]} ---")

            if self.dry_run:
                self._vlog(f"  [SKIP] dry-run mode")
                sr = StepResult(
                    step_index=i,
                    action=action,
                    success=True,
                    skipped=True,
                )
                result.steps.append(sr)
                result.skipped += 1
                continue

            step_start = time.monotonic()

            if action == "cli":
                self._vlog(f"  cmd: {step.get('command', '')[:100]}")
                sr = _exec_cli(step, self.project_root, self.timeout)
            elif action == "assert":
                target = step.get('file', step.get('stdout_contains', '?'))
                self._vlog(f"  target: {target}")
                sr = _exec_assert(step, self.project_root, last_stdout)
            elif action == "wait":
                self._vlog(f"  seconds: {step.get('seconds')}")
                sr = _exec_wait(step)
            elif action == "prompt":
                msg_preview = step.get("message", "")[:80].replace("\n", " ")
                self._vlog(f"  message: {msg_preview}...")
                if host is None:
                    sr = StepResult(
                        step_index=i,
                        action="prompt",
                        success=False,
                        error="No host adapter configured for prompt steps",
                    )
                else:
                    sr = _exec_prompt(step, host, self._variables)
            elif action == "loop":
                max_r = step.get("max_rounds", 10)
                self._vlog(f"  loop: max_rounds={max_r}")
                if host is None:
                    sr = StepResult(
                        step_index=i,
                        action="loop",
                        success=False,
                        error="No host adapter configured for loop steps",
                    )
                else:
                    sr = _exec_loop(
                        step, host, self._variables, self.project_root,
                        timeout=self.timeout,
                        vlog=self._vlog if self.verbose else None,
                    )
            else:
                sr = StepResult(
                    step_index=i,
                    action=action,
                    success=False,
                    error=f"Unknown action: {action}",
                )

            sr.step_index = i
            sr.duration_ms = int((time.monotonic() - step_start) * 1000)
            result.steps.append(sr)

            # Verbose logging of step result
            status_mark = "PASS" if sr.success else "FAIL"
            self._vlog(f"  [{status_mark}] {sr.duration_ms}ms")
            if sr.exit_code is not None:
                self._vlog(f"  exit_code: {sr.exit_code}")
            if sr.stdout:
                preview = sr.stdout.strip()[:200].replace("\n", "\n         ")
                self._vlog(f"  stdout: {preview}")
            if sr.stderr:
                preview = sr.stderr.strip()[:200].replace("\n", "\n         ")
                self._vlog(f"  stderr: {preview}")
            if sr.error:
                self._vlog(f"  error: {sr.error}")

            # Track stdout for assert steps and variable storage
            if action in ("cli", "prompt", "loop"):
                last_stdout = sr.stdout or ""
            store_as = step.get("store_as")
            if store_as and sr.stdout:
                self._variables[store_as] = sr.stdout
                self._vlog(f"  stored as: {{{{ {store_as} }}}}")

            if sr.success:
                result.passed += 1
                self._log_event(PLAN_STEP_OK, {
                    "step": i, "action": action, "description": description,
                })
            else:
                result.failed += 1
                self._log_event(PLAN_STEP_FAIL, {
                    "step": i, "action": action, "error": sr.error,
                    "description": description,
                })

                if on_fail == "abort":
                    result.aborted = True
                    result.abort_reason = (
                        f"Step {i} ({action}) failed: {sr.error}"
                    )
                    # Mark remaining steps as skipped
                    for j in range(i + 1, len(steps)):
                        result.steps.append(StepResult(
                            step_index=j,
                            action=steps[j].get("action", ""),
                            success=False,
                            skipped=True,
                        ))
                        result.skipped += 1
                    break
                elif on_fail == "skip":
                    # Already counted as failed, continue to next
                    pass
                # "continue" also just continues

        result.duration_ms = int((time.monotonic() - plan_start) * 1000)

        event_type = PLAN_COMPLETED if result.success else PLAN_ABORTED
        self._log_event(event_type, result.to_dict())

        self._vlog(f"")
        self._vlog(f"{'='*60}")
        self._vlog(f"PLAN {'PASSED' if result.success else 'FAILED'}: '{name}'")
        self._vlog(f"  {result.passed}/{result.total_steps} passed, "
                   f"{result.failed} failed, {result.skipped} skipped")
        self._vlog(f"  duration: {result.duration_ms}ms")
        if result.aborted:
            self._vlog(f"  abort: {result.abort_reason}")
        self._vlog(f"{'='*60}")

        # Cleanup host adapter
        if host is not None and host is not self.host:
            try:
                host.close()
            except Exception:
                pass

        return result

    def _log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Record a plan event to EventLog if available."""
        if self.event_log is None:
            return
        try:
            from vibecollab.domain.event_log import Event
            self.event_log.append(Event(
                event_type=event_type,
                summary=f"Plan execution: {event_type}",
                actor="plan_runner",
                payload=payload,
            ))
        except Exception:
            pass  # EventLog is optional, never fail the plan


# ---------------------------------------------------------------------------
# Temp project helper (for E2E tests)
# ---------------------------------------------------------------------------

def create_temp_project(
    base_dir: Path,
    name: str = "test-project",
    domain: str = "generic",
) -> Path:
    """Create a temporary VibeCollab project for testing.

    Runs `vibecollab init` in a subdirectory and initializes git.
    Returns the project root path.

    This is intended for use in pytest fixtures:

        @pytest.fixture
        def temp_project(tmp_path):
            return create_temp_project(tmp_path)
    """
    project_dir = base_dir / name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Init project
    subprocess.run(
        f'vibecollab init -n "{name}" -d {domain} -o "{project_dir}"',
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Ensure git repo exists
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        subprocess.run(
            "git init && git add -A && git commit -m init",
            shell=True,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

    return project_dir
