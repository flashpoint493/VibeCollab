"""
Unit tests for pipeline.py — SchemaValidator, ActionRegistry, DocSyncChecker, Pipeline.

Coverage targets:
- SchemaValidator: validate() all branches (project, roles, decisions, tasks, docs, git)
- ValidationReport: ok/not-ok, to_dict
- ActionRegistry: get_actions, get_all_events, register_action, format_action_hints
- DocSyncChecker: check_freshness (stale, missing, up-to-date)
- Pipeline: validate_config, check_docs, register_task_hooks, get_pending_actions, get_version
"""

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from vibecollab.core.pipeline import (
    ActionRegistry,
    DocSyncChecker,
    Pipeline,
    SchemaValidator,
    ValidationReport,
)


# ============================================================
# ValidationReport
# ============================================================


class TestValidationReport:
    def test_ok_when_no_errors(self):
        r = ValidationReport()
        assert r.ok is True
        assert r.errors == []
        assert r.warnings == []

    def test_not_ok_when_errors(self):
        r = ValidationReport(errors=["bad"])
        assert r.ok is False

    def test_to_dict(self):
        r = ValidationReport(errors=["err1"], warnings=["warn1", "warn2"])
        d = r.to_dict()
        assert d["ok"] is False
        assert d["error_count"] == 1
        assert d["warning_count"] == 2
        assert d["errors"] == ["err1"]
        assert d["warnings"] == ["warn1", "warn2"]

    def test_ok_with_warnings_only(self):
        r = ValidationReport(warnings=["just a warning"])
        assert r.ok is True
        assert r.to_dict()["ok"] is True

    def test_none_defaults(self):
        r = ValidationReport(errors=None, warnings=None)
        assert r.errors == []
        assert r.warnings == []


# ============================================================
# SchemaValidator
# ============================================================


class TestSchemaValidator:
    def test_no_schema_file(self):
        """Validator works without a schema file (validates built-in rules only)."""
        v = SchemaValidator(schema_path=None)
        config = {"project": {"name": "Test", "version": "v1.0"}}
        r = v.validate(config)
        assert r.ok is True

    def test_with_schema_file(self, tmp_path):
        """Validator loads schema file (even though not used for rules currently)."""
        schema = {"type": "object"}
        schema_file = tmp_path / "schema.yaml"
        schema_file.write_text(yaml.dump(schema), encoding="utf-8")
        v = SchemaValidator(schema_path=schema_file)
        assert v._schema == schema

    def test_with_nonexistent_schema(self, tmp_path):
        v = SchemaValidator(schema_path=tmp_path / "nope.yaml")
        assert v._schema is None

    # --- project section ---

    def test_missing_project_name(self):
        v = SchemaValidator()
        r = v.validate({"project": {}})
        assert not r.ok
        assert any("project.name" in e for e in r.errors)

    def test_valid_version_v1_0(self):
        v = SchemaValidator()
        r = v.validate({"project": {"name": "A", "version": "v1.0"}})
        assert r.ok

    def test_valid_version_v1_0_0(self):
        v = SchemaValidator()
        r = v.validate({"project": {"name": "A", "version": "v1.0.0"}})
        assert r.ok

    def test_invalid_version_format(self):
        v = SchemaValidator()
        r = v.validate({"project": {"name": "A", "version": "bad"}})
        assert r.ok  # version format is a warning, not error
        assert any("version" in w for w in r.warnings)

    def test_empty_version_no_warning(self):
        v = SchemaValidator()
        r = v.validate({"project": {"name": "A", "version": ""}})
        assert r.ok
        # Empty version should not trigger warning (version and not match)
        assert not any("version" in w for w in r.warnings)

    # --- roles section ---

    def test_role_missing_code(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "roles": [{"name": "Dev"}]
        })
        assert not r.ok
        assert any("code" in e for e in r.errors)

    def test_role_missing_name(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "roles": [{"code": "DEV"}]
        })
        assert not r.ok
        assert any("name" in e for e in r.errors)

    def test_role_code_not_uppercase(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "roles": [{"code": "dev", "name": "Dev"}]
        })
        assert r.ok  # lowercase is warning
        assert any("uppercase" in w for w in r.warnings)

    def test_role_valid(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "roles": [{"code": "DEV", "name": "Development"}]
        })
        assert r.ok
        assert not r.warnings

    # --- decision_levels section ---

    def test_invalid_decision_level(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "decision_levels": [{"level": "X"}]
        })
        assert any("decision_levels" in w for w in r.warnings)

    def test_valid_decision_levels(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "decision_levels": [
                {"level": "S"}, {"level": "A"}, {"level": "B"}, {"level": "C"}
            ]
        })
        assert r.ok

    # --- task_unit section ---

    def test_task_unit_missing_statuses(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "task_unit": {"id_pattern": "TASK-{role}-{seq}", "statuses": ["TODO", "DONE"]}
        })
        assert any("statuses missing" in w for w in r.warnings)

    def test_task_unit_bad_id_pattern(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "task_unit": {"id_pattern": "ISSUE-{seq}", "statuses": []}
        })
        assert any("id_pattern" in w for w in r.warnings)

    def test_task_unit_valid(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "task_unit": {
                "id_pattern": "TASK-{role}-{seq}",
                "statuses": ["TODO", "IN_PROGRESS", "REVIEW", "DONE"],
            }
        })
        assert r.ok

    def test_task_unit_empty(self):
        """Empty task_unit section should not cause errors."""
        v = SchemaValidator()
        r = v.validate({"project": {"name": "A"}, "task_unit": {}})
        assert r.ok

    # --- documentation section ---

    def test_key_file_missing_path(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "documentation": {"key_files": [{"purpose": "test"}]}
        })
        assert not r.ok
        assert any("key_files" in e for e in r.errors)

    def test_key_file_valid(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "documentation": {"key_files": [{"path": "README.md", "purpose": "docs"}]}
        })
        assert r.ok

    # --- git_workflow section ---

    def test_git_missing_feat_fix_prefix(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "git_workflow": {
                "commit_prefixes": [
                    {"prefix": "[DOC]", "description": "Docs"}
                ]
            }
        })
        assert any("FEAT" in w for w in r.warnings)

    def test_git_has_feat_fix(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "git_workflow": {
                "commit_prefixes": [
                    {"prefix": "[FEAT]", "description": "New features"},
                    {"prefix": "[FIX]", "description": "Fixes"},
                ]
            }
        })
        assert r.ok

    def test_git_empty_prefixes(self):
        """Empty prefixes list should not trigger warning."""
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "git_workflow": {"commit_prefixes": []}
        })
        assert r.ok

    def test_git_empty_section(self):
        v = SchemaValidator()
        r = v.validate({
            "project": {"name": "A"},
            "git_workflow": {}
        })
        assert r.ok

    # --- full valid config ---

    def test_full_valid_config(self):
        v = SchemaValidator()
        config = {
            "project": {"name": "Test", "version": "v1.0"},
            "roles": [
                {"code": "DEV", "name": "Development"},
                {"code": "PM", "name": "Project Management"},
            ],
            "decision_levels": [
                {"level": "S"}, {"level": "A"}, {"level": "B"}, {"level": "C"}
            ],
            "task_unit": {
                "id_pattern": "TASK-{role}-{seq}",
                "statuses": ["TODO", "IN_PROGRESS", "REVIEW", "DONE"],
            },
            "documentation": {
                "key_files": [{"path": "README.md", "purpose": "docs"}]
            },
            "git_workflow": {
                "commit_prefixes": [
                    {"prefix": "[FEAT]", "description": "features"},
                    {"prefix": "[FIX]", "description": "fixes"},
                ]
            },
        }
        r = v.validate(config)
        assert r.ok
        assert not r.warnings

    def test_empty_config(self):
        v = SchemaValidator()
        r = v.validate({})
        assert not r.ok  # project.name required


# ============================================================
# ActionRegistry
# ============================================================


class TestActionRegistry:
    def test_get_actions_known_event(self):
        actions = ActionRegistry.get_actions("task_completed")
        assert len(actions) >= 1
        # Should be sorted by priority
        priorities = [a[2] for a in actions]
        assert priorities == sorted(priorities)

    def test_get_actions_unknown_event(self):
        actions = ActionRegistry.get_actions("unknown_event_xyz")
        assert actions == []

    def test_get_all_events(self):
        events = ActionRegistry.get_all_events()
        assert "task_completed" in events
        assert "task_created" in events
        assert "insight_added" in events
        assert "milestone_completed" in events
        assert "config_changed" in events
        assert "docs_stale" in events

    def test_register_action_new_event(self):
        # Register on a fresh event name to avoid side effects
        event = "_test_custom_event_12345"
        ActionRegistry.register_action(event, "echo test", "test action", 5)
        actions = ActionRegistry.get_actions(event)
        assert len(actions) == 1
        assert actions[0][0] == "echo test"
        assert actions[0][1] == "test action"
        assert actions[0][2] == 5
        # Cleanup
        del ActionRegistry._ACTIONS[event]

    def test_register_action_existing_event(self):
        event = "_test_existing_event_12345"
        ActionRegistry._ACTIONS[event] = [("cmd1", "desc1", 1)]
        ActionRegistry.register_action(event, "cmd2", "desc2", 2)
        actions = ActionRegistry.get_actions(event)
        assert len(actions) == 2
        del ActionRegistry._ACTIONS[event]

    def test_format_action_hints_with_actions(self):
        text = ActionRegistry.format_action_hints("task_completed")
        assert "Recommended actions" in text
        assert "vibecollab" in text

    def test_format_action_hints_empty(self):
        text = ActionRegistry.format_action_hints("no_such_event_xyz")
        assert text == ""

    def test_format_action_hints_structure(self):
        text = ActionRegistry.format_action_hints("task_completed")
        lines = text.strip().split("\n")
        # First line is header, then pairs of P{n}: cmd + desc
        assert lines[0].startswith("Recommended actions")
        assert any(line.strip().startswith("P") for line in lines[1:])


# ============================================================
# DocSyncChecker
# ============================================================


class TestDocSyncChecker:
    def test_upstream_missing(self, tmp_path):
        """No report when upstream file doesn't exist."""
        checker = DocSyncChecker(tmp_path)
        results = checker.check_freshness()
        # No upstream files exist → no results
        assert results == []

    def test_downstream_missing(self, tmp_path):
        """Report 'missing' when downstream doesn't exist."""
        (tmp_path / "project.yaml").write_text("test", encoding="utf-8")
        # Don't create CONTRIBUTING_AI.md
        checker = DocSyncChecker(tmp_path)
        results = checker.check_freshness()
        missing = [r for r in results if r["status"] == "missing"]
        assert len(missing) >= 1
        assert missing[0]["downstream"] == "CONTRIBUTING_AI.md"

    def test_downstream_stale(self, tmp_path):
        """Report 'stale' when downstream is older than upstream."""
        down = tmp_path / "CONTRIBUTING_AI.md"
        down.write_text("old content", encoding="utf-8")
        # Wait a bit then write upstream
        time.sleep(0.05)
        up = tmp_path / "project.yaml"
        up.write_text("new content", encoding="utf-8")

        checker = DocSyncChecker(tmp_path)
        results = checker.check_freshness()
        stale = [r for r in results if r["status"] == "stale"]
        assert len(stale) >= 1
        assert stale[0]["upstream"] == "project.yaml"
        assert "hours_behind" in stale[0]

    def test_downstream_fresh(self, tmp_path):
        """No stale report when downstream is newer."""
        up = tmp_path / "project.yaml"
        up.write_text("content", encoding="utf-8")
        time.sleep(0.05)
        down = tmp_path / "CONTRIBUTING_AI.md"
        down.write_text("fresh content", encoding="utf-8")

        checker = DocSyncChecker(tmp_path)
        results = checker.check_freshness()
        # project.yaml → CONTRIBUTING_AI.md should not be stale
        stale_for_contrib = [
            r for r in results
            if r.get("downstream") == "CONTRIBUTING_AI.md" and r["status"] == "stale"
        ]
        assert len(stale_for_contrib) == 0

    def test_multiple_deps(self, tmp_path):
        """Check multiple dependency chains."""
        # Create docs dir
        (tmp_path / "docs").mkdir()
        (tmp_path / ".vibecollab").mkdir()

        # project.yaml → CONTRIBUTING_AI.md (stale)
        (tmp_path / "CONTRIBUTING_AI.md").write_text("old", encoding="utf-8")
        time.sleep(0.05)
        (tmp_path / "project.yaml").write_text("new", encoding="utf-8")

        # docs/CONTEXT.md → docs/CHANGELOG.md (fresh)
        (tmp_path / "docs" / "CONTEXT.md").write_text("ctx", encoding="utf-8")
        time.sleep(0.05)
        (tmp_path / "docs" / "CHANGELOG.md").write_text("log", encoding="utf-8")

        checker = DocSyncChecker(tmp_path)
        results = checker.check_freshness()
        assert any(r["downstream"] == "CONTRIBUTING_AI.md" and r["status"] == "stale"
                    for r in results)

    def test_stale_action_contains_commands(self, tmp_path):
        """Stale report includes action recommendations."""
        (tmp_path / "project.yaml").write_text("x", encoding="utf-8")
        checker = DocSyncChecker(tmp_path)
        results = checker.check_freshness()
        for r in results:
            assert "action" in r


# ============================================================
# Pipeline
# ============================================================


class TestPipeline:
    @pytest.fixture
    def project(self, tmp_path):
        config = {
            "project": {"name": "TestPipeline", "version": "v1.0"},
            "roles": [{"code": "DEV", "name": "Development"}],
            "git_workflow": {
                "commit_prefixes": [
                    {"prefix": "[FEAT]", "description": "features"},
                    {"prefix": "[FIX]", "description": "fixes"},
                ]
            },
        }
        (tmp_path / "project.yaml").write_text(
            yaml.dump(config), encoding="utf-8"
        )
        # Create schema dir (empty)
        (tmp_path / "schema").mkdir()
        return tmp_path

    def test_validate_config_ok(self, project):
        p = Pipeline(project_root=project)
        report = p.validate_config()
        assert report.ok

    def test_validate_config_missing(self, tmp_path):
        p = Pipeline(project_root=tmp_path, config_path="nonexistent.yaml")
        report = p.validate_config()
        assert not report.ok
        assert any("not found" in e for e in report.errors)

    def test_validate_config_invalid(self, tmp_path):
        (tmp_path / "project.yaml").write_text(
            yaml.dump({"project": {}}), encoding="utf-8"
        )
        p = Pipeline(project_root=tmp_path)
        report = p.validate_config()
        assert not report.ok

    def test_check_docs(self, project):
        p = Pipeline(project_root=project)
        # project.yaml exists but CONTRIBUTING_AI.md missing
        results = p.check_docs()
        assert any(r["downstream"] == "CONTRIBUTING_AI.md" for r in results)

    def test_check_docs_empty(self, tmp_path):
        p = Pipeline(project_root=tmp_path, config_path=None)
        results = p.check_docs()
        # No upstream files → empty
        assert results == []

    def test_register_task_hooks(self, project):
        from vibecollab.domain.task_manager import Task

        p = Pipeline(project_root=project)
        mock_tm = MagicMock()
        mock_tm.on_complete = MagicMock()
        p.register_task_hooks(mock_tm)
        mock_tm.on_complete.assert_called_once()

        # Extract the registered callback and call it
        callback = mock_tm.on_complete.call_args[0][0]
        task = Task(id="TASK-DEV-001", role="DEV", feature="test")
        callback(task)
        assert "_pipeline_actions" in task.metadata
        assert len(task.metadata["_pipeline_actions"]) > 0

    def test_register_task_hooks_no_on_complete(self, project):
        """Handles objects without on_complete gracefully."""
        p = Pipeline(project_root=project)
        obj = object()  # no on_complete attr
        p.register_task_hooks(obj)  # should not raise

    def test_get_pending_actions_with_issues(self, project):
        p = Pipeline(project_root=project)
        actions = p.get_pending_actions()
        # CONTRIBUTING_AI.md is missing → should have doc_freshness action
        assert any(a["source"] == "doc_freshness" for a in actions)

    def test_get_pending_actions_sorted(self, project):
        p = Pipeline(project_root=project)
        actions = p.get_pending_actions()
        priorities = [a["priority"] for a in actions]
        assert priorities == sorted(priorities)

    def test_get_pending_actions_clean(self, tmp_path):
        """No pending actions when config is None."""
        p = Pipeline(project_root=tmp_path, config_path=None)
        actions = p.get_pending_actions()
        # No config → no schema actions, no docs actions
        assert len(actions) == 0

    def test_get_pending_actions_config_errors(self, tmp_path):
        """Config with errors generates schema_validation actions."""
        (tmp_path / "project.yaml").write_text(
            yaml.dump({"project": {}}), encoding="utf-8"
        )
        p = Pipeline(project_root=tmp_path)
        actions = p.get_pending_actions()
        assert any(a["source"] == "schema_validation" for a in actions)

    def test_get_pending_actions_config_warnings(self, tmp_path):
        """Config with warnings generates low-priority actions."""
        config = {
            "project": {"name": "A", "version": "invalid-version"},
        }
        (tmp_path / "project.yaml").write_text(
            yaml.dump(config), encoding="utf-8"
        )
        p = Pipeline(project_root=tmp_path)
        actions = p.get_pending_actions()
        warnings = [a for a in actions if a["source"] == "schema_validation"
                     and a["priority"] == 3]
        assert len(warnings) >= 1
        assert warnings[0]["command"] is None

    def test_get_version(self, project):
        p = Pipeline(project_root=project)
        v = p.get_version()
        assert "package_version" in v
        assert "protocol_version" in v
        assert v["protocol_version"] == "v1.0"

    def test_get_version_no_config(self, tmp_path):
        p = Pipeline(project_root=tmp_path, config_path=None)
        v = p.get_version()
        assert v["protocol_version"] == "v1.0"  # default

    def test_load_config_with_schema(self, project):
        """Pipeline loads schema from schema/project.schema.yaml if exists."""
        schema = {"type": "object"}
        schema_file = project / "schema" / "project.schema.yaml"
        schema_file.write_text(yaml.dump(schema), encoding="utf-8")
        p = Pipeline(project_root=project)
        assert p.validator._schema is not None


# ============================================================
# CLI task.py bug fixes verification
# ============================================================


class TestCliTaskBugFixes:
    """Tests for the CLI task.py bug fixes:
    1. create_task ValueError now shows error message (not silent)
    2. rollback truncated raise SystemExit fixed
    """

    @pytest.fixture
    def project_dir(self, tmp_path, monkeypatch):
        config = {"project": {"name": "Test", "version": "v1.0"}}
        (tmp_path / "project.yaml").write_text(
            yaml.dump(config), encoding="utf-8"
        )
        (tmp_path / ".vibecollab").mkdir()
        monkeypatch.chdir(tmp_path)
        return tmp_path

    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner
        return CliRunner()

    def test_create_invalid_id_shows_error(self, runner, project_dir):
        """create_task ValueError should print error message, not silently exit."""
        from vibecollab.cli.task import task_group
        result = runner.invoke(task_group, [
            "create",
            "--id", "BAD-ID",
            "--role", "DEV",
            "--feature", "Test",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 1
        assert "Error" in result.output or "error" in result.output.lower()

    def test_create_duplicate_id_shows_error(self, runner, project_dir):
        """Duplicate task ID should show error message."""
        from vibecollab.cli.task import task_group
        # First create succeeds
        result = runner.invoke(task_group, [
            "create",
            "--id", "TASK-DEV-001",
            "--role", "DEV",
            "--feature", "First",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0

        # Duplicate should fail with message
        result = runner.invoke(task_group, [
            "create",
            "--id", "TASK-DEV-001",
            "--role", "DEV",
            "--feature", "Duplicate",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 1
        assert "Error" in result.output or "already exists" in result.output

    def test_rollback_from_done_shows_error(self, runner, project_dir):
        """Rollback from DONE should show error (not crash with truncated raise)."""
        from vibecollab.cli.task import task_group
        # Create and advance to DONE
        runner.invoke(task_group, [
            "create", "--id", "TASK-DEV-002", "--role", "DEV",
            "--feature", "Test", "-c", str(project_dir / "project.yaml"),
        ])
        runner.invoke(task_group, [
            "transition", "TASK-DEV-002", "IN_PROGRESS",
            "-c", str(project_dir / "project.yaml"),
        ])
        runner.invoke(task_group, [
            "transition", "TASK-DEV-002", "REVIEW",
            "-c", str(project_dir / "project.yaml"),
        ])
        runner.invoke(task_group, [
            "transition", "TASK-DEV-002", "DONE",
            "-c", str(project_dir / "project.yaml"),
        ])

        # Rollback from DONE should fail gracefully
        result = runner.invoke(task_group, [
            "rollback", "TASK-DEV-002",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 1
        assert "Error" in result.output or "Cannot rollback" in result.output

    def test_rollback_from_todo_shows_error(self, runner, project_dir):
        """Rollback from TODO should fail gracefully."""
        from vibecollab.cli.task import task_group
        runner.invoke(task_group, [
            "create", "--id", "TASK-DEV-003", "--role", "DEV",
            "--feature", "Test", "-c", str(project_dir / "project.yaml"),
        ])
        result = runner.invoke(task_group, [
            "rollback", "TASK-DEV-003",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 1

    def test_rollback_success(self, runner, project_dir):
        """Rollback IN_PROGRESS → TODO should succeed."""
        from vibecollab.cli.task import task_group
        runner.invoke(task_group, [
            "create", "--id", "TASK-DEV-004", "--role", "DEV",
            "--feature", "Test", "-c", str(project_dir / "project.yaml"),
        ])
        runner.invoke(task_group, [
            "transition", "TASK-DEV-004", "IN_PROGRESS",
            "-c", str(project_dir / "project.yaml"),
        ])
        result = runner.invoke(task_group, [
            "rollback", "TASK-DEV-004",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0
        assert "Rolled back" in result.output

    def test_rollback_with_reason(self, runner, project_dir):
        """Rollback with --reason should display reason."""
        from vibecollab.cli.task import task_group
        runner.invoke(task_group, [
            "create", "--id", "TASK-DEV-005", "--role", "DEV",
            "--feature", "Test", "-c", str(project_dir / "project.yaml"),
        ])
        runner.invoke(task_group, [
            "transition", "TASK-DEV-005", "IN_PROGRESS",
            "-c", str(project_dir / "project.yaml"),
        ])
        result = runner.invoke(task_group, [
            "rollback", "TASK-DEV-005", "-r", "Needs redesign",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0
        assert "Needs redesign" in result.output

    def test_rollback_nonexistent_task(self, runner, project_dir):
        """Rollback non-existent task should fail."""
        from vibecollab.cli.task import task_group
        result = runner.invoke(task_group, [
            "rollback", "TASK-NOPE-999",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 1

    def test_transition_completion_hints(self, runner, project_dir):
        """Transition to DONE should show completion hints."""
        from vibecollab.cli.task import task_group
        runner.invoke(task_group, [
            "create", "--id", "TASK-DEV-006", "--role", "DEV",
            "--feature", "Test", "-c", str(project_dir / "project.yaml"),
        ])
        runner.invoke(task_group, [
            "transition", "TASK-DEV-006", "IN_PROGRESS",
            "-c", str(project_dir / "project.yaml"),
        ])
        runner.invoke(task_group, [
            "transition", "TASK-DEV-006", "REVIEW",
            "-c", str(project_dir / "project.yaml"),
        ])
        result = runner.invoke(task_group, [
            "transition", "TASK-DEV-006", "DONE",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0
        assert "DONE" in result.output

    def test_rollback_json_output(self, runner, project_dir):
        """Rollback with --json should return valid JSON."""
        from vibecollab.cli.task import task_group
        runner.invoke(task_group, [
            "create", "--id", "TASK-DEV-007", "--role", "DEV",
            "--feature", "Test", "-c", str(project_dir / "project.yaml"),
        ])
        runner.invoke(task_group, [
            "transition", "TASK-DEV-007", "IN_PROGRESS",
            "-c", str(project_dir / "project.yaml"),
        ])
        result = runner.invoke(task_group, [
            "rollback", "TASK-DEV-007", "--json",
            "-c", str(project_dir / "project.yaml"),
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
