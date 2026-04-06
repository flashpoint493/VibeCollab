"""
Augment IDE Adapter

Augment 适配器实现。Augment 作为 IDE 插件，无特定的 skill 配置文件路径，
需要手动配置。
"""

from typing import Any

from ..base import BaseIDEAdapter, IDEType
from ..registry import register_adapter


@register_adapter
class AugmentAdapter(BaseIDEAdapter):
    """Augment IDE 适配器。"""

    ide_type = IDEType.AUGMENT
    display_name = "Augment"
    description = "Augment IDE plugin - manual configuration required. Place skill file in .claude/skills/ or .agents/skills/ directory"

    supports_skill = False  # 需要手动配置
    skill_file_path = None

    supports_mcp = False
    mcp_config_path = None

    def get_skill_content(self) -> str:
        """获取 Augment Skill 文件内容。

        由于 Augment 需要手动配置，此方法返回说明文档。

        Returns:
            str: 手动配置说明
        """
        return """# Augment Manual Configuration Guide

Augment does not support automatic skill file injection. Please configure manually:

## Option 1: Use .claude/skills/ Directory

1. Create directory: `.claude/skills/`
2. Create file: `.claude/skills/vibecollab.md`
3. Copy the following content:

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

---

## Option 2: Use .agents/skills/ Directory

Alternatively, place the skill file in `.agents/skills/vibecollab.md`.

## MCP Configuration

Augment does not currently support MCP server configuration.
"""

    def get_mcp_config(self, command: str, args: list[str]) -> dict[str, Any]:
        """获取 Augment MCP 配置。

        Augment 暂不支持 MCP，返回空字典。

        Args:
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            dict: 空配置字典
        """
        return {}
