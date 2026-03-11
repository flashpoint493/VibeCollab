"""
Supplementary tests for protocol_checker.py — Git-related and branch coverage gaps.

Covers uncovered lines: 89, 114-121, 131, 145, 174, 196, 228, 275, 288, 345,
403-408, 417, 545-619, 629-686, 700-709, 714, 726-727
"""

import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from vibecollab.core.protocol_checker import ProtocolChecker

# ============================================================
# Helper: create git repo
# ============================================================

def _git_init(project_root: Path):
    """Initialize a git repo with initial commit."""
    subprocess.run(["git", "init"], cwd=project_root, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_root, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=project_root, capture_output=True)
    # Initial commit
    (project_root / "README.md").write_text("init", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=project_root, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project_root, capture_output=True, check=True)


def _base_config(**overrides):
    """Create a minimal config dict."""
    cfg = {
        "dialogue_protocol": {
            "on_end": {"update_files": []},
            "on_start": {"read_files": []},
        },
    }
    cfg.update(overrides)
    return cfg


# ============================================================
# _check_documentation_protocol gaps
# ============================================================


class TestDocProtocol:
    def test_update_file_not_exists(self, tmp_path):
        """Line 114-121: update_files references a non-existent file."""
        config = _base_config()
        config["dialogue_protocol"]["on_end"]["update_files"] = ["docs/CONTEXT.md"]
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_documentation_protocol()
        errors = [r for r in results if "Doc Existence" in r.name]
        assert len(errors) == 1
        assert errors[0].severity == "error"
        assert "CONTEXT.md" in errors[0].message

    def test_threshold_hours_format(self, tmp_path):
        """Line 131: threshold >= 1 hour shows 'hours' instead of 'minutes'."""
        (tmp_path / "docs").mkdir()
        ctx = tmp_path / "docs" / "CONTEXT.md"
        ctx.write_text("old", encoding="utf-8")
        # Set mtime to 3 hours ago
        old_time = time.time() - 3 * 3600
        os.utime(ctx, (old_time, old_time))

        config = _base_config()
        config["dialogue_protocol"]["on_end"]["update_files"] = ["docs/CONTEXT.md"]
        config["protocol_check"] = {"checks": {"documentation": {"update_threshold_hours": 2}}}
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_documentation_protocol()
        warnings = [r for r in results if "Doc Update" in r.name]
        assert len(warnings) == 1
        assert "hours" in warnings[0].message

    def test_prd_enabled_but_missing(self, tmp_path):
        """Line 145: PRD management enabled but PRD.md doesn't exist."""
        config = _base_config()
        config["prd_management"] = {"enabled": True, "prd_file": "docs/PRD.md"}
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_documentation_protocol()
        prd_results = [r for r in results if "PRD" in r.name]
        assert len(prd_results) == 1
        assert prd_results[0].severity == "warning"

    def test_collab_doc_stale(self, tmp_path):
        """Line 174: collaboration doc exists but > 7 days old."""
        (tmp_path / "docs" / "developers").mkdir(parents=True)
        collab = tmp_path / "docs" / "developers" / "COLLABORATION.md"
        collab.write_text("old collab", encoding="utf-8")
        old_time = time.time() - 8 * 86400
        os.utime(collab, (old_time, old_time))

        config = _base_config()
        config["multi_developer"] = {
            "enabled": True,
            "collaboration": {"file": "docs/developers/COLLABORATION.md"},
        }
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_documentation_protocol()
        stale = [r for r in results if "Collaboration Doc Update" in r.name]
        assert len(stale) == 1
        assert stale[0].severity == "info"


# ============================================================
# _check_dialogue_protocol gaps
# ============================================================


class TestDialogueProtocol:
    def test_read_file_not_exists(self, tmp_path):
        """Line 196: on_start read_files references missing file."""
        config = _base_config()
        config["dialogue_protocol"]["on_start"]["read_files"] = ["CONTRIBUTING_AI.md"]
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_dialogue_protocol()
        errors = [r for r in results if "Dialogue Start File" in r.name]
        assert len(errors) == 1
        assert errors[0].severity == "error"


# ============================================================
# _check_multi_developer_protocol gaps
# ============================================================


class TestMultiDevProtocol:
    def test_discover_developers_from_fs(self, tmp_path):
        """Line 228: dynamic developer discovery from filesystem."""
        dev_dir = tmp_path / "docs" / "developers" / "alice"
        dev_dir.mkdir(parents=True)
        (dev_dir / "CONTEXT.md").write_text("# Alice", encoding="utf-8")
        (dev_dir / ".metadata.yaml").write_text("id: alice", encoding="utf-8")

        config = _base_config()
        config["multi_developer"] = {
            "enabled": True,
            "developers": [],  # empty → trigger filesystem discovery
            "collaboration": {"file": "docs/developers/COLLABORATION.md"},
        }
        # Create COLLABORATION.md
        (tmp_path / "docs" / "developers" / "COLLABORATION.md").write_text("collab", encoding="utf-8")

        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_multi_developer_protocol()
        # Should have found alice via fs
        alice_results = [r for r in results if "alice" in r.message.lower() or "alice" in r.name.lower()]
        assert len(alice_results) > 0

    def test_context_md_missing(self, tmp_path):
        """Line 275: developer dir exists but CONTEXT.md doesn't."""
        dev_dir = tmp_path / "docs" / "developers" / "bob"
        dev_dir.mkdir(parents=True)
        # No CONTEXT.md

        config = _base_config()
        config["multi_developer"] = {
            "enabled": True,
            "developers": [{"id": "bob", "name": "Bob"}],
            "collaboration": {"file": "docs/developers/COLLABORATION.md"},
        }
        (tmp_path / "docs" / "developers" / "COLLABORATION.md").write_text("c", encoding="utf-8")

        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_multi_developer_protocol()
        ctx_missing = [r for r in results if "CONTEXT.md does not exist" in r.message]
        assert len(ctx_missing) == 1
        assert ctx_missing[0].severity == "error"

    def test_context_md_stale(self, tmp_path):
        """Line 288: developer CONTEXT.md > 7 days old."""
        dev_dir = tmp_path / "docs" / "developers" / "alice"
        dev_dir.mkdir(parents=True)
        ctx = dev_dir / "CONTEXT.md"
        ctx.write_text("# Alice", encoding="utf-8")
        (dev_dir / ".metadata.yaml").write_text("id: alice", encoding="utf-8")
        old_time = time.time() - 10 * 86400
        os.utime(ctx, (old_time, old_time))

        config = _base_config()
        config["multi_developer"] = {
            "enabled": True,
            "developers": [{"id": "alice", "name": "Alice"}],
            "collaboration": {"file": "docs/developers/COLLABORATION.md"},
        }
        (tmp_path / "docs" / "developers" / "COLLABORATION.md").write_text("c", encoding="utf-8")

        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_multi_developer_protocol()
        stale = [r for r in results if "days" in r.message and "alice" in r.message.lower()]
        assert len(stale) == 1
        assert stale[0].severity == "info"

    def test_collab_doc_stale_in_multi_dev(self, tmp_path):
        """Line 345: collaboration doc > 7 days in multi-dev check."""
        dev_dir = tmp_path / "docs" / "developers" / "alice"
        dev_dir.mkdir(parents=True)
        (dev_dir / "CONTEXT.md").write_text("# Alice", encoding="utf-8")
        (dev_dir / ".metadata.yaml").write_text("id: alice", encoding="utf-8")

        collab = tmp_path / "docs" / "developers" / "COLLABORATION.md"
        collab.write_text("old collab", encoding="utf-8")
        old_time = time.time() - 10 * 86400
        os.utime(collab, (old_time, old_time))

        config = _base_config()
        config["multi_developer"] = {
            "enabled": True,
            "developers": [{"id": "alice", "name": "Alice"}],
            "collaboration": {"file": "docs/developers/COLLABORATION.md"},
        }

        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_multi_developer_protocol()
        stale = [r for r in results if "Collaboration Doc Update Frequency" in r.name]
        assert len(stale) == 1
        assert stale[0].severity == "info"


# ============================================================
# _check_document_consistency — level dispatch
# ============================================================


class TestDocConsistency:
    def test_git_commit_level_dispatch(self, tmp_path):
        """Lines 403-406: git_commit level is dispatched correctly."""
        config = _base_config()
        config["documentation"] = {
            "consistency": {
                "enabled": True,
                "linked_groups": [
                    {
                        "name": "test-group",
                        "files": ["a.md", "b.md"],
                        "level": "git_commit",
                    }
                ],
            }
        }
        # Not a git repo, so _check_git_commit_consistency returns []
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_document_consistency()
        # Should not crash, returns empty since not a git repo
        assert isinstance(results, list)

    def test_release_level_dispatch(self, tmp_path):
        """Lines 407-410: release level is dispatched correctly."""
        config = _base_config()
        config["documentation"] = {
            "consistency": {
                "enabled": True,
                "linked_groups": [
                    {
                        "name": "release-group",
                        "files": ["a.md", "b.md"],
                        "level": "release",
                    }
                ],
            }
        }
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_document_consistency()
        assert isinstance(results, list)

    def test_key_files_empty_path(self, tmp_path):
        """Line 417: key_files with empty path is skipped."""
        config = _base_config()
        config["documentation"] = {
            "consistency": {"enabled": True, "linked_groups": []},
            "key_files": [{"path": "", "description": "empty"}],
        }
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_document_consistency()
        assert isinstance(results, list)


# ============================================================
# Git-backed tests: _check_git_commit_consistency
# ============================================================


class TestGitCommitConsistency:
    def test_same_commit(self, tmp_path):
        """Files modified in same commit → no warning."""
        _git_init(tmp_path)
        (tmp_path / "a.md").write_text("a", encoding="utf-8")
        (tmp_path / "b.md").write_text("b", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add both"], cwd=tmp_path, capture_output=True, check=True)

        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_git_commit_consistency("test", ["a.md", "b.md"])
        assert len(results) == 0

    def test_different_commits(self, tmp_path):
        """Files in different commits → warning."""
        _git_init(tmp_path)
        (tmp_path / "a.md").write_text("a", encoding="utf-8")
        subprocess.run(["git", "add", "a.md"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add a"], cwd=tmp_path, capture_output=True, check=True)

        (tmp_path / "b.md").write_text("b", encoding="utf-8")
        subprocess.run(["git", "add", "b.md"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add b"], cwd=tmp_path, capture_output=True, check=True)

        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_git_commit_consistency("test", ["a.md", "b.md"])
        warnings = [r for r in results if r.severity == "warning"]
        assert len(warnings) >= 1
        assert "not in the same commit" in warnings[0].message

    def test_not_git_repo(self, tmp_path):
        """Non-git directory returns empty."""
        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_git_commit_consistency("test", ["a.md", "b.md"])
        assert results == []

    def test_file_not_exists(self, tmp_path):
        """Missing file is skipped gracefully."""
        _git_init(tmp_path)
        (tmp_path / "a.md").write_text("a", encoding="utf-8")
        subprocess.run(["git", "add", "a.md"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add a"], cwd=tmp_path, capture_output=True, check=True)

        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        # b.md doesn't exist — should be skipped, only 1 file → early return
        results = checker._check_git_commit_consistency("test", ["a.md", "b.md"])
        assert results == []


# ============================================================
# Git-backed tests: _check_release_consistency
# ============================================================


class TestReleaseConsistency:
    def test_partial_update_between_tags(self, tmp_path):
        """Some files changed between tags → info warning."""
        _git_init(tmp_path)
        (tmp_path / "a.md").write_text("a", encoding="utf-8")
        (tmp_path / "b.md").write_text("b", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add both"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "tag", "v1.0.0"], cwd=tmp_path, capture_output=True, check=True)

        # Only modify a.md
        (tmp_path / "a.md").write_text("a updated", encoding="utf-8")
        subprocess.run(["git", "add", "a.md"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "update a"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "tag", "v2.0.0"], cwd=tmp_path, capture_output=True, check=True)

        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_release_consistency("test", ["a.md", "b.md"])
        infos = [r for r in results if r.severity == "info"]
        assert len(infos) >= 1
        assert "b.md" in infos[0].message

    def test_all_files_changed(self, tmp_path):
        """All files changed between tags → no warning."""
        _git_init(tmp_path)
        (tmp_path / "a.md").write_text("a", encoding="utf-8")
        (tmp_path / "b.md").write_text("b", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add both"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "tag", "v1.0.0"], cwd=tmp_path, capture_output=True, check=True)

        (tmp_path / "a.md").write_text("a2", encoding="utf-8")
        (tmp_path / "b.md").write_text("b2", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "update both"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "tag", "v2.0.0"], cwd=tmp_path, capture_output=True, check=True)

        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_release_consistency("test", ["a.md", "b.md"])
        assert results == []

    def test_single_tag(self, tmp_path):
        """Only one tag → empty results."""
        _git_init(tmp_path)
        subprocess.run(["git", "tag", "v1.0.0"], cwd=tmp_path, capture_output=True, check=True)

        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_release_consistency("test", ["a.md", "b.md"])
        assert results == []

    def test_not_git_repo(self, tmp_path):
        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        results = checker._check_release_consistency("test", ["a.md", "b.md"])
        assert results == []


# ============================================================
# _is_file_tracked_in_git
# ============================================================


class TestIsFileTracked:
    def test_tracked_file(self, tmp_path):
        """Line 700-709: tracked file returns True."""
        _git_init(tmp_path)
        (tmp_path / "tracked.md").write_text("t", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.md"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=tmp_path, capture_output=True, check=True)

        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        assert checker._is_file_tracked_in_git(tmp_path / "tracked.md") is True

    def test_untracked_file(self, tmp_path):
        _git_init(tmp_path)
        (tmp_path / "untracked.md").write_text("u", encoding="utf-8")

        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        assert checker._is_file_tracked_in_git(tmp_path / "untracked.md") is False

    def test_not_git_repo(self, tmp_path):
        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        assert checker._is_file_tracked_in_git(tmp_path / "any.md") is False


# ============================================================
# _get_last_commit_time and _check_git_protocol
# ============================================================


class TestGitProtocol:
    def test_last_commit_old(self, tmp_path):
        """Line 89: commit > 24 hours ago produces info."""
        _git_init(tmp_path)
        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)

        # Mock _get_last_commit_time to return old time
        old_time = datetime.now() - timedelta(hours=48)
        with patch.object(checker, "_get_last_commit_time", return_value=old_time):
            results = checker._check_git_protocol()
        freq = [r for r in results if "Commit Frequency" in r.name]
        assert len(freq) == 1
        assert freq[0].severity == "info"
        assert "48" in freq[0].message or "hours" in freq[0].message

    def test_get_last_commit_time_no_git(self, tmp_path):
        """Line 714: non-git repo returns None."""
        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        assert checker._get_last_commit_time() is None

    def test_get_last_commit_time_exception(self, tmp_path):
        """Lines 726-727: subprocess exception returns None."""
        _git_init(tmp_path)
        config = _base_config()
        checker = ProtocolChecker(tmp_path, config)
        with patch("subprocess.run", side_effect=OSError("boom")):
            assert checker._get_last_commit_time() is None
