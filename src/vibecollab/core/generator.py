"""
LLMContext Generator -- Document generator.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .extension import ExtensionProcessor


class LLMContextGenerator:
    """AI collaboration protocol document generator.

    Uses PatternEngine (Jinja2 templates) to generate CONTRIBUTING_AI.md.
    """

    def __init__(self, config: Dict[str, Any], project_root: Optional[Path] = None):
        self.config = config
        self.project_root = project_root or Path.cwd()

        # Initialize extension processor
        self.extension_processor = ExtensionProcessor(self.project_root)
        self._load_extensions()

    def _load_extensions(self):
        """Load extension configurations."""
        # Load from domain_extensions
        if "domain_extensions" in self.config:
            self.extension_processor.load_from_config(self.config)

        # Load from standalone extension files (if specified)
        ext_files = self.config.get("extension_files", [])
        for ext_file in ext_files:
            ext_path = self.project_root / ext_file
            if ext_path.exists():
                import yaml as yaml_
                with open(ext_path, "r", encoding="utf-8") as f:
                    ext_data = yaml_.safe_load(f)
                self.extension_processor.load_from_config(ext_data)

    @classmethod
    def from_file(cls, path: Path, project_root: Optional[Path] = None) -> "LLMContextGenerator":
        """Load config from file."""
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        root = project_root or path.parent
        return cls(config, root)

    def validate(self) -> List[str]:
        """Validate config, return list of errors."""
        errors = []

        # Check required fields
        if "project" not in self.config:
            errors.append("Missing 'project' config")
        else:
            project = self.config["project"]
            if "name" not in project:
                errors.append("Missing 'project.name'")

        # Check role definitions
        roles = self.config.get("roles", [])
        for i, role in enumerate(roles):
            if "code" not in role:
                errors.append(f"Role {i} missing 'code'")
            if "name" not in role:
                errors.append(f"Role {i} missing 'name'")

        # Check decision levels
        levels = self.config.get("decision_levels", [])
        valid_levels = {"S", "A", "B", "C"}
        for level in levels:
            if level.get("level") not in valid_levels:
                errors.append(f"Invalid decision level: {level.get('level')}")

        return errors

    def generate(self) -> str:
        """Generate the complete CONTRIBUTING_AI.md document."""
        from .pattern_engine import PatternEngine
        engine = PatternEngine(self.config, self.project_root)
        return engine.render()
