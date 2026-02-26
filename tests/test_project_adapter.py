#!/usr/bin/env python3
"""
VibeCollab 单元测试 - ProjectAdapter
"""

import pytest
import yaml
from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vibecollab.project_adapter import ProjectAdapter


class TestProjectAdapter:
    """ProjectAdapter 单元测试"""

    def test_required_fields_validation(self):
        """测试必需字段验证"""
        # 缺少必需字段应该抛出异常
        incomplete_config = {
            'project': {
                'name': 'TestProject',
                # 缺少 version 和 domain
            }
        }

        with pytest.raises(ValueError, match="缺少必需字段"):
            ProjectAdapter(incomplete_config)

    def test_complete_config_passes_validation(self):
        """测试完整配置通过验证"""
        complete_config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            }
        }

        adapter = ProjectAdapter(complete_config)
        assert adapter is not None

    def test_get_simple_field(self):
        """测试简单字段获取"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            }
        }

        adapter = ProjectAdapter(config)

        assert adapter.get('project.name') == 'TestProject'
        assert adapter.get('project.version') == '0.1.0'
        assert adapter.get('project.domain') == 'generic'

    def test_get_dot_notation(self):
        """测试点路径解析"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'philosophy': {
                'vibe_development': {
                    'enabled': True,
                    'principles': ['principle1', 'principle2'],
                }
            }
        }

        adapter = ProjectAdapter(config)

        assert adapter.get('philosophy.vibe_development.enabled') is True
        assert adapter.get('philosophy.vibe_development.principles') == [
            'principle1', 'principle2'
        ]

    def test_get_with_default(self):
        """测试默认值"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            }
        }

        adapter = ProjectAdapter(config)

        # 不存在的字段返回默认值
        assert adapter.get('nonexistent.field', 'default') == 'default'
        assert adapter.get('project.description', 'No description') == 'No description'

    def test_get_role_default(self):
        """测试获取默认角色"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            }
        }

        adapter = ProjectAdapter(config)

        # 获取默认角色
        design_role = adapter.get_role('DESIGN')
        assert design_role['name'] == '协议设计'
        assert 'Schema设计' in design_role['focus']

        arch_role = adapter.get_role('ARCH')
        assert arch_role['name'] == '架构'

    def test_get_role_user_override(self):
        """测试用户角色覆盖默认角色"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'roles': [
                {
                    'code': 'DESIGN',
                    'name': '自定义设计',
                    'focus': ['自定义关注点'],
                    'triggers': [],
                    'is_gatekeeper': False,
                }
            ]
        }

        adapter = ProjectAdapter(config)

        # 应该返回用户定义的角色
        design_role = adapter.get_role('DESIGN')
        assert design_role['name'] == '自定义设计'
        assert design_role['focus'] == ['自定义关注点']

    def test_get_roles_merge(self):
        """测试角色合并"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'roles': [
                {
                    'code': 'CUSTOM_ROLE',
                    'name': '自定义角色',
                    'focus': [],
                    'triggers': [],
                    'is_gatekeeper': False,
                }
            ]
        }

        adapter = ProjectAdapter(config)

        all_roles = adapter.get_roles()

        # 应该包含默认角色和自定义角色
        role_codes = [r.get('code') for r in all_roles]
        assert 'DESIGN' in role_codes  # 默认
        assert 'ARCH' in role_codes    # 默认
        assert 'CUSTOM_ROLE' in role_codes  # 自定义

    def test_get_custom_field(self):
        """测试获取自定义字段"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'custom': {
                'company': 'Acme Corp',
                'team_size': 10,
                'sprint_days': 14,
            }
        }

        adapter = ProjectAdapter(config)

        assert adapter.get_custom('company') == 'Acme Corp'
        assert adapter.get_custom('team_size') == 10
        assert adapter.get_custom('sprint_days') == 14

    def test_get_custom_with_default(self):
        """测试自定义字段默认值"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'custom': {
                'company': 'Acme Corp',
            }
        }

        adapter = ProjectAdapter(config)

        assert adapter.get_custom('company') == 'Acme Corp'
        assert adapter.get_custom('nonexistent', 'default') == 'default'

    def test_has_custom(self):
        """测试检查自定义字段是否存在"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'custom': {
                'company': 'Acme Corp',
            }
        }

        adapter = ProjectAdapter(config)

        assert adapter.has_custom('company') is True
        assert adapter.has_custom('nonexistent') is False

    def test_list_custom_fields(self):
        """测试列出所有自定义字段"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'custom': {
                'company': 'Acme Corp',
                'team_size': 10,
                'sprint_days': 14,
            }
        }

        adapter = ProjectAdapter(config)

        custom_fields = adapter.list_custom_fields()
        assert 'company' in custom_fields
        assert 'team_size' in custom_fields
        assert 'sprint_days' in custom_fields
        assert len(custom_fields) == 3

    def test_is_multi_dev_enabled(self):
        """测试多开发者模式检查"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'multi_developer': {
                'enabled': True,
            }
        }

        adapter = ProjectAdapter(config)
        assert adapter.is_multi_dev_enabled() is True

        # 禁用
        config['multi_developer']['enabled'] = False
        adapter = ProjectAdapter(config)
        assert adapter.is_multi_dev_enabled() is False

    def test_is_agent_mode_enabled(self):
        """测试 Agent 模式检查"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'llm_client': {
                'provider': 'openai',
                'api_key': 'test-key',
                'model': 'gpt-4',
            }
        }

        adapter = ProjectAdapter(config)
        assert adapter.is_agent_mode_enabled() is True

        # 缺少 api_key
        config['llm_client']['api_key'] = None
        adapter = ProjectAdapter(config)
        assert adapter.is_agent_mode_enabled() is False

    def test_validate_success(self):
        """测试验证成功"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'roles': [],
            'philosophy': {},
            'lifecycle': {},
            'llm_client': {
                'provider': 'openai',
                'api_key': 'test',
            }
        }

        adapter = ProjectAdapter(config)
        result = adapter.validate()

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_warnings(self):
        """测试验证警告"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            }
            # 缺少推荐字段
        }

        adapter = ProjectAdapter(config)
        result = adapter.validate()

        # 应该有警告但有效
        assert result['valid'] is True
        assert len(result['warnings']) > 0
        assert any('roles' in w for w in result['warnings'])
        assert any('philosophy' in w for w in result['warnings'])

    def test_validate_agent_mode_warning(self):
        """测试 Agent 模式警告"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            },
            'multi_developer': {
                'enabled': True,
            }
            # 缺少 llm_client
        }

        adapter = ProjectAdapter(config)
        result = adapter.validate()

        # 应该有 Agent 模式警告
        assert any('llm_client' in w for w in result['warnings'])
        assert any('Agent' in w for w in result['warnings'])

    def test_to_dict(self):
        """测试转换为字典"""
        config = {
            'project': {
                'name': 'TestProject',
                'version': '0.1.0',
                'domain': 'generic',
            }
        }

        adapter = ProjectAdapter(config)
        result = adapter.to_dict()

        assert result == config


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
