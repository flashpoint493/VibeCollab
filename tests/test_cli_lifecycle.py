"""Tests for cli_lifecycle commands."""


import pytest
import yaml
from click.testing import CliRunner

from vibecollab.cli_lifecycle import lifecycle


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def config_file(tmp_path):
    """Create a temporary project.yaml for lifecycle tests."""
    config = {
        "lifecycle": {
            "current_stage": "demo",
            "stage_history": [
                {"stage": "demo", "started_at": "2026-01-01"}
            ],
        }
    }
    path = tmp_path / "project.yaml"
    path.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")
    return path


class TestCheck:
    def test_check_basic(self, runner, config_file):
        result = runner.invoke(lifecycle, ["check", "-c", str(config_file)])
        assert result.exit_code == 0
        assert "原型验证" in result.output
        assert "demo" in result.output

    def test_check_shows_upgrade_option(self, runner, config_file):
        result = runner.invoke(lifecycle, ["check", "-c", str(config_file)])
        assert result.exit_code == 0
        assert "升级" in result.output

    def test_check_shows_history(self, runner, config_file):
        result = runner.invoke(lifecycle, ["check", "-c", str(config_file)])
        assert "demo" in result.output
        assert "2026-01-01" in result.output

    def test_check_missing_config(self, runner):
        result = runner.invoke(lifecycle, ["check", "-c", "nonexistent.yaml"])
        assert result.exit_code == 1

    def test_check_with_milestones(self, runner, tmp_path):
        config = {
            "lifecycle": {
                "current_stage": "demo",
                "stages": {
                    "demo": {
                        "name": "原型验证",
                        "description": "验证概念",
                        "focus": ["核心"],
                        "principles": ["快速"],
                        "milestones": [
                            {"name": "M1", "completed": True},
                            {"name": "M2", "completed": False},
                        ],
                    }
                },
                "stage_history": [],
            }
        }
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")
        result = runner.invoke(lifecycle, ["check", "-c", str(path)])
        assert result.exit_code == 0
        assert "1/2" in result.output or "里程碑" in result.output

    def test_check_cannot_upgrade(self, runner, tmp_path):
        config = {
            "lifecycle": {
                "current_stage": "stable",
                "stage_history": [],
            }
        }
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")
        result = runner.invoke(lifecycle, ["check", "-c", str(path)])
        assert result.exit_code == 0
        assert "暂不能" in result.output or "最后阶段" in result.output


class TestUpgrade:
    def test_upgrade_default(self, runner, config_file):
        result = runner.invoke(lifecycle, ["upgrade", "-c", str(config_file)])
        assert result.exit_code == 0
        assert "升级成功" in result.output or "量产" in result.output

        # Verify config was updated
        updated = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        assert updated["lifecycle"]["current_stage"] == "production"

    def test_upgrade_specific_stage(self, runner, config_file):
        result = runner.invoke(lifecycle, ["upgrade", "-c", str(config_file), "-s", "production"])
        assert result.exit_code == 0

    def test_upgrade_missing_config(self, runner):
        result = runner.invoke(lifecycle, ["upgrade", "-c", "nonexistent.yaml"])
        assert result.exit_code == 1

    def test_upgrade_already_last_stage(self, runner, tmp_path):
        config = {"lifecycle": {"current_stage": "stable", "stage_history": []}}
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")
        result = runner.invoke(lifecycle, ["upgrade", "-c", str(path)])
        assert result.exit_code == 1

    def test_upgrade_shows_suggestions(self, runner, config_file):
        result = runner.invoke(lifecycle, ["upgrade", "-c", str(config_file)])
        assert result.exit_code == 0
        # Should show next steps
        assert "下一步" in result.output or "vibecollab" in result.output
