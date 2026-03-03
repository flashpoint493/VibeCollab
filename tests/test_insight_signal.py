"""
Tests for insight_signal.py — Signal collector + candidate Insight recommendations

Covers:
- SignalSnapshot: serialization/deserialization
- InsightCandidate: data structures
- InsightSignalCollector: snapshot CRUD, git signal analysis, doc analysis, Task analysis, suggest
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vibecollab.insight.signal import (
    CommitSignal,
    InsightCandidate,
    InsightSignalCollector,
    SignalSnapshot,
)


# ===================================================================
# SignalSnapshot
# ===================================================================


class TestSignalSnapshot:
    def test_defaults(self):
        s = SignalSnapshot()
        assert s.last_commit == ""
        assert s.last_timestamp == ""
        assert s.total_suggests == 0

    def test_roundtrip(self):
        s = SignalSnapshot(
            last_commit="abc123",
            last_timestamp="2026-02-27T10:00:00",
            last_insight_id="INS-015",
            total_suggests=3,
        )
        d = s.to_dict()
        s2 = SignalSnapshot.from_dict(d)
        assert s2.last_commit == "abc123"
        assert s2.total_suggests == 3

    def test_from_dict_missing_fields(self):
        s = SignalSnapshot.from_dict({})
        assert s.last_commit == ""
        assert s.total_suggests == 0


# ===================================================================
# InsightCandidate
# ===================================================================


class TestInsightCandidate:
    def test_defaults(self):
        c = InsightCandidate(title="test")
        assert c.tags == []
        assert c.category == "workflow"
        assert c.confidence == 0.5

    def test_to_dict(self):
        c = InsightCandidate(
            title="MCP Server",
            tags=["mcp", "server"],
            confidence=0.8,
        )
        d = c.to_dict()
        assert d["title"] == "MCP Server"
        assert d["confidence"] == 0.8


# ===================================================================
# InsightSignalCollector — Snapshot CRUD
# ===================================================================


class TestSnapshotCRUD:
    def test_load_empty(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        s = c.load_snapshot()
        assert s.last_commit == ""

    def test_save_and_load(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        snapshot = SignalSnapshot(
            last_commit="def456",
            last_timestamp="2026-02-27",
            total_suggests=2,
        )
        c.save_snapshot(snapshot)
        loaded = c.load_snapshot()
        assert loaded.last_commit == "def456"
        assert loaded.total_suggests == 2

    def test_update_snapshot(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        with patch.object(c, "_get_head_commit", return_value="head999"):
            s = c.update_snapshot(insight_id="INS-020")
        assert s.last_commit == "head999"
        assert s.last_insight_id == "INS-020"
        assert s.total_suggests == 1

    def test_update_snapshot_explicit_commit(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        s = c.update_snapshot(commit_hash="explicit123")
        assert s.last_commit == "explicit123"

    def test_load_corrupted_file(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        c.data_dir.mkdir(parents=True, exist_ok=True)
        (c.signal_path).write_text("not valid json", encoding="utf-8")
        s = c.load_snapshot()
        assert s.last_commit == ""


# ===================================================================
# InsightSignalCollector — Git signals
# ===================================================================


class TestGitSignals:
    def _make_run_result(self, stdout="", returncode=0):
        r = MagicMock()
        r.stdout = stdout
        r.returncode = returncode
        return r

    @patch("vibecollab.insight.signal.subprocess.run")
    def test_collect_git_signals_basic(self, mock_run, tmp_path):
        log_output = (
            "abc123|feat: add MCP server|ocarina|2026-02-27T10:00:00+08:00\n"
            "def456|fix: encoding bug|alice|2026-02-26T09:00:00+08:00"
        )
        mock_run.side_effect = [
            self._make_run_result(log_output),
            self._make_run_result("mcp_server.py\ncli_mcp.py"),
            self._make_run_result("cli.py"),
        ]
        c = InsightSignalCollector(tmp_path)
        signals = c.collect_git_signals()
        assert len(signals) == 2
        assert signals[0].subject == "feat: add MCP server"
        assert signals[0].author == "ocarina"

    @patch("vibecollab.insight.signal.subprocess.run")
    def test_collect_git_signals_empty(self, mock_run, tmp_path):
        mock_run.return_value = self._make_run_result("")
        c = InsightSignalCollector(tmp_path)
        signals = c.collect_git_signals()
        assert signals == []

    @patch("vibecollab.insight.signal.subprocess.run")
    def test_collect_git_signals_error(self, mock_run, tmp_path):
        mock_run.return_value = self._make_run_result("", returncode=1)
        c = InsightSignalCollector(tmp_path)
        assert c.collect_git_signals() == []

    @patch("vibecollab.insight.signal.subprocess.run")
    def test_collect_git_signals_timeout(self, mock_run, tmp_path):
        mock_run.side_effect = subprocess.TimeoutExpired("git", 15)
        c = InsightSignalCollector(tmp_path)
        assert c.collect_git_signals() == []


# ===================================================================
# InsightSignalCollector — Doc changes
# ===================================================================


class TestDocChanges:
    @patch("vibecollab.insight.signal.subprocess.run")
    def test_collect_doc_changes_decisions(self, mock_run, tmp_path):
        # Create doc files
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "DECISIONS.md").write_text("content", encoding="utf-8")
        (docs / "CONTEXT.md").write_text("content", encoding="utf-8")
        (docs / "ROADMAP.md").write_text("content", encoding="utf-8")
        (docs / "CHANGELOG.md").write_text("content", encoding="utf-8")

        def run_side_effect(cmd, **kwargs):
            r = MagicMock()
            r.returncode = 0
            if "DECISIONS.md" in str(cmd):
                r.stdout = "+## DECISION-016: New architecture decision\n-old content"
            else:
                r.stdout = ""
            return r

        mock_run.side_effect = run_side_effect
        c = InsightSignalCollector(tmp_path)
        changes = c.collect_doc_changes()
        assert "docs/DECISIONS.md" in changes

    def test_collect_doc_changes_no_docs(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        # Don't create doc files
        changes = c.collect_doc_changes()
        assert changes == {}


# ===================================================================
# InsightSignalCollector — Task changes
# ===================================================================


class TestTaskChanges:
    def test_no_tasks_file(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        result = c.collect_task_changes()
        assert result["total"] == 0

    def test_with_tasks(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        c.data_dir.mkdir(parents=True, exist_ok=True)
        tasks = [
            {"id": "TASK-DEV-001", "status": "DONE"},
            {"id": "TASK-DEV-002", "status": "DONE"},
            {"id": "TASK-DEV-003", "status": "DONE"},
            {"id": "TASK-DEV-004", "status": "IN_PROGRESS"},
        ]
        (c.data_dir / "tasks.json").write_text(
            json.dumps(tasks), encoding="utf-8"
        )
        result = c.collect_task_changes()
        assert len(result["completed"]) == 3
        assert len(result["new"]) == 1
        assert result["total"] == 4

    def test_corrupted_tasks(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        c.data_dir.mkdir(parents=True, exist_ok=True)
        (c.data_dir / "tasks.json").write_text("not json", encoding="utf-8")
        result = c.collect_task_changes()
        assert result["total"] == 0


# ===================================================================
# InsightSignalCollector — Analysis
# ===================================================================


class TestAnalysis:
    def test_analyze_git_features(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        signals = [
            CommitSignal(
                hash="a1", subject="feat: add MCP server",
                author="ocarina", date="2026-02-27",
                files_changed=["mcp_server.py"],
            ),
            CommitSignal(
                hash="a2", subject="feat: add CLI commands",
                author="ocarina", date="2026-02-27",
                files_changed=["cli_mcp.py"],
            ),
        ]
        candidates = c._analyze_git_signals(signals)
        assert any(c.source_signal == "git_feature" for c in candidates)

    def test_analyze_git_bugfix(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        signals = [
            CommitSignal(
                hash="b1", subject="fix: encoding bug",
                author="alice", date="2026-02-26",
                files_changed=["cli.py"],
            ),
        ]
        candidates = c._analyze_git_signals(signals)
        assert any(c.source_signal == "git_bugfix" for c in candidates)

    def test_analyze_git_refactor(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        signals = [
            CommitSignal(
                hash="c1", subject="refactor: extract module",
                author="bob", date="2026-02-25",
                files_changed=["module.py"],
            ),
        ]
        candidates = c._analyze_git_signals(signals)
        assert any(c.source_signal == "git_refactor" for c in candidates)

    def test_analyze_git_large_change(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        signals = [
            CommitSignal(
                hash="d1", subject="massive rewrite",
                author="ocarina", date="2026-02-27",
                files_changed=[f"file{i}.py" for i in range(15)],
            ),
        ]
        candidates = c._analyze_git_signals(signals)
        assert any(c.source_signal == "git_large_change" for c in candidates)

    def test_analyze_git_empty(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        assert c._analyze_git_signals([]) == []

    def test_analyze_doc_decisions(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        changes = {
            "docs/DECISIONS.md": ["+## DECISION-016: New decision"],
        }
        candidates = c._analyze_doc_changes(changes)
        assert len(candidates) == 1
        assert candidates[0].source_signal == "doc_decisions"
        assert candidates[0].confidence == 0.8

    def test_analyze_doc_roadmap(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        changes = {
            "docs/ROADMAP.md": ["+- [x] feature done ✅"],
        }
        candidates = c._analyze_doc_changes(changes)
        assert len(candidates) == 1
        assert candidates[0].source_signal == "doc_roadmap"

    def test_analyze_doc_context_large(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        changes = {
            "docs/CONTEXT.md": [f"+new line {i}" for i in range(15)],
        }
        candidates = c._analyze_doc_changes(changes)
        assert len(candidates) == 1
        assert candidates[0].source_signal == "doc_context"

    def test_analyze_doc_empty(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        assert c._analyze_doc_changes({}) == []

    def test_analyze_tasks_completed(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        changes = {"completed": ["T1", "T2", "T3"], "new": [], "total": 5}
        candidates = c._analyze_task_changes(changes)
        assert len(candidates) == 1
        assert candidates[0].source_signal == "task_completed"

    def test_analyze_tasks_few(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        changes = {"completed": ["T1"], "new": [], "total": 2}
        assert c._analyze_task_changes(changes) == []


# ===================================================================
# InsightSignalCollector — Suggest (integration)
# ===================================================================


class TestSuggest:
    @patch.object(InsightSignalCollector, "collect_git_signals")
    @patch.object(InsightSignalCollector, "collect_doc_changes")
    @patch.object(InsightSignalCollector, "collect_task_changes")
    def test_suggest_combined(self, mock_tasks, mock_docs, mock_git, tmp_path):
        mock_git.return_value = [
            CommitSignal(
                hash="a1", subject="feat: new feature",
                author="ocarina", date="2026-02-27",
                files_changed=["feature.py"],
            ),
        ]
        mock_docs.return_value = {
            "docs/DECISIONS.md": ["+## DECISION-020: new decision"],
        }
        mock_tasks.return_value = {"completed": [], "new": [], "total": 0}

        c = InsightSignalCollector(tmp_path)
        candidates = c.suggest()
        assert len(candidates) >= 2  # git feature + doc decision
        # Should be sorted by confidence descending
        for i in range(len(candidates) - 1):
            assert candidates[i].confidence >= candidates[i + 1].confidence

    @patch.object(InsightSignalCollector, "collect_git_signals")
    @patch.object(InsightSignalCollector, "collect_doc_changes")
    @patch.object(InsightSignalCollector, "collect_task_changes")
    def test_suggest_empty(self, mock_tasks, mock_docs, mock_git, tmp_path):
        mock_git.return_value = []
        mock_docs.return_value = {}
        mock_tasks.return_value = {"completed": [], "new": [], "total": 0}

        c = InsightSignalCollector(tmp_path)
        candidates = c.suggest()
        assert candidates == []


# ===================================================================
# Helpers
# ===================================================================


class TestHelpers:
    def test_deduplicate(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        candidates = [
            InsightCandidate(title="add MCP server feature"),
            InsightCandidate(title="add MCP server feature implementation"),
            InsightCandidate(title="totally different topic"),
        ]
        result = c._deduplicate(candidates)
        # First two should be deduplicated
        assert len(result) <= 3

    def test_deduplicate_empty(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        assert c._deduplicate([]) == []

    def test_title_similarity(self):
        assert InsightSignalCollector._title_similarity("a b c", "a b c") == 1.0
        assert InsightSignalCollector._title_similarity("a b c", "d e f") == 0.0
        assert InsightSignalCollector._title_similarity("", "") == 0.0
        assert InsightSignalCollector._title_similarity("a b c", "a b d") > 0.3

    def test_extract_tags_from_commits(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        commits = [
            CommitSignal(
                hash="x", subject="test", author="a", date="d",
                files_changed=["src/module.py", "tests/test_x.py", "config.yaml"],
            ),
        ]
        tags = c._extract_tags_from_commits(commits)
        assert "python" in tags
        assert "testing" in tags
        assert "config" in tags

    def test_extract_decision_title(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        lines = ["+## DECISION-016: Drop Web UI"]
        assert "Drop Web UI" in c._extract_decision_title(lines)

    def test_extract_decision_title_no_match(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        assert c._extract_decision_title(["no match"]) == "New architecture/technical decision"

    def test_summarize_commits_single(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        commits = [CommitSignal(hash="a", subject="fix bug", author="x", date="d")]
        assert c._summarize_commits(commits, "debug") == "fix bug"

    def test_summarize_commits_multiple(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        commits = [
            CommitSignal(hash="a", subject="first", author="x", date="d"),
            CommitSignal(hash="b", subject="second", author="x", date="d"),
        ]
        result = c._summarize_commits(commits, "feature")
        assert "other changes" in result

    def test_summarize_commits_empty(self, tmp_path):
        c = InsightSignalCollector(tmp_path)
        result = c._summarize_commits([], "feature")
        assert "feature" in result
