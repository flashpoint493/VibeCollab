"""
Insight Collection 模块单元测试
"""

import pytest

from vibecollab.insight_collection import (
    InsightCollection,
    WEB_DEV_ESSENTIALS,
    AI_DEVELOPMENT,
    BACKEND_FOUNDATIONS,
    VIBE_DEVELOPMENT_CORE,
    PRESET_COLLECTIONS,
)


class TestInsightCollection:
    """测试 InsightCollection"""

    def test_create_collection(self):
        """测试创建 Collection"""
        collection = InsightCollection(
            id="test-collection",
            name="测试集合",
            description="用于单元测试"
        )

        assert collection.id == "test-collection"
        assert collection.name == "测试集合"
        assert collection.description == "用于单元测试"

    def test_to_dict(self):
        """测试转换为字典"""
        collection = InsightCollection(
            id="test",
            name="Test",
            description="Test collection"
        )

        data = collection.to_dict()

        assert data["id"] == "test"
        assert data["name"] == "Test"
        assert "insights" in data
        assert "category" in data

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test collection",
            "insights": ["INS-001", "INS-002"],
            "category": "domain_specific",
            "domain": "web"
        }

        collection = InsightCollection.from_dict(data)

        assert collection.id == "test"
        assert collection.name == "Test"
        assert collection.insights == ["INS-001", "INS-002"]
        assert collection.category == "domain_specific"
        assert collection.domain == "web"

    def test_matches_profile(self):
        """测试 Profile 匹配"""
        collection = InsightCollection(
            id="test",
            name="Test",
            description="Test",
            applicable_to=["fullstack-dev", "backend-dev"]
        )

        assert collection.matches_profile("fullstack-dev") is True
        assert collection.matches_profile("backend-dev") is True
        assert collection.matches_profile("ai-specialist") is False

    def test_matches_domain(self):
        """测试领域匹配"""
        collection = InsightCollection(
            id="test",
            name="Test",
            description="Test",
            domain="web"
        )

        assert collection.matches_domain("web") is True
        assert collection.matches_domain("ai") is False

    def test_matches_domain_none(self):
        """测试领域为 None 时匹配所有"""
        collection = InsightCollection(
            id="test",
            name="Test",
            description="Test",
            domain=None
        )

        assert collection.matches_domain("web") is True
        assert collection.matches_domain("ai") is True

    def test_get_learning_path(self):
        """测试获取学习路径"""
        collection = InsightCollection(
            id="test",
            name="Test",
            description="Test",
            insights=["INS-001", "INS-002", "INS-003"],
            learning_order=["INS-003", "INS-001", "INS-002"]
        )

        path = collection.get_learning_path()
        assert path == ["INS-003", "INS-001", "INS-002"]

    def test_get_learning_path_default(self):
        """测试默认学习路径（按 insights 顺序）"""
        collection = InsightCollection(
            id="test",
            name="Test",
            description="Test",
            insights=["INS-001", "INS-002", "INS-003"]
        )

        path = collection.get_learning_path()
        assert path == ["INS-001", "INS-002", "INS-003"]

    def test_preset_collections_exist(self):
        """测试预设 Collection 存在"""
        assert "web-dev-essentials" in PRESET_COLLECTIONS
        assert "ai-development" in PRESET_COLLECTIONS
        assert "backend-foundations" in PRESET_COLLECTIONS
        assert "vibe-dev-core" in PRESET_COLLECTIONS

    def test_web_dev_essentials(self):
        """测试 Web 开发基础集合"""
        collection = WEB_DEV_ESSENTIALS

        assert collection.id == "web-dev-essentials"
        assert collection.domain == "web"
        assert collection.category == "domain_specific"
        assert "INS-001" in collection.insights
        assert "fullstack-dev" in collection.applicable_to

    def test_ai_development(self):
        """测试 AI 开发集合"""
        collection = AI_DEVELOPMENT

        assert collection.id == "ai-development"
        assert collection.domain == "ai"
        assert "INS-003" in collection.insights
        assert "INS-011" in collection.learning_order

    def test_backend_foundations(self):
        """测试后端基础集合"""
        collection = BACKEND_FOUNDATIONS

        assert collection.id == "backend-foundations"
        assert collection.domain == "backend"
        assert "INS-002" in collection.insights
        assert "backend-dev" in collection.applicable_to

    def test_vibe_development_core(self):
        """测试 Vibe Development 核心集合"""
        collection = VIBE_DEVELOPMENT_CORE

        assert collection.id == "vibe-dev-core"
        assert collection.category == "philosophy"
        assert collection.domain is None
        assert len(collection.applicable_to) == 0  # 适用于所有


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
