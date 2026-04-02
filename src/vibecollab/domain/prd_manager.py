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
        """Load PRD from file (YAML-first, Markdown fallback)"""
        if not self.prd_path.exists():
            # Try YAML sibling (e.g. docs/prd.yaml when prd_path is docs/PRD.md)
            yaml_path = self.prd_path.parent / (self.prd_path.stem.lower() + ".yaml")
            if yaml_path.exists():
                self._load_yaml(yaml_path)
            return

        # If path ends with .yaml, load directly as YAML
        if self.prd_path.suffix in (".yaml", ".yml"):
            self._load_yaml(self.prd_path)
            return

        # Legacy: try YAML sibling first, then fall back to Markdown parsing
        yaml_path = self.prd_path.parent / (self.prd_path.stem.lower() + ".yaml")
        if yaml_path.exists():
            self._load_yaml(yaml_path)
            return

        try:
            content = self.prd_path.read_text(encoding="utf-8")
            # Legacy: Parse Markdown format PRD
            self._parse_markdown(content)
        except Exception:
            pass

    def _load_yaml(self, path: Path):
        """Load PRD from YAML file (schema v1)"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if data.get("kind") == "prd" and "requirements" in data:
                for req_data in data["requirements"]:
                    # Map YAML fields to Requirement dataclass
                    req = Requirement(
                        id=req_data.get("id", ""),
                        title=req_data.get("title", ""),
                        original_description=req_data.get("original_description", ""),
                        current_description=req_data.get("current_description"),
                        status=req_data.get("status", "draft"),
                        priority=req_data.get("priority", "medium"),
                        created_at=req_data.get("created_at", ""),
                        updated_at=req_data.get("updated_at", ""),
                        changes=req_data.get("change_history", []),
                    )
                    self.requirements[req.id] = req
            elif "requirements" in data:
                # Backward compatible: old YAML without kind field
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
        """Save PRD to YAML file (schema v1)"""
        data = self._generate_yaml_data()
        # Determine output path: prefer .yaml extension
        out_path = self.prd_path
        if out_path.suffix in (".md",):
            out_path = out_path.parent / (out_path.stem.lower() + ".yaml")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def save_markdown(self, output_path: Optional[Path] = None):
        """Render PRD as Markdown (view layer)"""
        content = self._generate_markdown()
        path = output_path or self.prd_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _generate_yaml_data(self) -> dict:
        """Generate YAML-serializable dict (schema v1)"""
        reqs = []
        for req in sorted(
            self.requirements.values(),
            key=lambda r: (
                {"draft": 0, "confirmed": 1, "in_progress": 2, "completed": 3, "cancelled": 4}.get(r.status, 5),
                r.created_at,
            ),
        ):
            req_data = {
                "id": req.id,
                "title": req.title,
                "original_description": req.original_description,
                "status": req.status,
                "priority": req.priority,
                "created_at": req.created_at,
                "updated_at": req.updated_at,
            }
            if req.current_description and req.current_description != req.original_description:
                req_data["current_description"] = req.current_description
            if req.changes:
                req_data["change_history"] = req.changes
            reqs.append(req_data)

        status_counts = {}
        for req in self.requirements.values():
            status_counts[req.status] = status_counts.get(req.status, 0) + 1

        return {
            "kind": "prd",
            "version": "1",
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
            "requirements": reqs,
            "statistics": {
                "draft": status_counts.get("draft", 0),
                "confirmed": status_counts.get("confirmed", 0),
                "in_progress": status_counts.get("in_progress", 0),
                "completed": status_counts.get("completed", 0),
                "cancelled": status_counts.get("cancelled", 0),
            },
        }

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
