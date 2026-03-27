"""
Protocol Checker - Protocol compliance checker
Used to check whether AI follows the requirements of the collaboration protocol
"""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.git import get_git_status, is_git_repo


@dataclass
class CheckResult:
    """Check result"""
    name: str
    passed: bool
    message: str
    severity: str  # "error", "warning", "info"
    suggestion: Optional[str] = None


class ProtocolChecker:
    """Protocol checker"""

    def __init__(self, project_root: Path, config: Optional[Dict] = None):
        self.project_root = Path(project_root)
        self.config = config or {}
        self.docs_dir = self.project_root / "docs"

    def check_all(self) -> List[CheckResult]:
        """Execute all protocol checks

        Returns:
            List[CheckResult]: List of check results
        """
        results = []

        # Check Git related
        results.extend(self._check_git_protocol())

        # Check documentation updates
        results.extend(self._check_documentation_protocol())

        # Check dialogue flow protocol
        results.extend(self._check_dialogue_protocol())

        # Check multi-role protocol
        results.extend(self._check_role_context_protocol())

        # Check document consistency
        results.extend(self._check_document_consistency())

        return results

    def _check_git_protocol(self) -> List[CheckResult]:
        """Check Git protocol compliance"""
        results = []

        # Check if it's a Git repository
        if not is_git_repo(self.project_root):
            results.append(CheckResult(
                name="Git Repository Init",
                passed=False,
                message="Project directory is not a Git repository",
                severity="error",
                suggestion="Run 'git init' to initialize the repository, or use 'vibecollab init' to create a new project"
            ))
            return results  # If not a Git repo, other checks are meaningless

        # Check for uncommitted changes
        git_status = get_git_status(self.project_root)
        if git_status and git_status.get("has_uncommitted_changes"):
            results.append(CheckResult(
                name="Git Commit Requirement",
                passed=False,
                message="There are uncommitted changes",
                severity="warning",
                suggestion="Per protocol, git commit should be done after each effective dialogue. Run 'git status' to view changes, then commit"
            ))

        # Check recent commit time (if possible)
        last_commit_time = self._get_last_commit_time()
        if last_commit_time:
            hours_since_commit = (datetime.now() - last_commit_time).total_seconds() / 3600
            if hours_since_commit > 24:
                results.append(CheckResult(
                    name="Git Commit Frequency",
                    passed=True,
                    message=f"{int(hours_since_commit)} hours since last commit",
                    severity="info",
                    suggestion="If there was recent dialogue output, remember to commit to Git"
                ))

        return results

    def _check_documentation_protocol(self) -> List[CheckResult]:
        """Check documentation update protocol"""
        results = []

        # Read update threshold from config, default 0.25 hours = 15 minutes
        check_config = self.config.get("protocol_check", {}).get("checks", {}).get("documentation", {})
        threshold_hours = check_config.get("update_threshold_hours", 0.25)

        dialogue_protocol = self.config.get("dialogue_protocol", {})
        on_end = dialogue_protocol.get("on_end", {})
        required_files = on_end.get("update_files", [])

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                results.append(CheckResult(
                    name=f"Doc Existence: {file_path}",
                    passed=False,
                    message=f"Required document does not exist: {file_path}",
                    severity="error",
                    suggestion=f"Create file {file_path}, or use 'vibecollab init' to initialize the project"
                ))
                continue

            # Check if file was updated within threshold
            file_mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
            hours_since_update = (datetime.now() - file_mtime).total_seconds() / 3600

            if hours_since_update > threshold_hours:
                if threshold_hours < 1:
                    time_desc = f"{int(threshold_hours * 60)} minutes"
                else:
                    time_desc = f"{int(threshold_hours)} hours"
                results.append(CheckResult(
                    name=f"Doc Update: {file_path}",
                    passed=False,
                    message=f"Document {file_path} has not been updated for over {time_desc}",
                    severity="warning",
                    suggestion=f"Per protocol, {file_path} should be updated after dialogue ends. If there was recent dialogue, please update this document"
                ))

        # Check PRD.md (if configured)
        prd_config = self.config.get("prd_management", {})
        if prd_config.get("enabled", False):
            prd_path = self.project_root / prd_config.get("prd_file", "docs/PRD.md")
            if not prd_path.exists():
                results.append(CheckResult(
                    name="PRD Document",
                    passed=False,
                    message="PRD.md document does not exist",
                    severity="warning",
                    suggestion="Create docs/PRD.md to record project requirements and requirement changes"
                ))

        # Check multi-role collaboration document (if multi-role mode enabled)
        role_context_config = self.config.get("role_context", {})
        if role_context_config.get("enabled", False):
            collab_config = role_context_config.get("collaboration", {})
            collab_file = collab_config.get("file", "docs/roles/COLLABORATION.md")
            collab_path = self.project_root / collab_file

            if not collab_path.exists():
                results.append(CheckResult(
                    name="Collaboration Doc",
                    passed=False,
                    message=f"Multi-role collaboration document does not exist: {collab_file}",
                    severity="warning",
                    suggestion=f"Create {collab_file} to record role collaboration, task assignments and dependencies"
                ))
            else:
                # Check if file was recently updated (within 7 days)
                file_mtime = datetime.fromtimestamp(collab_path.stat().st_mtime)
                days_since_update = (datetime.now() - file_mtime).total_seconds() / 86400

                if days_since_update > 7:
                    results.append(CheckResult(
                        name="Collaboration Doc Update",
                        passed=True,
                        message=f"{collab_file} has not been updated for over 7 days",
                        severity="info",
                        suggestion="Recommend updating collaboration document regularly (weekly) to record task progress and team changes"
                    ))

        return results

    def _check_dialogue_protocol(self) -> List[CheckResult]:
        """Check dialogue flow protocol"""
        results = []

        dialogue_protocol = self.config.get("dialogue_protocol", {})
        on_start = dialogue_protocol.get("on_start", {})
        required_reads = on_start.get("read_files", [])

        # Check if files that should be read at dialogue start exist
        for file_path in required_reads:
            full_path = self.project_root / file_path
            if not full_path.exists():
                results.append(CheckResult(
                    name=f"Dialogue Start File: {file_path}",
                    passed=False,
                    message=f"File that should be read at dialogue start does not exist: {file_path}",
                    severity="error",
                    suggestion=f"Ensure file {file_path} exists, or use 'vibecollab init' to initialize the project"
                ))

        return results

    def _check_role_context_protocol(self) -> List[CheckResult]:
        """Check multi-role protocol compliance"""
        results = []

        role_context_config = self.config.get("role_context", {})
        if not role_context_config.get("enabled", False):
            # Multi-role mode not enabled, skip checks
            return results

        roles = role_context_config.get("roles", [])

        roles_dir_name = role_context_config.get("context", {}).get(
            "per_role_dir", "docs/roles"
        )
        roles_dir = self.project_root / roles_dir_name

        # If no static role list, discover dynamically from filesystem
        if not roles:
            if roles_dir.exists():
                discovered = []
                for d in sorted(roles_dir.iterdir()):
                    if d.is_dir() and not d.name.startswith("."):
                        discovered.append({"id": d.name, "name": d.name})
                roles = discovered

            if not roles:
                results.append(CheckResult(
                    name="Role Config",
                    passed=False,
                    message="Multi-role mode is enabled but no roles were found",
                    severity="warning",
                    suggestion=(
                        "Use 'vibecollab dev init -d <name>' to initialize a role, "
                        "or configure statically in role_context.roles"
                    )
                ))
                return results

        # Check each role's context files
        for dev in roles:
            dev_id = dev.get("id") if isinstance(dev, dict) else dev
            dev_name = (dev.get("name", dev_id) if isinstance(dev, dict) else dev)

            if not dev_id:
                results.append(CheckResult(
                    name="Role ID",
                    passed=False,
                    message=f"Role '{dev_name}' is missing the required 'id' field",
                    severity="error",
                    suggestion="Configure a unique id identifier for each role"
                ))
                continue

            dev_dir = roles_dir / dev_id

            # Check if role directory exists
            if not dev_dir.exists():
                results.append(CheckResult(
                    name=f"Role Dir: {dev_name}",
                    passed=False,
                    message=f"Role '{dev_name}' directory does not exist: docs/roles/{dev_id}",
                    severity="error",
                    suggestion=f"Create directory docs/roles/{dev_id} and add CONTEXT.md and .metadata.yaml"
                ))
                continue

            # Check CONTEXT.md
            context_file = dev_dir / "CONTEXT.md"
            if not context_file.exists():
                results.append(CheckResult(
                    name=f"Role Context: {dev_name}",
                    passed=False,
                    message=f"Role '{dev_name}' CONTEXT.md does not exist",
                    severity="error",
                    suggestion=f"Create docs/roles/{dev_id}/CONTEXT.md to record the role's work context"
                ))
            else:
                # Check if CONTEXT.md was recently updated (activity within 7 days)
                file_mtime = datetime.fromtimestamp(context_file.stat().st_mtime)
                days_since_update = (datetime.now() - file_mtime).total_seconds() / 86400

                if days_since_update > 7:
                    results.append(CheckResult(
                        name=f"Role Context Update: {dev_name}",
                        passed=True,
                        message=f"Role '{dev_name}' CONTEXT.md has not been updated for {int(days_since_update)} days",
                        severity="info",
                        suggestion=f"If {dev_name} has had recent development activity, remember to update their CONTEXT.md"
                    ))
                else:
                    results.append(CheckResult(
                        name=f"Role Context Update: {dev_name}",
                        passed=True,
                        message=f"Role '{dev_name}' CONTEXT.md was updated {int(days_since_update)} days ago",
                        severity="info"
                    ))

            # Check .metadata.yaml
            metadata_file = dev_dir / ".metadata.yaml"
            if not metadata_file.exists():
                results.append(CheckResult(
                    name=f"Role Metadata: {dev_name}",
                    passed=False,
                    message=f"Role '{dev_name}' .metadata.yaml does not exist",
                    severity="warning",
                    suggestion=f"Create docs/roles/{dev_id}/.metadata.yaml to record role info (role, expertise, etc.)"
                ))

            # Check if role's context update is in Git commits
            if context_file.exists():
                git_tracked = self._is_file_tracked_in_git(context_file)
                if not git_tracked:
                    results.append(CheckResult(
                        name=f"Git Tracking: {dev_name} CONTEXT.md",
                        passed=False,
                        message=f"Role '{dev_name}' CONTEXT.md is not tracked in Git version control",
                        severity="warning",
                        suggestion=f"Run 'git add docs/roles/{dev_id}/CONTEXT.md' and commit"
                    ))

        # Check collaboration document
        collab_config = role_context_config.get("collaboration", {})
        collab_file = collab_config.get("file", "docs/roles/COLLABORATION.md")
        collab_path = self.project_root / collab_file

        if not collab_path.exists():
            results.append(CheckResult(
                name="Multi-Role Collaboration Doc",
                passed=False,
                message=f"Collaboration document does not exist: {collab_file}",
                severity="error",
                suggestion=f"Create {collab_file} to record team task assignments, milestones and collaboration rules"
            ))
        else:
            # Check collaboration document update frequency
            file_mtime = datetime.fromtimestamp(collab_path.stat().st_mtime)
            days_since_update = (datetime.now() - file_mtime).total_seconds() / 86400

            if days_since_update > 7:
                results.append(CheckResult(
                    name="Collaboration Doc Update Frequency",
                    passed=True,
                    message=f"Collaboration document has not been updated for {int(days_since_update)} days",
                    severity="info",
                    suggestion="Recommend updating collaboration document weekly to record task progress and team changes"
                ))

        # Check conflict detection config
        conflict_config = role_context_config.get("conflict_detection", {})
        if not conflict_config.get("enabled", True):
            results.append(CheckResult(
                name="Conflict Detection",
                passed=True,
                message="Multi-role conflict detection is disabled",
                severity="warning",
                suggestion="Recommend enabling conflict detection to avoid multiple roles modifying the same files"
            ))

        return results

    def _check_document_consistency(self) -> List[CheckResult]:
        """Check consistency between related documents

        Through project.yaml documentation.consistency.linked_groups config,
        check whether documents in the same group have synchronized modification times.

        Supports three check granularity levels (consistency_level):
          - local_mtime: Local file modification time level (most sensitive, default 15min threshold)
          - git_commit:  Git commit time level (check if recent commit synchronized group files)
          - release:     Release version level (most lenient, only check file state at tags)
        """
        results = []

        doc_config = self.config.get("documentation", {})
        consistency_config = doc_config.get("consistency", {})
        if not consistency_config.get("enabled", False):
            return results

        linked_groups = consistency_config.get("linked_groups", [])
        default_level = consistency_config.get("default_level", "local_mtime")

        for group in linked_groups:
            group_name = group.get("name", "Unnamed Group")
            files = group.get("files", [])
            level = group.get("level", default_level)
            threshold_minutes = group.get("threshold_minutes", 15)

            if len(files) < 2:
                continue

            if level == "local_mtime":
                max_inactive = group.get("max_inactive_hours", 0)
                results.extend(
                    self._check_mtime_consistency(
                        group_name, files, threshold_minutes, max_inactive
                    )
                )
            elif level == "git_commit":
                results.extend(
                    self._check_git_commit_consistency(group_name, files)
                )
            elif level == "release":
                results.extend(
                    self._check_release_consistency(group_name, files)
                )

        # Check existence + optional staleness of all files declared in key_files
        key_files = doc_config.get("key_files", [])
        for kf in key_files:
            path = kf.get("path", "")
            if not path:
                continue
            full_path = self.project_root / path
            if not full_path.exists():
                results.append(CheckResult(
                    name=f"Key Doc Existence: {path}",
                    passed=False,
                    message=f"Key document does not exist: {path} (purpose: {kf.get('purpose', 'unknown')})",
                    severity="warning",
                    suggestion=f"Create {path}, it is declared as a key document"
                ))
                continue

            # Optional staleness check: max_stale_days
            max_stale_days = kf.get("max_stale_days")
            if max_stale_days is not None and max_stale_days > 0:
                file_mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                days_since_update = (datetime.now() - file_mtime).total_seconds() / 86400
                if days_since_update > max_stale_days:
                    results.append(CheckResult(
                        name=f"Key Doc Stale: {path}",
                        passed=False,
                        message=(
                            f"Key document {path} has not been updated for over {max_stale_days} days"
                            f" (last update: {int(days_since_update)} days ago)"
                        ),
                        severity="warning",
                        suggestion=(
                            f"Based on trigger condition '{kf.get('update_trigger', 'unknown')}', "
                            f"please check if {path} needs updating"
                        )
                    ))

            # Optional follow check: watch_files - warn when watched files updated but this file didn't follow
            watch_files = kf.get("watch_files", [])
            if watch_files and full_path.exists():
                my_mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                for wf in watch_files:
                    wf_path = self.project_root / wf
                    if wf_path.exists():
                        wf_mtime = datetime.fromtimestamp(wf_path.stat().st_mtime)
                        lag_minutes = (wf_mtime - my_mtime).total_seconds() / 60
                        if lag_minutes > 15:
                            results.append(CheckResult(
                                name=f"Key Doc Lag: {path}",
                                passed=False,
                                message=(
                                    f"{wf} has been updated, but {path} is lagging "
                                    f"{int(lag_minutes)} minutes behind"
                                ),
                                severity="warning",
                                suggestion=(
                                    f"Trigger condition '{kf.get('update_trigger', 'unknown')}' "
                                    f"may have been met, please check if {path} needs updating"
                                )
                            ))

        return results

    def _check_mtime_consistency(
        self, group_name: str, files: List[str], threshold_minutes: float,
        max_inactive_hours: float = 0
    ) -> List[CheckResult]:
        """Local file modification time level consistency check

        Check whether mtime differences among group files exceed the threshold.
        If a file was recently modified but associated files did not follow, produce a warning.

        Args:
            max_inactive_hours: Group-level configurable inactive window (hours).
                0 uses default 24h. -1 means always check (disable inactive skip).
        """
        results = []
        file_mtimes: Dict[str, datetime] = {}

        for f in files:
            full_path = self.project_root / f
            if full_path.exists():
                file_mtimes[f] = datetime.fromtimestamp(full_path.stat().st_mtime)

        if len(file_mtimes) < 2:
            return results

        # Find most recently and least recently modified files
        sorted_files = sorted(file_mtimes.items(), key=lambda x: x[1], reverse=True)
        newest_file, newest_time = sorted_files[0]
        oldest_file, oldest_time = sorted_files[-1]

        diff_minutes = (newest_time - oldest_time).total_seconds() / 60

        if diff_minutes > threshold_minutes:
            hours_since_newest = (datetime.now() - newest_time).total_seconds() / 3600
            # max_inactive_hours: -1 = always check; 0 = default 24h; >0 = custom
            inactive_limit = (
                float("inf") if max_inactive_hours < 0
                else (max_inactive_hours if max_inactive_hours > 0 else 24)
            )
            if hours_since_newest < inactive_limit:
                stale_files = [
                    f for f, t in sorted_files[1:]
                    if (newest_time - t).total_seconds() / 60 > threshold_minutes
                ]
                for stale_f in stale_files:
                    stale_t = file_mtimes[stale_f]
                    diff_min = int((newest_time - stale_t).total_seconds() / 60)
                    results.append(CheckResult(
                        name=f"Doc Consistency: {group_name}",
                        passed=False,
                        message=(
                            f"{newest_file} has been modified, but associated document {stale_f} "
                            f"is lagging {diff_min} minutes behind"
                        ),
                        severity="warning",
                        suggestion=(
                            f"Linked group [{group_name}] requires synchronized updates. "
                            f"Please check if {stale_f} needs to be updated accordingly"
                        )
                    ))

        return results

    def _check_git_commit_consistency(
        self, group_name: str, files: List[str]
    ) -> List[CheckResult]:
        """Git commit time level consistency check

        Check whether group files were modified in the same recent commit.
        If a file was modified in the latest commit but associated files are not in the same commit, produce a warning.
        """
        results = []

        if not is_git_repo(self.project_root):
            return results

        # Get the most recent commit hash for each file
        file_last_commits: Dict[str, Optional[str]] = {}
        for f in files:
            full_path = self.project_root / f
            if not full_path.exists():
                continue
            try:
                result = subprocess.run(
                    ["git", "log", "-1", "--format=%H", "--", f],
                    cwd=self.project_root,
                    capture_output=True, text=True
                )
                commit_hash = result.stdout.strip() if result.returncode == 0 else None
                file_last_commits[f] = commit_hash
            except BaseException:
                file_last_commits[f] = None

        if len(file_last_commits) < 2:
            return results

        # Find the most recently committed file
        commits_with_time: Dict[str, Optional[datetime]] = {}
        for f, commit_hash in file_last_commits.items():
            if commit_hash:
                try:
                    result = subprocess.run(
                        ["git", "log", "-1", "--format=%ct", commit_hash],
                        cwd=self.project_root,
                        capture_output=True, text=True
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        commits_with_time[f] = datetime.fromtimestamp(
                            int(result.stdout.strip())
                        )
                    else:
                        commits_with_time[f] = None
                except BaseException:
                    commits_with_time[f] = None
            else:
                commits_with_time[f] = None

        # Find the file with the most recent commit
        valid_entries = [(f, t) for f, t in commits_with_time.items() if t is not None]
        if len(valid_entries) < 2:
            return results

        valid_entries.sort(key=lambda x: x[1], reverse=True)
        newest_file, newest_time = valid_entries[0]
        newest_commit = file_last_commits[newest_file]

        # Check if other files are in the same commit
        for f, commit_hash in file_last_commits.items():
            if f == newest_file:
                continue
            if commit_hash != newest_commit:
                results.append(CheckResult(
                    name=f"Doc Git Consistency: {group_name}",
                    passed=False,
                    message=(
                        f"{newest_file} was modified in the recent commit, "
                        f"but associated document {f} is not in the same commit"
                    ),
                    severity="warning",
                    suggestion=(
                        f"Linked group [{group_name}] requires git commit sync. "
                        f"Recommend updating {f} when modifying {newest_file}"
                    )
                ))

        return results

    def _check_release_consistency(
        self, group_name: str, files: List[str]
    ) -> List[CheckResult]:
        """Release version level consistency check

        Check whether all files in the group were modified (compared to previous tag)
        at the most recent version tag. This is the most lenient check.
        """
        results = []

        if not is_git_repo(self.project_root):
            return results

        try:
            # Get the two most recent version tags
            tag_result = subprocess.run(
                ["git", "tag", "--sort=-v:refname", "-l", "v*"],
                cwd=self.project_root,
                capture_output=True, text=True
            )
            if tag_result.returncode != 0:
                return results

            tags = [t.strip() for t in tag_result.stdout.strip().split("\n") if t.strip()]
            if len(tags) < 2:
                return results

            latest_tag = tags[0]
            prev_tag = tags[1]

            # Get files modified between the two tags
            diff_result = subprocess.run(
                ["git", "diff", "--name-only", prev_tag, latest_tag],
                cwd=self.project_root,
                capture_output=True, text=True
            )
            if diff_result.returncode != 0:
                return results

            changed_files = set(diff_result.stdout.strip().split("\n"))

            # Check if all group files are in the change list
            group_in_diff = {f: f in changed_files for f in files}
            some_changed = any(group_in_diff.values())
            all_changed = all(group_in_diff.values())

            if some_changed and not all_changed:
                missing = [f for f, changed in group_in_diff.items() if not changed]
                for f in missing:
                    results.append(CheckResult(
                        name=f"Doc Version Consistency: {group_name}",
                        passed=False,
                        message=(
                            f"In version {prev_tag} -> {latest_tag}, "
                            f"some documents in the linked group were updated, but {f} was not synced"
                        ),
                        severity="info",
                        suggestion=(
                            f"Linked group [{group_name}] should be consistent at release. "
                            f"Please check if {f} needs updating"
                        )
                    ))
        except BaseException:
            pass

        return results

    def _is_file_tracked_in_git(self, file_path: Path) -> bool:
        """Check if a file is tracked in Git version control

        Args:
            file_path: File path

        Returns:
            bool: Whether the file is tracked
        """
        if not is_git_repo(self.project_root):
            return False

        try:
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(file_path.relative_to(self.project_root))],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except BaseException:
            return False

    def _get_last_commit_time(self) -> Optional[datetime]:
        """Get the time of the last commit"""
        if not is_git_repo(self.project_root):
            return None

        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp)
        except BaseException:
            return None

    def get_summary(self, results: List[CheckResult]) -> Dict:
        """Get check results summary

        Args:
            results: List of check results

        Returns:
            Dict: Summary information
        """
        total = len(results)
        errors = sum(1 for r in results if r.severity == "error")
        warnings = sum(1 for r in results if r.severity == "warning")
        infos = sum(1 for r in results if r.severity == "info")
        passed = sum(1 for r in results if r.passed)

        return {
            "total": total,
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
            "all_passed": errors == 0
        }
