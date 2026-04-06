"""
Adapter Registry - IDE 适配器注册表

管理所有 IDE 适配器的注册和查找。
"""

from typing import Optional, Type

from .base import BaseIDEAdapter, IDEType


class AdapterRegistry:
    """IDE 适配器注册表。

    单例模式管理所有适配器的注册和查找。
    """

    _instance: Optional["AdapterRegistry"] = None
    _adapters: dict[IDEType, BaseIDEAdapter]

    def __new__(cls) -> "AdapterRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._adapters = {}
        return cls._instance

    def register(self, adapter_class: Type[BaseIDEAdapter]) -> Type[BaseIDEAdapter]:
        """注册适配器类。

        可作为类装饰器使用。

        Args:
            adapter_class: 适配器类

        Returns:
            Type[BaseIDEAdapter]: 适配器类本身（支持装饰器用法）
        """
        adapter = adapter_class()
        self._adapters[adapter.ide_type] = adapter
        return adapter_class

    def get(self, ide_type: IDEType | str) -> BaseIDEAdapter:
        """获取适配器实例。

        Args:
            ide_type: IDE 类型或名称

        Returns:
            BaseIDEAdapter: 适配器实例

        Raises:
            ValueError: 如果适配器未注册
        """
        if isinstance(ide_type, str):
            ide_type = IDEType.from_string(ide_type)

        if ide_type not in self._adapters:
            raise ValueError(
                f"No adapter registered for IDE type: {ide_type.value}. "
                f"Available: {', '.join(a.value for a in self._adapters.keys())}"
            )

        return self._adapters[ide_type]

    def list_adapters(self) -> list[BaseIDEAdapter]:
        """列出所有已注册的适配器。

        Returns:
            list[BaseIDEAdapter]: 适配器实例列表
        """
        return list(self._adapters.values())

    def list_by_feature(self, skill: bool = False, mcp: bool = False) -> list[BaseIDEAdapter]:
        """按功能筛选适配器。

        Args:
            skill: 是否要求支持 Skill
            mcp: 是否要求支持 MCP

        Returns:
            list[BaseIDEAdapter]: 符合条件的适配器列表
        """
        result = []
        for adapter in self._adapters.values():
            if skill and not adapter.supports_skill:
                continue
            if mcp and not adapter.supports_mcp:
                continue
            result.append(adapter)
        return result

    def is_registered(self, ide_type: IDEType | str) -> bool:
        """检查适配器是否已注册。

        Args:
            ide_type: IDE 类型或名称

        Returns:
            bool: 是否已注册
        """
        if isinstance(ide_type, str):
            try:
                ide_type = IDEType.from_string(ide_type)
            except ValueError:
                return False
        return ide_type in self._adapters

    def clear(self) -> None:
        """清空所有注册的适配器（主要用于测试）。"""
        self._adapters.clear()


# 全局注册表实例
_registry = AdapterRegistry()


def register_adapter(adapter_class: Type[BaseIDEAdapter]) -> Type[BaseIDEAdapter]:
    """注册适配器类（装饰器语法）。

    Usage:
        @register_adapter
        class MyAdapter(BaseIDEAdapter):
            ...
    """
    return _registry.register(adapter_class)


def get_adapter(ide_type: IDEType | str) -> BaseIDEAdapter:
    """获取适配器实例。

    Args:
        ide_type: IDE 类型或名称

    Returns:
        BaseIDEAdapter: 适配器实例

    Raises:
        ValueError: 如果适配器未注册
    """
    return _registry.get(ide_type)


def list_adapters(skill: bool = False, mcp: bool = False) -> list[BaseIDEAdapter]:
    """列出所有已注册的适配器。

    Args:
        skill: 是否只返回支持 Skill 的适配器
        mcp: 是否只返回支持 MCP 的适配器

    Returns:
        list[BaseIDEAdapter]: 适配器实例列表
    """
    return _registry.list_by_feature(skill=skill, mcp=mcp)


def get_all_ide_types() -> list[IDEType]:
    """获取所有已注册的 IDE 类型。

    Returns:
        list[IDEType]: IDE 类型列表
    """
    return [adapter.ide_type for adapter in _registry.list_adapters()]


def get_adapter_info() -> list[dict]:
    """获取所有适配器的信息。

    Returns:
        list[dict]: 适配器信息字典列表
    """
    return [
        {
            "type": adapter.ide_type.value,
            "name": adapter.display_name,
            "description": adapter.description,
            "supports_skill": adapter.supports_skill,
            "supports_mcp": adapter.supports_mcp,
            "skill_path": adapter.skill_file_path,
            "mcp_path": adapter.mcp_config_path,
        }
        for adapter in _registry.list_adapters()
    ]
