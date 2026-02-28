"""
IDE platform registry — MCP / rules / skills paths per editor.

Structure aligned with vx (https://github.com/loonghao/vx): each platform has
.<platform>/skills/<skill-name>/ with SKILL.md; rules paths follow per-IDE conventions.
Write once, native format per platform. No external dependencies.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

# Platform id -> paths and format. rules_path and skills_path are relative to project root.
# rules_format: "cursor_mdc" (frontmatter + body) | "plain_md"
# skills_format: "skill_md" (SKILL.md in subdir, vx-style)
# MCP: only cursor, cline, codebuddy have mcp_path (MCP config file).
PLATFORMS: Dict[str, Dict[str, Any]] = {
    "cursor": {
        "mcp_path": ".cursor/mcp.json",
        "rules_path": ".cursor/rules/vibecollab.mdc",
        "rules_format": "cursor_mdc",
        "skills_path": ".cursor/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    "cline": {
        "mcp_path": ".cline/mcp_settings.json",
        "rules_path": ".clinerules/vibecollab.md",
        "rules_format": "plain_md",
        "skills_path": ".cline/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    "codebuddy": {
        "mcp_path": ".codebuddy/mcp.json",
        "rules_path": ".codebuddy/rules/vibecollab-protocol.mdc",
        "rules_format": "plain_md",
        "skills_path": ".codebuddy/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    "windsurf": {
        "mcp_path": None,
        "rules_path": ".windsurfrules",
        "rules_format": "plain_md",
        "skills_path": ".windsurf/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    "claude": {
        "mcp_path": None,
        "rules_path": ".claude/CLAUDE.md",
        "rules_format": "plain_md",
        "skills_path": ".claude/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    "opencode": {
        "mcp_path": None,
        "rules_path": "AGENTS.md",
        "rules_format": "plain_md",
        "skills_path": ".opencode/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    "roo": {
        "mcp_path": None,
        "rules_path": ".roo/rules/vibecollab.md",
        "rules_format": "plain_md",
        "skills_path": ".roo/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    "agents": {
        "mcp_path": None,
        "rules_path": "AGENTS.md",
        "rules_format": "plain_md",
        "skills_path": ".agents/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    # vx (https://github.com/loonghao/vx) also includes kiro, trae
    "kiro": {
        "mcp_path": None,
        "rules_path": ".kiro/rules/vibecollab.md",
        "rules_format": "plain_md",
        "skills_path": ".kiro/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
    "trae": {
        "mcp_path": None,
        "rules_path": ".trae/rules/vibecollab.md",
        "rules_format": "plain_md",
        "skills_path": ".trae/skills/vibecollab/SKILL.md",
        "skills_format": "skill_md",
    },
}


def list_platforms(with_mcp: Optional[bool] = None, with_rules: Optional[bool] = None) -> List[str]:
    """Return platform ids. If with_mcp=True, only those with mcp_path; if with_rules=True, only those with rules_path."""
    out = []
    for pid, p in PLATFORMS.items():
        if with_mcp is True and p.get("mcp_path") is None:
            continue
        if with_rules is True and p.get("rules_path") is None:
            continue
        out.append(pid)
    return sorted(out)


def get_platform(platform_id: str) -> Optional[Dict[str, Any]]:
    return PLATFORMS.get(platform_id)


def rules_path_for(root: Path, platform_id: str) -> Optional[Path]:
    p = get_platform(platform_id)
    if not p or not p.get("rules_path"):
        return None
    return root / p["rules_path"]


def skills_path_for(root: Path, platform_id: str) -> Optional[Path]:
    p = get_platform(platform_id)
    if not p or not p.get("skills_path"):
        return None
    return root / p["skills_path"]
