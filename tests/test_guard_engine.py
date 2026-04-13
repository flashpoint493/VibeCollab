"""Tests for Guard Protection Engine"""

from vibecollab.domain.guard import GuardEngine, GuardRule, GuardSeverity


class TestGuardRule:
    """Test GuardRule class"""

    def test_matches_glob_pattern(self):
        """Test pattern matching with glob syntax"""
        rule = GuardRule(name="test", pattern="**/*.meta")

        assert rule.matches("test.meta") is True
        assert rule.matches("dir/test.meta") is True
        assert rule.matches("deep/nested/test.meta") is True
        assert rule.matches("test.txt") is False

    def test_applies_to_operation(self):
        """Test operation filtering"""
        rule = GuardRule(name="test", pattern="**/*", operations=["delete", "modify"])

        assert rule.applies_to("delete") is True
        assert rule.applies_to("modify") is True
        assert rule.applies_to("create") is False

    def test_applies_to_all_operations_when_empty(self):
        """When operations list is empty, applies to all"""
        rule = GuardRule(name="test", pattern="**/*", operations=[])

        assert rule.applies_to("delete") is True
        assert rule.applies_to("create") is True
        assert rule.applies_to("modify") is True


class TestGuardEngine:
    """Test GuardEngine class"""

    def test_default_rules_loaded(self):
        """Test that default rules are loaded"""
        engine = GuardEngine()

        rules = engine.list_rules()
        rule_names = [r.name for r in rules]

        assert "meta_protection" in rule_names
        assert "library_protection" in rule_names
        assert "insight_protection" in rule_names

    def test_check_operation_allows_safe_operations(self):
        """Test that safe operations are allowed"""
        engine = GuardEngine()

        result = engine.check_operation("create", "safe_file.txt")
        assert result.allowed is True

    def test_check_operation_warns_meta_delete(self):
        """Test that deleting .meta files shows warning (v0.12.4: changed from BLOCK to WARN)"""
        engine = GuardEngine()

        result = engine.check_operation("delete", "test.meta")
        assert result.allowed is True  # WARN allows the operation
        assert result.severity == GuardSeverity.WARN
        assert "meta" in result.message.lower()

    def test_check_operation_warns_meta_modify(self):
        """Test that modifying .meta files shows warning (v0.12.4: changed from BLOCK to WARN)"""
        engine = GuardEngine()

        result = engine.check_operation("modify", "test.meta")
        assert result.allowed is True  # WARN allows the operation
        assert result.severity == GuardSeverity.WARN

    def test_check_operation_allows_meta_create(self):
        """Test that creating .meta files is allowed"""
        engine = GuardEngine()

        result = engine.check_operation("create", "test.meta")
        assert result.allowed is True  # create not in operations list

    def test_check_operation_blocks_library_delete(self):
        """Test that deleting Library files is blocked"""
        engine = GuardEngine()

        result = engine.check_operation("delete", "Library/test.txt")
        assert result.allowed is False
        assert result.severity == GuardSeverity.BLOCK

    def test_check_batch_operations(self):
        """Test batch operation checking"""
        engine = GuardEngine()

        operations = [
            {"operation": "create", "file_path": "safe.txt"},
            {"operation": "delete", "file_path": "test.meta"},  # v0.12.4: WARN allows
            {"operation": "modify", "file_path": "normal.txt"},
        ]

        results = engine.check_batch(operations)

        assert len(results) == 3
        assert results[0].allowed is True
        assert results[1].allowed is True  # v0.12.4: WARN allows operation
        assert results[2].allowed is True

    def test_test_path_returns_matching_rules(self):
        """Test path rule matching"""
        engine = GuardEngine()

        matching = engine.test_path("test.meta")
        rule_names = [r.name for r in matching]

        assert "meta_protection" in rule_names

    def test_custom_rules_from_config(self):
        """Test loading custom rules from config"""
        config = {
            "enabled": True,
            "rules": [
                {
                    "name": "custom_rule",
                    "pattern": "**/*.secret",
                    "operations": ["read"],
                    "severity": "warn",
                    "message": "Secret file access",
                }
            ],
        }

        engine = GuardEngine(config)

        rule_names = [r.name for r in engine.list_rules()]
        assert "custom_rule" in rule_names

    def test_disabled_engine_allows_all(self):
        """Test that disabled engine allows all operations"""
        config = {"enabled": False}
        engine = GuardEngine(config)

        result = engine.check_operation("delete", "test.meta")
        assert result.allowed is True

    def test_warn_severity_allows_with_message(self):
        """Test that WARN severity allows but includes message"""
        config = {
            "enabled": True,
            "rules": [
                {
                    "name": "warn_rule",
                    "pattern": "**/temp/**",
                    "operations": ["create"],
                    "severity": "warn",
                    "message": "Consider using tmpfile",
                }
            ],
        }

        engine = GuardEngine(config)
        result = engine.check_operation("create", "temp/file.txt")

        assert result.allowed is True
        assert result.severity == GuardSeverity.WARN
        assert "tmpfile" in result.message
