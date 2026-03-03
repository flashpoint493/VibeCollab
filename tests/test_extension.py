"""Tests for ExtensionProcessor."""


import pytest
import yaml

from vibecollab.core.extension import (
    Context,
    ExtensionProcessor,
    load_extension_from_file,
)


@pytest.fixture
def processor(tmp_path):
    return ExtensionProcessor(project_root=tmp_path)


@pytest.fixture
def sample_ext_data():
    return {
        "hooks": [
            {"trigger": "dialogue.start", "action": "inject_context",
             "context_id": "ctx1", "priority": 10},
            {"trigger": "dialogue.end", "action": "update_file",
             "condition": "files.exists('README.md')", "priority": 5},
        ],
        "contexts": {
            "ctx1": {
                "type": "template",
                "content": "Hello {name}!",
                "description": "Greeting",
            },
            "ctx2": {
                "type": "reference",
                "source": "docs/guide.md",
                "section": "Setup",
                "inline_if_short": True,
            },
            "ctx3": {
                "type": "file_list",
                "pattern": "*.py",
                "description": "Python files",
            },
            "ctx4": {
                "type": "computed",
                "from": "project.features",
            },
        },
        "additional_files": [{"path": "extra.md"}],
        "config": {"version": "1.0"},
    }


class TestLoadExtension:
    def test_load_hooks(self, processor, sample_ext_data):
        ext = processor.load_extension(sample_ext_data, "python")
        assert len(ext.hooks) == 2
        assert ext.hooks[0].trigger == "dialogue.start"
        assert ext.hooks[0].priority == 10

    def test_load_contexts(self, processor, sample_ext_data):
        ext = processor.load_extension(sample_ext_data, "python")
        assert "ctx1" in ext.contexts
        assert ext.contexts["ctx1"].type == "template"
        assert ext.contexts["ctx2"].type == "reference"

    def test_load_additional_files(self, processor, sample_ext_data):
        ext = processor.load_extension(sample_ext_data, "python")
        assert len(ext.additional_files) == 1

    def test_load_config(self, processor, sample_ext_data):
        ext = processor.load_extension(sample_ext_data, "python")
        assert ext.config["version"] == "1.0"


class TestLoadFromConfig:
    def test_loads_domain_extensions(self, processor, sample_ext_data):
        config = {"domain_extensions": {"python": sample_ext_data}}
        processor.load_from_config(config)
        assert "python" in processor.extensions

    def test_empty_domain(self, processor):
        config = {"domain_extensions": {"empty": None}}
        processor.load_from_config(config)
        assert "empty" not in processor.extensions

    def test_roles_override(self, processor, sample_ext_data):
        config = {
            "domain_extensions": {"python": sample_ext_data},
            "roles_override": [{"role": "dev"}],
        }
        processor.load_from_config(config)
        assert processor.extensions["python"].roles_override == [{"role": "dev"}]


class TestGetHooksForTrigger:
    def test_returns_matching_hooks(self, processor, sample_ext_data):
        processor.load_extension(sample_ext_data, "python")
        hooks = processor.get_hooks_for_trigger("dialogue.start")
        assert len(hooks) == 1
        assert hooks[0].context_id == "ctx1"

    def test_no_matching_hooks(self, processor, sample_ext_data):
        processor.load_extension(sample_ext_data, "python")
        hooks = processor.get_hooks_for_trigger("build.pre")
        assert hooks == []

    def test_sorted_by_priority(self, processor):
        ext_data = {
            "hooks": [
                {"trigger": "dialogue.start", "action": "inject_context", "priority": 1},
                {"trigger": "dialogue.start", "action": "inject_context", "priority": 10},
                {"trigger": "dialogue.start", "action": "inject_context", "priority": 5},
            ],
            "contexts": {},
        }
        processor.load_extension(ext_data, "test")
        hooks = processor.get_hooks_for_trigger("dialogue.start")
        assert [h.priority for h in hooks] == [10, 5, 1]


class TestEvaluateCondition:
    def test_no_condition(self, processor):
        assert processor.evaluate_condition(None, {}) is True

    def test_files_exists_true(self, processor, tmp_path):
        (tmp_path / "README.md").touch()
        assert processor.evaluate_condition("files.exists('README.md')", {}) is True

    def test_files_exists_false(self, processor):
        assert processor.evaluate_condition("files.exists('nope.md')", {}) is False

    def test_project_has_feature_true(self, processor):
        processor._project_config = {"project": {"features": ["auth", "api"]}}
        assert processor.evaluate_condition("project.has_feature('auth')", {}) is True

    def test_project_has_feature_false(self, processor):
        processor._project_config = {"project": {"features": ["api"]}}
        assert processor.evaluate_condition("project.has_feature('auth')", {}) is False

    def test_project_domain_match(self, processor):
        processor._project_config = {"project": {"domain": "web"}}
        assert processor.evaluate_condition("project.domain == 'web'", {}) is True

    def test_project_domain_no_match(self, processor):
        processor._project_config = {"project": {"domain": "mobile"}}
        assert processor.evaluate_condition("project.domain == 'web'", {}) is False

    def test_topic_relates_to(self, processor):
        assert processor.evaluate_condition(
            "topic.relates_to('database')", {"topic": "Database migration"}
        ) is True

    def test_topic_relates_to_no_match(self, processor):
        assert processor.evaluate_condition(
            "topic.relates_to('database')", {"topic": "UI design"}
        ) is False

    def test_unknown_condition(self, processor):
        assert processor.evaluate_condition("unknown.thing()", {}) is True


class TestResolveContext:
    def test_resolve_template(self, processor):
        ctx = Context(id="t", type="template", content="Hi {name}!")
        result = processor.resolve_context(ctx, {"name": "World"})
        assert result == "Hi World!"

    def test_resolve_template_empty(self, processor):
        ctx = Context(id="t", type="template", content=None)
        assert processor.resolve_context(ctx, {}) == ""

    def test_resolve_reference_file_exists(self, processor, tmp_path):
        (tmp_path / "doc.md").write_text("short content", encoding="utf-8")
        ctx = Context(id="r", type="reference", source="doc.md")
        result = processor.resolve_context(ctx, {})
        assert "short content" in result

    def test_resolve_reference_file_missing(self, processor):
        ctx = Context(id="r", type="reference", source="missing.md")
        result = processor.resolve_context(ctx, {})
        assert "not found" in result  # referenced file not found

    def test_resolve_reference_no_source(self, processor):
        ctx = Context(id="r", type="reference", source=None)
        assert processor.resolve_context(ctx, {}) == ""

    def test_resolve_reference_long_content(self, processor, tmp_path):
        (tmp_path / "long.md").write_text("x" * 600, encoding="utf-8")
        ctx = Context(id="r", type="reference", source="long.md", inline_if_short=True)
        result = processor.resolve_context(ctx, {})
        assert "See" in result  # should show reference link, not inline

    def test_resolve_reference_with_section(self, processor, tmp_path):
        content = "# Top\n## Setup\nsetup text\n## Other\nother text"
        (tmp_path / "guide.md").write_text(content, encoding="utf-8")
        ctx = Context(id="r", type="reference", source="guide.md", section="Setup")
        result = processor.resolve_context(ctx, {})
        assert "setup text" in result

    def test_resolve_file_list(self, processor, tmp_path):
        (tmp_path / "a.py").touch()
        (tmp_path / "b.py").touch()
        ctx = Context(id="f", type="file_list", pattern="*.py", description="Python files")
        result = processor.resolve_context(ctx, {})
        assert "Python files" in result
        assert "a.py" in result

    def test_resolve_file_list_no_matches(self, processor):
        ctx = Context(id="f", type="file_list", pattern="*.xyz")
        result = processor.resolve_context(ctx, {})
        assert "No files matching" in result

    def test_resolve_file_list_no_pattern(self, processor):
        ctx = Context(id="f", type="file_list", pattern=None)
        assert processor.resolve_context(ctx, {}) == ""

    def test_resolve_computed_list(self, processor):
        processor._project_config = {"project": {"features": ["auth", "api"]}}
        ctx = Context(id="c", type="computed", from_path="project.features")
        result = processor.resolve_context(ctx, {})
        assert "auth" in result
        assert "api" in result

    def test_resolve_computed_string(self, processor):
        processor._project_config = {"project": {"name": "Test"}}
        ctx = Context(id="c", type="computed", from_path="project.name")
        result = processor.resolve_context(ctx, {})
        assert result == "Test"

    def test_resolve_computed_no_path(self, processor):
        ctx = Context(id="c", type="computed", from_path=None)
        assert processor.resolve_context(ctx, {}) == ""

    def test_resolve_computed_missing_path(self, processor):
        processor._project_config = {}
        ctx = Context(id="c", type="computed", from_path="a.b.c")
        assert processor.resolve_context(ctx, {}) == ""

    def test_resolve_unknown_type(self, processor):
        ctx = Context(id="u", type="unknown")
        assert processor.resolve_context(ctx, {}) == ""


class TestProcessTrigger:
    def test_injects_context(self, processor, sample_ext_data, tmp_path):
        processor.load_extension(sample_ext_data, "python")
        results = processor.process_trigger(
            "dialogue.start", variables={"name": "Alice"}
        )
        assert len(results) == 1
        assert results[0]["content"] == "Hello Alice!"
        assert results[0]["source"] == "python"

    def test_condition_prevents_execution(self, processor, sample_ext_data):
        processor.load_extension(sample_ext_data, "python")
        # dialogue.end has condition files.exists('README.md') — file doesn't exist
        results = processor.process_trigger("dialogue.end")
        assert len(results) == 0

    def test_no_hooks_returns_empty(self, processor, sample_ext_data):
        processor.load_extension(sample_ext_data, "python")
        results = processor.process_trigger("build.pre")
        assert results == []


class TestGenerateExtensionSection:
    def test_generates_content(self, processor, sample_ext_data):
        processor.load_extension(sample_ext_data, "python")
        section = processor.generate_extension_section("python")
        assert "PYTHON" in section
        assert "dialogue.start" in section
        assert "ctx1" in section
        assert "Greeting" in section

    def test_unknown_domain_returns_empty(self, processor):
        assert processor.generate_extension_section("unknown") == ""


class TestLoadExtensionFromFile:
    def test_load_yaml_file(self, tmp_path):
        data = {
            "domain_extensions": {
                "web": {
                    "hooks": [{"trigger": "dialogue.start", "action": "inject_context"}],
                    "contexts": {"c1": {"type": "template", "content": "hi"}},
                }
            }
        }
        path = tmp_path / "ext.yaml"
        path.write_text(yaml.dump(data), encoding="utf-8")

        proc = load_extension_from_file(path, project_root=tmp_path)
        assert "web" in proc.extensions
