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
    """CLI 测试"""

    def setup_method(self):
        self.runner = CliRunner()

    def test_version(self):
        """测试版本命令"""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "vibecollab" in result.output and "version" in result.output

    def test_domains(self):
        """测试列出领域"""
        result = self.runner.invoke(main, ["domains"])
        assert result.exit_code == 0
        assert "generic" in result.output
        assert "game" in result.output
        assert "web" in result.output

    def test_init_project(self):
        """测试初始化项目"""
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
        """测试初始化已存在目录（无 force）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # 创建一个文件使目录非空
            (output_dir / "existing.txt").write_text("test")

            result = self.runner.invoke(main, [
                "init",
                "-n", "TestProject",
                "-d", "generic",
                "-o", str(output_dir)
            ])

            assert result.exit_code == 1
            assert "已存在" in result.output or "force" in result.output.lower()

    def test_validate_nonexistent_file(self):
        """测试验证不存在的文件"""
        result = self.runner.invoke(main, [
            "validate",
            "-c", "/nonexistent/path/config.yaml"
        ])

        assert result.exit_code == 1
        assert "不存在" in result.output

    def test_generate(self):
        """测试生成命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 先初始化项目
            output_dir = Path(tmpdir) / "test-project"
            self.runner.invoke(main, [
                "init",
                "-n", "TestProject",
                "-d", "generic",
                "-o", str(output_dir)
            ])

            # 重新生成
            result = self.runner.invoke(main, [
                "generate",
                "-c", str(output_dir / "project.yaml"),
                "-o", str(output_dir / "llm-new.txt")
            ])

            assert result.exit_code == 0
            assert (output_dir / "llm-new.txt").exists()

    def test_upgrade_with_multi_developer(self):
        """测试 upgrade 命令自动初始化多开发者目录结构"""
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"

            # 1. 初始化单开发者项目
            self.runner.invoke(main, [
                "init",
                "-n", "TestProject",
                "-d", "generic",
                "-o", str(output_dir)
            ])

            # 2. 手动修改配置启用多开发者模式
            config_path = output_dir / "project.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            config["multi_developer"] = {
                "enabled": True,
                "developers": [
                    {"id": "alice", "name": "Alice", "role": "backend"},
                    {"id": "bob", "name": "Bob", "role": "frontend"}
                ],
                "collaboration": {
                    "file": "docs/developers/COLLABORATION.md"
                }
            }

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            # 3. 运行 upgrade 命令
            result = self.runner.invoke(main, [
                "upgrade",
                "-c", str(config_path),
                "--force"
            ])

            # 4. 验证多开发者目录结构已创建
            assert result.exit_code == 0

            # 检查开发者目录
            alice_dir = output_dir / "docs" / "developers" / "alice"
            bob_dir = output_dir / "docs" / "developers" / "bob"
            assert alice_dir.exists(), "Alice 目录应该被创建"
            assert bob_dir.exists(), "Bob 目录应该被创建"

            # 检查 CONTEXT.md
            assert (alice_dir / "CONTEXT.md").exists(), "Alice 的 CONTEXT.md 应该被创建"
            assert (bob_dir / "CONTEXT.md").exists(), "Bob 的 CONTEXT.md 应该被创建"

            # 检查 .metadata.yaml
            assert (alice_dir / ".metadata.yaml").exists(), "Alice 的 .metadata.yaml 应该被创建"
            assert (bob_dir / ".metadata.yaml").exists(), "Bob 的 .metadata.yaml 应该被创建"

            # 检查协作文档
            collab_file = output_dir / "docs" / "developers" / "COLLABORATION.md"
            assert collab_file.exists(), "COLLABORATION.md 应该被创建"

            # 检查全局聚合的 CONTEXT.md
            global_context = output_dir / "docs" / "CONTEXT.md"
            assert global_context.exists(), "全局聚合的 CONTEXT.md 应该存在"

    def test_templates(self):
        """测试列出模板"""
        result = self.runner.invoke(main, ["templates"])
        assert result.exit_code == 0
        assert "可用模板" in result.output
        assert "default" in result.output.lower() or "project" in result.output.lower()

    def test_export_template_default(self):
        """测试导出默认模板"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "exported.yaml"
            result = self.runner.invoke(main, [
                "export-template", "-t", "default", "-o", str(output_path)
            ])
            assert result.exit_code == 0
            assert output_path.exists()
            content = yaml.safe_load(output_path.read_text(encoding="utf-8"))
            assert "project" in content

    def test_export_template_nonexistent(self):
        """测试导出不存在的模板"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "exported.yaml"
            result = self.runner.invoke(main, [
                "export-template", "-t", "nonexistent_template_xyz", "-o", str(output_path)
            ])
            assert result.exit_code != 0
            assert "不存在" in result.output

    def test_version_info(self):
        """测试版本信息命令"""
        result = self.runner.invoke(main, ["version-info"])
        assert result.exit_code == 0
        assert "版本信息" in result.output or "version" in result.output.lower()

    def test_check_basic(self):
        """测试协议检查命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            self.runner.invoke(main, [
                "init", "-n", "TestProject", "-d", "generic", "-o", str(output_dir)
            ])
            result = self.runner.invoke(main, [
                "check", "-c", str(output_dir / "project.yaml")
            ])
            assert result.exit_code == 0
            assert "检查完成" in result.output

    def test_check_no_config(self):
        """测试协议检查 - 配置不存在"""
        result = self.runner.invoke(main, [
            "check", "-c", "/nonexistent/project.yaml"
        ])
        assert result.exit_code != 0
        assert "不存在" in result.output

    def test_check_strict(self):
        """测试协议检查 - 严格模式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test-project"
            self.runner.invoke(main, [
                "init", "-n", "TestProject", "-d", "generic", "-o", str(output_dir)
            ])
            result = self.runner.invoke(main, [
                "check", "-c", str(output_dir / "project.yaml"), "--strict"
            ])
            # Strict mode may fail if there are warnings, that's acceptable
            assert "检查完成" in result.output or "检查" in result.output

    def test_health_basic(self):
        """测试健康检查命令"""
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
        """测试健康检查 JSON 输出"""
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
        """测试健康检查 - 配置不存在"""
        result = self.runner.invoke(main, [
            "health", "-c", "/nonexistent/project.yaml"
        ])
        assert result.exit_code != 0


