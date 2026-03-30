"""
Insight Trigger Registry

Discover and manage triggers from all insights for easy invocation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class Trigger:
    """A trigger definition from an insight"""

    word: str
    insight_id: str
    insight_title: str
    skill_name: str
    skill_description: str
    role: str
    priority: int = 5


class TriggerRegistry:
    """Registry for all insight triggers"""

    def __init__(self, insights_dir: Path):
        """
        Initialize trigger registry

        Args:
            insights_dir: Directory containing INS-XXX.yaml files
        """
        self.insights_dir = insights_dir
        self._triggers: List[Trigger] = []
        self._cache_valid = False

    def invalidate_cache(self):
        """Invalidate triggers cache"""
        self._cache_valid = False
        self._triggers.clear()

    def _load_all_triggers(self):
        """Load all triggers from insight files"""
        if self._cache_valid:
            return

        self._triggers.clear()

        if not self.insights_dir.exists():
            return

        for insight_file in self.insights_dir.glob("INS-*.yaml"):
            try:
                with open(insight_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data:
                    continue

                insight_id = data.get("id", insight_file.stem)
                insight_title = data.get("title", "Untitled")

                # Load triggers from role_skills
                role_skills = data.get("role_skills", {})
                for role, skills in role_skills.items():
                    if not isinstance(skills, list):
                        continue

                    for skill in skills:
                        trigger_word = skill.get("trigger", "")
                        if not trigger_word:
                            continue

                        trigger = Trigger(
                            word=trigger_word.lower(),
                            insight_id=insight_id,
                            insight_title=insight_title,
                            skill_name=skill.get("name", "Unnamed"),
                            skill_description=skill.get("description", ""),
                            role=role,
                            priority=skill.get("priority", 5),
                        )
                        self._triggers.append(trigger)

            except Exception:
                continue

        # Sort by priority (descending)
        self._triggers.sort(key=lambda t: t.priority, reverse=True)
        self._cache_valid = True

    def get_all_triggers(self) -> List[Trigger]:
        """Get all triggers"""
        self._load_all_triggers()
        return self._triggers.copy()

    def get_triggers_by_role(self, role: str) -> List[Trigger]:
        """Get triggers for a specific role"""
        self._load_all_triggers()
        return [t for t in self._triggers if t.role == role]

    def search_triggers(self, keyword: str) -> List[Trigger]:
        """Search triggers by keyword"""
        self._load_all_triggers()
        keyword_lower = keyword.lower()

        return [
            t
            for t in self._triggers
            if keyword_lower in t.word
            or keyword_lower in t.skill_name.lower()
            or keyword_lower in t.skill_description.lower()
            or keyword_lower in t.insight_title.lower()
        ]

    def get_trigger_stats(self) -> Dict:
        """Get statistics about triggers"""
        self._load_all_triggers()

        stats = {
            "total_triggers": len(self._triggers),
            "triggers_by_role": {},
            "unique_trigger_words": len(set(t.word for t in self._triggers)),
        }

        for trigger in self._triggers:
            role = trigger.role
            if role not in stats["triggers_by_role"]:
                stats["triggers_by_role"][role] = 0
            stats["triggers_by_role"][role] += 1

        return stats

    def find_trigger(self, trigger_word: str) -> Optional[Trigger]:
        """Find exact trigger by word"""
        self._load_all_triggers()
        word_lower = trigger_word.lower()

        for trigger in self._triggers:
            if trigger.word == word_lower:
                return trigger

        return None

    def format_triggers_table(self, role: Optional[str] = None) -> str:
        """Format triggers as a readable table"""
        if role:
            triggers = self.get_triggers_by_role(role)
            title = f"Triggers for {role} role"
        else:
            triggers = self.get_all_triggers()
            title = "All Available Triggers"

        if not triggers:
            return f"No triggers found{f' for role {role}' if role else ''}."

        lines = [f"\n{'=' * 60}", f"  {title}", f"{'=' * 60}\n"]

        # Group by role
        if not role:
            triggers_by_role: Dict[str, List[Trigger]] = {}
            for t in triggers:
                if t.role not in triggers_by_role:
                    triggers_by_role[t.role] = []
                triggers_by_role[t.role].append(t)

            for role_code, role_triggers in sorted(triggers_by_role.items()):
                lines.append(f"\n[{role_code}] {role_code} triggers:")
                lines.append("-" * 40)
                for t in role_triggers:
                    lines.append(f'  • "{t.word}" → {t.skill_name}')
                    if t.skill_description:
                        desc = t.skill_description[:50]
                        if len(t.skill_description) > 50:
                            desc += "..."
                        lines.append(f"    {desc}")
                    lines.append(f"    ({t.insight_id})")
                    lines.append("")
        else:
            for t in triggers:
                lines.append(f'  • "{t.word}" → {t.skill_name}')
                if t.skill_description:
                    desc = t.skill_description[:50]
                    if len(t.skill_description) > 50:
                        desc += "..."
                    lines.append(f"    {desc}")
                lines.append(f"    ({t.insight_id})")
                lines.append("")

        lines.append("\n💡 Usage: Mention trigger word in your request")
        lines.append("   Example: 'help me complete task' will activate Task-Insight Iteration")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Export all triggers as dictionary"""
        self._load_all_triggers()

        return {
            "triggers": [
                {
                    "word": t.word,
                    "insight_id": t.insight_id,
                    "insight_title": t.insight_title,
                    "skill_name": t.skill_name,
                    "skill_description": t.skill_description,
                    "role": t.role,
                    "priority": t.priority,
                }
                for t in self._triggers
            ]
        }
