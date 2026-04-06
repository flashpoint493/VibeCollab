"""
IDE Adapter Unit Tests

测试所有 IDE 适配器的功能。
"""

import json
from pathlib import Path

import pytest

from vibecollab.ide_adapter import get_adapter, list_adapters
from vibecollab.ide_adapter.adapters import (
    AugmentAdapter,
    ClaudeAdapter,
    ClineAdapter,
    CodeBuddyAdapter,
    ContinueAdapter,
    CopilotAdapter,
    CursorAdapter,
    GeminiAdapter,
    KimiCodeAdapter,
    KiroAdapter,
    OpenCodeAdapter,
    RooCodeAdapter,
    TraeAdapter,
    WarpAdapter,
    WindsurfAdapter,
)
from vibecollab.ide_adapter.base import IDEType, InjectionResult


class TestBaseIDEAdapter:
    """测试基类功能。"""

    def test_injection_result_add_operation(self):
        """测试 InjectionResult 添加操作。"""
        result = InjectionResult(success=True, ide_type=IDEType.CURSOR)
        result.add_operation(Path("/test/file.md"), "created")

        assert len(result.operations) == 1
        assert result.operations[0].action == "created"
        assert result.created_files == [Path("/test/file.md")]

    def test_injection_result_created_updated_files(self):
        """测试 InjectionResult 文件列表属性。"""
        result = InjectionResult(success=True, ide_type=IDEType.CURSOR)
        result.add_operation(Path("/test/file1.md"), "created")
        result.add_operation(Path("/test/file2.md"), "updated")
        result.add_operation(Path("/test/file3.md"), "skipped")

        assert len(result.created_files) == 1
        assert len(result.updated_files) == 1
        assert result.created_files[0].name == "file1.md"
        assert result.updated_files[0].name == "file2.md"


class TestCursorAdapter:
    """测试 Cursor 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = CursorAdapter()
        assert adapter.ide_type == IDEType.CURSOR
        assert adapter.display_name == "Cursor"
        assert adapter.supports_skill is True
        assert adapter.supports_mcp is True

    def test_get_skill_content(self):
        """测试获取 skill 内容。"""
        adapter = CursorAdapter()
        content = adapter.get_skill_content()
        assert "VibeCollab" in content
        assert "---" in content  # YAML Frontmatter

    def test_get_mcp_config(self):
        """测试获取 MCP 配置。"""
        adapter = CursorAdapter()
        config = adapter.get_mcp_config("python", ["-m", "vibecollab", "mcp", "serve"])

        assert "mcpServers" in config
        assert "vibecollab" in config["mcpServers"]
        assert config["mcpServers"]["vibecollab"]["command"] == "python"

    def test_inject_skill(self, tmp_path):
        """测试 skill 注入。"""
        adapter = CursorAdapter()
        result = adapter.inject_skill(tmp_path, force=False)

        assert result.success is True
        assert result.ide_type == IDEType.CURSOR
        assert (tmp_path / ".cursor" / "rules" / "vibecollab.mdc").exists()

    def test_inject_skill_no_force(self, tmp_path):
        """测试 skill 注入（不强制覆盖）。"""
        adapter = CursorAdapter()
        skill_file = tmp_path / ".cursor" / "rules" / "vibecollab.mdc"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("existing content")

        result = adapter.inject_skill(tmp_path, force=False)

        assert result.success is True
        assert any(op.action == "skipped" for op in result.operations)

    def test_inject_mcp_config(self, tmp_path):
        """测试 MCP 配置注入。"""
        adapter = CursorAdapter()
        result = adapter.inject_mcp_config(tmp_path, "python", ["-m", "vibecollab", "mcp", "serve"])

        assert result.success is True
        assert (tmp_path / ".cursor" / "mcp.json").exists()

    def test_check_skill_exists(self, tmp_path):
        """测试检查 skill 是否存在。"""
        adapter = CursorAdapter()
        assert adapter.check_skill_exists(tmp_path) is False

        skill_file = tmp_path / ".cursor" / "rules" / "vibecollab.mdc"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("test")

        assert adapter.check_skill_exists(tmp_path) is True


class TestKimiCodeAdapter:
    """测试 KimiCode 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = KimiCodeAdapter()
        assert adapter.ide_type == IDEType.KIMICODE
        assert adapter.display_name == "KimiCode"
        assert adapter.supports_skill is True
        assert adapter.supports_mcp is True
        assert adapter.skill_file_path == ".kimicode/rules/vibecollab.md"
        assert adapter.mcp_config_path == ".kimicode/mcp.json"

    def test_get_skill_content(self):
        """测试获取 skill 内容。"""
        adapter = KimiCodeAdapter()
        content = adapter.get_skill_content()
        assert "VibeCollab" in content
        assert "---" in content  # YAML Frontmatter
        assert "description:" in content
        assert "globs:" in content

    def test_get_mcp_config(self):
        """测试获取 MCP 配置。"""
        adapter = KimiCodeAdapter()
        config = adapter.get_mcp_config("python", ["-m", "vibecollab", "mcp", "serve"])

        assert "mcpServers" in config
        assert "vibecollab" in config["mcpServers"]
        assert config["mcpServers"]["vibecollab"]["command"] == "python"
        assert config["mcpServers"]["vibecollab"]["args"] == ["-m", "vibecollab", "mcp", "serve"]

    def test_inject_skill(self, tmp_path):
        """测试 skill 注入。"""
        adapter = KimiCodeAdapter()
        result = adapter.inject_skill(tmp_path, force=False)

        assert result.success is True
        assert result.ide_type == IDEType.KIMICODE
        skill_file = tmp_path / ".kimicode" / "rules" / "vibecollab.md"
        assert skill_file.exists()
        assert "VibeCollab" in skill_file.read_text()

    def test_inject_mcp_config(self, tmp_path):
        """测试 MCP 配置注入。"""
        adapter = KimiCodeAdapter()
        result = adapter.inject_mcp_config(tmp_path, "python", ["-m", "vibecollab", "mcp", "serve"])

        assert result.success is True
        config_file = tmp_path / ".kimicode" / "mcp.json"
        assert config_file.exists()

        config = json.loads(config_file.read_text())
        assert "mcpServers" in config
        assert "vibecollab" in config["mcpServers"]

    def test_inject_mcp_config_merge(self, tmp_path):
        """测试 MCP 配置合并。"""
        adapter = KimiCodeAdapter()

        # 先创建现有配置
        config_file = tmp_path / ".kimicode" / "mcp.json"
        config_file.parent.mkdir(parents=True)
        existing = {"mcpServers": {"other": {"command": "other"}}}
        config_file.write_text(json.dumps(existing))

        result = adapter.inject_mcp_config(tmp_path, "python", ["-m", "vibecollab", "mcp", "serve"])

        assert result.success is True
        config = json.loads(config_file.read_text())
        assert "other" in config["mcpServers"]
        assert "vibecollab" in config["mcpServers"]


class TestOpenCodeAdapter:
    """测试 OpenCode 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = OpenCodeAdapter()
        assert adapter.ide_type == IDEType.OPENCODE
        assert adapter.display_name == "OpenCode"
        assert adapter.supports_skill is True
        assert adapter.supports_mcp is False

    def test_inject_skill_with_package_json(self, tmp_path):
        """测试 skill 注入（包含 package.json）。"""
        adapter = OpenCodeAdapter()
        result = adapter.inject_skill(tmp_path, force=False)

        assert result.success is True
        assert (tmp_path / ".opencode" / "skills" / "vibecollab.md").exists()
        assert (tmp_path / ".opencode" / "package.json").exists()

        package = json.loads((tmp_path / ".opencode" / "package.json").read_text())
        assert "@opencode-ai/plugin" in package.get("dependencies", {})

    def test_get_mcp_config_raises(self):
        """测试 MCP 配置抛出异常。"""
        adapter = OpenCodeAdapter()
        with pytest.raises(NotImplementedError):
            adapter.get_mcp_config("python", [])


class TestClineAdapter:
    """测试 Cline 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = ClineAdapter()
        assert adapter.ide_type == IDEType.CLINE
        assert adapter.display_name == "Cline"
        assert adapter.supports_skill is True
        assert adapter.supports_mcp is True

    def test_get_mcp_config_has_disabled_field(self):
        """测试 Cline MCP 配置包含 disabled 字段。"""
        adapter = ClineAdapter()
        config = adapter.get_mcp_config("python", [])

        assert config["mcpServers"]["vibecollab"]["disabled"] is False


class TestCodeBuddyAdapter:
    """测试 CodeBuddy 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = CodeBuddyAdapter()
        assert adapter.ide_type == IDEType.CODEBUDDY
        assert adapter.display_name == "CodeBuddy"

    def test_get_skill_content_json(self):
        """测试 CodeBuddy skill 是 JSON 格式。"""
        adapter = CodeBuddyAdapter()
        content = adapter.get_skill_content()
        # CodeBuddy 使用 JSON 格式
        config = json.loads(content)
        assert "name" in config


class TestClaudeAdapter:
    """测试 Claude 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = ClaudeAdapter()
        assert adapter.ide_type == IDEType.CLAUDE
        assert adapter.display_name == "Claude Code"
        assert adapter.supports_skill is True

    def test_get_skill_content(self):
        """测试获取 skill 内容。"""
        adapter = ClaudeAdapter()
        content = adapter.get_skill_content()
        assert "VibeCollab" in content


class TestWindsurfAdapter:
    """测试 Windsurf 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = WindsurfAdapter()
        assert adapter.ide_type == IDEType.WINDSURF
        assert adapter.display_name == "Windsurf"


class TestRooCodeAdapter:
    """测试 Roo Code 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = RooCodeAdapter()
        assert adapter.ide_type == IDEType.ROOCODE
        assert adapter.display_name == "Roo Code"
        assert adapter.supports_skill is True
        # Roo Code 有多个模式
        content = adapter.get_skill_content()
        assert "VibeCollab" in content


class TestContinueAdapter:
    """测试 Continue 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = ContinueAdapter()
        assert adapter.ide_type == IDEType.CONTINUE
        assert adapter.display_name == "Continue"

    def test_inject_mcp_config_yaml(self, tmp_path):
        """测试 Continue 使用 YAML MCP 配置。"""
        adapter = ContinueAdapter()
        result = adapter.inject_mcp_config(tmp_path, "python", ["-m", "vibecollab", "mcp", "serve"])

        assert result.success is True
        # Continue 使用 YAML 格式
        config_file = tmp_path / ".continue" / "mcpServers" / "vibecollab.yaml"
        assert config_file.exists()
        # 验证是 YAML 格式
        content = config_file.read_text()
        assert "mcpServers:" in content or "name:" in content


class TestGeminiAdapter:
    """测试 Gemini 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = GeminiAdapter()
        assert adapter.ide_type == IDEType.GEMINI
        assert adapter.display_name == "Gemini CLI"


class TestKiroAdapter:
    """测试 Kiro 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = KiroAdapter()
        assert adapter.ide_type == IDEType.KIRO
        assert adapter.display_name == "Kiro"


class TestTraeAdapter:
    """测试 Trae 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = TraeAdapter()
        assert adapter.ide_type == IDEType.TRAE
        assert adapter.display_name == "Trae"


class TestCopilotAdapter:
    """测试 Copilot 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = CopilotAdapter()
        assert adapter.ide_type == IDEType.COPILOT
        assert adapter.display_name == "GitHub Copilot"


class TestAugmentAdapter:
    """测试 Augment 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = AugmentAdapter()
        assert adapter.ide_type == IDEType.AUGMENT
        assert adapter.display_name == "Augment"
        # Augment 不支持 skill 注入
        assert adapter.supports_skill is False


class TestWarpAdapter:
    """测试 Warp 适配器。"""

    def test_adapter_metadata(self):
        """测试适配器元数据。"""
        adapter = WarpAdapter()
        assert adapter.ide_type == IDEType.WARP
        assert adapter.display_name == "Warp"
        # Warp 不支持 skill 注入
        assert adapter.supports_skill is False


class TestAdapterRegistry:
    """测试适配器注册表。"""

    def test_list_adapters(self):
        """测试列出所有适配器。"""
        adapters = list_adapters()
        assert len(adapters) >= 15

        types = [a.ide_type for a in adapters]
        assert IDEType.CURSOR in types
        assert IDEType.KIMICODE in types
        assert IDEType.OPENCODE in types

    def test_get_adapter_cursor(self):
        """测试获取 Cursor 适配器。"""
        adapter = get_adapter("cursor")
        assert adapter.ide_type == IDEType.CURSOR

    def test_get_adapter_kimicode(self):
        """测试获取 KimiCode 适配器。"""
        adapter = get_adapter("kimicode")
        assert adapter.ide_type == IDEType.KIMICODE

    def test_get_adapter_opencode(self):
        """测试获取 OpenCode 适配器。"""
        adapter = get_adapter("opencode")
        assert adapter.ide_type == IDEType.OPENCODE

    def test_get_adapter_by_enum(self):
        """测试使用枚举获取适配器。"""
        adapter = get_adapter(IDEType.CURSOR)
        assert adapter.ide_type == IDEType.CURSOR

    def test_get_adapter_not_found(self):
        """测试获取不存在的适配器。"""
        with pytest.raises(ValueError):
            get_adapter("nonexistent")


class TestIDEType:
    """测试 IDEType 枚举。"""

    def test_from_string_cursor(self):
        """测试从字符串创建 Cursor 类型。"""
        ide_type = IDEType.from_string("cursor")
        assert ide_type == IDEType.CURSOR

    def test_from_string_kimicode(self):
        """测试从字符串创建 KimiCode 类型。"""
        ide_type = IDEType.from_string("kimicode")
        assert ide_type == IDEType.KIMICODE

    def test_from_string_opencode(self):
        """测试从字符串创建 OpenCode 类型。"""
        ide_type = IDEType.from_string("opencode")
        assert ide_type == IDEType.OPENCODE

    def test_from_string_case_insensitive(self):
        """测试大小写不敏感。"""
        assert IDEType.from_string("CURSOR") == IDEType.CURSOR
        assert IDEType.from_string("Cursor") == IDEType.CURSOR
        assert IDEType.from_string("KimiCode") == IDEType.KIMICODE

    def test_from_string_invalid(self):
        """测试无效类型抛出异常。"""
        with pytest.raises(ValueError):
            IDEType.from_string("invalid")
