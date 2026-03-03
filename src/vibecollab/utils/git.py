"""
Git utility functions - check and manage Git repositories
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def check_git_installed() -> bool:
    """Check if Git is installed

    Returns:
        bool: Whether Git is available
    """
    return shutil.which("git") is not None


def is_git_repo(path: Path) -> bool:
    """Check if path is a Git repository

    Args:
        path: Path to check

    Returns:
        bool: Whether it is a Git repository
    """
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def init_git_repo(path: Path, initial_commit: bool = True) -> Tuple[bool, Optional[str]]:
    """Initialize a Git repository

    Args:
        path: Project root directory
        initial_commit: Whether to create initial commit

    Returns:
        Tuple[bool, Optional[str]]: (success, error message)
    """
    if not check_git_installed():
        return False, "Git is not installed. Please install Git first"

    if is_git_repo(path):
        return True, None  # Already a Git repo

    try:
        # Initialize repository
        subprocess.run(
            ["git", "init"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True
        )

        # Create initial commit (if requested)
        if initial_commit:
            # Check if there are files to commit
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                # Add all files
                subprocess.run(
                    ["git", "add", "."],
                    cwd=path,
                    check=True,
                    capture_output=True,
                    text=True
                )

                # Create initial commit
                subprocess.run(
                    ["git", "commit", "-m", "chore: initial commit with vibe-collab setup"],
                    cwd=path,
                    check=True,
                    capture_output=True,
                    text=True
                )

        return True, None
    except subprocess.CalledProcessError as e:
        return False, f"Git init failed: {e.stderr}"
    except BaseException as e:
        return False, f"Git init error: {str(e)}"


def ensure_git_repo(path: Path, auto_init: bool = False) -> Tuple[bool, Optional[str], bool]:
    """Ensure path is a Git repository

    Args:
        path: Project root directory
        auto_init: Whether to auto-initialize if not exists

    Returns:
        Tuple[bool, Optional[str], bool]: (success, error message, whether newly initialized)
    """
    # Check if Git is installed
    if not check_git_installed():
        if auto_init:
            return False, "Git is not installed, cannot auto-init repo. Please install Git: https://git-scm.com/", False
        return False, "Git is not installed", False

    # Check if already a repo
    if is_git_repo(path):
        return True, None, False

    # If auto-init is needed
    if auto_init:
        success, error = init_git_repo(path, initial_commit=True)
        if success:
            return True, None, True
        return False, error, False

    # No auto-init, return hint
    return False, "Project directory is not a Git repository. Run 'git init' to initialize.", False


def get_git_status(path: Path) -> Optional[dict]:
    """Get Git repository status info

    Args:
        path: Project root directory

    Returns:
        Optional[dict]: Git status info, or None if not a repo
    """
    if not is_git_repo(path):
        return None

    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        branch = branch_result.stdout.strip()

        # Get commit count
        commit_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        commit_count = commit_result.stdout.strip()

        # Check for uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        has_changes = bool(status_result.stdout.strip())

        return {
            "branch": branch,
            "commit_count": int(commit_count) if commit_count else 0,
            "has_uncommitted_changes": has_changes
        }
    except BaseException:
        return None
