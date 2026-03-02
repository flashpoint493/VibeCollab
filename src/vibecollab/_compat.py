"""
Windows GBK 编码兼容层

在 Windows GBK 终端中，emoji 和特殊 Unicode 字符会导致 UnicodeEncodeError。
本模块提供三层防御:

1. ensure_safe_stdout() — 在 CLI 入口调用，将 stdout/stderr 的编码错误模式
   从 'strict' 改为 'replace'，让无法编码的字符变成 '?' 而非崩溃
2. safe_console() — Rich Console 工厂函数，确保 Console 输出也安全
3. EMOJI / BULLET 映射 — 将 emoji 替换为 ASCII 等价物

所有 CLI 模块应从此处导入，禁止各自实现编码检测。
"""

import io
import platform
import sys
from typing import Optional


def is_windows_gbk() -> bool:
    """检测是否为 Windows 且终端不支持 emoji 编码"""
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
# 第一层防御: stdout / stderr 编码安全
# ============================================================

_stdio_patched = False


def ensure_safe_stdout() -> None:
    """确保 stdout/stderr 在 Windows GBK 环境下不会因 Unicode 而崩溃。

    原理: 将 stdout/stderr 的 errors 模式从 'strict' 改为 'replace'，
    无法编码的字符会变成 '?' 而非抛出 UnicodeEncodeError。

    此函数幂等——多次调用只生效一次。应在 CLI 入口点最早期调用。
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

        # 如果编码本身就支持完整 Unicode (utf-8)，则无需处理
        try:
            "\u2705\u26a0\u2194\u2588\u2591".encode(encoding)
            continue
        except (UnicodeEncodeError, LookupError):
            pass

        # 如果 errors 已经是 replace/ignore/xmlcharrefreplace/backslashreplace，
        # 则已安全。注意: surrogateescape 在非 UTF 编码下仍会崩溃
        current_errors = getattr(stream, "errors", "strict")
        if current_errors in ("replace", "ignore", "xmlcharrefreplace",
                              "backslashreplace", "namereplace"):
            continue

        # Python 3.7+ TextIOWrapper 支持 reconfigure
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
                continue
            except Exception:
                pass

        # Fallback: 用新的 TextIOWrapper 替换
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
# 第二层防御: Rich Console 安全工厂
# ============================================================

def safe_console(**kwargs) -> "Console":
    """创建一个编码安全的 Rich Console 实例。

    在 Windows GBK 环境下，先确保 stdout 安全，再创建 Console。
    支持传入任何 Console 构造参数。
    """
    ensure_safe_stdout()
    from rich.console import Console
    return Console(**kwargs)


# ============================================================
# 第三层防御: Emoji / 特殊字符映射
# ============================================================

# 通用 emoji 替代映射
EMOJI = {
    # 长名称（cli/main.py / cli/lifecycle.py 使用）
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
    # severity（conflict_detector 使用）
    "high": "[!]" if _GBK else "🔴",
    "medium": "[~]" if _GBK else "🟡",
    "low": "[*]" if _GBK else "🟢",
    "idea": "[?]" if _GBK else "💡",
    # 短别名（cli/ai.py 使用）
    "ok": "OK" if _GBK else "✅",
    "warn": "!" if _GBK else "⚠️",
    "err": "X" if _GBK else "❌",
}

# Bullet point 替代
BULLET = "-" if _GBK else "•"


# ============================================================
# 辅助: 安全化任意文本输出
# ============================================================

def safe_str(text: str, encoding: Optional[str] = None) -> str:
    """将文本中无法编码的字符替换为 '?'，用于输出来自用户数据的文本。

    encoding 默认取 sys.stdout.encoding，适用于 click.echo / print 场景。
    """
    if encoding is None:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return text
    except (UnicodeEncodeError, LookupError):
        return text.encode(encoding, errors="replace").decode(encoding, errors="replace")
