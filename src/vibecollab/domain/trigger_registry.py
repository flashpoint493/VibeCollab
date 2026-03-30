"""
Insight Trigger Registry

Discover triggers from insight tags for easy invocation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class Trigger:
    """A trigger definition from insight tags"""

    word: str
    insight_ids: List[str] = field(default_factory=list)
    insight_titles: List[str] = field(default_factory=list)
    count: int = 0


class TriggerRegistry:
    """Registry for all insight triggers based on tags"""

    def __init__(self, insights_dir: Path):
        """
        Initialize trigger registry

        Args:
            insights_dir: Directory containing INS-XXX.yaml files
        """
        self.insights_dir = insights_dir
        self._triggers: Dict[str, Trigger] = {}
        self._cache_valid = False

    def invalidate_cache(self):
        """Invalidate triggers cache"""
        self._cache_valid = False
        self._triggers.clear()

    def _load_all_triggers(self):
        """Load all triggers from insight tags"""
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
                tags = data.get("tags", [])

                # Each tag becomes a trigger word
                for tag in tags:
                    tag_lower = tag.lower()
                    if tag_lower not in self._triggers:
                        self._triggers[tag_lower] = Trigger(
                            word=tag_lower,
                            insight_ids=[],
                            insight_titles=[],
                            count=0,
                        )

                    self._triggers[tag_lower].insight_ids.append(insight_id)
                    self._triggers[tag_lower].insight_titles.append(insight_title)
                    self._triggers[tag_lower].count += 1

            except Exception:
                continue

        self._cache_valid = True

    def get_all_triggers(self) -> List[Trigger]:
        """Get all triggers sorted by count (descending)"""
        self._load_all_triggers()
        return sorted(self._triggers.values(), key=lambda t: t.count, reverse=True)

    def get_trigger(self, word: str) -> Optional[Trigger]:
        """Get specific trigger by word"""
        self._load_all_triggers()
        return self._triggers.get(word.lower())

    def search_triggers(self, keyword: str) -> List[Trigger]:
        """Search triggers by keyword"""
        self._load_all_triggers()
        keyword_lower = keyword.lower()

        results = []
        for trigger in self._triggers.values():
            # Match trigger word
            if keyword_lower in trigger.word:
                results.append(trigger)
            # Match insight titles
            elif any(keyword_lower in title.lower() for title in trigger.insight_titles):
                results.append(trigger)

        return sorted(results, key=lambda t: t.count, reverse=True)

    def get_trigger_stats(self) -> Dict:
        """Get statistics about triggers"""
        self._load_all_triggers()

        total_insights = len(
            set(ins_id for trigger in self._triggers.values() for ins_id in trigger.insight_ids)
        )

        return {
            "total_triggers": len(self._triggers),
            "total_insights": total_insights,
            "most_common_trigger": (
                max(self._triggers.values(), key=lambda t: t.count).word if self._triggers else None
            ),
        }

    def format_triggers_table(self, limit: Optional[int] = None) -> str:
        """Format triggers as a readable table"""
        triggers = self.get_all_triggers()

        if not triggers:
            return "No triggers found."

        if limit:
            triggers = triggers[:limit]

        lines = [
            "",
            "=" * 70,
            "  Available Insight Triggers (Tags)",
            "=" * 70,
            "",
            "  Mention these words to find related insights:",
            "",
        ]

        for i, trigger in enumerate(triggers, 1):
            lines.append(f'  {i}. "{trigger.word}" → {trigger.count} insight(s)')
            # Show first 3 insight titles
            for title in trigger.insight_titles[:3]:
                short_title = title[:50] + "..." if len(title) > 50 else title
                lines.append(f"     • {short_title}")
            if len(trigger.insight_titles) > 3:
                lines.append(f"     ... and {len(trigger.insight_titles) - 3} more")
            lines.append("")

        lines.extend(
            [
                "-" * 70,
                "💡 Usage: Mention trigger word in your request",
                '   Example: "show me workflow insights" or "git best practices"',
                "",
            ]
        )

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Export all triggers as dictionary"""
        self._load_all_triggers()

        return {
            "triggers": [
                {
                    "word": t.word,
                    "insight_count": t.count,
                    "insight_ids": t.insight_ids,
                    "insight_titles": t.insight_titles,
                }
                for t in sorted(self._triggers.values(), key=lambda x: x.count, reverse=True)
            ]
        }

    def get_insights_by_tag(self, tag: str) -> List[Dict]:
        """Get all insights that have a specific tag"""
        self._load_all_triggers()

        trigger = self._triggers.get(tag.lower())
        if not trigger:
            return []

        return [
            {"id": ins_id, "title": title}
            for ins_id, title in zip(trigger.insight_ids, trigger.insight_titles)
        ]
