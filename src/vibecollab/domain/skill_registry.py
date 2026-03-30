"""
Skill Registry Module

Dynamic skill registration and management from Insights.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class Skill:
    """A skill definition"""

    id: str
    name: str
    description: str = ""
    priority: int = 5
    trigger: str = ""
    source_insight: str = ""

    def to_prompt_text(self) -> str:
        """Convert skill to prompt-friendly text"""
        text = f"Skill: {self.name}"
        if self.description:
            text += f" - {self.description}"
        if self.trigger:
            text += f" (trigger: {self.trigger})"
        return text


class SkillRegistry:
    """Registry for role-based skills loaded from Insights"""

    def __init__(self, insights_dir: Path):
        """
        Initialize skill registry

        Args:
            insights_dir: Directory containing INS-XXX.yaml files
        """
        self.insights_dir = insights_dir
        self._skills_cache: Dict[str, List[Skill]] = {}
        self._cache_valid = False

    def invalidate_cache(self):
        """Invalidate skills cache (call when insights change)"""
        self._cache_valid = False
        self._skills_cache.clear()

    def get_skills_for_role(self, role_code: str) -> List[Skill]:
        """
        Get all skills for a role

        Args:
            role_code: Role code (DEV, ARCH, etc.)

        Returns:
            List of skills sorted by priority (highest first)
        """
        # Check cache
        if self._cache_valid and role_code in self._skills_cache:
            return self._skills_cache[role_code]

        skills = []

        # Scan all insight files
        if self.insights_dir.exists():
            for insight_file in self.insights_dir.glob("INS-*.yaml"):
                try:
                    import yaml

                    with open(insight_file, "r", encoding="utf-8") as f:
                        insight_data = yaml.safe_load(f)

                    insight_id = insight_data.get("id", insight_file.stem)

                    # Check for role_skills section
                    role_skills = insight_data.get("role_skills", {})
                    if role_code in role_skills:
                        for skill_data in role_skills[role_code]:
                            skill = Skill(
                                id=skill_data.get("id", f"{insight_id}_{len(skills)}"),
                                name=skill_data.get("name", "Unnamed Skill"),
                                description=skill_data.get("description", ""),
                                priority=skill_data.get("priority", 5),
                                trigger=skill_data.get("trigger", ""),
                                source_insight=insight_id,
                            )
                            skills.append(skill)

                except Exception:
                    # Skip files that can't be parsed
                    continue

        # Sort by priority (descending)
        skills.sort(key=lambda s: s.priority, reverse=True)

        # Cache result
        self._skills_cache[role_code] = skills
        self._cache_valid = True

        return skills

    def get_all_skills(self) -> Dict[str, List[Skill]]:
        """
        Get all skills organized by role

        Returns:
            Dictionary mapping role_code to list of skills
        """
        all_skills = {}

        # Common roles to check
        common_roles = ["DEV", "ARCH", "QA", "TEST", "PM", "DESIGN"]

        for role in common_roles:
            skills = self.get_skills_for_role(role)
            if skills:
                all_skills[role] = skills

        return all_skills

    def find_skills_by_trigger(self, role_code: str, trigger_word: str) -> List[Skill]:
        """
        Find skills matching a trigger word

        Args:
            role_code: Role to search
            trigger_word: Trigger word to match

        Returns:
            List of matching skills
        """
        skills = self.get_skills_for_role(role_code)
        trigger_lower = trigger_word.lower()

        return [
            skill
            for skill in skills
            if trigger_lower in skill.trigger.lower()
            or trigger_lower in skill.name.lower()
            or trigger_lower in skill.description.lower()
        ]

    def format_skills_for_prompt(self, role_code: str, max_skills: int = 10) -> str:
        """
        Format skills as prompt text

        Args:
            role_code: Role code
            max_skills: Maximum number of skills to include

        Returns:
            Formatted prompt text
        """
        skills = self.get_skills_for_role(role_code)

        if not skills:
            return ""

        # Take top N skills by priority
        top_skills = skills[:max_skills]

        lines = [f"Available skills for {role_code} role:"]
        for i, skill in enumerate(top_skills, 1):
            lines.append(f"{i}. {skill.to_prompt_text()}")

        if len(skills) > max_skills:
            lines.append(f"... and {len(skills) - max_skills} more skills")

        return "\n".join(lines)
