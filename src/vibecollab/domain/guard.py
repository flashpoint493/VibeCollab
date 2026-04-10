"""
Guard Protection Engine

Pre/post-action guard rules to prevent accidental file operations.
"""

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class GuardSeverity(str, Enum):
    """Guard severity levels"""

    BLOCK = "block"  # Prevent operation entirely
    WARN = "warn"  # Allow but warn
    ALLOW = "allow"  # Silent pass


@dataclass
class GuardRule:
    """A single guard rule configuration"""

    name: str
    pattern: str  # Glob pattern
    operations: List[str] = field(default_factory=list)  # create, modify, delete, move
    severity: GuardSeverity = GuardSeverity.BLOCK
    message: str = ""
    exclude_patterns: List[str] = field(default_factory=list)  # Patterns to exclude

    def matches(self, file_path: str) -> bool:
        """Check if file path matches this rule's pattern (excluding excluded patterns)"""
        # First check excludes — use simple substring matching for directory excludes
        for exclude in self.exclude_patterns:
            # Handle **/DirName/** patterns: check if directory name appears in path
            clean = exclude.strip("*/")
            if clean and (f"/{clean}/" in file_path or f"\\{clean}\\" in file_path
                         or file_path.startswith(f"{clean}/") or file_path.startswith(f"{clean}\\")):
                return False
            # Also try fnmatch
            if fnmatch.fnmatch(file_path, exclude):
                return False

        return self._pattern_matches(file_path, self.pattern)

    def _pattern_matches(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches a single glob pattern"""
        # Convert **/ to handle nested directories
        if pattern.startswith("**/"):
            suffix = pattern[3:]  # Remove **/
            if suffix.endswith("/**"):
                # Pattern like **/Library/** - matches any path containing Library/
                dir_name = suffix[:-3]  # Remove /**
                return f"/{dir_name}/" in file_path or file_path.startswith(f"{dir_name}/")
            elif suffix.startswith("*."):
                # Extension matching: **/*.meta matches any .meta file
                ext = suffix[1:]  # e.g., .meta
                return file_path.endswith(ext)
            else:
                # General suffix matching
                return file_path.endswith(suffix) or "/" + suffix in file_path
        elif "**/" in pattern:
            # Handle patterns like **/Library/**
            parts = pattern.split("**")
            if len(parts) == 2:
                prefix, suffix = parts
                prefix = prefix.rstrip("/")
                suffix = suffix.lstrip("/")
                if prefix and not file_path.startswith(prefix):
                    return False
                if suffix and suffix not in file_path:
                    return False
                return True

        return fnmatch.fnmatch(file_path, pattern)

    def applies_to(self, operation: str) -> bool:
        """Check if rule applies to given operation"""
        return not self.operations or operation in self.operations


@dataclass
class GuardCheckResult:
    """Result of a guard check"""

    allowed: bool
    rule: Optional[GuardRule] = None
    severity: Optional[GuardSeverity] = None
    message: str = ""


class GuardEngine:
    """Guard protection engine for file operations"""

    # Default guard rules — sensible defaults, can be overridden by guard.yaml
    DEFAULT_RULES = [
        GuardRule(
            name="meta_protection",
            pattern="**/*.meta",
            operations=["delete", "modify"],
            severity=GuardSeverity.WARN,  # v0.12.4: changed from BLOCK to WARN
            message="Meta files should not be manually edited. Use vibecollab commands instead.",
            exclude_patterns=[
                "Assets/Plugins/**",
                "Assets/Art/**",
                "Assets/Resources/**",
            ],
        ),
        GuardRule(
            name="library_protection",
            pattern="**/Library/**",
            operations=["delete"],
            severity=GuardSeverity.BLOCK,
            message="Library directory contains auto-generated files. Deletion not recommended.",
        ),
        GuardRule(
            name="insight_protection",
            pattern=".vibecollab/insights/*.jsonl",
            operations=["delete", "modify"],
            severity=GuardSeverity.BLOCK,
            message="Insight data files are managed automatically. Manual modification not allowed.",
        ),
        GuardRule(
            name="temp_warning",
            pattern="**/Temp/**",
            operations=["create"],
            severity=GuardSeverity.WARN,
            message="Consider using tmpfile API for temporary files",
        ),
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize guard engine

        Args:
            config: Guards configuration from project.yaml
        """
        self.rules: List[GuardRule] = []
        self.enabled = True

        # Load default rules
        self._load_default_rules()

        # Load custom rules from config (overrides same-name defaults)
        if config:
            self._load_config(config)

    def _load_default_rules(self):
        """Load default protection rules"""
        self.rules.extend(self.DEFAULT_RULES)

    def _load_config(self, config: Dict[str, Any]):
        """Load rules from project.yaml / guard.yaml configuration.

        Custom rules with the same name as a default rule will OVERRIDE
        the default (not append), so guard.yaml is the source of truth.
        """
        self.enabled = config.get("enabled", True)

        custom_rules = config.get("rules", [])
        for rule_data in custom_rules:
            name = rule_data.get("name", "unnamed")

            # Map guard.yaml 'action' field to severity
            action = rule_data.get("action", rule_data.get("severity", "block"))
            severity_map = {"warn": "warn", "block": "block", "allow": "allow", "ignore": "allow"}
            severity_str = severity_map.get(action, "block")

            # Build exclude patterns from guard.yaml exclude_paths
            exclude_patterns = rule_data.get("exclude_paths", [])

            rule = GuardRule(
                name=name,
                pattern=rule_data.get("pattern", rule_data.get("path_pattern", "**/*")),
                operations=rule_data.get("operations", []),
                severity=GuardSeverity(severity_str),
                message=rule_data.get("message", ""),
                exclude_patterns=exclude_patterns,
            )

            # Override same-name default rule instead of appending
            self.rules = [r for r in self.rules if r.name != name]
            self.rules.append(rule)

    def check_operation(self, operation: str, file_path: str) -> GuardCheckResult:
        """
        Check if an operation is allowed on a file

        Args:
            operation: Operation type (create, modify, delete, move)
            file_path: Target file path

        Returns:
            GuardCheckResult with allowed status and details
        """
        if not self.enabled:
            return GuardCheckResult(allowed=True)

        # Find matching rules
        matching_rules = [
            rule for rule in self.rules if rule.matches(file_path) and rule.applies_to(operation)
        ]

        if not matching_rules:
            return GuardCheckResult(allowed=True)

        # Find the most restrictive rule
        # Priority: BLOCK > WARN > ALLOW
        severity_priority = {GuardSeverity.BLOCK: 3, GuardSeverity.WARN: 2, GuardSeverity.ALLOW: 1}

        most_restrictive = max(matching_rules, key=lambda r: severity_priority.get(r.severity, 0))

        if most_restrictive.severity == GuardSeverity.BLOCK:
            return GuardCheckResult(
                allowed=False,
                rule=most_restrictive,
                severity=most_restrictive.severity,
                message=most_restrictive.message
                or f"Operation '{operation}' blocked by rule '{most_restrictive.name}'",
            )
        elif most_restrictive.severity == GuardSeverity.WARN:
            return GuardCheckResult(
                allowed=True,
                rule=most_restrictive,
                severity=most_restrictive.severity,
                message=most_restrictive.message
                or f"Warning: Operation '{operation}' matched rule '{most_restrictive.name}'",
            )
        else:
            return GuardCheckResult(allowed=True)

    def check_batch(self, operations: List[Dict[str, str]]) -> List[GuardCheckResult]:
        """
        Check multiple operations

        Args:
            operations: List of {operation, file_path} dicts

        Returns:
            List of GuardCheckResults
        """
        return [self.check_operation(op["operation"], op["file_path"]) for op in operations]

    def list_rules(self) -> List[GuardRule]:
        """List all configured guard rules"""
        return self.rules.copy()

    def test_path(self, file_path: str) -> List[GuardRule]:
        """
        Test which rules apply to a given path

        Args:
            file_path: Path to test

        Returns:
            List of matching rules
        """
        return [rule for rule in self.rules if rule.matches(file_path)]
