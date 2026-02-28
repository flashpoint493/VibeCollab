"""
Windows GBK 编码兼容层

在 Windows GBK 终端中，emoji 和特殊 Unicode 字符会导致 UnicodeEncodeError。
本模块提供统一的检测和替代方案，所有 CLI 模块应从此处导入。
"""

import platform
import sys


def is_windows_gbk() -> bool:
    """检测是否为 Windows 且终端不支持 emoji 编码"""
    if platform.system() != "Windows":
        return False
    try:
        "✅⚠️❌ℹ️🤖🔑📦⏳●•".encode(sys.stdout.encoding or "utf-8")
        return False
    except (UnicodeEncodeError, LookupError):
        return True


_GBK = is_windows_gbk()

# 通用 emoji 替代映射
EMOJI = {
    # 长名称（cli.py / cli_lifecycle.py 使用）
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
    # 短别名（cli_ai.py 使用）
    "ok": "OK" if _GBK else "✅",
    "warn": "!" if _GBK else "⚠️",
    "err": "X" if _GBK else "❌",
}

# Bullet point 替代
BULLET = "-" if _GBK else "•"


def sanitize_for_console(text: str) -> str:
    """Replace Unicode chars that may fail to encode on Windows GBK console.

    Use before passing user/content text to Rich (e.g. Panel) to avoid
    UnicodeEncodeError when stdout encoding is GBK.
    """
    if not _GBK or not text:
        return text
    replacements = (
        ("\u26a0\ufe0f", "!"),   # ⚠️
        ("\u26a0", "!"),
        ("\u2705", "[OK]"),     # ✅
        ("\u274c", "[X]"),      # ❌
        ("\u2139\ufe0f", "[i]"),  # ℹ️
        ("\u2139", "[i]"),
        ("\u1f4ca", "[*]"),    # 📊
        ("\u1f4dd", "[doc]"),  # 📝
    )
    for char, sub in replacements:
        text = text.replace(char, sub)
    return text
