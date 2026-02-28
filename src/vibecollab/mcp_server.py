"""
VibeCollab MCP Server — Model Context Protocol 集成

让 VibeCollab 成为 Cline/Cursor/CodeBuddy 等 AI IDE 的"协议后端"，
从"手动复制粘贴"变成"IDE 自动读取协议"。

功能:
    - Tools: insight_search, insight_add, check, onboard, next, task_list
    - Resources: CONTRIBUTING_AI.md, CONTEXT.md, DECISIONS.md, ROADMAP.md, Insight YAML
    - Prompts: 对话开始时的上下文注入模板

依赖:
    pip install vibe-collab[mcp]

使用:
    vibecollab mcp serve                # stdio 模式 (推荐，IDE 直连)
    vibecollab mcp serve --transport sse # SSE 模式 (远程调试)
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _find_project_root(start: Optional[Path] = None) -> Path:
    """向上查找包含 project.yaml 的目录"""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "project.yaml").exists():
            return parent
    return current


def _safe_read_text(path: Path, encoding: str = "utf-8") -> str:
    """安全读取文件文本，文件不存在返回空字符串"""
    try:
        return path.read_text(encoding=encoding)
    except (OSError, UnicodeDecodeError):
        return ""


def _safe_load_yaml(path: Path) -> Dict:
    """安全加载 YAML 文件"""
    try:
        import yaml

        text = path.read_text(encoding="utf-8")
        return yaml.safe_load(text) or {}
    except Exception:
        return {}


def _get_insight_files(project_root: Path) -> List[Path]:
    """获取所有 Insight 文件，按 ID 倒序"""
    insights_dir = project_root / ".vibecollab" / "insights"
    if not insights_dir.exists():
        return []
    return sorted(insights_dir.glob("INS-*.yaml"), reverse=True)


def create_mcp_server(project_root: Optional[Path] = None):
    """创建并配置 MCP Server 实例

    Args:
        project_root: 项目根目录，为 None 时自动查找

    Returns:
        FastMCP 实例
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "MCP Server 需要 mcp 依赖。请安装: pip install vibe-collab[mcp]"
        )

    root = project_root or _find_project_root()
    config_path = root / "project.yaml"

    mcp = FastMCP(
        "vibecollab",
        instructions=(
            "VibeCollab 协议管理工具。提供项目协议文档读取、Insight 经验搜索与沉淀、"
            "协议遵循检查、开发引导等功能。对话开始时请先读取 contributing_ai 和 context 资源。"
        ),
    )

    # ================================================================
    # Resources — 协议文档暴露
    # ================================================================

    @mcp.resource("vibecollab://docs/contributing_ai")
    def get_contributing_ai() -> str:
        """项目 AI 协作协议 (CONTRIBUTING_AI.md) — 对话开始时必读"""
        return _safe_read_text(root / "CONTRIBUTING_AI.md")

    @mcp.resource("vibecollab://docs/context")
    def get_context() -> str:
        """项目当前状态 (docs/CONTEXT.md) — 对话开始时必读"""
        return _safe_read_text(root / "docs" / "CONTEXT.md")

    @mcp.resource("vibecollab://docs/decisions")
    def get_decisions() -> str:
        """决策记录 (docs/DECISIONS.md)"""
        return _safe_read_text(root / "docs" / "DECISIONS.md")

    @mcp.resource("vibecollab://docs/roadmap")
    def get_roadmap() -> str:
        """项目路线图 (docs/ROADMAP.md)"""
        return _safe_read_text(root / "docs" / "ROADMAP.md")

    @mcp.resource("vibecollab://docs/changelog")
    def get_changelog() -> str:
        """变更日志 (docs/CHANGELOG.md)"""
        return _safe_read_text(root / "docs" / "CHANGELOG.md")

    @mcp.resource("vibecollab://insights/list")
    def get_insights_list() -> str:
        """所有 Insight 沉淀条目列表 (ID + 标题 + 标签)"""
        files = _get_insight_files(root)
        if not files:
            return json.dumps({"insights": [], "count": 0}, ensure_ascii=False)

        insights = []
        for f in files:
            data = _safe_load_yaml(f)
            if data:
                insights.append({
                    "id": data.get("id", f.stem),
                    "title": data.get("title", ""),
                    "tags": data.get("tags", []),
                    "category": data.get("category", ""),
                })
        return json.dumps({"insights": insights, "count": len(insights)}, ensure_ascii=False)

    # ================================================================
    # Tools — 功能暴露
    # ================================================================

    @mcp.tool()
    def insight_search(query: str, tags: str = "", semantic: bool = False) -> str:
        """搜索 Insight 经验沉淀

        Args:
            query: 搜索关键词或自然语言描述
            tags: 标签过滤，逗号分隔 (如 "架构,MCP")
            semantic: 是否使用语义搜索 (需要已建立向量索引)
        """
        cmd = ["vibecollab", "insight", "search"]
        if tags:
            cmd.extend(["--tags", tags])
        if semantic:
            cmd.append("--semantic")
        cmd.append(query)

        result = _run_cli(cmd, root)
        return result

    @mcp.tool()
    def insight_add(
        title: str,
        tags: str,
        category: str,
        scenario: str,
        approach: str,
        summary: str = "",
        context: str = "",
    ) -> str:
        """沉淀新的 Insight 经验

        Args:
            title: 沉淀标题
            tags: 标签，逗号分隔
            category: 分类 (technique/workflow/decision/debug/tool/integration)
            scenario: 适用场景描述
            approach: 方法/步骤描述
            summary: 一句话摘要 (可选)
            context: 创建背景 (可选)
        """
        cmd = [
            "vibecollab", "insight", "add",
            "-t", title,
            "--tags", tags,
            "-c", category,
            "-s", scenario,
            "-a", approach,
        ]
        if summary:
            cmd.extend(["--summary", summary])
        if context:
            cmd.extend(["--context", context])

        return _run_cli(cmd, root)

    @mcp.tool()
    def check(strict: bool = False) -> str:
        """检查协议遵循情况

        Args:
            strict: 是否严格模式 (警告也视为失败)
        """
        cmd = ["vibecollab", "check"]
        if strict:
            cmd.append("--strict")
        return _run_cli(cmd, root)

    @mcp.tool()
    def onboard(developer: str = "", output_json: bool = True) -> str:
        """获取项目上下文引导信息 — 对话开始时调用

        Args:
            developer: 指定开发者 ID (可选)
            output_json: 是否输出 JSON 格式 (默认 True)
        """
        cmd = ["vibecollab", "onboard"]
        if developer:
            cmd.extend(["-d", developer])
        if output_json:
            cmd.append("--json")
        return _run_cli(cmd, root)

    @mcp.tool()
    def next_step() -> str:
        """获取下一步行动建议"""
        return _run_cli(["vibecollab", "next"], root)

    @mcp.tool()
    def task_list() -> str:
        """列出当前任务"""
        return _run_cli(["vibecollab", "task", "list"], root)

    @mcp.tool()
    def task_create(
        task_id: str,
        role: str,
        feature: str,
        assignee: str = "",
        description: str = "",
    ) -> str:
        """创建新任务（自动关联 Insight）

        Args:
            task_id: 任务 ID，格式 TASK-{ROLE}-{SEQ} (如 TASK-DEV-001)
            role: 角色代码 (DEV/PM/ARCH/...)
            feature: 功能描述
            assignee: 负责人 (可选)
            description: 详细描述 (可选)
        """
        cmd = [
            "vibecollab", "task", "create",
            "--id", task_id,
            "--role", role,
            "--feature", feature,
        ]
        if assignee:
            cmd.extend(["--assignee", assignee])
        if description:
            cmd.extend(["--description", description])
        cmd.append("--json")
        return _run_cli(cmd, root)

    @mcp.tool()
    def task_transition(
        task_id: str,
        new_status: str,
        reason: str = "",
    ) -> str:
        """推进任务状态

        合法转换: TODO→IN_PROGRESS, IN_PROGRESS→REVIEW/TODO, REVIEW→DONE/IN_PROGRESS

        Args:
            task_id: 任务 ID
            new_status: 目标状态 (TODO/IN_PROGRESS/REVIEW/DONE)
            reason: 变更原因 (可选)
        """
        cmd = [
            "vibecollab", "task", "transition",
            task_id, new_status.upper(),
            "--json",
        ]
        if reason:
            cmd.extend(["--reason", reason])
        return _run_cli(cmd, root)

    @mcp.tool()
    def project_prompt(developer: str = "", compact: bool = True) -> str:
        """生成完整的项目上下文 prompt 文本

        Args:
            developer: 指定开发者 ID (可选)
            compact: 是否精简模式 (默认 True)
        """
        cmd = ["vibecollab", "prompt"]
        if developer:
            cmd.extend(["-d", developer])
        if compact:
            cmd.append("--compact")
        return _run_cli(cmd, root)

    @mcp.tool()
    def developer_context(developer: str) -> str:
        """获取指定开发者的上下文信息

        Args:
            developer: 开发者 ID
        """
        dev_dir = root / "docs" / "developers" / developer
        if not dev_dir.exists():
            return json.dumps(
                {"error": f"开发者 '{developer}' 不存在"},
                ensure_ascii=False,
            )

        context_text = _safe_read_text(dev_dir / "CONTEXT.md")
        metadata = _safe_load_yaml(dev_dir / ".metadata.yaml")

        return json.dumps(
            {
                "developer": developer,
                "context": context_text,
                "metadata": metadata,
            },
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    def search_docs(query: str, doc_type: str = "", min_score: float = 0.0) -> str:
        """语义搜索项目文档和 Insight

        Args:
            query: 搜索内容 (自然语言)
            doc_type: 过滤来源类型 (insight/document，留空搜全部)
            min_score: 最低相关度阈值 (0.0-1.0)
        """
        cmd = ["vibecollab", "search", query]
        if doc_type:
            cmd.extend(["--type", doc_type])
        if min_score > 0:
            cmd.extend(["--min-score", str(min_score)])
        return _run_cli(cmd, root)

    @mcp.tool()
    def insight_suggest(output_json: bool = True) -> str:
        """基于结构化信号推荐候选 Insight — 从 git 增量/文档变更/Task 变化中提取

        Args:
            output_json: 是否输出 JSON 格式 (默认 True)
        """
        cmd = ["vibecollab", "insight", "suggest"]
        if output_json:
            cmd.append("--json")
        return _run_cli(cmd, root)

    @mcp.tool()
    def session_save(
        summary: str,
        developer: str = "",
        key_decisions: str = "",
        files_changed: str = "",
        insights_added: str = "",
        tags: str = "",
    ) -> str:
        """保存对话 session summary — 对话结束时调用

        Args:
            summary: 对话摘要文本 (必填)
            developer: 开发者 ID (可选)
            key_decisions: 关键决策，逗号分隔 (可选)
            files_changed: 涉及的文件，逗号分隔 (可选)
            insights_added: 新增的 Insight ID，逗号分隔 (可选)
            tags: 标签，逗号分隔 (可选)
        """
        try:
            from .session_store import Session, SessionStore

            store = SessionStore(root)
            session = Session(
                developer=developer,
                summary=summary,
                key_decisions=[
                    d.strip() for d in key_decisions.split(",") if d.strip()
                ] if key_decisions else [],
                files_changed=[
                    f.strip() for f in files_changed.split(",") if f.strip()
                ] if files_changed else [],
                insights_added=[
                    i.strip() for i in insights_added.split(",") if i.strip()
                ] if insights_added else [],
                tags=[
                    t.strip() for t in tags.split(",") if t.strip()
                ] if tags else [],
            )
            store.save(session)
            return json.dumps(
                {"status": "ok", "session_id": session.session_id,
                 "message": f"Session saved: {session.session_id}"},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"status": "error", "message": str(e)},
                ensure_ascii=False,
            )

    @mcp.tool()
    def insight_graph(output_format: str = "json") -> str:
        """获取 Insight 关联图谱

        Args:
            output_format: 输出格式 (json/mermaid)
        """
        fmt_flag = "json" if output_format == "json" else output_format
        cmd = ["vibecollab", "insight", "graph", "--format", fmt_flag]
        return _run_cli(cmd, root)

    @mcp.tool()
    def insight_export(ids: str = "", include_registry: bool = False) -> str:
        """导出 Insight 为 YAML 格式

        Args:
            ids: 要导出的 ID 列表，逗号分隔 (默认全部)
            include_registry: 是否包含注册表状态
        """
        cmd = ["vibecollab", "insight", "export"]
        if ids:
            cmd.extend(["--ids", ids])
        if include_registry:
            cmd.append("--include-registry")
        return _run_cli(cmd, root)

    @mcp.tool()
    def roadmap_status(output_json: bool = True) -> str:
        """获取 ROADMAP 各里程碑进度概览

        Args:
            output_json: 是否输出 JSON 格式 (默认 True)
        """
        cmd = ["vibecollab", "roadmap", "status"]
        if output_json:
            cmd.append("--json")
        return _run_cli(cmd, root)

    @mcp.tool()
    def roadmap_sync(direction: str = "both", dry_run: bool = False) -> str:
        """同步 ROADMAP.md ↔ tasks.json

        Args:
            direction: 同步方向 (both/roadmap_to_tasks/tasks_to_roadmap)
            dry_run: 是否仅预览 (默认 False)
        """
        cmd = ["vibecollab", "roadmap", "sync", "-d", direction, "--json"]
        if dry_run:
            cmd.append("--dry-run")
        return _run_cli(cmd, root)

    # ================================================================
    # Prompts — 对话模板
    # ================================================================

    @mcp.prompt()
    def start_conversation(developer: str = "") -> str:
        """对话开始时的上下文注入模板 — IDE 自动调用"""
        parts = [
            "# VibeCollab 协议上下文",
            "",
            "你正在参与一个使用 VibeCollab 协议管理的项目。请遵循以下规则：",
            "",
            "## 协议要求",
            "1. 对话开始：先读取 CONTRIBUTING_AI.md 和 CONTEXT.md 了解协作规则和项目状态",
            "2. 对话进行：遵循决策分级制度，重要决策需记录到 DECISIONS.md",
            "3. 对话结束：更新 CONTEXT.md + CHANGELOG.md，检查是否有值得沉淀的 Insight，执行 git commit",
            "",
            "## 可用工具",
            "- `insight_search`: 搜索已有经验沉淀",
            "- `insight_add`: 沉淀新经验",
            "- `insight_suggest`: 基于结构化信号推荐候选 Insight",
            "- `check`: 检查协议遵循情况",
            "- `onboard`: 获取完整项目上下文",
            "- `next_step`: 获取下一步建议",
            "- `search_docs`: 语义搜索项目文档",
            "- `task_list`: 列出当前任务",
            "- `task_create`: 创建新任务",
            "- `task_transition`: 推进任务状态",
            "- `insight_graph`: 查看 Insight 关联图谱",
            "- `insight_export`: 导出 Insight",
            "- `roadmap_status`: 查看 ROADMAP 各里程碑进度",
            "- `roadmap_sync`: 同步 ROADMAP ↔ tasks.json",
            "- `session_save`: 保存对话 session (对话结束时调用)",
            "",
        ]

        # 注入项目基本信息
        config = _safe_load_yaml(root / "project.yaml")
        proj = config.get("project", {})
        if proj:
            parts.extend([
                f"## 当前项目: {proj.get('name', 'Unknown')} {proj.get('version', '')}",
                f"描述: {proj.get('description', '')}",
                "",
            ])

        # 注入当前状态摘要
        context_text = _safe_read_text(root / "docs" / "CONTEXT.md")
        if context_text:
            lines = context_text.strip().split("\n")[:20]
            parts.extend([
                "## 当前项目状态 (CONTEXT.md 摘要)",
                *lines,
                "",
            ])

        # 开发者上下文
        if developer:
            dev_context = _safe_read_text(
                root / "docs" / "developers" / developer / "CONTEXT.md"
            )
            if dev_context:
                dev_lines = dev_context.strip().split("\n")[:15]
                parts.extend([
                    f"## 开发者 {developer} 的上下文",
                    *dev_lines,
                    "",
                ])

        return "\n".join(parts)

    return mcp


def _run_cli(cmd: List[str], cwd: Path) -> str:
    """运行 vibecollab CLI 命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        output = result.stdout
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return output
    except subprocess.TimeoutExpired:
        return "[错误] 命令执行超时 (30s)"
    except FileNotFoundError:
        return "[错误] vibecollab 命令未找到，请确认已安装: pip install vibe-collab"
    except Exception as e:
        return f"[错误] {e}"


def run_server(
    project_root: Optional[Path] = None,
    transport: str = "stdio",
):
    """启动 MCP Server

    Args:
        project_root: 项目根目录
        transport: 传输模式 ("stdio" 或 "sse")
    """
    server = create_mcp_server(project_root)
    server.run(transport=transport)
