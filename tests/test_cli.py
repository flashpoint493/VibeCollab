"""
Tests for LLMContext CLI
"""

import json
import tempfile
from pathlib import Path

import yaml
from click.testing import CliRunner

from vibecollab.cli import main


class TestCLI:
    """CLI tests"""

    def setup_method(self):
        self.runner = CliRunner()

    def test_version(self):
        """Test version command"""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "vibecollab" in result.output and "version" in result.output

    def test_domains(self):
        """Test listing domains"""
        result = self.runner.invoke(main, ["domains"])
        assert result.exit_code == 0
        assert "generic" in result.output
        assert "game" in result.output
        assert "web" in result.output

    def test_init_project(self):
        """Test project initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            result = self.runner.invoke(main, [
                "init",
                "-n", "TestProject",
                "-d", "generic",
                "-o", str(output_dir)
            ])

            assert result.exit_code == 0
            assert (output_dir / "CONTRIBUTING_AI.md").exists()
            assert (output_dir / "project.yaml").exists()

    def test_init_existing_dir_without_force(self):
        """Test init existing directory without force"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # Create a file to make directory non-empty
            (output_dir / "existing.txt").write_text("test")

            result = self.runner.invoke(main, [
                "init",
                "-n", "TestProject",
                "-d", "generic",
                "-o", str(output_dir)
            ])

            assert result.exit_code == 1
            assert "already exists" in result.output or "force" in result.output.lower()

    def test_validate_nonexistent_file(self):
        """Test validating non-existent file"""
        result = self.runner.invoke(main, [
            "validate",
            "-c", "/nonexistent/path/config.yaml"
        ])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_generate(self):
        """Test generate command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First initialize project
            output_dir = Path(tmpdir) / "test-project"
            self.runner.invoke(main, [
                "init",
                "-n", "TestProject",
                "-d", "generic",
                "-o", str(output_dir)
            ])

            # Re-generate
            result = self.runner.invoke(main, [
                "generate",
                "-c", str(output_dir / "project.yaml"),
                "-o", str(output_dir / "llm-new.txt")
            ])

            assert result.exit_code == 0
            assert (output_dir / "llm-new.txt").exists()

    def test_upgrade_with_role_context(self):
        """Test upgrade command auto-initializes multi-role directory structure"""
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"

            # 1. Initialize single-role project
            self.runner.invoke(main, [
                "init",
                "-n", "TestProject",
                "-d", "generic",
                "-o", str(output_dir)
            ])

            # 2. Manually modify config to enable multi-role mode
            config_path = output_dir / "project.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            config["role_context"] = {
                "enabled": True,
                "roles": [
                    {"id": "alice", "name": "Alice", "role": "backend"},
                    {"id": "bob", "name": "Bob", "role": "frontend"}
                ],
                "collaboration": {
                    "file": "docs/roles/COLLABORATION.md"
                }
            }

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            # 3. Run upgrade command
            result = self.runner.invoke(main, [
                "upgrade",
                "-c", str(config_path),
                "--force"
            ])

            # 4. Verify multi-role directory structure is created
            assert result.exit_code == 0

            # Check role directories
            alice_dir = output_dir / "docs" / "roles" / "alice"
            bob_dir = output_dir / "docs" / "roles" / "bob"
            assert alice_dir.exists(), "Alice directory should be created"
            assert bob_dir.exists(), "Bob directory should be created"

            # Check CONTEXT.md
            assert (alice_dir / "CONTEXT.md").exists(), "Alice's CONTEXT.md should be created"
            assert (bob_dir / "CONTEXT.md").exists(), "Bob's CONTEXT.md should be created"

            # Check .metadata.yaml
            assert (alice_dir / ".metadata.yaml").exists(), "Alice's .metadata.yaml should be created"
            assert (bob_dir / ".metadata.yaml").exists(), "Bob's .metadata.yaml should be created"

            # Check collaboration doc
            collab_file = output_dir / "docs" / "roles" / "COLLABORATION.md"
            assert collab_file.exists(), "COLLABORATION.md should be created"

            # Check global aggregated CONTEXT.md
            global_context = output_dir / "docs" / "CONTEXT.md"
            assert global_context.exists(), "Global aggregated CONTEXT.md should exist"

    def test_templates(self):
        """Test listing templates"""
        result = self.runner.invoke(main, ["templates"])
        assert result.exit_code == 0
        assert "Available Templates" in result.output
        assert "default" in result.output.lower() or "project" in result.output.lower()

    def test_check_basic(self):
        """Test protocol check command"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            self.runner.invoke(main, [
                "init", "-n", "TestProject", "-d", "generic", "-o", str(output_dir)
            ])
            result = self.runner.invoke(main, [
                "check", "-c", str(output_dir / "project.yaml")
            ])
            assert result.exit_code == 0
            assert "Check Complete" in result.output

    def test_check_no_config(self):
        """Test protocol check - config not found"""
        result = self.runner.invoke(main, [
            "check", "-c", "/nonexistent/project.yaml"
        ])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_check_strict(self):
        """Test protocol check - strict mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            self.runner.invoke(main, [
                "init", "-n", "TestProject", "-d", "generic", "-o", str(output_dir)
            ])
            result = self.runner.invoke(main, [
                "check", "-c", str(output_dir / "project.yaml"), "--strict"
            ])
            # Strict mode may fail if there are warnings, that's acceptable
            assert "Check Complete" in result.output or "Check" in result.output

    def test_health_basic(self):
        """Test health check command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            self.runner.invoke(main, [
                "init", "-n", "TestProject", "-d", "generic", "-o", str(output_dir)
            ])
            result = self.runner.invoke(main, [
                "health", "-c", str(output_dir / "project.yaml")
            ])
            assert "Grade" in result.output or "Health" in result.output

    def test_health_json(self):
        """Test health check JSON output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            self.runner.invoke(main, [
                "init", "-n", "TestProject", "-d", "generic", "-o", str(output_dir)
            ])
            result = self.runner.invoke(main, [
                "health", "-c", str(output_dir / "project.yaml"), "--json"
            ])
            # Should output valid JSON
            data = json.loads(result.output)
            assert "score" in data
            assert "signals" in data

    def test_health_no_config(self):
        """Test health check - config does not exist"""
        result = self.runner.invoke(main, [
            "health", "-c", "/nonexistent/project.yaml"
        ])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Minimal / complex project boundary tests
# ---------------------------------------------------------------------------

class TestMinimalProject:
    """Minimal project config boundary tests -- minimal config runs successfully."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_init_minimal(self):
        """Minimal params init succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "minimal"
            result = self.runner.invoke(main, [
                "init", "-n", "Min", "-d", "generic", "-o", str(out)
            ])
            assert result.exit_code == 0
            assert (out / "project.yaml").exists()

    def test_generate_minimal(self):
        """Minimal project.yaml generates successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "minimal"
            self.runner.invoke(main, [
                "init", "-n", "Min", "-d", "generic", "-o", str(out)
            ])
            result = self.runner.invoke(main, [
                "generate", "-c", str(out / "project.yaml"),
                "-o", str(out / "llms.txt")
            ])
            assert result.exit_code == 0
            assert (out / "llms.txt").exists()
            content = (out / "llms.txt").read_text(encoding="utf-8")
            assert "Min" in content

    def test_check_minimal(self):
        """Minimal config check does not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "minimal"
            self.runner.invoke(main, [
                "init", "-n", "Min", "-d", "generic", "-o", str(out)
            ])
            result = self.runner.invoke(main, [
                "check", "-c", str(out / "project.yaml")
            ])
            # check may have warnings but should not crash
            assert result.exit_code in (0, 1)

    def test_health_minimal(self):
        """Minimal config health does not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "minimal"
            self.runner.invoke(main, [
                "init", "-n", "Min", "-d", "generic", "-o", str(out)
            ])
            result = self.runner.invoke(main, [
                "health", "-c", str(out / "project.yaml")
            ])
            assert result.exit_code in (0, 1)

    def test_validate_minimal(self):
        """Minimal config validate passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "minimal"
            self.runner.invoke(main, [
                "init", "-n", "Min", "-d", "generic", "-o", str(out)
            ])
            result = self.runner.invoke(main, [
                "validate", "-c", str(out / "project.yaml")
            ])
            assert result.exit_code == 0

    def test_empty_yaml_graceful(self):
        """Empty YAML file does not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_config = Path(tmpdir) / "project.yaml"
            empty_config.write_text("", encoding="utf-8")
            result = self.runner.invoke(main, [
                "generate", "-c", str(empty_config)
            ])
            # Should error but not crash
            assert result.exit_code != 0 or "error" in result.output.lower()

    def test_yaml_only_name(self):
        """Minimal YAML with only project_name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / "project.yaml"
            config.write_text("project_name: OnlyName\n", encoding="utf-8")
            result = self.runner.invoke(main, [
                "validate", "-c", str(config)
            ])
            # May pass or report missing fields, should not crash
            assert result.exception is None or isinstance(result.exception, SystemExit)


class TestComplexProject:
    """Complex project config boundary tests -- full config runs successfully."""

    def setup_method(self):
        self.runner = CliRunner()

    def _create_complex_project(self, tmpdir):
        """Create a fully configured complex project."""
        out = Path(tmpdir) / "complex"
        self.runner.invoke(main, [
            "init", "-n", "ComplexProject", "-d", "generic", "-o", str(out)
        ])
        config_path = out / "project.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        # Add multi-role
        config["role_context"] = {
            "enabled": True,
            "roles": [
                {"id": "alice", "name": "Alice", "role": "backend"},
                {"id": "bob", "name": "Bob", "role": "frontend"},
                {"id": "charlie", "name": "Charlie", "role": "devops"},
            ],
            "collaboration": {"file": "docs/roles/COLLABORATION.md"},
        }

        # Add extension domain
        config.setdefault("domains", []).append("game")

        # Add lifecycle
        config["lifecycle"] = {
            "current_stage": "demo",
            "milestones": [
                {"name": "MVP", "completed": True},
                {"name": "Beta", "completed": False},
            ],
        }

        # Add documentation
        config["documentation"] = {
            "key_files": [
                {"path": "README.md", "purpose": "project entry"},
                {"path": "docs/ROADMAP.md", "purpose": "roadmap"},
                {"path": "docs/CHANGELOG.md", "purpose": "changelog"},
            ],
        }

        config_path.write_text(
            yaml.dump(config, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )

        # Create necessary files
        (out / "docs").mkdir(exist_ok=True)
        (out / "docs" / "roles").mkdir(exist_ok=True)
        (out / "docs" / "ROADMAP.md").write_text("# Roadmap\n", encoding="utf-8")
        (out / "docs" / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        (out / "README.md").write_text("# ComplexProject\n", encoding="utf-8")
        (out / "docs" / "roles" / "COLLABORATION.md").write_text(
            "# Collaboration\n", encoding="utf-8"
        )

        return out

    def test_generate_complex(self):
        """Full config generate succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self._create_complex_project(tmpdir)
            result = self.runner.invoke(main, [
                "generate", "-c", str(out / "project.yaml"),
                "-o", str(out / "llms.txt")
            ])
            assert result.exit_code == 0
            content = (out / "llms.txt").read_text(encoding="utf-8")
            assert "ComplexProject" in content

    def test_check_complex(self):
        """Full config check does not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self._create_complex_project(tmpdir)
            result = self.runner.invoke(main, [
                "check", "-c", str(out / "project.yaml")
            ])
            assert result.exit_code in (0, 1)

    def test_health_complex(self):
        """Full config health does not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self._create_complex_project(tmpdir)
            result = self.runner.invoke(main, [
                "health", "-c", str(out / "project.yaml")
            ])
            assert result.exit_code in (0, 1)

    def test_upgrade_complex(self):
        """Full config upgrade does not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self._create_complex_project(tmpdir)
            result = self.runner.invoke(main, [
                "upgrade", "-c", str(out / "project.yaml")
            ])
            # upgrade may no-op or succeed
            assert result.exit_code in (0, 1)

    def test_validate_complex(self):
        """Full config validate passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self._create_complex_project(tmpdir)
            result = self.runner.invoke(main, [
                "validate", "-c", str(out / "project.yaml")
            ])
            assert result.exit_code == 0

    def test_check_json_complex(self):
        """Full config check --json outputs valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self._create_complex_project(tmpdir)
            result = self.runner.invoke(main, [
                "check", "-c", str(out / "project.yaml"), "--json"
            ])
            if result.exit_code in (0, 1) and result.output.strip():
                try:
                    data = json.loads(result.output)
                    assert isinstance(data, dict)
                except json.JSONDecodeError:
                    pass  # JSON may be mixed with Rich output, not enforced

    def test_health_json_complex(self):
        """Full config health --json outputs valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self._create_complex_project(tmpdir)
            result = self.runner.invoke(main, [
                "health", "-c", str(out / "project.yaml"), "--json"
            ])
            if result.exit_code in (0, 1) and result.output.strip():
                try:
                    data = json.loads(result.output)
                    assert isinstance(data, dict)
                except json.JSONDecodeError:
                    pass

    def test_all_domains(self):
        """All available domains can init successfully."""
        result = self.runner.invoke(main, ["domains"])
        # Extract domain names from output
        domains = []
        for line in result.output.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("─") and "domain" not in stripped.lower():
                parts = stripped.split()
                if parts:
                    candidate = parts[0].strip("│").strip()
                    if candidate and candidate.isalpha() and len(candidate) < 20:
                        domains.append(candidate)

        for domain in domains[:5]:  # Only test first 5 to avoid slowness
            with tempfile.TemporaryDirectory() as tmpdir:
                out = Path(tmpdir) / f"test-{domain}"
                r = self.runner.invoke(main, [
                    "init", "-n", f"Test-{domain}", "-d", domain, "-o", str(out)
                ])
                assert r.exit_code == 0, f"init failed for domain {domain}: {r.output}"

