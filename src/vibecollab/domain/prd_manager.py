"""
PRD Manager - Product Requirements Document Manager
Manages and tracks project requirements including original descriptions and change history
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class Requirement:
    """Requirement item"""
    id: str
    title: str
    original_description: str
    current_description: Optional[str] = None
    status: str = "draft"  # draft, confirmed, in_progress, completed, cancelled
    priority: str = "medium"  # high, medium, low
    created_at: str = ""
    updated_at: str = ""
    changes: List[Dict] = None  # Requirement change history

    def __post_init__(self):
        if self.changes is None:
            self.changes = []
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d")
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.current_description:
            self.current_description = self.original_description


class PRDManager:
    """PRD Manager"""

    def __init__(self, prd_path: Path):
        self.prd_path = Path(prd_path)
        self.requirements: Dict[str, Requirement] = {}
        self._load()

    def _load(self):
        """Load PRD from file"""
        if not self.prd_path.exists():
            return

        try:
            content = self.prd_path.read_text(encoding="utf-8")
            # Parse Markdown format PRD
            self._parse_markdown(content)
        except Exception:
            # If parsing fails, try loading as YAML (backward compatible)
            try:
                with open(self.prd_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "requirements" in data:
                        for req_data in data["requirements"]:
                            req = Requirement(**req_data)
                            self.requirements[req.id] = req
            except Exception:
                pass

    def _parse_markdown(self, content: str):
        """Parse Markdown format PRD"""
        lines = content.split("\n")
        current_req = None
        in_requirement = False

        for line in lines:
            # Detect requirement title (## REQ-XXX: Title)
            if line.startswith("## REQ-"):
                # Save previous requirement
                if current_req:
                    self.requirements[current_req.id] = current_req

                # Parse new requirement
                parts = line[2:].split(":", 1)
                req_id = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else ""

                current_req = Requirement(
                    id=req_id,
                    title=title,
                    original_description="",
                    created_at=datetime.now().strftime("%Y-%m-%d")
                )
                in_requirement = True
                continue

            if not in_requirement or not current_req:
                continue

            # Parse requirement content
            if line.startswith("**Original Description**:"):
                continue
            elif line.startswith("**Current Description**:"):
                continue
            elif line.startswith("**Status**:"):
                status = line.split(":", 1)[1].strip()
                current_req.status = status
            elif line.startswith("**Priority**:"):
                priority = line.split(":", 1)[1].strip()
                current_req.priority = priority
            elif line.startswith("**Created**:"):
                created_at = line.split(":", 1)[1].strip()
                current_req.created_at = created_at
            elif line.startswith("**Updated**:"):
                updated_at = line.split(":", 1)[1].strip()
                current_req.updated_at = updated_at
            elif line.strip().startswith(">") and not current_req.original_description:
                # Original description is usually in a blockquote
                current_req.original_description = line.strip()[1:].strip()
            elif line.strip() and not line.startswith("#") and not line.startswith("|"):
                # Plain text, possibly part of description
                if not current_req.original_description:
                    current_req.original_description = line.strip()
                elif not current_req.current_description or current_req.current_description == current_req.original_description:
                    current_req.current_description = line.strip()

        # Save last requirement
        if current_req:
            self.requirements[current_req.id] = current_req

    def add_requirement(self, title: str, description: str, priority: str = "medium") -> Requirement:
        """Add a new requirement

        Args:
            title: Requirement title
            description: Requirement description
            priority: Priority level

        Returns:
            Requirement: The created requirement object
        """
        # Generate requirement ID
        req_id = f"REQ-{len(self.requirements) + 1:03d}"

        req = Requirement(
            id=req_id,
            title=title,
            original_description=description,
            current_description=description,
            status="draft",
            priority=priority,
            created_at=datetime.now().strftime("%Y-%m-%d"),
            updated_at=datetime.now().strftime("%Y-%m-%d")
        )

        self.requirements[req_id] = req
        return req

    def update_requirement(self, req_id: str, new_description: str, change_reason: str = ""):
        """Update a requirement

        Args:
            req_id: Requirement ID
            new_description: New requirement description
            change_reason: Reason for change
        """
        if req_id not in self.requirements:
            raise ValueError(f"Requirement not found: {req_id}")

        req = self.requirements[req_id]
        old_description = req.current_description

        # Record change
        change_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "from": old_description,
            "to": new_description,
            "reason": change_reason
        }
        req.changes.append(change_entry)

        # Update requirement
        req.current_description = new_description
        req.updated_at = datetime.now().strftime("%Y-%m-%d")

    def set_status(self, req_id: str, status: str):
        """Set requirement status

        Args:
            req_id: Requirement ID
            status: New status
        """
        if req_id not in self.requirements:
            raise ValueError(f"Requirement not found: {req_id}")

        req = self.requirements[req_id]
        req.status = status
        req.updated_at = datetime.now().strftime("%Y-%m-%d")

    def save(self):
        """Save PRD to file"""
        content = self._generate_markdown()
        self.prd_path.parent.mkdir(parents=True, exist_ok=True)
        self.prd_path.write_text(content, encoding="utf-8")

    def _generate_markdown(self) -> str:
        """Generate Markdown format PRD"""
        lines = [
            "# Product Requirements Document (PRD)",
            "",
            "This document records the project's original requirements and change history.",
            "",
            "## Requirements List",
            ""
        ]

        # Sort by status and priority
        sorted_reqs = sorted(
            self.requirements.values(),
            key=lambda r: (
                {"draft": 0, "confirmed": 1, "in_progress": 2, "completed": 3, "cancelled": 4}.get(r.status, 5),
                {"high": 0, "medium": 1, "low": 2}.get(r.priority, 3),
                r.created_at
            )
        )

        for req in sorted_reqs:
            lines.append(f"## {req.id}: {req.title}")
            lines.append("")
            lines.append("**Original Description**:")
            lines.append(f"> {req.original_description}")
            lines.append("")

            if req.current_description != req.original_description:
                lines.append("**Current Description**:")
                lines.append(f"> {req.current_description}")
                lines.append("")

            lines.append(f"**Status**: {req.status}")
            lines.append(f"**Priority**: {req.priority}")
            lines.append(f"**Created**: {req.created_at}")
            lines.append(f"**Updated**: {req.updated_at}")
            lines.append("")

            if req.changes:
                lines.append("**Change History**:")
                lines.append("")
                for change in req.changes:
                    lines.append(f"- **{change['date']}**: {change['reason'] or 'Requirement updated'}")
                    if change['from'] != change['to']:
                        lines.append(f"  - From: {change['from'][:100]}...")
                        lines.append(f"  - To: {change['to'][:100]}...")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Add requirement statistics
        lines.append("## Requirement Statistics")
        lines.append("")
        status_counts = {}
        for req in self.requirements.values():
            status_counts[req.status] = status_counts.get(req.status, 0) + 1

        lines.append("| Status | Count |")
        lines.append("|------|------|")
        for status, count in sorted(status_counts.items()):
            lines.append(f"| {status} | {count} |")
        lines.append("")

        lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def get_requirement(self, req_id: str) -> Optional[Requirement]:
        """Get a requirement

        Args:
            req_id: Requirement ID

        Returns:
            Optional[Requirement]: The requirement object, or None if not found
        """
        return self.requirements.get(req_id)

    def list_requirements(self, status: Optional[str] = None) -> List[Requirement]:
        """List requirements

        Args:
            status: Optional status filter

        Returns:
            List[Requirement]: List of requirements
        """
        reqs = list(self.requirements.values())
        if status:
            reqs = [r for r in reqs if r.status == status]
        return sorted(reqs, key=lambda r: r.created_at)
