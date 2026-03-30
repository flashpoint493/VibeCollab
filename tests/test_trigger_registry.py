"""Tests for Trigger Registry"""

import tempfile
from pathlib import Path

import yaml

from vibecollab.domain.trigger_registry import Trigger, TriggerRegistry


class TestTrigger:
    """Test Trigger dataclass"""

    def test_trigger_creation(self):
        """Test creating a trigger"""
        trigger = Trigger(
            word="test",
            insight_id="INS-001",
            insight_title="Test Insight",
            skill_name="Test Skill",
            skill_description="A test skill",
            role="DEV",
            priority=8,
        )

        assert trigger.word == "test"
        assert trigger.role == "DEV"
        assert trigger.priority == 8


class TestTriggerRegistry:
    """Test TriggerRegistry class"""

    def test_empty_registry(self):
        """Test registry with no insights"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = TriggerRegistry(Path(tmpdir))
            triggers = registry.get_all_triggers()

            assert triggers == []

    def test_load_triggers_from_insight(self):
        """Test loading triggers from insight file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            # Create a test insight with role_skills
            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "title": "Test Insight",
                "role_skills": {
                    "DEV": [
                        {
                            "id": "skill1",
                            "name": "Test Skill",
                            "description": "A test skill",
                            "trigger": "test trigger",
                            "priority": 8,
                        }
                    ]
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)
            triggers = registry.get_all_triggers()

            assert len(triggers) == 1
            assert triggers[0].word == "test trigger"
            assert triggers[0].role == "DEV"
            assert triggers[0].priority == 8

    def test_get_triggers_by_role(self):
        """Test filtering triggers by role"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "role_skills": {
                    "DEV": [{"id": "dev_skill", "name": "Dev Skill", "trigger": "dev"}],
                    "ARCH": [{"id": "arch_skill", "name": "Arch Skill", "trigger": "arch"}],
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)

            dev_triggers = registry.get_triggers_by_role("DEV")
            arch_triggers = registry.get_triggers_by_role("ARCH")

            assert len(dev_triggers) == 1
            assert dev_triggers[0].word == "dev"

            assert len(arch_triggers) == 1
            assert arch_triggers[0].word == "arch"

    def test_search_triggers(self):
        """Test searching triggers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "role_skills": {
                    "DEV": [
                        {"id": "refactor", "name": "Refactoring", "trigger": "refactor code"},
                        {"id": "test", "name": "Testing", "trigger": "write test"},
                    ]
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)
            matches = registry.search_triggers("refactor")

            assert len(matches) == 1
            assert matches[0].word == "refactor code"

    def test_get_trigger_stats(self):
        """Test getting trigger statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "role_skills": {
                    "DEV": [
                        {"id": "skill1", "name": "Skill 1", "trigger": "trigger1"},
                        {"id": "skill2", "name": "Skill 2", "trigger": "trigger2"},
                    ],
                    "ARCH": [{"id": "skill3", "name": "Skill 3", "trigger": "trigger3"}],
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)
            stats = registry.get_trigger_stats()

            assert stats["total_triggers"] == 3
            assert stats["triggers_by_role"]["DEV"] == 2
            assert stats["triggers_by_role"]["ARCH"] == 1
            assert stats["unique_trigger_words"] == 3

    def test_find_trigger_exact_match(self):
        """Test finding exact trigger"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "role_skills": {
                    "DEV": [{"id": "skill1", "name": "Skill 1", "trigger": "exact match"}]
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = TriggerRegistry(insights_dir)

            found = registry.find_trigger("exact match")
            not_found = registry.find_trigger("nonexistent")

            assert found is not None
            assert found.word == "exact match"
            assert not_found is None
