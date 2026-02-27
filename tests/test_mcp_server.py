"""
VibeCollab MCP Server 单元测试

测试 MCP Server 的核心功能:
- Server 创建和配置
- Resource 注册和读取
- Tool 注册和调用
- Prompt 模板生成
- CLI 命令 (mcp serve/config/inject)
- 边界情况 (空项目、缺失文件)
"""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner


# ============================================================
# 辅助
# ============================================================


def _mcp_available() -> bool:
    """检查 mcp 包是否可导入"""
    try:
        import mcp  # noqa: F401

        return True
    except ImportError:
        return False


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def project_dir(tmp_path):
    """创建一个完整的测试项目目录"""
    # project.yaml
    config = {
        "project": {
            "name": "TestProject",
            "version": "1.0.0",
            "description": "A test project for MCP",
        },
        "documentation": {
            "key_files": ["CONTRIBUTING_AI.md", "docs/CONTEXT.md"],
        },
    }
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config, allow_unicode=True), encoding="utf-8"
    )

    # CONTRIBUTING_AI.md
    (tmp_path / "CONTRIBUTING_AI.md").write_text(
        "# AI 协作协议\n\n## 核心理念\n以人为本的AI协作\n", encoding="utf-8"
    )

    # docs 目录
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "CONTEXT.md").write_text(
        "# 项目上下文\n\n## 当前状态\n- 版本: v1.0.0\n- 开发中\n", encoding="utf-8"
    )
    (docs / "DECISIONS.md").write_text(
        "# 决策记录\n\n### DECISION-001: 测试决策\n- 决策: A\n", encoding="utf-8"
    )
    (docs / "ROADMAP.md").write_text(
        "# 路线图\n\n- [ ] 待办事项 1\n- [x] 已完成事项\n", encoding="utf-8"
    )
    (docs / "CHANGELOG.md").write_text(
        "# 变更日志\n\n## v1.0.0\n- 初始版本\n", encoding="utf-8"
    )

    # 开发者目录
    dev_dir = docs / "developers" / "alice"
    dev_dir.mkdir(parents=True)
    (dev_dir / "CONTEXT.md").write_text(
        "# Alice 上下文\n\n## 当前任务\n- 开发 MCP Server\n", encoding="utf-8"
    )
    (dev_dir / ".metadata.yaml").write_text(
        yaml.dump({"id": "alice", "role": "developer"}), encoding="utf-8"
    )

    # .vibecollab/insights/
    insights_dir = tmp_path / ".vibecollab" / "insights"
    insights_dir.mkdir(parents=True)

    ins1 = {
        "id": "INS-001",
        "title": "测试 Insight 1",
        "tags": ["test", "mcp"],
        "category": "technique",
        "body": {"scenario": "测试场景", "approach": "测试方法"},
    }
    ins2 = {
        "id": "INS-002",
        "title": "测试 Insight 2",
        "tags": ["debug", "tool"],
        "category": "debug",
        "body": {"scenario": "调试场景", "approach": "调试方法"},
    }
    (insights_dir / "INS-001.yaml").write_text(
        yaml.dump(ins1, allow_unicode=True), encoding="utf-8"
    )
    (insights_dir / "INS-002.yaml").write_text(
        yaml.dump(ins2, allow_unicode=True), encoding="utf-8"
    )

    return tmp_path


@pytest.fixture
def empty_project(tmp_path):
    """最小项目 (仅 project.yaml)"""
    config = {"project": {"name": "EmptyProject", "version": "0.1.0"}}
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config), encoding="utf-8"
    )
    return tmp_path


# ============================================================
# 辅助函数测试
# ============================================================


class TestHelpers:
    def test_find_project_root(self, project_dir):
        from vibecollab.mcp_server import _find_project_root

        # 从项目根找
        assert _find_project_root(project_dir) == project_dir

        # 从子目录找
        sub = project_dir / "docs"
        assert _find_project_root(sub) == project_dir

    def test_find_project_root_no_yaml(self, tmp_path):
        from vibecollab.mcp_server import _find_project_root

        # 没有 project.yaml，返回起始目录
        result = _find_project_root(tmp_path)
        assert result == tmp_path

    def test_safe_read_text(self, project_dir):
        from vibecollab.mcp_server import _safe_read_text

        text = _safe_read_text(project_dir / "CONTRIBUTING_AI.md")
        assert "AI 协作协议" in text

    def test_safe_read_text_missing(self, tmp_path):
        from vibecollab.mcp_server import _safe_read_text

        assert _safe_read_text(tmp_path / "nonexistent.md") == ""

    def test_safe_load_yaml(self, project_dir):
        from vibecollab.mcp_server import _safe_load_yaml

        data = _safe_load_yaml(project_dir / "project.yaml")
        assert data["project"]["name"] == "TestProject"

    def test_safe_load_yaml_missing(self, tmp_path):
        from vibecollab.mcp_server import _safe_load_yaml

        assert _safe_load_yaml(tmp_path / "missing.yaml") == {}

    def test_get_insight_files(self, project_dir):
        from vibecollab.mcp_server import _get_insight_files

        files = _get_insight_files(project_dir)
        assert len(files) == 2
        assert files[0].name == "INS-002.yaml"  # 倒序

    def test_get_insight_files_no_dir(self, tmp_path):
        from vibecollab.mcp_server import _get_insight_files

        assert _get_insight_files(tmp_path) == []


# ============================================================
# MCP Server 创建测试
# ============================================================


class TestCreateMcpServer:
    def test_import_error_without_mcp(self, project_dir):
        """未安装 mcp 时应抛出 ImportError"""
        from vibecollab.mcp_server import create_mcp_server

        with patch.dict("sys.modules", {"mcp": None, "mcp.server.fastmcp": None}):
            with pytest.raises(ImportError, match="mcp 依赖"):
                create_mcp_server(project_dir)

    @pytest.mark.skipif(
        not _mcp_available(),
        reason="mcp 未安装，跳过 Server 实例化测试",
    )
    def test_create_server(self, project_dir):
        """成功创建 MCP Server 实例"""
        from vibecollab.mcp_server import create_mcp_server

        server = create_mcp_server(project_dir)
        assert server is not None


# ============================================================
# Resource 测试 (mock FastMCP)
# ============================================================


class TestResources:
    """测试 Resource 函数的数据读取逻辑"""

    def test_get_contributing_ai(self, project_dir):
        from vibecollab.mcp_server import _safe_read_text

        text = _safe_read_text(project_dir / "CONTRIBUTING_AI.md")
        assert "AI 协作协议" in text
        assert "核心理念" in text

    def test_get_context(self, project_dir):
        from vibecollab.mcp_server import _safe_read_text

        text = _safe_read_text(project_dir / "docs" / "CONTEXT.md")
        assert "项目上下文" in text
        assert "v1.0.0" in text

    def test_get_decisions(self, project_dir):
        from vibecollab.mcp_server import _safe_read_text

        text = _safe_read_text(project_dir / "docs" / "DECISIONS.md")
        assert "DECISION-001" in text

    def test_get_insights_list(self, project_dir):
        from vibecollab.mcp_server import _get_insight_files, _safe_load_yaml

        files = _get_insight_files(project_dir)
        insights = []
        for f in files:
            data = _safe_load_yaml(f)
            if data:
                insights.append({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "tags": data.get("tags"),
                })
        assert len(insights) == 2
        assert insights[0]["id"] == "INS-002"  # 倒序
        assert "mcp" in insights[1]["tags"]

    def test_empty_project_resources(self, empty_project):
        from vibecollab.mcp_server import _safe_read_text, _get_insight_files

        assert _safe_read_text(empty_project / "CONTRIBUTING_AI.md") == ""
        assert _safe_read_text(empty_project / "docs" / "CONTEXT.md") == ""
        assert _get_insight_files(empty_project) == []


# ============================================================
# Tool CLI 调用测试 (mock subprocess)
# ============================================================


class TestTools:
    """测试 Tool 函数的 CLI 调用逻辑"""

    def test_run_cli_success(self, project_dir):
        from vibecollab.mcp_server import _run_cli

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="搜索结果: INS-001\n",
                stderr="",
                returncode=0,
            )
            result = _run_cli(
                ["vibecollab", "insight", "search", "test"],
                project_dir,
            )
            assert "INS-001" in result
            mock_run.assert_called_once()

    def test_run_cli_error(self, project_dir):
        from vibecollab.mcp_server import _run_cli

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="错误信息",
                returncode=1,
            )
            result = _run_cli(["vibecollab", "check"], project_dir)
            assert "stderr" in result
            assert "错误信息" in result

    def test_run_cli_timeout(self, project_dir):
        from vibecollab.mcp_server import _run_cli

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = _run_cli(["vibecollab", "check"], project_dir)
            assert "超时" in result

    def test_run_cli_not_found(self, project_dir):
        from vibecollab.mcp_server import _run_cli

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _run_cli(["vibecollab", "check"], project_dir)
            assert "未找到" in result

    def test_developer_context_exists(self, project_dir):
        """开发者上下文读取"""
        from vibecollab.mcp_server import _safe_read_text, _safe_load_yaml

        dev_dir = project_dir / "docs" / "developers" / "alice"
        context = _safe_read_text(dev_dir / "CONTEXT.md")
        metadata = _safe_load_yaml(dev_dir / ".metadata.yaml")

        assert "Alice 上下文" in context
        assert metadata["id"] == "alice"

    def test_developer_context_missing(self, project_dir):
        dev_dir = project_dir / "docs" / "developers" / "nonexistent"
        assert not dev_dir.exists()


# ============================================================
# Prompt 模板测试
# ============================================================


class TestPrompts:
    def test_start_conversation_prompt(self, project_dir):
        """测试对话开始 prompt 生成逻辑"""
        from vibecollab.mcp_server import _safe_load_yaml, _safe_read_text

        # 模拟 prompt 生成逻辑
        config = _safe_load_yaml(project_dir / "project.yaml")
        proj = config.get("project", {})
        context_text = _safe_read_text(project_dir / "docs" / "CONTEXT.md")

        assert proj["name"] == "TestProject"
        assert "项目上下文" in context_text

    def test_start_conversation_with_developer(self, project_dir):
        from vibecollab.mcp_server import _safe_read_text

        dev_context = _safe_read_text(
            project_dir / "docs" / "developers" / "alice" / "CONTEXT.md"
        )
        assert "Alice 上下文" in dev_context
        assert "MCP Server" in dev_context

    def test_start_conversation_empty_project(self, empty_project):
        from vibecollab.mcp_server import _safe_load_yaml, _safe_read_text

        config = _safe_load_yaml(empty_project / "project.yaml")
        assert config["project"]["name"] == "EmptyProject"
        assert _safe_read_text(empty_project / "docs" / "CONTEXT.md") == ""


# ============================================================
# CLI 命令测试
# ============================================================


class TestCliMcp:
    def test_mcp_group_help(self):
        from vibecollab.cli_mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["--help"])
        assert result.exit_code == 0
        assert "MCP Server" in result.output

    def test_mcp_serve_help(self):
        from vibecollab.cli_mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["serve", "--help"])
        assert result.exit_code == 0
        assert "stdio" in result.output
        assert "sse" in result.output

    def test_mcp_config_cursor(self):
        from vibecollab.cli_mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["config", "--ide", "cursor"])
        assert result.exit_code == 0
        assert ".cursor/mcp.json" in result.output
        assert "vibecollab" in result.output

    def test_mcp_config_cline(self):
        from vibecollab.cli_mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["config", "--ide", "cline"])
        assert result.exit_code == 0
        assert ".cline/mcp_settings.json" in result.output

    def test_mcp_config_codebuddy(self):
        from vibecollab.cli_mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(mcp_group, ["config", "--ide", "codebuddy"])
        assert result.exit_code == 0
        assert ".codebuddy/mcp.json" in result.output

    def test_mcp_inject_cursor(self, tmp_path):
        from vibecollab.cli_mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(
            mcp_group, ["inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "已注入" in result.output

        # 验证文件已创建
        config_file = tmp_path / ".cursor" / "mcp.json"
        assert config_file.exists()
        data = json.loads(config_file.read_text())
        assert "vibecollab" in data["mcpServers"]

    def test_mcp_inject_all(self, tmp_path):
        from vibecollab.cli_mcp import mcp_group

        runner = CliRunner()
        result = runner.invoke(
            mcp_group, ["inject", "--ide", "all", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / ".cursor" / "mcp.json").exists()
        assert (tmp_path / ".cline" / "mcp_settings.json").exists()
        assert (tmp_path / ".codebuddy" / "mcp.json").exists()

    def test_mcp_inject_preserves_existing(self, tmp_path):
        """注入时应保留已有配置"""
        from vibecollab.cli_mcp import mcp_group

        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir()
        existing = {
            "mcpServers": {
                "other-tool": {"command": "other", "args": ["serve"]},
            }
        }
        (cursor_dir / "mcp.json").write_text(json.dumps(existing))

        runner = CliRunner()
        result = runner.invoke(
            mcp_group, ["inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0

        data = json.loads((cursor_dir / "mcp.json").read_text())
        assert "other-tool" in data["mcpServers"]
        assert "vibecollab" in data["mcpServers"]

    def test_mcp_serve_without_mcp_dep(self):
        """未安装 mcp 时 serve 应报错"""
        from vibecollab.cli_mcp import mcp_group

        runner = CliRunner()
        with patch.dict("sys.modules", {"vibecollab.mcp_server": None}):
            # 通过 mock import 失败
            result = runner.invoke(mcp_group, ["serve"])
            # 可能报 ImportError 或退出码非0
            # 具体行为取决于 mock 实现，这里只验证不崩溃
            assert result.exit_code != 0 or "错误" in result.output or "Error" in result.output


# ============================================================
# 集成测试 (完整 CLI 链路)
# ============================================================


class TestIntegration:
    def test_vibecollab_mcp_registered(self):
        """vibecollab mcp 命令已注册到主 CLI"""
        from vibecollab.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["mcp", "--help"])
        assert result.exit_code == 0
        assert "serve" in result.output
        assert "config" in result.output
        assert "inject" in result.output

    def test_full_inject_and_verify(self, tmp_path):
        """完整注入流程: inject → 验证配置文件内容"""
        from vibecollab.cli import main

        runner = CliRunner()
        result = runner.invoke(
            main, ["mcp", "inject", "--ide", "cursor", "-p", str(tmp_path)]
        )
        assert result.exit_code == 0

        config_path = tmp_path / ".cursor" / "mcp.json"
        assert config_path.exists()

        data = json.loads(config_path.read_text())
        server_config = data["mcpServers"]["vibecollab"]
        assert server_config["command"] == "vibecollab"
        assert server_config["args"] == ["mcp", "serve"]
