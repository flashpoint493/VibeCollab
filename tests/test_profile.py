"""
Profile 模块单元测试
"""

import pytest

from vibecollab.profile import (
    DeveloperProfile,
    FULLSTACK_DEV,
    AI_SPECIALIST,
    BACKEND_DEV,
    PRESET_PROFILES,
)


class TestDeveloperProfile:
    """测试 DeveloperProfile"""

    def test_create_profile(self):
        """测试创建 Profile"""
        profile = DeveloperProfile(
            id="test-profile",
            name="测试 Profile",
            description="用于单元测试"
        )

        assert profile.id == "test-profile"
        assert profile.name == "测试 Profile"
        assert profile.description == "用于单元测试"

    def test_to_dict(self):
        """测试转换为字典"""
        profile = DeveloperProfile(
            id="test",
            name="Test",
            description="Test profile"
        )

        data = profile.to_dict()

        assert data["id"] == "test"
        assert data["name"] == "Test"
        assert "skills" in data
        assert "expertise" in data

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test profile",
            "skills": ["python", "react"],
            "expertise": ["backend"],
        }

        profile = DeveloperProfile.from_dict(data)

        assert profile.id == "test"
        assert profile.name == "Test"
        assert profile.skills == ["python", "react"]
        assert profile.expertise == ["backend"]

    def test_match_skill(self):
        """测试技能匹配"""
        profile = DeveloperProfile(
            id="test",
            name="Test",
            description="Test",
            skills=["python", "react"],
            expertise=["backend"]
        )

        assert profile.match_skill("python") is True
        assert profile.match_skill("backend") is True
        assert profile.match_skill("java") is False

    def test_match_tag(self):
        """测试标签匹配"""
        profile = DeveloperProfile(
            id="test",
            name="Test",
            description="Test",
            tags=["web", "scalable"]
        )

        assert profile.match_tag("web") is True
        assert profile.match_tag("scalable") is True
        assert profile.match_tag("mobile") is False

    def test_get_insight_recommendations(self):
        """测试获取 Insight 推荐"""
        profile = DeveloperProfile(
            id="test",
            name="Test",
            description="Test",
            preferred_insights=["INS-001", "INS-002", "INS-003"]
        )

        available = ["INS-001", "INS-002", "INS-004"]
        recommended = profile.get_insight_recommendations(available, limit=2)

        assert recommended == ["INS-001", "INS-002"]

    def test_preset_profiles_exist(self):
        """测试预设 Profile 存在"""
        assert "fullstack-dev" in PRESET_PROFILES
        assert "ai-specialist" in PRESET_PROFILES
        assert "backend-dev" in PRESET_PROFILES

    def test_fullstack_dev_profile(self):
        """测试全栈开发者 Profile"""
        profile = FULLSTACK_DEV

        assert profile.id == "fullstack-dev"
        assert "react" in profile.expertise
        assert "nodejs" in profile.expertise
        assert profile.workflow_style == "iterative"

    def test_ai_specialist_profile(self):
        """测试 AI 专家 Profile"""
        profile = AI_SPECIALIST

        assert profile.id == "ai-specialist"
        assert "openai" in profile.expertise
        assert profile.workflow_style == "agent_autonomous"
        assert "innovation" in profile.priority_focus

    def test_backend_dev_profile(self):
        """测试后端开发者 Profile"""
        profile = BACKEND_DEV

        assert profile.id == "backend-dev"
        assert "python" in profile.expertise
        assert profile.workflow_style == "tdd"
        assert "performance" in profile.priority_focus


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
