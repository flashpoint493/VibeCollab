"""Tests for Skill Registry"""

import tempfile
from pathlib import Path

import yaml

from vibecollab.domain.skill_registry import Skill, SkillRegistry


class TestSkill:
    """Test Skill dataclass"""

    def test_to_prompt_text_basic(self):
        """Test basic prompt text generation"""
        skill = Skill(id="test_skill", name="Test Skill", description="A test skill")

        text = skill.to_prompt_text()
        assert "Test Skill" in text
        assert "A test skill" in text

    def test_to_prompt_text_with_trigger(self):
        """Test prompt text with trigger"""
        skill = Skill(
            id="refactor",
            name="Refactoring",
            description="Extract functions",
            trigger="refactor large function",
        )

        text = skill.to_prompt_text()
        assert "Refactoring" in text
        assert "refactor large function" in text


class TestSkillRegistry:
    """Test SkillRegistry class"""

    def test_empty_registry(self):
        """Test registry with no insights"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SkillRegistry(Path(tmpdir))
            skills = registry.get_skills_for_role("DEV")

            assert skills == []

    def test_load_skills_from_insight(self):
        """Test loading skills from insight file"""
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
                            "id": "refactoring",
                            "name": "Function Refactoring",
                            "description": "Extract large functions",
                            "priority": 8,
                            "trigger": "refactor",
                        }
                    ]
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = SkillRegistry(insights_dir)
            skills = registry.get_skills_for_role("DEV")

            assert len(skills) == 1
            assert skills[0].id == "refactoring"
            assert skills[0].name == "Function Refactoring"
            assert skills[0].priority == 8

    def test_skills_sorted_by_priority(self):
        """Test that skills are sorted by priority descending"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "role_skills": {
                    "DEV": [
                        {"id": "low", "name": "Low Priority", "priority": 3},
                        {"id": "high", "name": "High Priority", "priority": 9},
                        {"id": "medium", "name": "Medium Priority", "priority": 6},
                    ]
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = SkillRegistry(insights_dir)
            skills = registry.get_skills_for_role("DEV")

            assert skills[0].id == "high"
            assert skills[1].id == "medium"
            assert skills[2].id == "low"

    def test_different_roles_get_different_skills(self):
        """Test that different roles get different skills"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "role_skills": {
                    "DEV": [{"id": "dev_skill", "name": "Dev Skill"}],
                    "ARCH": [{"id": "arch_skill", "name": "Arch Skill"}],
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = SkillRegistry(insights_dir)

            dev_skills = registry.get_skills_for_role("DEV")
            arch_skills = registry.get_skills_for_role("ARCH")

            assert len(dev_skills) == 1
            assert dev_skills[0].id == "dev_skill"

            assert len(arch_skills) == 1
            assert arch_skills[0].id == "arch_skill"

    def test_find_skills_by_trigger(self):
        """Test finding skills by trigger word"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "role_skills": {
                    "DEV": [
                        {"id": "refactor", "name": "Refactoring", "trigger": "refactor function"},
                        {"id": "test", "name": "Testing", "trigger": "write test"},
                    ]
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = SkillRegistry(insights_dir)
            matches = registry.find_skills_by_trigger("DEV", "refactor")

            assert len(matches) == 1
            assert matches[0].id == "refactor"

    def test_format_skills_for_prompt(self):
        """Test formatting skills as prompt text"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            insight_data = {
                "kind": "insight",
                "id": "INS-TEST",
                "role_skills": {
                    "DEV": [{"id": "skill1", "name": "Skill One", "description": "First skill"}]
                },
            }

            insight_file = insights_dir / "INS-TEST.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            registry = SkillRegistry(insights_dir)
            prompt = registry.format_skills_for_prompt("DEV")

            assert "Available skills for DEV role:" in prompt
            assert "Skill One" in prompt
            assert "First skill" in prompt

    def test_cache_invalidation(self):
        """Test cache invalidation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            insights_dir = Path(tmpdir)

            # First call populates cache
            registry = SkillRegistry(insights_dir)
            _ = registry.get_skills_for_role("DEV")  # Populate cache

            # Invalidate cache
            registry.invalidate_cache()

            # Add new insight
            insight_data = {
                "kind": "insight",
                "id": "INS-NEW",
                "role_skills": {"DEV": [{"id": "new_skill", "name": "New Skill"}]},
            }

            insight_file = insights_dir / "INS-NEW.yaml"
            with open(insight_file, "w") as f:
                yaml.dump(insight_data, f)

            # Second call should see new skill
            skills2 = registry.get_skills_for_role("DEV")

            assert len(skills2) == 1
            assert skills2[0].id == "new_skill"
