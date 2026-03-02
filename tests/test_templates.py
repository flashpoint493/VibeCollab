"""Tests for TemplateManager."""


import pytest
import yaml

from vibecollab.core.templates import TemplateManager


@pytest.fixture
def templates_dir(tmp_path):
    """Create a temporary templates directory with sample files."""
    tdir = tmp_path / "templates"
    tdir.mkdir()

    # Project template
    (tdir / "web.project.yaml").write_text(
        yaml.dump({"project": {"name": "web"}}), encoding="utf-8"
    )
    (tdir / "default.yaml").write_text(
        yaml.dump({"project": {"name": "default"}}), encoding="utf-8"
    )

    # Domain extensions
    domains = tdir / "domains"
    domains.mkdir()
    (domains / "python.extension.yaml").write_text(
        yaml.dump({"domain": "python"}), encoding="utf-8"
    )

    return tdir


class TestInit:
    def test_custom_templates_dir(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        assert mgr.templates_dir == templates_dir

    def test_default_templates_dir_fallback(self):
        mgr = TemplateManager()
        assert mgr.templates_dir is not None


class TestListTemplates:
    def test_lists_project_and_extension(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        templates = mgr.list_templates()
        names = [t["name"] for t in templates]
        types = [t["type"] for t in templates]

        assert "web" in names
        assert "default" in names
        assert "python" in names
        assert "project" in types
        assert "extension" in types

    def test_empty_templates_dir(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        mgr = TemplateManager(templates_dir=empty)
        assert mgr.list_templates() == []

    def test_no_domains_dir(self, tmp_path):
        tdir = tmp_path / "nodomain"
        tdir.mkdir()
        (tdir / "a.project.yaml").write_text("x: 1", encoding="utf-8")
        mgr = TemplateManager(templates_dir=tdir)
        result = mgr.list_templates()
        assert len(result) == 1
        assert result[0]["type"] == "project"


class TestGetTemplate:
    def test_get_project_template(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        content = mgr.get_template("web")
        assert "web" in content

    def test_get_extension_template(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        content = mgr.get_template("python")
        assert "python" in content

    def test_get_plain_yaml(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        content = mgr.get_template("default")
        assert "default" in content

    def test_get_nonexistent_raises(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        with pytest.raises(FileNotFoundError, match="模板不存在"):
            mgr.get_template("nonexistent")


class TestLoadConfig:
    def test_load_returns_dict(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        config = mgr.load_config("web")
        assert isinstance(config, dict)
        assert config["project"]["name"] == "web"


class TestSaveTemplate:
    def test_save_project_template(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        mgr.save_template("newproj", {"project": {"name": "newproj"}}, "project")
        saved = templates_dir / "newproj.project.yaml"
        assert saved.exists()
        data = yaml.safe_load(saved.read_text(encoding="utf-8"))
        assert data["project"]["name"] == "newproj"

    def test_save_extension_template(self, templates_dir):
        mgr = TemplateManager(templates_dir=templates_dir)
        mgr.save_template("go", {"domain": "go"}, "extension")
        saved = templates_dir / "domains" / "go.extension.yaml"
        assert saved.exists()

    def test_save_extension_creates_domains_dir(self, tmp_path):
        tdir = tmp_path / "tpl"
        tdir.mkdir()
        mgr = TemplateManager(templates_dir=tdir)
        mgr.save_template("rust", {"domain": "rust"}, "extension")
        assert (tdir / "domains" / "rust.extension.yaml").exists()
