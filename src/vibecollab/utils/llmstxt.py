"""
LLMs.txt Integration - Integration with llms.txt standard
"""

import re
from pathlib import Path
from typing import Optional, Tuple


class LLMsTxtManager:
    """Manage llms.txt file detection, update, and creation"""

    AI_COLLAB_SECTION = """## AI Collaboration

- [AI Collaboration Guidelines](CONTRIBUTING_AI.md):
  Collaboration protocol, decision levels, task units, and workflow rules for AI-assisted development.
  This document defines how AI assistants should work with roles on this project.
"""

    @staticmethod
    def find_llmstxt(project_root: Path) -> Optional[Path]:
        """Find llms.txt file in the project"""
        llmstxt_path = project_root / "llms.txt"
        if llmstxt_path.exists():
            return llmstxt_path
        return None

    @staticmethod
    def has_ai_collab_section(content: str) -> bool:
        """Check if content already contains AI Collaboration section"""
        # Check for AI Collaboration related sections
        patterns = [
            r"##\s+AI\s+Collaboration",
            r"##\s+AI\s+.*[Cc]ollaboration",
            r"CONTRIBUTING_AI\.md",
            r"AI_COLLABORATION\.md",
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def find_insertion_point(content: str) -> int:
        """Find the best insertion point for AI Collaboration section"""
        lines = content.split("\n")

        # Prefer inserting after Documentation section
        for i, line in enumerate(lines):
            if re.match(r"^##\s+Documentation", line, re.IGNORECASE):
                # Find end of Documentation section
                for j in range(i + 1, len(lines)):
                    if re.match(r"^##\s+", lines[j]):
                        return j
                return len(lines)

        # If no Documentation section, insert at end
        return len(lines)

    @staticmethod
    def update_llmstxt(llmstxt_path: Path, contributing_ai_path: Path) -> bool:
        """Update existing llms.txt file, add AI Collaboration reference"""
        try:
            with open(llmstxt_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if already exists
            if LLMsTxtManager.has_ai_collab_section(content):
                return False  # Already exists, no update needed

            # Ensure reference path is correct (relative path)
            rel_path = contributing_ai_path.relative_to(llmstxt_path.parent)
            section = LLMsTxtManager.AI_COLLAB_SECTION.replace(
                "CONTRIBUTING_AI.md", str(rel_path)
            )

            # Find insertion point
            insert_pos = LLMsTxtManager.find_insertion_point(content)
            lines = content.split("\n")

            # Insert new section
            lines.insert(insert_pos, "")
            lines.insert(insert_pos + 1, section)

            # Write back
            with open(llmstxt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            return True
        except Exception as e:
            raise RuntimeError(f"Failed to update llms.txt: {e}")

    @staticmethod
    def create_llmstxt(
        project_root: Path,
        project_name: str,
        project_description: str,
        contributing_ai_path: Path,
    ) -> Path:
        """Create a new llms.txt file"""
        llmstxt_path = project_root / "llms.txt"

        # Ensure reference path is correct
        rel_path = contributing_ai_path.relative_to(project_root)

        content = f"""# {project_name}

> {project_description}

## Overview

This project uses AI-assisted development with structured collaboration protocols.

## Quick Start

See [AI Collaboration Guidelines]({rel_path}) for how to work with AI assistants on this project.

## AI Collaboration

- [AI Collaboration Guidelines]({rel_path}):
  Collaboration protocol, decision levels, task units, and workflow rules for AI-assisted development.
  This document defines how AI assistants should work with roles on this project.
"""

        with open(llmstxt_path, "w", encoding="utf-8") as f:
            f.write(content)

        return llmstxt_path

    @staticmethod
    def ensure_integration(
        project_root: Path,
        project_name: str,
        project_description: str,
        contributing_ai_path: Path,
    ) -> Tuple[bool, Optional[Path]]:
        """
        Ensure llms.txt integration is complete

        Returns:
            (is_updated, llmstxt_path):
                is_updated: Whether an update was made (True=updated/created, False=already exists)
                llmstxt_path: Path to llms.txt file
        """
        llmstxt_path = LLMsTxtManager.find_llmstxt(project_root)

        if llmstxt_path:
            # Exists, try to update
            updated = LLMsTxtManager.update_llmstxt(llmstxt_path, contributing_ai_path)
            return updated, llmstxt_path
        else:
            # Does not exist, create new
            new_path = LLMsTxtManager.create_llmstxt(
                project_root, project_name, project_description, contributing_ai_path
            )
            return True, new_path
