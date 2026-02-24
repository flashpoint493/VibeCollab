"""Tests for the Agent Executor module."""

import tempfile
from pathlib import Path

from vibecollab.agent_executor import (
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
            assert any("超过" in e for e in errors)

    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("../../etc/passwd", "create", "bad")]
            errors = exe.validate_changes(changes)
            assert any("穿越" in e for e in errors)

    def test_protected_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            for protected in [".git/config", ".env", "project.yaml", "pyproject.toml"]:
                changes = [FileChange(protected, "modify", "x")]
                errors = exe.validate_changes(changes)
                assert any("受保护" in e for e in errors), f"{protected} should be protected"

    def test_file_too_large(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe = self._exe(tmpdir)
            changes = [FileChange("big.py", "create", "x" * 600_000)]
            errors = exe.validate_changes(changes)
            assert any("过大" in e for e in errors)


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
            assert any("没有" in e for e in result.errors)

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
            assert any("未找到" in e for e in result.errors)

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
