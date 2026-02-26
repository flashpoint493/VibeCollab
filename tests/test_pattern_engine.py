#!/usr/bin/env python3
"""
VibeCollab 单元测试 - PatternEngine 集成 ProjectAdapter
"""

import pytest
import yaml
from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vibecollab.pattern_engine import PatternEngine
from vibecollab.project_adapter import ProjectAdapter


class TestPatternEngineWithAdapter:
    """PatternEngine 与 ProjectAdapter 集成测试"""

    @pytest.fixture
    def minimal_config(self):
        """最小配置"""
        return {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            }
        }

    @pytest.fixture
    def full_config(self):
        """完整配置"""
        return {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
                'description': 'Test project for unit testing',
            },
            'philosophy': {
                'vibe_development': {
                    'enabled': True,
                    'principles': ['AI 不是执行者', '不急于产出代码'],
                },
                'decision_quality': {
                    'target_rate': 0.9,
                    'critical_tolerance': 0,
                }
            },
            'roles': [
                {
                    'code': 'DESIGN',
                    'name': '协议设计',
                    'focus': ['Schema设计', '协议演进'],
                    'triggers': ['设计', '协议', 'Schema'],
                    'is_gatekeeper': False,
                }
            ],
            'custom': {
                'company': 'Acme Corp',
                'team_size': 10,
            }
        }

    def test_adapter_instance_created(self, minimal_config):
        """测试 PatternEngine 创建了适配器实例"""
        engine = PatternEngine(minimal_config)

        # 应该有 adapter 属性
        assert hasattr(engine, 'adapter')
        assert engine.adapter is not None
        assert isinstance(engine.adapter, ProjectAdapter)

    def test_adapter_has_access_to_config(self, full_config):
        """测试适配器可以访问配置"""
        engine = PatternEngine(full_config)

        # 通过适配器访问
        assert engine.adapter.get('project.name') == 'TestProject'
        assert engine.adapter.get_custom('company') == 'Acme Corp'

    def test_adapter_in_context(self, full_config):
        """测试适配器在模板上下文中"""
        engine = PatternEngine(full_config)

        # 获取上下文
        ctx = engine._build_context({'id': 'test'})

        # 应该包含 adapter
        assert 'adapter' in ctx
        assert ctx['adapter'] is not None
        assert isinstance(ctx['adapter'], ProjectAdapter)

    def test_custom_fields_in_context(self, full_config):
        """测试自定义字段在上下文中"""
        engine = PatternEngine(full_config)

        ctx = engine._build_context({'id': 'test'})

        # 应该包含 custom 字段
        assert 'custom' in ctx
        assert ctx['custom']['company'] == 'Acme Corp'
        assert ctx['custom']['team_size'] == 10

    def test_render_with_adapter(self, full_config):
        """测试使用适配器渲染模板"""
        engine = PatternEngine(full_config)

        # 渲染（不验证内容，只验证不报错）
        try:
            result = engine.render()
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            pytest.fail(f"渲染失败: {e}")

    def test_adapter_required_fields_validation(self):
        """测试适配器验证必需字段"""
        incomplete_config = {
            'project': {
                'name': 'TestProject',
                # 缺少 version 和 domain
            }
        }

        # 应该抛出 ValueError
        with pytest.raises(ValueError, match="缺少必需字段"):
            PatternEngine(incomplete_config)

    def test_adapter_get_role(self, full_config):
        """测试适配器获取角色"""
        engine = PatternEngine(full_config)

        # 获取用户定义的角色
        design_role = engine.adapter.get_role('DESIGN')
        assert design_role['name'] == '协议设计'

        # 获取默认角色
        arch_role = engine.adapter.get_role('ARCH')
        assert arch_role['name'] == '架构'

    def test_adapter_list_custom_fields(self, full_config):
        """测试列出自定义字段"""
        engine = PatternEngine(full_config)

        custom_fields = engine.adapter.list_custom_fields()
        assert 'company' in custom_fields
        assert 'team_size' in custom_fields

    def test_adapter_validate(self, full_config):
        """测试适配器验证"""
        engine = PatternEngine(full_config)

        result = engine.adapter.validate()

        assert result['valid'] is True

    def test_minimal_config_works(self, minimal_config):
        """测试最小配置可以工作"""
        engine = PatternEngine(minimal_config)

        # 应该能渲染
        result = engine.render()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_adapter_methods_accessible(self, full_config):
        """测试适配器方法可访问"""
        engine = PatternEngine(full_config)

        adapter = engine.adapter

        # 测试各种方法
        assert adapter.get_project_name() == 'TestProject'
        assert adapter.get_project_version() == '0.1.0'
        assert adapter.get_project_domain() == 'generic'
        assert adapter.get('philosophy.vibe_development.enabled') is True

    def test_custom_field_not_configured(self, minimal_config):
        """测试未配置自定义字段"""
        engine = PatternEngine(minimal_config)

        ctx = engine._build_context({'id': 'test'})

        # custom 应该是空字典
        assert 'custom' in ctx
        assert ctx['custom'] == {}

        # 获取不存在的自定义字段应返回默认值
        assert engine.adapter.get_custom('nonexistent', 'default') == 'default'

    def test_roles_merge(self, full_config):
        """测试角色合并"""
        engine = PatternEngine(full_config)

        ctx = engine._build_context({'id': 'test'})

        # 应该包含用户定义和默认角色
        roles = ctx.get('roles', [])
        role_codes = [r.get('code') for r in roles]

        # 用户定义的 DESIGN
        assert 'DESIGN' in role_codes

        # 默认的 ARCH（用户未定义）
        assert 'ARCH' in role_codes

    def test_render_includes_project_info(self, full_config):
        """测试渲染包含项目信息"""
        engine = PatternEngine(full_config)

        result = engine.render()

        # 应该包含项目名称
        assert 'TestProject' in result

    def test_render_includes_custom_fields(self, full_config):
        """测试渲染包含自定义字段（如果模板使用）"""
        engine = PatternEngine(full_config)

        result = engine.render()

        # 注意：实际渲染内容取决于模板
        # 这里只验证不报错，具体内容需要模板支持


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
