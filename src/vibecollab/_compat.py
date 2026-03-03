"""
Windows GBK encoding compatibility layer

On Windows GBK terminals, emoji and special Unicode characters cause UnicodeEncodeError.
This module provides three layers of defense:

1. ensure_safe_stdout() -- Called at CLI entry, changes stdout/stderr error mode
   from 'strict' to 'replace', turning unencodable characters into '?' instead of crashing
2. safe_console() -- Rich Console factory function, ensures Console output is safe
3. EMOJI / BULLET mapping -- Replaces emoji with ASCII equivalents

All CLI modules should import from here; do not implement encoding detection individually.
"""

import io
import platform
import sys
from typing import Optional


def is_windows_gbk() -> bool:
    """Detect whether the platform is Windows with a terminal that cannot encode emoji"""
    if platform.system() != "Windows":
        return False
    try:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        "✅⚠️❌ℹ️🤖🔑📦⏳●•↔█░✓✗".encode(encoding)
        return False
    except (UnicodeEncodeError, LookupError):
        return True


_GBK = is_windows_gbk()


# ============================================================
# Layer 1: stdout / stderr encoding safety
# ============================================================

_stdio_patched = False


def ensure_safe_stdout() -> None:
    """Ensure stdout/stderr do not crash due to Unicode on Windows GBK.

    Principle: Change stdout/stderr errors mode from 'strict' to 'replace',
    so unencodable characters become '?' instead of raising UnicodeEncodeError.

    This function is idempotent -- multiple calls only take effect once.
    Should be called at the earliest point in the CLI entry.
    """
    global _stdio_patched
    if _stdio_patched:
        return
    _stdio_patched = True

    if platform.system() != "Windows":
        return

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue

        encoding = getattr(stream, "encoding", None) or "utf-8"

        # If encoding natively supports full Unicode (utf-8), no action needed
        try:
            "\u2705\u26a0\u2194\u2588\u2591".encode(encoding)
            continue
        except (UnicodeEncodeError, LookupError):
            pass

        # If errors is already replace/ignore/xmlcharrefreplace/backslashreplace,
        # it's safe. Note: surrogateescape can still crash on non-UTF encodings
        current_errors = getattr(stream, "errors", "strict")
        if current_errors in ("replace", "ignore", "xmlcharrefreplace",
                              "backslashreplace", "namereplace"):
            continue

        # Python 3.7+ TextIOWrapper supports reconfigure
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
                continue
            except Exception:
                pass

        # Fallback: replace with a new TextIOWrapper
        try:
            binary = getattr(stream, "buffer", None)
            if binary is not None:
                wrapper = io.TextIOWrapper(
                    binary,
                    encoding=encoding,
                    errors="replace",
                    line_buffering=stream.line_buffering,
                )
                setattr(sys, stream_name, wrapper)
        except Exception:
            pass


# ============================================================
# Layer 2: Rich Console safe factory
# ============================================================

def safe_console(**kwargs) -> "Console":
    """Create an encoding-safe Rich Console instance.

    On Windows GBK, ensures stdout is safe before creating Console.
    Accepts any Console constructor arguments.
    """
    ensure_safe_stdout()
    from rich.console import Console
    return Console(**kwargs)


# ============================================================
# Layer 3: Emoji / special character mapping
# ============================================================

# Universal emoji substitution mapping
EMOJI = {
    # Long names (used by cli/main.py / cli/lifecycle.py)
    "success": "OK" if _GBK else "✅",
    "warning": "!" if _GBK else "⚠️",
    "error": "X" if _GBK else "❌",
    "info": "i" if _GBK else "ℹ️",
    "lock": "[LOCK]" if _GBK else "🔒",
    "sparkles": "+" if _GBK else "✨",
    "bot": ">" if _GBK else "🤖",
    "user": ">" if _GBK else "👤",
    "think": "..." if _GBK else "🧠",
    "stop": "[STOP]" if _GBK else "🛑",
    "key": ">" if _GBK else "🔑",
    "gear": ">" if _GBK else "⚙️",
    "package": "[PKG]" if _GBK else "📦",
    "hourglass": "[...]" if _GBK else "⏳",
    "circle": "*" if _GBK else "●",
    "check": "v" if _GBK else "✓",
    "cross": "x" if _GBK else "✗",
    "arrow": "<->" if _GBK else "↔",
    "bar_fill": "#" if _GBK else "█",
    "bar_empty": "-" if _GBK else "░",
    # severity (used by conflict_detector)
    "high": "[!]" if _GBK else "🔴",
    "medium": "[~]" if _GBK else "🟡",
    "low": "[*]" if _GBK else "🟢",
    "idea": "[?]" if _GBK else "💡",
    # Short aliases (used by cli/ai.py)
    "ok": "OK" if _GBK else "✅",
    "warn": "!" if _GBK else "⚠️",
    "err": "X" if _GBK else "❌",
}

# Bullet point substitute
BULLET = "-" if _GBK else "•"


# ============================================================
# Helper: sanitize arbitrary text output
# ============================================================

def safe_str(text: str, encoding: Optional[str] = None) -> str:
    """Replace unencodable characters in text with '?', for outputting user data.

    encoding defaults to sys.stdout.encoding, suitable for click.echo / print.
    """
    if encoding is None:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return text
    except (UnicodeEncodeError, LookupError):
        return text.encode(encoding, errors="replace").decode(encoding, errors="replace")
