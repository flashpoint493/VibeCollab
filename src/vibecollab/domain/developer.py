"""
Developer/Role management module

DEPRECATED: This module is kept for backward compatibility.
Use role.RoleManager instead for new code.
"""

from .role import RoleManager, ContextAggregator

# Backward compatibility: DeveloperManager is now an alias for RoleManager
DeveloperManager = RoleManager

__all__ = ["RoleManager", "DeveloperManager", "ContextAggregator"]
