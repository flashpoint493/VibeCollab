"""
Execution Plan - YAML-driven multi-round workflow automation.

A lightweight plan runner that reads a YAML execution plan and drives
steps through host adapters that communicate with IDE AI or CLI tools.

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
  - FileExchangeAdapter: Drives IDE AI (Cursor/Cline) via file exchange
  - SubprocessAdapter:   Drives any stdin/stdout CLI tool as host

Plan format examples:

  Linear plan:
    name: "Multi-round task workflow"
    host: file_exchange
    steps:
      - action: prompt
        message: "Please call onboard, then create task TASK-DEV-001"
        expect:
          contains: "TASK-DEV-001"

  Autonomous loop:
    name: "Iterate project 50 rounds"
    host: file_exchange
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

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Python 3.9 compat: runtime_checkable Protocol
try:
    from typing import Protocol, runtime_checkable
except ImportError:
    from typing_extensions import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Public API exports
# ---------------------------------------------------------------------------

__all__ = [
    # Constants
    "RESPONSE_READY_MARKER",
    "PLAN_STARTED",
    "PLAN_STEP_OK",
    "PLAN_STEP_FAIL",
    "PLAN_COMPLETED",
    "PLAN_ABORTED",
    # Data classes
    "HostResponse",
    "StepResult",
    "PlanResult",
    "LoopRound",
    "LoopResult",
    "StepState",
    "PlanExecutionState",
    # Protocols & Adapters
    "HostAdapter",
    "SubprocessAdapter",
    "FileExchangeAdapter",
    # Core functions
    "load_plan",
    "validate_plan",
    "resolve_host_adapter",
    "run_state_command",
    "check_goal",
    # State management
    "StepStateManager",
    # Runner
    "PlanRunner",
    "StepExecutor",
]

# ---------------------------------------------------------------------------
# Shared constants (used by both execution_plan and auto_driver)
# ---------------------------------------------------------------------------

RESPONSE_READY_MARKER = "<!-- VIBECOLLAB_RESPONSE_READY -->"
"""Marker that IDE AI writes to signal response completion."""

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


# ---------------------------------------------------------------------------
# FileExchangeAdapter — lightweight file-based host communication
# ---------------------------------------------------------------------------

class FileExchangeAdapter:
    """Host adapter that communicates with IDE AI via file exchange.

    This adapter enables vibecollab to drive Cursor/Cline AI by writing
    instructions to a file and polling for responses. The IDE AI (with
    tool-use capabilities) monitors the instruction file and writes
    results back.

    Design: vibecollab acts as the orchestrator, emitting structured
    instructions; the host IDE interprets and executes with its tool-use
    capabilities, then writes results back via the response file.

    Protocol:
        1. vibecollab writes instruction to instruction_file
        2. IDE AI detects new instruction, executes with tool-use
        3. IDE AI writes result to response_file
        4. vibecollab reads response, clears files, continues

    Args:
        exchange_dir: Directory for exchange files (default: .vibecollab/loop/)
        instruction_file: Filename for instructions (default: instruction.md)
        response_file: Filename for responses (default: response.md)
        poll_interval: Seconds between response checks (default: 2.0)
        timeout: Max seconds to wait for response (default: 300)
    """

    # Use shared constant
    READY_MARKER = RESPONSE_READY_MARKER

    def __init__(
        self,
        exchange_dir: str = ".vibecollab/loop",
        instruction_file: str = "instruction.md",
        response_file: str = "response.md",
        poll_interval: float = 2.0,
        timeout: int = 300,
        project_root: Optional[Path] = None,
    ):
        self._project_root = project_root or Path.cwd()
        self._exchange_dir = self._project_root / exchange_dir
        self._instruction_path = self._exchange_dir / instruction_file
        self._response_path = self._exchange_dir / response_file
        self._poll_interval = poll_interval
        self._timeout = timeout
        self._round = 0

    def _ensure_dir(self) -> None:
        """Create exchange directory if not exists."""
        self._exchange_dir.mkdir(parents=True, exist_ok=True)

    def _write_instruction(self, message: str) -> None:
        """Write instruction file with metadata header."""
        self._round += 1
        header = (
            f"<!-- VIBECOLLAB_INSTRUCTION -->\n"
            f"<!-- round: {self._round} -->\n"
            f"<!-- timestamp: {datetime.now(timezone.utc).isoformat()} -->\n\n"
        )
        self._instruction_path.write_text(
            header + message, encoding="utf-8"
        )

    def _clear_response(self) -> None:
        """Clear response file to prepare for new response."""
        if self._response_path.exists():
            self._response_path.unlink()

    def _read_response(self) -> Optional[str]:
        """Read response if ready marker is present."""
        if not self._response_path.exists():
            return None
        content = self._response_path.read_text(encoding="utf-8")
        if self.READY_MARKER not in content:
            return None
        # Remove the ready marker from content
        return content.replace(self.READY_MARKER, "").strip()

    def send(self, message: str, context: Optional[Dict[str, Any]] = None) -> HostResponse:
        """Send instruction and wait for IDE AI response.

        Writes instruction to file, then polls for response until timeout.
        """
        self._ensure_dir()
        self._clear_response()
        self._write_instruction(message)

        # Poll for response
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            response = self._read_response()
            if response is not None:
                return HostResponse(content=response, success=True)
            time.sleep(self._poll_interval)

        return HostResponse(
            content="",
            success=False,
            error=f"Timeout waiting for IDE response after {self._timeout}s. "
                  f"Ensure your IDE AI is monitoring {self._instruction_path}",
        )

    def close(self) -> None:
        """Cleanup exchange files."""
        try:
            if self._instruction_path.exists():
                self._instruction_path.unlink()
            if self._response_path.exists():
                self._response_path.unlink()
        except Exception:
            pass


# Adapter factory — resolve 'host' field from YAML plan
ADAPTER_REGISTRY: Dict[str, type] = {
    "subprocess": SubprocessAdapter,
    "file_exchange": FileExchangeAdapter,
    # "auto" is lazily resolved (requires optional dependencies)
}


def resolve_host_adapter(
    plan: Dict[str, Any],
    project_root: Optional[Path] = None,
    verbose: bool = False,
) -> Optional["HostAdapter"]:
    """Create a HostAdapter from a plan's 'host' configuration.

    The 'host' field can be:
      - A string: adapter type name (e.g. "file_exchange", "subprocess")
      - A string with colon: "auto:cursor", "auto:cline" (AutoAdapter with IDE)
      - A dict:   {"type": "subprocess", "command": "claude", ...}
      - Absent:   returns None (plan has no prompt steps)

    AutoAdapter support (v0.10.7+):
      - "auto" or "auto:cursor" → AutoAdapter(ide="cursor")
      - "auto:cline"           → AutoAdapter(ide="cline")
      - "auto:codebuddy"       → AutoAdapter(ide="codebuddy")
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

    # Handle "auto" and "auto:<ide>" syntax
    if host_type == "auto" or host_type.startswith("auto:"):
        ide = "cursor"  # default
        if ":" in host_type:
            ide = host_type.split(":", 1)[1]
        # Lazy import to avoid requiring pyautogui at module level
        from ..contrib.auto_driver import AutoAdapter
        return AutoAdapter(
            ide=ide,
            project_root=project_root,
            verbose=verbose,
            **host_opts,
        )
    elif host_type == "subprocess":
        command = host_opts.pop("command", "")
        if not command:
            raise ValueError("SubprocessAdapter requires 'command' in host config")
        return SubprocessAdapter(command=command, cwd=project_root, **host_opts)
    elif host_type == "file_exchange":
        return FileExchangeAdapter(project_root=project_root, **host_opts)
    else:
        raise ValueError(
            f"Unknown host adapter type: '{host_type}'. "
            f"Available: {sorted(list(ADAPTER_REGISTRY.keys()) + ['auto'])}"
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
            "Set host to 'file_exchange', 'subprocess', or a config dict."
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


# ---------------------------------------------------------------------------
# Public utility functions (reusable by auto_driver and other modules)
# ---------------------------------------------------------------------------

def run_state_command(
    command: str,
    project_root: Path,
    timeout: int = 30,
) -> str:
    """Run a state-gathering command and return its stdout.

    This function is used to capture the current project state before
    each round of an autonomous loop. Common examples:

        run_state_command("vibecollab next --json", project_root)
        run_state_command("vibecollab check --json", project_root)

    Args:
        command: Shell command to execute
        project_root: Working directory for the command
        timeout: Max seconds to wait (default: 30)

    Returns:
        Stripped stdout content, or empty string on error
    """
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


def check_goal(
    check_command: str,
    check_expect: Dict[str, Any],
    project_root: Path,
    timeout: int = 30,
) -> bool:
    """Run a goal-check command and verify expectations.

    Used to determine if the loop's goal has been achieved. The command
    is executed and its exit code / stdout are compared against expectations.

    Args:
        check_command: Shell command to execute (e.g., "vibecollab check")
        check_expect: Dict with optional keys:
            - exit_code: Expected return code (default: 0)
            - stdout_contains: String that must appear in stdout
        project_root: Working directory for the command
        timeout: Max seconds to wait (default: 30)

    Returns:
        True if all expectations are met, False otherwise

    Example:
        check_goal(
            "vibecollab check",
            {"exit_code": 0, "stdout_contains": "All checks passed"},
            Path(".")
        )
    """
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
            vlog("")
            vlog(f"  ┌── Loop Round {round_num}/{max_rounds} ──")

        # 1. Gather state
        state = ""
        if state_command:
            # Variable substitution in state_command
            cmd = state_command
            for key, value in variables.items():
                cmd = cmd.replace("{{" + key + "}}", value)
            state = run_state_command(cmd, project_root, timeout=state_timeout)
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
            goal_met = check_goal(check_command, check_expect, project_root, timeout=state_timeout)
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
# Step State Management (v0.11.0+ - Single-step execution support)
# ---------------------------------------------------------------------------

@dataclass
class StepState:
    """State of a single step execution."""
    index: int
    action: str
    description: str
    success: bool = False
    executed: bool = False
    skipped: bool = False
    error: str = ""
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    executed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "action": self.action,
            "description": self.description,
            "success": self.success,
            "executed": self.executed,
            "skipped": self.skipped,
            "error": self.error,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "executed_at": self.executed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepState":
        return cls(
            index=data.get("index", 0),
            action=data.get("action", ""),
            description=data.get("description", ""),
            success=data.get("success", False),
            executed=data.get("executed", False),
            skipped=data.get("skipped", False),
            error=data.get("error", ""),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            duration_ms=data.get("duration_ms", 0),
            executed_at=data.get("executed_at"),
        )


@dataclass
class PlanExecutionState:
    """Complete execution state for a plan."""
    plan_name: str
    plan_path: str
    total_steps: int
    steps: List[StepState]
    variables: Dict[str, str]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"  # pending, running, paused, completed, failed
    current_step_index: int = 0
    last_stdout: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_name": self.plan_name,
            "plan_path": self.plan_path,
            "total_steps": self.total_steps,
            "steps": [s.to_dict() for s in self.steps],
            "variables": self.variables,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "current_step_index": self.current_step_index,
            "last_stdout": self.last_stdout,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanExecutionState":
        return cls(
            plan_name=data.get("plan_name", ""),
            plan_path=data.get("plan_path", ""),
            total_steps=data.get("total_steps", 0),
            steps=[StepState.from_dict(s) for s in data.get("steps", [])],
            variables=data.get("variables", {}),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            status=data.get("status", "pending"),
            current_step_index=data.get("current_step_index", 0),
            last_stdout=data.get("last_stdout", ""),
        )

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps if s.executed and s.success)

    @property
    def failed_steps(self) -> int:
        return sum(1 for s in self.steps if s.executed and not s.success and not s.skipped)

    @property
    def is_complete(self) -> bool:
        return self.status in ("completed", "failed")


class StepStateManager:
    """Manages persistent storage of plan execution state.

    State is stored in .vibecollab/plan_state/<plan_name>.json
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.state_dir = self.project_root / ".vibecollab" / "plan_state"

    def _ensure_dir(self) -> None:
        """Ensure state directory exists."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_state_file(self, plan_name: str) -> Path:
        """Get the state file path for a plan."""
        # Sanitize plan name for filesystem
        safe_name = plan_name.replace("/", "_").replace("\\", "_").replace(":", "_")
        return self.state_dir / f"{safe_name}.json"

    def save_state(self, state: PlanExecutionState) -> None:
        """Save execution state to disk."""
        self._ensure_dir()
        state_file = self._get_state_file(state.plan_name)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

    def load_state(self, plan_name: str) -> Optional[PlanExecutionState]:
        """Load execution state from disk."""
        state_file = self._get_state_file(plan_name)
        if not state_file.exists():
            return None
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PlanExecutionState.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def delete_state(self, plan_name: str) -> bool:
        """Delete execution state for a plan."""
        state_file = self._get_state_file(plan_name)
        if state_file.exists():
            state_file.unlink()
            return True
        return False

    def list_states(self) -> List[Dict[str, Any]]:
        """List all saved execution states."""
        if not self.state_dir.exists():
            return []
        states = []
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                states.append({
                    "plan_name": data.get("plan_name", state_file.stem),
                    "status": data.get("status", "unknown"),
                    "progress": f"{data.get('current_step_index', 0)}/{data.get('total_steps', 0)}",
                    "started_at": data.get("started_at"),
                    "path": str(state_file),
                })
            except Exception:
                pass
        return states

    def has_state(self, plan_name: str) -> bool:
        """Check if a saved state exists for a plan."""
        return self._get_state_file(plan_name).exists()


# ---------------------------------------------------------------------------
# Step Executor - Single step execution
# ---------------------------------------------------------------------------

class StepExecutor:
    """Execute a single step with state tracking.

    This class encapsulates the logic for executing individual steps,
    making it reusable for both full plan execution and single-step mode.
    """

    def __init__(
        self,
        project_root: Path,
        timeout: int = 120,
        host: Optional[HostAdapter] = None,
        verbose: bool = False,
    ):
        self.project_root = project_root.resolve()
        self.timeout = timeout
        self.host = host
        self.verbose = verbose

    def execute(
        self,
        step: Dict[str, Any],
        step_index: int,
        last_stdout: str = "",
        variables: Optional[Dict[str, str]] = None,
    ) -> Tuple[StepResult, str, Dict[str, str]]:
        """Execute a single step.

        Args:
            step: The step definition
            step_index: Index of the step
            last_stdout: stdout from previous step (for assert steps)
            variables: Variable storage for store_as functionality

        Returns:
            Tuple of (StepResult, new_last_stdout, updated_variables)
        """
        action = step.get("action", "")
        variables = variables or {}

        step_start = time.monotonic()

        if action == "cli":
            sr = _exec_cli(step, self.project_root, self.timeout)
        elif action == "assert":
            sr = _exec_assert(step, self.project_root, last_stdout)
        elif action == "wait":
            sr = _exec_wait(step)
        elif action == "prompt":
            if self.host is None:
                sr = StepResult(
                    step_index=step_index,
                    action="prompt",
                    success=False,
                    error="No host adapter configured for prompt steps",
                )
            else:
                sr = _exec_prompt(step, self.host, variables)
        elif action == "loop":
            if self.host is None:
                sr = StepResult(
                    step_index=step_index,
                    action="loop",
                    success=False,
                    error="No host adapter configured for loop steps",
                )
            else:
                sr = _exec_loop(
                    step, self.host, variables, self.project_root,
                    timeout=self.timeout,
                    vlog=self._vlog if self.verbose else None,
                )
        else:
            sr = StepResult(
                step_index=step_index,
                action=action,
                success=False,
                error=f"Unknown action: {action}",
            )

        sr.step_index = step_index
        sr.duration_ms = int((time.monotonic() - step_start) * 1000)

        # Update last_stdout for next step
        if action in ("cli", "prompt", "loop"):
            last_stdout = sr.stdout or ""

        # Handle variable storage
        store_as = step.get("store_as")
        if store_as and sr.stdout:
            variables[store_as] = sr.stdout

        return sr, last_stdout, variables

    def _vlog(self, msg: str) -> None:
        """Print verbose log message."""
        if self.verbose:
            import sys as _sys
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[plan:{ts}] {msg}", file=_sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Extended PlanRunner with single-step and interactive support
# ---------------------------------------------------------------------------

class PlanRunner:
    """Execute a YAML plan against a project directory.

    Supports:
    - Full plan execution
    - Single-step execution (--index)
    - Interactive step-by-step execution (--interactive)
    - Resume from saved state (--resume)
    - Range execution (--from-step, --to-step)

    Usage:
        plan = load_plan(Path("my_plan.yaml"))
        runner = PlanRunner(project_root=Path("/path/to/project"))

        # Full execution
        result = runner.run(plan)

        # Single step
        result = runner.run_step(plan, step_index=2)

        # Interactive
        result = runner.run_interactive(plan)

        # Resume from saved state
        result = runner.run(plan, resume=True)

        print(result.summary())
    """

    def __init__(
        self,
        project_root: Path,
        timeout: int = 120,
        event_log: Optional[Any] = None,
        dry_run: bool = False,
        host: Optional[HostAdapter] = None,
        verbose: bool = False,
        state_manager: Optional[StepStateManager] = None,
    ):
        self.project_root = project_root.resolve()
        self.timeout = timeout
        self.event_log = event_log
        self.dry_run = dry_run
        self.host = host
        self.verbose = verbose
        self.state_manager = state_manager or StepStateManager(project_root)
        self._variables: Dict[str, str] = {}
        self._state: Optional[PlanExecutionState] = None

    def _vlog(self, msg: str) -> None:
        """Print verbose log message to stderr."""
        if self.verbose:
            import sys as _sys
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[plan:{ts}] {msg}", file=_sys.stderr, flush=True)

    def _init_state(self, plan: Dict[str, Any], plan_path: str = "") -> PlanExecutionState:
        """Initialize execution state from plan."""
        steps = plan.get("steps", [])
        step_states = [
            StepState(
                index=i,
                action=s.get("action", ""),
                description=s.get(
                    "description",
                    s.get("command", s.get("message", s.get("action", "")))[:80]
                ),
            )
            for i, s in enumerate(steps)
        ]
        return PlanExecutionState(
            plan_name=plan.get("name", "unnamed"),
            plan_path=plan_path,
            total_steps=len(steps),
            steps=step_states,
            variables={},
        )

    def _save_state(self) -> None:
        """Save current execution state."""
        if self._state:
            self._state.variables = self._variables.copy()
            self.state_manager.save_state(self._state)

    def run(
        self,
        plan: Dict[str, Any],
        plan_path: str = "",
        from_step: int = 0,
        to_step: Optional[int] = None,
        resume: bool = False,
        interactive: bool = False,
    ) -> PlanResult:
        """Execute plan with various modes.

        Args:
            plan: The plan dictionary
            plan_path: Path to the plan file (for state tracking)
            from_step: Start from this step index (0-based)
            to_step: Stop at this step index (inclusive, None for all)
            resume: Resume from saved state
            interactive: Pause after each step for user confirmation

        Returns:
            PlanResult with execution results
        """
        name = plan.get("name", "unnamed")
        steps = plan.get("steps", [])
        default_on_fail = plan.get("on_fail", "abort")

        # Initialize or load state
        if resume:
            saved_state = self.state_manager.load_state(name)
            if saved_state:
                self._state = saved_state
                from_step = saved_state.current_step_index
                self._variables = saved_state.variables.copy()
                self._vlog(f"Resumed from saved state at step {from_step}")
            else:
                self._state = self._init_state(plan, plan_path)
                self._vlog("No saved state found, starting from beginning")
        else:
            self._state = self._init_state(plan, plan_path)

        self._state.started_at = datetime.now(timezone.utc).isoformat()
        self._state.status = "running"

        # Auto-resolve host adapter
        host = self.host
        if host is None and plan.get("host"):
            host = resolve_host_adapter(plan, self.project_root, self.verbose)

        result = PlanResult(name=name, total_steps=len(steps))
        plan_start = time.monotonic()

        self._log_event(PLAN_STARTED, {"name": name, "steps": len(steps), "from_step": from_step})

        self._vlog(f"{'='*60}")
        self._vlog(f"PLAN START: '{name}' ({len(steps)} steps)")
        self._vlog(f"  project_root: {self.project_root}")
        self._vlog(f"  from_step: {from_step}")
        if to_step is not None:
            self._vlog(f"  to_step: {to_step}")
        if host:
            self._vlog(f"  host adapter: {type(host).__name__}")
        if self.dry_run:
            self._vlog("  mode: DRY RUN")
        if interactive:
            self._vlog("  mode: INTERACTIVE")
        self._vlog(f"{'='*60}")

        # Initialize step executor
        executor = StepExecutor(
            project_root=self.project_root,
            timeout=self.timeout,
            host=host,
            verbose=self.verbose,
        )

        last_stdout = self._state.last_stdout
        end_step = to_step if to_step is not None else len(steps) - 1

        for i in range(from_step, min(end_step + 1, len(steps))):
            step = steps[i]
            action = step.get("action", "")
            on_fail = step.get("on_fail", default_on_fail)
            description = step.get(
                "description",
                step.get("command", step.get("message", action)[:80] if step.get("message") else action),
            )

            self._state.current_step_index = i

            self._vlog("")
            self._vlog(f"--- Step {i}/{len(steps)-1}: [{action}] {description[:60]} ---")

            # Print step info for interactive mode
            if interactive:
                print(f"\n[Step {i+1}/{len(steps)}] {description}")
                print(f"  Action: {action}")
                if step.get("command"):
                    print(f"  Command: {step.get('command')}")
                if self.dry_run:
                    print("  [DRY RUN - skipping]")
                else:
                    response = input("  Press Enter to execute, 's' to skip, 'q' to quit: ").strip().lower()
                    if response == 'q':
                        self._state.status = "paused"
                        result.aborted = True
                        result.abort_reason = "User quit at step {i}"
                        self._save_state()
                        print("  State saved. Resume with: vibecollab plan run <workflow> --resume")
                        break
                    elif response == 's':
                        sr = StepResult(
                            step_index=i,
                            action=action,
                            success=True,
                            skipped=True,
                        )
                        self._state.steps[i].skipped = True
                        self._state.steps[i].executed = True
                        result.steps.append(sr)
                        result.skipped += 1
                        continue

            if self.dry_run:
                self._vlog("  [SKIP] dry-run mode")
                sr = StepResult(
                    step_index=i,
                    action=action,
                    success=True,
                    skipped=True,
                )
                result.steps.append(sr)
                result.skipped += 1
                continue

            # Execute the step
            sr, last_stdout, self._variables = executor.execute(
                step=step,
                step_index=i,
                last_stdout=last_stdout,
                variables=self._variables,
            )

            result.steps.append(sr)

            # Update state
            self._state.steps[i].executed = True
            self._state.steps[i].success = sr.success
            self._state.steps[i].skipped = sr.skipped
            self._state.steps[i].error = sr.error or ""
            self._state.steps[i].stdout = sr.stdout or ""
            self._state.steps[i].stderr = sr.stderr or ""
            self._state.steps[i].duration_ms = sr.duration_ms
            self._state.steps[i].executed_at = datetime.now(timezone.utc).isoformat()
            self._state.last_stdout = last_stdout

            # Verbose logging
            status_mark = "PASS" if sr.success else "FAIL"
            self._vlog(f"  [{status_mark}] {sr.duration_ms}ms")
            if sr.error:
                self._vlog(f"  error: {sr.error}")

            # Save state after each step
            self._save_state()

            if sr.success and not sr.skipped:
                result.passed += 1
                self._log_event(PLAN_STEP_OK, {"step": i, "action": action})
            elif not sr.skipped:
                result.failed += 1
                self._log_event(PLAN_STEP_FAIL, {"step": i, "action": action, "error": sr.error})

                if on_fail == "abort":
                    result.aborted = True
                    result.abort_reason = f"Step {i} ({action}) failed: {sr.error}"
                    self._state.status = "failed"
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

        result.duration_ms = int((time.monotonic() - plan_start) * 1000)

        # Final state update
        if not result.aborted and result.failed == 0:
            self._state.status = "completed"
            self._state.completed_at = datetime.now(timezone.utc).isoformat()
        elif not result.aborted:
            self._state.status = "failed"

        self._state.current_step_index = len(result.steps)
        self._save_state()

        event_type = PLAN_COMPLETED if result.success else PLAN_ABORTED
        self._log_event(event_type, result.to_dict())

        self._vlog("")
        self._vlog(f"{'='*60}")
        self._vlog(f"PLAN {'PASSED' if result.success else 'FAILED'}: '{name}'")
        self._vlog(f"  {result.passed}/{result.total_steps} passed")
        self._vlog(f"{'='*60}")

        # Cleanup host adapter
        if host is not None and host is not self.host:
            try:
                host.close()
            except Exception:
                pass

        return result

    def run_step(
        self,
        plan: Dict[str, Any],
        step_index: int,
        plan_path: str = "",
        save_state: bool = True,
    ) -> StepResult:
        """Execute a single step by index.

        Args:
            plan: The plan dictionary
            step_index: Index of the step to execute
            plan_path: Path to the plan file
            save_state: Whether to save execution state

        Returns:
            StepResult for the executed step
        """
        steps = plan.get("steps", [])
        if step_index < 0 or step_index >= len(steps):
            raise ValueError(f"Invalid step index: {step_index} (plan has {len(steps)} steps)")

        # Load or initialize state
        name = plan.get("name", "unnamed")
        saved_state = self.state_manager.load_state(name)
        if saved_state:
            self._state = saved_state
            self._variables = saved_state.variables.copy()
        else:
            self._state = self._init_state(plan, plan_path)

        self._state.status = "running"

        # Auto-resolve host adapter
        host = self.host
        if host is None and plan.get("host"):
            host = resolve_host_adapter(plan, self.project_root, self.verbose)

        step = steps[step_index]
        action = step.get("action", "")

        self._vlog(f"Executing single step {step_index}: [{action}]")

        # Initialize step executor
        executor = StepExecutor(
            project_root=self.project_root,
            timeout=self.timeout,
            host=host,
            verbose=self.verbose,
        )

        # Execute
        last_stdout = self._state.last_stdout if step_index == 0 else self._state.steps[step_index - 1].stdout
        sr, new_stdout, self._variables = executor.execute(
            step=step,
            step_index=step_index,
            last_stdout=last_stdout,
            variables=self._variables,
        )

        # Update state
        self._state.steps[step_index].executed = True
        self._state.steps[step_index].success = sr.success
        self._state.steps[step_index].error = sr.error or ""
        self._state.steps[step_index].stdout = sr.stdout or ""
        self._state.steps[step_index].stderr = sr.stderr or ""
        self._state.steps[step_index].duration_ms = sr.duration_ms
        self._state.steps[step_index].executed_at = datetime.now(timezone.utc).isoformat()
        self._state.current_step_index = step_index + 1
        self._state.last_stdout = new_stdout

        if save_state:
            self._save_state()

        # Cleanup host adapter
        if host is not None and host is not self.host:
            try:
                host.close()
            except Exception:
                pass

        return sr

    def run_interactive(self, plan: Dict[str, Any], plan_path: str = "") -> PlanResult:
        """Run plan in interactive mode (alias for run with interactive=True).

        Args:
            plan: The plan dictionary
            plan_path: Path to the plan file

        Returns:
            PlanResult with execution results
        """
        return self.run(plan, plan_path=plan_path, interactive=True)

    def get_step_info(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get information about all steps in a plan.

        Args:
            plan: The plan dictionary

        Returns:
            List of step information dictionaries
        """
        steps = plan.get("steps", [])
        name = plan.get("name", "unnamed")

        # Load state if exists
        saved_state = self.state_manager.load_state(name)
        step_states = {}
        if saved_state:
            step_states = {s.index: s for s in saved_state.steps}

        result = []
        for i, step in enumerate(steps):
            action = step.get("action", "")
            description = step.get(
                "description",
                step.get("command", step.get("message", action)[:80] if step.get("message") else action),
            )

            state = step_states.get(i)
            status = "pending"
            if state:
                if state.skipped:
                    status = "skipped"
                elif state.executed:
                    status = "success" if state.success else "failed"

            result.append({
                "index": i,
                "action": action,
                "description": description,
                "status": status,
                "executed_at": state.executed_at if state else None,
            })

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
