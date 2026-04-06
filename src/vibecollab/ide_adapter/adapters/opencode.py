"""
OpenCode IDE Adapter

OpenCode 适配器实现，支持 Skill 注入。
"""

from typing import Any

from ..base import BaseIDEAdapter, IDEType
from ..registry import register_adapter


@register_adapter
class OpenCodeAdapter(BaseIDEAdapter):
    """OpenCode IDE 适配器。"""

    ide_type = IDEType.OPENCODE
    display_name = "OpenCode"
    description = "OpenCode IDE with plugin-based skill system"

    supports_skill = True
    skill_file_path = ".opencode/skills/vibecollab.md"

    supports_mcp = False
    mcp_config_path = None

    def get_skill_content(self) -> str:
        """获取 OpenCode Skill 文件内容。"""
        return """# VibeCollab Skill for OpenCode

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
        """OpenCode 不支持 MCP 配置。"""
        raise NotImplementedError("OpenCode does not support MCP configuration")

    def inject_skill(self, project_root, force: bool = False):
        """注入 Skill，同时创建 package.json。"""
        import json

        result = super().inject_skill(project_root, force)

        if not result.success:
            return result

        # OpenCode 需要额外的 package.json
        try:
            opencode_dir = project_root / ".opencode"
            package_file = opencode_dir / "package.json"

            package_content = {"dependencies": {"@opencode-ai/plugin": "1.3.2"}}

            if package_file.exists() and not force:
                try:
                    existing = json.loads(package_file.read_text(encoding="utf-8"))
                    if existing.get("dependencies", {}).get("@opencode-ai/plugin"):
                        result.add_operation(
                            package_file,
                            "skipped",
                            "OpenCode already configured"
                        )
                    else:
                        existing["dependencies"] = existing.get("dependencies", {})
                        existing["dependencies"]["@opencode-ai/plugin"] = "1.3.2"
                        package_file.write_text(
                            json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8",
                        )
                        result.add_operation(package_file, "updated")
                except (json.JSONDecodeError, OSError):
                    package_file.write_text(
                        json.dumps(package_content, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    result.add_operation(package_file, "created")
            else:
                package_file.write_text(
                    json.dumps(package_content, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                action = "updated" if package_file.exists() else "created"
                result.add_operation(package_file, action)

        except Exception as e:
            result.message += f" (Warning: package.json creation failed: {e})"

        return result
