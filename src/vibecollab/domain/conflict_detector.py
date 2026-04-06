"""
Cross-role conflict detection module

Provides conflict detection capabilities in role-based collaboration.
"""

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

from .._compat import EMOJI as _COMPAT_EMOJI
from .._compat import is_windows_gbk

USE_EMOJI = not is_windows_gbk()

EMOJI_MAP = _COMPAT_EMOJI


class ConflictType:
    """Conflict type enum"""

    FILE = "file"  # File conflict
    TASK = "task"  # Task conflict
    DEPENDENCY = "dependency"  # Dependency conflict
    NAMING = "naming"  # Naming conflict


class Conflict:
    """Conflict object"""

    def __init__(
        self,
        conflict_type: str,
        severity: str,
        roles: List[str],
        description: str,
        details: Optional[Dict] = None,
    ):
        """
        Initialize conflict object

        Args:
            conflict_type: Conflict type (file/task/dependency/naming)
            severity: Severity level (high/medium/low)
            roles: List of involved roles
            description: Conflict description
            details: Detail info (optional)
        """
        self.type = conflict_type
        self.severity = severity
        self.roles = roles
        self.description = description
        self.details = details or {}
        self.detected_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dict format"""
        return {
            "type": self.type,
            "severity": self.severity,
            "roles": self.roles,
            "description": self.description,
            "details": self.details,
            "detected_at": self.detected_at.isoformat(),
        }

    def __str__(self) -> str:
        """String representation"""
        devs = ", ".join(self.roles)
        return f"[{self.severity.upper()}] {self.type}: {self.description} (roles: {devs})"


class ConflictDetector:
    """Cross-role conflict detector"""

    def __init__(self, project_root: Path, config: dict):
        """
        Initialize conflict detector

        Args:
            project_root: Project root directory
            config: Project configuration
        """
        self.project_root = project_root
        self.config = config
        self.role_context_config = config.get("multi_developer", {})

        # Developer directory (isolated in .vibecollab/ to avoid project conflicts)
        self.roles_dir = project_root / self.role_context_config.get("context", {}).get(
            "per_role_dir", ".vibecollab/roles"
        )

        # Cache
        self._role_contexts = {}
        self._collaboration_data = None
        self._git_changed_files = {}

    def detect_all_conflicts(
        self, target_role: Optional[str] = None, between_roles: Optional[Tuple[str, str]] = None
    ) -> List[Conflict]:
        """
        Detect all types of conflicts

        Args:
            target_role: Target developer (None to detect current developer)
            between_roles: Detect conflicts between two specific developers

        Returns:
            List of conflicts
        """
        conflicts = []

        # Load data
        self._load_role_contexts()
        self._load_collaboration_data()
        self._load_git_changes()

        # Determine developer scope to check
        if between_roles:
            dev1, dev2 = between_roles
            if dev1 not in self._role_contexts or dev2 not in self._role_contexts:
                return conflicts
            check_pairs = [(dev1, dev2)]
        elif target_role:
            if target_role not in self._role_contexts:
                return conflicts
            other_devs = [d for d in self._role_contexts.keys() if d != target_role]
            check_pairs = [(target_role, other) for other in other_devs]
        else:
            # Detect conflicts among all developers
            devs = list(self._role_contexts.keys())
            check_pairs = [
                (devs[i], devs[j]) for i in range(len(devs)) for j in range(i + 1, len(devs))
            ]

        # Execute conflict detection for each type
        for dev1, dev2 in check_pairs:
            conflicts.extend(self._detect_file_conflicts(dev1, dev2))
            conflicts.extend(self._detect_task_conflicts(dev1, dev2))
            conflicts.extend(self._detect_naming_conflicts(dev1, dev2))

        # Detect dependency conflicts (global, not limited to pairwise)
        conflicts.extend(self._detect_dependency_conflicts())

        return conflicts

    def _load_role_contexts(self):
        """Load all developer contexts"""
        if not self.roles_dir.exists():
            return

        for dev_dir in self.roles_dir.iterdir():
            if not dev_dir.is_dir() or dev_dir.name.startswith("."):
                continue

            developer = dev_dir.name
            context_file = dev_dir / "CONTEXT.md"
            metadata_file = dev_dir / ".metadata.yaml"

            if context_file.exists():
                context_content = context_file.read_text(encoding="utf-8")

                # Extract key info
                current_tasks = self._extract_current_tasks(context_content)
                recent_work = self._extract_section_content(context_content, "Recently Completed")
                issues = self._extract_section_content(context_content, "Pending Issues")

                metadata = {}
                if metadata_file.exists():
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = yaml.safe_load(f) or {}

                self._role_contexts[developer] = {
                    "tasks": current_tasks,
                    "recent_work": recent_work,
                    "issues": issues,
                    "metadata": metadata,
                    "raw_content": context_content,
                }

    def _load_collaboration_data(self):
        """Load collaboration document data"""
        collab_config = self.role_context_config.get("collaboration", {})
        collab_file = self.project_root / collab_config.get("file", "docs/roles/COLLABORATION.md")

        if not collab_file.exists():
            self._collaboration_data = {"tasks": {}, "dependencies": {}}
            return

        content = collab_file.read_text(encoding="utf-8")

        # Parse task assignment matrix
        tasks = {}
        task_pattern = (
            r"\| (TASK-[A-Z]+-\d+)[:\s]([^\|]+) \| ([^\|]+) \| ([^\|]*) \| ([^\|]+) \| ([^\|]+) \|"
        )
        for match in re.finditer(task_pattern, content):
            task_id = match.group(1).strip()
            task_name = match.group(2).strip()
            owner = match.group(3).strip()
            collaborators = match.group(4).strip()
            status = match.group(5).strip()
            dependencies = match.group(6).strip()

            tasks[task_id] = {
                "name": task_name,
                "owner": owner,
                "collaborators": [
                    c.strip() for c in collaborators.split(",") if c.strip() and c.strip() != "-"
                ],
                "status": status,
                "dependencies": [
                    d.strip() for d in dependencies.split(",") if d.strip() and d.strip() != "-"
                ],
            }

        self._collaboration_data = {"tasks": tasks}

    def _load_git_changes(self):
        """Load Git changed files (inferred from each developer's CONTEXT)"""
        # Simplified: extract file paths from the "Recently Completed" section of CONTEXT.md
        for developer, ctx_data in self._role_contexts.items():
            recent = ctx_data.get("recent_work", "")

            # Extract possible file paths (simple regex)
            file_patterns = re.findall(r"`([^\`]+\.[a-z]{2,4})`", recent)
            self._git_changed_files[developer] = set(file_patterns)

    def _detect_file_conflicts(self, dev1: str, dev2: str) -> List[Conflict]:
        """Detect file conflicts"""
        conflicts = []

        files1 = self._git_changed_files.get(dev1, set())
        files2 = self._git_changed_files.get(dev2, set())

        common_files = files1 & files2

        if common_files:
            conflicts.append(
                Conflict(
                    conflict_type=ConflictType.FILE,
                    severity="medium",
                    roles=[dev1, dev2],
                    description="Modified the same files simultaneously",
                    details={"files": list(common_files)},
                )
            )

        return conflicts

    def _detect_task_conflicts(self, dev1: str, dev2: str) -> List[Conflict]:
        """Detect task conflicts"""
        conflicts = []

        tasks1 = self._role_contexts.get(dev1, {}).get("tasks", [])
        tasks2 = self._role_contexts.get(dev2, {}).get("tasks", [])

        # Detect similar task descriptions (simple string matching)
        for task1 in tasks1:
            for task2 in tasks2:
                similarity = self._calculate_similarity(task1, task2)
                if similarity > 0.6:  # 60% similarity threshold
                    conflicts.append(
                        Conflict(
                            conflict_type=ConflictType.TASK,
                            severity="high",
                            roles=[dev1, dev2],
                            description="Possible duplicate or overlapping tasks",
                            details={
                                f"{dev1}_task": task1,
                                f"{dev2}_task": task2,
                                "similarity": similarity,
                            },
                        )
                    )

        return conflicts

    def _detect_dependency_conflicts(self) -> List[Conflict]:
        """Detect dependency conflicts (circular deps, inconsistent deps)"""
        conflicts = []

        tasks = self._collaboration_data.get("tasks", {})

        # Build dependency graph
        dep_graph = defaultdict(set)
        for task_id, task_data in tasks.items():
            for dep in task_data.get("dependencies", []):
                dep_graph[task_id].add(dep)

        # Detect circular dependencies (depth-first search)
        visited = set()
        rec_stack = set()

        def has_cycle(node, path):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path + [neighbor]):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle = path[path.index(neighbor) :] + [neighbor]
                    conflicts.append(
                        Conflict(
                            conflict_type=ConflictType.DEPENDENCY,
                            severity="high",
                            roles=self._get_roles_for_tasks(cycle),
                            description="Circular dependency detected",
                            details={"cycle": " → ".join(cycle)},
                        )
                    )
                    return True

            rec_stack.remove(node)
            return False

        for task_id in dep_graph.keys():
            if task_id not in visited:
                has_cycle(task_id, [task_id])

        return conflicts

    def _detect_naming_conflicts(self, dev1: str, dev2: str) -> List[Conflict]:
        """Detect naming conflicts (function names, class names, etc.)"""
        conflicts = []

        # Extract possible names from CONTEXT (simplified)
        ctx1 = self._role_contexts.get(dev1, {}).get("raw_content", "")
        ctx2 = self._role_contexts.get(dev2, {}).get("raw_content", "")

        # Extract class/function names from code blocks
        names1 = self._extract_code_names(ctx1)
        names2 = self._extract_code_names(ctx2)

        common_names = names1 & names2

        if common_names:
            conflicts.append(
                Conflict(
                    conflict_type=ConflictType.NAMING,
                    severity="low",
                    roles=[dev1, dev2],
                    description="Using identical naming",
                    details={"names": list(common_names)},
                )
            )

        return conflicts

    def _extract_current_tasks(self, content: str) -> List[str]:
        """Extract current tasks from CONTEXT"""
        tasks = []

        # Extract "Current Tasks" section
        section = self._extract_section_content(content, "Current Tasks")

        # Extract list items
        lines = section.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                task = line.lstrip("-*").strip()
                if task and not task.startswith("("):
                    tasks.append(task)

        return tasks

    def _extract_section_content(self, content: str, section_header: str) -> str:
        """Extract content of a specified section from Markdown"""
        pattern = rf"##\s+{re.escape(section_header)}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()
        return ""

    def _extract_code_names(self, content: str) -> Set[str]:
        """Extract code names (class names, function names, etc.) from content"""
        names = set()

        # Extract code blocks
        code_blocks = re.findall(r"```[a-z]*\n(.*?)\n```", content, re.DOTALL)

        for code in code_blocks:
            # Extract class names (class ClassName)
            class_names = re.findall(r"class\s+([A-Z][a-zA-Z0-9_]*)", code)
            names.update(class_names)

            # Extract function names (def function_name or function functionName)
            func_names = re.findall(r"(?:def|function)\s+([a-z_][a-zA-Z0-9_]*)", code)
            names.update(func_names)

        return names

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (simple Jaccard similarity)"""
        if not str1 or not str2:
            return 0.0

        # Convert to lowercase and tokenize
        words1 = set(re.findall(r"\w+", str1.lower()))
        words2 = set(re.findall(r"\w+", str2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _get_roles_for_tasks(self, task_ids: List[str]) -> List[str]:
        """Get developers associated with tasks"""
        tasks = self._collaboration_data.get("tasks", {})
        developers = set()

        for task_id in task_ids:
            task = tasks.get(task_id, {})
            owner = task.get("owner", "")
            if owner:
                developers.add(owner)

        return list(developers)

    def generate_conflict_report(self, conflicts: List[Conflict], verbose: bool = False) -> str:
        """
        Generate conflict report

        Args:
            conflicts: List of conflicts
            verbose: Whether to include details

        Returns:
            Report text
        """
        if not conflicts:
            return f"{EMOJI_MAP['success']} No conflicts detected"

        lines = []
        lines.append(f"{EMOJI_MAP['warning']} Detected {len(conflicts)} potential conflicts\n")

        # Group by severity
        by_severity = defaultdict(list)
        for conflict in conflicts:
            by_severity[conflict.severity].append(conflict)

        severity_order = ["high", "medium", "low"]
        severity_icons = {
            "high": EMOJI_MAP["high"],
            "medium": EMOJI_MAP["medium"],
            "low": EMOJI_MAP["low"],
        }

        for severity in severity_order:
            items = by_severity.get(severity, [])
            if not items:
                continue

            lines.append(
                f"\n{severity_icons[severity]} {severity.upper()} priority ({len(items)} items):"
            )
            lines.append("-" * 60)

            for i, conflict in enumerate(items, 1):
                devs = ", ".join(conflict.roles)
                lines.append(f"{i}. [{conflict.type.upper()}] {conflict.description}")
                lines.append(f"   Roles: {devs}")

                if verbose and conflict.details:
                    lines.append("   Details:")
                    for key, value in conflict.details.items():
                        lines.append(f"     - {key}: {value}")

                lines.append("")

        lines.append("\n" + "=" * 60)
        lines.append(f"{EMOJI_MAP['idea']} Suggestions:")
        lines.append("  1. Communicate with relevant developers to clarify division of work")
        lines.append("  2. Update COLLABORATION.md to record collaboration decisions")
        lines.append("  3. Consider task reassignment or merging")

        return "\n".join(lines)
