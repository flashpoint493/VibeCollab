"""Tests for git_utils module."""

import subprocess
from unittest.mock import MagicMock, patch

from vibecollab.utils.git import (
    check_git_installed,
    ensure_git_repo,
    get_git_status,
    init_git_repo,
    is_git_repo,
)


class TestCheckGitInstalled:
    def test_git_available(self):
        with patch("vibecollab.utils.git.shutil.which", return_value="/usr/bin/git"):
            assert check_git_installed() is True

    def test_git_not_available(self):
        with patch("vibecollab.utils.git.shutil.which", return_value=None):
            assert check_git_installed() is False


class TestIsGitRepo:
    def test_is_repo(self, tmp_path):
        (tmp_path / ".git").mkdir()
        assert is_git_repo(tmp_path) is True

    def test_not_repo(self, tmp_path):
        assert is_git_repo(tmp_path) is False

    def test_git_file_not_dir(self, tmp_path):
        (tmp_path / ".git").write_text("ref: ...", encoding="utf-8")
        assert is_git_repo(tmp_path) is False


class TestInitGitRepo:
    def test_git_not_installed(self, tmp_path):
        with patch("vibecollab.utils.git.check_git_installed", return_value=False):
            success, error = init_git_repo(tmp_path)
            assert success is False
            assert "未安装" in error

    def test_already_git_repo(self, tmp_path):
        (tmp_path / ".git").mkdir()
        success, error = init_git_repo(tmp_path)
        assert success is True
        assert error is None

    def test_init_success_with_commit(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello", encoding="utf-8")

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.stdout = "?? file.txt\n" if "status" in cmd else ""
            result.stderr = ""
            result.returncode = 0
            return result

        with patch("vibecollab.utils.git.check_git_installed", return_value=True), \
             patch("vibecollab.utils.git.subprocess.run", side_effect=mock_run):
            success, error = init_git_repo(tmp_path, initial_commit=True)
            assert success is True
            assert error is None

    def test_init_no_files_to_commit(self, tmp_path):
        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.stdout = ""
            result.stderr = ""
            result.returncode = 0
            return result

        with patch("vibecollab.utils.git.check_git_installed", return_value=True), \
             patch("vibecollab.utils.git.subprocess.run", side_effect=mock_run):
            success, error = init_git_repo(tmp_path, initial_commit=True)
            assert success is True

    def test_init_called_process_error(self, tmp_path):
        with patch("vibecollab.utils.git.check_git_installed", return_value=True), \
             patch("vibecollab.utils.git.subprocess.run",
                   side_effect=subprocess.CalledProcessError(1, "git", stderr="fail")):
            success, error = init_git_repo(tmp_path)
            assert success is False
            assert "失败" in error

    def test_init_generic_exception(self, tmp_path):
        with patch("vibecollab.utils.git.check_git_installed", return_value=True), \
             patch("vibecollab.utils.git.subprocess.run",
                   side_effect=OSError("boom")):
            success, error = init_git_repo(tmp_path)
            assert success is False
            assert "出错" in error


class TestEnsureGitRepo:
    def test_git_not_installed_no_auto(self, tmp_path):
        with patch("vibecollab.utils.git.check_git_installed", return_value=False):
            ok, err, is_new = ensure_git_repo(tmp_path, auto_init=False)
            assert ok is False
            assert "未安装" in err
            assert is_new is False

    def test_git_not_installed_auto(self, tmp_path):
        with patch("vibecollab.utils.git.check_git_installed", return_value=False):
            ok, err, is_new = ensure_git_repo(tmp_path, auto_init=True)
            assert ok is False
            assert "安装" in err
            assert is_new is False

    def test_already_repo(self, tmp_path):
        (tmp_path / ".git").mkdir()
        ok, err, is_new = ensure_git_repo(tmp_path)
        assert ok is True
        assert err is None
        assert is_new is False

    def test_auto_init_success(self, tmp_path):
        with patch("vibecollab.utils.git.check_git_installed", return_value=True), \
             patch("vibecollab.utils.git.init_git_repo", return_value=(True, None)):
            ok, err, is_new = ensure_git_repo(tmp_path, auto_init=True)
            assert ok is True
            assert is_new is True

    def test_auto_init_failure(self, tmp_path):
        with patch("vibecollab.utils.git.check_git_installed", return_value=True), \
             patch("vibecollab.utils.git.init_git_repo", return_value=(False, "fail")):
            ok, err, is_new = ensure_git_repo(tmp_path, auto_init=True)
            assert ok is False
            assert err == "fail"
            assert is_new is False

    def test_no_auto_init_not_repo(self, tmp_path):
        with patch("vibecollab.utils.git.check_git_installed", return_value=True):
            ok, err, is_new = ensure_git_repo(tmp_path, auto_init=False)
            assert ok is False
            assert "不是 Git 仓库" in err


class TestGetGitStatus:
    def test_not_a_repo(self, tmp_path):
        assert get_git_status(tmp_path) is None

    def test_returns_status(self, tmp_path):
        (tmp_path / ".git").mkdir()

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if "branch" in cmd:
                result.stdout = "main\n"
            elif "rev-list" in cmd:
                result.stdout = "42\n"
            elif "status" in cmd:
                result.stdout = "M file.txt\n"
            return result

        with patch("vibecollab.utils.git.subprocess.run", side_effect=mock_run):
            status = get_git_status(tmp_path)
            assert status["branch"] == "main"
            assert status["commit_count"] == 42
            assert status["has_uncommitted_changes"] is True

    def test_clean_repo(self, tmp_path):
        (tmp_path / ".git").mkdir()

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if "branch" in cmd:
                result.stdout = "dev\n"
            elif "rev-list" in cmd:
                result.stdout = "0\n"
            elif "status" in cmd:
                result.stdout = ""
            return result

        with patch("vibecollab.utils.git.subprocess.run", side_effect=mock_run):
            status = get_git_status(tmp_path)
            assert status["branch"] == "dev"
            assert status["commit_count"] == 0
            assert status["has_uncommitted_changes"] is False

    def test_exception_returns_none(self, tmp_path):
        (tmp_path / ".git").mkdir()
        with patch("vibecollab.utils.git.subprocess.run", side_effect=OSError("boom")):
            assert get_git_status(tmp_path) is None
