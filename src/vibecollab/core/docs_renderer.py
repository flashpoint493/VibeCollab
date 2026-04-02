"""
Docs Renderer - Convert YAML documents to Markdown views

This module provides functionality to render YAML document files (docs/*.yaml)
to human-readable Markdown views (docs/*.md).
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jinja2 import Environment, TemplateNotFound


class DocsRenderer:
    """Render YAML documents to Markdown views

    Core principle: YAML is source of truth → Markdown is a generated view.
    """

    # Mapping of YAML kind to template names
    KIND_TEMPLATES = {
        "context": ("context.yaml", "context.md"),
        "decisions": ("decisions.yaml", "decisions.md"),
        "changelog": ("changelog.yaml", "changelog.md"),
        "roadmap": ("roadmap.yaml", "roadmap.md"),
        "prd": ("prd.yaml", "prd.md"),
        "qa": ("qa.yaml", "qa.md"),
    }

    # Output file names for each kind
    KIND_OUTPUT_FILES = {
        "context": "CONTEXT.md",
        "decisions": "DECISIONS.md",
        "changelog": "CHANGELOG.md",
        "roadmap": "ROADMAP.md",
        "prd": "PRD.md",
        "qa": "QA_TEST_CASES.md",
    }

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize the renderer

        Args:
            templates_dir: Directory containing Jinja2 templates.
                          If None, uses package default templates.
        """
        if templates_dir:
            self.templates_dir = templates_dir
        else:
            # Default to package templates directory
            package_dir = Path(__file__).parent.parent  # core/ -> vibecollab/
            self.templates_dir = package_dir / "templates" / "docs"

        self.jinja_env = Environment(loader=self._create_loader())

    def _create_loader(self):
        """Create a Jinja2 loader for templates"""
        from jinja2 import FileSystemLoader

        return FileSystemLoader(str(self.templates_dir))

    def list_renderable_docs(self, docs_dir: Path) -> list[Dict[str, Any]]:
        """List all YAML documents that can be rendered in the docs directory

        Args:
            docs_dir: Path to docs directory

        Returns:
            List of dicts with 'yaml_path', 'kind', 'output_name' keys
        """
        results = []
        if not docs_dir.exists():
            return results

        for yaml_file in docs_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data or not isinstance(data, dict):
                    continue

                kind = data.get("kind")
                if kind in self.KIND_OUTPUT_FILES:
                    results.append(
                        {
                            "yaml_path": yaml_file,
                            "kind": kind,
                            "output_name": self.KIND_OUTPUT_FILES[kind],
                            "version": data.get("version", "unknown"),
                        }
                    )
            except Exception:
                continue  # Skip files that can't be parsed

        return results

    def render_doc(self, yaml_path: Path, output_path: Optional[Path] = None) -> Path:
        """Render a single YAML document to Markdown

        Args:
            yaml_path: Path to YAML document
            output_path: Output path for Markdown (optional, auto-detected if None)

        Returns:
            Path to generated Markdown file
        """
        # Load YAML data
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or not isinstance(data, dict):
            raise ValueError(f"Invalid YAML file: {yaml_path}")

        kind = data.get("kind")
        if not kind:
            raise ValueError(f"YAML file missing 'kind' field: {yaml_path}")

        # Determine output path
        if output_path is None:
            docs_dir = yaml_path.parent
            output_filename = self.KIND_OUTPUT_FILES.get(kind)
            if not output_filename:
                raise ValueError(f"Unknown document kind: {kind}")
            output_path = docs_dir / output_filename

        # Get template name
        template_info = self.KIND_TEMPLATES.get(kind)
        if not template_info:
            raise ValueError(f"No template configured for kind: {kind}")

        _, md_template_name = template_info
        template_file = f"{md_template_name}.j2"

        # Load and render template
        try:
            template = self.jinja_env.get_template(template_file)
        except TemplateNotFound:
            raise ValueError(f"Template not found: {template_file}")

        # Add metadata for template
        template_context = dict(data)
        template_context.setdefault("today", self._get_today())
        template_context.setdefault("project_name", self._get_project_name(yaml_path))

        # Render
        markdown = template.render(**template_context)

        # Write output
        output_path.write_text(markdown, encoding="utf-8")
        return output_path

    def render_all(self, docs_dir: Path, kinds: Optional[list[str]] = None) -> Dict[str, Path]:
        """Render all YAML documents in a directory

        Args:
            docs_dir: Path to docs directory
            kinds: Optional list of kinds to render (render all if None)

        Returns:
            Dict mapping kind to output path
        """
        results = {}
        renderable = self.list_renderable_docs(docs_dir)

        for doc_info in renderable:
            kind = doc_info["kind"]
            if kinds and kind not in kinds:
                continue

            yaml_path = doc_info["yaml_path"]
            output_path = docs_dir / doc_info["output_name"]

            try:
                rendered_path = self.render_doc(yaml_path, output_path)
                results[kind] = rendered_path
            except Exception as e:
                # Continue with other docs even if one fails
                results[kind] = e

        return results

    def _get_today(self) -> str:
        """Get current date in YYYY-MM-DD format"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d")

    def _get_project_name(self, yaml_path: Path) -> str:
        """Try to get project name from project.yaml"""
        project_dir = yaml_path.parent.parent
        project_yaml = project_dir / "project.yaml"

        if project_yaml.exists():
            try:
                with open(project_yaml, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                return config.get("project", {}).get("name", "Project")
            except Exception:
                pass

        return "Project"

    def validate_doc(self, yaml_path: Path) -> tuple[bool, list[str]]:
        """Validate a YAML document structure

        Args:
            yaml_path: Path to YAML document

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return False, [f"YAML syntax error: {e}"]
        except Exception as e:
            return False, [f"Failed to read file: {e}"]

        if not data:
            return False, ["File is empty"]

        if not isinstance(data, dict):
            return False, ["Root must be a dictionary"]

        # Check required fields
        if "kind" not in data:
            errors.append("Missing required field: 'kind'")
        elif data["kind"] not in self.KIND_TEMPLATES:
            errors.append(f"Unknown kind: '{data['kind']}'")

        if "version" not in data:
            errors.append("Missing recommended field: 'version'")

        return len(errors) == 0, errors
