"""
Tests for insight derivation chain functionality (FP-015)
"""

import pytest
from datetime import datetime, timezone

from vibecollab.domain.event_log import Event, EventLog, EventType
from vibecollab.insight.derivation_detector import DerivationDetector, DerivationSuggestion
from vibecollab.insight.manager import InsightManager


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def project_dir(tmp_path):
    (tmp_path / ".vibecollab" / "insights").mkdir(parents=True)
    (tmp_path / "docs" / "roles").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def insight_mgr(project_dir):
    return InsightManager(project_dir)


@pytest.fixture
def event_log(project_dir):
    return EventLog(project_dir)


@pytest.fixture
def detector(insight_mgr, event_log):
    return DerivationDetector(insight_mgr, event_log)


def _body(**kwargs):
    base = {"scenario": "test scenario", "approach": "test approach"}
    base.update(kwargs)
    return base


# -----------------------------------------------------------------------------
# Tests: DerivationSuggestion
# -----------------------------------------------------------------------------


class TestDerivationSuggestion:
    def test_to_dict(self):
        s = DerivationSuggestion(
            insight_id="INS-001",
            reason="Test reason",
            confidence=0.8,
            source_task="TASK-DEV-001",
            related_insights=["INS-002", "INS-003"],
        )
        d = s.to_dict()
        assert d["insight_id"] == "INS-001"
        assert d["confidence"] == 0.8
        assert d["source_task"] == "TASK-DEV-001"


# -----------------------------------------------------------------------------
# Tests: DerivationDetector - Basic
# -----------------------------------------------------------------------------


class TestDerivationDetectorBasic:
    def test_init(self, insight_mgr, event_log):
        detector = DerivationDetector(insight_mgr, event_log)
        assert detector.insight_manager == insight_mgr
        assert detector.event_log == event_log

    def test_suggest_for_new_insight_empty(self, detector):
        suggestions = detector.suggest_for_new_insight("Test", ["tag1"], lookback_days=0)
        assert suggestions == []

    def test_suggest_with_tag_matching(self, insight_mgr, detector):
        # Create existing insights
        insight_mgr.create(
            title="Base Pattern",
            tags=["python", "refactor"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        insight_mgr.create(
            title="Advanced Pattern",
            tags=["python", "architecture"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        # Suggest for new insight with matching tags (disable lookback to avoid date issues)
        suggestions = detector.suggest_for_new_insight(
            "New Pattern", ["python", "design"], lookback_days=0
        )

        assert len(suggestions) > 0
        # First suggestion should be related to python tag
        assert "INS-001" in [s.insight_id for s in suggestions]


# -----------------------------------------------------------------------------
# Tests: DerivationDetector - Task-based detection
# -----------------------------------------------------------------------------


class TestDerivationFromTask:
    def test_detect_from_task_completion_no_events(self, detector):
        suggestions = detector.detect_from_task_completion("TASK-DEV-001")
        assert suggestions == []

    def test_get_insights_used_during_task(self, insight_mgr, event_log, detector):
        from datetime import datetime, timezone

        # Create insight
        ins = insight_mgr.create(
            title="Test Insight",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        now = datetime.now(timezone.utc).isoformat()

        # Log task transition to IN_PROGRESS
        event_log.append(
            Event(
                event_type=EventType.TASK_STATUS_CHANGED,
                actor="test",
                summary="Task started",
                payload={"task_id": "TASK-DEV-001", "new_status": "IN_PROGRESS"},
                timestamp=now,
            )
        )

        # Log insight usage
        event_log.append(
            Event(
                event_type=EventType.CUSTOM,
                actor="test",
                summary="Used insight",
                payload={"action": "insight_used", "insight_id": ins.id, "task_id": "TASK-DEV-001"},
                timestamp=now,
            )
        )

        # Log task completion
        event_log.append(
            Event(
                event_type=EventType.TASK_COMPLETED,
                actor="test",
                summary="Task completed",
                payload={"task_id": "TASK-DEV-001", "new_status": "DONE"},
                timestamp=now,
            )
        )

        used = detector._get_insights_used_during_task("TASK-DEV-001")
        assert ins.id in used

    def test_get_recently_used_insights(self, insight_mgr, event_log, detector):
        from datetime import datetime, timezone

        # Create and use insight
        ins = insight_mgr.create(
            title="Recent Insight",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        now = datetime.now(timezone.utc).isoformat()

        event_log.append(
            Event(
                event_type=EventType.CUSTOM,
                actor="test",
                summary="Used insight",
                payload={"action": "insight_used", "insight_id": ins.id},
                timestamp=now,
            )
        )

        recent = detector._get_recently_used_insights(days=7)
        assert ins.id in recent


# -----------------------------------------------------------------------------
# Tests: DerivationDetector - Create with derivation
# -----------------------------------------------------------------------------


class TestCreateWithDerivation:
    def test_create_without_auto_derivation(self, insight_mgr, detector):
        insight, suggestions = detector.create_insight_with_derivation(
            title="Standalone Insight",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
            auto_derivation=False,
        )

        assert insight.id == "INS-001"
        assert insight.origin.derived_from == []

    def test_create_with_manual_derivation(self, insight_mgr, detector):
        # Create parent insight
        parent = insight_mgr.create(
            title="Parent Insight",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        # Create child with manual derived_from
        child, suggestions = detector.create_insight_with_derivation(
            title="Child Insight",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
            derived_from=[parent.id],
            auto_derivation=False,
        )

        assert child.origin.derived_from == [parent.id]

    def test_create_with_auto_derivation(self, insight_mgr, event_log, detector):
        # Create parent insight
        parent = insight_mgr.create(
            title="Parent Pattern",
            tags=["python", "pattern"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        # Log usage of parent insight
        event_log.append(
            Event(
                event_type=EventType.CUSTOM,
                actor="test",
                summary="Used parent",
                payload={"action": "insight_used", "insight_id": parent.id},
            )
        )

        # Create child with matching tags
        child, suggestions = detector.create_insight_with_derivation(
            title="Child Pattern",
            tags=["python", "pattern", "advanced"],
            category="technique",
            body=_body(),
            created_by="test",
            auto_derivation=True,
            min_confidence=0.3,  # Lower threshold for test
        )

        # Should have auto-detected derivation
        assert len(suggestions) > 0
        # The parent might be included based on confidence


# -----------------------------------------------------------------------------
# Tests: DerivationDetector - Tag matching
# -----------------------------------------------------------------------------


class TestTagMatching:
    def test_find_tag_matching_insights(self, insight_mgr, detector):
        insight_mgr.create(
            title="Python Tips",
            tags=["python", "tips"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        insight_mgr.create(
            title="Java Guide",
            tags=["java", "guide"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        matches = detector._find_tag_matching_insights(["python", "coding"])

        assert len(matches) > 0
        assert matches[0][0] == "INS-001"  # Python tips should match
        assert matches[0][1] == 0.5  # 1 of 2 tags match

    def test_find_tag_matching_empty(self, detector):
        matches = detector._find_tag_matching_insights([])
        assert matches == []


# -----------------------------------------------------------------------------
# Tests: Event log integration
# -----------------------------------------------------------------------------


class TestEventLogIntegration:
    def test_record_task_insight_link(self, insight_mgr, event_log, detector):
        detector.record_task_insight_link("TASK-DEV-001", "INS-001", "related")

        events = event_log.read_all()
        assert len(events) == 1
        assert events[0].payload["action"] == "task_insight_linked"
        assert events[0].payload["task_id"] == "TASK-DEV-001"
        assert events[0].payload["insight_id"] == "INS-001"

    def test_no_event_log(self, insight_mgr):
        detector = DerivationDetector(insight_mgr, None)
        # Should not raise
        detector.record_task_insight_link("TASK-DEV-001", "INS-001")

        # No events should be recorded (no crash)
        recent = detector._get_recently_used_insights(days=7)
        assert recent == set()


# -----------------------------------------------------------------------------
# Tests: Confidence scoring
# -----------------------------------------------------------------------------


class TestConfidenceScoring:
    def test_confidence_calculation(self, insight_mgr, event_log, detector):
        # Create multiple insights
        ins1 = insight_mgr.create(
            title="Base",
            tags=["python"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        ins2 = insight_mgr.create(
            title="Related",
            tags=["python", "advanced"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        # Log usage for ins1
        event_log.append(
            Event(
                event_type=EventType.CUSTOM,
                actor="test",
                summary="Used base",
                payload={"action": "insight_used", "insight_id": ins1.id},
            )
        )

        # Suggestions should have confidence scores
        suggestions = detector.suggest_for_new_insight(
            "New", ["python", "advanced"], lookback_days=7
        )

        for s in suggestions:
            assert 0.0 <= s.confidence <= 1.0

    def test_filter_by_min_confidence(self, insight_mgr, detector):
        # Create insight
        insight_mgr.create(
            title="Match",
            tags=["python"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        # Get suggestions with high threshold
        suggestions = detector.suggest_for_new_insight(
            "New", ["completely", "different", "tags"], lookback_days=7
        )

        # Should be empty or have low confidence
        high_conf = [s for s in suggestions if s.confidence >= 0.8]
        assert len(high_conf) == 0


# -----------------------------------------------------------------------------
# Edge cases
# -----------------------------------------------------------------------------


class TestDerivationEdgeCases:
    def test_circular_derivation_detection(self, insight_mgr, detector):
        # This tests that we don't have issues with circular references
        # in the suggestion logic (actual circular detection is in get_full_trace)
        ins1 = insight_mgr.create(
            title="A",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
        )

        # Create with self-reference (should be handled gracefully)
        ins2, _ = detector.create_insight_with_derivation(
            title="B",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
            derived_from=[ins1.id],
            auto_derivation=False,
        )

        assert ins2.origin.derived_from == [ins1.id]

    def test_nonexistent_task(self, detector):
        suggestions = detector.detect_from_task_completion("NONEXISTENT-TASK")
        assert suggestions == []

    def test_missing_insight_in_suggestions(self, insight_mgr, detector):
        # Suggest with non-existent insight ID in manual list
        child, _ = detector.create_insight_with_derivation(
            title="Child",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
            derived_from=["INS-999"],  # Non-existent
            auto_derivation=False,
        )

        # Should still create but with the invalid reference
        assert child.origin.derived_from == ["INS-999"]
