"""CLI subpackage — all Click commands."""
# Ensure stdout/stderr encoding safety before importing any CLI module
from vibecollab._compat import ensure_safe_stdout as _ensure_safe_stdout
_ensure_safe_stdout()

from vibecollab.cli.main import main  # noqa: F401

__all__ = ["main"]
