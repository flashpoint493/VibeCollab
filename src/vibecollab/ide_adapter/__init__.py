"""
Universal IDE Adapter - 通用 IDE 适配器框架

为不同 IDE (OpenCode, Cursor, Cline, CodeBuddy 等) 提供统一的适配接口，
支持 Skill 注入和 MCP 配置管理。

Usage:
    from vibecollab.ide_adapter import get_adapter, IDEType

    # 获取适配器
    adapter = get_adapter(IDEType.CURSOR)

    # 注入 Skill
    adapter.inject_skill(project_root, force=False)

    # 注入 MCP 配置
    adapter.inject_mcp_config(project_root, command="vibecollab", args=["mcp", "serve"])
"""

from typing import Optional

# 导入所有内置适配器以完成注册
from .adapters import (
    ClineAdapter,
    CodeBuddyAdapter,
    CursorAdapter,
    OpenCodeAdapter,
)
from .base import BaseIDEAdapter, IDEType, InjectionResult
from .registry import (
    AdapterRegistry,
    get_adapter,
    get_adapter_info,
    list_adapters,
    register_adapter,
)

__all__ = [
    # 基类和枚举
    "BaseIDEAdapter",
    "IDEType",
    "InjectionResult",
    # 注册表
    "AdapterRegistry",
    "get_adapter",
    "list_adapters",
    "register_adapter",
    "get_adapter_info",
    # 具体适配器
    "OpenCodeAdapter",
    "CursorAdapter",
    "ClineAdapter",
    "CodeBuddyAdapter",
]


def inject_skill(ide: str, project_root: Optional[str] = None, force: bool = False) -> InjectionResult:
    """便捷函数：向指定 IDE 注入 Skill。

    Args:
        ide: IDE 名称 (opencode, cursor, cline, codebuddy)
        project_root: 项目根目录，默认为当前目录
        force: 是否强制覆盖现有文件

    Returns:
        InjectionResult: 注入结果
    """
    from pathlib import Path

    adapter = get_adapter(ide)
    root = Path(project_root) if project_root else Path.cwd()
    return adapter.inject_skill(root, force=force)


def inject_mcp_config(
    ide: str,
    command: str,
    args: list[str],
    project_root: Optional[str] = None,
) -> InjectionResult:
    """便捷函数：向指定 IDE 注入 MCP 配置。

    Args:
        ide: IDE 名称 (cursor, cline, codebuddy)
        command: MCP 服务器命令
        args: MCP 服务器参数
        project_root: 项目根目录，默认为当前目录

    Returns:
        InjectionResult: 注入结果
    """
    from pathlib import Path

    adapter = get_adapter(ide)
    root = Path(project_root) if project_root else Path.cwd()
    return adapter.inject_mcp_config(root, command=command, args=args)


def get_mcp_config(ide: str, command: str, args: list[str]) -> dict:
    """获取指定 IDE 的 MCP 配置内容。

    Args:
        ide: IDE 名称
        command: MCP 服务器命令
        args: MCP 服务器参数

    Returns:
        dict: MCP 配置字典
    """
    adapter = get_adapter(ide)
    return adapter.get_mcp_config(command, args)
