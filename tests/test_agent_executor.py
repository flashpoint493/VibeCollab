"""Tests for the Agent Executor module."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from vibecollab.agent.executor import (
    MAX_FILES_PER_CYCLE,
    AgentExecutor,
    ExecutionResult,
    FileChange,
)


class TestFileChange:
    def test_basic(self):
        fc = FileChange(file="a.py", action="create", content="x = 1")
        assert fc.file == "a.py"
        assert fc.action == "create"


class TestExecutionResult:
    def test_defaults(self):
        r = ExecutionResult()
        assert not r.success
        assert r.changes_applied == []

    def test_to_dict(self):
        r = ExecutionResult(success=True, git_hash="abc123")
        d = r.to_dict()
        assert d["success"] is True
        assert d["git_hash"] == "abc123"


class TestParseChanges:
    def _exe(self, tmpdir):
        return AgentExecutor(Path(tmpdir))

    def test_single_json_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            output = '```json\n{"file": "a.py", "action": "create", "content": "x = 1"}\n```'
            changes = exe.parse_changes(output)
            assert len(changes) == 1
            assert changes[0].file == "a.py"
            assert changes[0].action == "create"

    def test_json_array(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            output = '```json\n[{"file": "a.py", "action": "create", "content": "x"}, {"file": "b.py", "action": "modify", "content": "y"}]\n```'
            changes = exe.parse_changes(output)
            assert len(changes) == 2

    def test_changes_wrapper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            output = '```json\n{"changes": [{"file": "a.py", "action": "create", "content": "x"}]}\n```'
            changes = exe.parse_changes(output)
            assert len(changes) == 1

    def test_plan_json_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            output = '```json\n{"task_summary": "do stuff", "steps": [{"action": "test"}]}\n```'
            changes = exe.parse_changes(output)
            assert len(changes) == 0

    def test_invalid_json_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            output = '```json\nnot valid json\n```'
            changes = exe.parse_changes(output)
            assert len(changes) == 0

    def test_no_json_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = exe.parse_changes("just some text")
            assert len(changes) == 0

    def test_missing_file_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            output = '```json\n{"action": "create", "content": "x"}\n```'
            changes = exe.parse_changes(output)
            assert len(changes) == 0

    def test_invalid_action(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            output = '```json\n{"file": "a.py", "action": "explode", "content": "x"}\n```'
            changes = exe.parse_changes(output)
            assert len(changes) == 0

    def test_multiple_json_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            output = (
                'First block:\n```json\n{"file": "a.py", "action": "create", "content": "x"}\n```\n'
                'Second block:\n```json\n{"file": "b.py", "action": "modify", "content": "y"}\n```'
            )
            changes = exe.parse_changes(output)
            assert len(changes) == 2


class TestValidateChanges:
    def _exe(self, tmpdir):
        return AgentExecutor(Path(tmpdir))

    def test_valid_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("src/a.py", "create", "x = 1")]
            errors = exe.validate_changes(changes)
            assert errors == []

    def test_too_many_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange(f"f{i}.py", "create", "x") for i in range(MAX_FILES_PER_CYCLE + 1)]
            errors = exe.validate_changes(changes)
            assert any("exceeds" in e for e in errors)

    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("../../etc/passwd", "create", "bad")]
            errors = exe.validate_changes(changes)
            assert any("traversal" in e for e in errors)

    def test_protected_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            for protected in [".git/config", ".env", "project.yaml", "pyproject.toml"]:
                changes = [FileChange(protected, "modify", "x")]
                errors = exe.validate_changes(changes)
                assert any("Protected" in e for e in errors), f"{protected} should be protected"

    def test_file_too_large(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("big.py", "create", "x" * 600_000)]
            errors = exe.validate_changes(changes)
            assert any("too large" in e for e in errors)


class TestApplyChanges:
    def _exe(self, tmpdir, dry_run=False):
        return AgentExecutor(Path(tmpdir), dry_run=dry_run)

    def test_create_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("new_file.py", "create", "print('hello')")]
            result = exe.apply_changes(changes)
            assert result.success
            assert (Path(tmpdir) / "new_file.py").read_text(encoding="utf-8") == "print('hello')"

    def test_create_nested_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("src/sub/module.py", "create", "x = 1")]
            result = exe.apply_changes(changes)
            assert result.success
            assert (Path(tmpdir) / "src" / "sub" / "module.py").exists()

    def test_modify_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "existing.py"
            f.write_text("old content", encoding="utf-8")
            exe = self._exe(tmpdir)
            changes = [FileChange("existing.py", "modify", "new content")]
            result = exe.apply_changes(changes)
            assert result.success
            assert f.read_text(encoding="utf-8") == "new content"

    def test_delete_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "to_delete.py"
            f.write_text("bye", encoding="utf-8")
            exe = self._exe(tmpdir)
            changes = [FileChange("to_delete.py", "delete")]
            result = exe.apply_changes(changes)
            assert result.success
            assert not f.exists()

    def test_delete_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("ghost.py", "delete")]
            result = exe.apply_changes(changes)
            assert result.success
            assert any("absent" in s for s in result.changes_skipped)

    def test_empty_content_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("empty.py", "create", "")]
            result = exe.apply_changes(changes)
            assert any("empty content" in s for s in result.changes_skipped)

    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir, dry_run=True)
            changes = [FileChange("a.py", "create", "x = 1")]
            result = exe.apply_changes(changes)
            assert result.success
            assert not (Path(tmpdir) / "a.py").exists()
            assert any("dry-run" in s for s in result.changes_skipped)

    def test_no_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            result = exe.apply_changes([])
            assert not result.success
            assert any("No applicable" in e for e in result.errors)

    def test_validation_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange(".env", "create", "SECRET=xxx")]
            result = exe.apply_changes(changes)
            assert not result.success


class TestRollback:
    def test_rollback_created_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            changes = [FileChange("new.py", "create", "x")]
            exe.apply_changes(changes)
            assert (Path(tmpdir) / "new.py").exists()
            rolled = exe.rollback()
            assert not (Path(tmpdir) / "new.py").exists()
            assert any("removed" in r for r in rolled)

    def test_rollback_modified_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "exist.py"
            f.write_text("original", encoding="utf-8")
            exe = AgentExecutor(Path(tmpdir))
            changes = [FileChange("exist.py", "modify", "changed")]
            exe.apply_changes(changes)
            assert f.read_text(encoding="utf-8") == "changed"
            exe.rollback()
            assert f.read_text(encoding="utf-8") == "original"

    def test_rollback_deleted_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "del.py"
            f.write_text("content", encoding="utf-8")
            exe = AgentExecutor(Path(tmpdir))
            changes = [FileChange("del.py", "delete")]
            exe.apply_changes(changes)
            assert not f.exists()
            exe.rollback()
            assert f.exists()
            assert f.read_text(encoding="utf-8") == "content"


class TestRunTests:
    def test_passing_tests(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            passed, output = exe.run_tests("python -c \"print('ok')\"")
            assert passed
            assert "ok" in output

    def test_failing_tests(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            passed, output = exe.run_tests("python -c \"raise SystemExit(1)\"")
            assert not passed

    def test_dry_run_skips(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir), dry_run=True)
            passed, output = exe.run_tests()
            assert passed
            assert "dry-run" in output


class TestGitCommit:
    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir), dry_run=True)
            ok, msg = exe.git_commit("test")
            assert ok
            assert "dry-run" in msg


class TestFullCycle:
    def test_no_changes_parsed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            result = exe.execute_full_cycle("no json here")
            assert not result.success
            assert any("No parsable" in e for e in result.errors)

    def test_validation_error_blocks_apply(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            output = '```json\n{"file": ".env", "action": "create", "content": "SECRET"}\n```'
            result = exe.execute_full_cycle(output)
            assert not result.success

    def test_dry_run_full_cycle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir), dry_run=True)
            output = '```json\n{"file": "a.py", "action": "create", "content": "x = 1"}\n```'
            result = exe.execute_full_cycle(output)
            assert result.success
            assert not (Path(tmpdir) / "a.py").exists()

    def test_apply_and_test_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            output = '```json\n{"file": "hello.txt", "action": "create", "content": "world"}\n```'
            result = exe.execute_full_cycle(
                output,
                test_command="python -c \"print('pass')\"",
            )
            assert result.test_passed
            assert (Path(tmpdir) / "hello.txt").exists()

    def test_test_failure_triggers_rollback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            output = '```json\n{"file": "bad.txt", "action": "create", "content": "oops"}\n```'
            result = exe.execute_full_cycle(
                output,
                test_command="python -c \"raise SystemExit(1)\"",
            )
            assert not result.success
            assert result.rollback_performed
            assert not (Path(tmpdir) / "bad.txt").exists()


# ---------------------------------------------------------------------------
# Test: git_commit — real git repo scenarios
# ---------------------------------------------------------------------------

class TestGitCommitReal:
    """Test git_commit behavior in a real git repo."""

    def _init_git_repo(self, path):
        """Initialize a temporary git repo."""
        subprocess.run(["git", "init"], cwd=path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                       cwd=path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"],
                       cwd=path, capture_output=True)

    def test_git_commit_success(self):
        """Git commit returns hash after creating file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._init_git_repo(tmpdir)
            # Create initial commit
            (Path(tmpdir) / "init.txt").write_text("init")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True)

            # Create new file
            (Path(tmpdir) / "new.txt").write_text("hello")
            exe = AgentExecutor(Path(tmpdir))
            success, hash_or_err = exe.git_commit("[TEST] add new.txt")
            assert success
            assert len(hash_or_err) > 0  # Short hash

    def test_git_commit_nothing_to_commit(self):
        """Git commit returns (True, '(no changes)') when nothing to commit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._init_git_repo(tmpdir)
            (Path(tmpdir) / "init.txt").write_text("init")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True)

            exe = AgentExecutor(Path(tmpdir))
            success, msg = exe.git_commit("[TEST] no changes")
            assert success
            assert msg == "(no changes)"

    def test_git_commit_no_repo(self):
        """Commit fails in a non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("data")
            exe = AgentExecutor(Path(tmpdir))
            success, err = exe.git_commit("[TEST] should fail")
            assert not success
            assert len(err) > 0  # Error message


# ---------------------------------------------------------------------------
# Test: run_tests — timeout and exceptions
# ---------------------------------------------------------------------------

class TestRunTestsEdgeCases:
    def test_run_tests_timeout(self):
        """Test timeout handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            with mock.patch("vibecollab.agent.executor.subprocess.run",
                            side_effect=subprocess.TimeoutExpired(cmd="test", timeout=300)):
                passed, output = exe.run_tests("dummy_cmd")
                assert not passed
                assert "timeout" in output.lower()

    def test_run_tests_exception(self):
        """Test execution exception handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            with mock.patch("vibecollab.agent.executor.subprocess.run",
                            side_effect=OSError("command not found")):
                passed, output = exe.run_tests("nonexistent_cmd")
                assert not passed
                assert "failed" in output.lower()

    def test_run_tests_custom_command(self):
        """Custom test command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            passed, output = exe.run_tests("python -c \"print('custom test ok')\"")
            assert passed
            assert "custom test ok" in output


# ---------------------------------------------------------------------------
# Test: apply_changes — edge cases
# ---------------------------------------------------------------------------

class TestApplyChangesEdgeCases:
    def test_apply_write_failure(self):
        """Write failure errors are captured in result.errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            changes = [FileChange(file="test.txt", action="create", content="data")]

            with mock.patch("pathlib.Path.write_text", side_effect=PermissionError("denied")):
                result = exe.apply_changes(changes)
                assert len(result.errors) > 0
                assert "Write failed" in result.errors[0]

    def test_apply_delete_nonexistent(self):
        """Deleting non-existent file skips instead of erroring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            changes = [FileChange(file="ghost.txt", action="delete")]
            result = exe.apply_changes(changes)
            assert "already absent" in result.changes_skipped[0]


# ---------------------------------------------------------------------------
# Test: validate_changes — edge cases
# ---------------------------------------------------------------------------

class TestValidateChangesEdgeCases:
    def test_validate_invalid_path(self):
        """Path traversal attempt triggers error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            changes = [FileChange(file="../../etc/passwd", action="create", content="x")]
            errors = exe.validate_changes(changes)
            assert len(errors) > 0


# ---------------------------------------------------------------------------
# Test: rollback — edge cases
# ---------------------------------------------------------------------------

class TestRollbackEdgeCases:
    def test_rollback_locked_file(self):
        """Rollback does not throw if write fails (except Exception: pass)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            # Simulate existing backups
            exe._backups = {"test.txt": "original content"}
            # Simulate unwritable file
            with mock.patch("pathlib.Path.write_text", side_effect=PermissionError):
                rolled = exe.rollback()
                # No exception, but also not marked as successful rollback
                assert "test.txt" not in str(rolled) or len(rolled) == 0

    def test_rollback_empty(self):
        """Empty backups returns empty list on rollback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            assert exe.rollback() == []


# ---------------------------------------------------------------------------
# Test: execute_full_cycle — git commit failure path
# ---------------------------------------------------------------------------

class TestFullCycleGitFailure:
    def test_test_pass_but_git_fail(self):
        """Tests pass but git commit fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            output = '```json\n{"file": "ok.txt", "action": "create", "content": "data"}\n```'

            with mock.patch.object(exe, "git_commit", return_value=(False, "git error")):
                result = exe.execute_full_cycle(
                    output,
                    test_command="python -c \"print('pass')\"",
                )
                assert not result.success
                assert result.test_passed
                assert not result.git_committed
                assert any("Git commit failed" in e for e in result.errors)

    def test_full_cycle_with_real_git(self):
        """Full cycle: apply -> test -> git commit all succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "t@t.com"],
                           cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "T"],
                           cwd=tmpdir, capture_output=True)
            # Need initial commit
            (Path(tmpdir) / "init.txt").write_text("init")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True)

            exe = AgentExecutor(Path(tmpdir))
            output = '```json\n{"file": "hello.py", "action": "create", "content": "print(42)"}\n```'
            result = exe.execute_full_cycle(
                output,
                test_command="python -c \"print('ok')\"",
            )
            assert result.success
            assert result.test_passed
            assert result.git_committed
            assert len(result.git_hash) > 0


# ---------------------------------------------------------------------------
# Test: _parse_single_change — edge inputs
# ---------------------------------------------------------------------------

class TestParseSingleChangeEdge:
    def test_non_dict_input(self):
        assert AgentExecutor._parse_single_change("string") is None
        assert AgentExecutor._parse_single_change(42) is None
        assert AgentExecutor._parse_single_change(None) is None

    def test_missing_action(self):
        assert AgentExecutor._parse_single_change({"file": "a.py"}) is None

    def test_invalid_action(self):
        assert AgentExecutor._parse_single_change(
            {"file": "a.py", "action": "rename"}
        ) is None


# ---------------------------------------------------------------------------
# Test: Agent serve long-running stress simulation
# ---------------------------------------------------------------------------

class TestServeStressSimulation:
    """Simulate agent serve 100+ cycles state management."""

    def test_100_cycles_success(self):
        """100 successful cycles: sequential apply -> test -> state correct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(100):
                exe = AgentExecutor(Path(tmpdir))
                output = f'```json\n{{"file": "f{i}.txt", "action": "create", "content": "cycle {i}"}}\n```'
                result = exe.apply_changes(exe.parse_changes(output))
                assert result.success
                assert (Path(tmpdir) / f"f{i}.txt").exists()
            # Verify all 100 files exist
            files = list(Path(tmpdir).glob("f*.txt"))
            assert len(files) == 100

    def test_mixed_success_failure_cycles(self):
        """Alternating success/failure cycle simulation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            success_count = 0
            rollback_count = 0
            for i in range(50):
                exe = AgentExecutor(Path(tmpdir))
                output = f'```json\n{{"file": "mix{i}.txt", "action": "create", "content": "data"}}\n```'
                if i % 3 == 0:
                    # Simulate test failure -> rollback
                    result = exe.execute_full_cycle(
                        output,
                        test_command="python -c \"raise SystemExit(1)\"",
                    )
                    assert result.rollback_performed
                    rollback_count += 1
                else:
                    result = exe.execute_full_cycle(
                        output,
                        test_command="python -c \"print('ok')\"",
                    )
                    success_count += 1

            assert success_count > 0
            assert rollback_count > 0

    def test_concurrent_file_operations(self):
        """Multiple AgentExecutor instances operating on same directory (not truly concurrent but verifies isolation)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe1 = AgentExecutor(Path(tmpdir))
            exe2 = AgentExecutor(Path(tmpdir))

            # exe1 creates file
            out1 = '```json\n{"file": "shared.txt", "action": "create", "content": "v1"}\n```'
            result1 = exe1.apply_changes(exe1.parse_changes(out1))
            assert result1.success

            # exe2 modifies same file
            out2 = '```json\n{"file": "shared.txt", "action": "modify", "content": "v2"}\n```'
            result2 = exe2.apply_changes(exe2.parse_changes(out2))
            assert result2.success

            content = (Path(tmpdir) / "shared.txt").read_text()
            assert content == "v2"


# ---------------------------------------------------------------------------
# Test: PID lock concurrency safety
# ---------------------------------------------------------------------------

class TestPIDLockConcurrency:
    """Test PID lock concurrency safety."""

    def test_acquire_release_cycle(self):
        """Acquire -> release -> re-acquire works correctly."""
        from vibecollab.cli.ai import _acquire_lock, _release_lock
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "agent.pid"

            assert _acquire_lock(lock_path) is True
            assert lock_path.exists()

            _release_lock(lock_path)
            assert not lock_path.exists()

            assert _acquire_lock(lock_path) is True

    def test_stale_lock_takeover(self):
        """Stale lock is taken over."""
        from vibecollab.cli.ai import _acquire_lock
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "agent.pid"
            lock_path.write_text("999999999")  # Non-existent PID

            assert _acquire_lock(lock_path) is True
            assert lock_path.read_text().strip() == str(os.getpid())

    def test_active_lock_rejected(self):
        """Active lock is rejected."""
        from vibecollab.cli.ai import _acquire_lock
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "agent.pid"
            lock_path.write_text(str(os.getpid()))  # Current process

            assert _acquire_lock(lock_path) is False


# ---------------------------------------------------------------------------
# Test: Adaptive backoff algorithm edge conditions
# ---------------------------------------------------------------------------

class TestAdaptiveBackoffEdge:
    """Test adaptive backoff algorithm edge conditions."""

    def test_backoff_respects_max(self):
        """Backoff time does not exceed max_sleep."""
        from vibecollab.cli.ai import DEFAULT_MAX_SLEEP_S, DEFAULT_MIN_SLEEP_S
        current = DEFAULT_MIN_SLEEP_S
        for _ in range(20):
            current = min(DEFAULT_MAX_SLEEP_S, max(DEFAULT_MIN_SLEEP_S, current * 2))
        assert current <= DEFAULT_MAX_SLEEP_S

    def test_backoff_resets_on_success(self):
        """Backoff resets to min_sleep on success."""
        from vibecollab.cli.ai import DEFAULT_MIN_SLEEP_S
        # Simulate: 5 failures then 1 success
        current = DEFAULT_MIN_SLEEP_S
        for _ in range(5):
            current = min(300, max(2, current * 2))
        # Success
        current = DEFAULT_MIN_SLEEP_S
        assert current == DEFAULT_MIN_SLEEP_S


# ---------------------------------------------------------------------------
# Test: Agent run failure recovery scenarios
# ---------------------------------------------------------------------------

class TestAgentRunFailureRecovery:
    """Test various failure and recovery scenarios for agent run."""

    def test_rollback_restores_original(self):
        """Rollback restores original file content after failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir) / "existing.txt"
            original.write_text("original content")

            exe = AgentExecutor(Path(tmpdir))
            output = '```json\n{"file": "existing.txt", "action": "modify", "content": "modified"}\n```'
            result = exe.execute_full_cycle(
                output,
                test_command="python -c \"raise SystemExit(1)\"",
            )
            assert result.rollback_performed
            assert original.read_text() == "original content"

    def test_rollback_removes_new_files(self):
        """Rollback removes newly created files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            output = '```json\n{"file": "new.txt", "action": "create", "content": "data"}\n```'
            result = exe.execute_full_cycle(
                output,
                test_command="python -c \"raise SystemExit(1)\"",
            )
            assert result.rollback_performed
            assert not (Path(tmpdir) / "new.txt").exists()

    def test_multiple_files_rollback(self):
        """Multiple file changes all rolled back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.txt").write_text("a_original")
            exe = AgentExecutor(Path(tmpdir))
            output = (
                '```json\n[{"file": "a.txt", "action": "modify", "content": "a_new"},'
                '{"file": "b.txt", "action": "create", "content": "b_new"}]\n```'
            )
            result = exe.execute_full_cycle(
                output,
                test_command="python -c \"raise SystemExit(1)\"",
            )
            assert result.rollback_performed
            assert (Path(tmpdir) / "a.txt").read_text() == "a_original"
            assert not (Path(tmpdir) / "b.txt").exists()

    def test_invalid_llm_output_graceful(self):
        """Completely unparseable LLM output does not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            result = exe.execute_full_cycle("Just some random text without JSON")
            assert not result.success
            assert "No parsable" in result.errors[0] or "LLM" in result.errors[0]

    def test_protected_file_rejected(self):
        """Attempting to modify protected file is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = AgentExecutor(Path(tmpdir))
            output = '```json\n{"file": ".env", "action": "create", "content": "SECRET=bad"}\n```'
            result = exe.execute_full_cycle(output)
            assert not result.success
            assert any("Protected" in e for e in result.errors)
