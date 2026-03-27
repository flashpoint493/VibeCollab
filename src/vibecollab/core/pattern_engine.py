"""
Pattern Engine -- Jinja2-based CONTRIBUTING_AI.md template rendering engine.

Externalizes the original 27 hardcoded _add_*() methods from generator.py
into independent .md.j2 template files, driven by manifest.yaml for section
ordering and conditional switches.

Backward compatible: LLMContextGenerator.generate() internally calls
PatternEngine; the external API remains unchanged.

Template Overlay:
  Users can create a .vibecollab/patterns/ directory at the project root
  with custom templates and manifest.yaml.
  - Custom templates take priority over built-in ones (same-name override)
  - Custom manifest.yaml can add/override/exclude sections
  - Merge strategy: merge by section id; local entries override built-in
"""

import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, select_autoescape

# Built-in patterns directory (within package)
PATTERNS_DIR = Path(__file__).parent.parent / "patterns"

# User local custom template directory (relative to project_root)
LOCAL_PATTERNS_SUBDIR = Path(".vibecollab") / "patterns"


class PatternEngine:
    """Jinja2-driven protocol document rendering engine.

    Supports template overlay: users can place custom .md.j2 templates
    and/or manifest.yaml under {project_root}/.vibecollab/patterns/
    to override/extend built-in templates.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        project_root: Optional[Path] = None,
        patterns_dir: Optional[Path] = None,
    ):
        self.config = config
        self.project_root = project_root or Path.cwd()
        self.patterns_dir = patterns_dir or PATTERNS_DIR

        # Detect user local patterns directory
        self.local_patterns_dir: Optional[Path] = None
        local_candidate = self.project_root / LOCAL_PATTERNS_SUBDIR
        if local_candidate.is_dir():
            self.local_patterns_dir = local_candidate

        # Load and merge manifest
        self.manifest = self._load_manifest()

        # Jinja2 environment -- ChoiceLoader for local-first resolution
        loaders = []
        if self.local_patterns_dir:
            loaders.append(FileSystemLoader(str(self.local_patterns_dir)))
        loaders.append(FileSystemLoader(str(self.patterns_dir)))

        self.env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape([]),
            keep_trailing_newline=True,
            trim_blocks=False,
            lstrip_blocks=False,
        )
        # Register custom filters
        self.env.filters["join_list"] = _filter_join_list
        self.env.filters["format_review"] = _filter_format_review
        self.env.filters["quote_list"] = _filter_quote_list

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Render the complete CONTRIBUTING_AI.md document."""
        sections: List[str] = []

        for entry in self.manifest.get("sections", []):
            template_file = entry["template"]
            condition = entry.get("condition")

            # Condition check
            if condition and not self._evaluate_condition(condition):
                continue

            template = self.env.get_template(template_file)
            ctx = self._build_context(entry)
            rendered = template.render(**ctx)

            if rendered.strip():
                sections.append(rendered)

        return "\n".join(sections)

    def list_patterns(self) -> List[Dict[str, Any]]:
        """List all registered patterns (with overlay source annotation)."""
        result = []
        for entry in self.manifest.get("sections", []):
            info = {
                "id": entry.get("id", ""),
                "template": entry["template"],
                "description": entry.get("description", ""),
                "condition": entry.get("condition"),
            }
            # Annotate template source
            if self.local_patterns_dir:
                local_tmpl = self.local_patterns_dir / entry["template"]
                info["source"] = "local" if local_tmpl.is_file() else "builtin"
            else:
                info["source"] = "builtin"
            result.append(info)
        return result

    @property
    def has_local_overlay(self) -> bool:
        """Whether user local template overlay is enabled."""
        return self.local_patterns_dir is not None

    # ------------------------------------------------------------------
    # Manifest loading & merging
    # ------------------------------------------------------------------

    def _load_manifest(self) -> Dict[str, Any]:
        """Load manifest with local overlay merge support.

        Merge strategy:
        1. Load built-in manifest.yaml as the base
        2. If local manifest.yaml exists, merge by section id:
           - Same id: local entry overrides built-in entry
           - New local id: insert at position (via 'after' field) or append
           - Local exclude list: exclude specified section ids
        """
        # Load built-in manifest
        builtin_path = self.patterns_dir / "manifest.yaml"
        with open(builtin_path, "r", encoding="utf-8") as f:
            builtin_manifest = yaml.safe_load(f) or {}

        if not self.local_patterns_dir:
            return builtin_manifest

        # Check local manifest
        local_manifest_path = self.local_patterns_dir / "manifest.yaml"
        if not local_manifest_path.is_file():
            return builtin_manifest

        with open(local_manifest_path, "r", encoding="utf-8") as f:
            local_manifest = yaml.safe_load(f) or {}

        return self._merge_manifests(builtin_manifest, local_manifest)

    @staticmethod
    def _merge_manifests(
        builtin: Dict[str, Any],
        local: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge built-in manifest and local manifest.

        Local manifest supported fields:
        - sections: section list, merged by id with built-in
        - exclude: list of section ids to exclude
        """
        result = copy.deepcopy(builtin)
        builtin_sections = result.get("sections", [])

        # Exclude list
        exclude_ids = set(local.get("exclude", []))
        if exclude_ids:
            builtin_sections = [
                s for s in builtin_sections if s.get("id") not in exclude_ids
            ]

        # Build id -> index mapping
        id_to_idx = {s.get("id"): i for i, s in enumerate(builtin_sections)}

        # Merge local sections
        local_sections = local.get("sections", [])
        append_sections = []

        for local_entry in local_sections:
            sid = local_entry.get("id")
            if sid and sid in id_to_idx:
                # Override: replace built-in entry with local entry
                builtin_sections[id_to_idx[sid]] = local_entry
            else:
                # New: check 'after' field for insert position
                after_id = local_entry.get("after")
                if after_id and after_id in id_to_idx:
                    insert_idx = id_to_idx[after_id] + 1
                    builtin_sections.insert(insert_idx, local_entry)
                    # Rebuild index
                    id_to_idx = {
                        s.get("id"): i for i, s in enumerate(builtin_sections)
                    }
                else:
                    append_sections.append(local_entry)

        # Append sections without specified position (before footer)
        if append_sections:
            footer_idx = id_to_idx.get("footer")
            if footer_idx is not None:
                for i, s in enumerate(append_sections):
                    builtin_sections.insert(footer_idx + i, s)
            else:
                builtin_sections.extend(append_sections)

        result["sections"] = builtin_sections
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_context(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Build template rendering context."""
        ctx: Dict[str, Any] = {
            "config": self.config,
            "project": self.config.get("project", {}),
            "now": datetime.now(),
        }

        # Expand common config sections to top-level for template convenience
        for key in [
            "philosophy", "roles", "decision_levels", "task_unit",
            "dialogue_protocol", "requirement_clarification",
            "git_workflow", "testing", "milestone", "iteration",
            "version_review", "build", "quick_acceptance",
            "prompt_engineering", "confirmed_decisions",
            "contributing_ai_changelog", "documentation",
            "role_context", "protocol_check", "prd_management",
            "symbology", "domain_extensions",
        ]:
            ctx[key] = self.config.get(key, {} if key not in (
                "roles", "decision_levels", "confirmed_decisions",
                "contributing_ai_changelog",
            ) else [])

        # Extension processor context
        ctx["extensions"] = self._get_extensions_context()

        return ctx

    def _get_extensions_context(self) -> Dict[str, Any]:
        """Get extension info for template rendering."""
        from .extension import ExtensionProcessor
        processor = ExtensionProcessor(self.project_root)

        # Load from domain_extensions
        if "domain_extensions" in self.config:
            processor.load_from_config(self.config)

        # Load from standalone extension files
        ext_files = self.config.get("extension_files", [])
        for ext_file in ext_files:
            ext_path = self.project_root / ext_file
            if ext_path.exists():
                with open(ext_path, "r", encoding="utf-8") as f:
                    ext_data = yaml.safe_load(f)
                processor.load_from_config(ext_data)

        return {
            "has_extensions": bool(processor.extensions),
            "extensions": processor.extensions,
        }

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate manifest condition expression.

        Supported conditions:
        - "config.role_context.enabled" -> self.config["role_context"]["enabled"]
        - "config.protocol_check.enabled|true" -> default True (when key missing)
        - "config.testing.product_qa.enabled" -> ...
        - "has_extensions" -> whether extensions are loaded
        - "config.symbology" -> symbology is non-empty
        """
        if condition == "has_extensions":
            ctx = self._get_extensions_context()
            return ctx["has_extensions"]

        if condition.startswith("config."):
            # Support "|default" syntax: "config.x.enabled|true"
            default_val = None
            expr = condition[len("config."):]
            if "|" in expr:
                expr, default_str = expr.split("|", 1)
                default_val = default_str.strip().lower() in ("true", "1", "yes")

            parts = expr.split(".")
            val = self.config
            for part in parts:
                if isinstance(val, dict):
                    val = val.get(part)
                else:
                    return default_val if default_val is not None else False
                if val is None:
                    return default_val if default_val is not None else False

            # Bool returns directly; non-empty collection/dict returns True
            if isinstance(val, bool):
                return val
            if isinstance(val, (dict, list)):
                return bool(val)
            return bool(val)

        return True


# ------------------------------------------------------------------
# Jinja2 custom filters
# ------------------------------------------------------------------

def _filter_join_list(value, separator=", "):
    """Join a list with the specified separator."""
    if isinstance(value, list):
        return separator.join(str(v) for v in value)
    return str(value)


def _filter_quote_list(value, separator=", "):
    """Quote each element and join with separator."""
    if isinstance(value, list):
        return separator.join(f'"{v}"' for v in value)
    return str(value)


def _filter_format_review(review: Dict) -> str:
    """Format review requirement description."""
    if not isinstance(review, dict):
        return str(review)
    if not review.get("required", False):
        if review.get("mode") == "auto":
            return "AI suggests, human can quickly confirm or auto-approve"
        return "AI decides autonomously, adjustable afterwards"

    if review.get("mode") == "sync":
        return "Must be manually confirmed, record decision rationale"
    elif review.get("mode") == "async":
        return "Human review, async confirmation allowed"
    return "Review required"
