"""
Tests for LLMContext Generator
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from vibecollab import LLMContextGenerator, Project


class TestLLMContextGenerator:
    """Generator 测试"""

    def test_generate_basic(self):
        """测试基础生成"""
        config = {
            "project": {
                "name": "TestProject",
                "version": "v1.0",
                "domain": "generic"
            },
            "philosophy": {
                "vibe_development": {
                    "enabled": True,
                    "principles": ["Test principle"]
                },
                "decision_quality": {
                    "target_rate": 0.9,
                    "critical_tolerance": 0
                }
            },
            "roles": [
                {
                    "code": "DEV",
                    "name": "开发",
                    "focus": ["实现"],
                    "triggers": ["开发"],
                    "is_gatekeeper": False
                }
            ],
            "decision_levels": [
                {
                    "level": "S",
                    "name": "战略决策",
                    "scope": "整体方向",
                    "review": {"required": True, "mode": "sync"}
                }
            ]
        }
        
        generator = LLMContextGenerator(config)
        content = generator.generate()
        
        assert "TestProject" in content
        assert "Vibe Development" in content
        assert "[DEV]" in content

    def test_validate_missing_project(self):
        """测试验证：缺少 project"""
        config = {}
        generator = LLMContextGenerator(config)
        errors = generator.validate()
        
        assert len(errors) > 0
        assert any("project" in e for e in errors)

    def test_validate_invalid_decision_level(self):
        """测试验证：无效决策级别"""
        config = {
            "project": {"name": "Test"},
            "decision_levels": [
                {"level": "X", "name": "Invalid"}
            ]
        }
        generator = LLMContextGenerator(config)
        errors = generator.validate()
        
        assert any("决策级别" in e or "level" in e.lower() for e in errors)


class TestProject:
    """Project 测试"""

    def test_create_project(self):
        """测试创建项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            project = Project.create(
                name="TestProject",
                domain="generic",
                output_dir=output_dir
            )
            project.generate_all()
            
            # 检查文件是否生成
            assert (output_dir / "CONTRIBUTING_AI.md").exists()
            assert (output_dir / "project.yaml").exists()
            assert (output_dir / "docs" / "CONTEXT.md").exists()
            assert (output_dir / "docs" / "DECISIONS.md").exists()

    def test_project_config_content(self):
        """测试项目配置内容"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            project = Project.create(
                name="MyTestProject",
                domain="web",
                output_dir=output_dir
            )
            project.generate_all()
            
            # 读取生成的配置
            with open(output_dir / "project.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            assert config["project"]["name"] == "MyTestProject"
            assert config["project"]["domain"] == "web"
