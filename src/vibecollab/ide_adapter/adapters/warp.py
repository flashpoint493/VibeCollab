"""
Warp Terminal Adapter

Warp 适配器实现。Warp 使用云端 Warp Drive 存储工作流，
不支持本地文件注入。
"""

from typing import Any

from ..base import BaseIDEAdapter, IDEType
from ..registry import register_adapter


@register_adapter
class WarpAdapter(BaseIDEAdapter):
    """Warp Terminal 适配器。"""

    ide_type = IDEType.WARP
    display_name = "Warp"
    description = "Warp Terminal - cloud-based Warp Drive workflows, manual configuration required"

    supports_skill = False  # 云端存储，不支持本地注入
    skill_file_path = None

    supports_mcp = False
    mcp_config_path = None

    def get_skill_content(self) -> str:
        """获取 Warp 配置指南。

        由于 Warp 使用云端 Warp Drive，此方法返回说明文档。

        Returns:
            str: 手动配置说明
        """
        return """# Warp Terminal Configuration Guide

Warp uses cloud-based Warp Drive for workflows and does not support local file injection.

## Warp Drive Workflows (Cloud)

1. Open Warp Terminal
2. Access Warp Drive (Cmd+Shift+D or Ctrl+Shift+D)
3. Create a new workflow named "vibecollab"
4. Add the following commands as workflow steps:

### Onboarding Steps

```bash
# Get project context
vibecollab onboard

# Read documentation
cat docs/CONTEXT.md
cat docs/ROADMAP.md
```

### Development Steps

```bash
# Create task
vibecollab task create --role DEV --feature "$1"

# Check protocol compliance
vibecollab check

# Record insight
vibecollab insight add --category pattern --content "$1"

# Update task status
vibecollab task transition "$1" "$2"
```

### End of Session Steps

```bash
# Save session
vibecollab session_save --summary "$1" --role "$2"

# Complete task
vibecollab task solidify "$1"

# Git operations
git add -A
git commit -m "$1"
```

## Local YAML Workflows (Experimental)

Some versions of Warp support local YAML workflows. If available, create:
`.warp/workflows/vibecollab.yaml`

Refer to Warp documentation for the latest YAML format.

## MCP Configuration

Warp does not currently support MCP server configuration.

## Key Files Reference

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
        """获取 Warp MCP 配置。

        Warp 暂不支持 MCP，返回空字典。

        Args:
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            dict: 空配置字典
        """
        return {}
