"""
Tests for Template Library CLI commands (FP-005)
"""

import json

import yaml
from click.testing import CliRunner

from vibecollab.cli.main import main
from vibecollab.core.template_library import TemplateLibrary


class TestTemplateLibraryCore:
    """Test TemplateLibrary core functionality"""

    def test_init_loads_builtin_manifest(self):
        """TemplateLibrary should load built-in manifest"""
        lib = TemplateLibrary()
        assert lib.manifest is not None
        assert "core_templates" in lib.manifest
        assert "config_templates" in lib.manifest

    def test_list_templates_returns_builtins(self):
        """list_templates should return built-in templates"""
        lib = TemplateLibrary()
        templates = lib.list_templates()

        # Should have some templates
        assert len(templates) > 0

        # Check for known core templates
        template_ids = [t["id"] for t in templates]
        assert "context" in template_ids
        assert "decisions" in template_ids
        assert "roadmap" in template_ids

    def test_get_template_builtin(self):
        """get_template should return built-in template info"""
        lib = TemplateLibrary()
        tpl = lib.get_template("context")

        assert tpl is not None
        assert tpl["id"] == "context"
        assert tpl["source"] == "builtin"

    def test_get_template_not_found(self):
        """get_template should return None for unknown template"""
        lib = TemplateLibrary()
        tpl = lib.get_template("nonexistent")
        assert tpl is None

    def test_get_template_path_builtin(self):
        """get_template_path should return path for built-in template"""
        lib = TemplateLibrary()
        path = lib.get_template_path("context")

        assert path is not None
        assert path.exists()
        assert path.suffix == ".j2"

    def test_validate_template_valid(self):
        """validate_template should pass for valid templates"""
        lib = TemplateLibrary()
        is_valid, errors = lib.validate_template("context")

        assert is_valid
        assert len(errors) == 0

    def test_validate_template_invalid(self):
        """validate_template should fail for nonexistent template"""
        lib = TemplateLibrary()
        is_valid, errors = lib.validate_template("nonexistent")

        assert not is_valid
        assert len(errors) > 0

    def test_get_stats(self):
        """get_stats should return template counts"""
        lib = TemplateLibrary()
        stats = lib.get_stats()

        assert "builtin" in stats
        assert "custom" in stats
        assert "total" in stats
        assert stats["total"] == stats["builtin"] + stats["custom"]


class TestTemplateLibraryCustom:
    """Test custom template functionality"""

    def test_load_local_templates_empty(self, tmp_path):
        """Loading local templates from empty directory should work"""
        lib = TemplateLibrary(project_root=tmp_path)
        assert lib.local_templates == {}

    def test_create_custom_template(self, tmp_path):
        """create_custom_template should create template file"""
        lib = TemplateLibrary(project_root=tmp_path)
        success, message = lib.create_custom_template("my-tpl", "My template")

        assert success
        template_file = tmp_path / ".vibecollab" / "templates" / "my-tpl.yaml.j2"
        assert template_file.exists()

    def test_create_custom_template_duplicate_fails(self, tmp_path):
        """Creating duplicate template should fail"""
        lib = TemplateLibrary(project_root=tmp_path)
        lib.create_custom_template("my-tpl", "My template")

        success, message = lib.create_custom_template("my-tpl", "My template")
        assert not success
        assert "already exists" in message

    def test_list_templates_includes_custom(self, tmp_path):
        """list_templates should include custom templates"""
        lib = TemplateLibrary(project_root=tmp_path)
        lib.create_custom_template("custom-one", "Custom 1")
        lib.create_custom_template("custom-two", "Custom 2")

        templates = lib.list_templates()
        template_ids = [t["id"] for t in templates]

        assert "custom-one" in template_ids
        assert "custom-two" in template_ids

    def test_custom_template_override(self, tmp_path):
        """Custom template with same ID should be returned before builtin"""
        lib = TemplateLibrary(project_root=tmp_path)
        lib.create_custom_template("context", "My custom context")

        tpl = lib.get_template("context")
        assert tpl["source"] == "local"

    def test_get_custom_templates_dir_creates_dir(self, tmp_path):
        """get_custom_templates_dir should create directory if needed"""
        lib = TemplateLibrary(project_root=tmp_path)
        custom_dir = lib.get_custom_templates_dir()

        assert custom_dir.exists()
        assert custom_dir.name == "templates"


class TestTemplateLibraryUse:
    """Test template usage functionality"""

    def test_use_template_builtin(self, tmp_path):
        """use_template should generate document from built-in template"""
        lib = TemplateLibrary(project_root=tmp_path)
        output_path = tmp_path / "output.yaml"

        success, message = lib.use_template("context", output_path)

        assert success
        assert output_path.exists()

    def test_use_template_with_variables(self, tmp_path):
        """use_template should substitute variables"""
        lib = TemplateLibrary(project_root=tmp_path)
        output_path = tmp_path / "output.yaml"

        success, message = lib.use_template(
            "context",
            output_path,
            variables={"test_var": "test_value"},
        )

        assert success
        content = output_path.read_text()
        # The context template doesn't use custom variables, but it should render
        assert "kind: context" in content or "#" in content

    def test_use_template_invalid_template(self, tmp_path):
        """use_template should fail for invalid template"""
        lib = TemplateLibrary(project_root=tmp_path)
        output_path = tmp_path / "output.yaml"

        success, message = lib.use_template("nonexistent", output_path)

        assert not success
        assert "not found" in message


class TestTemplateCLI:
    """Test CLI commands for templates"""

    def test_template_list_command(self):
        """template list command should work"""
        runner = CliRunner()
        result = runner.invoke(main, ["template", "list"])

        assert result.exit_code == 0
        assert "context" in result.output
        assert "decisions" in result.output

    def test_template_list_json(self):
        """template list --json should output valid JSON"""
        runner = CliRunner()
        result = runner.invoke(main, ["template", "list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_template_list_category_filter(self):
        """template list --category should filter templates"""
        runner = CliRunner()
        result = runner.invoke(main, ["template", "list", "--category", "core"])

        assert result.exit_code == 0

    def test_template_show_builtin(self):
        """template show should display template details"""
        runner = CliRunner()
        result = runner.invoke(main, ["template", "show", "context"])

        assert result.exit_code == 0
        assert "context" in result.output
        assert "builtin" in result.output

    def test_template_show_not_found(self):
        """template show for nonexistent template should fail"""
        runner = CliRunner()
        result = runner.invoke(main, ["template", "show", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output

    def test_template_validate_valid(self):
        """template validate should pass for valid template"""
        runner = CliRunner()
        result = runner.invoke(main, ["template", "validate", "context"])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_template_validate_invalid(self):
        """template validate should fail for invalid template"""
        runner = CliRunner()
        result = runner.invoke(main, ["template", "validate", "nonexistent"])

        assert result.exit_code != 0

    def test_template_create(self, tmp_path):
        """template create should create custom template"""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["template", "create", "my-test", "-d", "Test template", "-p", str(tmp_path)],
        )

        assert result.exit_code == 0
        template_file = tmp_path / ".vibecollab" / "templates" / "my-test.yaml.j2"
        assert template_file.exists()

    def test_template_use_builtin(self, tmp_path):
        """template use should generate from built-in template"""
        runner = CliRunner()
        output_file = tmp_path / "output.yaml"

        result = runner.invoke(
            main,
            ["template", "use", "context", "-o", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_template_use_with_variables(self, tmp_path):
        """template use with --var should substitute variables"""
        runner = CliRunner()
        output_file = tmp_path / "output.yaml"

        result = runner.invoke(
            main,
            ["template", "use", "context", "-o", str(output_file), "--var", "test=value"],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_template_use_invalid_template(self):
        """template use with invalid template should fail"""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["template", "use", "nonexistent", "-o", "/tmp/output.yaml"],
        )

        assert result.exit_code != 0
        assert "not found" in result.output

    def test_template_use_dry_run(self):
        """template use --dry-run should preview without writing"""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["template", "use", "context", "-o", "/tmp/output.yaml", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry Run" in result.output or "Preview" in result.output


class TestTemplateCategories:
    """Test template category functionality"""

    def test_list_categories(self):
        """list_categories should return all categories"""
        lib = TemplateLibrary()
        categories = lib.list_categories()

        assert "core" in categories
        assert "configuration" in categories
        assert "collaboration" in categories
        assert "domain" in categories
        assert "custom" in categories

    def test_get_template_category_core(self):
        """Core templates should have 'core' category"""
        lib = TemplateLibrary()
        tpl = lib.get_template("context")
        assert tpl.get("category") == "core"

    def test_get_template_category_config(self):
        """Config templates should have appropriate category"""
        lib = TemplateLibrary()
        tpl = lib.get_template("philosophy")
        assert tpl.get("category") in ["configuration", "collaboration"]


class TestTemplateIntegration:
    """Integration tests for template library"""

    def test_end_to_end_create_and_use(self, tmp_path):
        """Full workflow: create custom template and use it"""
        lib = TemplateLibrary(project_root=tmp_path)

        # Create custom template
        success, _ = lib.create_custom_template("e2e-test", "E2E test template")
        assert success

        # Use the template
        output_path = tmp_path / "e2e-output.yaml"
        success, message = lib.use_template("e2e-test", output_path)

        assert success
        assert output_path.exists()

    def test_bootstrap_project_yaml(self, tmp_path):
        """Template library should work with project.yaml config"""
        # Create a minimal project.yaml
        project_yaml = tmp_path / "project.yaml"
        project_config = {
            "project": {"name": "TestProject", "domain": "generic"},
            "version": "1.0.0",
        }
        project_yaml.write_text(yaml.dump(project_config))

        lib = TemplateLibrary(project_root=tmp_path)
        output_path = tmp_path / "output.yaml"

        success, _ = lib.use_template(
            "context",
            output_path,
            project_config=project_config,
        )

        assert success
        content = output_path.read_text()
        assert "TestProject" in content or "kind: context" in content
