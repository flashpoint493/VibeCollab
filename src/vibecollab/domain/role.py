"""
Role-based context management module

Provides role identity management, context isolation, and collaboration tracking.
Replaces the old DeveloperManager which was person-based.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .._compat import EMOJI as _EMOJI

# Local config file for storing current role selection
LOCAL_CONFIG_FILE = ".vibecollab.local.yaml"


class RoleManager:
    """Role manager, responsible for role identity and context management"""

    def __init__(self, project_root: Path, config: dict):
        """
        Initialize role manager

        Args:
            project_root: Project root directory
            config: Project configuration (project.yaml)
        """
        self.project_root = project_root
        self.config = config
        self.role_context_config = config.get("role_context", {})
        self.enabled = self.role_context_config.get("enabled", True)

        # Role directory
        self.roles_dir = project_root / self.role_context_config.get("context", {}).get(
            "per_role_dir", "docs/roles"
        )

    def get_current_role(self) -> str:
        """
        Get current role identity

        Priority order:
        1. Local config file (.vibecollab.local.yaml)
        2. Environment variable (VIBECOLLAB_ROLE)
        3. Configured current_role in project.yaml
        4. Default: first available role

        Returns:
            Role code (e.g., 'dev', 'insight_collector')
        """
        role = None

        # 1. First check local config file
        local_role = self._get_local_role()
        if local_role:
            role = local_role

        # 2. Check environment variable
        if not role:
            role = os.environ.get("VIBECOLLAB_ROLE")

        # 3. Use configured current_role
        if not role:
            role = self.role_context_config.get("current_role")

        # 4. Fallback to first available role
        if not role:
            roles = self.list_roles()
            if roles:
                role = roles[0]
            else:
                role = "dev"  # Ultimate fallback

        return role

    def _get_local_role(self) -> Optional[str]:
        """Get role from local config file"""
        local_config_path = self.project_root / LOCAL_CONFIG_FILE
        if local_config_path.exists():
            try:
                with open(local_config_path, "r", encoding="utf-8") as f:
                    local_config = yaml.safe_load(f) or {}
                return local_config.get("current_role")
            except Exception:
                pass
        return None

    def set_local_role(self, role: str) -> bool:
        """Set current role in local config"""
        local_config_path = self.project_root / LOCAL_CONFIG_FILE
        try:
            local_config = {}
            if local_config_path.exists():
                with open(local_config_path, "r", encoding="utf-8") as f:
                    local_config = yaml.safe_load(f) or {}

            local_config["current_role"] = role
            local_config["switched_at"] = datetime.now().isoformat()

            with open(local_config_path, "w", encoding="utf-8") as f:
                yaml.dump(local_config, f, allow_unicode=True)
            return True
        except Exception:
            return False

    def clear_switch(self) -> bool:
        """Clear role switch, restore default"""
        local_config_path = self.project_root / LOCAL_CONFIG_FILE
        try:
            if local_config_path.exists():
                with open(local_config_path, "r", encoding="utf-8") as f:
                    local_config = yaml.safe_load(f) or {}

                local_config.pop("current_role", None)
                local_config["cleared_at"] = datetime.now().isoformat()

                with open(local_config_path, "w", encoding="utf-8") as f:
                    yaml.dump(local_config, f, allow_unicode=True)
            return True
        except Exception:
            return False

    def list_roles(self) -> List[str]:
        """List all available roles"""
        assignments = self.role_context_config.get("role_assignments", [])
        return [a.get("role") for a in assignments if a.get("role")]

    def get_role_config(self, role: str) -> Optional[Dict]:
        """Get configuration for a specific role"""
        assignments = self.role_context_config.get("role_assignments", [])
        for assignment in assignments:
            if assignment.get("role") == role:
                return assignment
        return None

    def get_identity_source(self) -> str:
        """Get the source of current role identity"""
        local_config_path = self.project_root / LOCAL_CONFIG_FILE
        if local_config_path.exists():
            try:
                with open(local_config_path, "r", encoding="utf-8") as f:
                    local_config = yaml.safe_load(f) or {}
                if "current_role" in local_config:
                    return "local_switch"
            except Exception:
                pass

        if os.environ.get("VIBECOLLAB_ROLE"):
            return "env_var"

        if self.role_context_config.get("current_role"):
            return "config_default"

        return "fallback"

    def get_role_context_file(self, role: str) -> Path:
        """Get context file path for a role"""
        return self.roles_dir / role / "CONTEXT.md"

    def init_role_context(self, role: str) -> None:
        """Initialize context directory and file for a role"""
        role_dir = self.roles_dir / role
        role_dir.mkdir(parents=True, exist_ok=True)

        context_file = role_dir / "CONTEXT.md"
        if not context_file.exists():
            project_name = self.config.get("project", {}).get("name", "Project")
            today = datetime.now().strftime("%Y-%m-%d")

            content = f"""# {project_name} - {role} Context

## Current Status
- **Role**: {role}
- **Last Updated**: {today}
- **Status**: Active

## Current Tasks
(None)

## Pending Decisions
(None)

## Completed Items
(None)

## Role-Specific Configuration
{self._get_role_config_summary(role)}

---
*This file is auto-managed by VibeCollab*
"""
            context_file.write_text(content, encoding="utf-8")

    def _get_role_config_summary(self, role: str) -> str:
        """Get role configuration summary for context file"""
        role_config = self.get_role_config(role)
        if not role_config:
            return "(No specific configuration)"

        lines = []
        if role_config.get("description"):
            lines.append(f"**Description**: {role_config['description']}")
        if role_config.get("insights"):
            lines.append(f"**Associated Insights**: {', '.join(role_config['insights'])}")
        if role_config.get("preferences"):
            lines.append(f"**Preferences**: {role_config['preferences']}")

        return "\n".join(lines) if lines else "(No specific configuration)"

    def get_role_status(self, role: str) -> Dict:
        """Get status information for a role"""
        context_file = self.get_role_context_file(role)

        status = {
            "exists": context_file.exists(),
            "last_updated": None,
            "total_updates": 0,
            "raw_content": "",
        }

        if context_file.exists():
            try:
                content = context_file.read_text(encoding="utf-8")
                status["raw_content"] = content

                # Parse last updated
                for line in content.split("\n"):
                    if "**Last Updated**:" in line:
                        status["last_updated"] = line.split(":", 1)[1].strip()
                        break
            except Exception:
                pass

        return status

    def switch_role(self, role: str) -> bool:
        """Switch to a different role"""
        if role not in self.list_roles():
            return False

        # Initialize context if needed
        self.init_role_context(role)

        # Save switch
        return self.set_local_role(role)


class ContextAggregator:
    """Aggregate context from multiple roles into global context"""

    def __init__(self, project_root: Path, config: dict):
        self.project_root = project_root
        self.config = config
        self.role_manager = RoleManager(project_root, config)

    def generate_and_save(self) -> Path:
        """Generate global aggregated context"""
        aggregation_config = self.config.get("role_context", {}).get("context", {})
        output_file = self.project_root / aggregation_config.get(
            "aggregation_file", "docs/CONTEXT.md"
        )

        content = self._aggregate_content()
        output_file.write_text(content, encoding="utf-8")
        return output_file

    def _aggregate_content(self) -> str:
        """Generate aggregated context content"""
        project_name = self.config.get("project", {}).get("name", "Project")
        today = datetime.now().strftime("%Y-%m-%d")

        roles = self.role_manager.list_roles()
        current_role = self.role_manager.get_current_role()

        lines = [
            f"# {project_name} - Global Context",
            "",
            f"> ⚠️ **This file is auto-generated, do not edit manually**",
            f"> Last updated: {today}",
            f"> Current role: {current_role}",
            f"> Active roles: {', '.join(roles)}",
            "",
            "## Active Roles",
            "",
        ]

        for role in roles:
            status = self.role_manager.get_role_status(role)
            is_current = " (current)" if role == current_role else ""
            status_emoji = _EMOJI["success"] if status["exists"] else _EMOJI["warning"]
            lines.append(f"- {status_emoji} **{role}**{is_current}")

        lines.extend(
            [
                "",
                "## Cross-Role Collaboration",
                "(See docs/roles/COLLABORATION.md for details)",
                "",
                "---",
                "*This file is auto-aggregated from role contexts*",
            ]
        )

        return "\n".join(lines)


# Backward compatibility alias
DeveloperManager = RoleManager
