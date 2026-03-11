"""
AI CLI commands -- Human-AI dialogue + autonomous Agent mode

Supports three usage modes:
1. IDE dialogue: Developer in Cursor/CodeBuddy, reads CONTRIBUTING_AI.md (already available)
2. CLI human-AI interaction: vibecollab ai ask / vibecollab ai chat
3. Agent autonomous: vibecollab ai agent run / serve / plan

Safety gate mechanisms:
- Max cycle limit (max_cycles)
- Adaptive sleep + exponential backoff
- pending-solidify check (blocks if previous task not solidified)
- Singleton PID lock (prevents multiple instances)
- Memory threshold protection
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click
from rich.markdown import Markdown
from rich.panel import Panel

from .._compat import EMOJI as _COMPAT_EMOJI
from .._compat import is_windows_gbk, safe_console
from ..agent.llm_client import LLMClient, LLMConfig, LLMResponse, Message, build_project_context
from ..domain.event_log import Event, EventLog, EventType
from ..domain.task_manager import TaskManager, TaskStatus
from ..i18n import _


def _log_event(event_log: EventLog, event_type: str, summary: str,
               actor: str = "cli", payload: dict = None) -> None:
    """Helper: append an Event to the log."""
    event_log.append(Event(
        event_type=event_type,
        summary=summary,
        actor=actor,
        payload=payload or {},
    ))

# ---------------------------------------------------------------------------
# Windows GBK compatibility (imported from shared module)
# ---------------------------------------------------------------------------

USE_EMOJI = not is_windows_gbk()
EMOJI = _COMPAT_EMOJI

console = safe_console()

# ---------------------------------------------------------------------------
# Agent safety gates
# ---------------------------------------------------------------------------

# Defaults (can be overridden via environment variables)
DEFAULT_MAX_CYCLES = 50
DEFAULT_MIN_SLEEP_S = 2
DEFAULT_MAX_SLEEP_S = 300
DEFAULT_PENDING_SLEEP_S = 60
DEFAULT_MAX_RSS_MB = 500
DEFAULT_IDLE_THRESHOLD_S = 1  # Fast cycle threshold

# Environment variable names
ENV_MAX_CYCLES = "VIBECOLLAB_AGENT_MAX_CYCLES"
ENV_MIN_SLEEP = "VIBECOLLAB_AGENT_MIN_SLEEP"
ENV_MAX_SLEEP = "VIBECOLLAB_AGENT_MAX_SLEEP"
ENV_MAX_RSS_MB = "VIBECOLLAB_AGENT_MAX_RSS_MB"

# PID lock file name
PID_LOCK_FILE = "agent.pid"


def _get_agent_config():
    """Read Agent runtime config (env vars > defaults)."""
    return {
        "max_cycles": int(os.getenv(ENV_MAX_CYCLES, str(DEFAULT_MAX_CYCLES))),
        "min_sleep": float(os.getenv(ENV_MIN_SLEEP, str(DEFAULT_MIN_SLEEP_S))),
        "max_sleep": float(os.getenv(ENV_MAX_SLEEP, str(DEFAULT_MAX_SLEEP_S))),
        "max_rss_mb": int(os.getenv(ENV_MAX_RSS_MB, str(DEFAULT_MAX_RSS_MB))),
        "pending_sleep": DEFAULT_PENDING_SLEEP_S,
        "idle_threshold": DEFAULT_IDLE_THRESHOLD_S,
    }


def _acquire_lock(lock_path: Path) -> bool:
    """Singleton PID lock -- prevent multiple agent instances from running.

    - Lock file exists -> check if PID is alive
    - Alive -> refuse to start
    - Stale -> take over
    """
    if lock_path.exists():
        try:
            old_pid = int(lock_path.read_text().strip())
            # Check if process is alive (signal 0 doesn't send signal, only checks)
            os.kill(old_pid, 0)
            return False  # An instance is already running
        except (ValueError, OSError, ProcessLookupError):
            pass  # Stale lock or invalid PID -> take over

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(os.getpid()))
    return True


def _release_lock(lock_path: Path):
    """Release PID lock -- only delete if PID matches."""
    try:
        if lock_path.exists():
            stored_pid = int(lock_path.read_text().strip())
            if stored_pid == os.getpid():
                lock_path.unlink()
    except (ValueError, OSError):
        pass


def _check_rss_mb() -> float:
    """Get current process RSS (MB). Cross-platform compatible."""
    try:
        import resource
        # Unix: resource.getrusage (KB on Linux, bytes on macOS)
        ru = resource.getrusage(resource.RUSAGE_SELF)
        rss_kb = ru.ru_maxrss
        if sys.platform == "darwin":
            return rss_kb / (1024 * 1024)  # macOS: bytes -> MB
        return rss_kb / 1024  # Linux: KB -> MB
    except ImportError:
        pass
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0  # Cannot detect -> no limit


def _is_pending_solidify(task_mgr: TaskManager) -> bool:
    """Check if any tasks are in REVIEW status awaiting solidification.

    If tasks created/advanced in a previous run have not been solidified, block new cycles.
    """
    review_tasks = task_mgr.list_tasks(status=TaskStatus.REVIEW)
    return len(review_tasks) > 0


# ---------------------------------------------------------------------------
# Project root detection
# ---------------------------------------------------------------------------

def _find_project_root(start: Optional[str] = None) -> Path:
    """Find project.yaml by searching upward from the specified or current directory."""
    p = Path(start) if start else Path.cwd()
    for candidate in [p] + list(p.parents):
        if (candidate / "project.yaml").exists():
            return candidate
    return p  # fallback: current directory


def _ensure_llm_configured() -> LLMClient:
    """Ensure LLM is configured, return client instance."""
    config = LLMConfig()
    if not config.is_configured:
        console.print(
            f"[red]{EMOJI['err']} LLM not configured.[/red]\n\n"
            f"[bold]Option 1 (recommended): Interactive setup wizard[/bold]\n"
            f"  vibecollab config setup\n\n"
            f"[bold]Option 2: Set environment variables manually[/bold]\n"
            f"  export VIBECOLLAB_LLM_API_KEY=your-api-key\n"
            f"  export VIBECOLLAB_LLM_PROVIDER=openai  # or anthropic\n"
            f"  export VIBECOLLAB_LLM_BASE_URL=https://openrouter.ai/api/v1  # optional\n\n"
            f"[bold]Option 3: Config file[/bold]\n"
            f"  vibecollab config set llm.api_key your-api-key\n"
            f"  vibecollab config set llm.provider openai"
        )
        raise SystemExit(1)
    return LLMClient(config)


def _display_response(resp: LLMResponse, show_usage: bool = False):
    """Format and display LLM response."""
    if resp.ok:
        console.print()
        console.print(Panel(
            Markdown(resp.content),
            title=f"{EMOJI['bot']} AI",
            border_style="green",
        ))
        if show_usage and resp.usage:
            tokens_in = resp.usage.get("prompt_tokens", resp.usage.get("input_tokens", 0))
            tokens_out = resp.usage.get("completion_tokens", resp.usage.get("output_tokens", 0))
            console.print(
                f"[dim]Model: {resp.model} | "
                f"Input: {tokens_in} tokens | "
                f"Output: {tokens_out} tokens[/dim]"
            )
    else:
        console.print(f"[red]{EMOJI['err']} LLM returned empty response[/red]")


# ---------------------------------------------------------------------------
# System prompt construction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_BASE = (
    "You are an AI development assistant integrated with the VibeCollab project "
    "collaboration framework. You follow the project's CONTRIBUTING_AI.md protocol.\n\n"
    "Key principles:\n"
    "- Follow the project's role system (DESIGN/ARCH/DEV/PM/QA/TEST)\n"
    "- Respect the project lifecycle stage\n"
    "- Record decisions per the DECISIONS.md format\n"
    "- Track tasks per the task_unit conventions\n"
    "- Update context files after significant changes\n"
)

SYSTEM_PROMPT_AGENT = (
    "You are an AUTONOMOUS AI Agent driving project development. "
    "You operate independently on a server, following the CONTRIBUTING_AI.md protocol.\n\n"
    "Your execution loop:\n"
    "1. ASSESS: Read project context (CONTEXT.md, ROADMAP.md, tasks)\n"
    "2. PLAN: Identify the highest-priority actionable task\n"
    "3. EXECUTE: Generate code changes, tests, or documentation\n"
    "4. VALIDATE: Run tests, check for regressions\n"
    "5. SOLIDIFY: If validation passes, commit changes\n"
    "6. REPORT: Update CONTEXT.md, CHANGELOG.md, ROADMAP.md\n\n"
    "Safety rules:\n"
    "- Never force-push or delete branches\n"
    "- Always run tests before committing\n"
    "- If unsure, output a plan without executing\n"
    "- Respect blast radius limits (max files per change)\n"
    "- Stop if repeated failures detected (circuit breaker)\n"
)


def _build_system_prompt(project_root: Path, agent_mode: bool = False) -> str:
    """Build system prompt with project context."""
    base = SYSTEM_PROMPT_AGENT if agent_mode else SYSTEM_PROMPT_BASE
    context = build_project_context(project_root)
    return f"{base}\n\n# Project Context\n\n{context}"


# ---------------------------------------------------------------------------
# Click command group
# ---------------------------------------------------------------------------

@click.group()
def ai():
    """[experimental] AI assistant commands -- Human-AI dialogue & Agent autonomous mode

    Experimental feature. VibeCollab's core positioning is a protocol management tool;
    LLM communication and Tool Use are best handled by specialized terminals like
    Cline/Cursor/Aider. This command group provides a lightweight alternative
    but is not the primary development direction.
    """
    pass


# ===== Human-AI interaction commands =====

@ai.command()
@click.argument("question")
@click.option("--project", "-p", default=None, help=_("Project root directory (auto-detect by default)"))
@click.option("--no-context", is_flag=True, help=_("Do not inject project context"))
@click.option("--temperature", "-t", default=0.7, type=float, help=_("Sampling temperature (0.0-1.0)"))
@click.option("--verbose", "-v", is_flag=True, help=_("Show token usage and details"))
def ask(question: str, project: Optional[str], no_context: bool,
        temperature: float, verbose: bool):
    """Ask AI a question (single turn, with project context)

    Examples:

        vibecollab ai ask "What should I do next?"
        vibecollab ai ask "Is this module's architecture reasonable?" -v
        vibecollab ai ask "Help me write a test" --no-context
    """
    client = _ensure_llm_configured()
    project_root = _find_project_root(project)

    console.print(f"[dim]Project: {project_root}[/dim]")
    console.print(f"[dim]Model: {client.config.model} ({client.config.provider})[/dim]")
    console.print(f"\n{EMOJI['user']} {question}")

    try:
        if no_context:
            resp = client.ask(question, temperature=temperature)
        else:
            system = _build_system_prompt(project_root)
            messages = [
                Message(role="system", content=system),
                Message(role="user", content=question),
            ]
            resp = client.chat(messages, temperature=temperature)

        _display_response(resp, show_usage=verbose)

        # Log to EventLog
        event_log = EventLog(project_root)
        _log_event(event_log, EventType.CUSTOM,
                   f"AI ask: {question[:100]}", actor="cli",
                   payload={"model": resp.model, "question_length": len(question)})

    except ImportError as e:
        console.print(f"[red]{EMOJI['err']} {e}[/red]")
        console.print("[dim]Install LLM dependencies: pip install vibe-collab[llm][/dim]")
        raise SystemExit(1)
    except (RuntimeError, ValueError) as e:
        console.print(f"[red]{EMOJI['err']} LLM call failed: {e}[/red]")
        raise SystemExit(1)


@ai.command()
@click.option("--project", "-p", default=None, help=_("Project root directory (auto-detect by default)"))
@click.option("--no-context", is_flag=True, help=_("Do not inject project context"))
@click.option("--temperature", "-t", default=0.7, type=float, help=_("Sampling temperature"))
@click.option("--verbose", "-v", is_flag=True, help=_("Show token usage"))
def chat(project: Optional[str], no_context: bool, temperature: float, verbose: bool):
    """Multi-turn conversation with AI (Ctrl+C to exit)

    Examples:

        vibecollab ai chat
        vibecollab ai chat -p ./my-project -v
    """
    client = _ensure_llm_configured()
    project_root = _find_project_root(project)

    console.print(f"[dim]Project: {project_root}[/dim]")
    console.print(f"[dim]Model: {client.config.model} ({client.config.provider})[/dim]")
    console.print("[dim]Type 'exit' or Ctrl+C to quit[/dim]\n")

    # Initialize message history
    messages = []
    if not no_context:
        system = _build_system_prompt(project_root)
        messages.append(Message(role="system", content=system))

    turn_count = 0
    try:
        while True:
            try:
                user_input = input(f"{EMOJI['user']} You: ")
            except EOFError:
                break

            if user_input.strip().lower() in ("exit", "quit", "bye", "/exit", "/quit"):
                console.print(f"\n{EMOJI['ok']} Conversation ended")
                break

            if not user_input.strip():
                continue

            messages.append(Message(role="user", content=user_input))

            try:
                resp = client.chat(messages, temperature=temperature)

                if resp.ok:
                    messages.append(Message(role="assistant", content=resp.content))
                    _display_response(resp, show_usage=verbose)
                    turn_count += 1
                else:
                    console.print(f"[red]{EMOJI['err']} Empty response, please retry[/red]")
                    messages.pop()  # Remove unsuccessful user message

            except (RuntimeError, ValueError) as e:
                console.print(f"[red]{EMOJI['err']} Call failed: {e}[/red]")
                messages.pop()

    except KeyboardInterrupt:
        console.print(f"\n\n{EMOJI['ok']} Conversation ended ({turn_count} turns)")

    # Log to EventLog
    if turn_count > 0:
        event_log = EventLog(project_root)
        _log_event(event_log, EventType.CUSTOM,
                   f"AI chat session: {turn_count} turns", actor="cli",
                   payload={"turns": turn_count, "model": client.config.model})


# ===== Agent autonomous commands =====

@ai.group()
def agent():
    """Agent autonomous mode -- server deployment, self-driven development"""
    pass


@agent.command()
@click.option("--project", "-p", default=None, help=_("Project root directory"))
@click.option("--verbose", "-v", is_flag=True, help=_("Verbose output"))
def plan(project: Optional[str], verbose: bool):
    """Analyze project state, generate action plan (read-only)

    Reads project context, task list, and event log; lets LLM generate next-step plan.
    This is a read-only operation -- no files are modified.

    Examples:

        vibecollab ai agent plan
        vibecollab ai agent plan -p ./my-project -v
    """
    client = _ensure_llm_configured()
    project_root = _find_project_root(project)

    console.print(Panel.fit(
        f"[bold]Agent Plan Mode[/bold]\nProject: {project_root}",
        border_style="cyan",
    ))

    system = _build_system_prompt(project_root, agent_mode=True)
    messages = [
        Message(role="system", content=system),
        Message(role="user", content=(
            "Analyze the current project state and generate a detailed action plan. "
            "List the top 3-5 highest priority tasks, with concrete steps for each. "
            "Do NOT execute anything — only plan.\n\n"
            "Output format:\n"
            "## Action Plan\n"
            "### Priority 1: [task description]\n"
            "- Step 1: ...\n"
            "- Step 2: ...\n"
            "- Expected outcome: ...\n\n"
            "### Priority 2: ...\n"
        )),
    ]

    try:
        console.print(f"[cyan]{EMOJI['think']} Analyzing project status...[/cyan]")
        resp = client.chat(messages, temperature=0.3)  # Low temperature for determinism

        _display_response(resp, show_usage=verbose)

        # Log to EventLog
        event_log = EventLog(project_root)
        _log_event(event_log, EventType.CUSTOM,
                   "Agent plan: generated action plan", actor="agent",
                   payload={"model": resp.model})

    except (ImportError, RuntimeError, ValueError) as e:
        console.print(f"[red]{EMOJI['err']} {e}[/red]")
        raise SystemExit(1)


@agent.command()
@click.option("--project", "-p", default=None, help=_("Project root directory"))
@click.option("--dry-run", is_flag=True, help=_("Dry run (only generate plan, do not execute)"))
@click.option("--verbose", "-v", is_flag=True, help=_("Verbose output"))
def run(project: Optional[str], dry_run: bool, verbose: bool):
    """Execute a single Agent cycle: Plan -> Execute -> Solidify

    Suitable for cron scheduled tasks or manual triggers. Only one cycle per run.

    Examples:

        vibecollab ai agent run
        vibecollab ai agent run --dry-run
        vibecollab ai agent run -p ./my-project -v
    """
    client = _ensure_llm_configured()
    project_root = _find_project_root(project)
    vc_dir = project_root / ".vibecollab"
    vc_dir.mkdir(parents=True, exist_ok=True)

    event_log = EventLog(project_root)
    task_mgr = TaskManager(project_root, event_log)

    console.print(Panel.fit(
        f"[bold]Agent Run Mode[/bold] (single cycle)\n"
        f"Project: {project_root}\n"
        f"Dry-run: {'Yes' if dry_run else 'No'}",
        border_style="yellow",
    ))

    # Gate: pending solidify check
    if _is_pending_solidify(task_mgr):
        review_tasks = task_mgr.list_tasks(status=TaskStatus.REVIEW)
        task_ids = [t.id for t in review_tasks]
        console.print(
            f"[yellow]{EMOJI['warn']} Pending solidification tasks: {', '.join(task_ids)}[/yellow]\n"
            f"Please complete review before running a new cycle."
        )
        raise SystemExit(1)

    # Phase 1: ASSESS + PLAN
    console.print("\n[cyan]Phase 1: ASSESS + PLAN[/cyan]")
    system = _build_system_prompt(project_root, agent_mode=True)

    plan_prompt = (
        "You are executing a single agent cycle. Phase 1: ASSESS and PLAN.\n\n"
        "1. Analyze the current project state from the context above\n"
        "2. Identify the single highest-priority actionable task\n"
        "3. Generate a concrete execution plan with specific file changes\n\n"
        "Output as JSON:\n"
        "```json\n"
        '{\n'
        '  "task_summary": "brief description",\n'
        '  "priority": "high/medium/low",\n'
        '  "steps": [\n'
        '    {"action": "create/modify/test/document", "target": "file/path", "description": "what to do"}\n'
        '  ],\n'
        '  "expected_outcome": "what success looks like",\n'
        '  "risks": ["potential issues"]\n'
        '}\n'
        "```"
    )

    messages = [
        Message(role="system", content=system),
        Message(role="user", content=plan_prompt),
    ]

    try:
        console.print(f"[cyan]{EMOJI['think']} Phase 1: Analyzing and planning...[/cyan]")
        plan_resp = client.chat(messages, temperature=0.3)

        if not plan_resp.ok:
            console.print(f"[red]{EMOJI['err']} Plan phase failed: empty response[/red]")
            raise SystemExit(1)

        console.print(Panel(
            Markdown(plan_resp.content),
            title="Action Plan",
            border_style="cyan",
        ))

        _log_event(event_log, EventType.CUSTOM,
                   "Agent run: plan generated", actor="agent",
                   payload={"model": plan_resp.model, "dry_run": dry_run})

        if dry_run:
            console.print(f"\n[yellow]{EMOJI['warn']} Dry-run mode: no changes executed[/yellow]")
            return

        # Phase 2: EXECUTE (let LLM generate specific code changes)
        console.print("\n[cyan]Phase 2: EXECUTE[/cyan]")
        messages.append(Message(role="assistant", content=plan_resp.content))
        messages.append(Message(role="user", content=(
            "Phase 2: EXECUTE. Based on your plan, generate the specific code changes.\n\n"
            "For each file change, output a JSON code block:\n"
            "```json\n"
            '{"file": "relative/path", "action": "create|modify|delete", '
            '"content": "full file content"}\n'
            "```\n\n"
            "Rules:\n"
            "- Output one JSON block per file change\n"
            "- For 'modify', include the COMPLETE new file content, not a diff\n"
            "- Generate ACTUAL code, not placeholders\n"
            "- Follow the project's coding conventions"
        )))

        console.print(f"[cyan]{EMOJI['think']} Phase 2: Generating code changes...[/cyan]")
        exec_resp = client.chat(messages, temperature=0.2)

        if exec_resp.ok:
            console.print(Panel(
                Markdown(exec_resp.content),
                title="Generated Changes",
                border_style="yellow",
            ))

        # Phase 3: APPLY + TEST + COMMIT
        console.print("\n[cyan]Phase 3: APPLY + TEST + COMMIT[/cyan]")

        from ..agent.executor import AgentExecutor
        executor = AgentExecutor(project_root)
        changes = executor.parse_changes(exec_resp.content if exec_resp.ok else "")

        if not changes:
            console.print(f"[yellow]{EMOJI['warn']} No file changes parsed from LLM output[/yellow]")
            _log_event(event_log, EventType.CUSTOM,
                       "Agent run: no parseable changes", actor="agent")
            return

        console.print(f"  Parsed {len(changes)} file change(s):")
        for c in changes:
            console.print(f"    {c.action}: {c.file}")

        # Get test command
        test_cmd = None
        cfg_path = project_root / "project.yaml"
        if cfg_path.exists():
            import yaml
            with open(cfg_path, "r", encoding="utf-8") as f:
                proj_cfg = yaml.safe_load(f) or {}
            qa = proj_cfg.get("quick_acceptance", {})
            if qa.get("start_command"):
                test_cmd = qa["start_command"]

        result = executor.execute_full_cycle(
            exec_resp.content,
            commit_message=f"[AGENT] {plan_resp.content[:80].splitlines()[0]}",
            test_command=test_cmd,
        )

        if result.success:
            console.print(f"\n{EMOJI['ok']} [green]Cycle completed![/green]")
            for applied in result.changes_applied:
                console.print(f"  [green]{applied}[/green]")
            if result.test_passed:
                console.print(f"  {EMOJI['ok']} Tests passed")
            if result.git_committed:
                console.print(f"  {EMOJI['ok']} Git commit: {result.git_hash}")

            _log_event(event_log, EventType.CUSTOM,
                       "Agent run: cycle completed successfully", actor="agent",
                       payload=result.to_dict())
        else:
            console.print(f"\n[red]{EMOJI['err']} Cycle execution failed[/red]")
            for err in result.errors:
                console.print(f"  [red]{err}[/red]")
            if result.rollback_performed:
                console.print(f"  [yellow]{EMOJI['warn']} All changes rolled back[/yellow]")

            _log_event(event_log, EventType.VALIDATION_FAILED,
                       "Agent run: execution failed", actor="agent",
                       payload=result.to_dict())

    except (ImportError, RuntimeError, ValueError) as e:
        console.print(f"[red]{EMOJI['err']} Agent run failed: {e}[/red]")
        _log_event(event_log, EventType.VALIDATION_FAILED,
                   f"Agent run failed: {str(e)[:200]}", actor="agent")
        raise SystemExit(1)


@agent.command()
@click.option("--project", "-p", default=None, help=_("Project root directory"))
@click.option("--max-cycles", "-n", default=None, type=int,
              help=f"Max cycles (default: {DEFAULT_MAX_CYCLES})")
@click.option("--verbose", "-v", is_flag=True, help=_("Verbose output"))
def serve(project: Optional[str], max_cycles: Optional[int], verbose: bool):
    """Long-running Agent service -- loop Plan -> Execute -> Solidify

    Suitable for server deployment, self-driven project development.
    Includes full safety gates: max cycles, adaptive sleep, pending-solidify wait,
    PID lock, memory threshold, fix-loop circuit breaker.

    Examples:

        vibecollab ai agent serve
        vibecollab ai agent serve -n 10 -v
        VIBECOLLAB_AGENT_MAX_CYCLES=20 vibecollab ai agent serve
    """
    client = _ensure_llm_configured()
    project_root = _find_project_root(project)
    vc_dir = project_root / ".vibecollab"
    vc_dir.mkdir(parents=True, exist_ok=True)

    agent_cfg = _get_agent_config()
    if max_cycles is not None:
        agent_cfg["max_cycles"] = max_cycles

    lock_path = vc_dir / PID_LOCK_FILE

    # Gate 1: Singleton PID lock
    if not _acquire_lock(lock_path):
        console.print(
            f"[red]{EMOJI['err']} Agent instance already running.[/red]\n"
            f"Lock file: {lock_path}\n"
            f"If no other instance is running, delete the lock file and retry."
        )
        raise SystemExit(1)

    event_log = EventLog(project_root)
    task_mgr = TaskManager(project_root, event_log)

    console.print(Panel.fit(
        f"[bold]Agent Serve Mode[/bold] (long-running)\n"
        f"Project: {project_root}\n"
        f"Max cycles: {agent_cfg['max_cycles']}\n"
        f"PID: {os.getpid()}\n"
        f"Model: {client.config.model} ({client.config.provider})",
        border_style="green",
    ))

    _log_event(event_log, EventType.CUSTOM,
               f"Agent serve started (max_cycles={agent_cfg['max_cycles']})",
               actor="agent",
               payload={"pid": os.getpid(), "config": agent_cfg})

    cycle_count = 0
    consecutive_failures = 0
    current_sleep = agent_cfg["min_sleep"]
    CIRCUIT_BREAKER_THRESHOLD = 3  # Circuit breaker after N consecutive failures

    try:
        while cycle_count < agent_cfg["max_cycles"]:
            cycle_count += 1
            cycle_start = time.time()

            console.print(f"\n{'=' * 60}")
            console.print(
                f"[bold]Cycle {cycle_count}/{agent_cfg['max_cycles']}[/bold] "
                f"| {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )
            console.print(f"{'=' * 60}")

            # Gate 2: pending solidify check
            if _is_pending_solidify(task_mgr):
                review_tasks = task_mgr.list_tasks(status=TaskStatus.REVIEW)
                task_ids = [t.id for t in review_tasks]
                console.print(
                    f"[yellow]{EMOJI['warn']} Pending solidification tasks: {', '.join(task_ids)} "
                    f"-- waiting {agent_cfg['pending_sleep']}s[/yellow]"
                )
                time.sleep(agent_cfg["pending_sleep"])
                cycle_count -= 1  # Do not count toward cycle total
                continue

            # Gate 3: Memory check
            rss_mb = _check_rss_mb()
            if rss_mb > 0 and rss_mb > agent_cfg["max_rss_mb"]:
                console.print(
                    f"[red]{EMOJI['stop']} Memory exceeded: {rss_mb:.0f}MB > {agent_cfg['max_rss_mb']}MB "
                    f"-- stopping service[/red]"
                )
                break

            # Gate 4: Fix-loop circuit breaker
            if consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD:
                console.print(
                    f"[red]{EMOJI['stop']} Circuit breaker triggered: {consecutive_failures} consecutive failures "
                    f"-- waiting {agent_cfg['max_sleep']}s before retry[/red]"
                )
                _log_event(event_log, EventType.VALIDATION_FAILED,
                           f"Circuit breaker: {consecutive_failures} consecutive failures",
                           actor="agent")
                time.sleep(agent_cfg["max_sleep"])
                consecutive_failures = 0  # Reset, give another chance
                continue

            # Execute cycle
            ok = _execute_agent_cycle(
                client, project_root, event_log, task_mgr, verbose
            )

            cycle_duration = time.time() - cycle_start

            if ok:
                consecutive_failures = 0
                current_sleep = agent_cfg["min_sleep"]
                console.print(f"[green]{EMOJI['ok']} Cycle completed ({cycle_duration:.1f}s)[/green]")
            else:
                consecutive_failures += 1
                # Adaptive backoff: failure or too fast -> exponential backoff
                if cycle_duration < agent_cfg["idle_threshold"] or not ok:
                    current_sleep = min(
                        agent_cfg["max_sleep"],
                        max(agent_cfg["min_sleep"], current_sleep * 2)
                    )
                console.print(
                    f"[yellow]{EMOJI['warn']} Cycle failed "
                    f"(consecutive failures: {consecutive_failures})[/yellow]"
                )

            # Sleep (with jitter to prevent lock-step)
            jitter = random.uniform(0, min(1.0, current_sleep * 0.1))
            sleep_time = current_sleep + jitter
            console.print(f"[dim]Next cycle in: {sleep_time:.1f}s[/dim]")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        console.print(f"\n\n{EMOJI['stop']} Agent interrupted by user (completed {cycle_count} cycles)")

    finally:
        _release_lock(lock_path)
        _log_event(event_log, EventType.CUSTOM,
                   f"Agent serve stopped (cycles={cycle_count})",
                   actor="agent",
                   payload={
                       "cycles_completed": cycle_count,
                       "consecutive_failures": consecutive_failures,
                   })
        console.print(f"\n{EMOJI['ok']} Agent service ended. Total {cycle_count} cycle(s).")


def _execute_agent_cycle(
    client: LLMClient,
    project_root: Path,
    event_log: EventLog,
    task_mgr: TaskManager,
    verbose: bool,
) -> bool:
    """Execute a single agent cycle. Returns True=success, False=failure.

    Three phases: ASSESS+PLAN -> EXECUTE -> SOLIDIFY+REPORT
    """
    try:
        system = _build_system_prompt(project_root, agent_mode=True)

        # Phase 1: PLAN
        messages = [
            Message(role="system", content=system),
            Message(role="user", content=(
                "Execute one development cycle. Phase 1: ASSESS and PLAN.\n"
                "Identify the single most important task to advance the project.\n"
                "Output a concise plan with specific actions."
            )),
        ]

        plan_resp = client.chat(messages, temperature=0.3)
        if not plan_resp.ok:
            return False

        if verbose:
            console.print(Panel(
                Markdown(plan_resp.content),
                title="Plan", border_style="cyan",
            ))

        # Phase 2: EXECUTE
        messages.append(Message(role="assistant", content=plan_resp.content))
        messages.append(Message(role="user", content=(
            "Phase 2: EXECUTE. Generate the specific changes.\n"
            "For each file, output a JSON code block:\n"
            "```json\n"
            '{"file": "relative/path", "action": "create|modify|delete", '
            '"content": "full file content"}\n'
            "```\n"
            "Output ACTUAL code, not placeholders. One JSON block per file."
        )))

        exec_resp = client.chat(messages, temperature=0.2)
        if not exec_resp.ok:
            return False

        if verbose:
            console.print(Panel(
                Markdown(exec_resp.content),
                title="Execute", border_style="yellow",
            ))

        # Phase 3: APPLY + TEST + COMMIT
        from ..agent.executor import AgentExecutor
        executor = AgentExecutor(project_root)
        changes = executor.parse_changes(exec_resp.content)

        if not changes:
            _log_event(event_log, EventType.CUSTOM,
                       "Agent cycle: no parseable changes", actor="agent")
            return True  # Not a failure, just no executable changes

        # Get test command
        test_cmd = None
        cfg_path = project_root / "project.yaml"
        if cfg_path.exists():
            import yaml
            with open(cfg_path, "r", encoding="utf-8") as f:
                proj_cfg = yaml.safe_load(f) or {}
            qa = proj_cfg.get("quick_acceptance", {})
            if qa.get("start_command"):
                test_cmd = qa["start_command"]

        result = executor.execute_full_cycle(
            exec_resp.content,
            commit_message=f"[AGENT] {plan_resp.content[:80].splitlines()[0]}",
            test_command=test_cmd,
        )

        _log_event(event_log, EventType.CUSTOM,
                   f"Agent cycle {'completed' if result.success else 'failed'}",
                   actor="agent", payload=result.to_dict())

        if verbose and result.success:
            console.print(f"  Applied: {len(result.changes_applied)} files, "
                          f"git: {result.git_hash}")

        return result.success

    except Exception as e:
        console.print(f"[red]Cycle error: {e}[/red]")
        return False


@agent.command()
@click.option("--project", "-p", default=None, help=_("Project root directory"))
def status(project: Optional[str]):
    """View Agent runtime status

    Examples:

        vibecollab ai agent status
    """
    project_root = _find_project_root(project)
    vc_dir = project_root / ".vibecollab"
    lock_path = vc_dir / PID_LOCK_FILE

    console.print(Panel.fit(
        f"[bold]Agent Status[/bold]\nProject: {project_root}",
        border_style="blue",
    ))

    # Check PID lock
    if lock_path.exists():
        try:
            pid = int(lock_path.read_text().strip())
            try:
                os.kill(pid, 0)
                console.print(f"[green]{EMOJI['ok']} Agent is running (PID: {pid})[/green]")
            except OSError:
                console.print(f"[yellow]{EMOJI['warn']} Stale lock file (PID: {pid} has exited)[/yellow]")
        except ValueError:
            console.print(f"[yellow]{EMOJI['warn']} Invalid lock file[/yellow]")
    else:
        console.print("[dim]Agent is not running[/dim]")

    # LLM configuration status
    config = LLMConfig()
    console.print("\n[bold]LLM Configuration:[/bold]")
    for k, v in config.to_safe_dict().items():
        console.print(f"  {k}: {v}")

    # Task statistics
    tasks_path = vc_dir / "tasks.json"
    if tasks_path.exists():
        try:
            tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
            by_status = {}
            for t in tasks.values():
                s = t.get("status", "UNKNOWN")
                by_status[s] = by_status.get(s, 0) + 1
            console.print("\n[bold]Task Statistics:[/bold]")
            for s, n in sorted(by_status.items()):
                console.print(f"  {s}: {n}")
        except (json.JSONDecodeError, OSError):
            pass

    # Recent events
    events_path = vc_dir / "events.jsonl"
    if events_path.exists():
        try:
            event_log = EventLog(project_root)
            recent = event_log.read_recent(5)
            if recent:
                console.print("\n[bold]Recent Events:[/bold]")
                for evt in recent:
                    console.print(
                        f"  [{evt.event_type}] {evt.summary} "
                        f"({evt.timestamp[:19]})"
                    )
        except Exception:
            pass


# Export command group
__all__ = ["ai"]
