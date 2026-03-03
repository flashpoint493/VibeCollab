"""
Tests for Task-Insight auto-linking integration (v0.7.1).

Covers:
- _extract_search_tags: tag extraction from task fields
- _find_related_insights: auto-search when InsightManager is available
- create_task with Insight auto-linking
- suggest_insights for existing tasks
- Backward compatibility (no InsightManager)
- CLI: task create / list / show / suggest
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from vibecollab.insight.manager import InsightManager
from vibecollab.domain.task_manager import TaskManager, TaskStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project_dir():
    """Temporary project directory with Insight data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        insights_dir = root / ".vibecollab" / "insights"
        insights_dir.mkdir(parents=True)

        # Create test Insights
        for i, (title, tags, cat) in enumerate([
            ("CLI command group pattern", ["cli", "click", "architecture", "modularity"], "workflow"),
            ("Jinja2 template engine", ["jinja2", "template", "engine", "pattern"], "technique"),
            ("Git commit convention", ["git", "commit", "workflow", "convention"], "workflow"),
            ("Test driven development", ["test", "pytest", "tdd", "quality"], "technique"),
            ("Authentication module design", ["auth", "security", "module", "architecture"], "technique"),
        ], start=1):
            insight_data = {
                "kind": "insight",
                "version": "1",
                "id": f"INS-{i:03d}",
                "title": title,
                "tags": tags,
                "category": cat,
                "body": {
                    "scenario": f"Test scenario {i}",
                    "approach": f"Test approach {i}",
                },
                "origin": {
                    "created_by": "test",
                    "created_at": "2026-01-01T00:00:00+00:00",
                },
            }
            with open(insights_dir / f"INS-{i:03d}.yaml", "w", encoding="utf-8") as f:
                yaml.dump(insight_data, f, allow_unicode=True)

        # Create registry
        registry = {
            "schema_version": "1",
            "entries": {
                f"INS-{i:03d}": {"weight": 1.0, "used_count": 0, "active": True}
                for i in range(1, 6)
            },
            "settings": {
                "decay_rate": 0.95,
                "decay_interval_days": 30,
                "use_reward": 0.1,
                "deactivate_threshold": 0.1,
            },
        }
        with open(insights_dir / "registry.yaml", "w", encoding="utf-8") as f:
            yaml.dump(registry, f, allow_unicode=True)

        yield root


@pytest.fixture
def mgr_with_insights(project_dir):
    """TaskManager with InsightManager."""
    im = InsightManager(project_root=project_dir)
    return TaskManager(project_root=project_dir, insight_manager=im)


@pytest.fixture
def mgr_without_insights(project_dir):
    """TaskManager without InsightManager."""
    return TaskManager(project_root=project_dir, insight_manager=None)


# ---------------------------------------------------------------------------
# TestExtractSearchTags
# ---------------------------------------------------------------------------

class TestExtractSearchTags:
    """Tests for _extract_search_tags static method."""

    def test_basic_extraction(self):
        tags = TaskManager._extract_search_tags("Add auth module", role="DEV")
        assert "auth" in tags
        assert "module" in tags
        assert "dev" in tags

    def test_stop_words_removed(self):
        tags = TaskManager._extract_search_tags(
            "The quick and easy way to do it"
        )
        # "the", "and", "to", "do", "it" are stop words
        assert "the" not in tags
        assert "and" not in tags
        assert "quick" in tags
        assert "easy" in tags

    def test_chinese_text(self):
        tags = TaskManager._extract_search_tags("实现认证模块设计")
        # Chinese text without spaces stays as one token
        assert len(tags) >= 1
        assert "实现认证模块设计" in tags

    def test_chinese_with_spaces(self):
        tags = TaskManager._extract_search_tags("认证 模块 设计")
        assert "认证" in tags
        assert "模块" in tags
        assert "设计" in tags

    def test_description_included(self):
        tags = TaskManager._extract_search_tags(
            "Add CLI", description="click-based command group"
        )
        assert "cli" in tags
        assert "click" in tags
        assert "command" in tags

    def test_deduplication(self):
        tags = TaskManager._extract_search_tags(
            "cli cli cli module", role="DEV"
        )
        assert tags.count("cli") == 1

    def test_empty_input(self):
        tags = TaskManager._extract_search_tags("")
        assert tags == []

    def test_single_char_filtered(self):
        tags = TaskManager._extract_search_tags("a b c real word")
        assert "a" not in tags
        assert "real" in tags
        assert "word" in tags


# ---------------------------------------------------------------------------
# TestInsightAutoLink
# ---------------------------------------------------------------------------

class TestInsightAutoLink:
    """Tests for automatic Insight linking on task creation."""

    def test_create_task_links_insights(self, mgr_with_insights):
        task = mgr_with_insights.create_task(
            id="TASK-DEV-001", role="DEV",
            feature="Implement CLI command group",
            actor="test",
        )
        related = task.metadata.get("related_insights", [])
        assert len(related) > 0
        # INS-001 has tags [cli, click, architecture, modularity]
        ids = [r["id"] for r in related]
        assert "INS-001" in ids

    def test_create_task_no_match(self, mgr_with_insights):
        task = mgr_with_insights.create_task(
            id="TASK-PM-001", role="PM",
            feature="Schedule meeting",
            actor="test",
        )
        related = task.metadata.get("related_insights", [])
        # "schedule" and "meeting" don't match any test Insight tags
        assert len(related) == 0

    def test_create_task_without_insight_manager(self, mgr_without_insights):
        task = mgr_without_insights.create_task(
            id="TASK-DEV-001", role="DEV",
            feature="Implement CLI command group",
            actor="test",
        )
        # No InsightManager → no related_insights in metadata
        assert "related_insights" not in task.metadata

    def test_related_insights_have_score(self, mgr_with_insights):
        task = mgr_with_insights.create_task(
            id="TASK-DEV-002", role="DEV",
            feature="Add authentication security module",
            actor="test",
        )
        related = task.metadata.get("related_insights", [])
        if related:
            for r in related:
                assert "score" in r
                assert isinstance(r["score"], float)
                assert 0 < r["score"] <= 2.0

    def test_event_log_records_related(self, mgr_with_insights):
        mgr_with_insights.create_task(
            id="TASK-DEV-003", role="DEV",
            feature="CLI click architecture",
            actor="test",
        )
        events = mgr_with_insights.event_log.read_all()
        created_events = [e for e in events if e.event_type == "task_created"]
        assert len(created_events) >= 1
        payload = created_events[-1].payload
        if "related_insights" in payload:
            assert "INS-001" in payload["related_insights"]

    def test_related_insights_persisted(self, mgr_with_insights):
        """Related insights survive save/load cycle."""
        mgr_with_insights.create_task(
            id="TASK-DEV-004", role="DEV",
            feature="template engine pattern",
            actor="test",
        )
        # Reload from disk
        mgr2 = TaskManager(project_root=mgr_with_insights.project_root)
        task = mgr2.get_task("TASK-DEV-004")
        assert task is not None
        related = task.metadata.get("related_insights", [])
        assert len(related) > 0

    def test_description_improves_matching(self, mgr_with_insights):
        """Adding description should potentially improve matching."""
        t1 = mgr_with_insights.create_task(
            id="TASK-DEV-005", role="DEV",
            feature="Add module",
            actor="test",
        )
        t1.metadata.get("related_insights", [])  # noqa: F841 - exercise the code path

        t2 = mgr_with_insights.create_task(
            id="TASK-DEV-006", role="DEV",
            feature="Add module",
            description="authentication security architecture design",
            actor="test",
        )
        r2 = t2.metadata.get("related_insights", [])
        # More descriptive text should find INS-005 (auth, security, architecture)
        ids2 = [r["id"] for r in r2]
        assert "INS-005" in ids2


# ---------------------------------------------------------------------------
# TestSuggestInsights
# ---------------------------------------------------------------------------

class TestSuggestInsights:
    """Tests for suggest_insights method."""

    def test_suggest_for_existing_task(self, mgr_with_insights):
        mgr_with_insights.create_task(
            id="TASK-DEV-010", role="DEV",
            feature="Improve testing workflow",
            actor="test",
        )
        suggestions = mgr_with_insights.suggest_insights("TASK-DEV-010")
        assert isinstance(suggestions, list)
        for s in suggestions:
            assert "id" in s
            assert "title" in s
            assert "score" in s
            assert "tags" in s

    def test_suggest_nonexistent_task(self, mgr_with_insights):
        results = mgr_with_insights.suggest_insights("TASK-DEV-999")
        assert results == []

    def test_suggest_without_insight_manager(self, mgr_without_insights):
        mgr_without_insights.create_task(
            id="TASK-DEV-010", role="DEV",
            feature="Anything",
            actor="test",
        )
        results = mgr_without_insights.suggest_insights("TASK-DEV-010")
        assert results == []

    def test_suggest_respects_limit(self, mgr_with_insights):
        mgr_with_insights.create_task(
            id="TASK-DEV-011", role="DEV",
            feature="cli click architecture template test pytest",
            actor="test",
        )
        results = mgr_with_insights.suggest_insights("TASK-DEV-011", limit=2)
        assert len(results) <= 2


# ---------------------------------------------------------------------------
# TestBackwardCompatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    """Ensure existing code that doesn't pass insight_manager still works."""

    def test_default_no_insight_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TaskManager(project_root=Path(tmpdir))
            assert mgr.insight_manager is None
            task = mgr.create_task(
                id="TASK-DEV-001", role="DEV",
                feature="Something", actor="test",
            )
            assert "related_insights" not in task.metadata

    def test_existing_tests_pattern_still_works(self):
        """The old TaskManager(project_root=path) signature works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TaskManager(project_root=Path(tmpdir))
            task = mgr.create_task(
                id="TASK-DEV-001", role="DEV",
                feature="Add auth", assignee="alice",
                actor="ocarina",
            )
            assert task.id == "TASK-DEV-001"
            assert task.status == TaskStatus.TODO
            assert task.assignee == "alice"


# ---------------------------------------------------------------------------
# TestCLI
# ---------------------------------------------------------------------------

class TestCLI:
    """Tests for vibecollab task CLI commands."""

    def _setup_project(self, tmpdir):
        """Set up a minimal project for CLI testing."""
        root = Path(tmpdir)
        insights_dir = root / ".vibecollab" / "insights"
        insights_dir.mkdir(parents=True)

        # One test Insight
        insight_data = {
            "kind": "insight", "version": "1",
            "id": "INS-001",
            "title": "CLI command group pattern",
            "tags": ["cli", "click", "architecture"],
            "category": "workflow",
            "body": {"scenario": "test", "approach": "test"},
            "origin": {
                "created_by": "test",
                "created_at": "2026-01-01T00:00:00+00:00",
            },
        }
        with open(insights_dir / "INS-001.yaml", "w", encoding="utf-8") as f:
            yaml.dump(insight_data, f, allow_unicode=True)

        registry = {
            "schema_version": "1",
            "entries": {
                "INS-001": {"weight": 1.0, "used_count": 0, "active": True},
            },
            "settings": {
                "decay_rate": 0.95, "decay_interval_days": 30,
                "use_reward": 0.1, "deactivate_threshold": 0.1,
            },
        }
        with open(insights_dir / "registry.yaml", "w", encoding="utf-8") as f:
            yaml.dump(registry, f, allow_unicode=True)

        return root

    def test_create_and_show(self):
        import os

        from vibecollab.cli.task import task_group

        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._setup_project(tmpdir)
            runner = CliRunner()
            old_cwd = os.getcwd()
            os.chdir(root)
            try:
                # Create
                result = runner.invoke(task_group, [
                    "create", "--id", "TASK-DEV-001",
                    "--role", "DEV", "--feature", "CLI click architecture",
                    "--json",
                ])
                assert result.exit_code == 0
                data = json.loads(result.output)
                assert data["id"] == "TASK-DEV-001"
                assert "related_insights" in data.get("metadata", {})

                # Show
                result = runner.invoke(task_group, [
                    "show", "TASK-DEV-001", "--json",
                ])
                assert result.exit_code == 0
                data = json.loads(result.output)
                assert data["id"] == "TASK-DEV-001"
            finally:
                os.chdir(old_cwd)

    def test_list(self):
        import os

        from vibecollab.cli.task import task_group

        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._setup_project(tmpdir)
            runner = CliRunner()
            old_cwd = os.getcwd()
            os.chdir(root)
            try:
                runner.invoke(task_group, [
                    "create", "--id", "TASK-DEV-001",
                    "--role", "DEV", "--feature", "Task one",
                ])
                runner.invoke(task_group, [
                    "create", "--id", "TASK-PM-001",
                    "--role", "PM", "--feature", "Task two",
                ])
                result = runner.invoke(task_group, ["list", "--json"])
                assert result.exit_code == 0
                data = json.loads(result.output)
                assert len(data) == 2
            finally:
                os.chdir(old_cwd)

    def test_suggest(self):
        import os

        from vibecollab.cli.task import task_group

        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._setup_project(tmpdir)
            runner = CliRunner()
            old_cwd = os.getcwd()
            os.chdir(root)
            try:
                runner.invoke(task_group, [
                    "create", "--id", "TASK-DEV-001",
                    "--role", "DEV", "--feature", "CLI click",
                ])
                result = runner.invoke(task_group, [
                    "suggest", "TASK-DEV-001", "--json",
                ])
                assert result.exit_code == 0
                data = json.loads(result.output)
                assert isinstance(data, list)
            finally:
                os.chdir(old_cwd)

    def test_create_invalid_id(self):
        import os

        from vibecollab.cli.task import task_group

        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._setup_project(tmpdir)
            runner = CliRunner()
            old_cwd = os.getcwd()
            os.chdir(root)
            try:
                result = runner.invoke(task_group, [
                    "create", "--id", "INVALID",
                    "--role", "DEV", "--feature", "Bad",
                ])
                assert result.exit_code != 0
            finally:
                os.chdir(old_cwd)

    def test_show_nonexistent(self):
        import os

        from vibecollab.cli.task import task_group

        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._setup_project(tmpdir)
            runner = CliRunner()
            old_cwd = os.getcwd()
            os.chdir(root)
            try:
                result = runner.invoke(task_group, [
                    "show", "TASK-DEV-999",
                ])
                assert result.exit_code != 0
            finally:
                os.chdir(old_cwd)

    def test_list_empty(self):
        import os

        from vibecollab.cli.task import task_group

        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._setup_project(tmpdir)
            runner = CliRunner()
            old_cwd = os.getcwd()
            os.chdir(root)
            try:
                result = runner.invoke(task_group, ["list"])
                assert result.exit_code == 0
                assert "No tasks" in result.output
            finally:
                os.chdir(old_cwd)

    def test_create_rich_output(self):
        import os

        from vibecollab.cli.task import task_group

        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._setup_project(tmpdir)
            runner = CliRunner()
            old_cwd = os.getcwd()
            os.chdir(root)
            try:
                result = runner.invoke(task_group, [
                    "create", "--id", "TASK-DEV-001",
                    "--role", "DEV", "--feature", "CLI architecture click",
                    "--assignee", "ocarina",
                    "--description", "Build click-based command",
                ])
                assert result.exit_code == 0
                assert "TASK-DEV-001" in result.output
                assert "ocarina" in result.output
                assert "Insight" in result.output
            finally:
                os.chdir(old_cwd)
