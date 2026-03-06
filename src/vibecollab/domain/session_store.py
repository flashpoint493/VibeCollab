"""
Session Store -- Conversation summary persistent storage

Persists AI IDE conversation summaries locally as one of the input signals for insight suggest.

Storage structure:
    .vibecollab/
    +-- sessions/
        |-- 2026-02-27T14-30-00.json
        |-- 2026-02-27T16-00-00.json
        +-- ...

Each session file contains:
- session_id: Auto-generated timestamp ID
- developer: Developer name
- summary: Conversation summary text
- key_decisions: List of key decisions
- files_changed: List of files involved
- created_at: Creation time
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Session:
    """Conversation session record"""

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
            _auto_id=False,  # from_dict does not auto-generate
        )


class SessionStore:
    """Conversation session storage manager

    Usage:
        store = SessionStore(project_root=Path("."))
        session = store.save(Session(
            developer="dev",
            summary="Implemented MCP Server + AI IDE integration",
            key_decisions=["DECISION-015: Removed self-bootstrap capability"],
            files_changed=["mcp_server.py", "cli_mcp.py"],
        ))
        recent = store.list_recent(5)
    """

    SESSIONS_DIR = "sessions"

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.sessions_dir = self.project_root / ".vibecollab" / self.SESSIONS_DIR

    def save(self, session: Session) -> Session:
        """Save session to file"""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        path = self.sessions_dir / f"{session.session_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
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
        """List all sessions, sorted by time descending"""
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
        """List most recent N sessions"""
        return self.list_all()[:limit]

    def list_since(self, since_timestamp: str) -> List[Session]:
        """List sessions after a given timestamp"""
        all_sessions = self.list_all()
        if not since_timestamp:
            return all_sessions
        return [
            s for s in all_sessions
            if s.created_at >= since_timestamp
        ]

    def delete(self, session_id: str) -> bool:
        """Delete session"""
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return False
        path.unlink()
        return True

    def count(self) -> int:
        """Total session count"""
        if not self.sessions_dir.exists():
            return 0
        return len(list(self.sessions_dir.glob("*.json")))

    def get_summaries_text(self, limit: int = 5) -> str:
        """Get recent session summary text as input signal for insight suggest"""
        sessions = self.list_recent(limit)
        if not sessions:
            return ""
        parts = []
        for s in sessions:
            parts.append(f"[{s.created_at[:10]}] {s.summary}")
            if s.key_decisions:
                for d in s.key_decisions:
                    parts.append(f"  - Decision: {d}")
        return "\n".join(parts)
