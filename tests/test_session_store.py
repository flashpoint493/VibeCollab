"""
Tests for session_store.py — session persistence

Covers:
- Session: data structure, auto fields, serialization
- SessionStore: save, get, list_all, list_recent, list_since, delete, count, get_summaries_text
"""



from vibecollab.domain.session_store import Session, SessionStore

# ===================================================================
# Session dataclass
# ===================================================================


class TestSession:
    def test_defaults(self):
        s = Session()
        assert s.session_id != ""  # auto-generated
        assert s.created_at != ""  # auto-generated
        assert s.summary == ""
        assert s.key_decisions == []

    def test_explicit_fields(self):
        s = Session(
            session_id="test-001",
            role="ocarina",
            summary="MCP Server implementation",
            key_decisions=["DECISION-015"],
            files_changed=["mcp_server.py"],
            created_at="2026-02-27T10:00:00",
        )
        assert s.session_id == "test-001"
        assert s.role == "ocarina"
        assert len(s.key_decisions) == 1

    def test_roundtrip(self):
        s = Session(
            session_id="test-002",
            role="alice",
            summary="Test session",
            tags=["test", "demo"],
        )
        d = s.to_dict()
        s2 = Session.from_dict(d)
        assert s2.session_id == "test-002"
        assert s2.role == "alice"
        assert s2.tags == ["test", "demo"]

    def test_from_dict_missing_fields(self):
        s = Session.from_dict({})
        assert s.session_id == ""
        assert s.summary == ""


# ===================================================================
# SessionStore — CRUD
# ===================================================================


class TestSessionStore:
    def test_save_and_get(self, tmp_path):
        store = SessionStore(tmp_path)
        session = Session(
            session_id="s-001",
            role="ocarina",
            summary="Test session",
        )
        store.save(session)
        loaded = store.get("s-001")
        assert loaded is not None
        assert loaded.role == "ocarina"
        assert loaded.summary == "Test session"

    def test_get_nonexistent(self, tmp_path):
        store = SessionStore(tmp_path)
        assert store.get("nonexistent") is None

    def test_list_all_empty(self, tmp_path):
        store = SessionStore(tmp_path)
        assert store.list_all() == []

    def test_list_all_ordered(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save(Session(session_id="a-001", summary="first"))
        store.save(Session(session_id="b-002", summary="second"))
        store.save(Session(session_id="c-003", summary="third"))
        all_sessions = store.list_all()
        assert len(all_sessions) == 3
        # Reverse order (c > b > a)
        assert all_sessions[0].session_id == "c-003"

    def test_list_recent(self, tmp_path):
        store = SessionStore(tmp_path)
        for i in range(5):
            store.save(Session(session_id=f"s-{i:03d}", summary=f"session {i}"))
        recent = store.list_recent(3)
        assert len(recent) == 3

    def test_list_since(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save(Session(
            session_id="old",
            summary="old session",
            created_at="2026-02-25T00:00:00",
        ))
        store.save(Session(
            session_id="new",
            summary="new session",
            created_at="2026-02-27T10:00:00",
        ))
        result = store.list_since("2026-02-26T00:00:00")
        assert len(result) == 1
        assert result[0].session_id == "new"

    def test_list_since_empty_timestamp(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save(Session(session_id="s1", summary="test"))
        assert len(store.list_since("")) == 1

    def test_delete(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save(Session(session_id="to-delete", summary="bye"))
        assert store.delete("to-delete") is True
        assert store.get("to-delete") is None

    def test_delete_nonexistent(self, tmp_path):
        store = SessionStore(tmp_path)
        assert store.delete("nope") is False

    def test_count(self, tmp_path):
        store = SessionStore(tmp_path)
        assert store.count() == 0
        store.save(Session(session_id="s1"))
        store.save(Session(session_id="s2"))
        assert store.count() == 2

    def test_count_no_dir(self, tmp_path):
        store = SessionStore(tmp_path)
        assert store.count() == 0

    def test_get_summaries_text(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save(Session(
            session_id="s1",
            summary="Implemented MCP Server",
            key_decisions=["DECISION-015"],
            created_at="2026-02-27T10:00:00",
        ))
        store.save(Session(
            session_id="s2",
            summary="Added tests",
            created_at="2026-02-27T12:00:00",
        ))
        text = store.get_summaries_text()
        assert "Implemented MCP Server" in text
        assert "Added tests" in text
        assert "DECISION-015" in text

    def test_get_summaries_text_empty(self, tmp_path):
        store = SessionStore(tmp_path)
        assert store.get_summaries_text() == ""

    def test_corrupted_session_file(self, tmp_path):
        store = SessionStore(tmp_path)
        store.sessions_dir.mkdir(parents=True, exist_ok=True)
        (store.sessions_dir / "bad.json").write_text("not json", encoding="utf-8")
        # list_all should skip corrupted
        sessions = store.list_all()
        assert sessions == []

    def test_get_corrupted(self, tmp_path):
        store = SessionStore(tmp_path)
        store.sessions_dir.mkdir(parents=True, exist_ok=True)
        (store.sessions_dir / "bad.json").write_text("{}", encoding="utf-8")
        s = store.get("bad")
        # from_dict with empty dict gives empty session
        assert s is not None
        assert s.session_id == ""
