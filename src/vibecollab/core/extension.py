"""
LLMContext Extension - Extension mechanism processor

Extension = Process hooks + Context injection + Reference documents
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Context:
    """Context definition"""
    id: str
    type: str  # reference | template | computed | file_list
    source: Optional[str] = None       # type=reference
    section: Optional[str] = None      # type=reference
    inline_if_short: bool = True       # type=reference
    content: Optional[str] = None      # type=template
    from_path: Optional[str] = None    # type=computed
    transform: Optional[str] = None    # type=computed
    pattern: Optional[str] = None      # type=file_list
    description: Optional[str] = None


@dataclass
class Hook:
    """Hook definition"""
    trigger: str      # Trigger point
    action: str       # Action type
    context_id: Optional[str] = None
    condition: Optional[str] = None
    priority: int = 0


@dataclass
class Extension:
    """Extension definition"""
    domain: str
    hooks: List[Hook] = field(default_factory=list)
    contexts: Dict[str, Context] = field(default_factory=dict)
    additional_files: List[Dict] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    roles_override: List[Dict] = field(default_factory=list)


class ExtensionProcessor:
    """Extension processor"""

    # Supported trigger points
    TRIGGERS = {
        "dialogue.start",
        "dialogue.end",
        "qa.list_test_cases",
        "qa.acceptance",
        "dev.feature_complete",
        "dev.before_implement",
        "build.pre",
        "build.post",
        "milestone.review",
        "milestone.planning",
    }

    # Supported actions
    ACTIONS = {
        "inject_context",
        "append_checklist",
        "require_file_read",
        "update_file",
    }

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.extensions: Dict[str, Extension] = {}
        self._project_config: Dict[str, Any] = {}

    def load_extension(self, ext_data: Dict[str, Any], domain: str) -> Extension:
        """Load extension definition"""
        ext = Extension(domain=domain)

        # Load hooks
        for hook_data in ext_data.get("hooks", []):
            hook = Hook(
                trigger=hook_data.get("trigger", ""),
                action=hook_data.get("action", ""),
                context_id=hook_data.get("context_id"),
                condition=hook_data.get("condition"),
                priority=hook_data.get("priority", 0),
            )
            ext.hooks.append(hook)

        # Load contexts
        for ctx_id, ctx_data in ext_data.get("contexts", {}).items():
            ctx = Context(
                id=ctx_id,
                type=ctx_data.get("type", "template"),
                source=ctx_data.get("source"),
                section=ctx_data.get("section"),
                inline_if_short=ctx_data.get("inline_if_short", True),
                content=ctx_data.get("content"),
                from_path=ctx_data.get("from"),
                transform=ctx_data.get("transform"),
                pattern=ctx_data.get("pattern"),
                description=ctx_data.get("description"),
            )
            ext.contexts[ctx_id] = ctx

        # Load additional files
        ext.additional_files = ext_data.get("additional_files", [])

        # Load config
        ext.config = ext_data.get("config", {})

        self.extensions[domain] = ext
        return ext

    def load_from_config(self, config: Dict[str, Any]) -> None:
        """Load all extensions from project config"""
        self._project_config = config

        # Load roles_override (top-level)
        roles_override = config.get("roles_override", [])

        # Load domain_extensions
        domain_exts = config.get("domain_extensions", {}) or {}
        for domain, ext_data in domain_exts.items():
            if ext_data:  # Ensure ext_data is not None
                ext = self.load_extension(ext_data, domain)
                ext.roles_override = roles_override

    def get_hooks_for_trigger(self, trigger: str) -> List[Hook]:
        """Get all hooks for a trigger point, sorted by priority"""
        hooks = []
        for ext in self.extensions.values():
            for hook in ext.hooks:
                if hook.trigger == trigger:
                    hooks.append(hook)

        # Sort by priority descending
        return sorted(hooks, key=lambda h: h.priority, reverse=True)

    def evaluate_condition(self, condition: Optional[str], runtime_ctx: Dict[str, Any]) -> bool:
        """Evaluate condition expression"""
        if not condition:
            return True

        # Simple condition parser
        # Supports: files.exists('path'), project.has_feature('x'), project.domain == 'x'

        # files.exists('path')
        match = re.match(r"files\.exists\(['\"](.+)['\"]\)", condition)
        if match:
            file_path = self.project_root / match.group(1)
            return file_path.exists()

        # project.has_feature('x')
        match = re.match(r"project\.has_feature\(['\"](.+)['\"]\)", condition)
        if match:
            feature = match.group(1)
            features = self._project_config.get("project", {}).get("features", [])
            return feature in features

        # project.domain == 'x'
        match = re.match(r"project\.domain\s*==\s*['\"](.+)['\"]", condition)
        if match:
            target_domain = match.group(1)
            current_domain = self._project_config.get("project", {}).get("domain", "")
            return current_domain == target_domain

        # topic.relates_to('x') - needs runtime context
        match = re.match(r"topic\.relates_to\(['\"](.+)['\"]\)", condition)
        if match:
            topic = match.group(1)
            current_topic = runtime_ctx.get("topic", "")
            return topic.lower() in current_topic.lower()

        # Default return True (unknown conditions don't block execution)
        return True

    def resolve_context(self, ctx: Context, variables: Dict[str, Any]) -> str:
        """Resolve context content"""
        if ctx.type == "reference":
            return self._resolve_reference(ctx)
        elif ctx.type == "template":
            return self._resolve_template(ctx, variables)
        elif ctx.type == "file_list":
            return self._resolve_file_list(ctx)
        elif ctx.type == "computed":
            return self._resolve_computed(ctx, variables)
        return ""

    def _resolve_reference(self, ctx: Context) -> str:
        """Resolve reference type context"""
        if not ctx.source:
            return ""

        file_path = self.project_root / ctx.source
        if not file_path.exists():
            return f"<!-- Referenced file not found: {ctx.source} -->"

        content = file_path.read_text(encoding="utf-8")

        # If section is specified, extract that section
        if ctx.section:
            content = self._extract_section(content, ctx.section)

        # If content is short and inline is configured, return full content
        if ctx.inline_if_short and len(content) < 500:
            return content

        # Otherwise return reference hint
        return f"See `{ctx.source}`" + (f" -> {ctx.section}" if ctx.section else "")

    def _resolve_template(self, ctx: Context, variables: Dict[str, Any]) -> str:
        """Resolve template type context"""
        if not ctx.content:
            return ""

        content = ctx.content

        # Replace variables {variable_name}
        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", str(value))

        return content

    def _resolve_file_list(self, ctx: Context) -> str:
        """Resolve file list type context"""
        if not ctx.pattern:
            return ""

        files = list(self.project_root.glob(ctx.pattern))
        if not files:
            return f"<!-- No files matching {ctx.pattern} found -->"

        result = f"**{ctx.description or 'Related files'}**:\n"
        for f in files:
            result += f"- `{f.relative_to(self.project_root)}`\n"
        return result

    def _resolve_computed(self, ctx: Context, variables: Dict[str, Any]) -> str:
        """Resolve computed type context"""
        if not ctx.from_path:
            return ""

        # Get data from config
        data = self._get_nested_value(self._project_config, ctx.from_path)
        if data is None:
            return ""

        # Simple transform
        if isinstance(data, list):
            return "\n".join(f"- {item}" for item in data)
        return str(data)

    def _extract_section(self, content: str, section_header: str) -> str:
        """Extract a specific section from Markdown"""
        lines = content.split("\n")
        result = []
        in_section = False
        section_level = 0

        for line in lines:
            if line.strip().startswith("#"):
                # Check if this is the target section
                if section_header in line:
                    in_section = True
                    section_level = len(line) - len(line.lstrip("#"))
                    result.append(line)
                    continue
                # Check if we've left the target section
                elif in_section:
                    current_level = len(line) - len(line.lstrip("#"))
                    if current_level <= section_level:
                        break
            if in_section:
                result.append(line)

        return "\n".join(result)

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dict using dot-separated path"""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def process_trigger(
        self,
        trigger: str,
        runtime_ctx: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a trigger point, return list of actions to execute

        Args:
            trigger: Trigger point identifier
            runtime_ctx: Runtime context (e.g. current topic)
            variables: Template variables

        Returns:
            List of actions, each containing:
            - action: Action type
            - content: Content to inject (if any)
            - context_id: Context ID
            - source: Source extension
        """
        runtime_ctx = runtime_ctx or {}
        variables = variables or {}

        results = []
        hooks = self.get_hooks_for_trigger(trigger)

        for hook in hooks:
            # Evaluate condition
            if not self.evaluate_condition(hook.condition, runtime_ctx):
                continue

            result = {
                "action": hook.action,
                "context_id": hook.context_id,
            }

            # If context injection is needed, resolve content
            if hook.action == "inject_context" and hook.context_id:
                for ext in self.extensions.values():
                    if hook.context_id in ext.contexts:
                        ctx = ext.contexts[hook.context_id]
                        # Merge extension config into variables
                        merged_vars = {**ext.config, **variables}
                        result["content"] = self.resolve_context(ctx, merged_vars)
                        result["source"] = ext.domain
                        break

            results.append(result)

        return results

    def generate_extension_section(self, domain: str) -> str:
        """Generate extension section content for a domain"""
        if domain not in self.extensions:
            return ""

        ext = self.extensions[domain]
        content = f"""# Domain Extension: {domain.upper()}

## Extension Hooks

The following hooks are automatically triggered at specific process points:

| Trigger | Action | Condition | Context |
|---------|--------|-----------|---------|
"""
        for hook in ext.hooks:
            condition = hook.condition or "-"
            ctx_id = hook.context_id or "-"
            content += f"| `{hook.trigger}` | {hook.action} | {condition} | {ctx_id} |\n"

        content += """
## Available Contexts

"""
        for ctx_id, ctx in ext.contexts.items():
            desc = ctx.description or ""
            content += f"### {ctx_id}\n\n"
            content += f"- **Type**: {ctx.type}\n"
            if ctx.source:
                content += f"- **Source**: `{ctx.source}`\n"
            if desc:
                content += f"- **Description**: {desc}\n"
            content += "\n"

        return content


def load_extension_from_file(path: Path, project_root: Optional[Path] = None) -> ExtensionProcessor:
    """Load extension from YAML file"""
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    processor = ExtensionProcessor(project_root)
    processor.load_from_config(data)
    return processor
