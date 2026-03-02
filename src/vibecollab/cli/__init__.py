"""CLI subpackage — all Click commands."""
# 在导入任何 CLI 模块之前，确保 stdout/stderr 编码安全
from vibecollab._compat import ensure_safe_stdout as _ensure_safe_stdout
_ensure_safe_stdout()

from vibecollab.cli.main import main  # noqa: F401

__all__ = ["main"]
