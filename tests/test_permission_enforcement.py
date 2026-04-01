"""
Tests for TaskManager permission enforcement via RoleManager integration.

Covers: create_task permission check, transition permission check,
        backward compatibility when role_manager is None.
"""

from unittest import mock

import pytest

from vibecollab.domain.task_manager import TaskManager, TaskStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project directory."""
    (tmp_path / ".vibecollab").mkdir()
    return tmp_path


@pytest.fixture
def mock_role_manager():
    """Create a mock RoleManager with configurable permissions."""
    rm = mock.MagicMock()
    # Default: allow everything
    rm.can_create_task_for.return_value = True
    rm.can_transition_to.return_value = True
    return rm


@pytest.fixture
def mgr_with_perms(tmp_project, mock_role_manager):
    """TaskManager with RoleManager for permission checking."""
    return TaskManager(
        project_root=tmp_project,
        role_manager=mock_role_manager,
    )


@pytest.fixture
def mgr_without_perms(tmp_project):
    """TaskManager without RoleManager (backward compatible)."""
    return TaskManager(project_root=tmp_project)


# ---------------------------------------------------------------------------
# Backward compatibility (no RoleManager)
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_create_task_without_role_manager(self, mgr_without_perms):
        """TaskManager works normally without RoleManager."""
        task = mgr_without_perms.create_task(
            id="TASK-DEV-001", role="DEV", feature="Test feature",
            actor="anyone",
        )
        assert task.id == "TASK-DEV-001"

    def test_transition_without_role_manager(self, mgr_without_perms):
        """Transition works without RoleManager."""
        mgr_without_perms.create_task(
            id="TASK-DEV-001", role="DEV", feature="Test",
        )
        result = mgr_without_perms.transition(
            "TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="anyone",
        )
        assert result.ok is True


# ---------------------------------------------------------------------------
# create_task permission enforcement
# ---------------------------------------------------------------------------

class TestCreateTaskPermissions:
    def test_allowed_create(self, mgr_with_perms, mock_role_manager):
        """Create succeeds when RoleManager allows it."""
        mock_role_manager.can_create_task_for.return_value = True
        task = mgr_with_perms.create_task(
            id="TASK-DEV-001", role="DEV", feature="Test",
            actor="dev",
        )
        assert task.id == "TASK-DEV-001"
        mock_role_manager.can_create_task_for.assert_called_once_with(
            "DEV", developer="dev",
        )

    def test_denied_create(self, mgr_with_perms, mock_role_manager):
        """Create raises PermissionError when denied."""
        mock_role_manager.can_create_task_for.return_value = False
        with pytest.raises(PermissionError, match="Permission denied"):
            mgr_with_perms.create_task(
                id="TASK-PM-001", role="PM", feature="Plan",
                actor="dev",
            )

    def test_denied_create_no_task_saved(self, mgr_with_perms, mock_role_manager):
        """Denied create should not persist any task."""
        mock_role_manager.can_create_task_for.return_value = False
        with pytest.raises(PermissionError):
            mgr_with_perms.create_task(
                id="TASK-PM-001", role="PM", feature="Plan",
                actor="dev",
            )
        assert mgr_with_perms.get_task("TASK-PM-001") is None

    def test_create_checks_before_save(self, mgr_with_perms, mock_role_manager):
        """Permission check happens before task creation (not after)."""
        mock_role_manager.can_create_task_for.return_value = False
        with pytest.raises(PermissionError):
            mgr_with_perms.create_task(
                id="TASK-DEV-001", role="DEV", feature="Test",
                actor="dev",
            )
        # Task should not exist at all
        assert len(mgr_with_perms.list_tasks()) == 0


# ---------------------------------------------------------------------------
# transition permission enforcement
# ---------------------------------------------------------------------------

class TestTransitionPermissions:
    def test_allowed_transition(self, mgr_with_perms, mock_role_manager):
        """Transition succeeds when RoleManager allows it."""
        mgr_with_perms.create_task(
            id="TASK-DEV-001", role="DEV", feature="Test",
        )
        mock_role_manager.can_transition_to.return_value = True
        result = mgr_with_perms.transition(
            "TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="dev",
        )
        assert result.ok is True

    def test_denied_transition(self, mgr_with_perms, mock_role_manager):
        """Transition denied returns ValidationResult with violation."""
        mgr_with_perms.create_task(
            id="TASK-DEV-001", role="DEV", feature="Test",
        )
        # Advance to IN_PROGRESS first
        mgr_with_perms.transition(
            "TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="dev",
        )
        # Now deny DONE transition
        mock_role_manager.can_transition_to.return_value = False
        result = mgr_with_perms.transition(
            "TASK-DEV-001", TaskStatus.REVIEW, actor="dev",
        )
        assert result.ok is False
        assert "Permission denied" in result.violations[0]

    def test_denied_transition_preserves_status(self, mgr_with_perms, mock_role_manager):
        """Denied transition should not change task status."""
        mgr_with_perms.create_task(
            id="TASK-DEV-001", role="DEV", feature="Test",
        )
        mgr_with_perms.transition(
            "TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="dev",
        )
        mock_role_manager.can_transition_to.return_value = False
        mgr_with_perms.transition(
            "TASK-DEV-001", TaskStatus.REVIEW, actor="dev",
        )
        task = mgr_with_perms.get_task("TASK-DEV-001")
        assert task.status == TaskStatus.IN_PROGRESS

    def test_state_machine_checked_before_permission(
        self, mgr_with_perms, mock_role_manager,
    ):
        """State machine validation runs before permission check."""
        mgr_with_perms.create_task(
            id="TASK-DEV-001", role="DEV", feature="Test",
        )
        # Try illegal transition: TODO -> DONE
        mock_role_manager.can_transition_to.return_value = True
        result = mgr_with_perms.transition(
            "TASK-DEV-001", TaskStatus.DONE, actor="dev",
        )
        assert result.ok is False
        assert "Illegal transition" in result.violations[0]
        # Permission check should NOT have been called (early return)
        mock_role_manager.can_transition_to.assert_not_called()


# ---------------------------------------------------------------------------
# Schema validation for guards + hooks config
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_valid_guards_config(self):
        from vibecollab.core.pipeline import SchemaValidator
        validator = SchemaValidator()
        config = {
            "project": {"name": "Test", "version": "v1.0"},
            "guards": {
                "enabled": True,
                "rules": [
                    {
                        "name": "test_rule",
                        "pattern": "**/*.meta",
                        "operations": ["delete", "modify"],
                        "severity": "block",
                        "message": "Test",
                    }
                ],
            },
        }
        report = validator.validate(config)
        assert report.ok
        assert len(report.warnings) == 0

    def test_invalid_guard_severity(self):
        from vibecollab.core.pipeline import SchemaValidator
        validator = SchemaValidator()
        config = {
            "project": {"name": "Test", "version": "v1.0"},
            "guards": {
                "rules": [
                    {
                        "name": "test",
                        "pattern": "**/*",
                        "severity": "invalid_level",
                    }
                ],
            },
        }
        report = validator.validate(config)
        assert any("severity" in w for w in report.warnings)

    def test_missing_guard_rule_name(self):
        from vibecollab.core.pipeline import SchemaValidator
        validator = SchemaValidator()
        config = {
            "project": {"name": "Test", "version": "v1.0"},
            "guards": {
                "rules": [
                    {"pattern": "**/*", "severity": "block"}
                ],
            },
        }
        report = validator.validate(config)
        assert any("name is required" in e for e in report.errors)

    def test_valid_hooks_config(self):
        from vibecollab.core.pipeline import SchemaValidator
        validator = SchemaValidator()
        config = {
            "project": {"name": "Test", "version": "v1.0"},
            "hooks": {
                "enabled": True,
                "rules": {
                    "pre-commit": ["vibecollab check"],
                    "pre-push": ["pytest tests/"],
                },
            },
        }
        report = validator.validate(config)
        assert report.ok

    def test_invalid_hook_type(self):
        from vibecollab.core.pipeline import SchemaValidator
        validator = SchemaValidator()
        config = {
            "project": {"name": "Test", "version": "v1.0"},
            "hooks": {
                "rules": {
                    "invalid-hook": ["echo test"],
                },
            },
        }
        report = validator.validate(config)
        assert any("unknown hook type" in w for w in report.warnings)

    def test_hooks_rules_not_list(self):
        from vibecollab.core.pipeline import SchemaValidator
        validator = SchemaValidator()
        config = {
            "project": {"name": "Test", "version": "v1.0"},
            "hooks": {
                "rules": {
                    "pre-commit": "not a list",
                },
            },
        }
        report = validator.validate(config)
        assert any("must be a list" in e for e in report.errors)
