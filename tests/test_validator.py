"""
Validator 模块单元测试
"""

import pytest

from vibecollab.validator import (
    ConfigValidator,
    ConfigValidationResult,
    ValidationError,
    ValidationErrorLevel,
)


class TestConfigValidationResult:
    """测试 ConfigValidationResult"""

    def test_create_result(self):
        """测试创建验证结果"""
        result = ConfigValidationResult(is_valid=False)

        assert result.is_valid is False
        assert result.has_errors is False
        assert result.has_warnings is False

    def test_add_error(self):
        """测试添加错误"""
        result = ConfigValidationResult(is_valid=False)

        result.add_error("test.field", "测试错误", "建议修复")

        assert result.has_errors is True
        assert len(result.errors) == 1
        assert result.errors[0].field == "test.field"

    def test_add_warning(self):
        """测试添加警告"""
        result = ConfigValidationResult(is_valid=False)

        result.add_warning("test.field", "测试警告", "建议优化")

        assert result.has_warnings is True
        assert len(result.warnings) == 1

    def test_add_info(self):
        """测试添加信息"""
        result = ConfigValidationResult(is_valid=False)

        result.add_info("test.field", "测试信息")

        assert len(result.infos) == 1

    def test_to_dict(self):
        """测试转换为字典"""
        result = ConfigValidationResult(is_valid=False)

        result.add_error("field1", "error1")
        result.add_warning("field2", "warning1")
        result.add_info("field3", "info1")

        data = result.to_dict()

        assert data["is_valid"] is False
        assert data["error_count"] == 1
        assert data["warning_count"] == 1
        assert len(data["errors"]) == 1
        assert len(data["warnings"]) == 1


class TestValidationError:
    """测试 ValidationError"""

    def test_create_error(self):
        """测试创建错误"""
        error = ValidationError(
            field="test.field",
            level=ValidationErrorLevel.ERROR,
            message="测试错误"
        )

        assert error.field == "test.field"
        assert error.level == ValidationErrorLevel.ERROR
        assert error.message == "测试错误"

    def test_str_with_suggestion(self):
        """测试字符串输出（带建议）"""
        error = ValidationError(
            field="test.field",
            level=ValidationErrorLevel.ERROR,
            message="测试错误",
            suggestion="建议修复"
        )

        s = str(error)
        assert "❌" in s
        assert "test.field" in s
        assert "测试错误" in s
        assert "💡" in s
        assert "建议修复" in s


class TestConfigValidator:
    """测试 ConfigValidator"""

    def test_minimal_config(self):
        """测试最小配置"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "generic",
            }
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_required_fields(self):
        """测试缺少必需字段"""
        config = {
            "project": {
                "name": "Test",
            }
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_invalid_domain(self):
        """测试无效领域"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "invalid-domain",
            }
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert result.is_valid is True  # 无错误，只有警告
        assert len(result.warnings) > 0
        assert "未知的领域" in result.warnings[0].message

    def test_no_roles_warning(self):
        """测试无角色警告"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "generic",
            },
            "roles": [],
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert len(result.warnings) > 0
        assert "未定义任何角色" in result.warnings[0].message

    def test_role_missing_code(self):
        """测试角色缺少 code"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "generic",
            },
            "roles": [
                {"name": "Developer"},
            ]
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert len(result.errors) > 0
        assert "缺少 'code' 字段" in result.errors[0].message

    def test_role_duplicate_code(self):
        """测试角色代码重复"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "generic",
            },
            "roles": [
                {"code": "DEV", "name": "Developer"},
                {"code": "DEV", "name": "Dev"},
            ]
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert len(result.errors) > 0
        assert "角色代码重复" in result.errors[0].message

    def test_invalid_decision_level(self):
        """测试无效决策级别"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "generic",
            },
            "decision_levels": [
                {"level": "X", "name": "Invalid"},
            ]
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert len(result.errors) > 0
        assert "无效的决策级别" in result.errors[0].message

    def test_decision_quality_range(self):
        """测试决策质量范围"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "generic",
            },
            "philosophy": {
                "decision_quality": {
                    "target_rate": 1.5,  # 超出范围
                }
            }
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert len(result.errors) > 0
        assert "必须在 0-1 之间" in result.errors[0].message

    def test_coverage_target_range(self):
        """测试覆盖率目标范围"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "generic",
            },
            "testing": {
                "unit_test": {
                    "coverage_target": 150,  # 超出范围
                }
            }
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        assert len(result.errors) > 0
        assert "必须在 0-100 之间" in result.errors[0].message

    def test_multi_dev_without_llm(self):
        """测试多开发者模式无 LLM 配置"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.0.0",
                "domain": "generic",
            },
            "roles": [  # 添加默认角色避免警告
                {"code": "DEV", "name": "Developer"}
            ],
            "multi_developer": {
                "enabled": True,
            }
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        llm_warnings = [
            w for w in result.warnings
            if "LLM 客户端" in w.message
        ]
        assert len(llm_warnings) > 0

    def test_valid_version_format(self):
        """测试有效版本格式"""
        config = {
            "project": {
                "name": "Test",
                "version": "1.2.3",
                "domain": "generic",
            }
        }

        validator = ConfigValidator(config)
        result = validator.validate()

        # 应该没有版本格式警告
        version_warnings = [
            w for w in result.warnings
            if "版本格式" in w.message
        ]
        assert len(version_warnings) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
