"""
Built-in IDE Adapters - 内置 IDE 适配器

包含所有内置的 IDE 适配器实现。
"""

from .augment import AugmentAdapter
from .claude import ClaudeAdapter
from .cline import ClineAdapter
from .codebuddy import CodeBuddyAdapter
from .continue_ import ContinueAdapter
from .copilot import CopilotAdapter
from .cursor import CursorAdapter
from .gemini import GeminiAdapter
from .kimicode import KimiCodeAdapter
from .kiro import KiroAdapter
from .opencode import OpenCodeAdapter
from .roocode import RooCodeAdapter
from .trae import TraeAdapter
from .warp import WarpAdapter
from .windsurf import WindsurfAdapter

__all__ = [
    "OpenCodeAdapter",
    "CursorAdapter",
    "ClineAdapter",
    "CodeBuddyAdapter",
    "ClaudeAdapter",
    "WindsurfAdapter",
    "RooCodeAdapter",
    "GeminiAdapter",
    "KiroAdapter",
    "ContinueAdapter",
    "TraeAdapter",
    "CopilotAdapter",
    "AugmentAdapter",
    "WarpAdapter",
    "KimiCodeAdapter",
]
