"""
Insight Collection - Insight 集合（知识包）

将相关的 Insight 打包为可移植的知识单元。
设计原则：
- Collection 是可移植的知识包
- 不包含项目特定状态
- 可以被 Profile 引用
- 支持领域扩展
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class InsightCollection:
    """Insight 集合（知识包）

    将一组相关的 Insight 打包为可移植的知识单元。
    可以被 Profile 引用，也可以直接作为学习材料。
    """

    # 基础信息
    id: str
    name: str
    description: str

    # 包含的 Insight
    insights: List[str] = field(default_factory=list)

    # 分类和领域
    category: str = "general"  # technique, workflow, domain_specific
    domain: Optional[str] = None  # web, ai, data, game 等

    # 适用场景
    applicable_to: List[str] = field(default_factory=list)  # profile ids, role codes

    # 学习路径（可选）
    learning_order: List[str] = field(default_factory=list)  # insight ids in order

    # 依赖关系
    dependencies: List[str] = field(default_factory=list)  # prerequisite collection ids

    # 元数据
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "unknown"
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "insights": self.insights,
            "category": self.category,
            "domain": self.domain,
            "applicable_to": self.applicable_to,
            "learning_order": self.learning_order,
            "dependencies": self.dependencies,
            "version": self.version,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InsightCollection":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            insights=data.get("insights", []),
            category=data.get("category", "general"),
            domain=data.get("domain"),
            applicable_to=data.get("applicable_to", []),
            learning_order=data.get("learning_order", []),
            dependencies=data.get("dependencies", []),
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            created_by=data.get("created_by", "unknown"),
            updated_at=data.get("updated_at"),
        )

    def matches_profile(self, profile_id: str) -> bool:
        """检查是否适用于某个 Profile"""
        return profile_id in self.applicable_to

    def matches_domain(self, domain: str) -> bool:
        """检查是否匹配某个领域"""
        return self.domain == domain or self.domain is None

    def get_learning_path(self) -> List[str]:
        """获取学习路径（insight ids）"""
        return self.learning_order if self.learning_order else self.insights


# 预设 Collection

WEB_DEV_ESSENTIALS = InsightCollection(
    id="web-dev-essentials",
    name="Web 开发基础",
    description="Web 项目必备 Insight 集合",
    category="domain_specific",
    domain="web",
    insights=["INS-001", "INS-002", "INS-005", "INS-012"],
    applicable_to=["fullstack-dev", "frontend-dev"],
    learning_order=["INS-001", "INS-002", "INS-005", "INS-012"],
    version="1.0",
    created_by="vibecollab",
)

AI_DEVELOPMENT = InsightCollection(
    id="ai-development",
    name="AI 开发基础",
    description="AI/LLM 应用开发必备 Insight",
    category="domain_specific",
    domain="ai",
    insights=["INS-003", "INS-007", "INS-011", "INS-012"],
    applicable_to=["ai-specialist"],
    learning_order=["INS-011", "INS-003", "INS-007", "INS-012"],
    version="1.0",
    created_by="vibecollab",
)

BACKEND_FOUNDATIONS = InsightCollection(
    id="backend-foundations",
    name="后端开发基础",
    description="后端系统架构和性能优化",
    category="domain_specific",
    domain="backend",
    insights=["INS-002", "INS-004", "INS-006"],
    applicable_to=["backend-dev", "fullstack-dev"],
    learning_order=["INS-002", "INS-004", "INS-006"],
    version="1.0",
    created_by="vibecollab",
)

VIBE_DEVELOPMENT_CORE = InsightCollection(
    id="vibe-dev-core",
    name="Vibe Development 核心",
    description="Vibe Development 哲学和协作协议",
    category="philosophy",
    insights=["INS-011", "INS-012"],
    applicable_to=[],  # 适用于所有
    learning_order=["INS-011", "INS-012"],
    version="1.0",
    created_by="vibecollab",
)


PRESET_COLLECTIONS = {
    "web-dev-essentials": WEB_DEV_ESSENTIALS,
    "ai-development": AI_DEVELOPMENT,
    "backend-foundations": BACKEND_FOUNDATIONS,
    "vibe-dev-core": VIBE_DEVELOPMENT_CORE,
}
