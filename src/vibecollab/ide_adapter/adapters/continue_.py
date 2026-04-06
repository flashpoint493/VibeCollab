"""
Continue Adapter

Continue 适配器实现，支持 MCP 配置（YAML 格式）。
"""

from pathlib import Path
from typing import Any

from ..base import BaseIDEAdapter, IDEType, InjectionResult
from ..registry import register_adapter


@register_adapter
class ContinueAdapter(BaseIDEAdapter):
    """Continue IDE 适配器。"""

    ide_type = IDEType.CONTINUE
    display_name = "Continue"
    description = "Continue IDE with MCP support (YAML config)"

    supports_skill = False
    skill_file_path = None

    supports_mcp = True
    mcp_config_path = ".continue/mcpServers/vibecollab.yaml"

    def get_skill_content(self) -> str:
        """获取 Continue Skill 文件内容。

        Continue 暂不支持 Skill，返回空字符串。
        """
        return ""

    def get_mcp_config(self, command: str, args: list[str]) -> dict[str, Any]:
        """获取 Continue MCP 配置。

        Args:
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            dict: MCP 配置字典
        """
        return {
            "name": "vibecollab",
            "version": "0.12.0",
            "schema": "v1",
            "mcpServers": [
                {
                    "name": "VibeCollab",
                    "command": command,
                    "args": args,
                }
            ]
        }

    def inject_mcp_config(
        self,
        project_root: Path,
        command: str,
        args: list[str],
    ) -> InjectionResult:
        """注入 MCP 配置到项目（YAML 格式）。

        覆盖基类方法以支持 YAML 格式而不是 JSON。

        Args:
            project_root: 项目根目录
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            InjectionResult: 注入结果
        """
        result = InjectionResult(success=True, ide_type=self.ide_type)

        if not self.supports_mcp or not self.mcp_config_path:
            result.success = False
            result.message = f"{self.display_name} does not support MCP configuration"
            return result

        try:
            import yaml

            config_path = project_root / self.mcp_config_path
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # 获取新配置
            new_config = self.get_mcp_config(command, args)

            # 写入 YAML 文件
            config_path.write_text(
                yaml.dump(new_config, indent=2, allow_unicode=True, sort_keys=False),
                encoding="utf-8"
            )

            action = "updated" if config_path.exists() else "created"
            result.add_operation(config_path, action)
            result.message = f"{self.display_name} MCP config injected"

        except ImportError:
            result.success = False
            result.message = "PyYAML is required for Continue MCP config. Install with: pip install pyyaml"
        except Exception as e:
            result.success = False
            result.message = f"Failed to inject MCP config: {e}"

        return result

    def check_mcp_config_exists(self, project_root: Path) -> bool:
        """检查 MCP 配置是否已存在。

        Args:
            project_root: 项目根目录

        Returns:
            bool: 是否存在
        """
        if not self.supports_mcp or not self.mcp_config_path:
            return False
        config_path = project_root / self.mcp_config_path
        if not config_path.exists():
            return False

        try:
            import yaml
            content = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            return "mcpServers" in content and any(
                server.get("name") == "VibeCollab"
                for server in content.get("mcpServers", [])
            )
        except (yaml.YAMLError, OSError):
            return False
