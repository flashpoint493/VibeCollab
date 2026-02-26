"""
Guide CLI 命令 — AI Agent 接入引导与行动建议

提供两个核心命令，让 AI Agent 能自主理解项目、自主推进开发：

命令:
    vibecollab onboard              AI 接入时的上下文引导
    vibecollab next                 修改后的下一步行动建议
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _safe_load_yaml(path: Path) -> Optional[dict]:
    """安全加载 YAML，失败返回 None"""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None


def _safe_read_text(path: Path, max_lines: int = 0) -> str:
    """安全读取文本文件"""
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
        if max_lines > 0:
            lines = text.splitlines()
            return "\n".join(lines[:max_lines])
        return text
    except Exception:
        return ""


def _get_git_uncommitted(project_root: Path) -> List[str]:
    """获取未提交的文件列表"""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=project_root, capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return [line.strip() for line in result.stdout.strip().splitlines()]
        return []
    except BaseException:
        return []


def _get_git_diff_files(project_root: Path) -> List[str]:
    """获取 git diff 的文件名列表"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=project_root, capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()
        return []
    except BaseException:
        return []


def _get_recent_decisions(decisions_path: Path, count: int = 3) -> List[str]:
    """从 DECISIONS.md 提取最近 N 条决策标题"""
    text = _safe_read_text(decisions_path)
    if not text:
        return []
    decisions = []
    for line in text.splitlines():
        if line.startswith("### DECISION-"):
            decisions.append(line.replace("### ", "").strip())
    return decisions[-count:] if decisions else []


def _extract_pending_from_roadmap(roadmap_path: Path) -> List[str]:
    """从 ROADMAP.md 提取未完成项 (- [ ])"""
    text = _safe_read_text(roadmap_path)
    if not text:
        return []
    pending = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            pending.append(stripped[5:].strip())
    return pending


def _check_linked_groups_freshness(
    project_root: Path, config: dict
) -> List[Dict]:
    """检查关联文档组的新鲜度，返回需要同步的组"""
    doc_config = config.get("documentation", {})
    consistency_config = doc_config.get("consistency", {})
    if not consistency_config.get("enabled", False):
        return []

    linked_groups = consistency_config.get("linked_groups", [])
    stale_groups = []

    for group in linked_groups:
        group_name = group.get("name", "")
        files = group.get("files", [])
        threshold_minutes = group.get("threshold_minutes", 15)

        if len(files) < 2:
            continue

        # 收集文件的 mtime
        mtimes = {}
        for f in files:
            full_path = project_root / f
            if full_path.exists():
                mtimes[f] = datetime.fromtimestamp(full_path.stat().st_mtime)

        if len(mtimes) < 2:
            continue

        sorted_files = sorted(mtimes.items(), key=lambda x: x[1], reverse=True)
        newest_file, newest_time = sorted_files[0]

        # 只关注 24h 内有修改的组
        hours_since = (datetime.now() - newest_time).total_seconds() / 3600
        if hours_since > 24:
            continue

        stale = []
        for f, t in sorted_files[1:]:
            diff_min = (newest_time - t).total_seconds() / 60
            if diff_min > threshold_minutes:
                stale.append((f, int(diff_min)))

        if stale:
            stale_groups.append({
                "group": group_name,
                "leader": newest_file,
                "stale": stale,
            })

    return stale_groups


def _get_read_files_list(config: dict) -> List[str]:
    """获取 dialogue_protocol.on_start.read_files"""
    return config.get("dialogue_protocol", {}).get("on_start", {}).get("read_files", [])


def _get_update_files_list(config: dict) -> List[str]:
    """获取 dialogue_protocol.on_end.update_files"""
    return config.get("dialogue_protocol", {}).get("on_end", {}).get("update_files", [])


def _suggest_commit_message(diff_files: List[str]) -> str:
    """根据 diff 文件列表建议 commit message prefix"""
    has_src = any(f.startswith("src/") for f in diff_files)
    has_test = any(f.startswith("tests/") for f in diff_files)
    has_doc = any(
        f.startswith("docs/") or f.endswith(".md") or f == "llms.txt"
        for f in diff_files
    )
    has_config = any(
        f in ("project.yaml", "pyproject.toml", ".gitignore")
        for f in diff_files
    )
    has_schema = any(f.startswith("schema/") for f in diff_files)

    if has_src and has_test:
        return "[FEAT]"
    elif has_test and not has_src:
        return "[TEST]"
    elif has_doc and not has_src:
        return "[DOC]"
    elif has_config and not has_src:
        return "[CONFIG]"
    elif has_schema:
        return "[DESIGN]"
    elif has_src:
        return "[FEAT]"
    return "[VIBE]"


# ============================================================
# vibecollab onboard
# ============================================================

@click.command()
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option("--developer", "-d", default=None, help="指定开发者 ID")
@click.option("--json", "as_json", is_flag=True, help="JSON 输出")
def onboard(config: str, developer: Optional[str], as_json: bool):
    """AI Agent 接入时的上下文引导

    输出项目全貌、当前进度、待办事项、应读文件列表，
    让 AI 无需猜测即可理解项目状态并开始工作。

    Examples:

        vibecollab onboard                  # 标准引导

        vibecollab onboard -d ocarina       # 指定开发者视角

        vibecollab onboard --json           # 机器可读输出
    """
    config_path = Path(config)
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    project_config = _safe_load_yaml(config_path)
    if not project_config:
        console.print("[red]错误:[/red] 无法加载 project.yaml")
        raise SystemExit(1)

    # === 1. 项目概况 ===
    proj = project_config.get("project", {})
    project_name = proj.get("name", "Unknown")
    project_version = proj.get("version", "Unknown")
    project_desc = proj.get("description", "")

    # === 2. 当前进度（从 CONTEXT.md） ===
    context_text = _safe_read_text(project_root / "docs" / "CONTEXT.md", max_lines=30)

    # === 3. 最近决策 ===
    recent_decisions = _get_recent_decisions(project_root / "docs" / "DECISIONS.md", 3)

    # === 4. 未完成的路线图项 ===
    pending_roadmap = _extract_pending_from_roadmap(project_root / "docs" / "ROADMAP.md")

    # === 5. 未提交的变更 ===
    uncommitted = _get_git_uncommitted(project_root)

    # === 6. 应读文件列表 ===
    read_files = _get_read_files_list(project_config)

    # === 7. 开发者信息 ===
    developer_info = None
    if developer:
        dev_context_path = project_root / "docs" / "developers" / developer / "CONTEXT.md"
        dev_meta_path = project_root / "docs" / "developers" / developer / ".metadata.yaml"
        developer_info = {
            "id": developer,
            "context": _safe_read_text(dev_context_path, max_lines=20),
            "metadata": _safe_load_yaml(dev_meta_path),
        }

    # === 8. 关键文件清单 ===
    key_files = project_config.get("documentation", {}).get("key_files", [])

    # === 9. Insight 统计（如果存在） ===
    insight_count = 0
    insights_dir = project_root / ".vibecollab" / "insights"
    if insights_dir.exists():
        insight_count = len(list(insights_dir.glob("INS-*.yaml")))

    # === 输出 ===
    if as_json:
        output = {
            "project": {"name": project_name, "version": project_version, "description": project_desc},
            "read_files": read_files,
            "recent_decisions": recent_decisions,
            "pending_roadmap": pending_roadmap,
            "uncommitted_changes": len(uncommitted),
            "insight_count": insight_count,
            "key_files": [kf.get("path", "") for kf in key_files],
        }
        if developer_info:
            output["developer"] = {
                "id": developer_info["id"],
                "has_context": bool(developer_info["context"]),
                "has_metadata": developer_info["metadata"] is not None,
            }
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # Rich 输出
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{project_name}[/bold cyan] {project_version}\n"
        f"[dim]{project_desc}[/dim]",
        title="项目概况",
    ))

    # 应读文件
    console.print()
    console.print("[bold]你应该先读的文件:[/bold]")
    for f in read_files:
        full_path = project_root / f
        exists = full_path.exists()
        status = "[green]存在[/green]" if exists else "[red]缺失[/red]"
        console.print(f"  {status}  {f}")

    # 当前进度
    if context_text:
        console.print()
        console.print(Panel(context_text, title="当前进度 (docs/CONTEXT.md)", border_style="blue"))

    # 开发者信息
    if developer_info:
        console.print()
        if developer_info["context"]:
            console.print(Panel(
                developer_info["context"],
                title=f"开发者 {developer} 的上下文",
                border_style="cyan"
            ))
        if developer_info["metadata"]:
            meta = developer_info["metadata"]
            tags = meta.get("tags", [])
            contributed = meta.get("contributed", [])
            bookmarks = meta.get("bookmarks", [])
            if tags or contributed or bookmarks:
                console.print(f"  [dim]Tags:[/dim] {', '.join(tags[:10])}")
                console.print(f"  [dim]Contributed:[/dim] {', '.join(contributed[:5])}")
                console.print(f"  [dim]Bookmarks:[/dim] {', '.join(bookmarks[:5])}")

    # 最近决策
    if recent_decisions:
        console.print()
        console.print("[bold]最近决策:[/bold]")
        for d in recent_decisions:
            console.print(f"  • {d}")

    # 路线图待办
    if pending_roadmap:
        console.print()
        console.print("[bold yellow]路线图待办:[/bold yellow]")
        for item in pending_roadmap[:10]:
            console.print(f"  [ ] {item}")

    # 未提交变更
    if uncommitted:
        console.print()
        console.print(f"[bold yellow]未提交变更: {len(uncommitted)} 个文件[/bold yellow]")
        for line in uncommitted[:8]:
            console.print(f"  {line}")
        if len(uncommitted) > 8:
            console.print(f"  [dim]... 还有 {len(uncommitted) - 8} 个[/dim]")

    # Insight 统计
    if insight_count > 0:
        console.print()
        console.print(f"[dim]Insight 沉淀: {insight_count} 条 (vibecollab insight list 查看)[/dim]")

    # 关键文件清单
    console.print()
    table = Table(title="关键文件清单", show_header=True)
    table.add_column("文件", style="cyan")
    table.add_column("用途")
    table.add_column("状态")
    for kf in key_files:
        path = kf.get("path", "")
        purpose = kf.get("purpose", "")
        exists = (project_root / path).exists()
        status = "[green]✓[/green]" if exists else "[red]✗[/red]"
        table.add_row(path, purpose, status)
    console.print(table)

    # 最后的引导建议
    console.print()
    suggestions = []
    if uncommitted:
        suggestions.append("有未提交变更 → 先 `git status` 检查是否需要 commit")
    if pending_roadmap:
        suggestions.append(f"路线图有 {len(pending_roadmap)} 项待办 → 查看 `docs/ROADMAP.md`")
    if not developer:
        suggestions.append("可用 `vibecollab onboard -d <你的ID>` 查看你的个人上下文")

    suggestions.append("修改文件后用 `vibecollab next` 查看下一步建议")
    suggestions.append("用 `vibecollab check --insights` 执行一致性自检")

    console.print(Panel(
        "\n".join(f"  • {s}" for s in suggestions),
        title="建议的下一步",
        border_style="green"
    ))


# ============================================================
# vibecollab next
# ============================================================

@click.command()
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option("--json", "as_json", is_flag=True, help="JSON 输出")
def next_step(config: str, as_json: bool):
    """修改后的下一步行动建议

    基于当前工作区状态（git diff、文件 mtime、linked_groups 配置）
    生成具体的行动建议：哪些文档需要同步、建议的 commit message、
    下一步应该做什么。

    Examples:

        vibecollab next                     # 查看行动建议

        vibecollab next --json              # 机器可读输出
    """
    config_path = Path(config)
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    project_config = _safe_load_yaml(config_path)
    if not project_config:
        console.print("[red]错误:[/red] 无法加载 project.yaml")
        raise SystemExit(1)

    # === 1. Git 状态 ===
    uncommitted = _get_git_uncommitted(project_root)
    diff_files = _get_git_diff_files(project_root)

    # === 2. 关联文档同步检查 ===
    stale_groups = _check_linked_groups_freshness(project_root, project_config)

    # === 3. 对话结束应更新的文件 ===
    update_files = _get_update_files_list(project_config)
    check_config = project_config.get("protocol_check", {}).get("checks", {}).get("documentation", {})
    threshold_hours = check_config.get("update_threshold_hours", 0.25)
    overdue_update_files = []
    for f in update_files:
        full_path = project_root / f
        if full_path.exists():
            mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
            hours_since = (datetime.now() - mtime).total_seconds() / 3600
            if hours_since > threshold_hours:
                overdue_update_files.append((f, int(hours_since * 60)))

    # === 4. Commit message 建议 ===
    suggested_prefix = _suggest_commit_message(diff_files) if diff_files else None

    # === 5. 关键文件缺失 ===
    key_files = project_config.get("documentation", {}).get("key_files", [])
    missing_key_files = []
    for kf in key_files:
        path = kf.get("path", "")
        if path and not (project_root / path).exists():
            missing_key_files.append(path)

    # === 6. 构建行动列表 ===
    actions: List[Dict] = []
    priority = 0

    # P0: 关联文档同步
    for group in stale_groups:
        for f, diff_min in group["stale"]:
            priority += 1
            actions.append({
                "priority": f"P0-{priority}",
                "type": "sync_document",
                "action": f"同步更新 {f}",
                "reason": f"{group['leader']} 已修改，{f} 落后 {diff_min} 分钟",
                "group": group["group"],
            })

    # P1: 对话结束应更新的文件
    for f, minutes in overdue_update_files:
        priority += 1
        actions.append({
            "priority": f"P1-{priority}",
            "type": "update_document",
            "action": f"更新 {f}",
            "reason": f"协议要求对话结束时更新，已超过 {minutes} 分钟",
        })

    # P1: 有变更未提交
    if uncommitted:
        priority += 1
        prefix = suggested_prefix or "[FEAT]"
        actions.append({
            "priority": f"P1-{priority}",
            "type": "git_commit",
            "action": f"提交变更 ({len(uncommitted)} 个文件)",
            "reason": "存在未提交的更改",
            "suggestion": f'git commit -m "{prefix} <描述>"',
        })

    # P2: 关键文件缺失
    for f in missing_key_files:
        priority += 1
        actions.append({
            "priority": f"P2-{priority}",
            "type": "create_file",
            "action": f"创建 {f}",
            "reason": "在 documentation.key_files 中声明但不存在",
        })

    # P3: 建议运行 check
    if actions:
        priority += 1
        actions.append({
            "priority": f"P3-{priority}",
            "type": "run_check",
            "action": "运行 vibecollab check --insights",
            "reason": "完成上述操作后建议自检一致性",
        })

    # === 输出 ===
    if as_json:
        output = {
            "uncommitted_count": len(uncommitted),
            "diff_files": diff_files,
            "stale_groups": stale_groups,
            "overdue_update_files": [{"file": f, "minutes_overdue": m} for f, m in overdue_update_files],
            "suggested_commit_prefix": suggested_prefix,
            "missing_key_files": missing_key_files,
            "actions": actions,
        }
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        return

    console.print()

    if not actions:
        console.print(Panel.fit(
            "[bold green]一切就绪，无需额外操作[/bold green]\n\n"
            "[dim]工作区干净，关联文档同步，无过期文件。[/dim]",
            title="Next Step"
        ))
        return

    console.print(Panel.fit(
        f"[bold]发现 {len(actions)} 项待处理事项[/bold]",
        title="Next Step"
    ))
    console.print()

    # 按优先级分组展示
    for action in actions:
        prio = action["priority"]
        if prio.startswith("P0"):
            style = "bold red"
            label = "紧急"
        elif prio.startswith("P1"):
            style = "bold yellow"
            label = "重要"
        elif prio.startswith("P2"):
            style = "yellow"
            label = "建议"
        else:
            style = "dim"
            label = "提示"

        console.print(f"  [{style}][{label}][/{style}] {action['action']}")
        console.print(f"         [dim]原因: {action['reason']}[/dim]")
        if "suggestion" in action:
            console.print(f"         [cyan]→ {action['suggestion']}[/cyan]")
        if "group" in action:
            console.print(f"         [dim]关联组: {action['group']}[/dim]")
        console.print()

    # diff 文件概览
    if diff_files:
        console.print("[bold]当前变更文件:[/bold]")
        for f in diff_files[:15]:
            console.print(f"  {f}")
        if len(diff_files) > 15:
            console.print(f"  [dim]... 还有 {len(diff_files) - 15} 个[/dim]")

        if suggested_prefix:
            console.print()
            console.print(f"[dim]建议的 commit prefix: {suggested_prefix}[/dim]")
