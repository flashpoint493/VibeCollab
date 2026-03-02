"""
Tests for cli_insight.py — Insight 沉淀系统 CLI 命令
"""

import json
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from vibecollab.cli.insight import insight

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project_dir(tmp_path):
    """创建带有 project.yaml 和基础目录的临时项目"""
    config = {
        "project": {"name": "TestProject", "version": "v1.0"},
        "multi_developer": {
            "enabled": True,
            "identity": {"primary": "git_username", "fallback": "system_user", "normalize": True},
            "context": {"per_developer_dir": "docs/developers", "metadata_file": ".metadata.yaml"},
        },
    }
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config, allow_unicode=True), encoding="utf-8"
    )
    (tmp_path / ".vibecollab").mkdir()
    (tmp_path / "docs" / "developers" / "testdev").mkdir(parents=True)
    # 初始化 developer metadata
    meta = {"developer": "testdev", "created_at": "2026-01-01", "total_updates": 0}
    meta_path = tmp_path / "docs" / "developers" / "testdev" / ".metadata.yaml"
    meta_path.write_text(yaml.dump(meta), encoding="utf-8")
    return tmp_path


@pytest.fixture
def chdir_project(project_dir, monkeypatch):
    """切换工作目录到临时项目"""
    monkeypatch.chdir(project_dir)
    return project_dir


# ---------------------------------------------------------------------------
# Tests: list
# ---------------------------------------------------------------------------

class TestListInsights:
    def test_list_empty(self, runner, chdir_project):
        result = runner.invoke(insight, ["list"])
        assert result.exit_code == 0
        assert "暂无沉淀" in result.output

    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_list_with_items(self, mock_dm, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(
            title="Test Insight",
            tags=["test"],
            category="technique",
            body={"scenario": "s", "approach": "a"},
            created_by="testdev",
        )
        result = runner.invoke(insight, ["list"])
        assert result.exit_code == 0
        assert "INS-001" in result.output
        assert "Test Insight" in result.output

    def test_list_json(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(
            title="JSON Test",
            tags=["json"],
            category="workflow",
            body={"scenario": "s", "approach": "a"},
            created_by="testdev",
        )
        result = runner.invoke(insight, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "INS-001"
        assert data[0]["category"] == "workflow"

    def test_list_active_only(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(
            title="Active",
            tags=["a"],
            category="technique",
            body={"scenario": "s", "approach": "a"},
            created_by="testdev",
        )
        mgr.create(
            title="Inactive",
            tags=["b"],
            category="debug",
            body={"scenario": "s", "approach": "a"},
            created_by="testdev",
        )
        # 手动停用 INS-002
        entries, settings = mgr.get_registry()
        entries["INS-002"].active = False
        mgr._save_registry(entries, settings)

        result = runner.invoke(insight, ["list", "--active-only"])
        assert result.exit_code == 0
        assert "INS-001" in result.output
        assert "INS-002" not in result.output


# ---------------------------------------------------------------------------
# Tests: show
# ---------------------------------------------------------------------------

class TestShowInsight:
    def test_show_existing(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(
            title="Show Test",
            tags=["demo"],
            category="technique",
            body={"scenario": "test scenario", "approach": "test approach"},
            created_by="testdev",
            summary="A summary",
        )
        result = runner.invoke(insight, ["show", "INS-001"])
        assert result.exit_code == 0
        assert "Show Test" in result.output
        assert "test scenario" in result.output
        assert "A summary" in result.output
        assert "testdev" in result.output

    def test_show_not_found(self, runner, chdir_project):
        result = runner.invoke(insight, ["show", "INS-999"])
        assert result.exit_code != 0
        assert "未找到" in result.output


# ---------------------------------------------------------------------------
# Tests: add
# ---------------------------------------------------------------------------

class TestAddInsight:
    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_add_basic(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.domain.developer import DeveloperManager
        # 模拟 developer manager 使用固定身份
        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            result = runner.invoke(insight, [
                "add",
                "--title", "CLI Created",
                "--tags", "cli,test",
                "--category", "technique",
                "--scenario", "When using CLI",
                "--approach", "Run the command",
            ])
        assert result.exit_code == 0
        assert "INS-001" in result.output
        assert "CLI Created" in result.output

    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_add_with_all_options(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.domain.developer import DeveloperManager
        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            result = runner.invoke(insight, [
                "add",
                "--title", "Full Options",
                "--tags", "arch,python",
                "--category", "workflow",
                "--scenario", "Full scenario",
                "--approach", "Full approach",
                "--summary", "Full summary",
                "--validation", "Run tests",
                "--source-type", "task",
                "--source-ref", "TASK-DEV-001",
            ])
        assert result.exit_code == 0
        assert "INS-001" in result.output


# ---------------------------------------------------------------------------
# Tests: search
# ---------------------------------------------------------------------------

class TestSearchInsights:
    def test_search_by_tags(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="A", tags=["python", "refactor"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")
        mgr.create(title="B", tags=["java"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        result = runner.invoke(insight, ["search", "--tags", "python"])
        assert result.exit_code == 0
        assert "INS-001" in result.output
        assert "INS-002" not in result.output

    def test_search_by_category(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="A", tags=["a"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")
        mgr.create(title="B", tags=["b"], category="workflow",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        result = runner.invoke(insight, ["search", "--category", "workflow"])
        assert result.exit_code == 0
        assert "INS-002" in result.output

    def test_search_no_args(self, runner, chdir_project):
        result = runner.invoke(insight, ["search"])
        assert result.exit_code != 0

    def test_search_no_results(self, runner, chdir_project):
        result = runner.invoke(insight, ["search", "--tags", "nonexistent"])
        assert result.exit_code == 0
        assert "未找到" in result.output


# ---------------------------------------------------------------------------
# Tests: use
# ---------------------------------------------------------------------------

class TestUseInsight:
    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_use_existing(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.cli.insight import _load_insight_manager
        from vibecollab.domain.developer import DeveloperManager

        mgr = _load_insight_manager()
        mgr.create(title="Use Me", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            result = runner.invoke(insight, ["use", "INS-001"])

        assert result.exit_code == 0
        assert "已记录使用" in result.output
        assert "INS-001" in result.output

    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_use_not_found(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.domain.developer import DeveloperManager
        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            result = runner.invoke(insight, ["use", "INS-999"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Tests: decay
# ---------------------------------------------------------------------------

class TestDecayInsights:
    def test_decay_dry_run(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="Decay Me", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        result = runner.invoke(insight, ["decay", "--dry-run"])
        assert result.exit_code == 0
        assert "衰减预览" in result.output
        assert "INS-001" in result.output

    def test_decay_execute(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="Decay Me", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        result = runner.invoke(insight, ["decay"])
        assert result.exit_code == 0
        assert "权重衰减已执行" in result.output


# ---------------------------------------------------------------------------
# Tests: check
# ---------------------------------------------------------------------------

class TestCheckInsights:
    def test_check_clean(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="OK", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        result = runner.invoke(insight, ["check"])
        assert result.exit_code == 0
        assert "通过" in result.output or "无错误" in result.output

    def test_check_with_orphan(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="OK", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")
        # 手动在注册表中添加不存在的条目
        entries, settings = mgr.get_registry()
        from vibecollab.insight.manager import RegistryEntry
        entries["INS-999"] = RegistryEntry()
        mgr._save_registry(entries, settings)

        result = runner.invoke(insight, ["check"])
        assert result.exit_code != 0
        assert "ERROR" in result.output

    def test_check_json(self, runner, chdir_project):
        result = runner.invoke(insight, ["check", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True


# ---------------------------------------------------------------------------
# Tests: delete
# ---------------------------------------------------------------------------

class TestDeleteInsight:
    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_delete_with_yes(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.cli.insight import _load_insight_manager
        from vibecollab.domain.developer import DeveloperManager

        mgr = _load_insight_manager()
        mgr.create(title="Delete Me", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            result = runner.invoke(insight, ["delete", "INS-001", "-y"])

        assert result.exit_code == 0
        assert "已删除" in result.output
        assert mgr.get("INS-001") is None

    def test_delete_not_found(self, runner, chdir_project):
        result = runner.invoke(insight, ["delete", "INS-999", "-y"])
        assert result.exit_code != 0
        assert "未找到" in result.output


# ---------------------------------------------------------------------------
# Tests: bookmark / unbookmark
# ---------------------------------------------------------------------------

class TestBookmarkInsight:
    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_bookmark_existing(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.cli.insight import _load_insight_manager
        from vibecollab.domain.developer import DeveloperManager

        mgr = _load_insight_manager()
        mgr.create(title="Bookmark Me", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            result = runner.invoke(insight, ["bookmark", "INS-001"])

        assert result.exit_code == 0
        assert "已收藏" in result.output

    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_bookmark_duplicate(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.cli.insight import _load_insight_manager
        from vibecollab.domain.developer import DeveloperManager

        mgr = _load_insight_manager()
        mgr.create(title="Bookmark Me", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            runner.invoke(insight, ["bookmark", "INS-001"])
            result = runner.invoke(insight, ["bookmark", "INS-001"])

        assert result.exit_code == 0
        assert "已存在" in result.output

    def test_bookmark_not_found(self, runner, chdir_project):
        result = runner.invoke(insight, ["bookmark", "INS-999"])
        assert result.exit_code != 0
        assert "未找到" in result.output


class TestUnbookmarkInsight:
    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_unbookmark_existing(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.cli.insight import _load_insight_manager
        from vibecollab.domain.developer import DeveloperManager

        mgr = _load_insight_manager()
        mgr.create(title="Unbookmark Me", tags=["test"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            # First bookmark, then unbookmark
            runner.invoke(insight, ["bookmark", "INS-001"])
            result = runner.invoke(insight, ["unbookmark", "INS-001"])

        assert result.exit_code == 0
        assert "已取消收藏" in result.output

    @patch("vibecollab.cli.insight._load_developer_manager")
    def test_unbookmark_nonexistent(self, mock_dm_factory, runner, chdir_project, project_dir):
        from vibecollab.domain.developer import DeveloperManager

        dm = DeveloperManager(project_dir, yaml.safe_load(
            (project_dir / "project.yaml").read_text(encoding="utf-8")
        ))
        with patch.object(dm, "get_current_developer", return_value="testdev"):
            mock_dm_factory.return_value = dm
            result = runner.invoke(insight, ["unbookmark", "INS-999"])

        assert result.exit_code == 0
        assert "未找到收藏" in result.output


# ---------------------------------------------------------------------------
# Tests: trace
# ---------------------------------------------------------------------------

class TestTraceInsight:
    def test_trace_simple(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="Base", tags=["a"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")
        mgr.create(title="Child", tags=["b"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev",
                    derived_from=["INS-001"])

        result = runner.invoke(insight, ["trace", "INS-001"])
        assert result.exit_code == 0
        assert "溯源树" in result.output
        assert "INS-001" in result.output
        assert "INS-002" in result.output

    def test_trace_no_relations(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="Standalone", tags=["a"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        result = runner.invoke(insight, ["trace", "INS-001"])
        assert result.exit_code == 0
        assert "(无)" in result.output

    def test_trace_json(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="Base", tags=["a"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        result = runner.invoke(insight, ["trace", "INS-001", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "INS-001"

    def test_trace_not_found(self, runner, chdir_project):
        result = runner.invoke(insight, ["trace", "INS-999"])
        assert result.exit_code != 0
        assert "未找到" in result.output


# ---------------------------------------------------------------------------
# Tests: who
# ---------------------------------------------------------------------------

class TestWhoInsight:
    def test_who_basic(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="Who Test", tags=["a"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")
        mgr.record_use("INS-001", used_by="otherdev")

        result = runner.invoke(insight, ["who", "INS-001"])
        assert result.exit_code == 0
        assert "testdev" in result.output
        assert "otherdev" in result.output

    def test_who_json(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="Who Test", tags=["a"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")

        result = runner.invoke(insight, ["who", "INS-001", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["created_by"] == "testdev"

    def test_who_not_found(self, runner, chdir_project):
        result = runner.invoke(insight, ["who", "INS-999"])
        assert result.exit_code != 0
        assert "未找到" in result.output


# ---------------------------------------------------------------------------
# Tests: stats
# ---------------------------------------------------------------------------

class TestStatsInsight:
    def test_stats_empty(self, runner, chdir_project):
        result = runner.invoke(insight, ["stats"])
        assert result.exit_code == 0
        assert "共享统计" in result.output
        assert "0" in result.output

    def test_stats_with_data(self, runner, chdir_project):
        from vibecollab.cli.insight import _load_insight_manager
        mgr = _load_insight_manager()
        mgr.create(title="A", tags=["a"], category="technique",
                    body={"scenario": "s", "approach": "a"}, created_by="testdev")
        mgr.record_use("INS-001", used_by="testdev")

        result = runner.invoke(insight, ["stats"])
        assert result.exit_code == 0
        assert "1" in result.output

    def test_stats_json(self, runner, chdir_project):
        result = runner.invoke(insight, ["stats", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "summary" in data
        assert "developers" in data
        assert "insights" in data
