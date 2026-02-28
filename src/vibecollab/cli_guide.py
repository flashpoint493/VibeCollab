"""
Guide CLI 命令 — AI Agent 接入引导与行动建议

提供三个核心命令，让 AI Agent 能自主理解项目、自主推进开发：

命令:
    vibecollab onboard              AI 接入时的上下文引导（Rich 面板）
    vibecollab prompt               生成 LLM 可直接使用的上下文 prompt 文本
    vibecollab next                 修改后的下一步行动建议
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ._compat import BULLET, is_windows_gbk, sanitize_for_console

logger = logging.getLogger(__name__)

console = Console()


def _search_related_insights(
    project_root: Path, query_text: str, top_k: int = 5
) -> List[Dict]:
    """从向量索引中搜索与查询文本相关的 Insight

    返回 [{id, title, tags, score}] 列表，如果索引不存在则返回空列表。
    """
    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    if not db_path.exists():
        return []

    try:
        from .embedder import Embedder, EmbedderConfig
        from .vector_store import VectorStore

        # 从已有 DB 推断维度
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT dimensions FROM vectors LIMIT 1"
        ).fetchone()
        conn.close()

        if not row:
            return []
        dimensions = row[0]

        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=dimensions))
        store = VectorStore(db_path=db_path, dimensions=dimensions)

        query_vector = embedder.embed_text(query_text)
        results = store.search(
            query_vector, top_k=top_k, source_type="insight"
        )
        store.close()

        related = []
        for r in results:
            meta = r.metadata or {}
            related.append({
                "id": r.doc_id.replace("insight:", ""),
                "title": meta.get("title", ""),
                "tags": meta.get("tags", []),
                "score": round(r.score, 3),
            })
        return related

    except Exception as e:
        logger.debug("语义搜索 Insight 失败: %s", e)
        return []


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


def _collect_project_context(
    config_path: Path, developer: Optional[str] = None
) -> Dict:
    """收集项目上下文数据（onboard 和 prompt 共用）

    Returns:
        Dict 包含: project_root, project_name, project_version, project_desc,
        context_text, recent_decisions, pending_roadmap, uncommitted,
        read_files, developer_info, key_files, insight_count, top_insights,
        project_config
    """
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    project_config = _safe_load_yaml(config_path)
    if not project_config:
        return {}

    proj = project_config.get("project", {})

    # 开发者信息
    developer_info = None
    if developer:
        dev_context_path = project_root / "docs" / "developers" / developer / "CONTEXT.md"
        dev_meta_path = project_root / "docs" / "developers" / developer / ".metadata.yaml"
        developer_info = {
            "id": developer,
            "context": _safe_read_text(dev_context_path, max_lines=20),
            "metadata": _safe_load_yaml(dev_meta_path),
        }

    # Insight
    insight_count = 0
    top_insights: List[Dict] = []
    insights_dir = project_root / ".vibecollab" / "insights"
    if insights_dir.exists():
        insight_files = sorted(insights_dir.glob("INS-*.yaml"), reverse=True)
        insight_count = len(insight_files)
        for ins_file in insight_files[:5]:
            ins_data = _safe_load_yaml(ins_file)
            if ins_data:
                top_insights.append({
                    "id": ins_data.get("id", ins_file.stem),
                    "title": ins_data.get("title", ""),
                    "tags": ins_data.get("tags", []),
                })

    # Task 概览
    active_tasks: List[Dict] = []
    task_summary: Dict = {"total": 0, "todo": 0, "in_progress": 0, "review": 0, "done": 0}
    try:
        from .task_manager import TaskManager
        tm = TaskManager(project_root=project_root)
        all_tasks = tm.list_tasks()
        task_summary["total"] = len(all_tasks)
        for t in all_tasks:
            status_key = t.status.lower()
            if status_key in task_summary:
                task_summary[status_key] += 1
            if t.status != "DONE":
                active_tasks.append({
                    "id": t.id,
                    "feature": t.feature,
                    "status": t.status,
                    "assignee": t.assignee or "-",
                })
    except Exception:
        pass

    # EventLog 最近事件
    recent_events: List[Dict] = []
    try:
        from .event_log import EventLog
        el = EventLog(project_root=project_root)
        for evt in el.read_recent(5):
            recent_events.append({
                "event_type": evt.event_type,
                "summary": evt.summary,
                "actor": evt.actor,
                "timestamp": evt.timestamp[:19] if evt.timestamp else "",
            })
    except Exception:
        pass

    # 语义搜索: 从当前任务描述匹配相关 Insight
    context_text = _safe_read_text(project_root / "docs" / "CONTEXT.md", max_lines=30)
    related_insights: List[Dict] = []

    # 构建查询文本: 优先用开发者上下文，否则用项目 CONTEXT.md
    query_text = ""
    if developer_info and developer_info.get("context"):
        query_text = developer_info["context"]
    elif context_text:
        query_text = context_text

    if query_text and insight_count > 0:
        related_insights = _search_related_insights(project_root, query_text)

    return {
        "project_root": project_root,
        "project_config": project_config,
        "project_name": proj.get("name", "Unknown"),
        "project_version": proj.get("version", "Unknown"),
        "project_desc": proj.get("description", ""),
        "context_text": context_text,
        "recent_decisions": _get_recent_decisions(project_root / "docs" / "DECISIONS.md", 3),
        "pending_roadmap": _extract_pending_from_roadmap(project_root / "docs" / "ROADMAP.md"),
        "uncommitted": _get_git_uncommitted(project_root),
        "read_files": _get_read_files_list(project_config),
        "developer_info": developer_info,
        "key_files": project_config.get("documentation", {}).get("key_files", []),
        "insight_count": insight_count,
        "top_insights": top_insights,
        "related_insights": related_insights,
        "active_tasks": active_tasks,
        "task_summary": task_summary,
        "recent_events": recent_events,
    }


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
    ctx = _collect_project_context(config_path, developer)
    if not ctx:
        console.print("[red]错误:[/red] 无法加载 project.yaml")
        raise SystemExit(1)

    project_root = ctx["project_root"]
    project_name = ctx["project_name"]
    project_version = ctx["project_version"]
    project_desc = ctx["project_desc"]
    context_text = ctx["context_text"]
    recent_decisions = ctx["recent_decisions"]
    pending_roadmap = ctx["pending_roadmap"]
    uncommitted = ctx["uncommitted"]
    read_files = ctx["read_files"]
    developer_info = ctx["developer_info"]
    key_files = ctx["key_files"]
    insight_count = ctx["insight_count"]
    top_insights = ctx["top_insights"]
    related_insights = ctx.get("related_insights", [])
    active_tasks = ctx.get("active_tasks", [])
    task_summary = ctx.get("task_summary", {})
    recent_events = ctx.get("recent_events", [])

    # === 输出 ===
    if as_json:
        output = {
            "project": {"name": project_name, "version": project_version, "description": project_desc},
            "read_files": read_files,
            "recent_decisions": recent_decisions,
            "pending_roadmap": pending_roadmap,
            "uncommitted_changes": len(uncommitted),
            "insight_count": insight_count,
            "top_insights": top_insights,
            "related_insights": related_insights,
            "key_files": [kf.get("path", "") for kf in key_files],
            "task_summary": task_summary,
            "active_tasks": active_tasks,
            "recent_events": recent_events,
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

    # 当前进度 (Windows GBK 下需替换不可编码字符，避免 Rich 输出时报错)
    if context_text:
        console.print()
        safe_context = sanitize_for_console(context_text) if is_windows_gbk() else context_text
        console.print(Panel(safe_context, title="当前进度 (docs/CONTEXT.md)", border_style="blue"))

    # 开发者信息
    if developer_info:
        console.print()
        if developer_info["context"]:
            dev_ctx = developer_info["context"]
            if is_windows_gbk():
                dev_ctx = sanitize_for_console(dev_ctx)
            console.print(Panel(
                dev_ctx,
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
            console.print(f"  {BULLET} {d}")

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

    # Insight 统计 + Top-N 摘要
    if insight_count > 0:
        console.print()
        console.print(f"[bold]Insight 沉淀: {insight_count} 条[/bold]")
        if top_insights:
            for ins in top_insights:
                tags_str = ", ".join(ins["tags"][:4]) if ins["tags"] else ""
                tag_label = f" [dim]({tags_str})[/dim]" if tags_str else ""
                console.print(f"  {BULLET} {ins['id']}: {ins['title']}{tag_label}")
            if insight_count > 5:
                console.print(f"  [dim]... 还有 {insight_count - 5} 条 (vibecollab insight list 查看)[/dim]")
        else:
            console.print(f"  [dim]vibecollab insight list 查看全部[/dim]")

    # 与当前任务相关的 Insight（语义匹配）
    if related_insights:
        console.print()
        ri_lines = []
        for ri in related_insights:
            tags_str = ", ".join(ri["tags"][:4]) if ri.get("tags") else ""
            tag_part = f" [dim]({tags_str})[/dim]" if tags_str else ""
            score_label = f"[dim]{ri['score']:.2f}[/dim]" if ri.get("score") else ""
            ri_lines.append(
                f"  {BULLET} [bold]{ri['id']}[/bold]: {ri.get('title', '')}{tag_part}  {score_label}"
            )
        console.print(Panel(
            "\n".join(ri_lines),
            title="与当前任务相关的 Insight (语义匹配)",
            border_style="magenta",
        ))

    # Task 概览
    total_tasks = task_summary.get("total", 0)
    if total_tasks > 0:
        console.print()
        ts = task_summary
        console.print(
            f"[bold]任务概览:[/bold] "
            f"TODO={ts.get('todo', 0)} "
            f"IN_PROGRESS={ts.get('in_progress', 0)} "
            f"REVIEW={ts.get('review', 0)} "
            f"DONE={ts.get('done', 0)} "
            f"(共 {total_tasks})"
        )
        if active_tasks:
            for at in active_tasks[:8]:
                status_style = {
                    "TODO": "dim", "IN_PROGRESS": "yellow", "REVIEW": "cyan",
                }.get(at["status"], "")
                console.print(
                    f"  {BULLET} {at['id']}  [{status_style}]{at['status']:12s}[/{status_style}]  "
                    f"{at['feature']}  (@{at['assignee']})"
                )
            if len(active_tasks) > 8:
                console.print(f"  [dim]... 还有 {len(active_tasks) - 8} 个活跃任务[/dim]")

    # 最近 EventLog 事件
    if recent_events:
        console.print()
        evt_lines = []
        for evt in recent_events:
            evt_lines.append(
                f"  {BULLET} [dim]{evt['timestamp']}[/dim]  "
                f"{evt['summary']}  [dim](@{evt['actor']})[/dim]"
            )
        console.print(Panel(
            "\n".join(evt_lines),
            title="最近事件 (EventLog)",
            border_style="dim",
        ))

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
        "\n".join(f"  {BULLET} {s}" for s in suggestions),
        title="建议的下一步",
        border_style="green"
    ))


# ============================================================
# vibecollab prompt — 生成 LLM 上下文 prompt
# ============================================================

# 协议章节与 CONTRIBUTING_AI.md 的标题映射
_SECTION_MAP = {
    "protocol": [
        "# 一、核心理念",
        "# 三、决策分级制度",
        "## 4.2 标准对话流程",
    ],
    "context": [],       # 动态生成，不从文件提取
    "insight": [
        "# 经验沉淀工作流 (Insight Workflow)",
    ],
    "roles": [
        "# 二、职能角色定义",
    ],
    "testing": [
        "# 五、测试体系",
    ],
    "git": [
        "## 4.3 Git 协作规范",
    ],
}

_ALL_SECTIONS = ["protocol", "context", "insight"]


def _extract_md_sections(text: str, start_headings: List[str]) -> str:
    """从 Markdown 文本中提取指定标题开始到下一个同级标题结束的内容"""
    lines = text.splitlines()
    result_parts: List[str] = []

    for start_heading in start_headings:
        # 确定标题级别
        heading_level = len(start_heading) - len(start_heading.lstrip("#"))
        capturing = False
        section_lines: List[str] = []

        for line in lines:
            if line.strip() == start_heading.strip():
                capturing = True
                section_lines = [line]
                continue

            if capturing:
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    line_level = len(stripped) - len(stripped.lstrip("#"))
                    if line_level <= heading_level:
                        break
                section_lines.append(line)

        if section_lines:
            result_parts.append("\n".join(section_lines))

    return "\n\n".join(result_parts)


def _build_prompt_text(
    ctx: Dict,
    sections: List[str],
    compact: bool = False,
) -> str:
    """构建 LLM prompt 纯文本"""
    parts: List[str] = []
    project_root = ctx["project_root"]

    # Header
    parts.append(f"# 项目上下文: {ctx['project_name']} {ctx['project_version']}")
    parts.append(f"> {ctx['project_desc']}")
    parts.append("")

    # Protocol section — 从 CONTRIBUTING_AI.md 提取关键章节
    if "protocol" in sections:
        contrib_path = project_root / "CONTRIBUTING_AI.md"
        if contrib_path.exists():
            contrib_text = _safe_read_text(contrib_path)
            headings = _SECTION_MAP["protocol"]
            if not compact:
                # 完整模式: 加上更多章节
                headings = headings + _SECTION_MAP.get("roles", []) + _SECTION_MAP.get("git", [])
            extracted = _extract_md_sections(contrib_text, headings)
            if extracted:
                parts.append("---")
                parts.append("## 协作协议")
                parts.append(extracted)
                parts.append("")

    # Context section
    if "context" in sections:
        parts.append("---")
        parts.append("## 当前状态")
        parts.append("")

        if ctx["context_text"]:
            parts.append(ctx["context_text"])
            parts.append("")

        dev_info = ctx.get("developer_info")
        if dev_info and dev_info.get("context"):
            parts.append(f"### 开发者: {dev_info['id']}")
            parts.append(dev_info["context"])
            parts.append("")

        if ctx["recent_decisions"]:
            parts.append("### 最近决策")
            for d in ctx["recent_decisions"]:
                parts.append(f"- {d}")
            parts.append("")

        if not compact and ctx["pending_roadmap"]:
            parts.append("### 路线图待办")
            for item in ctx["pending_roadmap"][:10]:
                parts.append(f"- [ ] {item}")
            parts.append("")

        if ctx["uncommitted"]:
            parts.append(f"### 未提交变更: {len(ctx['uncommitted'])} 个文件")
            parts.append("")

    # Insight section
    if "insight" in sections and ctx["top_insights"]:
        parts.append("---")
        parts.append(f"## Insight 沉淀 ({ctx['insight_count']} 条)")
        parts.append("")
        for ins in ctx["top_insights"]:
            tags_str = ", ".join(ins["tags"][:4]) if ins["tags"] else ""
            tag_part = f" ({tags_str})" if tags_str else ""
            parts.append(f"- **{ins['id']}**: {ins['title']}{tag_part}")
        if ctx["insight_count"] > 5:
            parts.append(f"- ... 还有 {ctx['insight_count'] - 5} 条")
        parts.append("")
        parts.append("> 使用 `vibecollab insight search --tags <关键词>` 检索相关经验")
        parts.append("")

        # 在非 compact 模式下，附加 Insight 工作流说明
        if not compact:
            contrib_path = project_root / "CONTRIBUTING_AI.md"
            if contrib_path.exists():
                contrib_text = _safe_read_text(contrib_path)
                insight_section = _extract_md_sections(contrib_text, _SECTION_MAP["insight"])
                if insight_section:
                    parts.append(insight_section)
                    parts.append("")

    # Footer
    parts.append("---")
    parts.append("*由 `vibecollab prompt` 自动生成*")

    return "\n".join(parts)


@click.command("prompt")
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option("--developer", "-d", default=None, help="指定开发者 ID")
@click.option("--compact", is_flag=True, help="精简模式（仅协议核心 + 当前状态）")
@click.option(
    "--sections", "-s", default=None,
    help="选择性注入章节，逗号分隔 (protocol,context,insight,roles,testing,git)"
)
@click.option("--copy", "to_clipboard", is_flag=True, help="复制到剪贴板")
def prompt_cmd(
    config: str,
    developer: Optional[str],
    compact: bool,
    sections: Optional[str],
    to_clipboard: bool,
):
    """生成 LLM 可直接使用的上下文 prompt

    输出纯 Markdown 文本，包含协作协议摘要、项目当前状态、
    Insight 经验等，可直接复制粘贴到任何 LLM 对话窗口。

    Examples:

        vibecollab prompt                     # 完整 prompt

        vibecollab prompt --compact           # 精简版

        vibecollab prompt --copy              # 直接复制到剪贴板

        vibecollab prompt -d ocarina          # 含开发者上下文

        vibecollab prompt -s protocol,context # 只要协议+状态
    """
    config_path = Path(config)
    ctx = _collect_project_context(config_path, developer)
    if not ctx:
        console.print("[red]错误:[/red] 无法加载 project.yaml")
        raise SystemExit(1)

    # 解析 sections
    if sections:
        selected = [s.strip() for s in sections.split(",") if s.strip()]
    else:
        selected = list(_ALL_SECTIONS)

    text = _build_prompt_text(ctx, selected, compact=compact)

    if to_clipboard:
        try:
            import subprocess as _sp
            process = _sp.Popen(["clip"], stdin=_sp.PIPE, shell=True)
            process.communicate(text.encode("utf-16-le"))
            token_estimate = len(text) // 4
            console.print(
                f"[green]OK[/green] prompt 已复制到剪贴板 "
                f"(~{token_estimate} tokens, {len(text)} chars)"
            )
        except Exception:
            click.echo(text)
            console.print("[yellow]警告: 剪贴板复制失败，已输出到 stdout[/yellow]")
    else:
        click.echo(text)


# ============================================================
# Insight 沉淀提示辅助
# ============================================================

def _check_insight_opportunity(project_root: Path, diff_files: List[str]) -> Optional[str]:
    """检查当前工作区是否存在值得沉淀 Insight 的信号。

    返回提示原因字符串，如果无需提示则返回 None。
    """
    if not diff_files:
        return None

    # 信号 1: 变更涉及多种文件类型 → 可能是跨模块集成经验
    extensions = {Path(f).suffix for f in diff_files if Path(f).suffix}
    multi_type = len(extensions) >= 3

    # 信号 2: 变更涉及测试文件 → 可能修复了 bug 或发现了新模式
    has_test_changes = any("test" in f.lower() for f in diff_files)

    # 信号 3: 变更涉及配置/CI 文件 → 可能有工具/工作流经验
    config_patterns = (".yml", ".yaml", ".toml", ".cfg", ".ini", ".json")
    has_config_changes = any(Path(f).suffix in config_patterns for f in diff_files)

    # 信号 4: 较大量的变更 → 可能是重要的重构或特性
    large_changeset = len(diff_files) >= 8

    # 信号 5: .vibecollab 目录尚无 Insight → 引导首次沉淀
    insights_dir = project_root / ".vibecollab" / "insights"
    no_insights_yet = not insights_dir.exists() or not list(insights_dir.glob("INS-*.yaml"))

    reasons = []
    if no_insights_yet:
        reasons.append("项目尚无 Insight 沉淀，建议开始积累经验")
    if multi_type and has_test_changes:
        reasons.append("变更涉及多种文件类型+测试，可能有值得记录的调试/集成经验")
    elif has_test_changes:
        reasons.append("变更涉及测试文件，可能发现了 bug 或新测试模式")
    elif multi_type:
        reasons.append("变更涉及多种文件类型，可能有跨模块集成经验")
    if has_config_changes:
        reasons.append("变更涉及配置文件，可能有工具/工作流经验")
    if large_changeset and not reasons:
        reasons.append(f"本次变更涉及 {len(diff_files)} 个文件，建议回顾是否有值得沉淀的经验")

    if not reasons:
        return None

    return "；".join(reasons)


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

    # P1~P2: Task 状态推荐行动
    try:
        from .task_manager import TaskManager
        tm = TaskManager(project_root=project_root)
        all_tasks = tm.list_tasks()

        review_tasks = [t for t in all_tasks if t.status == "REVIEW"]
        if review_tasks:
            for t in review_tasks[:3]:
                priority += 1
                actions.append({
                    "priority": f"P1-{priority}",
                    "type": "task_solidify",
                    "action": f"固化任务 {t.id}: {t.feature}",
                    "reason": f"任务处于 REVIEW 状态，可尝试固化",
                    "suggestion": f"vibecollab task solidify {t.id}",
                })

        # 检查被依赖阻塞的任务
        blocked_tasks = []
        for t in all_tasks:
            if t.status == "DONE":
                continue
            for dep_id in (t.dependencies or []):
                dep = tm.get_task(dep_id)
                if dep and dep.status != "DONE":
                    blocked_tasks.append((t, dep_id))
                    break
        if blocked_tasks:
            for t, dep_id in blocked_tasks[:2]:
                priority += 1
                actions.append({
                    "priority": f"P2-{priority}",
                    "type": "task_blocked",
                    "action": f"任务 {t.id} 被 {dep_id} 阻塞",
                    "reason": f"依赖 {dep_id} 尚未完成",
                    "suggestion": f"vibecollab task show {dep_id}",
                })

        # TODO 积压提示
        todo_count = sum(1 for t in all_tasks if t.status == "TODO")
        if todo_count > 3:
            priority += 1
            actions.append({
                "priority": f"P2-{priority}",
                "type": "task_backlog",
                "action": f"{todo_count} 个待办任务积压",
                "reason": "建议开始处理或拆分任务",
                "suggestion": "vibecollab task list --status TODO",
            })
    except Exception:
        pass

    # P2: Insight 沉淀提示
    insight_prompt = _check_insight_opportunity(project_root, diff_files)
    if insight_prompt:
        priority += 1
        actions.append({
            "priority": f"P2-{priority}",
            "type": "insight_review",
            "action": "检查是否有值得沉淀的经验 (Insight)",
            "reason": insight_prompt,
            "suggestion": 'vibecollab insight add --title "<标题>" --tags "<标签>" --category <类别> --body "<经验描述>"',
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
