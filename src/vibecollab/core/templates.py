"""
LLMContext Templates - Template management
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class TemplateManager:
    """Template manager"""

    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir:
            self.templates_dir = templates_dir
        else:
            # Default to package templates directory
            self.templates_dir = self._get_package_templates_dir()

    def _get_package_templates_dir(self) -> Path:
        """Get package templates directory"""
        # Try to get from package resources
        try:
            # Python 3.9+
            import importlib.resources as pkg_resources
            ref = pkg_resources.files("llmcontext") / "templates"
            return Path(str(ref))
        except (ImportError, TypeError, AttributeError):
            pass

        # Fallback to relative path
        package_dir = Path(__file__).parent.parent  # core/ -> vibecollab/
        templates_dir = package_dir / "templates"

        if templates_dir.exists():
            return templates_dir

        # Try project root directory
        root_templates = package_dir.parent.parent / "templates"
        if root_templates.exists():
            return root_templates

        raise FileNotFoundError("Cannot find templates directory")

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        templates = []

        # Main templates
        for yaml_file in self.templates_dir.glob("*.yaml"):
            templates.append({
                "name": yaml_file.stem.replace(".project", ""),
                "type": "project",
                "path": yaml_file
            })

        # Domain extensions
        domains_dir = self.templates_dir / "domains"
        if domains_dir.exists():
            for yaml_file in domains_dir.glob("*.yaml"):
                templates.append({
                    "name": yaml_file.stem.replace(".extension", ""),
                    "type": "extension",
                    "path": yaml_file
                })

        return templates

    def get_template(self, name: str) -> str:
        """Get template content"""
        # Try main template
        template_path = self.templates_dir / f"{name}.project.yaml"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        # Try domain extension
        template_path = self.templates_dir / "domains" / f"{name}.extension.yaml"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        # Try without suffix
        template_path = self.templates_dir / f"{name}.yaml"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        raise FileNotFoundError(f"Template not found: {name}")

    def load_config(self, name: str) -> Dict[str, Any]:
        """Load and parse template config"""
        content = self.get_template(name)
        return yaml.safe_load(content)

    def save_template(self, name: str, config: Dict[str, Any], template_type: str = "project"):
        """Save custom template"""
        if template_type == "extension":
            template_path = self.templates_dir / "domains" / f"{name}.extension.yaml"
            template_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            template_path = self.templates_dir / f"{name}.project.yaml"

        with open(template_path, "w", encoding="utf-8") as f:
            yaml.dump(
                config,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )
