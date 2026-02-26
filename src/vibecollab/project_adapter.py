"""
Project Adapter - 配置适配器

提供向后兼容的配置访问和扩展性支持。

Design principles:
- 必需字段验证，防止配置错误
- 安全的字段访问，支持点路径
- 提供默认值，增强容错性
- 支持自定义字段，提高扩展性
- 向后兼容，不破坏现有配置
"""

from typing import Any, Dict, List, Optional


class ProjectAdapter:
    """项目配置适配器

    提供安全的配置访问、默认值支持、自定义字段支持。
    解决用户自定义 project.yaml 字段时的兼容性问题。
    """

    # 必需字段
    REQUIRED_FIELDS = frozenset({
        'project.name',
        'project.version',
        'project.domain',
    })

    # 默认角色定义
    DEFAULT_ROLES: Dict[str, Dict[str, Any]] = {
        'DESIGN': {
            'name': '协议设计',
            'focus': ['Schema设计', '协议演进', '用户体验'],
            'triggers': ['设计', '协议', 'Schema'],
            'is_gatekeeper': False,
        },
        'ARCH': {
            'name': '架构',
            'focus': ['模块结构', '扩展机制', '性能'],
            'triggers': ['架构', '重构', '模块'],
            'is_gatekeeper': False,
        },
        'DEV': {
            'name': '开发',
            'focus': ['功能实现', 'Bug修复'],
            'triggers': ['开发', '实现', '代码'],
            'is_gatekeeper': False,
        },
        'PM': {
            'name': '项目管理',
            'focus': ['里程碑', '发布', '优先级'],
            'triggers': ['规划', '发布', '里程碑'],
            'is_gatekeeper': False,
        },
        'QA': {
            'name': '产品质量保证',
            'focus': ['验收测试', '用户体验验证'],
            'triggers': ['验收', '体验测试'],
            'is_gatekeeper': True,
        },
        'TEST': {
            'name': '单元测试',
            'focus': ['pytest', '覆盖率'],
            'triggers': ['单元测试', 'pytest'],
            'is_gatekeeper': False,
        },
    }

    def __init__(self, config: Dict[str, Any]):
        """初始化适配器

        Args:
            config: 项目配置字典（从 project.yaml 加载）

        Raises:
            ValueError: 缺少必需字段
        """
        self.config = config
        self._validate_required()

    def _validate_required(self) -> None:
        """验证必需字段

        Raises:
            ValueError: 缺少必需字段时抛出
        """
        missing = []

        for field in self.REQUIRED_FIELDS:
            parts = field.split('.')
            value = self.config

            for part in parts:
                if not isinstance(value, dict):
                    missing.append(field)
                    break
                value = value.get(part)
                if value is None:
                    missing.append(field)
                    break

        if missing:
            raise ValueError(
                f"缺少必需字段: {', '.join(missing)}. "
                f"请参考 CONTRIBUTING_AI.md 配置项目。"
            )

    def get(self, path: str, default: Any = None) -> Any:
        """安全获取字段，支持点路径

        Args:
            path: 字段路径，如 'project.name' 或 'philosophy.vibe_development.enabled'
            default: 默认值，字段不存在时返回

        Returns:
            字段值，或默认值

        Examples:
            >>> adapter.get('project.name')
            'VibeCollab'

            >>> adapter.get('philosophy.vibe_development.enabled', False)
            True

            >>> adapter.get('custom.some_field', 'default')
            'default'
        """
        parts = path.split('.')
        value = self.config

        for part in parts:
            if not isinstance(value, dict):
                return default
            value = value.get(part)
            if value is None:
                return default

        return value

    def get_role(self, code: str) -> Dict[str, Any]:
        """获取角色定义

        优先返回用户配置的角色，不存在则返回默认角色。

        Args:
            code: 角色代码，如 'DESIGN', 'ARCH'

        Returns:
            角色定义字典

        Examples:
            >>> adapter.get_role('DESIGN')
            {
                'name': '协议设计',
                'focus': ['Schema设计', '协议演进'],
                ...
            }
        """
        # 先查找用户配置的角色
        user_roles = self.get('roles', [])
        for role in user_roles:
            if role.get('code') == code:
                return role

        # 返回默认角色
        return self.DEFAULT_ROLES.get(code, {})

    def get_roles(self) -> List[Dict[str, Any]]:
        """获取所有角色定义

        合并用户配置和默认角色，用户配置优先。
        支持两种用户配置格式：
        1. 列表格式: [{'code': 'DESIGN', 'name': '...', ...}]
        2. 字典格式: {'DESIGN': {'name': '...', ...}}

        Returns:
            角色定义列表（统一为列表格式，每个角色包含 'code' 字段）
        """
        user_roles_raw = self.get('roles', [])

        # 将用户角色转换为统一列表格式
        user_roles = []
        user_role_codes = set()

        if isinstance(user_roles_raw, dict):
            # 字典格式: {'DESIGN': {...}, 'ARCH': {...}}
            for code, role_data in user_roles_raw.items():
                user_roles.append({'code': code, **role_data})
                user_role_codes.add(code)
        elif isinstance(user_roles_raw, list):
            # 列表格式: [{'code': 'DESIGN', ...}, ...]
            user_roles = user_roles_raw[:]
            user_role_codes = {role.get('code') for role in user_roles if role}

        # 合并默认角色（排除用户已配置的）
        for code, default_role in self.DEFAULT_ROLES.items():
            if code not in user_role_codes:
                # 默认角色需要添加 'code' 字段
                user_roles.append({'code': code, **default_role})

        return user_roles

    def get_custom(self, key: str, default: Any = None) -> Any:
        """获取自定义字段

        从 custom.* 命名空间获取字段。

        Args:
            key: 自定义字段名
            default: 默认值

        Returns:
            自定义字段值

        Examples:
            >>> adapter.get_custom('company', 'Unknown')
            'Acme Corp'

            >>> adapter.get_custom('team_size', 5)
            10
        """
        return self.get(f'custom.{key}', default)

    def has_custom(self, key: str) -> bool:
        """检查是否存在自定义字段

        Args:
            key: 自定义字段名

        Returns:
            是否存在该字段
        """
        return self.get_custom(key) is not None

    def list_custom_fields(self) -> List[str]:
        """列出所有自定义字段

        Returns:
            自定义字段名列表
        """
        custom = self.get('custom', {})
        if not isinstance(custom, dict):
            return []
        return list(custom.keys())

    def get_philosophy(self, key: str, default: Any = None) -> Any:
        """获取哲学配置

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self.get(f'philosophy.{key}', default)

    def get_lifecycle(self, key: str, default: Any = None) -> Any:
        """获取生命周期配置

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self.get(f'lifecycle.{key}', default)

    def is_multi_dev_enabled(self) -> bool:
        """检查多开发者模式是否启用

        Returns:
            是否启用多开发者模式
        """
        return self.get('multi_developer.enabled', False)

    def is_agent_mode_enabled(self) -> bool:
        """检查 Agent 模式是否可用

        Returns:
            Agent 模式是否可用
        """
        # 需要 llm_client 配置
        llm_client = self.get('llm_client', {})
        return bool(llm_client.get('provider') and llm_client.get('api_key'))

    def get_project_name(self) -> str:
        """获取项目名称

        Returns:
            项目名称
        """
        return self.get('project.name', 'Unknown')

    def get_project_version(self) -> str:
        """获取项目版本

        Returns:
            项目版本
        """
        return self.get('project.version', '0.0.0')

    def get_project_domain(self) -> str:
        """获取项目领域

        Returns:
            项目领域
        """
        return self.get('project.domain', 'generic')

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            包含所有配置的字典
        """
        return self.config

    def validate(self) -> Dict[str, Any]:
        """验证配置

        Returns:
            验证结果字典，包含：
            - valid: 是否有效
            - errors: 错误列表
            - warnings: 警告列表
        """
        errors = []
        warnings = []

        # 1. 验证必需字段（已在 __init__ 中完成）

        # 2. 检查推荐字段
        recommended_fields = [
            'roles',
            'philosophy',
            'lifecycle',
            'decision_quality',
        ]

        for field in recommended_fields:
            if self.get(field) is None:
                warnings.append(f"缺少推荐字段: {field} (将使用默认值)")

        # 3. 检查 Agent 模式依赖
        if self.is_multi_dev_enabled() and not self.is_agent_mode_enabled():
            warnings.append(
                "多开发者模式已启用，但 llm_client 未配置，Agent 模式将无法使用"
            )

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
        }
