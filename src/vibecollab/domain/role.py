"""
Multi-developer support module

Provides role identity recognition, context management, collaboration document generation, etc.
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .._compat import EMOJI as _EMOJI

# Local config file for storing current developer selection
LOCAL_CONFIG_FILE = ".vibecollab.local.yaml"


class RoleManager:
    """Role manager, responsible for identity recognition and directory management"""

    def __init__(self, project_root: Path, config: dict):
        """
        Initialize developer manager

        Args:
            project_root: Project root directory
            config: Project configuration (project.yaml)
        """
        self.project_root = project_root
        self.config = config
        self.role_context_config = config.get('role_context', config.get('multi_developer', {}))
        self.enabled = self.role_context_config.get('enabled', False)

        # Developer directory
        self.roles_dir = project_root / self.role_context_config.get('context', {}).get(
            'per_role_dir', 'docs/developers'
        )

    def get_current_role(self) -> str:
        """
        Get current role identity

        Priority order:
        1. Local config file (.vibecollab.local.yaml)
        2. Environment variable (VIBECOLLAB_ROLE)
        3. Primary strategy (git_username / system_user)
        4. Fallback strategy
        5. Default value

        Returns:
            Role identifier (normalized string)
        """
        identity_config = self.role_context_config.get('identity', {})
        primary = identity_config.get('primary', 'git_username')
        fallback = identity_config.get('fallback', 'system_user')
        normalize = identity_config.get('normalize', True)

        role_val = None

        # 1. First check local config file (set by CLI switch)
        local_role = self._get_local_role()
        if local_role:
            role_val = local_role

        # 2. Check environment variable
        if not role_val:
            role_val = os.environ.get('VIBECOLLAB_ROLE')

        # 3. Try primary strategy
        if not role_val:
            if primary == 'git_username':
                role_val = self._get_git_username()
            elif primary == 'system_user':
                role_val = self._get_system_user()
            elif primary == 'manual':
                # Manual mode already handled above
                pass

        # 4. Fall back to backup strategy
        if not role_val:
            if fallback == 'git_username':
                role_val = self._get_git_username()
            elif fallback == 'system_user':
                role_val = self._get_system_user()

        # 5. Final fallback: use default value
        if not role_val:
            role_val = 'unknown_role'

        # Normalize
        if normalize:
            developer = self._normalize_role_name(developer)

        return role_val

    def _get_local_role(self) -> Optional[str]:
        """Get role identity from local config file"""
        local_config_path = self.project_root / LOCAL_CONFIG_FILE
        if local_config_path.exists():
            try:
                with open(local_config_path, 'r', encoding='utf-8') as f:
                    local_config = yaml.safe_load(f) or {}
                    return local_config.get('current_role')
            except Exception:
                pass
        return None

    def switch_role(self, developer: str) -> bool:
        """
        Switch current role identity (persisted to local config file)

        Args:
            developer: Target role identifier

        Returns:
            Whether the switch was successful
        """
        identity_config = self.role_context_config.get('identity', {})
        normalize = identity_config.get('normalize', True)

        # Normalize developer name
        if normalize:
            developer = self._normalize_role_name(developer)

        local_config_path = self.project_root / LOCAL_CONFIG_FILE

        # Read existing config
        local_config = {}
        if local_config_path.exists():
            try:
                with open(local_config_path, 'r', encoding='utf-8') as f:
                    local_config = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Update developer
        local_config['current_role'] = developer
        local_config['switched_at'] = datetime.now().isoformat()

        # Write config
        try:
            with open(local_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(local_config, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception:
            return False

    def clear_switch(self) -> bool:
        """
        Clear developer switch setting, restore default identification strategy

        Returns:
            Whether the clear was successful
        """
        local_config_path = self.project_root / LOCAL_CONFIG_FILE

        if not local_config_path.exists():
            return True

        try:
            with open(local_config_path, 'r', encoding='utf-8') as f:
                local_config = yaml.safe_load(f) or {}

            # Remove developer settings
            if 'current_role' in local_config:
                del local_config['current_role']
            if 'switched_at' in local_config:
                del local_config['switched_at']

            # If config is empty, delete the file
            if not local_config:
                local_config_path.unlink()
            else:
                with open(local_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(local_config, f, allow_unicode=True, sort_keys=False)

            return True
        except Exception:
            return False

    def get_identity_source(self) -> str:
        """
        Get the source of the current role identity

        Returns:
            Identity source description
        """
        # Check local config
        if self._get_local_role():
            return "local_switch"

        # Check environment variable
        if os.environ.get('VIBECOLLAB_ROLE'):
            return "env_var"

        # Return primary strategy
        identity_config = self.role_context_config.get('identity', {})
        return identity_config.get('primary', 'git_username')

    def _get_git_username(self) -> Optional[str]:
        """Get username from Git config"""
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except BaseException:
            pass
        return None

    def _get_system_user(self) -> Optional[str]:
        """Get system username"""
        return os.environ.get('USER') or os.environ.get('USERNAME')

    def _normalize_role_name(self, name: str) -> str:
        """
        Normalize developer name

        Rules:
        - Convert to lowercase
        - Replace spaces with underscores
        - Remove special characters, keep only letters, digits, underscores

        Args:
            name: Original name

        Returns:
            Normalized name
        """
        # Convert to lowercase
        name = name.lower()
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        # Remove special characters
        name = re.sub(r'[^a-z0-9_]', '', name)
        return name

    def get_role_dir(self, developer: Optional[str] = None) -> Path:
        """
        Get developer's working directory

        Args:
            developer: Role identifier, None uses current developer

        Returns:
            Developer working directory path
        """
        if developer is None:
            developer = self.get_current_role()
        return self.roles_dir / developer

    def get_role_context_file(self, developer: Optional[str] = None) -> Path:
        """
        Get developer's CONTEXT.md file path

        Args:
            developer: Role identifier, None uses current developer

        Returns:
            CONTEXT.md file path
        """
        return self.get_role_dir(developer) / "CONTEXT.md"

    def get_role_metadata_file(self, developer: Optional[str] = None) -> Path:
        """
        Get developer's metadata file path

        Args:
            developer: Role identifier, None uses current developer

        Returns:
            Metadata file path
        """
        metadata_filename = self.role_context_config.get('context', {}).get(
            'metadata_file', '.metadata.yaml'
        )
        return self.get_role_dir(developer) / metadata_filename

    def list_roles(self) -> List[str]:
        """
        List all developers

        Returns:
            List of developer identifiers
        """
        if not self.roles_dir.exists():
            return []

        developers = []
        for item in self.roles_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                developers.append(item.name)

        return sorted(developers)

    def ensure_role_dir(self, developer: Optional[str] = None) -> Path:
        """
        Ensure developer directory exists, create if not

        Args:
            developer: Role identifier, None uses current developer

        Returns:
            Developer working directory path
        """
        dev_dir = self.get_role_dir(developer)
        dev_dir.mkdir(parents=True, exist_ok=True)
        return dev_dir

    def init_role_context(self, developer: Optional[str] = None, force: bool = False):
        """
        Initialize developer's context files

        Args:
            developer: Role identifier, None uses current developer
            force: Whether to force re-initialization (overwrite existing files)
        """
        if developer is None:
            developer = self.get_current_role()

        self.ensure_role_dir(developer)
        context_file = self.get_role_context_file(developer)
        metadata_file = self.get_role_metadata_file(developer)

        # Initialize CONTEXT.md
        if not context_file.exists() or force:
            project_name = self.config.get('project', {}).get('name', 'MyProject')
            project_version = self.config.get('project', {}).get('version', 'v1.0')

            context_content = f"""# {project_name} - {developer}'s Working Context

## Current Status
- **Version**: {project_version}
- **Developer**: {developer}
- **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Current Tasks
(No tasks yet)

## Recently Completed
(No records yet)

## Pending Issues
(No issues yet)

## Technical Debt
(No debt yet)

---
*This file is maintained by {developer}*
"""
            context_file.write_text(context_content, encoding='utf-8')

        # Initialize metadata
        if not metadata_file.exists() or force:
            metadata = {
                'developer': developer,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_updates': 0
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                yaml.dump(metadata, f, allow_unicode=True, sort_keys=False)

    def update_metadata(self, developer: Optional[str] = None):
        """
        Update developer's metadata

        Args:
            developer: Role identifier, None uses current developer
        """
        if developer is None:
            developer = self.get_current_role()

        metadata_file = self.get_role_metadata_file(developer)

        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f) or {}
        else:
            metadata = {
                'developer': developer,
                'created_at': datetime.now().isoformat(),
                'total_updates': 0
            }

        metadata['last_updated'] = datetime.now().isoformat()
        metadata['total_updates'] = metadata.get('total_updates', 0) + 1

        with open(metadata_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True, sort_keys=False)

    def get_role_status(self, developer: str) -> Dict:
        """
        Get developer's status information

        Args:
            developer: Role identifier

        Returns:
            Dictionary containing status information
        """
        context_file = self.get_role_context_file(developer)
        metadata_file = self.get_role_metadata_file(developer)

        status = {
            'developer': developer,
            'exists': context_file.exists(),
            'context_file': str(context_file),
            'last_updated': None,
            'total_updates': 0
        }

        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f) or {}
                status['last_updated'] = metadata.get('last_updated')
                status['total_updates'] = metadata.get('total_updates', 0)

        return status

    # ------------------------------------------------------------------
    # Tag system extension
    # ------------------------------------------------------------------

    def _read_metadata(self, developer: Optional[str] = None) -> Dict:
        """Read developer's metadata, returns dict (returns empty dict if not exists)"""
        if developer is None:
            developer = self.get_current_role()
        metadata_file = self.get_role_metadata_file(developer)
        if not metadata_file.exists():
            return {}
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _write_metadata(self, metadata: Dict, developer: Optional[str] = None) -> None:
        """Write developer's metadata"""
        if developer is None:
            developer = self.get_current_role()
        metadata_file = self.get_role_metadata_file(developer)
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True, sort_keys=False)

    def get_tags(self, developer: Optional[str] = None) -> List[str]:
        """Get developer's tag list"""
        meta = self._read_metadata(developer)
        return meta.get('tags', [])

    def set_tags(self, tags: List[str], developer: Optional[str] = None) -> None:
        """Set developer's tag list (full overwrite)"""
        meta = self._read_metadata(developer)
        meta['tags'] = tags
        self._write_metadata(meta, developer)

    def add_tag(self, tag: str, developer: Optional[str] = None) -> bool:
        """Add a tag (add if not duplicate, returns whether added)"""
        meta = self._read_metadata(developer)
        tags = meta.get('tags', [])
        if tag in tags:
            return False
        tags.append(tag)
        meta['tags'] = tags
        self._write_metadata(meta, developer)
        return True

    def remove_tag(self, tag: str, developer: Optional[str] = None) -> bool:
        """Remove a tag (remove if exists, returns whether removed)"""
        meta = self._read_metadata(developer)
        tags = meta.get('tags', [])
        if tag not in tags:
            return False
        tags.remove(tag)
        meta['tags'] = tags
        self._write_metadata(meta, developer)
        return True

    def get_contributed(self, developer: Optional[str] = None) -> List[str]:
        """Get list of insight IDs contributed by developer"""
        meta = self._read_metadata(developer)
        return meta.get('contributed', [])

    def add_contributed(self, insight_id: str, developer: Optional[str] = None) -> bool:
        """Record developer contributed an insight (add if not duplicate)"""
        meta = self._read_metadata(developer)
        contributed = meta.get('contributed', [])
        if insight_id in contributed:
            return False
        contributed.append(insight_id)
        meta['contributed'] = contributed
        self._write_metadata(meta, developer)
        return True

    def remove_contributed(self, insight_id: str, developer: Optional[str] = None) -> bool:
        """Remove a contributed record"""
        meta = self._read_metadata(developer)
        contributed = meta.get('contributed', [])
        if insight_id not in contributed:
            return False
        contributed.remove(insight_id)
        meta['contributed'] = contributed
        self._write_metadata(meta, developer)
        return True

    def get_bookmarks(self, developer: Optional[str] = None) -> List[str]:
        """Get list of insight IDs bookmarked by developer"""
        meta = self._read_metadata(developer)
        return meta.get('bookmarks', [])

    def add_bookmark(self, insight_id: str, developer: Optional[str] = None) -> bool:
        """Bookmark an insight (add if not duplicate)"""
        meta = self._read_metadata(developer)
        bookmarks = meta.get('bookmarks', [])
        if insight_id in bookmarks:
            return False
        bookmarks.append(insight_id)
        meta['bookmarks'] = bookmarks
        self._write_metadata(meta, developer)
        return True

    def remove_bookmark(self, insight_id: str, developer: Optional[str] = None) -> bool:
        """Remove a bookmarked insight"""
        meta = self._read_metadata(developer)
        bookmarks = meta.get('bookmarks', [])
        if insight_id not in bookmarks:
            return False
        bookmarks.remove(insight_id)
        meta['bookmarks'] = bookmarks
        self._write_metadata(meta, developer)
        return True


class ContextAggregator:
    """Context aggregator, responsible for generating global CONTEXT.md"""

    def __init__(self, project_root: Path, config: dict):
        """
        Initialize context aggregator

        Args:
            project_root: Project root directory
            config: Project configuration (project.yaml)
        """
        self.project_root = project_root
        self.config = config
        self.role_context_config = config.get('role_context', config.get('multi_developer', {}))
        self.developer_manager = RoleManager(project_root, config)

    def aggregate(self) -> str:
        """
        Aggregate all developers' contexts, generate global CONTEXT.md

        Returns:
            Aggregated global CONTEXT content
        """
        project_name = self.config.get('project', {}).get('name', 'MyProject')
        project_version = self.config.get('project', {}).get('version', 'v1.0')

        developers = self.developer_manager.list_roles()

        # Build global CONTEXT
        sections = []

        # Title and warning
        sections.append(f"# {project_name} Global Context")
        sections.append("")
        sections.append(f"> {_EMOJI['warning']} **This file is auto-generated, do not edit manually**")
        sections.append(f"> Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"> Aggregated from: {', '.join(developers) if developers else '(no developers)'}")
        sections.append("")

        # Project overall status
        sections.append("## Project Overall Status")
        sections.append(f"- **Version**: {project_version}")
        sections.append(f"- **Active roles**: {len(developers)} ({', '.join(developers)})")
        sections.append("")

        # Each developer's work status
        if developers:
            sections.append("## Role Work Status")
            sections.append("")

            for dev in developers:
                dev_status = self._extract_role_summary(dev)
                sections.append(f"### {dev}")
                sections.append(f"- **Last updated**: {dev_status['last_updated']}")
                sections.append(f"- **Current task**: {dev_status['current_task']}")
                sections.append(f"- **Progress**: {dev_status['progress']}")
                sections.append(f"- **Pending issues**: {dev_status['issues']}")
                sections.append(f"- **Next steps**: {dev_status['next_steps']}")
                sections.append("")
        else:
            sections.append("## Developer Status")
            sections.append("(No developers yet)")
            sections.append("")

        # Cross-developer dependencies (extracted from COLLABORATION.md)
        collaboration_info = self._extract_collaboration_info()
        if collaboration_info:
            sections.append("## Cross-developer Collaboration")
            sections.append(collaboration_info)
            sections.append("")

        # Global technical debt (merged from all developers)
        global_debts = self._merge_technical_debts(developers)
        if global_debts:
            sections.append("## Global Technical Debt")
            for debt in global_debts:
                sections.append(f"- {debt}")
            sections.append("")

        sections.append("---")
        sections.append("*This file is auto-aggregated from multi-role contexts*")

        return "\n".join(sections)

    def _extract_role_summary(self, developer: str) -> Dict:
        """
        Extract summary info from developer's CONTEXT.md

        Args:
            developer: Role identifier

        Returns:
            Summary info dictionary
        """
        context_file = self.developer_manager.get_role_context_file(developer)

        summary = {
            'last_updated': 'Unknown',
            'current_task': '(No tasks)',
            'progress': '(None)',
            'issues': '(None)',
            'next_steps': '(None)'
        }

        if not context_file.exists():
            return summary

        try:
            content = context_file.read_text(encoding='utf-8')

            # Extract last updated time
            if '上次更新' in content:
                match = re.search(r'上次更新.*?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
                if match:
                    summary['last_updated'] = match.group(1)
            elif 'Last Updated' in content:
                match = re.search(r'Last Updated.*?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
                if match:
                    summary['last_updated'] = match.group(1)

            # Extract current tasks (simple extraction of first non-empty line)
            for header in ('## Current Tasks', '## 当前任务'):
                if header in content:
                    task_section = re.search(rf'{re.escape(header)}\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
                    if task_section:
                        lines = [ln.strip() for ln in task_section.group(1).split('\n') if ln.strip() and not ln.strip().startswith('(')]
                        if lines:
                            summary['current_task'] = lines[0][:100]  # Limit length
                    break

            # Extract other info (simplified)
            # Can further refine extraction logic as needed

        except Exception:
            pass

        return summary

    def _extract_collaboration_info(self) -> Optional[str]:
        """
        Extract collaboration info from COLLABORATION.md

        Returns:
            Collaboration info string, or None if not available
        """
        collab_config = self.role_context_config.get('collaboration', {})
        collab_file_path = self.project_root / collab_config.get('file', 'docs/developers/COLLABORATION.md')

        if not collab_file_path.exists():
            return None

        try:
            collab_file_path.read_text(encoding='utf-8')
            # Extract key collaboration info (simplified)
            # Can parse task dependency matrices, etc.
            return "(See docs/developers/COLLABORATION.md for details)"
        except Exception:
            return None

    def _merge_technical_debts(self, developers: List[str]) -> List[str]:
        """
        Merge technical debts from all developers

        Args:
            developers: List of developers

        Returns:
            Technical debt list
        """
        debts = []

        for dev in developers:
            context_file = self.developer_manager.get_role_context_file(dev)
            if not context_file.exists():
                continue

            try:
                content = context_file.read_text(encoding='utf-8')
                for header in ('## Technical Debt', '## 技术债务'):
                    if header in content:
                        debt_section = re.search(rf'{re.escape(header)}\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
                        if debt_section:
                            lines = [ln.strip() for ln in debt_section.group(1).split('\n') if ln.strip() and ln.strip().startswith('-')]
                            for line in lines:
                                debts.append(f"[{dev}] {line}")
                        break
            except Exception:
                pass

        return debts

    def generate_and_save(self) -> Path:
        """
        Generate and save global CONTEXT.md

        Returns:
            Saved file path
        """
        context_config = self.role_context_config.get('context', {})
        output_file = self.project_root / context_config.get('aggregation_file', 'docs/CONTEXT.md')

        content = self.aggregate()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding='utf-8')

        return output_file


def migrate_to_role_context(project_root: Path, config: dict, developer_name: Optional[str] = None):
    """
    Migrate to role-based context mode

    Args:
        project_root: Project root directory
        config: Project configuration
        developer_name: Initial developer name, None for auto-detection
    """
    dm = RoleManager(project_root, config)

    if developer_name is None:
        developer_name = dm.get_current_role()

    # 1. Create developer directory
    dev_dir = dm.ensure_role_dir(developer_name)

    # 2. Move existing CONTEXT.md
    old_context = project_root / "docs" / "CONTEXT.md"
    new_context = dm.get_role_context_file(developer_name)

    if old_context.exists() and not new_context.exists():
        # Move file
        new_context.write_text(old_context.read_text(encoding='utf-8'), encoding='utf-8')

        # Backup original file
        backup = project_root / "docs" / "CONTEXT.md.backup"
        old_context.rename(backup)

    # 3. Initialize metadata
    dm.init_role_context(developer_name)

    # 4. Generate COLLABORATION.md
    collab_config = config.get('role_context', config.get('multi_developer', {})).get('collaboration', {})
    collab_file = project_root / collab_config.get('file', 'docs/developers/COLLABORATION.md')

    if not collab_file.exists():
        collab_content = f"""# Developer Collaboration Record

## Current Collaboration

(No collaboration records yet)

## Task Assignment Matrix

| Task | Owner | Collaborator | Status | Dependency |
|------|-------|--------------|--------|------------|
| - | {developer_name} | - | - | - |

## Handover Records

(No handover records yet)

---
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        collab_file.parent.mkdir(parents=True, exist_ok=True)
        collab_file.write_text(collab_content, encoding='utf-8')

    # 5. Generate new global aggregated CONTEXT.md
    aggregator = ContextAggregator(project_root, config)
    aggregator.generate_and_save()

    print(f"{_EMOJI['success']} Successfully migrated to role-based mode")
    print(f"   Developer: {developer_name}")
    print(f"   Context directory: {dev_dir}")
