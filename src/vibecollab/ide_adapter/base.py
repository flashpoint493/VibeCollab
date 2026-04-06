"""
Base IDE Adapter - IDE 适配器抽象基类

定义所有 IDE 适配器必须实现的接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class IDEType(str, Enum):
    """支持的 IDE 类型。"""

    OPENCODE = "opencode"
    CURSOR = "cursor"
    CLINE = "cline"
    CODEBUDDY = "codebuddy"
    CLAUDE = "claude"
    WINDSURF = "windsurf"
    ROOCODE = "roocode"
    GEMINI = "gemini"
    KIRO = "kiro"
    CONTINUE = "continue"
    TRAE = "trae"
    COPILOT = "copilot"
    AUGMENT = "augment"
    WARP = "warp"
    KIMICODE = "kimicode"

    @classmethod
    def from_string(cls, value: str) -> "IDEType":
        """从字符串创建 IDEType，支持别名。"""
        value = value.lower().strip()
        mapping = {
            "opencode": cls.OPENCODE,
            "cursor": cls.CURSOR,
            "cline": cls.CLINE,
            "codebuddy": cls.CODEBUDDY,
            "claude": cls.CLAUDE,
            "windsurf": cls.WINDSURF,
            "roocode": cls.ROOCODE,
            "gemini": cls.GEMINI,
            "kiro": cls.KIRO,
            "continue": cls.CONTINUE,
            "trae": cls.TRAE,
            "copilot": cls.COPILOT,
            "augment": cls.AUGMENT,
            "warp": cls.WARP,
            "kimicode": cls.KIMICODE,
            # 别名
            "code-buddy": cls.CODEBUDDY,
        }
        if value not in mapping:
            raise ValueError(f"Unknown IDE type: {value}")
        return mapping[value]


@dataclass
class FileOperation:
    """文件操作记录。"""

    path: Path
    action: str  # "created", "updated", "skipped", "error"
    message: str = ""


@dataclass
class InjectionResult:
    """注入操作结果。"""

    success: bool
    ide_type: IDEType
    operations: list[FileOperation] = field(default_factory=list)
    message: str = ""

    def add_operation(self, path: Path, action: str, message: str = "") -> None:
        """添加文件操作记录。"""
        self.operations.append(FileOperation(path=path, action=action, message=message))

    @property
    def created_files(self) -> list[Path]:
        """获取创建的文件列表。"""
        return [op.path for op in self.operations if op.action == "created"]

    @property
    def updated_files(self) -> list[Path]:
        """获取更新的文件列表。"""
        return [op.path for op in self.operations if op.action == "updated"]


class BaseIDEAdapter(ABC):
    """IDE 适配器抽象基类。

    所有 IDE 适配器必须继承此类并实现抽象方法。
    """

    # 适配器元数据
    ide_type: IDEType
    display_name: str
    description: str = ""

    # Skill 配置
    supports_skill: bool = False
    skill_file_path: Optional[str] = None  # 相对路径模板

    # MCP 配置
    supports_mcp: bool = False
    mcp_config_path: Optional[str] = None  # 相对路径模板

    def __init__(self) -> None:
        """初始化适配器。"""
        pass

    @abstractmethod
    def get_skill_content(self) -> str:
        """获取 Skill 文件内容。

        Returns:
            str: Skill 文件内容
        """
        pass

    @abstractmethod
    def get_mcp_config(self, command: str, args: list[str]) -> dict[str, Any]:
        """获取 MCP 配置字典。

        Args:
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            dict: MCP 配置字典
        """
        pass

    def inject_skill(self, project_root: Path, force: bool = False) -> InjectionResult:
        """注入 Skill 到项目。

        Args:
            project_root: 项目根目录
            force: 是否强制覆盖现有文件

        Returns:
            InjectionResult: 注入结果
        """
        result = InjectionResult(success=True, ide_type=self.ide_type)

        if not self.supports_skill or not self.skill_file_path:
            result.success = False
            result.message = f"{self.display_name} does not support skill injection"
            return result

        try:
            skill_file = project_root / self.skill_file_path
            skill_file.parent.mkdir(parents=True, exist_ok=True)

            content = self.get_skill_content()

            if skill_file.exists() and not force:
                result.add_operation(
                    skill_file,
                    "skipped",
                    "File already exists (use force=True to overwrite)"
                )
            else:
                skill_file.write_text(content, encoding="utf-8")
                action = "updated" if skill_file.exists() else "created"
                result.add_operation(skill_file, action)

            result.message = f"{self.display_name} skill injection complete"

        except Exception as e:
            result.success = False
            result.message = f"Failed to inject skill: {e}"

        return result

    def inject_mcp_config(
        self,
        project_root: Path,
        command: str,
        args: list[str],
    ) -> InjectionResult:
        """注入 MCP 配置到项目。

        Args:
            project_root: 项目根目录
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            InjectionResult: 注入结果
        """
        import json

        result = InjectionResult(success=True, ide_type=self.ide_type)

        if not self.supports_mcp or not self.mcp_config_path:
            result.success = False
            result.message = f"{self.display_name} does not support MCP configuration"
            return result

        try:
            config_path = project_root / self.mcp_config_path
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # 读取现有配置
            existing: dict = {}
            if config_path.exists():
                try:
                    existing = json.loads(config_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    existing = {}

            # 合并新配置
            new_config = self.get_mcp_config(command, args)
            merged = self._merge_mcp_config(existing, new_config)

            # 写入文件
            config_path.write_text(
                json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8"
            )

            action = "updated" if config_path.exists() else "created"
            result.add_operation(config_path, action)
            result.message = f"{self.display_name} MCP config injected"

        except Exception as e:
            result.success = False
            result.message = f"Failed to inject MCP config: {e}"

        return result

    def _merge_mcp_config(self, existing: dict, new_config: dict) -> dict:
        """合并 MCP 配置。

        Args:
            existing: 现有配置
            new_config: 新配置

        Returns:
            dict: 合并后的配置
        """
        # 默认策略：深度合并 mcpServers
        if "mcpServers" not in existing:
            existing["mcpServers"] = {}

        if "mcpServers" in new_config:
            existing["mcpServers"].update(new_config["mcpServers"])

        return existing

    def check_skill_exists(self, project_root: Path) -> bool:
        """检查 Skill 文件是否已存在。

        Args:
            project_root: 项目根目录

        Returns:
            bool: 是否存在
        """
        if not self.supports_skill or not self.skill_file_path:
            return False
        return (project_root / self.skill_file_path).exists()

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
            import json
            content = json.loads(config_path.read_text(encoding="utf-8"))
            return "mcpServers" in content and "vibecollab" in content.get("mcpServers", {})
        except (json.JSONDecodeError, OSError):
            return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(ide_type={self.ide_type.value})>"
