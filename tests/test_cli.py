"""
Tests for LLMTxt CLI
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile

from llmtxt.cli import main


class TestCLI:
    """CLI 测试"""

    def setup_method(self):
        self.runner = CliRunner()

    def test_version(self):
        """测试版本命令"""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

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
            assert (output_dir / "llm.txt").exists()
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
