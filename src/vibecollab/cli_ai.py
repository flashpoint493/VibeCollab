"""
AI CLI 命令 — 人机对话 + 自主 Agent 模式

支持三种使用模式：
1. IDE 对话: 开发者在 Cursor/CodeBuddy 中，读 CONTRIBUTING_AI.md（已有）
2. CLI 人机交互: vibecollab ai ask / vibecollab ai chat
3. Agent 自主: vibecollab ai agent run / serve / plan

安全门控机制：
- 最大周期数限制 (max_cycles)
- 自适应睡眠 + 指数退避
- pending-solidify 检查 (前次未固化则等待)
- 单例 PID 锁 (防止多实例)
- 内存阈值保护
"""

import json
import os
import platform
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .event_log import Event, EventLog, EventType
from .llm_client import LLMClient, LLMConfig, LLMResponse, Message, build_project_context
from .task_manager import TaskManager, TaskStatus


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
# Windows GBK 兼容 (与 cli.py / cli_lifecycle.py 保持一致)
# ---------------------------------------------------------------------------

def is_windows_gbk():
    if platform.system() != "Windows":
        return False
    try:
        "✅⚠️❌ℹ️".encode(sys.stdout.encoding or "utf-8")
        return False
    except (UnicodeEncodeError, LookupError):
        return True

USE_EMOJI = not is_windows_gbk()
EMOJI = {
    "ok": "OK" if not USE_EMOJI else "✅",
    "warn": "!" if not USE_EMOJI else "⚠️",
    "err": "x" if not USE_EMOJI else "❌",
    "bot": ">" if not USE_EMOJI else "🤖",
    "user": ">" if not USE_EMOJI else "👤",
    "think": "..." if not USE_EMOJI else "🧠",
    "stop": "[STOP]" if not USE_EMOJI else "🛑",
}

console = Console()

# ---------------------------------------------------------------------------
# Agent 安全门控
# ---------------------------------------------------------------------------

# 默认值 (可通过环境变量覆盖)
DEFAULT_MAX_CYCLES = 50
DEFAULT_MIN_SLEEP_S = 2
DEFAULT_MAX_SLEEP_S = 300
DEFAULT_PENDING_SLEEP_S = 60
DEFAULT_MAX_RSS_MB = 500
DEFAULT_IDLE_THRESHOLD_S = 1  # 快速周期阈值

# 环境变量名
ENV_MAX_CYCLES = "VIBECOLLAB_AGENT_MAX_CYCLES"
ENV_MIN_SLEEP = "VIBECOLLAB_AGENT_MIN_SLEEP"
ENV_MAX_SLEEP = "VIBECOLLAB_AGENT_MAX_SLEEP"
ENV_MAX_RSS_MB = "VIBECOLLAB_AGENT_MAX_RSS_MB"

# PID 锁文件名
PID_LOCK_FILE = "agent.pid"


def _get_agent_config():
    """读取 Agent 运行配置 (环境变量 > 默认值)."""
    return {
        "max_cycles": int(os.getenv(ENV_MAX_CYCLES, str(DEFAULT_MAX_CYCLES))),
        "min_sleep": float(os.getenv(ENV_MIN_SLEEP, str(DEFAULT_MIN_SLEEP_S))),
        "max_sleep": float(os.getenv(ENV_MAX_SLEEP, str(DEFAULT_MAX_SLEEP_S))),
        "max_rss_mb": int(os.getenv(ENV_MAX_RSS_MB, str(DEFAULT_MAX_RSS_MB))),
        "pending_sleep": DEFAULT_PENDING_SLEEP_S,
        "idle_threshold": DEFAULT_IDLE_THRESHOLD_S,
    }


def _acquire_lock(lock_path: Path) -> bool:
    """单例 PID 锁 — 防止多个 agent 实例同时运行.

    - 锁文件存在 → 检查 PID 是否存活
    - 存活 → 拒绝启动
    - 陈旧 → 接管
    """
    if lock_path.exists():
        try:
            old_pid = int(lock_path.read_text().strip())
            # 检查进程是否存活 (signal 0 不发送信号，仅检查)
            os.kill(old_pid, 0)
            return False  # 已有实例在运行
        except (ValueError, OSError, ProcessLookupError):
            pass  # 陈旧锁或无效 PID → 接管

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(os.getpid()))
    return True


def _release_lock(lock_path: Path):
    """释放 PID 锁 — 仅当 PID 匹配时删除."""
    try:
        if lock_path.exists():
            stored_pid = int(lock_path.read_text().strip())
            if stored_pid == os.getpid():
                lock_path.unlink()
    except (ValueError, OSError):
        pass


def _check_rss_mb() -> float:
    """获取当前进程 RSS (MB). 跨平台兼容."""
    try:
        import resource
        # Unix: resource.getrusage (单位 KB on Linux, bytes on macOS)
        ru = resource.getrusage(resource.RUSAGE_SELF)
        rss_kb = ru.ru_maxrss
        if sys.platform == "darwin":
            return rss_kb / (1024 * 1024)  # macOS: bytes → MB
        return rss_kb / 1024  # Linux: KB → MB
    except ImportError:
        pass
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0  # 无法检测 → 不限制


def _is_pending_solidify(task_mgr: TaskManager) -> bool:
    """检查是否有任务处于 REVIEW 状态等待固化.

    前次运行创建/推进的任务如果未完成固化，则阻塞新周期.
    """
    review_tasks = task_mgr.list_tasks(status=TaskStatus.REVIEW)
    return len(review_tasks) > 0


# ---------------------------------------------------------------------------
# 项目根目录检测
# ---------------------------------------------------------------------------

def _find_project_root(start: Optional[str] = None) -> Path:
    """从指定目录或当前目录向上查找 project.yaml."""
    p = Path(start) if start else Path.cwd()
    for candidate in [p] + list(p.parents):
        if (candidate / "project.yaml").exists():
            return candidate
    return p  # fallback: 当前目录


def _ensure_llm_configured() -> LLMClient:
    """确保 LLM 已配置，返回客户端实例."""
    config = LLMConfig()
    if not config.is_configured:
        console.print(
            f"[red]{EMOJI['err']} LLM 未配置。[/red]\n\n"
            f"[bold]方式一 (推荐): 交互式配置向导[/bold]\n"
            f"  vibecollab config setup\n\n"
            f"[bold]方式二: 手动设置环境变量[/bold]\n"
            f"  export VIBECOLLAB_LLM_API_KEY=your-api-key\n"
            f"  export VIBECOLLAB_LLM_PROVIDER=openai  # 或 anthropic\n"
            f"  export VIBECOLLAB_LLM_BASE_URL=https://openrouter.ai/api/v1  # 可选\n\n"
            f"[bold]方式三: 配置文件[/bold]\n"
            f"  vibecollab config set llm.api_key your-api-key\n"
            f"  vibecollab config set llm.provider openai"
        )
        raise SystemExit(1)
    return LLMClient(config)


def _display_response(resp: LLMResponse, show_usage: bool = False):
    """格式化显示 LLM 响应."""
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
                f"[dim]模型: {resp.model} | "
                f"输入: {tokens_in} tokens | "
                f"输出: {tokens_out} tokens[/dim]"
            )
    else:
        console.print(f"[red]{EMOJI['err']} LLM 返回空响应[/red]")


# ---------------------------------------------------------------------------
# 系统 Prompt 构建
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
    """构建包含项目上下文的 system prompt."""
    base = SYSTEM_PROMPT_AGENT if agent_mode else SYSTEM_PROMPT_BASE
    context = build_project_context(project_root)
    return f"{base}\n\n# Project Context\n\n{context}"


# ---------------------------------------------------------------------------
# Click 命令组
# ---------------------------------------------------------------------------

@click.group()
def ai():
    """AI 助手命令 — 人机对话 & Agent 自主模式"""
    pass


# ===== 人机交互命令 =====

@ai.command()
@click.argument("question")
@click.option("--project", "-p", default=None, help="项目根目录 (默认自动检测)")
@click.option("--no-context", is_flag=True, help="不注入项目上下文")
@click.option("--temperature", "-t", default=0.7, type=float, help="采样温度 (0.0-1.0)")
@click.option("--verbose", "-v", is_flag=True, help="显示 token 用量等详细信息")
def ask(question: str, project: Optional[str], no_context: bool,
        temperature: float, verbose: bool):
    """向 AI 提问 (单轮，带项目上下文)

    Examples:

        vibecollab ai ask "下一步应该做什么?"
        vibecollab ai ask "这个模块的架构设计合理吗?" -v
        vibecollab ai ask "帮我写个测试" --no-context
    """
    client = _ensure_llm_configured()
    project_root = _find_project_root(project)

    console.print(f"[dim]项目: {project_root}[/dim]")
    console.print(f"[dim]模型: {client.config.model} ({client.config.provider})[/dim]")
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

        # 记录到 EventLog
        event_log = EventLog(project_root)
        _log_event(event_log, EventType.CUSTOM,
                   f"AI ask: {question[:100]}", actor="cli",
                   payload={"model": resp.model, "question_length": len(question)})

    except ImportError as e:
        console.print(f"[red]{EMOJI['err']} {e}[/red]")
        console.print("[dim]安装 LLM 依赖: pip install vibe-collab[llm][/dim]")
        raise SystemExit(1)
    except (RuntimeError, ValueError) as e:
        console.print(f"[red]{EMOJI['err']} LLM 调用失败: {e}[/red]")
        raise SystemExit(1)


@ai.command()
@click.option("--project", "-p", default=None, help="项目根目录 (默认自动检测)")
@click.option("--no-context", is_flag=True, help="不注入项目上下文")
@click.option("--temperature", "-t", default=0.7, type=float, help="采样温度")
@click.option("--verbose", "-v", is_flag=True, help="显示 token 用量")
def chat(project: Optional[str], no_context: bool, temperature: float, verbose: bool):
    """与 AI 多轮对话 (Ctrl+C 退出)

    Examples:

        vibecollab ai chat
        vibecollab ai chat -p ./my-project -v
    """
    client = _ensure_llm_configured()
    project_root = _find_project_root(project)

    console.print(f"[dim]项目: {project_root}[/dim]")
    console.print(f"[dim]模型: {client.config.model} ({client.config.provider})[/dim]")
    console.print("[dim]输入 'exit' 或 Ctrl+C 退出[/dim]\n")

    # 初始化消息历史
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
                console.print(f"\n{EMOJI['ok']} 对话结束")
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
                    console.print(f"[red]{EMOJI['err']} 空响应，请重试[/red]")
                    messages.pop()  # 移除未成功的用户消息

            except (RuntimeError, ValueError) as e:
                console.print(f"[red]{EMOJI['err']} 调用失败: {e}[/red]")
                messages.pop()

    except KeyboardInterrupt:
        console.print(f"\n\n{EMOJI['ok']} 对话结束 ({turn_count} 轮)")

    # 记录到 EventLog
    if turn_count > 0:
        event_log = EventLog(project_root)
        _log_event(event_log, EventType.CUSTOM,
                   f"AI chat session: {turn_count} turns", actor="cli",
                   payload={"turns": turn_count, "model": client.config.model})


# ===== Agent 自主命令 =====

@ai.group()
def agent():
    """Agent 自主模式 — 服务器部署，自驱开发"""
    pass


@agent.command()
@click.option("--project", "-p", default=None, help="项目根目录")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def plan(project: Optional[str], verbose: bool):
    """分析项目状态，生成行动计划 (不执行)

    读取项目上下文、任务列表、事件日志，让 LLM 生成下一步计划。
    这是一个只读操作，不会修改任何文件。

    Examples:

        vibecollab ai agent plan
        vibecollab ai agent plan -p ./my-project -v
    """
    client = _ensure_llm_configured()
    project_root = _find_project_root(project)

    console.print(Panel.fit(
        f"[bold]Agent Plan 模式[/bold]\n项目: {project_root}",
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
        console.print(f"[cyan]{EMOJI['think']} 分析项目状态...[/cyan]")
        resp = client.chat(messages, temperature=0.3)  # 低温度，更确定性

        _display_response(resp, show_usage=verbose)

        # 记录到 EventLog
        event_log = EventLog(project_root)
        _log_event(event_log, EventType.CUSTOM,
                   "Agent plan: generated action plan", actor="agent",
                   payload={"model": resp.model})

    except (ImportError, RuntimeError, ValueError) as e:
        console.print(f"[red]{EMOJI['err']} {e}[/red]")
        raise SystemExit(1)


@agent.command()
@click.option("--project", "-p", default=None, help="项目根目录")
@click.option("--dry-run", is_flag=True, help="试运行 (只生成计划，不执行)")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def run(project: Optional[str], dry_run: bool, verbose: bool):
    """执行单次 Agent 周期: Plan -> Execute -> Solidify

    适合 cron 定时任务或手动触发。每次运行只执行一个周期。

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
        f"[bold]Agent Run 模式[/bold] (单次周期)\n"
        f"项目: {project_root}\n"
        f"Dry-run: {'是' if dry_run else '否'}",
        border_style="yellow",
    ))

    # Gate: pending solidify 检查
    if _is_pending_solidify(task_mgr):
        review_tasks = task_mgr.list_tasks(status=TaskStatus.REVIEW)
        task_ids = [t.id for t in review_tasks]
        console.print(
            f"[yellow]{EMOJI['warn']} 存在待固化任务: {', '.join(task_ids)}[/yellow]\n"
            f"请先完成 review 再运行新周期。"
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
        console.print(f"[cyan]{EMOJI['think']} Phase 1: 分析与规划...[/cyan]")
        plan_resp = client.chat(messages, temperature=0.3)

        if not plan_resp.ok:
            console.print(f"[red]{EMOJI['err']} Plan 阶段失败: 空响应[/red]")
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
            console.print(f"\n[yellow]{EMOJI['warn']} Dry-run 模式: 不执行变更[/yellow]")
            return

        # Phase 2: EXECUTE (让 LLM 生成具体代码变更)
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

        console.print(f"[cyan]{EMOJI['think']} Phase 2: 生成代码变更...[/cyan]")
        exec_resp = client.chat(messages, temperature=0.2)

        if exec_resp.ok:
            console.print(Panel(
                Markdown(exec_resp.content),
                title="Generated Changes",
                border_style="yellow",
            ))

        # Phase 3: APPLY + TEST + COMMIT
        console.print("\n[cyan]Phase 3: APPLY + TEST + COMMIT[/cyan]")

        from .agent_executor import AgentExecutor
        executor = AgentExecutor(project_root)
        changes = executor.parse_changes(exec_resp.content if exec_resp.ok else "")

        if not changes:
            console.print(f"[yellow]{EMOJI['warn']} 未从 LLM 输出中解析到文件变更[/yellow]")
            _log_event(event_log, EventType.CUSTOM,
                       "Agent run: no parseable changes", actor="agent")
            return

        console.print(f"  解析到 {len(changes)} 个文件变更:")
        for c in changes:
            console.print(f"    {c.action}: {c.file}")

        # 获取测试命令
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
            console.print(f"\n{EMOJI['ok']} [green]周期完成![/green]")
            for applied in result.changes_applied:
                console.print(f"  [green]{applied}[/green]")
            if result.test_passed:
                console.print(f"  {EMOJI['ok']} 测试通过")
            if result.git_committed:
                console.print(f"  {EMOJI['ok']} Git commit: {result.git_hash}")

            _log_event(event_log, EventType.CUSTOM,
                       "Agent run: cycle completed successfully", actor="agent",
                       payload=result.to_dict())
        else:
            console.print(f"\n[red]{EMOJI['err']} 周期执行失败[/red]")
            for err in result.errors:
                console.print(f"  [red]{err}[/red]")
            if result.rollback_performed:
                console.print(f"  [yellow]{EMOJI['warn']} 已回滚所有变更[/yellow]")

            _log_event(event_log, EventType.VALIDATION_FAILED,
                       "Agent run: execution failed", actor="agent",
                       payload=result.to_dict())

    except (ImportError, RuntimeError, ValueError) as e:
        console.print(f"[red]{EMOJI['err']} Agent run 失败: {e}[/red]")
        _log_event(event_log, EventType.VALIDATION_FAILED,
                   f"Agent run failed: {str(e)[:200]}", actor="agent")
        raise SystemExit(1)


@agent.command()
@click.option("--project", "-p", default=None, help="项目根目录")
@click.option("--max-cycles", "-n", default=None, type=int,
              help=f"最大周期数 (默认: {DEFAULT_MAX_CYCLES})")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def serve(project: Optional[str], max_cycles: Optional[int], verbose: bool):
    """长运行 Agent 服务 — 循环执行 Plan -> Execute -> Solidify

    适合服务器部署，自驱动推进项目开发。
    包含完整安全门控: 最大周期、自适应睡眠、pending-solidify 等待、
    PID 锁、内存阈值、修复循环断路器。

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

    # Gate 1: 单例 PID 锁
    if not _acquire_lock(lock_path):
        console.print(
            f"[red]{EMOJI['err']} Agent 已有实例在运行。[/red]\n"
            f"锁文件: {lock_path}\n"
            f"如确认无其他实例，删除锁文件后重试。"
        )
        raise SystemExit(1)

    event_log = EventLog(project_root)
    task_mgr = TaskManager(project_root, event_log)

    console.print(Panel.fit(
        f"[bold]Agent Serve 模式[/bold] (长运行)\n"
        f"项目: {project_root}\n"
        f"最大周期: {agent_cfg['max_cycles']}\n"
        f"PID: {os.getpid()}\n"
        f"模型: {client.config.model} ({client.config.provider})",
        border_style="green",
    ))

    _log_event(event_log, EventType.CUSTOM,
               f"Agent serve started (max_cycles={agent_cfg['max_cycles']})",
               actor="agent",
               payload={"pid": os.getpid(), "config": agent_cfg})

    cycle_count = 0
    consecutive_failures = 0
    current_sleep = agent_cfg["min_sleep"]
    CIRCUIT_BREAKER_THRESHOLD = 3  # 连续失败 N 次触发断路器

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

            # Gate 2: pending solidify 检查
            if _is_pending_solidify(task_mgr):
                review_tasks = task_mgr.list_tasks(status=TaskStatus.REVIEW)
                task_ids = [t.id for t in review_tasks]
                console.print(
                    f"[yellow]{EMOJI['warn']} 待固化任务: {', '.join(task_ids)} "
                    f"— 等待 {agent_cfg['pending_sleep']}s[/yellow]"
                )
                time.sleep(agent_cfg["pending_sleep"])
                cycle_count -= 1  # 不计入周期数
                continue

            # Gate 3: 内存检查
            rss_mb = _check_rss_mb()
            if rss_mb > 0 and rss_mb > agent_cfg["max_rss_mb"]:
                console.print(
                    f"[red]{EMOJI['stop']} 内存超限: {rss_mb:.0f}MB > {agent_cfg['max_rss_mb']}MB "
                    f"— 停止服务[/red]"
                )
                break

            # Gate 4: 修复循环断路器
            if consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD:
                console.print(
                    f"[red]{EMOJI['stop']} 断路器触发: 连续 {consecutive_failures} 次失败 "
                    f"— 等待 {agent_cfg['max_sleep']}s 后重试[/red]"
                )
                _log_event(event_log, EventType.VALIDATION_FAILED,
                           f"Circuit breaker: {consecutive_failures} consecutive failures",
                           actor="agent")
                time.sleep(agent_cfg["max_sleep"])
                consecutive_failures = 0  # 重置，给一次机会
                continue

            # 执行周期
            ok = _execute_agent_cycle(
                client, project_root, event_log, task_mgr, verbose
            )

            cycle_duration = time.time() - cycle_start

            if ok:
                consecutive_failures = 0
                current_sleep = agent_cfg["min_sleep"]
                console.print(f"[green]{EMOJI['ok']} 周期完成 ({cycle_duration:.1f}s)[/green]")
            else:
                consecutive_failures += 1
                # 自适应退避: 失败或过快 → 指数退避
                if cycle_duration < agent_cfg["idle_threshold"] or not ok:
                    current_sleep = min(
                        agent_cfg["max_sleep"],
                        max(agent_cfg["min_sleep"], current_sleep * 2)
                    )
                console.print(
                    f"[yellow]{EMOJI['warn']} 周期失败 "
                    f"(连续失败: {consecutive_failures})[/yellow]"
                )

            # 睡眠 (加抖动防止锁步)
            jitter = random.uniform(0, min(1.0, current_sleep * 0.1))
            sleep_time = current_sleep + jitter
            console.print(f"[dim]下次周期: {sleep_time:.1f}s 后[/dim]")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        console.print(f"\n\n{EMOJI['stop']} Agent 被用户中断 (已完成 {cycle_count} 周期)")

    finally:
        _release_lock(lock_path)
        _log_event(event_log, EventType.CUSTOM,
                   f"Agent serve stopped (cycles={cycle_count})",
                   actor="agent",
                   payload={
                       "cycles_completed": cycle_count,
                       "consecutive_failures": consecutive_failures,
                   })
        console.print(f"\n{EMOJI['ok']} Agent 服务结束。共 {cycle_count} 个周期。")


def _execute_agent_cycle(
    client: LLMClient,
    project_root: Path,
    event_log: EventLog,
    task_mgr: TaskManager,
    verbose: bool,
) -> bool:
    """执行单个 agent 周期. 返回 True=成功, False=失败.

    三阶段: ASSESS+PLAN → EXECUTE → SOLIDIFY+REPORT
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
        from .agent_executor import AgentExecutor
        executor = AgentExecutor(project_root)
        changes = executor.parse_changes(exec_resp.content)

        if not changes:
            _log_event(event_log, EventType.CUSTOM,
                       "Agent cycle: no parseable changes", actor="agent")
            return True  # 非失败，只是没有可执行的变更

        # 获取测试命令
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
@click.option("--project", "-p", default=None, help="项目根目录")
def status(project: Optional[str]):
    """查看 Agent 运行状态

    Examples:

        vibecollab ai agent status
    """
    project_root = _find_project_root(project)
    vc_dir = project_root / ".vibecollab"
    lock_path = vc_dir / PID_LOCK_FILE

    console.print(Panel.fit(
        f"[bold]Agent 状态[/bold]\n项目: {project_root}",
        border_style="blue",
    ))

    # 检查 PID 锁
    if lock_path.exists():
        try:
            pid = int(lock_path.read_text().strip())
            try:
                os.kill(pid, 0)
                console.print(f"[green]{EMOJI['ok']} Agent 正在运行 (PID: {pid})[/green]")
            except OSError:
                console.print(f"[yellow]{EMOJI['warn']} 陈旧锁文件 (PID: {pid} 已退出)[/yellow]")
        except ValueError:
            console.print(f"[yellow]{EMOJI['warn']} 无效锁文件[/yellow]")
    else:
        console.print("[dim]Agent 未运行[/dim]")

    # LLM 配置状态
    config = LLMConfig()
    console.print("\n[bold]LLM 配置:[/bold]")
    for k, v in config.to_safe_dict().items():
        console.print(f"  {k}: {v}")

    # 任务统计
    tasks_path = vc_dir / "tasks.json"
    if tasks_path.exists():
        try:
            tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
            by_status = {}
            for t in tasks.values():
                s = t.get("status", "UNKNOWN")
                by_status[s] = by_status.get(s, 0) + 1
            console.print("\n[bold]任务统计:[/bold]")
            for s, n in sorted(by_status.items()):
                console.print(f"  {s}: {n}")
        except (json.JSONDecodeError, OSError):
            pass

    # 最近事件
    events_path = vc_dir / "events.jsonl"
    if events_path.exists():
        try:
            event_log = EventLog(project_root)
            recent = event_log.read_recent(5)
            if recent:
                console.print("\n[bold]最近事件:[/bold]")
                for evt in recent:
                    console.print(
                        f"  [{evt.event_type}] {evt.summary} "
                        f"({evt.timestamp[:19]})"
                    )
        except Exception:
            pass


# 导出命令组
__all__ = ["ai"]
