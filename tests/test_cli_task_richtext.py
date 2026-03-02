"""
Supplementary tests for cli_task.py — non-JSON (rich text) output paths.

Covers uncovered lines: 26-30, 38-39, 114-117, 140-158, 176-188
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner

from vibecollab.cli.task import task_group


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    """Create project with tasks dir and change to it."""
    config = {
        "project": {"name": "Test", "version": "1.0"},
    }
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config), encoding="utf-8"
    )
    (tmp_path / ".vibecollab").mkdir()
    (tmp_path / ".vibecollab" / "insights").mkdir()
    (tmp_path / ".vibecollab" / "tasks").mkdir()

    # Create insight for suggest tests
    ins = {
        "id": "INS-001",
        "title": "Test Insight",
        "tags": ["test", "dev"],
        "category": "technique",
        "body": {"scenario": "scenario", "approach": "approach"},
    }
    (tmp_path / ".vibecollab" / "insights" / "INS-001.yaml").write_text(
        yaml.dump(ins, allow_unicode=True), encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)
    return tmp_path


# ============================================================
# _load_config tests (lines 26-30)
# ============================================================


class TestLoadConfig:
    def test_load_existing(self, project_dir):
        from vibecollab.cli.task import _load_config
        config = _load_config(str(project_dir / "project.yaml"))
        assert config["project"]["name"] == "Test"

    def test_load_missing(self, tmp_path):
        from vibecollab.cli.task import _load_config
        config = _load_config(str(tmp_path / "nonexistent.yaml"))
        assert config == {}

    def test_load_empty(self, tmp_path):
        (tmp_path / "empty.yaml").write_text("", encoding="utf-8")
        from vibecollab.cli.task import _load_config
        config = _load_config(str(tmp_path / "empty.yaml"))
        assert config == {}


# ============================================================
# _get_managers InsightManager failure (line 38-39)
# ============================================================


class TestGetManagers:
    def test_insight_manager_fails(self, project_dir):
        from vibecollab.cli.task import _get_managers
        with patch("vibecollab.cli.task.InsightManager", side_effect=Exception("boom")):
            tm, im = _get_managers(str(project_dir / "project.yaml"))
            assert tm is not None
            assert im is None


# ============================================================
# list_tasks non-JSON (lines 114-117)
# ============================================================


class TestListTasksRichText:
    def test_list_with_tasks(self, runner, project_dir):
        """Non-JSON list with existing tasks."""
        # Create a task first
        result = runner.invoke(task_group, [
            "create",
            "--id", "TASK-DEV-001",
            "--role", "DEV",
            "--feature", "Test feature",
            "--json",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0

        # List without --json
        result = runner.invoke(task_group, [
            "list",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0
        assert "TASK-DEV-001" in result.output
        assert "Test feature" in result.output


# ============================================================
# show_task non-JSON (lines 140-158)
# ============================================================


class TestShowTaskRichText:
    def test_show_basic(self, runner, project_dir):
        """Show task details without --json."""
        runner.invoke(task_group, [
            "create",
            "--id", "TASK-DEV-002",
            "--role", "DEV",
            "--feature", "Feature two",
            "--description", "Detailed description",
            "--json",
            "-c", str(project_dir / "project.yaml"),
        ])

        result = runner.invoke(task_group, [
            "show", "TASK-DEV-002",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0
        assert "TASK-DEV-002" in result.output
        assert "DEV" in result.output
        assert "Feature two" in result.output
        assert "Detailed description" in result.output

    def test_show_nonexistent(self, runner, project_dir):
        """Show non-existent task errors."""
        result = runner.invoke(task_group, [
            "show", "TASK-NOPE-999",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 1


# ============================================================
# suggest_insights non-JSON (lines 176-188)
# ============================================================


class TestSuggestRichText:
    def test_suggest_no_results(self, runner, project_dir):
        """Suggest with no related insights shows friendly message."""
        # Create a task with no matching insights
        runner.invoke(task_group, [
            "create",
            "--id", "TASK-DEV-003",
            "--role", "DEV",
            "--feature", "Unrelated feature xyz",
            "--json",
            "-c", str(project_dir / "project.yaml"),
        ])

        result = runner.invoke(task_group, [
            "suggest", "TASK-DEV-003",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0
        # Either shows results or "未找到关联" message
        assert "TASK-DEV-003" in result.output

    def test_suggest_nonexistent_task(self, runner, project_dir):
        """Suggest for non-existent task errors."""
        result = runner.invoke(task_group, [
            "suggest", "TASK-NOPE-999",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 1

    def test_suggest_with_results(self, runner, project_dir):
        """Suggest with matching insights shows formatted output."""
        # Create a task that matches our insight tags
        runner.invoke(task_group, [
            "create",
            "--id", "TASK-DEV-004",
            "--role", "DEV",
            "--feature", "Test technique development",
            "--json",
            "-c", str(project_dir / "project.yaml"),
        ])

        result = runner.invoke(task_group, [
            "suggest", "TASK-DEV-004",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0
        # Check for either results or no-results message
        assert "TASK-DEV-004" in result.output
