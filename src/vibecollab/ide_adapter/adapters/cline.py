"""
Cline IDE Adapter

Cline 适配器实现，支持 Skill 注入和 MCP 配置。
"""

from typing import Any

from ..base import BaseIDEAdapter, IDEType
from ..registry import register_adapter


@register_adapter
class ClineAdapter(BaseIDEAdapter):
    """Cline IDE 适配器。"""

    ide_type = IDEType.CLINE
    display_name = "Cline"
    description = "Cline IDE with skills and MCP support"

    supports_skill = True
    skill_file_path = ".cline/skills/vibecollab.md"

    supports_mcp = True
    mcp_config_path = ".cline/mcp_settings.json"

    def get_skill_content(self) -> str:
        """获取 Cline Skill 文件内容。"""
        return """# VibeCollab Skill for Cline

## Overview

VibeCollab is a configurable AI collaboration protocol framework with built-in knowledge capture (Insight) and task management. Use it to maintain structured context across conversations.

## When to Use

- Starting a new conversation on a VibeCollab-managed project
- Need to search past development experiences (Insights)
- Want to capture reusable knowledge from current work
- Need to check project protocol compliance
- Managing tasks and roadmap items

## Available Commands

### Core Workflow Commands

```bash
# Start of conversation - get full project context
vibecollab onboard

# Check protocol compliance (includes Insight consistency by default)
vibecollab check

# Get next action suggestions based on project state
vibecollab next

# Save conversation summary at the end
vibecollab session_save --summary "What was accomplished" --role <role>
```

### Task Management Commands

```bash
# Create a new task
vibecollab task create --role DEV --feature "Implement login" --output "auth.py"

# List current tasks
vibecollab task list

# Mark task as started
vibecollab task start <task_id>

# Complete a task (auto-updates context)
vibecollab task done <task_id>
```

### Insight System Commands

```bash
# Record a new insight
vibecollab insight add --category pattern --content "Found that using X approach reduces Y by 50%"

# Search insights by tag
vibecollab insight search --tag performance

# Semantic search across insights
vibecollab insight semantic "how to handle errors"

# List recent insights
vibecollab insight list --limit 10
```

### Roadmap Commands

```bash
# View current milestone status
vibecollab roadmap status

# List all milestones
vibecollab roadmap list

# Create task from ROADMAP
vibecollab roadmap task <milestone_id>
```

## Protocol Guidelines

### At Start of Conversation

1. Run `vibecollab onboard` to get full project context
2. Check `docs/CONTEXT.md` for current state
3. Review any assigned tasks from previous sessions

### During Development

1. Create task before implementing: `vibecollab task create`
2. Run `vibecollab check` periodically to verify compliance
3. Record insights when discovering useful patterns: `vibecollab insight add`
4. Update task status as you progress

### At End of Conversation

1. Save session summary: `vibecollab session_save`
2. Mark completed tasks: `vibecollab task done`
3. Update CHANGELOG.md with what was accomplished
4. Ensure all decisions are recorded in docs/DECISIONS.md

## Key Files

- `project.yaml` - Project configuration and protocol settings
- `CONTRIBUTING_AI.md` - Full AI collaboration rules
- `docs/CONTEXT.md` - Current development context
- `docs/ROADMAP.md` - Project roadmap and milestones
- `docs/DECISIONS.md` - Important decision records
- `docs/CHANGELOG.md` - Development changelog
- `.vibecollab/events.jsonl` - Event log for Insight generation

## Multi-Role Mode

If the project has `role_context.enabled: true`:

- Each role has their own context in `docs/roles/{id}/`
- Check current identity with `vibecollab dev whoami`
- Collaboration tracked in `docs/roles/COLLABORATION.md`

## Best Practices

1. **Always onboard first** - Get context before starting work
2. **One task at a time** - Focus on single task completion
3. **Record insights immediately** - Don't wait, capture knowledge while fresh
4. **Update context continuously** - Keep docs/CONTEXT.md current
5. **Follow decision levels** - S/A decisions need confirmation, B/C can proceed
6. **Git commit regularly** - Each task completion should have a commit
"""

    def get_mcp_config(self, command: str, args: list[str]) -> dict[str, Any]:
        """获取 Cline MCP 配置。

        Cline 需要额外的 disabled 字段。

        Args:
            command: MCP 服务器命令
            args: MCP 服务器参数

        Returns:
            dict: MCP 配置字典
        """
        return {
            "mcpServers": {
                "vibecollab": {
                    "command": command,
                    "args": args,
                    "disabled": False,
                }
            }
        }
