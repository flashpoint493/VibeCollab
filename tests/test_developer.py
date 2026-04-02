"""
RoleManager + ContextAggregator + migrate_to_role_context unit tests
"""

import os
from unittest.mock import patch

import pytest
import yaml

from vibecollab.domain.role import (
    LOCAL_CONFIG_FILE,
    ContextAggregator,
    RoleManager,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _base_config(
    enabled=True,
    primary="git_username",
    fallback="system_user",
    normalize=True,
    per_role_dir="docs/roles",
    metadata_file=".metadata.yaml",
    aggregation_file="docs/CONTEXT.md",
    collaboration_file="docs/roles/COLLABORATION.md",
):
    """Build a minimal usable multi-role config"""
    return {
        "project": {"name": "TestProject", "version": "v1.0.0"},
        "role_context": {
            "enabled": enabled,
            "identity": {
                "primary": primary,
                "fallback": fallback,
                "normalize": normalize,
            },
            "context": {
                "per_role_dir": per_role_dir,
                "metadata_file": metadata_file,
                "aggregation_file": aggregation_file,
            },
            "collaboration": {
                "enabled": True,
                "file": collaboration_file,
            },
        },
    }


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory"""
    (tmp_path / "docs" / "roles").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def config():
    return _base_config()


@pytest.fixture
def dm(project_dir, config):
    return RoleManager(project_dir, config)


# ===========================================================================
# RoleManager — Initialization
# ===========================================================================


class TestRoleManagerInit:
    def test_enabled_flag(self, project_dir):
        mgr = RoleManager(project_dir, _base_config(enabled=True))
        assert mgr.enabled is True

    def test_disabled_flag(self, project_dir):
        mgr = RoleManager(project_dir, _base_config(enabled=False))
        assert mgr.enabled is False

    def test_roles_dir_path(self, project_dir, config):
        mgr = RoleManager(project_dir, config)
        assert mgr.roles_dir == project_dir / "docs" / "roles"

    def test_custom_roles_dir(self, project_dir):
        cfg = _base_config(per_role_dir="custom/devs")
        mgr = RoleManager(project_dir, cfg)
        assert mgr.roles_dir == project_dir / "custom" / "devs"

    def test_empty_config(self, project_dir):
        mgr = RoleManager(project_dir, {})
        assert mgr.enabled is False


# ===========================================================================
# RoleManager — Name normalization
# ===========================================================================


class TestNormalizeName:
    def test_lowercase(self, dm):
        assert dm._normalize_role_name("Alice") == "alice"

    def test_spaces_to_underscore(self, dm):
        assert dm._normalize_role_name("John Doe") == "john_doe"

    def test_special_chars_removed(self, dm):
        assert dm._normalize_role_name("dev@#$123") == "dev123"

    def test_mixed(self, dm):
        assert dm._normalize_role_name("Bob The-Builder!") == "bob_thebuilder"

    def test_unicode_stripped(self, dm):
        assert dm._normalize_role_name("开发者A") == "a"

    def test_empty_string(self, dm):
        assert dm._normalize_role_name("") == ""

    def test_already_normalized(self, dm):
        assert dm._normalize_role_name("ocarina") == "ocarina"


# ===========================================================================
# RoleManager — Identity detection
# ===========================================================================


class TestGetCurrentRole:
    def test_local_config_takes_priority(self, project_dir, config):
        local_cfg = project_dir / LOCAL_CONFIG_FILE
        local_cfg.write_text("current_role: alice\n", encoding="utf-8")
        mgr = RoleManager(project_dir, config)
        assert mgr.get_current_role() == "alice"

    def test_env_var_over_git(self, project_dir, config):
        with patch.dict(os.environ, {"VIBECOLLAB_ROLE": "EnvDev"}):
            mgr = RoleManager(project_dir, config)
            assert mgr.get_current_role() == "envdev"  # normalized

    @patch("vibecollab.domain.role.RoleManager._get_git_username", return_value="GitUser")
    def test_git_username_primary(self, mock_git, project_dir, config):
        mgr = RoleManager(project_dir, config)
        assert mgr.get_current_role() == "gituser"

    @patch("vibecollab.domain.role.RoleManager._get_git_username", return_value=None)
    @patch("vibecollab.domain.role.RoleManager._get_system_user", return_value="SysUser")
    def test_fallback_to_system_user(self, mock_sys, mock_git, project_dir, config):
        mgr = RoleManager(project_dir, config)
        assert mgr.get_current_role() == "sysuser"

    @patch("vibecollab.domain.role.RoleManager._get_git_username", return_value=None)
    @patch("vibecollab.domain.role.RoleManager._get_system_user", return_value=None)
    def test_final_fallback_unknown(self, mock_sys, mock_git, project_dir, config):
        mgr = RoleManager(project_dir, config)
        assert mgr.get_current_role() == "unknown_role"

    def test_system_user_primary(self, project_dir):
        cfg = _base_config(primary="system_user", fallback="git_username")
        # Mock both USER (Linux) and USERNAME (Windows) to ensure cross-platform
        env_override = {"USER": "WinUser", "USERNAME": "WinUser"}
        with patch.dict(os.environ, env_override, clear=False):
            mgr = RoleManager(project_dir, cfg)
            assert mgr.get_current_role() == "winuser"

    def test_no_normalize(self, project_dir):
        cfg = _base_config(normalize=False)
        with patch.dict(os.environ, {"VIBECOLLAB_ROLE": "MixedCase"}):
            mgr = RoleManager(project_dir, cfg)
            assert mgr.get_current_role() == "MixedCase"

    def test_manual_primary_uses_env(self, project_dir):
        cfg = _base_config(primary="manual")
        with patch.dict(os.environ, {"VIBECOLLAB_ROLE": "ManualDev"}):
            mgr = RoleManager(project_dir, cfg)
            assert mgr.get_current_role() == "manualdev"


# ===========================================================================
# RoleManager — Identity source
# ===========================================================================


class TestGetIdentitySource:
    def test_local_switch_source(self, project_dir, config):
        local_cfg = project_dir / LOCAL_CONFIG_FILE
        local_cfg.write_text("current_role: alice\n", encoding="utf-8")
        mgr = RoleManager(project_dir, config)
        assert mgr.get_identity_source() == "local_switch"

    def test_env_var_source(self, project_dir, config):
        with patch.dict(os.environ, {"VIBECOLLAB_ROLE": "test"}):
            mgr = RoleManager(project_dir, config)
            assert mgr.get_identity_source() == "env_var"

    def test_default_source(self, project_dir, config):
        mgr = RoleManager(project_dir, config)
        assert mgr.get_identity_source() == "git_username"

    def test_custom_primary_source(self, project_dir):
        cfg = _base_config(primary="system_user")
        mgr = RoleManager(project_dir, cfg)
        assert mgr.get_identity_source() == "system_user"


# ===========================================================================
# RoleManager — switch / clear
# ===========================================================================


class TestSwitchRole:
    def test_switch_creates_local_config(self, dm, project_dir):
        assert dm.switch_role("bob") is True
        local_cfg = project_dir / LOCAL_CONFIG_FILE
        assert local_cfg.exists()
        data = yaml.safe_load(local_cfg.read_text(encoding="utf-8"))
        assert data["current_role"] == "bob"
        assert "switched_at" in data

    def test_switch_normalizes_name(self, dm, project_dir):
        dm.switch_role("Alice Bob")
        data = yaml.safe_load((project_dir / LOCAL_CONFIG_FILE).read_text(encoding="utf-8"))
        assert data["current_role"] == "alice_bob"

    def test_switch_overwrites_existing(self, dm, project_dir):
        dm.switch_role("alice")
        dm.switch_role("bob")
        data = yaml.safe_load((project_dir / LOCAL_CONFIG_FILE).read_text(encoding="utf-8"))
        assert data["current_role"] == "bob"

    def test_clear_removes_role(self, dm, project_dir):
        dm.switch_role("alice")
        assert dm.clear_switch() is True
        local_cfg = project_dir / LOCAL_CONFIG_FILE
        assert not local_cfg.exists()  # empty config => file deleted

    def test_clear_no_file(self, dm):
        assert dm.clear_switch() is True

    def test_clear_preserves_other_keys(self, dm, project_dir):
        local_cfg = project_dir / LOCAL_CONFIG_FILE
        local_cfg.write_text(
            "current_role: alice\nswitched_at: '2026-01-01'\nextra_key: value\n", encoding="utf-8"
        )
        dm.clear_switch()
        data = yaml.safe_load(local_cfg.read_text(encoding="utf-8"))
        assert "current_role" not in data
        assert data["extra_key"] == "value"


# ===========================================================================
# RoleManager — Directories and file paths
# ===========================================================================


class TestPaths:
    @patch("vibecollab.domain.role.RoleManager._get_git_username", return_value="testdev")
    def test_role_dir(self, mock_git, dm, project_dir):
        assert dm.get_role_dir("alice") == project_dir / "docs" / "roles" / "alice"

    @patch("vibecollab.domain.role.RoleManager._get_git_username", return_value="testdev")
    def test_role_dir_default(self, mock_git, dm, project_dir):
        assert dm.get_role_dir() == project_dir / "docs" / "roles" / "testdev"

    def test_context_file(self, dm, project_dir):
        assert (
            dm.get_role_context_file("alice")
            == project_dir / "docs" / "roles" / "alice" / "CONTEXT.md"
        )

    def test_metadata_file(self, dm, project_dir):
        assert (
            dm.get_role_metadata_file("alice")
            == project_dir / "docs" / "roles" / "alice" / ".metadata.yaml"
        )

    def test_custom_metadata_filename(self, project_dir):
        cfg = _base_config(metadata_file="meta.yml")
        mgr = RoleManager(project_dir, cfg)
        assert mgr.get_role_metadata_file("alice").name == "meta.yml"


# ===========================================================================
# RoleManager — List, create, initialize
# ===========================================================================


class TestListAndInit:
    def test_list_empty(self, dm):
        assert dm.list_roles() == []

    def test_list_with_roles(self, dm, project_dir):
        (project_dir / "docs" / "roles" / "alice").mkdir()
        (project_dir / "docs" / "roles" / "bob").mkdir()
        assert dm.list_roles() == ["alice", "bob"]

    def test_list_ignores_dotdirs(self, dm, project_dir):
        (project_dir / "docs" / "roles" / ".hidden").mkdir()
        (project_dir / "docs" / "roles" / "alice").mkdir()
        assert dm.list_roles() == ["alice"]

    def test_list_ignores_files(self, dm, project_dir):
        (project_dir / "docs" / "roles" / "COLLABORATION.md").write_text("x", encoding="utf-8")
        (project_dir / "docs" / "roles" / "alice").mkdir()
        assert dm.list_roles() == ["alice"]

    def test_list_nonexistent_dir(self, project_dir, config):
        cfg = _base_config(per_role_dir="nonexistent/dir")
        mgr = RoleManager(project_dir, cfg)
        assert mgr.list_roles() == []

    def test_ensure_role_dir(self, dm, project_dir):
        path = dm.ensure_role_dir("newdev")
        assert path.exists()
        assert path == project_dir / "docs" / "roles" / "newdev"

    def test_ensure_role_dir_idempotent(self, dm):
        dm.ensure_role_dir("alice")
        dm.ensure_role_dir("alice")  # should not raise

    def test_init_role_context(self, dm, project_dir):
        dm.init_role_context("alice")
        ctx = dm.get_role_context_file("alice")
        meta = dm.get_role_metadata_file("alice")
        assert ctx.exists()
        assert meta.exists()
        content = ctx.read_text(encoding="utf-8")
        assert "alice" in content
        assert "TestProject" in content

    def test_init_no_overwrite(self, dm, project_dir):
        dm.init_role_context("alice")
        ctx = dm.get_role_context_file("alice")
        ctx.write_text("custom content", encoding="utf-8")
        dm.init_role_context("alice")  # force=False by default
        assert ctx.read_text(encoding="utf-8") == "custom content"

    def test_init_force_overwrite(self, dm, project_dir):
        dm.init_role_context("alice")
        ctx = dm.get_role_context_file("alice")
        ctx.write_text("custom content", encoding="utf-8")
        dm.init_role_context("alice", force=True)
        assert "custom content" not in ctx.read_text(encoding="utf-8")
        assert "alice" in ctx.read_text(encoding="utf-8")


# ===========================================================================
# RoleManager — Metadata
# ===========================================================================


class TestMetadata:
    def test_update_metadata_creates(self, dm, project_dir):
        dm.ensure_role_dir("alice")
        dm.update_metadata("alice")
        meta = dm.get_role_metadata_file("alice")
        data = yaml.safe_load(meta.read_text(encoding="utf-8"))
        assert data["role"] == "alice"
        assert data["total_updates"] == 1
        assert "last_updated" in data

    def test_update_metadata_increments(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.update_metadata("alice")
        dm.update_metadata("alice")
        meta = dm.get_role_metadata_file("alice")
        data = yaml.safe_load(meta.read_text(encoding="utf-8"))
        assert data["total_updates"] == 2

    def test_get_role_status(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.update_metadata("alice")
        status = dm.get_role_status("alice")
        assert status["role"] == "alice"
        assert status["exists"] is True
        assert status["total_updates"] >= 1
        assert status["last_updated"] is not None

    def test_get_status_nonexistent(self, dm):
        status = dm.get_role_status("nobody")
        assert status["exists"] is False
        assert status["total_updates"] == 0
        assert status["last_updated"] is None


# ===========================================================================
# ContextAggregator
# ===========================================================================


class TestContextAggregator:
    def test_aggregate_no_roles(self, project_dir, config):
        agg = ContextAggregator(project_dir, config)
        content = agg.aggregate()
        assert "TestProject" in content
        assert "(no roles)" in content

    def test_aggregate_with_roles(self, project_dir, config):
        dm = RoleManager(project_dir, config)
        dm.init_role_context("alice")
        dm.init_role_context("bob")
        agg = ContextAggregator(project_dir, config)
        content = agg.aggregate()
        assert "alice" in content
        assert "bob" in content
        assert "Active roles" in content
        assert "2" in content

    def test_aggregate_extracts_current_task(self, project_dir, config):
        dm = RoleManager(project_dir, config)
        dm.init_role_context("alice")
        ctx = dm.get_role_context_file("alice")
        ctx.write_text(
            "# TestProject\n\n## 当前任务\n- **TASK-DEV-001**: 实现经验系统\n\n## 其他\n",
            encoding="utf-8",
        )
        agg = ContextAggregator(project_dir, config)
        content = agg.aggregate()
        assert "TASK-DEV-001" in content

    def test_aggregate_extracts_update_time(self, project_dir, config):
        dm = RoleManager(project_dir, config)
        dm.init_role_context("alice")
        ctx = dm.get_role_context_file("alice")
        ctx.write_text(
            "# TestProject\n\n## 当前状态\n- **上次更新**: 2026-02-25 10:00:00\n\n## 当前任务\n无\n",
            encoding="utf-8",
        )
        agg = ContextAggregator(project_dir, config)
        content = agg.aggregate()
        assert "2026-02-25 10:00:00" in content

    def test_aggregate_merges_tech_debts(self, project_dir, config):
        dm = RoleManager(project_dir, config)
        dm.init_role_context("alice")
        dm.init_role_context("bob")
        alice_ctx = dm.get_role_context_file("alice")
        bob_ctx = dm.get_role_context_file("bob")
        alice_ctx.write_text(
            "# P\n\n## 技术债务\n- 需要重构 CLI\n\n---\n",
            encoding="utf-8",
        )
        bob_ctx.write_text(
            "# P\n\n## 技术债务\n- 补充 E2E 测试\n\n---\n",
            encoding="utf-8",
        )
        agg = ContextAggregator(project_dir, config)
        content = agg.aggregate()
        assert "[alice]" in content
        assert "[bob]" in content
        assert "重构 CLI" in content
        assert "E2E 测试" in content

    def test_aggregate_collaboration_info(self, project_dir, config):
        collab_file = project_dir / "docs" / "roles" / "COLLABORATION.md"
        collab_file.write_text("# Collaboration\n## 协作\n", encoding="utf-8")
        dm = RoleManager(project_dir, config)
        dm.init_role_context("alice")
        agg = ContextAggregator(project_dir, config)
        content = agg.aggregate()
        assert "COLLABORATION.md" in content

    def test_aggregate_no_collaboration_file(self, project_dir, config):
        dm = RoleManager(project_dir, config)
        dm.init_role_context("alice")
        agg = ContextAggregator(project_dir, config)
        content = agg.aggregate()
        assert "COLLABORATION" not in content or "Cross-role collaboration" not in content

    def test_generate_and_save(self, project_dir, config):
        dm = RoleManager(project_dir, config)
        dm.init_role_context("alice")
        agg = ContextAggregator(project_dir, config)
        output = agg.generate_and_save()
        # v0.12.0+: Returns YAML path (source of truth), Markdown is a generated view
        assert output.exists()
        assert output == project_dir / "docs" / "context.yaml"
        # Verify YAML content
        content = output.read_text(encoding="utf-8")
        assert "alice" in content
        # Verify Markdown view is also generated
        md_output = project_dir / "docs" / "CONTEXT.md"
        assert md_output.exists()


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    def test_corrupt_local_config(self, project_dir, config):
        local_cfg = project_dir / LOCAL_CONFIG_FILE
        local_cfg.write_text("{{invalid yaml::", encoding="utf-8")
        mgr = RoleManager(project_dir, config)
        # Should not crash, falls back to other strategy
        dev = mgr.get_current_role()
        assert isinstance(dev, str)

    def test_corrupt_metadata_file(self, dm, project_dir):
        dm.ensure_role_dir("alice")
        meta = dm.get_role_metadata_file("alice")
        meta.write_text("{{broken yaml", encoding="utf-8")
        # update_metadata raises exception when reading corrupted YAML
        with pytest.raises(yaml.YAMLError):
            dm.update_metadata("alice")

    def test_context_file_unicode(self, dm, project_dir):
        dm.init_role_context("alice")
        ctx = dm.get_role_context_file("alice")
        ctx.write_text(
            "# 项目\n\n## 当前任务\n- 中文任务描述\n\n## 技术债务\n- 需要处理 Unicode 边界\n",
            encoding="utf-8",
        )
        agg = ContextAggregator(project_dir, _base_config())
        content = agg.aggregate()
        assert "中文任务描述" in content

    def test_empty_context_file(self, dm, project_dir):
        dm.ensure_role_dir("alice")
        ctx = dm.get_role_context_file("alice")
        ctx.write_text("", encoding="utf-8")
        agg = ContextAggregator(project_dir, _base_config())
        content = agg.aggregate()
        assert "alice" in content  # role still listed

    def test_sorted_roles(self, dm, project_dir):
        for name in ["charlie", "alice", "bob"]:
            (project_dir / "docs" / "roles" / name).mkdir()
        assert dm.list_roles() == ["alice", "bob", "charlie"]


# ===========================================================================
# RoleManager — Tag system extension
# ===========================================================================


class TestRoleTags:
    def test_get_tags_empty(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.get_tags("alice") == []

    def test_set_tags(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.set_tags(["arch", "python", "test-first"], "alice")
        assert dm.get_tags("alice") == ["arch", "python", "test-first"]

    def test_set_tags_overwrites(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.set_tags(["arch"], "alice")
        dm.set_tags(["python"], "alice")
        assert dm.get_tags("alice") == ["python"]

    def test_add_tag(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.add_tag("arch", "alice") is True
        assert dm.add_tag("python", "alice") is True
        assert dm.get_tags("alice") == ["arch", "python"]

    def test_add_tag_duplicate(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.add_tag("arch", "alice")
        assert dm.add_tag("arch", "alice") is False
        assert dm.get_tags("alice") == ["arch"]

    def test_remove_tag(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.set_tags(["arch", "python"], "alice")
        assert dm.remove_tag("arch", "alice") is True
        assert dm.get_tags("alice") == ["python"]

    def test_remove_tag_nonexistent(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.remove_tag("nonexistent", "alice") is False

    def test_tags_preserve_other_metadata(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.update_metadata("alice")
        dm.set_tags(["arch"], "alice")
        meta_file = dm.get_role_metadata_file("alice")
        data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert data["tags"] == ["arch"]
        assert data["role"] == "alice"
        assert "total_updates" in data


class TestRoleContributed:
    def test_get_contributed_empty(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.get_contributed("alice") == []

    def test_add_contributed(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.add_contributed("INS-001", "alice") is True
        assert dm.add_contributed("INS-002", "alice") is True
        assert dm.get_contributed("alice") == ["INS-001", "INS-002"]

    def test_add_contributed_duplicate(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.add_contributed("INS-001", "alice")
        assert dm.add_contributed("INS-001", "alice") is False
        assert dm.get_contributed("alice") == ["INS-001"]

    def test_remove_contributed(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.add_contributed("INS-001", "alice")
        dm.add_contributed("INS-002", "alice")
        assert dm.remove_contributed("INS-001", "alice") is True
        assert dm.get_contributed("alice") == ["INS-002"]

    def test_remove_contributed_nonexistent(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.remove_contributed("INS-999", "alice") is False


class TestRoleBookmarks:
    def test_get_bookmarks_empty(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.get_bookmarks("alice") == []

    def test_add_bookmark(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.add_bookmark("INS-001", "alice") is True
        assert dm.add_bookmark("INS-003", "alice") is True
        assert dm.get_bookmarks("alice") == ["INS-001", "INS-003"]

    def test_add_bookmark_duplicate(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.add_bookmark("INS-001", "alice")
        assert dm.add_bookmark("INS-001", "alice") is False
        assert dm.get_bookmarks("alice") == ["INS-001"]

    def test_remove_bookmark(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.add_bookmark("INS-001", "alice")
        dm.add_bookmark("INS-002", "alice")
        assert dm.remove_bookmark("INS-001", "alice") is True
        assert dm.get_bookmarks("alice") == ["INS-002"]

    def test_remove_bookmark_nonexistent(self, dm, project_dir):
        dm.init_role_context("alice")
        assert dm.remove_bookmark("INS-999", "alice") is False


class TestMetadataReadWrite:
    def test_read_metadata_no_file(self, dm, project_dir):
        assert dm._read_metadata("nonexistent") == {}

    def test_write_metadata_creates_dir(self, dm, project_dir):
        dm._write_metadata({"role": "newdev", "tags": ["test"]}, "newdev")
        meta_file = dm.get_role_metadata_file("newdev")
        assert meta_file.exists()
        data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert data["tags"] == ["test"]

    def test_combined_fields(self, dm, project_dir):
        dm.init_role_context("alice")
        dm.set_tags(["arch", "python"], "alice")
        dm.add_contributed("INS-001", "alice")
        dm.add_bookmark("INS-002", "alice")
        meta_file = dm.get_role_metadata_file("alice")
        data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
        assert data["tags"] == ["arch", "python"]
        assert data["contributed"] == ["INS-001"]
        assert data["bookmarks"] == ["INS-002"]
        assert data["role"] == "alice"
