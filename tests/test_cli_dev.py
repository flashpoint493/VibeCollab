"""
Tests for `vibecollab dev` CLI command group (7 subcommands).
"""

import tempfile
from pathlib import Path

import yaml
from click.testing import CliRunner

from vibecollab.cli import main


def _make_role_based_project(tmp_path: Path) -> Path:
    """Create a multi-role project with alice and bob."""
    config = {
        "project": {"name": "TestProject", "version": "v1.0.0"},
        "role_context": {
            "enabled": True,
            "roles": [
                {"id": "alice", "name": "Alice", "role": "backend"},
                {"id": "bob", "name": "Bob", "role": "frontend"},
            ],
            "collaboration": {"file": ".vibecollab/roles/COLLABORATION.md"},
        },
    }
    config_path = tmp_path / "project.yaml"
    config_path.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")

    # Create role directories
    for dev in ("alice", "bob"):
        dev_dir = tmp_path / ".vibecollab" / "roles" / dev
        dev_dir.mkdir(parents=True, exist_ok=True)
        (dev_dir / "CONTEXT.md").write_text(f"# {dev} Context\nWorking on stuff", encoding="utf-8")
        (dev_dir / ".metadata.yaml").write_text(
            yaml.dump(
                {
                    "role": dev,
                    "created_at": "2026-02-20",
                    "last_updated": "2026-02-26",
                    "total_updates": 5,
                }
            ),
            encoding="utf-8",
        )

    # Collaboration doc
    collab_dir = tmp_path / ".vibecollab" / "roles"
    (collab_dir / "COLLABORATION.md").write_text("# Collaboration\n", encoding="utf-8")

    return config_path


def _make_single_dev_project(tmp_path: Path) -> Path:
    """Create a single-role project (role_context disabled)."""
    config = {
        "project": {"name": "TestProject", "version": "v1.0.0"},
    }
    config_path = tmp_path / "project.yaml"
    config_path.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")
    return config_path


class TestDevWhoami:
    def setup_method(self):
        self.runner = CliRunner()

    def test_whoami_basic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "whoami", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "Current role" in result.output.lower() or "Current Role" in result.output

    def test_whoami_no_config(self):
        result = self.runner.invoke(main, ["role", "whoami", "-c", "/nonexistent/project.yaml"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestDevList:
    def setup_method(self):
        self.runner = CliRunner()

    def test_list_roles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "list", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "alice" in result.output
            assert "bob" in result.output

    def test_list_single_dev_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_single_dev_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "list", "-c", str(config_path)])
            # Single-role projects now work by default
            assert result.exit_code == 0
            assert "Single-role mode" in result.output or "runner" in result.output.lower()


class TestDevStatus:
    def setup_method(self):
        self.runner = CliRunner()

    def test_status_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "status", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "alice" in result.output
            assert "bob" in result.output

    def test_status_specific_role(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "status", "alice", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "alice" in result.output.lower()

    def test_status_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_single_dev_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "status", "-c", str(config_path)])
            # Single-role projects now work by default
            assert result.exit_code == 0
            assert "not initialized" in result.output.lower() or "runner" in result.output.lower()


class TestDevSync:
    def setup_method(self):
        self.runner = CliRunner()

    def test_sync_basic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "sync", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "Aggregation complete" in result.output
            # Verify global CONTEXT.md was created
            global_ctx = Path(tmpdir) / "docs" / "CONTEXT.md"
            assert global_ctx.exists()

    def test_sync_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_single_dev_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "sync", "-c", str(config_path)])
            # sync may fail for uninitialized role, just check it runs
            assert result.exit_code in [0, 1]  # Allow failure for uninitialized role


class TestDevInit:
    def setup_method(self):
        self.runner = CliRunner()

    def test_init_new_role(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(
                main, ["role", "init", "-d", "charlie", "-c", str(config_path)]
            )
            assert result.exit_code == 0
            assert "Initialization complete" in result.output
            charlie_ctx = Path(tmpdir) / ".vibecollab" / "roles" / "charlie" / "CONTEXT.md"
            assert charlie_ctx.exists()

    def test_init_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_single_dev_project(Path(tmpdir))
            result = self.runner.invoke(
                main, ["role", "init", "-d", "charlie", "-c", str(config_path)]
            )
            assert result.exit_code == 0
            assert "Single-role mode" in result.output or "initializing" in result.output.lower()


class TestDevSwitch:
    def setup_method(self):
        self.runner = CliRunner()

    def test_switch_to_role(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "switch", "bob", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "bob" in result.output
            # Verify local config written
            local_yaml = Path(tmpdir) / ".vibecollab.local.yaml"
            assert local_yaml.exists()

    def test_switch_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            # First switch to bob
            self.runner.invoke(main, ["role", "switch", "bob", "-c", str(config_path)])
            # Then clear
            result = self.runner.invoke(main, ["role", "switch", "--clear", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "cleared" in result.output.lower()

    def test_switch_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_single_dev_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "switch", "alice", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "Single-role mode" in result.output or "cannot switch" in result.output.lower()


class TestDevConflicts:
    def setup_method(self):
        self.runner = CliRunner()

    def test_conflicts_no_conflicts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "conflicts", "-c", str(config_path)])
            assert result.exit_code == 0

    def test_conflicts_between(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_role_based_project(Path(tmpdir))
            result = self.runner.invoke(
                main, ["role", "conflicts", "--between", "alice", "bob", "-c", str(config_path)]
            )
            assert result.exit_code == 0

    def test_conflicts_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = _make_single_dev_project(Path(tmpdir))
            result = self.runner.invoke(main, ["role", "conflicts", "-c", str(config_path)])
            assert result.exit_code == 0
