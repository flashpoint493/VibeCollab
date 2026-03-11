"""
Auto Driver - Autonomous IDE adapter for unattended automation.

This module provides the AutoAdapter — a HostAdapter implementation
that drives IDE AI through keyboard simulation. Unlike FileExchangeAdapter
(which writes files and waits), AutoAdapter actively simulates keyboard
input to control the IDE chat UI.

Architecture (after v0.10.7 merge):
    ┌─────────────────┐
    │   PlanRunner     │  (execution_plan.py - sole execution engine)
    │   _exec_loop()   │
    └────────┬────────┘
             │  adapter.send(instruction)
             ▼
    ┌─────────────────┐
    │   AutoAdapter   │  (this module - HostAdapter implementation)
    │   - pyautogui   │  Ctrl+L, paste, Enter → IDE AI Chat
    │   - pygetwindow │  Window focus & management
    │   - pyperclip   │  Clipboard for instruction delivery
    └────────┬────────┘
             │ IDE AI executes with tool-use
             ▼
    ┌─────────────────┐
    │  response.md    │  ← IDE AI writes completion marker
    └─────────────────┘
             ▲
             │ Poll for VIBECOLLAB_RESPONSE_READY
    ┌────────┴────────┐
    │   AutoAdapter   │  → returns HostResponse to PlanRunner
    └─────────────────┘

Usage:
    # Via CLI (recommended)
    vibecollab plan run plans/dev-loop.yaml --host auto:cursor

    # Via .bat launcher
    vibecollab auto init --preset dev-loop
    # Double-click the generated .bat file

    # Programmatic
    from vibecollab.contrib.auto_driver import AutoAdapter
    adapter = AutoAdapter(ide="cursor", project_root=Path("."))
    resp = adapter.send("Please implement feature X")

Shared Components (from execution_plan.py):
    - RESPONSE_READY_MARKER: Completion signal marker
    - HostResponse: Standard response data class
    - run_state_command(): Execute state-gathering commands (used by _exec_loop)
    - check_goal(): Verify if loop goal is met (used by _exec_loop)

Requirements:
    pip install vibe-collab[auto]  # includes pyautogui, pygetwindow, pyperclip

CLI Commands:
    vibecollab plan run plans/dev.yaml --host auto:cursor  # Start automation
    vibecollab auto init --preset dev-loop                 # Create .bat launcher
    vibecollab auto list                                   # List preset plans
    vibecollab auto status                                 # Check running status
    vibecollab auto stop                                   # Stop running driver
"""

import os
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Import shared types from execution_plan
from ..core.execution_plan import (
    RESPONSE_READY_MARKER,
    HostResponse,
)

# Lazy imports for optional dependencies
_pyautogui = None
_pygetwindow = None
_pyperclip = None


def _ensure_dependencies():
    """Lazily import optional dependencies."""
    global _pyautogui, _pygetwindow, _pyperclip

    if _pyautogui is None:
        try:
            import pyautogui
            _pyautogui = pyautogui
            # Disable fail-safe for unattended operation
            _pyautogui.FAILSAFE = False
        except ImportError:
            raise ImportError(
                "pyautogui is required for auto driver. "
                "Install with: pip install vibe-collab[auto]"
            )

    if _pygetwindow is None:
        try:
            import pygetwindow as gw
            _pygetwindow = gw
        except ImportError:
            raise ImportError(
                "pygetwindow is required for auto driver. "
                "Install with: pip install vibe-collab[auto]"
            )

    if _pyperclip is None:
        try:
            import pyperclip
            _pyperclip = pyperclip
        except ImportError:
            raise ImportError(
                "pyperclip is required for auto driver. "
                "Install with: pip install vibe-collab[auto]"
            )


# ---------------------------------------------------------------------------
# IDE Configuration
# ---------------------------------------------------------------------------

@dataclass
class IDEConfig:
    """Configuration for a specific IDE."""
    name: str
    window_title_pattern: str  # Pattern to match window title
    open_chat_hotkey: List[str]  # Hotkey to open chat (e.g., ["ctrl", "l"])
    send_hotkey: List[str] = field(default_factory=lambda: ["enter"])
    chat_input_delay: float = 0.5  # Delay after opening chat before typing
    send_delay: float = 0.2  # Delay after sending before monitoring


IDE_CONFIGS: Dict[str, IDEConfig] = {
    "cursor": IDEConfig(
        name="Cursor",
        window_title_pattern="Cursor",
        open_chat_hotkey=["ctrl", "l"],
    ),
    "cline": IDEConfig(
        name="Cline",
        window_title_pattern="Visual Studio Code",
        open_chat_hotkey=["ctrl", "shift", "p"],  # Opens command palette
    ),
    "codebuddy": IDEConfig(
        name="CodeBuddy",
        window_title_pattern="CodeBuddy",
        open_chat_hotkey=["ctrl", "l"],
    ),
}


# ---------------------------------------------------------------------------
# AutoAdapter — HostAdapter implementation via keyboard simulation
# ---------------------------------------------------------------------------

class AutoAdapter:
    """Host adapter that drives IDE AI through keyboard simulation.

    Implements the HostAdapter protocol (send + close) by:
    1. Finding and activating the IDE window
    2. Opening the chat input via hotkey (Ctrl+L for Cursor)
    3. Pasting the instruction via clipboard
    4. Pressing Enter to send
    5. Polling response.md for VIBECOLLAB_RESPONSE_READY marker

    This adapter is registered in ADAPTER_REGISTRY as "auto" and supports
    IDE sub-options via colon syntax: "auto:cursor", "auto:cline", etc.

    Args:
        ide: IDE identifier (cursor, cline, codebuddy). Default: cursor
        project_root: Project root directory. Default: cwd
        response_timeout: Max seconds to wait for IDE response. Default: 600
        poll_interval: Seconds between response file checks. Default: 5.0
        verbose: Enable verbose logging to stderr. Default: False
    """

    RESPONSE_FILE = ".vibecollab/loop/response.md"
    RESPONSE_MARKER = RESPONSE_READY_MARKER

    def __init__(
        self,
        ide: str = "cursor",
        project_root: Optional[Path] = None,
        response_timeout: int = 600,
        poll_interval: float = 5.0,
        verbose: bool = False,
    ):
        _ensure_dependencies()

        self.ide = ide.lower()
        self.project_root = project_root or Path.cwd()
        self.response_timeout = response_timeout
        self.poll_interval = poll_interval
        self.verbose = verbose

        if self.ide not in IDE_CONFIGS:
            raise ValueError(
                f"Unknown IDE: {ide}. Supported: {list(IDE_CONFIGS.keys())}"
            )

        self.ide_config = IDE_CONFIGS[self.ide]
        self._response_path = self.project_root / self.RESPONSE_FILE

    def _log(self, msg: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[auto:{ts}] {msg}", file=sys.stderr, flush=True)

    def _find_ide_window(self) -> bool:
        """Find and activate IDE window by title pattern."""
        try:
            windows = _pygetwindow.getWindowsWithTitle(
                self.ide_config.window_title_pattern
            )
            if not windows:
                self._log(f"No window found matching: {self.ide_config.window_title_pattern}")
                return False

            # Activate the first matching window
            window = windows[0]
            if window.isMinimized:
                window.restore()
            window.activate()
            time.sleep(0.3)  # Wait for window to activate
            return True
        except Exception as e:
            self._log(f"Error finding IDE window: {e}")
            return False

    def _open_chat(self) -> None:
        """Open IDE chat input using configured hotkey."""
        hotkey = self.ide_config.open_chat_hotkey
        self._log(f"Opening chat with hotkey: {'+'.join(hotkey)}")
        _pyautogui.hotkey(*hotkey)
        time.sleep(self.ide_config.chat_input_delay)

    def _paste_and_send(self, instruction: str) -> None:
        """Paste instruction via clipboard and send."""
        _pyperclip.copy(instruction)
        self._log(f"Instruction copied ({len(instruction)} chars)")

        # Paste
        _pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)

        # Send
        _pyautogui.hotkey(*self.ide_config.send_hotkey)
        time.sleep(self.ide_config.send_delay)
        self._log("Instruction sent")

    def _clear_response_file(self) -> None:
        """Clear response file to prepare for new response."""
        if self._response_path.exists():
            self._response_path.unlink()
        # Ensure parent directory exists
        self._response_path.parent.mkdir(parents=True, exist_ok=True)

    def _wait_for_response(self) -> Optional[str]:
        """Wait for response file with completion marker."""
        deadline = time.monotonic() + self.response_timeout

        while time.monotonic() < deadline:
            if self._response_path.exists():
                content = self._response_path.read_text(encoding="utf-8")
                if self.RESPONSE_MARKER in content:
                    return content.replace(self.RESPONSE_MARKER, "").strip()
            time.sleep(self.poll_interval)

        return None

    # === HostAdapter Protocol ===

    def send(self, message: str, context: Optional[Dict[str, Any]] = None) -> HostResponse:
        """Send instruction to IDE via keyboard simulation.

        Implements HostAdapter.send():
        1. Find & activate IDE window
        2. Open chat input (Ctrl+L)
        3. Paste instruction from clipboard
        4. Press Enter to send
        5. Poll response.md for completion marker
        6. Return response content

        Args:
            message: Instruction text to send to IDE AI
            context: Optional context dict (unused, for protocol compatibility)

        Returns:
            HostResponse with IDE AI's response content
        """
        # Append response instruction to message
        full_message = message + f"""

---
**IMPORTANT**: When done, write your response to `.vibecollab/loop/response.md` and include:
`{self.RESPONSE_MARKER}`
at the end of the file to signal completion.
"""

        # 1. Find IDE window (with retry)
        if not self._find_ide_window():
            self._log("Cannot find IDE window, retrying in 10s...")
            time.sleep(10)
            if not self._find_ide_window():
                return HostResponse(
                    content="",
                    success=False,
                    error=f"IDE window not found: {self.ide_config.window_title_pattern}",
                )

        # 2. Clear response file
        self._clear_response_file()

        # 3. Open chat and send instruction
        self._open_chat()
        self._paste_and_send(full_message)

        # 4. Wait for response
        self._log(f"Waiting for response (timeout: {self.response_timeout}s)...")
        response = self._wait_for_response()

        if response is None:
            return HostResponse(
                content="",
                success=False,
                error=f"Response timeout after {self.response_timeout}s. "
                      f"Ensure IDE AI writes to {self._response_path} "
                      f"with marker {self.RESPONSE_MARKER}",
            )

        self._log(f"Response received: {len(response)} chars")
        return HostResponse(content=response, success=True)

    def close(self) -> None:
        """Cleanup resources. AutoAdapter has no persistent resources."""
        pass


# ---------------------------------------------------------------------------
# Process Management (for auto status / auto stop)
# ---------------------------------------------------------------------------

@dataclass
class AutoDriverState:
    """Persistent state for auto driver process tracking."""
    plan_path: str
    ide: str
    pid: int
    started_at: str
    host_type: str = "auto"
    current_round: int = 0
    max_rounds: int = 50
    status: str = "running"  # running | stopped | completed | failed
    last_instruction: str = ""
    last_response: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_path": self.plan_path,
            "ide": self.ide,
            "pid": self.pid,
            "started_at": self.started_at,
            "host_type": self.host_type,
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "status": self.status,
            "last_instruction": self.last_instruction[:200] if self.last_instruction else "",
            "last_response": self.last_response[:200] if self.last_response else "",
            "error": self.error,
        }


STATE_FILE = ".vibecollab/auto_driver.state.yaml"


def save_state(state: AutoDriverState, project_root: Optional[Path] = None) -> None:
    """Persist auto driver state to file."""
    root = project_root or Path.cwd()
    state_path = root / STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(state.to_dict(), f, allow_unicode=True)


def get_status(project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get status of running auto driver."""
    root = project_root or Path.cwd()
    state_path = root / STATE_FILE

    if not state_path.exists():
        return None

    try:
        with open(state_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def stop_driver(project_root: Optional[Path] = None) -> bool:
    """Stop running auto driver by sending signal."""
    status = get_status(project_root)
    if status is None:
        return False

    pid = status.get("pid")
    if pid is None:
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except (ProcessLookupError, PermissionError):
        return False


# ---------------------------------------------------------------------------
# .bat launcher generation
# ---------------------------------------------------------------------------

def generate_bat_content(
    plan_file: str,
    ide: str = "cursor",
    project_root: Optional[Path] = None,
) -> str:
    """Generate .bat file content for launching auto driver.

    The .bat uses `vibecollab plan run ... --host auto:<ide>` as the
    unified execution entry point.
    """
    root = project_root or Path.cwd()

    return f'''@echo off
REM VibeCollab Auto Driver Launcher
REM Generated for: {Path(plan_file).name}
REM Double-click this file to start autonomous IDE automation

echo ========================================
echo   VibeCollab Auto Driver
echo ========================================
echo.
echo Plan: {plan_file}
echo IDE: {ide}
echo Host: auto:{ide}
echo.
echo Starting in 3 seconds...
echo Press Ctrl+C to cancel.
timeout /t 3 /nobreak > nul

cd /d "{root}"

REM Check if vibecollab is installed
where vibecollab >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] vibecollab not found. Please install: pip install vibe-collab[auto]
    pause
    exit /b 1
)

REM Start auto driver via plan run (unified execution engine)
echo.
echo Starting auto driver via plan run...
echo To stop: run "vibecollab auto stop" or close this window
echo.

vibecollab plan run "{plan_file}" --host auto:{ide} -v

echo.
echo ========================================
echo   Auto Driver Finished
echo ========================================
pause
'''
