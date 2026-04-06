"""
Kiro Adapter

Kiro 适配器实现，支持 Skill 注入。
"""

from typing import Any

from ..base import BaseIDEAdapter, IDEType
from ..registry import register_adapter


@register_adapter
class KiroAdapter(BaseIDEAdapter):
    """Kiro IDE 适配器。"""

    ide_type = IDEType.KIRO
    display_name = "Kiro"
    description = "Kiro IDE with skills support"

    supports_skill = True
    skill_file_path = ".kiro/skills/vibecollab/SKILL.md"

    supports_mcp = False
    mcp_config_path = None

    def get_skill_content(self) -> str:
        """获取 Kiro Skill 文件内容（Markdown + YAML Frontmatter 格式）。"""
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
        """获取 Kiro MCP 配置。

        Args:
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            dict: MCP 配置字典
        """
        # Kiro 暂不支持 MCP
        return {}
