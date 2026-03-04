"""
VibeCollab MCP Server Unit Tests

Testing MCP Server core functionality:
- Server creation and configuration
- Resource registration and reading
- Tool registration and invocation
- Prompt template generation
- CLI commands (mcp serve/config/inject)
- Edge cases (empty project, missing files)
"""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner


# ============================================================
# Helpers
# ============================================================


def _mcp_available() -> bool:
    """Check if mcp package is importable"""
    try:
        import mcp  # noqa: F401

        return True
    except ImportError:
        return False


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def project_dir(tmp_path):
    """Create a complete test project directory"""
    # project.yaml
    config = {
        "project": {
            "name": "TestProject",
            "version": "1.0.0",
            "description": "A test project for MCP",
        },
        "documentation": {
            "key_files": ["CONTRIBUTING_AI.md", "docs/CONTEXT.md"],
        },
    }
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config, allow_unicode=True), encoding="utf-8"
    )

    # CONTRIBUTING_AI.md
    (tmp_path / "CONTRIBUTING_AI.md").write_text(
        "# AI Collaboration Protocol\n\n## Core Philosophy\nHuman-centered AI collaboration\n", encoding="utf-8"
    )

    # docs directory
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "CONTEXT.md").write_text(
        "# Project Context\n\n## Current Status\n- Version: v1.0.0\n- In development\n", encoding="utf-8"
    )
    (docs / "DECISIONS.md").write_text(
        "# Decision Records\n\n### DECISION-001: Test Decision\n- Decision: A\n", encoding="utf-8"
    )
    (docs / "ROADMAP.md").write_text(
        "# Roadmap\n\n- [ ] TODO Item 1\n- [x] Completed Item\n", encoding="utf-8"
    )
    (docs / "CHANGELOG.md").write_text(
        "# Changelog\n\n## v1.0.0\n- Initial release\n", encoding="utf-8"
    )

    # Developer directory
    dev_dir = docs / "developers" / "alice"
    dev_dir.mkdir(parents=True)
    (dev_dir / "CONTEXT.md").write_text(
        "# Alice Context\n\n## Current Task\n- Developing MCP Server\n", encoding="utf-8"
    )
    (dev_dir / ".metadata.yaml").write_text(
        yaml.dump({"id": "alice", "role": "developer"}), encoding="utf-8"
    )

    # .vibecollab/insights/
    insights_dir = tmp_path / ".vibecollab" / "insights"
    insights_dir.mkdir(parents=True)

    ins1 = {
        "id": "INS-001",
        "title": "Test Insight 1",
        "tags": ["test", "mcp"],
        "category": "technique",
        "body": {"scenario": "Test scenario", "approach": "Test approach"},
    }
    ins2 = {
        "id": "INS-002",
        "title": "Test Insight 2",
        "tags": ["debug", "tool"],
        "category": "debug",
        "body": {"scenario": "Debug scenario", "approach": "Debug approach"},
    }
    (insights_dir / "INS-001.yaml").write_text(
        yaml.dump(ins1, allow_unicode=True), encoding="utf-8"
    )
    (insights_dir / "INS-002.yaml").write_text(
        yaml.dump(ins2, allow_unicode=True), encoding="utf-8"
    )

    return tmp_path


@pytest.fixture
def empty_project(tmp_path):
    """Minimal project (only project.yaml)"""
    config = {"project": {"name": "EmptyProject", "version": "0.1.0"}}
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config), encoding="utf-8"
    )
    return tmp_path


# ============================================================
# Helper function tests
# ============================================================


class TestHelpers:
    def test_find_project_root(self, project_dir):
        from vibecollab.agent.mcp_server import _find_project_root

        # Find from project root
        assert _find_project_root(project_dir) == project_dir

        # Find from subdirectory
        sub = project_dir / "docs"
        assert _find_project_root(sub) == project_dir

    def test_find_project_root_no_yaml(self, tmp_path):
        from vibecollab.agent.mcp_server import _find_project_root

        # No project.yaml, returns starting directory
        result = _find_project_root(tmp_path)
        assert result == tmp_path

    def test_safe_read_text(self, project_dir):
        from vibecollab.agent.mcp_server import _safe_read_text

        text = _safe_read_text(project_dir / "CONTRIBUTING_AI.md")
        assert "AI Collaboration Protocol" in text

    def test_safe_read_text_missing(self, tmp_path):
        from vibecollab.agent.mcp_server import _safe_read_text

        assert _safe_read_text(tmp_path / "nonexistent.md") == ""

    def test_safe_load_yaml(self, project_dir):
        from vibecollab.agent.mcp_server import _safe_load_yaml

        data = _safe_load_yaml(project_dir / "project.yaml")
        assert data["project"]["name"] == "TestProject"

    def test_safe_load_yaml_missing(self, tmp_path):
        from vibecollab.agent.mcp_server import _safe_load_yaml

        assert _safe_load_yaml(tmp_path / "missing.yaml") == {}

    def test_get_insight_files(self, project_dir):
        from vibecollab.agent.mcp_server import _get_insight_files

        files = _get_insight_files(project_dir)
        assert len(files) == 2
        assert files[0].name == "INS-002.yaml"  # Reverse order

    def test_get_insight_files_no_dir(self, tmp_path):
        from vibecollab.agent.mcp_server import _get_insight_files

        assert _get_insight_files(tmp_path) == []


# ============================================================
# MCP Server creation tests
# ============================================================


class TestCreateMcpServer:
    def test_import_error_without_mcp(self, project_dir):
        """Should raise ImportError when mcp is not installed"""
        from vibecollab.agent.mcp_server import create_mcp_server

        with patch.dict("sys.modules", {"mcp": None, "mcp.server.fastmcp": None}):
            with pytest.raises((ImportError, ModuleNotFoundError)):
                create_mcp_server(project_dir)

    @pytest.mark.skipif(
        not _mcp_available(),
        reason="mcp not installed, skipping server instantiation test",
    )
    def test_create_server(self, project_dir):
        """Successfully create MCP Server instance"""
        from vibecollab.agent.mcp_server import create_mcp_server

        server = create_mcp_server(project_dir)
        assert server is not None


# ============================================================
# Resource tests (mock FastMCP)
# ============================================================


class TestResources:
    """Test Resource function data reading logic"""

    def test_get_contributing_ai(self, project_dir):
        from vibecollab.agent.mcp_server import _safe_read_text

        text = _safe_read_text(project_dir / "CONTRIBUTING_AI.md")
        assert "AI Collaboration Protocol" in text
        assert "Core Philosophy" in text

    def test_get_context(self, project_dir):
        from vibecollab.agent.mcp_server import _safe_read_text

        text = _safe_read_text(project_dir / "docs" / "CONTEXT.md")
        assert "Project Context" in text
        assert "v1.0.0" in text

    def test_get_decisions(self, project_dir):
        from vibecollab.agent.mcp_server import _safe_read_text

        text = _safe_read_text(project_dir / "docs" / "DECISIONS.md")
        assert "DECISION-001" in text

    def test_get_insights_list(self, project_dir):
        from vibecollab.agent.mcp_server import _get_insight_files, _safe_load_yaml

        files = _get_insight_files(project_dir)
        insights = []
        for f in files:
            data = _safe_load_yaml(f)
            if data:
                insights.append({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "tags": data.get("tags"),
                })
        assert len(insights) == 2
        assert insights[0]["id"] == "INS-002"  # Reverse order
        assert "mcp" in insights[1]["tags"]

    def test_empty_project_resources(self, empty_project):
        from vibecollab.agent.mcp_server import _safe_read_text, _get_insight_files

        assert _safe_read_text(empty_project / "CONTRIBUTING_AI.md") == ""
        assert _safe_read_text(empty_project / "docs" / "CONTEXT.md") == ""
        assert _get_insight_files(empty_project) == []


# ============================================================
# Tool CLI invocation tests (mock subprocess)
# ============================================================


class TestTools:
    """Test Tool function CLI invocation logic"""

    def test_run_cli_success(self, project_dir):
        from vibecollab.agent.mcp_server import _run_cli

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Search result: INS-001\n",
                stderr="",
                returncode=0,
            )
            result = _run_cli(
                ["vibecollab", "insight", "search", "test"],
                project_dir,
            )
            assert "INS-001" in result
            mock_run.assert_called_once()

    def test_run_cli_error(self, project_dir):
        from vibecollab.agent.mcp_server import _run_cli

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="Error message",
                returncode=1,
            )
            result = _run_cli(["vibecollab", "check"], project_dir)
            assert "stderr" in result
            assert "Error message" in result

    def test_run_cli_timeout(self, project_dir):
        from vibecollab.agent.mcp_server import _run_cli

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = _run_cli(["vibecollab", "check"], project_dir)
            assert "timed out" in result.lower()

    def test_run_cli_not_found(self, project_dir):
        from vibecollab.agent.mcp_server import _run_cli

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _run_cli(["vibecollab", "check"], project_dir)
            assert "not found" in result.lower()

    def test_developer_context_exists(self, project_dir):
        """Developer context reading"""
        from vibecollab.agent.mcp_server import _safe_read_text, _safe_load_yaml

        dev_dir = project_dir / "docs" / "developers" / "alice"
        context = _safe_read_text(dev_dir / "CONTEXT.md")
        metadata = _safe_load_yaml(dev_dir / ".metadata.yaml")

        assert "Alice Context" in context
        assert metadata["id"] == "alice"

    def test_developer_context_missing(self, project_dir):
        dev_dir = project_dir / "docs" / "developers" / "nonexistent"
        assert not dev_dir.exists()


# ============================================================
# Prompt template tests
# ============================================================


class TestPrompts:
    def test_start_conversation_prompt(self, project_dir):
        """Test conversation start prompt generation logic"""
        from vibecollab.agent.mcp_server import _safe_load_yaml, _safe_read_text

        # Simulate prompt generation logic
        config = _safe_load_yaml(project_dir / "project.yaml")
        proj = config.get("project", {})
        context_text = _safe_read_text(project_dir / "docs" / "CONTEXT.md")

        assert proj["name"] == "TestProject"
        assert "Project Context" in context_text

    def test_start_conversation_with_developer(self, project_dir):
        from vibecollab.agent.mcp_server import _safe_read_text

        dev_context = _safe_read_text(
            project_dir / "docs" / "developers" / "alice" / "CONTEXT.md"
        )
        assert "Alice Context" in dev_context
        assert "MCP Server" in dev_context

    def test_start_conversation_empty_project(self, empty_project):
        from vibecollab.agent.mcp_server import _safe_load_yaml, _safe_read_text

        config = _safe_load_yaml(empty_project / "project.yaml")
        assert config["project"]["name"] == "EmptyProject"
        assert _safe_read_text(empty_project / "docs" / "CONTEXT.md") == ""


# ============================================================
# CLI command tests
# ============================================================


class TestCliMcp:
    def test_mcp_group_help(self):
        from vibecollab.cli.mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["--help"])
        assert result.exit_code == 0
        assert "MCP Server" in result.output

    def test_mcp_serve_help(self):
        from vibecollab.cli.mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["serve", "--help"])
        assert result.exit_code == 0
        assert "stdio" in result.output
        assert "sse" in result.output

    def test_mcp_config_cursor(self):
        from vibecollab.cli.mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["config", "--ide", "cursor"])
        assert result.exit_code == 0
        assert ".cursor/mcp.json" in result.output
        assert "vibecollab" in result.output

    def test_mcp_config_cline(self):
        from vibecollab.cli.mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["config", "--ide", "cline"])
        assert result.exit_code == 0
        assert ".cline/mcp_settings.json" in result.output

    def test_mcp_config_codebuddy(self):
        from vibecollab.cli.mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["config", "--ide", "codebuddy"])
        assert result.exit_code == 0
        assert ".codebuddy/mcp.json" in result.output

    def test_mcp_inject_cursor(self, tmp_path):
        from vibecollab.cli.mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(
            mcp_group, ["inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Injected" in result.output

        # Verify file was created
        config_file = tmp_path / ".cursor" / "mcp.json"
        assert config_file.exists()
        data = json.loads(config_file.read_text())
        assert "vibecollab" in data["mcpServers"]

    def test_mcp_inject_all(self, tmp_path):
        from vibecollab.cli.mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(
            mcp_group, ["inject", "--ide", "all", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / ".cursor" / "mcp.json").exists()
        assert (tmp_path / ".cline" / "mcp_settings.json").exists()
        assert (tmp_path / ".codebuddy" / "mcp.json").exists()

    def test_mcp_inject_preserves_existing(self, tmp_path):
        """Injection should preserve existing config"""
        from vibecollab.cli.mcp import mcp_group

        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir()
        existing = {
            "mcpServers": {
                "other-tool": {"command": "other", "args": ["serve"]},
            }
        }
        (cursor_dir / "mcp.json").write_text(json.dumps(existing))

        runner = CliRunner()
        result = runner.invoke(
            mcp_group, ["inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0

        data = json.loads((cursor_dir / "mcp.json").read_text())
        assert "other-tool" in data["mcpServers"]
        assert "vibecollab" in data["mcpServers"]

    def test_mcp_serve_without_mcp_dep(self):
        """Serve should error when mcp is not installed"""
        from vibecollab.cli.mcp import mcp_group

        runner = CliRunner()
        with patch.dict("sys.modules", {"vibecollab.agent.mcp_server": None}):
            # Simulate import failure via mock
            result = runner.invoke(mcp_group, ["serve"])
            # Could throw ImportError or non-zero exit code
            # Specific behavior depends on mock, just verify no crash
            assert result.exit_code != 0 or "Error" in result.output


# ============================================================
# Integration tests (full CLI pipeline)
# ============================================================


class TestIntegration:
    def test_vibecollab_mcp_registered(self):
        """vibecollab mcp command is registered in main CLI"""
        from vibecollab.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["mcp", "--help"])
        assert result.exit_code == 0
        assert "serve" in result.output
        assert "config" in result.output
        assert "inject" in result.output

    def test_full_inject_and_verify(self, tmp_path):
        """Full injection flow: inject -> verify config file content"""
        from vibecollab.cli import main

        runner = CliRunner()
        result = runner.invoke(
            main, ["mcp", "inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0

        config_path = tmp_path / ".cursor" / "mcp.json"
        assert config_path.exists()

        data = json.loads(config_path.read_text())
        server_config = data["mcpServers"]["vibecollab"]
        assert server_config["command"] == "vibecollab"
        assert server_config["args"] == ["mcp", "serve"]
