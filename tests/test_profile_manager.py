"""
Profile Manager 模块单元测试
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from vibecollab.profile_manager import ProfileManager
from vibecollab.profile import DeveloperProfile
from vibecollab.insight_collection import InsightCollection


class TestProfileManager:
    """测试 ProfileManager"""

    def test_init_manager(self):
        """测试初始化管理器"""
        manager = ProfileManager()

        assert manager.profiles is not None
        assert manager.collections is not None
        assert len(manager.profiles) > 0  # 应该有预设 Profile

    def test_get_profile(self):
        """测试获取 Profile"""
        manager = ProfileManager()

        profile = manager.get_profile("fullstack-dev")

        assert profile is not None
        assert profile.id == "fullstack-dev"

    def test_get_profile_not_found(self):
        """测试获取不存在的 Profile"""
        manager = ProfileManager()

        profile = manager.get_profile("nonexistent")

        assert profile is None

    def test_list_profiles(self):
        """测试列出所有 Profile"""
        manager = ProfileManager()

        profiles = manager.list_profiles()

        assert len(profiles) > 0
        assert all(isinstance(p, DeveloperProfile) for p in profiles)

    def test_search_profiles_by_skill(self):
        """测试按技能搜索 Profile"""
        manager = ProfileManager()

        profiles = manager.search_profiles(skill="python")

        assert len(profiles) > 0
        assert any(p.match_skill("python") for p in profiles)

    def test_search_profiles_by_tag(self):
        """测试按标签搜索 Profile"""
        manager = ProfileManager()

        profiles = manager.search_profiles(tag="ai")

        assert len(profiles) > 0
        assert any(p.match_tag("ai") for p in profiles)

    def test_recommend_profiles(self):
        """测试推荐 Profile"""
        manager = ProfileManager()

        profiles = manager.recommend_profiles(
            skills=["python", "react"],
            tags=["web"],
            limit=2
        )

        assert len(profiles) <= 2
        assert len(profiles) > 0

    def test_get_collection(self):
        """测试获取 Collection"""
        manager = ProfileManager()

        collection = manager.get_collection("web-dev-essentials")

        assert collection is not None
        assert collection.id == "web-dev-essentials"

    def test_get_collection_not_found(self):
        """测试获取不存在的 Collection"""
        manager = ProfileManager()

        collection = manager.get_collection("nonexistent")

        assert collection is None

    def test_list_collections(self):
        """测试列出所有 Collection"""
        manager = ProfileManager()

        collections = manager.list_collections()

        assert len(collections) > 0
        assert all(isinstance(c, InsightCollection) for c in collections)

    def test_search_collections_by_domain(self):
        """测试按领域搜索 Collection"""
        manager = ProfileManager()

        collections = manager.search_collections(domain="web")

        assert len(collections) > 0
        assert any(c.matches_domain("web") for c in collections)

    def test_search_collections_by_category(self):
        """测试按分类搜索 Collection"""
        manager = ProfileManager()

        collections = manager.search_collections(category="philosophy")

        assert len(collections) > 0
        assert any(c.category == "philosophy" for c in collections)

    def test_recommend_collections_for_profile(self):
        """测试为 Profile 推荐 Collection"""
        manager = ProfileManager()

        collections = manager.recommend_collections("fullstack-dev", limit=2)

        assert len(collections) <= 2
        assert all(c.matches_profile("fullstack-dev") for c in collections)

    def test_recommend_for_developer(self):
        """测试为开发者推荐 Profile 和 Collection"""
        manager = ProfileManager()

        result = manager.recommend_for_developer(
            skills=["python", "react"],
            tags=["web"],
            limit=2
        )

        assert "profiles" in result
        assert "collections" in result
        assert len(result["profiles"]) <= 2
        assert len(result["collections"]) <= 2

    def test_custom_profile_loading(self):
        """测试加载自定义 Profile"""
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # 创建 .vibecollab/profiles 目录
            profiles_dir = temp_dir / ".vibecollab" / "profiles"
            profiles_dir.mkdir(parents=True)

            # 创建自定义 Profile
            custom_profile = profiles_dir / "custom.yaml"
            custom_profile.write_text("""
id: custom-dev
name: 自定义开发者
description: 测试自定义 Profile
skills:
  - rust
  - wasm
expertise:
  - performance
  - systems
tags:
  - low-level
workflow_style: iterative
""")

            # 初始化管理器
            manager = ProfileManager(project_root=temp_dir)

            # 验证自定义 Profile 已加载
            profile = manager.get_profile("custom-dev")
            assert profile is not None
            assert profile.name == "自定义开发者"
            assert "rust" in profile.skills

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)

    def test_custom_collection_loading(self):
        """测试加载自定义 Collection"""
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # 创建 .vibecollab/collections 目录
            collections_dir = temp_dir / ".vibecollab" / "collections"
            collections_dir.mkdir(parents=True)

            # 创建自定义 Collection
            custom_collection = collections_dir / "custom.yaml"
            custom_collection.write_text("""
id: custom-collection
name: 自定义集合
description: 测试自定义 Collection
category: domain_specific
domain: rust
insights:
  - INS-001
  - INS-002
applicable_to:
  - custom-dev
""")

            # 初始化管理器
            manager = ProfileManager(project_root=temp_dir)

            # 验证自定义 Collection 已加载
            collection = manager.get_collection("custom-collection")
            assert collection is not None
            assert collection.name == "自定义集合"
            assert collection.domain == "rust"

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
