"""
Session Store — 对话 summary 持久化存储

将 AI IDE 对话结束时的 summary 持久化到本地，作为 insight suggest 的输入信号之一。

存储结构：
    .vibecollab/
    └── sessions/
        ├── 2026-02-27T14-30-00.json
        ├── 2026-02-27T16-00-00.json
        └── ...

每个 session 文件包含：
- session_id: 自动生成的时间戳 ID
- developer: 开发者名称
- summary: 对话摘要文本
- key_decisions: 关键决策列表
- files_changed: 涉及的文件列表
- created_at: 创建时间
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Session:
    """对话 session 记录"""

    session_id: str = ""
    developer: str = ""
    summary: str = ""
    key_decisions: List[str] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    insights_added: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    _auto_id: bool = field(default=True, repr=False)

    def __post_init__(self):
        if self._auto_id and not self.session_id:
            self.session_id = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H-%M-%S"
            )
        if self._auto_id and not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("_auto_id", None)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data.get("session_id", ""),
            developer=data.get("developer", ""),
            summary=data.get("summary", ""),
            key_decisions=data.get("key_decisions", []),
            files_changed=data.get("files_changed", []),
            insights_added=data.get("insights_added", []),
            tags=data.get("tags", []),
            created_at=data.get("created_at", ""),
            _auto_id=False,  # from_dict 不自动生成
        )


class SessionStore:
    """对话 session 存储管理器

    Usage:
        store = SessionStore(project_root=Path("."))
        session = store.save(Session(
            developer="ocarina",
            summary="实现 MCP Server + AI IDE 集成",
            key_decisions=["DECISION-015: 砍掉自举能力"],
            files_changed=["mcp_server.py", "cli_mcp.py"],
        ))
        recent = store.list_recent(5)
    """

    SESSIONS_DIR = "sessions"

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.sessions_dir = self.project_root / ".vibecollab" / self.SESSIONS_DIR

    def save(self, session: Session) -> Session:
        """保存 session 到文件"""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        path = self.sessions_dir / f"{session.session_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """按 ID 获取 session"""
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception:
            return None

    def list_all(self) -> List[Session]:
        """列出所有 session，按时间倒序"""
        if not self.sessions_dir.exists():
            return []
        sessions = []
        for path in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(Session.from_dict(data))
            except Exception:
                continue
        return sessions

    def list_recent(self, limit: int = 10) -> List[Session]:
        """列出最近 N 个 session"""
        return self.list_all()[:limit]

    def list_since(self, since_timestamp: str) -> List[Session]:
        """列出某时间点之后的 session"""
        all_sessions = self.list_all()
        if not since_timestamp:
            return all_sessions
        return [
            s for s in all_sessions
            if s.created_at >= since_timestamp
        ]

    def delete(self, session_id: str) -> bool:
        """删除 session"""
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return False
        path.unlink()
        return True

    def count(self) -> int:
        """session 总数"""
        if not self.sessions_dir.exists():
            return 0
        return len(list(self.sessions_dir.glob("*.json")))

    def get_summaries_text(self, limit: int = 5) -> str:
        """获取最近 session 的 summary 文本，用于 insight suggest 的输入信号"""
        sessions = self.list_recent(limit)
        if not sessions:
            return ""
        parts = []
        for s in sessions:
            parts.append(f"[{s.created_at[:10]}] {s.summary}")
            if s.key_decisions:
                for d in s.key_decisions:
                    parts.append(f"  - 决策: {d}")
        return "\n".join(parts)
