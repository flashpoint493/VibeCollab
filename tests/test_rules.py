"""
VibeCollab rules inject CLI tests.

Covers: rules inject --ide cursor/codebuddy/all, --dry-run.
"""


from click.testing import CliRunner


class TestRulesInject:
    """Tests for vibecollab rules inject."""

    def test_rules_inject_help(self):
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(rules_group, ["inject", "--help"])
        assert result.exit_code == 0
        assert "cursor" in result.output
        assert "codebuddy" in result.output
        assert "dry-run" in result.output

    def test_rules_inject_dry_run_cursor(self, tmp_path):
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group,
            ["inject", "--ide", "cursor", "-p", str(tmp_path), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "dry-run" in result.output
        assert "vibecollab.mdc" in result.output and ".cursor" in result.output
        assert not (tmp_path / ".cursor" / "rules" / "vibecollab.mdc").exists()

    def test_rules_inject_dry_run_all(self, tmp_path):
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group,
            ["inject", "--ide", "all", "-p", str(tmp_path), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "vibecollab.mdc" in result.output and "vibecollab-protocol.mdc" in result.output
        assert not (tmp_path / ".cursor" / "rules" / "vibecollab.mdc").exists()
        assert not (tmp_path / ".codebuddy" / "rules" / "vibecollab-protocol.mdc").exists()

    def test_rules_inject_cursor(self, tmp_path):
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group, ["inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Injected" in result.output or "已注入" in result.output

        path = tmp_path / ".cursor" / "rules" / "vibecollab.mdc"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "alwaysApply: true" in text
        assert "VibeCollab" in text
        assert "CONTRIBUTING_AI.md" in text
        assert "docs/CONTEXT.md" in text

    def test_rules_inject_codebuddy(self, tmp_path):
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group, ["inject", "--ide", "codebuddy", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0

        path = tmp_path / ".codebuddy" / "rules" / "vibecollab-protocol.mdc"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "VibeCollab" in text
        assert "CONTRIBUTING_AI.md" in text
        assert "Context recovery" in text

    def test_rules_inject_all(self, tmp_path):
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group, ["inject", "--ide", "all", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / ".cursor" / "rules" / "vibecollab.mdc").exists()
        assert (tmp_path / ".clinerules" / "vibecollab.md").exists()
        assert (
            tmp_path / ".codebuddy" / "rules" / "vibecollab-protocol.mdc"
        ).exists()
        assert (tmp_path / ".cursor" / "skills" / "vibecollab" / "SKILL.md").exists()

    def test_rules_inject_windsurf(self, tmp_path):
        """Extra platforms (e.g. windsurf) get rules and skills."""
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group, ["inject", "--ide", "windsurf", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / ".windsurfrules").exists()
        assert "VibeCollab" in (tmp_path / ".windsurfrules").read_text(encoding="utf-8")
        assert (tmp_path / ".windsurf" / "skills" / "vibecollab" / "SKILL.md").exists()

    def test_rules_inject_kiro(self, tmp_path):
        """vx-aligned platform kiro gets rules + skills (see github.com/loonghao/vx)."""
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group, ["inject", "--ide", "kiro", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / ".kiro" / "rules" / "vibecollab.md").exists()
        assert "VibeCollab" in (
            tmp_path / ".kiro" / "rules" / "vibecollab.md"
        ).read_text(encoding="utf-8")
        assert (tmp_path / ".kiro" / "skills" / "vibecollab" / "SKILL.md").exists()

    def test_rules_inject_trae(self, tmp_path):
        """vx-aligned platform trae gets rules + skills."""
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group, ["inject", "--ide", "trae", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / ".trae" / "rules" / "vibecollab.md").exists()
        assert (tmp_path / ".trae" / "skills" / "vibecollab" / "SKILL.md").exists()

    def test_rules_inject_schema_driven(self, tmp_path):
        """When project.yaml exists, rule body is generated from schema (same as README/context)."""
        import yaml

        (tmp_path / "project.yaml").write_text(
            yaml.dump({
                "project": {"name": "TestProject", "version": "v1.0.0"},
                "documentation": {
                    "context_file": "docs/CONTEXT.md",
                    "decisions_file": "docs/DECISIONS.md",
                    "changelog_file": "docs/CHANGELOG.md",
                    "key_files": [
                        {"path": "CONTRIBUTING_AI.md", "purpose": "AI rules"},
                        {"path": "docs/CONTEXT.md", "purpose": "Context"},
                    ],
                },
            }),
            encoding="utf-8",
        )
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group, ["inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        text = (tmp_path / ".cursor" / "rules" / "vibecollab.mdc").read_text(
            encoding="utf-8"
        )
        assert "TestProject protocol" in text
        assert "docs/CONTEXT.md" in text
        assert "docs/DECISIONS.md" in text


class TestRulesIntegration:
    """Integration: rules command registered on main CLI."""

    def test_vibecollab_rules_registered(self):
        from vibecollab.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["rules", "--help"])
        assert result.exit_code == 0
        assert "inject" in result.output
        assert "cline" in result.output.lower()

    def test_rules_inject_cline(self, tmp_path):
        from vibecollab.cli_rules import rules_group

        runner = CliRunner()
        result = runner.invoke(
            rules_group, ["inject", "--ide", "cline", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        path = tmp_path / ".clinerules" / "vibecollab.md"
        assert path.exists()
        assert "VibeCollab" in path.read_text(encoding="utf-8")

    def test_main_rules_inject_cursor(self, tmp_path):
        from vibecollab.cli import main

        runner = CliRunner()
        result = runner.invoke(
            main, ["rules", "inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / ".cursor" / "rules" / "vibecollab.mdc").exists()

    def test_setup_all(self, tmp_path):
        """setup --ide all injects MCP + rules for cursor, cline, codebuddy."""
        from vibecollab.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["setup", "--ide", "all", "-p", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / ".cursor" / "mcp.json").exists()
        assert (tmp_path / ".cline" / "mcp_settings.json").exists()
        assert (tmp_path / ".codebuddy" / "mcp.json").exists()
        assert (tmp_path / ".cursor" / "rules" / "vibecollab.mdc").exists()
        assert (tmp_path / ".clinerules" / "vibecollab.md").exists()
        assert (
            tmp_path / ".codebuddy" / "rules" / "vibecollab-protocol.mdc"
        ).exists()
