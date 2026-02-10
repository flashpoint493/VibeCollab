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

    def test_chapter_numbering(self):
        """测试章节编号的正确性"""
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
            ],
            "documentation": {
                "key_files": []
            },
            "multi_developer": {
                "enabled": True,
                "identity": {
                    "primary": "git_username",
                    "fallback": "system_user",
                    "normalize": True
                }
            },
            "symbology": {
                "decision_status": [
                    {"symbol": "PENDING", "meaning": "待确认"}
                ]
            },
            "lifecycle": {
                "stages": {
                    "demo": {
                        "name": "原型验证",
                        "description": "快速验证核心概念",
                        "focus": ["快速迭代"],
                        "principles": ["快速试错"]
                    }
                }
            }
        }
        
        generator = LLMContextGenerator(config)
        content = generator.generate()
        
        # 验证主章节编号顺序正确
        expected_chapters = [
            "# 一、核心理念",
            "# 二、职能角色定义",
            "# 三、决策分级制度",
            "# 四、开发流程协议",
            "# 五、测试体系",
            "# 六、里程碑定义",
            "# 七、迭代管理",
            "# 八、阶段化协作规则",
            "# 九、上下文管理",
            "# 十、多开发者/Agent 协作协议",
            "# 十一、符号学标注系统",
            "# 十二、协议自检机制",
        ]
        
        for chapter in expected_chapters:
            assert chapter in content, f"章节 '{chapter}' 未找到"
        
        # 验证没有重复的章节编号
        import re
        chapter_pattern = r'^# (一|二|三|四|五|六|七|八|九|十|十一|十二|十三|十四)、'
        chapters_found = re.findall(chapter_pattern, content, re.MULTILINE)
        
        # 检查是否有重复
        from collections import Counter
        chapter_counts = Counter(chapters_found)
        duplicates = [ch for ch, count in chapter_counts.items() if count > 1]
        assert len(duplicates) == 0, f"发现重复的章节编号: {duplicates}"
        
        # 验证子章节编号（以多开发者章节为例）
        assert "## 10.1 协作模式概述" in content
        assert "## 10.2 目录结构" in content
        assert "## 10.3 开发者身份识别" in content
        assert "## 10.4 上下文管理" in content
        
        # 验证阶段化协作规则的子章节
        assert "## 8.1 项目生涯阶段说明" in content
        assert "## 8.2 阶段化协作指导" in content
        
        # 验证上下文管理的子章节
        assert "## 9.1 关键文件职责" in content
        assert "## 9.2 上下文恢复协议" in content
        assert "## 9.3 上下文保存协议" in content
        
        # 验证协议自检机制的子章节
        assert "## 12.1 协议自检的重要性" in content
        assert "## 12.2 自检触发方式" in content

