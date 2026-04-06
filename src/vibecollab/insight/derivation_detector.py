"""
Insight Derivation Detector - Automatic provenance detection from task transitions

This module provides automatic detection of insight derivation relationships
based on task transitions and event logs. When tasks transition through their
lifecycle (TODO → IN_PROGRESS → DONE), the system analyzes related insights
and can automatically suggest or set derived_from relationships.

Usage:
    detector = DerivationDetector(insight_manager, event_log)
    # On task completion, detect derivations
    derivations = detector.detect_from_task_completion(task_id)
    # Create new insight with auto-detected derived_from
    insight = detector.create_with_derivation(...)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

if TYPE_CHECKING:
    from ..domain.event_log import EventLog
    from ..insight.manager import InsightManager


@dataclass
class DerivationSuggestion:
    """A suggested derivation relationship."""

    insight_id: str
    reason: str
    confidence: float  # 0.0 to 1.0
    source_task: Optional[str] = None
    related_insights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "reason": self.reason,
            "confidence": self.confidence,
            "source_task": self.source_task,
            "related_insights": self.related_insights,
        }


class DerivationDetector:
    """Automatically detect insight derivation relationships.

    Analyzes task transitions and event logs to:
    1. Track which insights were used during a task
    2. Suggest derived_from relationships when creating new insights
    3. Build derivation chains based on task completion patterns

    Detection strategies:
    - Task-related insights: Insights linked to tasks that were completed
      before creating a new insight
    - Event log analysis: Look for insight_used events during task execution
    - Temporal proximity: Insights used recently before new insight creation
    """

    def __init__(self, insight_manager: "InsightManager", event_log: Optional["EventLog"] = None):
        self.insight_manager = insight_manager
        self.event_log = event_log

    def detect_from_task_completion(
        self,
        task_id: str,
        min_confidence: float = 0.5,
    ) -> List[DerivationSuggestion]:
        """Detect potential derivation sources after task completion.

        Analyzes:
        1. Insights directly linked to the task
        2. Insights used during task execution (from event log)
        3. Insights created during task execution

        Args:
            task_id: The completed task ID
            min_confidence: Minimum confidence threshold for suggestions

        Returns:
            List of DerivationSuggestion sorted by confidence
        """
        suggestions: Dict[str, DerivationSuggestion] = {}

        # Collect insights from various sources
        related = self._get_task_related_insights(task_id)
        used = self._get_insights_used_during_task(task_id)
        created = self._get_insights_created_during_task(task_id)

        # Build suggestions from related insights
        for ins_id in related:
            if ins_id in suggestions:
                suggestions[ins_id].confidence = min(1.0, suggestions[ins_id].confidence + 0.3)
            else:
                suggestions[ins_id] = DerivationSuggestion(
                    insight_id=ins_id,
                    reason="Insight linked to completed task",
                    confidence=0.6,
                    source_task=task_id,
                )

        # Add used insights with higher confidence
        for ins_id in used:
            if ins_id in suggestions:
                suggestions[ins_id].confidence = min(1.0, suggestions[ins_id].confidence + 0.2)
                suggestions[ins_id].reason += ", actively used during task"
            else:
                suggestions[ins_id] = DerivationSuggestion(
                    insight_id=ins_id,
                    reason="Insight actively used during task execution",
                    confidence=0.7,
                    source_task=task_id,
                )

        # Filter out insights created during this task (can't be derived from them)
        for ins_id in created:
            suggestions.pop(ins_id, None)

        # Filter by confidence and sort
        result = [s for s in suggestions.values() if s.confidence >= min_confidence]
        result.sort(key=lambda x: x.confidence, reverse=True)
        return result

    def suggest_for_new_insight(
        self,
        title: str,
        tags: List[str],
        recent_tasks: Optional[List[str]] = None,
        lookback_days: int = 7,
    ) -> List[DerivationSuggestion]:
        """Suggest derivation sources for a new insight.

        Combines multiple strategies:
        1. Recently completed tasks and their insights
        2. Tag similarity with existing insights
        3. Recently used insights from event log

        Args:
            title: New insight title (for semantic matching)
            tags: New insight tags
            recent_tasks: Optional list of recently worked task IDs
            lookback_days: How far back to look in event log

        Returns:
            List of DerivationSuggestion sorted by confidence
        """
        suggestions: Dict[str, DerivationSuggestion] = {}

        # Get insights from recent tasks
        if recent_tasks:
            for task_id in recent_tasks:
                task_suggestions = self.detect_from_task_completion(task_id)
                for s in task_suggestions:
                    if s.insight_id in suggestions:
                        suggestions[s.insight_id].confidence = min(
                            1.0, max(suggestions[s.insight_id].confidence, s.confidence) + 0.1
                        )
                    else:
                        suggestions[s.insight_id] = s

        # Get recently used insights from event log
        recent_used = self._get_recently_used_insights(lookback_days)
        for ins_id in recent_used:
            if ins_id in suggestions:
                suggestions[ins_id].confidence = min(1.0, suggestions[ins_id].confidence + 0.1)
            else:
                suggestions[ins_id] = DerivationSuggestion(
                    insight_id=ins_id,
                    reason="Recently used insight",
                    confidence=0.4,
                )

        # Tag-based similarity boost
        tag_matches = self._find_tag_matching_insights(tags)
        for ins_id, match_score in tag_matches:
            if ins_id in suggestions:
                suggestions[ins_id].confidence = min(
                    1.0, suggestions[ins_id].confidence + match_score * 0.2
                )
            elif match_score >= 0.5:
                suggestions[ins_id] = DerivationSuggestion(
                    insight_id=ins_id,
                    reason=f"Tag similarity ({match_score:.0%} overlap)",
                    confidence=match_score * 0.5,
                )

        # Filter and sort
        result = [s for s in suggestions.values() if s.confidence >= 0.3]
        result.sort(key=lambda x: x.confidence, reverse=True)
        return result[:10]  # Return top 10

    def create_insight_with_derivation(
        self,
        title: str,
        tags: List[str],
        category: str,
        body: Dict[str, Any],
        created_by: str,
        source_task: Optional[str] = None,
        auto_derivation: bool = True,
        min_confidence: float = 0.6,
        **kwargs,
    ) -> tuple:
        """Create a new insight with automatic derivation detection.

        Args:
            title: Insight title
            tags: Insight tags
            category: Insight category
            body: Insight body
            created_by: Creator identifier
            source_task: Optional task ID that spawned this insight
            auto_derivation: Whether to auto-detect derived_from
            min_confidence: Minimum confidence for auto-derivation
            **kwargs: Additional fields for insight creation

        Returns:
            Tuple of (Insight, List[DerivationSuggestion]) - the created insight
            and the suggestions used (if any)
        """
        derived_from: List[str] = []
        suggestions: List[DerivationSuggestion] = []

        # Handle manual derived_from from kwargs
        manual_derived = kwargs.pop("derived_from", None)
        if manual_derived:
            derived_from = list(manual_derived)

        if auto_derivation:
            # Get recent tasks to consider
            recent_tasks = [source_task] if source_task else []
            if not recent_tasks and self.event_log:
                # Get recently completed tasks
                recent_tasks = self._get_recent_completed_tasks(days=7)

            suggestions = self.suggest_for_new_insight(title, tags, recent_tasks=recent_tasks)

            # Use high-confidence suggestions (avoiding duplicates)
            for s in suggestions:
                if s.confidence >= min_confidence and s.insight_id not in derived_from:
                    derived_from.append(s.insight_id)

        # Prepare source info
        source_type = kwargs.pop("source_type", None)
        source_desc = kwargs.pop("source_desc", None)
        if derived_from and not source_type:
            source_type = "insight"
        if derived_from and not source_desc:
            source_desc = f"Derived from {','.join(derived_from)}"

        # Create the insight
        insight = self.insight_manager.create(
            title=title,
            tags=tags,
            category=category,
            body=body,
            created_by=created_by,
            derived_from=derived_from if derived_from else None,
            source_type=source_type,
            source_desc=source_desc,
            **kwargs,
        )

        return insight, suggestions

    def _get_task_related_insights(self, task_id: str) -> Set[str]:
        """Get insights linked to a task from task metadata."""
        # This would need to access task metadata from TaskManager
        # For now, we rely on event log analysis
        return set()

    def _get_insights_used_during_task(self, task_id: str, window_hours: int = 48) -> Set[str]:
        """Get insights used during task execution from event log."""
        if not self.event_log:
            return set()

        from ..domain.event_log import EventType

        events = self.event_log.read_all()

        # Find task start event (transition to IN_PROGRESS)
        task_start = None
        task_end = None
        for event in events:
            if event.payload.get("task_id") == task_id:
                if event.payload.get("new_status") == "IN_PROGRESS":
                    task_start = event.timestamp
                elif event.payload.get("new_status") in ("DONE", "REVIEW"):
                    task_end = event.timestamp

        if not task_start:
            return set()

        # Find insight_used events between task start and end
        used = set()
        for event in events:
            if (
                event.event_type == EventType.CUSTOM
                and event.payload.get("action") == "insight_used"
            ):
                ins_id = event.payload.get("insight_id")
                if ins_id and task_start <= event.timestamp <= (
                    task_end or datetime.now(timezone.utc).isoformat()
                ):
                    used.add(ins_id)

        return used

    def _get_insights_created_during_task(self, task_id: str, window_hours: int = 48) -> Set[str]:
        """Get insights created during task execution."""
        if not self.event_log:
            return set()

        from ..domain.event_log import EventType

        events = self.event_log.read_all()

        # Find task start/end
        task_start = None
        task_end = None
        for event in events:
            if event.payload.get("task_id") == task_id:
                if event.payload.get("new_status") == "IN_PROGRESS":
                    task_start = event.timestamp
                elif event.payload.get("new_status") == "DONE":
                    task_end = event.timestamp

        if not task_start:
            return set()

        # Find insight_created events during task
        created = set()
        for event in events:
            if (
                event.event_type == EventType.CUSTOM
                and event.payload.get("action") == "insight_created"
            ):
                ins_id = event.payload.get("insight_id")
                if ins_id and task_start <= event.timestamp <= (
                    task_end or datetime.now(timezone.utc).isoformat()
                ):
                    created.add(ins_id)

        return created

    def _get_recently_used_insights(self, days: int = 7) -> Set[str]:
        """Get insights used in the last N days from event log."""
        if not self.event_log:
            return set()

        from datetime import timedelta

        from ..domain.event_log import EventType

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        events = self.event_log.read_all()
        used = set()

        for event in events:
            if (
                event.event_type == EventType.CUSTOM
                and event.payload.get("action") == "insight_used"
                and event.timestamp >= cutoff_iso
            ):
                ins_id = event.payload.get("insight_id")
                if ins_id:
                    used.add(ins_id)

        return used

    def _get_recent_completed_tasks(self, days: int = 7) -> List[str]:
        """Get list of recently completed task IDs."""
        if not self.event_log:
            return []

        from datetime import timedelta

        from ..domain.event_log import EventType

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        events = self.event_log.read_all()
        completed = []

        for event in events:
            if event.event_type == EventType.TASK_COMPLETED or (
                event.payload.get("new_status") == "DONE" and event.payload.get("task_id")
            ):
                if event.timestamp >= cutoff_iso:
                    task_id = event.payload.get("task_id")
                    if task_id and task_id not in completed:
                        completed.append(task_id)

        return completed[:10]  # Return most recent 10

    def _find_tag_matching_insights(self, tags: List[str], top_k: int = 10) -> List[tuple]:
        """Find insights with matching tags and return (insight_id, score) tuples."""
        if not tags:
            return []

        query_tags = set(t.lower() for t in tags)
        matches = []

        for ins in self.insight_manager.list_all():
            ins_tags = set(t.lower() for t in ins.tags)
            overlap = query_tags & ins_tags
            if overlap:
                score = len(overlap) / max(len(query_tags), len(ins_tags))
                matches.append((ins.id, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]

    def record_task_insight_link(
        self, task_id: str, insight_id: str, link_type: str = "related"
    ) -> None:
        """Record a link between a task and an insight in the event log.

        This creates an auditable record of task-insight associations
        for future derivation detection.

        Args:
            task_id: The task ID
            insight_id: The insight ID
            link_type: Type of link (related, derived, used, etc.)
        """
        if not self.event_log:
            return

        from ..domain.event_log import Event, EventType

        self.event_log.append(
            Event(
                event_type=EventType.CUSTOM,
                actor="system",
                summary=f"Task {task_id} linked to insight {insight_id}",
                payload={
                    "action": "task_insight_linked",
                    "task_id": task_id,
                    "insight_id": insight_id,
                    "link_type": link_type,
                },
            )
        )
