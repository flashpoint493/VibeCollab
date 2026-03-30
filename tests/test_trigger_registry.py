"""Tests for Trigger Registry (Tag-based)"""

import tempfile
from pathlib import Path

import yaml

from vibecollab.domain.trigger_registry import Trigger, TriggerRegistry


class TestTrigger:
    """Test Trigger dataclass"""

    def test_trigger_creation(self):
        """Test creating a trigger"""
        trigger = Trigger(
            word="git",
            insight_ids=["INS-001", "INS-002"],
            insight_titles=["Git Best Practices", "Git Workflow"],
            count=2,
        )

        assert trigger.word == "git"
        assert len(trigger.insight_ids) == 2
        assert trigger.count == 2


class TestTriggerRegistry:
    """Test TriggerRegistry class"""

    def test_empty_registry(self):
        """Test registry with no insights"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = TriggerRegistry(Path(tmpdir))
            triggers = registry.get_all_triggers()

            assert triggers == []

    def test_load_triggers_from_tags(self):
        """Test loading triggers from insight tags"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            # Create a test insight with tags
            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "title": "Test Insight",
                "tags": ["git", "workflow", "best-practice"],
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)
            triggers = registry.get_all_triggers()

            assert len(triggers) == 3
            trigger_words = [t.word for t in triggers]
            assert "git" in trigger_words
            assert "workflow" in trigger_words
            assert "best-practice" in trigger_words

    def test_trigger_counts_multiple_insights(self):
        """Test that triggers count multiple insights with same tag"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            # Create two insights with same tag
            insight1 = {
                "kind": "insight",
                "id": "INS-001",
                "title": "Git Basics",
                "tags": ["git"],
            }
            insight2 = {
                "kind": "insight",
                "id": "INS-002",
                "title": "Git Advanced",
                "tags": ["git"],
            }

            with open(insights_dir / "INS-001.yaml", "w") as f:
                yaml.dump(insight1, f)
            with open(insights_dir / "INS-002.yaml", "w") as f:
                yaml.dump(insight2, f)

            registry = TriggerRegistry(insights_dir)
            git_trigger = registry.get_trigger("git")

            assert git_trigger is not None
            assert git_trigger.count == 2
            assert len(git_trigger.insight_ids) == 2

    def test_search_triggers(self):
        """Test searching triggers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "title": "Git Workflow Best Practices",
                "tags": ["git", "workflow"],
            }

            with open(insights_dir / "INS-TEST.yaml", "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)

            # Search by tag word
            matches = registry.search_triggers("git")
            assert len(matches) == 1
            assert matches[0].word == "git"

            # Search by tag word
            matches = registry.search_triggers("workflow")
            assert len(matches) == 1
            assert matches[0].word == "workflow"

            # Search by title word (should match "workflow" in title and tag)
            matches = registry.search_triggers("practices")
            # "practices" appears in title, should match both triggers
            assert len(matches) == 2

            # Search with no match
            matches = registry.search_triggers("nonexistent")
            assert len(matches) == 0

    def test_get_trigger_stats(self):
        """Test getting trigger statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "title": "Test Insight",
                "tags": ["git", "workflow", "testing"],
            }

            with open(insights_dir / "INS-TEST.yaml", "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)
            stats = registry.get_trigger_stats()

            assert stats["total_triggers"] == 3
            assert stats["total_insights"] == 1

    def test_get_insights_by_tag(self):
        """Test getting insights by tag"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "title": "Git Best Practices",
                "tags": ["git"],
            }

            with open(insights_dir / "INS-TEST.yaml", "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)
            insights = registry.get_insights_by_tag("git")

            assert len(insights) == 1
            assert insights[0]["id"] == "INS-TEST"
            assert insights[0]["title"] == "Git Best Practices"

    def test_cache_invalidation(self):
        """Test cache invalidation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            # First call populates cache
            registry = TriggerRegistry(insights_dir)
            _ = registry.get_all_triggers()

            # Invalidate cache
            registry.invalidate_cache()

            # Add new insight
            insight_data = {
                "kind": "insight",
                "id": "INS-NEW",
                "title": "New Insight",
                "tags": ["new-tag"],
            }

            with open(insights_dir / "INS-NEW.yaml", "w") as f:
                yaml.dump(insight_data, f)

            # Second call should see new trigger
            triggers = registry.get_all_triggers()
            trigger_words = [t.word for t in triggers]

            assert "new-tag" in trigger_words
