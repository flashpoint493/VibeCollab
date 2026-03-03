"""
Tests for LLMContext Generator
"""

import tempfile
from pathlib import Path

import yaml

from vibecollab import LLMContextGenerator, Project


class TestLLMContextGenerator:
    """Generator tests."""

    def test_generate_basic(self):
        """Test basic generation."""
        config = {
            "project": {
                "name": "TestProject",
                "version": "v1.0",
                "domain": "generic"
            },
            "philosophy": {
                "vibe_development": {
                    "enabled": True,
                    "principles": ["Test principle"]
                },
                "decision_quality": {
                    "target_rate": 0.9,
                    "critical_tolerance": 0
                }
            },
            "roles": [
                {
                    "code": "DEV",
                    "name": "Development",
                    "focus": ["Implementation"],
                    "triggers": ["develop"],
                    "is_gatekeeper": False
                }
            ],
            "decision_levels": [
                {
                    "level": "S",
                    "name": "Strategic",
                    "scope": "Overall direction",
                    "review": {"required": True, "mode": "sync"}
                }
            ]
        }

        generator = LLMContextGenerator(config)
        content = generator.generate()

        assert "TestProject" in content
        assert "Vibe Development" in content
        assert "[DEV]" in content

    def test_validate_missing_project(self):
        """Test validation: missing project."""
        config = {}
        generator = LLMContextGenerator(config)
        errors = generator.validate()

        assert len(errors) > 0
        assert any("project" in e for e in errors)

    def test_validate_invalid_decision_level(self):
        """Test validation: invalid decision level."""
        config = {
            "project": {"name": "Test"},
            "decision_levels": [
                {"level": "X", "name": "Invalid"}
            ]
        }
        generator = LLMContextGenerator(config)
        errors = generator.validate()

        assert any("decision" in e.lower() or "level" in e.lower() for e in errors)


class TestProject:
    """Project tests."""

    def test_create_project(self):
        """Test project creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            project = Project.create(
                name="TestProject",
                domain="generic",
                output_dir=output_dir
            )
            project.generate_all()

            assert (output_dir / "CONTRIBUTING_AI.md").exists()
            assert (output_dir / "project.yaml").exists()
            assert (output_dir / "docs" / "CONTEXT.md").exists()
            assert (output_dir / "docs" / "DECISIONS.md").exists()

    def test_project_config_content(self):
        """Test project config content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            project = Project.create(
                name="MyTestProject",
                domain="web",
                output_dir=output_dir
            )
            project.generate_all()

            with open(output_dir / "project.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            assert config["project"]["name"] == "MyTestProject"
            assert config["project"]["domain"] == "web"

    def test_chapter_numbering(self):
        """Test chapter numbering correctness."""
        config = {
            "project": {
                "name": "TestProject",
                "version": "v1.0",
                "domain": "generic"
            },
            "philosophy": {
                "vibe_development": {
                    "enabled": True,
                    "principles": ["Test principle"]
                },
                "decision_quality": {
                    "target_rate": 0.9,
                    "critical_tolerance": 0
                }
            },
            "roles": [
                {
                    "code": "DEV",
                    "name": "Development",
                    "focus": ["Implementation"],
                    "triggers": ["develop"],
                    "is_gatekeeper": False
                }
            ],
            "decision_levels": [
                {
                    "level": "S",
                    "name": "Strategic",
                    "scope": "Overall direction",
                    "review": {"required": True, "mode": "sync"}
                }
            ],
            "documentation": {
                "key_files": []
            },
            "multi_developer": {
                "enabled": True,
                "identity": {
                    "primary": "git_username",
                    "fallback": "system_user",
                    "normalize": True
                }
            },
            "symbology": {
                "decision_status": [
                    {"symbol": "PENDING", "meaning": "Pending"}
                ]
            },
            "lifecycle": {
                "stages": {
                    "demo": {
                        "name": "Prototype",
                        "description": "Rapidly validate core concepts",
                        "focus": ["Rapid iteration"],
                        "principles": ["Fail fast"]
                    }
                }
            }
        }

        generator = LLMContextGenerator(config)
        content = generator.generate()

        # Verify main chapter numbering order
        expected_chapters = [
            "# I. Core Philosophy",
            "# II. Role Definitions",
            "# III. Decision Classification System",
            "# IV. Development Workflow Protocol",
            "# V. Testing System",
            "# VI. Milestone Definition",
            "# VII. Iteration Management",
            "# VIII. Phase-Based Collaboration Rules",
            "# IX. Context Management",
            "# X. Multi-Developer/Agent Collaboration Protocol",
            "# XI. Symbology Annotation System",
            "# XII. Protocol Self-Check Mechanism",
        ]

        for chapter in expected_chapters:
            assert chapter in content, f"Chapter '{chapter}' not found"

        # Verify no duplicate chapter numbering
        import re
        chapter_pattern = r'^# (I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV)\.'
        chapters_found = re.findall(chapter_pattern, content, re.MULTILINE)

        from collections import Counter
        chapter_counts = Counter(chapters_found)
        duplicates = [ch for ch, count in chapter_counts.items() if count > 1]
        assert len(duplicates) == 0, f"Found duplicate chapter numbering: {duplicates}"

        # Verify sub-chapter numbering (multi-developer section)
        assert "## 10.1 Collaboration Mode Overview" in content
        assert "## 10.2 Directory Structure" in content
        assert "## 10.3 Developer Identity Detection" in content
        assert "## 10.4 Context Management" in content

        # Verify phase-based collaboration sub-chapters
        assert "## 8.1 Project Lifecycle Phases" in content
        assert "## 8.2 Phase-Based Collaboration Guidance" in content

        # Verify context management sub-chapters
        assert "## 9.1 Key File Responsibilities" in content
        assert "## 9.2 Context Restoration Protocol" in content
        assert "## 9.3 Context Save Protocol" in content

        # Verify protocol self-check sub-chapters
        assert "## 12.1 Importance of Protocol Self-Check" in content
        assert "## 12.2 Self-Check Trigger Methods" in content

