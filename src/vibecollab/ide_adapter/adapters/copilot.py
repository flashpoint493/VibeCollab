"""
GitHub Copilot Adapter

GitHub Copilot 适配器实现，作为 VS Code 扩展使用 .vscode/ 目录结构。
"""

from typing import Any

from ..base import BaseIDEAdapter, IDEType
from ..registry import register_adapter


@register_adapter
class CopilotAdapter(BaseIDEAdapter):
    """GitHub Copilot 适配器。"""

    ide_type = IDEType.COPILOT
    display_name = "GitHub Copilot"
    description = "GitHub Copilot as VS Code extension with skills support"

    supports_skill = True
    skill_file_path = ".github/skills/vibecollab.md"

    supports_mcp = False
    mcp_config_path = None  # VS Code uses settings.json (not yet supported)

    def get_skill_content(self) -> str:
        """获取 Copilot Skill 文件内容（Markdown + YAML Frontmatter）。"""
        return """---
description: VibeCollab Protocol Rules
globs: "**/*"
alwaysApply: true
---

# VibeCollab AI Collaboration Protocol

You are assisting with a VibeCollab-managed project. Follow these guidelines:

## At Start of Conversation

1. Run `vibecollab onboard` to get full project context
2. Read `docs/CONTEXT.md` for current development state
3. Check `docs/ROADMAP.md` for current milestone
4. Review assigned tasks from previous sessions

## During Development

1. **Create task before implementing**: `vibecollab task create --role DEV --feature "X"`
2. **Check protocol compliance**: `vibecollab check`
3. **Record insights**: `vibecollab insight add --category pattern --content "..."`
4. **Update task status**: `vibecollab task transition <id> <status>`

## At End of Conversation

1. **Save session**: `vibecollab session_save --summary "..." --role <role>`
2. **Complete tasks**: `vibecollab task solidify <id>`
3. **Update CHANGELOG.md**
4. **Record decisions** in `docs/DECISIONS.md`
5. **Git commit** all changes

## Key Files

- `project.yaml` - Project configuration
- `CONTRIBUTING_AI.md` - Full collaboration rules
- `docs/CONTEXT.md` - Current context
- `docs/DECISIONS.md` - Decision records
- `docs/ROADMAP.md` - Milestones and tasks
- `docs/CHANGELOG.md` - Change history

## Decision Levels

- **S (Strategic)**: Overall direction - requires human approval
- **A (Architecture)**: System design - human review required
- **B (Implementation)**: Specific approach - quick confirm
- **C (Detail)**: Naming, params - AI decides autonomously
"""

    def get_mcp_config(self, command: str, args: list[str]) -> dict[str, Any]:
        """获取 Copilot MCP 配置。

        Copilot 暂不支持 MCP 配置注入，返回空字典。

        Args:
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            dict: 空配置字典
        """
        return {}
