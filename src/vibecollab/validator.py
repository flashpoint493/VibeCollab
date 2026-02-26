"""
配置验证器 - 完整的配置检查和报告系统

提供更全面的配置验证，包括：
- 必需字段检查
- 数据类型验证
- 值范围检查
- 配置完整性验证
- 格式化输出
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ValidationErrorLevel(Enum):
    """验证错误级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    level: ValidationErrorLevel
    message: str
    suggestion: Optional[str] = None

    def __str__(self):
        emoji = {
            ValidationErrorLevel.ERROR: "❌",
            ValidationErrorLevel.WARNING: "⚠️",
            ValidationErrorLevel.INFO: "ℹ️",
        }
        s = f"{emoji[self.level]} {self.field}: {self.message}"
        if self.suggestion:
            s += f"\n   💡 {self.suggestion}"
        return s


@dataclass
class ConfigValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    infos: List[ValidationError] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def add_error(self, field: str, message: str, suggestion: Optional[str] = None):
        """添加错误"""
        self.errors.append(ValidationError(
            field=field,
            level=ValidationErrorLevel.ERROR,
            message=message,
            suggestion=suggestion
        ))

    def add_warning(self, field: str, message: str, suggestion: Optional[str] = None):
        """添加警告"""
        self.warnings.append(ValidationError(
            field=field,
            level=ValidationErrorLevel.WARNING,
            message=message,
            suggestion=suggestion
        ))

    def add_info(self, field: str, message: str):
        """添加信息"""
        self.infos.append(ValidationError(
            field=field,
            level=ValidationErrorLevel.INFO,
            message=message
        ))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [str(e) for e in self.errors],
            "warnings": [str(w) for w in self.warnings],
        }


class ConfigValidator:
    """配置验证器"""

    # 必需字段
    REQUIRED_FIELDS = {
        "project.name",
        "project.version",
        "project.domain",
    }

    # 有效的决策级别
    VALID_DECISION_LEVELS = {"S", "A", "B", "C"}

    # 有效的项目领域
    VALID_DOMAINS = {
        "generic", "game", "web", "data", "mobile", "ai", "backend",
    }

    # 优先级范围
    PRIORITY_RANGE = (0, 100)

    def __init__(self, config: Dict[str, Any]):
        """初始化验证器

        Args:
            config: 配置字典
        """
        self.config = config

    def validate(self) -> ConfigValidationResult:
        """执行完整验证

        Returns:
            ConfigValidationResult 对象
        """
        result = ConfigValidationResult()

        # 1. 验证必需字段
        self._validate_required_fields(result)

        # 2. 验证项目配置
        self._validate_project_config(result)

        # 3. 验证角色配置
        self._validate_roles(result)

        # 4. 验证决策级别
        self._validate_decision_levels(result)

        # 5. 验证哲学配置
        self._validate_philosophy(result)

        # 6. 验证测试配置
        self._validate_testing(result)

        # 7. 验证里程碑配置
        self._validate_milestone(result)

        # 8. 验证多开发者配置
        self._validate_multi_developer(result)

        # 设置验证结果
        result.is_valid = not result.has_errors

        return result

    def _validate_required_fields(self, result: ConfigValidationResult):
        """验证必需字段"""
        for field in self.REQUIRED_FIELDS:
            parts = field.split('.')
            value = self.config

            for part in parts:
                if not isinstance(value, dict):
                    result.add_error(field, f"字段路径 {field} 中 {part} 不是字典类型")
                    break
                value = value.get(part)
                if value is None:
                    result.add_error(field, f"缺少必需字段")
                    break

    def _validate_project_config(self, result: ConfigValidationResult):
        """验证项目配置"""
        project = self.config.get("project", {})

        # 验证领域
        domain = project.get("domain")
        if domain and domain not in self.VALID_DOMAINS:
            result.add_warning(
                "project.domain",
                f"未知的领域: {domain}",
                suggestion=f"有效领域: {', '.join(self.VALID_DOMAINS)}"
            )

        # 验证版本格式
        version = project.get("version")
        if version and not self._is_valid_version(version):
            result.add_warning(
                "project.version",
                f"版本格式可能不符合语义化版本: {version}",
                suggestion="建议使用格式: major.minor.patch (如 1.0.0)"
            )

    def _validate_roles(self, result: ConfigValidationResult):
        """验证角色配置"""
        roles = self.config.get("roles", [])

        if not roles:
            result.add_warning(
                "roles",
                "未定义任何角色",
                suggestion="建议定义至少一个角色 (如 DEV, PM, QA)"
            )
            return

        # 检查角色代码唯一性
        codes = set()
        for i, role in enumerate(roles):
            code = role.get("code")
            if not code:
                result.add_error("roles", f"角色 {i} 缺少 'code' 字段")
                continue

            if code in codes:
                result.add_error("roles", f"角色代码重复: {code}")
            codes.add(code)

            # 检查必填字段
            if "name" not in role:
                result.add_error("roles", f"角色 {code} 缺少 'name' 字段")

            # 检查 gatekeeper 数量
            if role.get("is_gatekeeper"):
                result.add_info(
                    f"roles.{code}",
                    f"角色 {code} 是 gatekeeper"
                )

    def _validate_decision_levels(self, result: ConfigValidationResult):
        """验证决策级别配置"""
        levels = self.config.get("decision_levels", [])

        if not levels:
            result.add_warning(
                "decision_levels",
                "未定义决策级别",
                suggestion="建议定义至少一个决策级别 (S, A, B, C)"
            )
            return

        valid_codes = set()
        for level in levels:
            code = level.get("level")
            if not code:
                result.add_error("decision_levels", "决策级别缺少 'level' 字段")
                continue

            if code not in self.VALID_DECISION_LEVELS:
                result.add_error(
                    "decision_levels",
                    f"无效的决策级别: {code}",
                    suggestion=f"有效级别: {', '.join(self.VALID_DECISION_LEVELS)}"
                )
                continue

            if code in valid_codes:
                result.add_error("decision_levels", f"决策级别重复: {code}")
            valid_codes.add(code)

    def _validate_philosophy(self, result: ConfigValidationResult):
        """验证哲学配置"""
        philosophy = self.config.get("philosophy", {})

        # 检查决策质量配置
        decision_quality = philosophy.get("decision_quality", {})
        if decision_quality:
            target = decision_quality.get("target_rate")
            if target is not None:
                if not (0 <= target <= 1):
                    result.add_error(
                        "philosophy.decision_quality.target_rate",
                        f"目标决策质量率必须在 0-1 之间: {target}"
                    )

            tolerance = decision_quality.get("critical_tolerance")
            if tolerance is not None:
                if not (0 <= tolerance <= 1):
                    result.add_error(
                        "philosophy.decision_quality.critical_tolerance",
                        f"关键容错率必须在 0-1 之间: {tolerance}"
                    )

    def _validate_testing(self, result: ConfigValidationResult):
        """验证测试配置"""
        testing = self.config.get("testing", {})

        if not testing:
            result.add_warning(
                "testing",
                "未配置测试相关设置",
                suggestion="建议配置 unit_test 和 product_qa"
            )
            return

        # 检查单元测试配置
        unit_test = testing.get("unit_test")
        if unit_test:
            coverage_target = unit_test.get("coverage_target")
            if coverage_target is not None:
                if not (0 <= coverage_target <= 100):
                    result.add_error(
                        "testing.unit_test.coverage_target",
                        f"代码覆盖率目标必须在 0-100 之间: {coverage_target}"
                    )

    def _validate_milestone(self, result: ConfigValidationResult):
        """验证里程碑配置"""
        milestone = self.config.get("milestone", {})

        if not milestone:
            result.add_warning(
                "milestone",
                "未配置里程碑",
                suggestion="建议配置当前里程碑和发布计划"
            )
            return

        # 检查优先级定义
        priorities = milestone.get("bug_priorities")
        if priorities:
            for i, priority in enumerate(priorities):
                level = priority.get("level")
                if level and not (0 <= level <= 5):
                    result.add_error(
                        f"milestone.bug_priorities.{i}",
                        f"Bug 优先级必须在 0-5 之间: {level}"
                    )

    def _validate_multi_developer(self, result: ConfigValidationResult):
        """验证多开发者配置"""
        multi_dev = self.config.get("multi_developer", {})

        if multi_dev.get("enabled"):
            result.add_info(
                "multi_developer",
                "多开发者模式已启用"
            )

            # 检查 LLM 配置
            llm_client = self.config.get("llm_client", {})
            if not llm_client.get("provider") or not llm_client.get("api_key"):
                result.add_warning(
                    "multi_developer",
                    "多开发者模式需要配置 LLM 客户端",
                    suggestion="在 llm_client 配置中设置 provider 和 api_key"
                )

    def validate(self) -> ConfigValidationResult:
        """执行完整验证

        Returns:
            ConfigValidationResult 对象
        """
        result = ConfigValidationResult(is_valid=False)

        # 1. 验证必需字段
        self._validate_required_fields(result)

        # 2. 验证项目配置
        self._validate_project_config(result)

        # 3. 验证角色配置
        self._validate_roles(result)

        # 4. 验证决策级别
        self._validate_decision_levels(result)

        # 5. 验证哲学配置
        self._validate_philosophy(result)

        # 6. 验证测试配置
        self._validate_testing(result)

        # 7. 验证里程碑配置
        self._validate_milestone(result)

        # 8. 验证多开发者配置
        self._validate_multi_developer(result)

        # 设置验证结果
        result.is_valid = not result.has_errors

        return result

    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """检查版本是否有效"""
        import re
        # 简单的语义化版本检查
        pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.\d+)?)?(\+[a-zA-Z0-9]+(\.\d+)?)?$"
        return bool(re.match(pattern, version))
