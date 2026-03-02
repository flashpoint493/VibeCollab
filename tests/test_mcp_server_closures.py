"""
Tests for mcp_server.py internal closures (resources, tools, prompts)

The existing test_mcp_server.py only covers helper functions and cli_mcp commands.
This file covers the closures registered inside create_mcp_server() which account
for the bulk of uncovered lines (98-508).

Strategy: mock ``mcp.server.fastmcp.FastMCP`` so that create_mcp_server() can run
without the real mcp package, and capture all registered resource/tool/prompt functions.
"""

import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
import yaml


# ============================================================
# Capture helpers
# ============================================================


class _CaptureMCP:
    """A mock FastMCP that captures registered resources/tools/prompts."""

    def __init__(self, *a, **kw):
        self.resources = {}
        self.tools = {}
        self.prompts = {}

    def resource(self, uri):
        def decorator(fn):
            self.resources[uri] = fn
            return fn
        return decorator

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator

    def prompt(self):
        def decorator(fn):
            self.prompts[fn.__name__] = fn
            return fn
        return decorator


def _build_server(project_root: Path) -> _CaptureMCP:
    """Build a capture-MCP server with all closures registered."""
    capture = _CaptureMCP()

    # Create a fake mcp.server.fastmcp module with our capture class
    fake_fastmcp = ModuleType("mcp.server.fastmcp")
    fake_fastmcp.FastMCP = lambda *a, **kw: capture

    fake_server = ModuleType("mcp.server")
    fake_server.fastmcp = fake_fastmcp

    fake_mcp = ModuleType("mcp")
    fake_mcp.server = fake_server

    saved = {}
    for key in ("mcp", "mcp.server", "mcp.server.fastmcp"):
        saved[key] = sys.modules.get(key)

    try:
        sys.modules["mcp"] = fake_mcp
        sys.modules["mcp.server"] = fake_server
        sys.modules["mcp.server.fastmcp"] = fake_fastmcp

        # Re-import to pick up our fake module
        import importlib
        import vibecollab.agent.mcp_server as mod
        importlib.reload(mod)

        mod.create_mcp_server(project_root)
    finally:
        # Restore original modules
        for key, val in saved.items():
            if val is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = val
        # Reload to restore original state
        import importlib
        import vibecollab.agent.mcp_server as mod2
        importlib.reload(mod2)

    return capture


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def project_dir(tmp_path):
    """Full test project directory."""
    config = {
        "project": {
            "name": "TestProject",
            "version": "1.0.0",
            "description": "A test project",
        },
        "documentation": {"key_files": []},
    }
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config, allow_unicode=True), encoding="utf-8"
    )
    (tmp_path / "CONTRIBUTING_AI.md").write_text(
        "# AI Guide\nRules here.", encoding="utf-8"
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "CONTEXT.md").write_text(
        "# Context\n\nProject status line 1\nline 2\n", encoding="utf-8"
    )
    (docs / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
    (docs / "ROADMAP.md").write_text("# Roadmap\n", encoding="utf-8")
    (docs / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")

    dev_dir = docs / "developers" / "alice"
    dev_dir.mkdir(parents=True)
    (dev_dir / "CONTEXT.md").write_text(
        "# Alice Context\nWorking on feature X\n", encoding="utf-8"
    )
    (dev_dir / ".metadata.yaml").write_text(
        yaml.dump({"id": "alice", "role": "dev"}), encoding="utf-8"
    )

    insights_dir = tmp_path / ".vibecollab" / "insights"
    insights_dir.mkdir(parents=True)
    ins = {
        "id": "INS-001", "title": "Test Insight",
        "tags": ["test"], "category": "technique",
        "body": {"scenario": "s", "approach": "a"},
    }
    (insights_dir / "INS-001.yaml").write_text(
        yaml.dump(ins, allow_unicode=True), encoding="utf-8"
    )

    # sessions dir for session_save tests
    (tmp_path / ".vibecollab" / "sessions").mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.fixture
def empty_project(tmp_path):
    config = {"project": {"name": "Empty", "version": "0.1"}}
    (tmp_path / "project.yaml").write_text(yaml.dump(config), encoding="utf-8")
    return tmp_path


@pytest.fixture
def mcp(project_dir):
    """Captured MCP with all closures from a full project."""
    return _build_server(project_dir)


@pytest.fixture
def mcp_empty(empty_project):
    return _build_server(empty_project)


# ============================================================
# Resource tests
# ============================================================


class TestResources:
    def test_contributing_ai(self, mcp):
        text = mcp.resources["vibecollab://docs/contributing_ai"]()
        assert "AI Guide" in text

    def test_context(self, mcp):
        text = mcp.resources["vibecollab://docs/context"]()
        assert "Context" in text

    def test_decisions(self, mcp):
        text = mcp.resources["vibecollab://docs/decisions"]()
        assert "Decisions" in text

    def test_roadmap(self, mcp):
        text = mcp.resources["vibecollab://docs/roadmap"]()
        assert "Roadmap" in text

    def test_changelog(self, mcp):
        text = mcp.resources["vibecollab://docs/changelog"]()
        assert "Changelog" in text

    def test_insights_list(self, mcp):
        result = json.loads(mcp.resources["vibecollab://insights/list"]())
        assert result["count"] == 1
        assert result["insights"][0]["id"] == "INS-001"

    def test_insights_list_empty(self, mcp_empty):
        result = json.loads(mcp_empty.resources["vibecollab://insights/list"]())
        assert result["count"] == 0

    def test_resources_missing_files(self, mcp_empty):
        assert mcp_empty.resources["vibecollab://docs/contributing_ai"]() == ""
        assert mcp_empty.resources["vibecollab://docs/context"]() == ""


# ============================================================
# Tool tests — CLI-delegating tools
# ============================================================


class TestCliTools:
    """Tools that delegate to _run_cli — verify command construction."""

    def _mock_run(self, mcp, tool_name, kwargs, expected_fragments):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            result = mcp.tools[tool_name](**kwargs)
            assert result == "OK"
            cmd = m.call_args[0][0]
            for frag in expected_fragments:
                assert frag in cmd, f"'{frag}' not in {cmd}"

    def test_insight_search_basic(self, mcp):
        self._mock_run(mcp, "insight_search",
                       {"query": "test"},
                       ["vibecollab", "insight", "search", "test"])

    def test_insight_search_with_tags_and_semantic(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["insight_search"](query="q", tags="a,b", semantic=True)
            cmd = m.call_args[0][0]
            assert "--tags" in cmd
            assert "a,b" in cmd
            assert "--semantic" in cmd

    def test_insight_add_minimal(self, mcp):
        self._mock_run(mcp, "insight_add",
                       {"title": "T", "tags": "t", "category": "technique",
                        "scenario": "s", "approach": "a"},
                       ["vibecollab", "insight", "add", "-t", "T"])

    def test_insight_add_with_optional(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["insight_add"](
                title="T", tags="t", category="technique",
                scenario="s", approach="a",
                summary="sum", context="ctx",
            )
            cmd = m.call_args[0][0]
            assert "--summary" in cmd
            assert "--context" in cmd

    def test_check(self, mcp):
        self._mock_run(mcp, "check", {}, ["vibecollab", "check"])

    def test_check_strict(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["check"](strict=True)
            assert "--strict" in m.call_args[0][0]

    def test_onboard_defaults(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["onboard"]()
            cmd = m.call_args[0][0]
            assert "--json" in cmd

    def test_onboard_with_developer(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["onboard"](developer="alice")
            cmd = m.call_args[0][0]
            assert "-d" in cmd
            assert "alice" in cmd

    def test_next_step(self, mcp):
        self._mock_run(mcp, "next_step", {}, ["vibecollab", "next"])

    def test_task_list(self, mcp):
        self._mock_run(mcp, "task_list", {}, ["vibecollab", "task", "list"])

    def test_task_create_minimal(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["task_create"](task_id="TASK-DEV-001", role="DEV", feature="F")
            cmd = m.call_args[0][0]
            assert "--id" in cmd
            assert "--role" in cmd
            assert "--json" in cmd

    def test_task_create_with_optional(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["task_create"](
                task_id="T", role="R", feature="F",
                assignee="alice", description="desc",
            )
            cmd = m.call_args[0][0]
            assert "--assignee" in cmd
            assert "--description" in cmd

    def test_task_transition(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["task_transition"](task_id="TASK-DEV-001", new_status="in_progress")
            cmd = m.call_args[0][0]
            assert "IN_PROGRESS" in cmd
            assert "--json" in cmd

    def test_task_transition_with_reason(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["task_transition"](
                task_id="T", new_status="done", reason="completed"
            )
            assert "--reason" in m.call_args[0][0]

    def test_project_prompt_defaults(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["project_prompt"]()
            assert "--compact" in m.call_args[0][0]

    def test_project_prompt_with_developer(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["project_prompt"](developer="bob")
            cmd = m.call_args[0][0]
            assert "-d" in cmd
            assert "bob" in cmd

    def test_search_docs(self, mcp):
        self._mock_run(mcp, "search_docs", {"query": "q"}, ["vibecollab", "search", "q"])

    def test_search_docs_with_filters(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["search_docs"](query="q", doc_type="insight", min_score=0.5)
            cmd = m.call_args[0][0]
            assert "--type" in cmd
            assert "--min-score" in cmd

    def test_insight_suggest(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["insight_suggest"]()
            assert "--json" in m.call_args[0][0]

    def test_insight_graph_json(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["insight_graph"](output_format="json")
            cmd = m.call_args[0][0]
            assert "--format" in cmd
            assert "json" in cmd

    def test_insight_graph_mermaid(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["insight_graph"](output_format="mermaid")
            assert "mermaid" in m.call_args[0][0]

    def test_insight_export_all(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["insight_export"]()
            cmd = m.call_args[0][0]
            assert "export" in cmd

    def test_insight_export_with_ids_and_registry(self, mcp):
        with patch("vibecollab.agent.mcp_server._run_cli", return_value="OK") as m:
            mcp.tools["insight_export"](ids="INS-001,INS-002", include_registry=True)
            cmd = m.call_args[0][0]
            assert "--ids" in cmd
            assert "--include-registry" in cmd


# ============================================================
# Tool tests — non-CLI tools
# ============================================================


class TestDirectTools:
    """Tools that don't delegate to _run_cli."""

    def test_developer_context_exists(self, mcp):
        result = json.loads(mcp.tools["developer_context"](developer="alice"))
        assert result["developer"] == "alice"
        assert "Alice Context" in result["context"]
        assert result["metadata"]["id"] == "alice"

    def test_developer_context_missing(self, mcp):
        result = json.loads(mcp.tools["developer_context"](developer="unknown"))
        assert "error" in result

    def test_session_save_basic(self, mcp):
        result = json.loads(mcp.tools["session_save"](summary="Test session"))
        assert result["status"] == "ok"
        assert result["session_id"]

    def test_session_save_with_all_fields(self, mcp):
        result = json.loads(mcp.tools["session_save"](
            summary="Full session",
            developer="alice",
            key_decisions="D1, D2",
            files_changed="file1.py, file2.py",
            insights_added="INS-001, INS-002",
            tags="tag1, tag2",
        ))
        assert result["status"] == "ok"

    def test_session_save_error(self, mcp):
        with patch("vibecollab.domain.session_store.SessionStore.save", side_effect=Exception("disk full")):
            result = json.loads(mcp.tools["session_save"](summary="fail"))
            assert result["status"] == "error"
            assert "disk full" in result["message"]


# ============================================================
# Prompt tests
# ============================================================


class TestPrompts:
    def test_start_conversation_basic(self, mcp):
        text = mcp.prompts["start_conversation"]()
        assert "VibeCollab" in text
        assert "TestProject" in text
        assert "Context" in text

    def test_start_conversation_with_developer(self, mcp):
        text = mcp.prompts["start_conversation"](developer="alice")
        assert "alice" in text
        assert "Alice Context" in text

    def test_start_conversation_empty_project(self, mcp_empty):
        text = mcp_empty.prompts["start_conversation"]()
        assert "VibeCollab" in text
        assert "Empty" in text

    def test_start_conversation_unknown_developer(self, mcp):
        text = mcp.prompts["start_conversation"](developer="nonexistent")
        assert "VibeCollab" in text


# ============================================================
# _run_cli edge case
# ============================================================


class TestRunCliEdge:
    def test_run_cli_generic_exception(self, project_dir):
        from vibecollab.agent.mcp_server import _run_cli
        with patch("subprocess.run", side_effect=PermissionError("denied")):
            result = _run_cli(["vibecollab", "check"], project_dir)
            assert "错误" in result
            assert "denied" in result


# ============================================================
# run_server
# ============================================================


class TestRunServer:
    def test_run_server(self, project_dir):
        from vibecollab.agent.mcp_server import run_server

        mock_server = MagicMock()
        with patch("vibecollab.agent.mcp_server.create_mcp_server", return_value=mock_server):
            run_server(project_root=project_dir, transport="stdio")
            mock_server.run.assert_called_once_with(transport="stdio")
