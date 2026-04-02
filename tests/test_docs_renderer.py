"""
Tests for DocsRenderer module
"""

from pathlib import Path

import pytest

from vibecollab.core.docs_renderer import DocsRenderer


class TestDocsRenderer:
    """Test DocsRenderer functionality"""

    def test_init_default_templates(self):
        """Test renderer initializes with default templates"""
        renderer = DocsRenderer()
        assert renderer.templates_dir.exists()
        assert (renderer.templates_dir / "context.md.j2").exists()

    def test_list_renderable_docs(self, tmp_path):
        """Test listing renderable YAML documents"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create valid YAML files
        (docs_dir / "context.yaml").write_text("""
kind: context
version: "1"
project_status:
  current_version: "v1.0"
""")
        (docs_dir / "changelog.yaml").write_text("""
kind: changelog
version: "1"
entries: []
""")
        # Create invalid/non-renderable file
        (docs_dir / "random.yaml").write_text("foo: bar")

        renderer = DocsRenderer()
        result = renderer.list_renderable_docs(docs_dir)

        assert len(result) == 2
        kinds = [r["kind"] for r in result]
        assert "context" in kinds
        assert "changelog" in kinds

    def test_validate_doc_valid(self, tmp_path):
        """Test validating a valid document"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
kind: context
version: "1"
project_status:
  current_version: "v1.0"
""")

        renderer = DocsRenderer()
        is_valid, errors = renderer.validate_doc(yaml_file)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_doc_missing_kind(self, tmp_path):
        """Test validating document without kind"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("version: '1'")

        renderer = DocsRenderer()
        is_valid, errors = renderer.validate_doc(yaml_file)

        assert is_valid is False
        assert any("kind" in e.lower() for e in errors)

    def test_validate_doc_empty(self, tmp_path):
        """Test validating empty document"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("")

        renderer = DocsRenderer()
        is_valid, errors = renderer.validate_doc(yaml_file)

        assert is_valid is False

    def test_render_doc_context(self, tmp_path):
        """Test rendering context document"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        yaml_file = docs_dir / "context.yaml"
        yaml_file.write_text("""
kind: context
version: "1"
updated_at: "2026-04-01"
project_status:
  current_version: "v1.0"
  active_role: "dev"
  milestone: "Test milestone"
""")

        renderer = DocsRenderer()
        output = renderer.render_doc(yaml_file)

        assert output.exists()
        assert output.name == "CONTEXT.md"
        content = output.read_text()
        assert "v1.0" in content
        assert "Test milestone" in content

    def test_render_doc_decisions(self, tmp_path):
        """Test rendering decisions document"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        yaml_file = docs_dir / "decisions.yaml"
        yaml_file.write_text("""
kind: decisions
version: "1"
decisions:
  - id: DECISION-001
    title: "Test Decision"
    date: "2026-04-01"
    level: S
    status: confirmed
    context: "Test context"
    problem: "Test problem"
    decision_text: "Test decision"
    rationale: "Test rationale"
""")

        renderer = DocsRenderer()
        output = renderer.render_doc(yaml_file)

        assert output.exists()
        assert output.name == "DECISIONS.md"
        content = output.read_text()
        assert "DECISION-001" in content
        assert "Test Decision" in content

    def test_render_doc_changelog(self, tmp_path):
        """Test rendering changelog document"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        yaml_file = docs_dir / "changelog.yaml"
        yaml_file.write_text("""
kind: changelog
version: "1"
entries:
  - version: "v1.0.0"
    date: "2026-04-01"
    changes:
      - type: added
        description: "Initial release"
""")

        renderer = DocsRenderer()
        output = renderer.render_doc(yaml_file)

        assert output.exists()
        assert output.name == "CHANGELOG.md"
        content = output.read_text()
        assert "v1.0.0" in content
        assert "Initial release" in content

    def test_render_all(self, tmp_path):
        """Test rendering all documents"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create multiple YAML files
        (docs_dir / "context.yaml").write_text("""
kind: context
version: "1"
updated_at: "2026-04-01"
project_status:
  current_version: "v1.0"
  active_role: "dev"
  milestone: "Test"
""")
        (docs_dir / "changelog.yaml").write_text("""
kind: changelog
version: "1"
entries: []
""")

        renderer = DocsRenderer()
        results = renderer.render_all(docs_dir)

        assert len(results) == 2
        assert all(isinstance(p, Path) for p in results.values())
        assert (docs_dir / "CONTEXT.md").exists()
        assert (docs_dir / "CHANGELOG.md").exists()

    def test_render_all_with_kinds_filter(self, tmp_path):
        """Test rendering specific kinds only"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (docs_dir / "context.yaml").write_text("""
kind: context
version: "1"
updated_at: "2026-04-01"
project_status:
  current_version: "v1.0"
  active_role: "dev"
  milestone: "Test"
""")
        (docs_dir / "changelog.yaml").write_text("""
kind: changelog
version: "1"
entries: []
""")

        renderer = DocsRenderer()
        results = renderer.render_all(docs_dir, kinds=["context"])

        assert len(results) == 1
        assert "context" in results
        assert (docs_dir / "CONTEXT.md").exists()
        assert not (docs_dir / "CHANGELOG.md").exists()

    def test_render_doc_unknown_kind(self, tmp_path):
        """Test rendering document with unknown kind"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        yaml_file = docs_dir / "unknown.yaml"
        yaml_file.write_text("""
kind: unknown_type
version: "1"
""")

        renderer = DocsRenderer()
        with pytest.raises(ValueError, match="Unknown document kind"):
            renderer.render_doc(yaml_file)
