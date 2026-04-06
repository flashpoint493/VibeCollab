"""
Template Library - FP-005 Document Template Library

Manages document templates for the VibeCollab Pattern Engine:
- Built-in YAML-native templates via manifest.yaml
- User custom templates in .vibecollab/templates/
- Jinja2 variable substitution
"""

import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Built-in docs templates directory
BUILTIN_DOCS_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "docs"

# User local custom templates directory (relative to project_root)
LOCAL_TEMPLATES_SUBDIR = Path(".vibecollab") / "templates"


class TemplateLibrary:
    """Document Template Library manager.

    Provides access to built-in and user-custom document templates.
    Templates are YAML-native Jinja2 templates for generating project documents.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.builtin_dir = BUILTIN_DOCS_TEMPLATES_DIR

        # Load built-in manifest
        self.manifest = self._load_builtin_manifest()

        # Detect and load user local templates
        self.local_dir: Optional[Path] = None
        self.local_templates: Dict[str, Dict[str, Any]] = {}
        self._load_local_templates()

    def _load_builtin_manifest(self) -> Dict[str, Any]:
        """Load built-in template manifest."""
        manifest_path = self.builtin_dir / "manifest.yaml"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_local_templates(self):
        """Load user custom templates from .vibecollab/templates/."""
        local_candidate = self.project_root / LOCAL_TEMPLATES_SUBDIR
        if not local_candidate.is_dir():
            return

        self.local_dir = local_candidate

        # Load all .yaml.j2 files from local templates directory
        for template_file in self.local_dir.glob("*.yaml.j2"):
            template_id = template_file.stem.replace(".yaml", "").replace(".j2", "")
            self.local_templates[template_id] = {
                "id": template_id,
                "template": template_file.name,
                "path": template_file,
                "type": "custom",
                "source": "local",
            }

            # Try to extract description from template content
            try:
                content = template_file.read_text(encoding="utf-8")
                # Look for comment at the start
                if content.startswith("#"):
                    first_line = content.split("\n")[0]
                    desc = first_line.lstrip("# ").strip()
                    self.local_templates[template_id]["description"] = desc
            except Exception:
                pass

    def list_templates(
        self,
        category: Optional[str] = None,
        include_builtin: bool = True,
        include_custom: bool = True,
    ) -> List[Dict[str, Any]]:
        """List all available templates.

        Args:
            category: Filter by category (core, configuration, collaboration, domain)
            include_builtin: Include built-in templates
            include_custom: Include user custom templates

        Returns:
            List of template info dictionaries
        """
        templates = []

        # Add built-in templates from manifest
        if include_builtin and self.manifest:
            # Core templates
            for tpl in self.manifest.get("core_templates", []):
                tpl_info = copy.deepcopy(tpl)
                tpl_info["type"] = "core"
                tpl_info["source"] = "builtin"
                tpl_info["category"] = "core"
                templates.append(tpl_info)

            # Config templates
            for tpl in self.manifest.get("config_templates", []):
                tpl_info = copy.deepcopy(tpl)
                tpl_info["type"] = "config"
                tpl_info["source"] = "builtin"
                tpl_info["category"] = self._get_template_category(tpl["id"])
                templates.append(tpl_info)

        # Add custom templates
        if include_custom:
            for tpl_id, tpl_info in self.local_templates.items():
                templates.append(copy.deepcopy(tpl_info))

        # Filter by category if specified
        if category:
            templates = [t for t in templates if t.get("category") == category]

        return templates

    def _get_template_category(self, template_id: str) -> str:
        """Get category for a built-in template."""
        categories = self.manifest.get("categories", {})
        for cat, ids in categories.items():
            if template_id in ids:
                return cat
        return "configuration"

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template info by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template info dict or None if not found
        """
        # Check custom templates first (override built-in)
        if template_id in self.local_templates:
            return copy.deepcopy(self.local_templates[template_id])

        # Check built-in templates
        all_builtin = self.manifest.get("core_templates", []) + self.manifest.get(
            "config_templates", []
        )
        for tpl in all_builtin:
            if tpl.get("id") == template_id:
                tpl_info = copy.deepcopy(tpl)
                tpl_info["type"] = (
                    "core" if tpl in self.manifest.get("core_templates", []) else "config"
                )
                tpl_info["source"] = "builtin"
                tpl_info["category"] = self._get_template_category(template_id)
                return tpl_info

        return None

    def get_template_path(self, template_id: str) -> Optional[Path]:
        """Get the file path for a template.

        Args:
            template_id: Template identifier

        Returns:
            Path to template file or None if not found
        """
        # Check custom templates first
        if template_id in self.local_templates:
            return self.local_templates[template_id]["path"]

        # Check built-in templates
        tpl_info = self.get_template(template_id)
        if tpl_info and tpl_info.get("source") == "builtin":
            template_file = tpl_info.get("template")
            if template_file:
                return self.builtin_dir / template_file

        return None

    def use_template(
        self,
        template_id: str,
        output_path: Path,
        variables: Optional[Dict[str, Any]] = None,
        project_config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """Use a template to generate a document.

        Args:
            template_id: Template to use
            output_path: Where to write the generated document
            variables: Variables to substitute in the template
            project_config: Project configuration for template context

        Returns:
            Tuple of (success, message)
        """
        template_path = self.get_template_path(template_id)
        if not template_path:
            return False, f"Template not found: {template_id}"

        if not template_path.exists():
            return False, f"Template file not found: {template_path}"

        try:
            # Read template content
            template_content = template_path.read_text(encoding="utf-8")

            # Setup Jinja2 environment
            env = Environment(
                loader=FileSystemLoader(str(template_path.parent)),
                autoescape=select_autoescape([]),
                keep_trailing_newline=True,
                trim_blocks=False,
                lstrip_blocks=False,
            )

            template = env.from_string(template_content)

            # Build context
            ctx = self._build_context(variables, project_config)

            # Render template
            rendered = template.render(**ctx)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            output_path.write_text(rendered, encoding="utf-8")

            return True, f"Generated: {output_path}"

        except Exception as e:
            return False, f"Template rendering failed: {e}"

    def _build_context(
        self,
        variables: Optional[Dict[str, Any]],
        project_config: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build template rendering context."""
        today = datetime.now().strftime("%Y-%m-%d")

        ctx: Dict[str, Any] = {
            "today": today,
            "now": datetime.now(),
            "config": project_config or {},
            "project": (project_config or {}).get("project", {}),
            "vars": variables or {},
        }

        # Add common variables
        if variables:
            for key, value in variables.items():
                if key not in ctx:
                    ctx[key] = value

        # Add project config sections
        if project_config:
            for key in [
                "philosophy",
                "roles",
                "decision_levels",
                "task_unit",
                "dialogue_protocol",
                "requirement_clarification",
                "git_workflow",
                "testing",
                "milestone",
                "iteration",
                "version_review",
                "build",
                "quick_acceptance",
                "prompt_engineering",
                "confirmed_decisions",
                "contributing_ai_changelog",
                "documentation",
                "role_context",
                "protocol_check",
                "prd_management",
                "symbology",
                "domain_extensions",
            ]:
                ctx[key] = project_config.get(
                    key,
                    {}
                    if key
                    not in (
                        "roles",
                        "decision_levels",
                        "confirmed_decisions",
                        "contributing_ai_changelog",
                    )
                    else [],
                )

        return ctx

    def validate_template(self, template_id: str) -> Tuple[bool, List[str]]:
        """Validate a template can be loaded and rendered.

        Args:
            template_id: Template to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        template_path = self.get_template_path(template_id)
        if not template_path:
            return False, [f"Template not found: {template_id}"]

        errors = []

        try:
            # Try to read the file
            content = template_path.read_text(encoding="utf-8")

            # Try to parse as Jinja2 template
            env = Environment(autoescape=select_autoescape([]))
            try:
                env.from_string(content)
            except Exception as e:
                errors.append(f"Template syntax error: {e}")

        except Exception as e:
            errors.append(f"Failed to read template: {e}")

        return len(errors) == 0, errors

    def get_custom_templates_dir(self) -> Path:
        """Get the path to custom templates directory (creating if needed)."""
        custom_dir = self.project_root / LOCAL_TEMPLATES_SUBDIR
        custom_dir.mkdir(parents=True, exist_ok=True)
        return custom_dir

    def create_custom_template(
        self,
        template_id: str,
        description: str = "",
        template_content: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Create a new custom template.

        Custom templates can override built-in templates of the same ID.

        Args:
            template_id: Identifier for the new template
            description: Template description
            template_content: Optional initial content

        Returns:
            Tuple of (success, message)
        """
        # Validate template_id
        if not template_id.replace("_", "").replace("-", "").isalnum():
            return False, "Template ID must be alphanumeric with underscores/hyphens only"

        # Check if a custom template with same ID already exists
        if template_id in self.local_templates:
            return False, f"Custom template '{template_id}' already exists"

        # Create template file (can override built-in)
        custom_dir = self.get_custom_templates_dir()
        template_file = custom_dir / f"{template_id}.yaml.j2"

        if template_content is None:
            template_content = f"""# {description or f"Custom template: {template_id}"}
kind: {template_id}
version: "1"
updated_at: "{{{{ today }}}}"

# Add your template content here
# Available variables: today, now, config, project, vars
"""

        try:
            template_file.write_text(template_content, encoding="utf-8")
            # Reload local templates
            self._load_local_templates()
            return True, f"Created template: {template_file}"
        except Exception as e:
            return False, f"Failed to create template: {e}"

    def list_categories(self) -> List[str]:
        """List all template categories."""
        return ["core", "configuration", "collaboration", "domain", "custom"]

    def get_stats(self) -> Dict[str, int]:
        """Get template library statistics."""
        builtin_count = len(self.manifest.get("core_templates", [])) + len(
            self.manifest.get("config_templates", [])
        )
        custom_count = len(self.local_templates)

        return {
            "builtin": builtin_count,
            "custom": custom_count,
            "total": builtin_count + custom_count,
        }
