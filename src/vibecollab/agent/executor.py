"""
Agent Executor -- Transforms LLM plans into actual file changes

Responsibilities:
1. Parse JSON file change instructions returned by LLM
2. Apply changes to the file system (create/modify/delete)
3. Run test verification
4. Execute git commit
5. Return execution result report

Safety measures:
- All paths restricted within project_root (prevent directory traversal)
- Maximum single-batch file change limit
- Create backups before writing
- Auto-rollback on test failure
"""

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

MAX_FILES_PER_CYCLE = 10
MAX_FILE_SIZE_BYTES = 500_000  # 500KB


@dataclass
class FileChange:
    """Single file change instruction"""
    file: str
    action: str  # create | modify | delete
    content: str = ""
    description: str = ""


@dataclass
class ExecutionResult:
    """Execution result report"""
    success: bool = False
    changes_applied: List[str] = field(default_factory=list)
    changes_skipped: List[str] = field(default_factory=list)
    test_passed: bool = False
    test_output: str = ""
    git_committed: bool = False
    git_hash: str = ""
    errors: List[str] = field(default_factory=list)
    rollback_performed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "changes_applied": self.changes_applied,
            "changes_skipped": self.changes_skipped,
            "test_passed": self.test_passed,
            "git_committed": self.git_committed,
            "git_hash": self.git_hash,
            "errors": self.errors,
            "rollback_performed": self.rollback_performed,
        }


class AgentExecutor:
    """Transforms LLM output into actual project changes"""

    def __init__(self, project_root: Path, dry_run: bool = False):
        self.project_root = Path(project_root).resolve()
        self.dry_run = dry_run
        self._backups: Dict[str, Optional[str]] = {}

    def parse_changes(self, llm_output: str) -> List[FileChange]:
        """Parse file change instructions from LLM output

        Supports two formats:
        1. JSON code blocks: ```json {"file": ..., "action": ..., "content": ...} ```
        2. JSON array: ```json [{"file": ..., ...}, ...] ```
        """
        changes = []

        # Extract all JSON code blocks
        json_blocks = re.findall(r'```json\s*\n(.*?)```', llm_output, re.DOTALL)

        for block in json_blocks:
            block = block.strip()
            try:
                parsed = json.loads(block)
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, list):
                for item in parsed:
                    change = self._parse_single_change(item)
                    if change:
                        changes.append(change)
            elif isinstance(parsed, dict):
                # May be plan JSON (has steps field) rather than change JSON
                if "file" in parsed and "action" in parsed:
                    change = self._parse_single_change(parsed)
                    if change:
                        changes.append(change)
                elif "changes" in parsed and isinstance(parsed["changes"], list):
                    for item in parsed["changes"]:
                        change = self._parse_single_change(item)
                        if change:
                            changes.append(change)

        return changes

    @staticmethod
    def _parse_single_change(item: dict) -> Optional[FileChange]:
        """Parse a single change instruction"""
        if not isinstance(item, dict):
            return None
        file_path = item.get("file", "")
        action = item.get("action", "").lower()
        if not file_path or action not in ("create", "modify", "delete"):
            return None
        return FileChange(
            file=file_path,
            action=action,
            content=item.get("content", ""),
            description=item.get("description", ""),
        )

    def validate_changes(self, changes: List[FileChange]) -> List[str]:
        """Validate change safety, return list of errors"""
        errors = []

        if len(changes) > MAX_FILES_PER_CYCLE:
            errors.append(
                f"Number of changed files ({len(changes)}) exceeds single-batch limit ({MAX_FILES_PER_CYCLE})"
            )

        for change in changes:
            # Path safety check
            try:
                target = (self.project_root / change.file).resolve()
                if not str(target).startswith(str(self.project_root)):
                    errors.append(f"Path traversal denied: {change.file}")
                    continue
            except (ValueError, OSError):
                errors.append(f"Invalid path: {change.file}")
                continue

            # File size check
            if change.content and len(change.content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
                errors.append(f"File too large: {change.file} ({len(change.content)} bytes)")

            # Dangerous path check
            dangerous = [".git/", ".env", "project.yaml", "pyproject.toml"]
            for d in dangerous:
                if change.file == d or change.file.startswith(d):
                    errors.append(f"Protected file: {change.file}")

        return errors

    def apply_changes(self, changes: List[FileChange]) -> ExecutionResult:
        """Apply file changes to disk"""
        result = ExecutionResult()

        # Validate
        errors = self.validate_changes(changes)
        if errors:
            result.errors = errors
            return result

        if not changes:
            result.errors.append("No applicable changes")
            return result

        # Backup
        self._backups.clear()
        for change in changes:
            target = self.project_root / change.file
            if target.exists():
                try:
                    self._backups[change.file] = target.read_text(encoding="utf-8")
                except Exception:
                    self._backups[change.file] = None
            else:
                self._backups[change.file] = None

        # Apply
        for change in changes:
            target = self.project_root / change.file
            try:
                if self.dry_run:
                    result.changes_skipped.append(f"[dry-run] {change.action}: {change.file}")
                    continue

                if change.action == "delete":
                    if target.exists():
                        target.unlink()
                        result.changes_applied.append(f"deleted: {change.file}")
                    else:
                        result.changes_skipped.append(f"already absent: {change.file}")

                elif change.action in ("create", "modify"):
                    if not change.content:
                        result.changes_skipped.append(f"empty content: {change.file}")
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(change.content, encoding="utf-8")
                    result.changes_applied.append(f"{change.action}: {change.file}")

            except Exception as e:
                result.errors.append(f"Write failed {change.file}: {e}")

        if self.dry_run:
            result.success = True
            return result

        result.success = len(result.errors) == 0
        return result

    def run_tests(self, test_command: Optional[str] = None) -> tuple:
        """Run tests, return (passed: bool, output: str)"""
        if self.dry_run:
            return True, "[dry-run] tests skipped"

        cmd = test_command or "python -m pytest tests/ -q --tb=short"
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8",
                errors="replace",
            )
            output = (proc.stdout + proc.stderr).strip()
            passed = proc.returncode == 0
            return passed, output
        except subprocess.TimeoutExpired:
            return False, "Test timeout (300s)"
        except BaseException as e:
            return False, f"Test execution failed: {e}"

    def rollback(self) -> List[str]:
        """Rollback all backed-up file changes"""
        rolled_back = []
        for file_path, original_content in self._backups.items():
            target = self.project_root / file_path
            try:
                if original_content is None:
                    # Did not exist originally, delete newly created file
                    if target.exists():
                        target.unlink()
                        rolled_back.append(f"removed: {file_path}")
                else:
                    target.write_text(original_content, encoding="utf-8")
                    rolled_back.append(f"restored: {file_path}")
            except Exception:
                pass
        self._backups.clear()
        return rolled_back

    def git_commit(self, message: str) -> tuple:
        """Execute git add + commit, return (success: bool, hash_or_error: str)"""
        if self.dry_run:
            return True, "[dry-run]"

        try:
            # git add -A
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(self.project_root),
                capture_output=True, text=True, timeout=30,
            )
            # git commit
            proc = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(self.project_root),
                capture_output=True, text=True, timeout=30,
            )
            if proc.returncode == 0:
                # Get commit hash
                hash_proc = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=str(self.project_root),
                    capture_output=True, text=True, timeout=10,
                )
                return True, hash_proc.stdout.strip()
            else:
                output = (proc.stdout + proc.stderr).strip()
                if "nothing to commit" in output:
                    return True, "(no changes)"
                return False, output
        except BaseException as e:
            return False, str(e)

    def execute_full_cycle(
        self,
        llm_output: str,
        commit_message: str = "[AGENT] automated changes",
        test_command: Optional[str] = None,
    ) -> ExecutionResult:
        """Full execution cycle: parse -> validate -> apply -> test -> commit/rollback"""
        result = ExecutionResult()

        # Step 1: Parse
        changes = self.parse_changes(llm_output)
        if not changes:
            result.errors.append("No parsable file changes found in LLM output")
            return result

        # Step 2: Validate
        validation_errors = self.validate_changes(changes)
        if validation_errors:
            result.errors = validation_errors
            return result

        # Step 3: Apply
        result = self.apply_changes(changes)
        if not result.success:
            return result

        if self.dry_run:
            return result

        # Step 4: Test
        test_passed, test_output = self.run_tests(test_command)
        result.test_passed = test_passed
        result.test_output = test_output

        if not test_passed:
            # Test failed -> rollback
            rolled = self.rollback()
            result.rollback_performed = True
            result.success = False
            result.errors.append(f"Tests failed, rolled back {len(rolled)} file(s)")
            return result

        # Step 5: Git commit
        committed, hash_or_err = self.git_commit(commit_message)
        result.git_committed = committed
        result.git_hash = hash_or_err
        if not committed:
            result.errors.append(f"Git commit failed: {hash_or_err}")

        result.success = committed
        return result
