"""
Developer Profile - 开发者能力画像

定义开发者角色的技能、倾向、常用模式，支持打包和移植。
设计原则：
- Profile 定义能力和倾向，不包含运行时状态
- 可打包、可移植
- 与 Insight Collection 配合使用
- 避免过度设计（遵循 INS-011）
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DeveloperProfile:
    """开发者能力画像

    定义角色的技能、倾向、偏好 Insight，可打包和移植。
    不包含运行时状态（如 CONTEXT.md 内容），只包含静态配置。
    """

    # 基础信息
    id: str
    name: str
    description: str

    # 技能和专长
    skills: List[str] = field(default_factory=list)
    expertise: List[str] = field(default_factory=list)

    # 偏好的 Insight
    preferred_insights: List[str] = field(default_factory=list)

    # 标签（用于搜索和分类）
    tags: List[str] = field(default_factory=list)

    # 工作风格
    workflow_style: str = "iterative"  # iterative, tdd, agent_autonomous
    communication_style: str = "concise"  # concise, detailed, interactive

    # 优先级倾向
    priority_focus: List[str] = field(default_factory=list)  # quality, speed, simplicity

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
            "skills": self.skills,
            "expertise": self.expertise,
            "preferred_insights": self.preferred_insights,
            "tags": self.tags,
            "workflow_style": self.workflow_style,
            "communication_style": self.communication_style,
            "priority_focus": self.priority_focus,
            "version": self.version,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeveloperProfile":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            skills=data.get("skills", []),
            expertise=data.get("expertise", []),
            preferred_insights=data.get("preferred_insights", []),
            tags=data.get("tags", []),
            workflow_style=data.get("workflow_style", "iterative"),
            communication_style=data.get("communication_style", "concise"),
            priority_focus=data.get("priority_focus", []),
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            created_by=data.get("created_by", "unknown"),
            updated_at=data.get("updated_at"),
        )

    def match_skill(self, skill: str) -> bool:
        """检查是否匹配某个技能"""
        return skill in self.skills or skill in self.expertise

    def match_tag(self, tag: str) -> bool:
        """检查是否匹配某个标签"""
        return tag in self.tags

    def get_insight_recommendations(
        self,
        available_insights: List[str],
        limit: int = 5
    ) -> List[str]:
        """获取推荐的 Insight

        Args:
            available_insights: 可用的 Insight ID 列表
            limit: 返回数量限制

        Returns:
            推荐的 Insight ID 列表
        """
        # 返回偏好且可用的 Insight
        recommended = [
            insight_id
            for insight_id in self.preferred_insights
            if insight_id in available_insights
        ]
        return recommended[:limit]


# 预设 Profile

FULLSTACK_DEV = DeveloperProfile(
    id="fullstack-dev",
    name="全栈开发者",
    description="能够处理前后端开发的通用开发者",
    skills=["frontend", "backend", "devops"],
    expertise=["react", "nodejs", "python", "docker"],
    preferred_insights=["INS-001", "INS-005", "INS-012"],
    tags=["web", "scalable", "fullstack"],
    workflow_style="iterative",
    communication_style="concise",
    priority_focus=["quality", "scalability"],
    version="1.0",
    created_by="vibecollab",
)

AI_SPECIALIST = DeveloperProfile(
    id="ai-specialist",
    name="AI 专家",
    description="专注于 LLM 集成和 AI 应用的开发者",
    skills=["llm_integration", "prompt_engineering", "ml"],
    expertise=["openai", "anthropic", "transformers"],
    preferred_insights=["INS-003", "INS-007", "INS-011"],
    tags=["ai", "ml", "llm"],
    workflow_style="agent_autonomous",
    communication_style="detailed",
    priority_focus=["quality", "innovation"],
    version="1.0",
    created_by="vibecollab",
)

BACKEND_DEV = DeveloperProfile(
    id="backend-dev",
    name="后端开发者",
    description="专注于后端系统架构和性能优化的开发者",
    skills=["backend", "database", "api"],
    expertise=["python", "postgresql", "redis", "microservices"],
    preferred_insights=["INS-002", "INS-004", "INS-006"],
    tags=["backend", "performance", "api"],
    workflow_style="tdd",
    communication_style="concise",
    priority_focus=["performance", "reliability"],
    version="1.0",
    created_by="vibecollab",
)


PRESET_PROFILES = {
    "fullstack-dev": FULLSTACK_DEV,
    "ai-specialist": AI_SPECIALIST,
    "backend-dev": BACKEND_DEV,
}
