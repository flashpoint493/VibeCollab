"""Tests for LLMsTxtManager."""

from pathlib import Path

import pytest

from vibecollab.llmstxt import LLMsTxtManager


class TestFindLlmstxt:
    def test_find_existing(self, tmp_path):
        (tmp_path / "llms.txt").write_text("# Project", encoding="utf-8")
        assert LLMsTxtManager.find_llmstxt(tmp_path) == tmp_path / "llms.txt"

    def test_find_missing(self, tmp_path):
        assert LLMsTxtManager.find_llmstxt(tmp_path) is None


class TestHasAiCollabSection:
    def test_has_section_heading(self):
        assert LLMsTxtManager.has_ai_collab_section("## AI Collaboration\nstuff")

    def test_has_contributing_ai_ref(self):
        assert LLMsTxtManager.has_ai_collab_section("see CONTRIBUTING_AI.md")

    def test_has_ai_collaboration_variant(self):
        assert LLMsTxtManager.has_ai_collab_section("## AI Dev Collaboration")

    def test_no_section(self):
        assert not LLMsTxtManager.has_ai_collab_section("# Project\n## Overview\nnothing here")

    def test_empty_content(self):
        assert not LLMsTxtManager.has_ai_collab_section("")


class TestFindInsertionPoint:
    def test_after_documentation_section(self):
        content = "# Project\n## Documentation\n- doc1\n## Other\n- other"
        pos = LLMsTxtManager.find_insertion_point(content)
        lines = content.split("\n")
        assert lines[pos] == "## Other"

    def test_documentation_at_end(self):
        content = "# Project\n## Documentation\n- doc1\n- doc2"
        pos = LLMsTxtManager.find_insertion_point(content)
        assert pos == 4  # after last line

    def test_no_documentation_section(self):
        content = "# Project\n## Overview\n- stuff"
        pos = LLMsTxtManager.find_insertion_point(content)
        assert pos == 3  # end of file


class TestUpdateLlmstxt:
    def test_update_adds_section(self, tmp_path):
        llmstxt = tmp_path / "llms.txt"
        llmstxt.write_text("# Project\n## Documentation\n- docs\n", encoding="utf-8")
        contrib = tmp_path / "CONTRIBUTING_AI.md"
        contrib.touch()

        result = LLMsTxtManager.update_llmstxt(llmstxt, contrib)
        assert result is True
        content = llmstxt.read_text(encoding="utf-8")
        assert "AI Collaboration" in content
        assert "CONTRIBUTING_AI.md" in content

    def test_update_skips_existing(self, tmp_path):
        llmstxt = tmp_path / "llms.txt"
        llmstxt.write_text("# Project\n## AI Collaboration\n- existing", encoding="utf-8")
        contrib = tmp_path / "CONTRIBUTING_AI.md"
        contrib.touch()

        result = LLMsTxtManager.update_llmstxt(llmstxt, contrib)
        assert result is False

    def test_update_with_relative_path(self, tmp_path):
        subdir = tmp_path / "docs"
        subdir.mkdir()
        llmstxt = tmp_path / "llms.txt"
        llmstxt.write_text("# Project\n", encoding="utf-8")
        contrib = tmp_path / "docs" / "CONTRIBUTING_AI.md"
        contrib.touch()

        LLMsTxtManager.update_llmstxt(llmstxt, contrib)
        content = llmstxt.read_text(encoding="utf-8")
        assert "docs" in content or "CONTRIBUTING_AI" in content


class TestCreateLlmstxt:
    def test_creates_file(self, tmp_path):
        contrib = tmp_path / "CONTRIBUTING_AI.md"
        contrib.touch()

        path = LLMsTxtManager.create_llmstxt(
            tmp_path, "TestProject", "A test project", contrib
        )
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "TestProject" in content
        assert "A test project" in content
        assert "AI Collaboration" in content


class TestEnsureIntegration:
    def test_creates_new_when_missing(self, tmp_path):
        contrib = tmp_path / "CONTRIBUTING_AI.md"
        contrib.touch()

        updated, path = LLMsTxtManager.ensure_integration(
            tmp_path, "Test", "desc", contrib
        )
        assert updated is True
        assert path.exists()

    def test_updates_existing(self, tmp_path):
        llmstxt = tmp_path / "llms.txt"
        llmstxt.write_text("# Existing\n", encoding="utf-8")
        contrib = tmp_path / "CONTRIBUTING_AI.md"
        contrib.touch()

        updated, path = LLMsTxtManager.ensure_integration(
            tmp_path, "Test", "desc", contrib
        )
        assert updated is True
        assert "AI Collaboration" in path.read_text(encoding="utf-8")

    def test_no_update_when_already_exists(self, tmp_path):
        llmstxt = tmp_path / "llms.txt"
        llmstxt.write_text("# Project\n## AI Collaboration\n", encoding="utf-8")
        contrib = tmp_path / "CONTRIBUTING_AI.md"
        contrib.touch()

        updated, path = LLMsTxtManager.ensure_integration(
            tmp_path, "Test", "desc", contrib
        )
        assert updated is False
