"""
Profile Manager - 开发者画像和 Insight 集合管理器

管理 Profile 和 Collection 的加载、匹配、推荐。
设计原则：
- 简单的 CRUD 操作
- 基于标签和技能的匹配
- 智能推荐系统
- 避免过度设计（遵循 INS-011）
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .profile import DeveloperProfile, PRESET_PROFILES
from .insight_collection import InsightCollection, PRESET_COLLECTIONS


class ProfileManager:
    """Profile 和 Collection 管理器

    负责：
    - 加载和管理 Profile
    - 加载和管理 Collection
    - Profile 匹配和推荐
    - Collection 匹配和推荐
    """

    def __init__(self, project_root: Optional[Path] = None):
        """初始化管理器

        Args:
            project_root: 项目根目录，用于查找自定义 Profile
        """
        self.project_root = project_root or Path.cwd()

        # 加载预设 Profile 和 Collection
        self.profiles: Dict[str, DeveloperProfile] = PRESET_PROFILES.copy()
        self.collections: Dict[str, InsightCollection] = PRESET_COLLECTIONS.copy()

        # 加载自定义 Profile
        self._load_custom_profiles()

        # 加载自定义 Collection
        self._load_custom_collections()

    def _load_custom_profiles(self):
        """加载自定义 Profile"""
        profiles_dir = self.project_root / ".vibecollab" / "profiles"

        if not profiles_dir.exists():
            return

        for profile_file in profiles_dir.glob("*.yaml"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if data and 'id' in data:
                    profile = DeveloperProfile.from_dict(data)
                    self.profiles[profile.id] = profile

            except Exception as e:
                print(f"⚠️  加载 Profile 失败 {profile_file}: {e}")

    def _load_custom_collections(self):
        """加载自定义 Collection"""
        collections_dir = self.project_root / ".vibecollab" / "collections"

        if not collections_dir.exists():
            return

        for collection_file in collections_dir.glob("*.yaml"):
            try:
                with open(collection_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if data and 'id' in data:
                    collection = InsightCollection.from_dict(data)
                    self.collections[collection.id] = collection

            except Exception as e:
                print(f"⚠️  加载 Collection 失败 {collection_file}: {e}")

    # ------------------------------------------------------------------
    # Profile 管理
    # ------------------------------------------------------------------

    def get_profile(self, profile_id: str) -> Optional[DeveloperProfile]:
        """获取 Profile

        Args:
            profile_id: Profile ID

        Returns:
            Profile 实例，不存在则返回 None
        """
        return self.profiles.get(profile_id)

    def list_profiles(self) -> List[DeveloperProfile]:
        """列出所有 Profile

        Returns:
            Profile 列表
        """
        return list(self.profiles.values())

    def search_profiles(
        self,
        skill: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 10
    ) -> List[DeveloperProfile]:
        """搜索 Profile

        Args:
            skill: 技能关键词
            tag: 标签
            limit: 返回数量限制

        Returns:
            匹配的 Profile 列表
        """
        results = []

        for profile in self.profiles.values():
            # 技能匹配
            if skill and not profile.match_skill(skill):
                continue

            # 标签匹配
            if tag and not profile.match_tag(tag):
                continue

            results.append(profile)

            if len(results) >= limit:
                break

        return results

    def recommend_profiles(
        self,
        skills: List[str],
        tags: List[str],
        limit: int = 5
    ) -> List[DeveloperProfile]:
        """推荐 Profile

        根据技能和标签推荐最适合的 Profile。

        Args:
            skills: 技能列表
            tags: 标签列表
            limit: 返回数量限制

        Returns:
            推荐的 Profile 列表（按匹配度排序）
        """
        scored = []

        for profile in self.profiles.values():
            score = 0

            # 技能匹配分数
            for skill in skills:
                if profile.match_skill(skill):
                    score += 2

            # 标签匹配分数
            for tag in tags:
                if profile.match_tag(tag):
                    score += 1

            if score > 0:
                scored.append((profile, score))

        # 按分数排序
        scored.sort(key=lambda x: x[1], reverse=True)

        return [p for p, _ in scored[:limit]]

    # ------------------------------------------------------------------
    # Collection 管理
    # ------------------------------------------------------------------

    def get_collection(self, collection_id: str) -> Optional[InsightCollection]:
        """获取 Collection

        Args:
            collection_id: Collection ID

        Returns:
            Collection 实例，不存在则返回 None
        """
        return self.collections.get(collection_id)

    def list_collections(self) -> List[InsightCollection]:
        """列出所有 Collection

        Returns:
            Collection 列表
        """
        return list(self.collections.values())

    def search_collections(
        self,
        domain: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[InsightCollection]:
        """搜索 Collection

        Args:
            domain: 领域
            category: 分类
            limit: 返回数量限制

        Returns:
            匹配的 Collection 列表
        """
        results = []

        for collection in self.collections.values():
            # 领域匹配
            if domain and not collection.matches_domain(domain):
                continue

            # 分类匹配
            if category and collection.category != category:
                continue

            results.append(collection)

            if len(results) >= limit:
                break

        return results

    def recommend_collections(
        self,
        profile_id: str,
        limit: int = 5
    ) -> List[InsightCollection]:
        """为 Profile 推荐 Collection

        Args:
            profile_id: Profile ID
            limit: 返回数量限制

        Returns:
            推荐的 Collection 列表
        """
        results = []

        for collection in self.collections.values():
            if collection.matches_profile(profile_id):
                results.append(collection)

                if len(results) >= limit:
                    break

        return results

    # ------------------------------------------------------------------
    # 组合推荐
    # ------------------------------------------------------------------

    def recommend_for_developer(
        self,
        skills: List[str],
        tags: List[str],
        limit: int = 3
    ) -> Dict[str, Any]:
        """为开发者推荐 Profile 和 Collection

        Args:
            skills: 开发者技能
            tags: 开发者标签
            limit: 推荐数量限制

        Returns:
            {
                "profiles": [Profile, ...],
                "collections": [Collection, ...],
            }
        """
        # 推荐 Profile
        profiles = self.recommend_profiles(skills, tags, limit)

        # 推荐 Collection
        collections = []

        for profile in profiles:
            profile_collections = self.recommend_collections(profile.id, limit)
            collections.extend(profile_collections)

            if len(collections) >= limit:
                break

        # 去重
        seen = set()
        unique_collections = []
        for collection in collections:
            if collection.id not in seen:
                seen.add(collection.id)
                unique_collections.append(collection)

        return {
            "profiles": profiles[:limit],
            "collections": unique_collections[:limit],
        }
