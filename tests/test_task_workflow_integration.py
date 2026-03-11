"""
v0.9.3 Task/EventLog core workflow integration - unit tests

Test coverage:
- Task CLI new commands: transition / solidify / rollback
- onboard injects Task overview + EventLog summary
- next recommends actions based on Task status
- MCP Server new Tools: task_create / task_transition
"""

import json

import pytest
import yaml
from click.testing import CliRunner

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def project_dir(tmp_path):
    """Create a complete test project directory"""
    config = {
        "project": {
            "name": "TestProject",
            "version": "1.0.0",
            "description": "A test project",
        },
        "documentation": {
            "key_files": [
                {"path": "CONTRIBUTING_AI.md", "purpose": "AI collaboration protocol"},
            ],
        },
        "dialogue_protocol": {
            "on_start": {"read_files": ["CONTRIBUTING_AI.md"]},
            "on_end": {"update_files": []},
        },
    }
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config, allow_unicode=True), encoding="utf-8"
    )
    (tmp_path / "CONTRIBUTING_AI.md").write_text("# AI Protocol\n", encoding="utf-8")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "CONTEXT.md").write_text("# Context\nv1.0.0\n", encoding="utf-8")
    (docs / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
    (docs / "ROADMAP.md").write_text("# Roadmap\n- [ ] Task 1\n", encoding="utf-8")
    (docs / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")

    vc = tmp_path / ".vibecollab"
    vc.mkdir()
    ins_dir = vc / "insights"
    ins_dir.mkdir()
    reg_data = {"version": 1, "entries": {}}
    (ins_dir / "registry.yaml").write_text(
        yaml.dump(reg_data, allow_unicode=True), encoding="utf-8"
    )

    return tmp_path


@pytest.fixture
def project_with_tasks(project_dir):
    """Project with tasks"""
    from vibecollab.domain.task_manager import TaskManager

    tm = TaskManager(project_root=project_dir)
    tm.create_task(id="TASK-DEV-001", role="DEV", feature="Implement feature A", assignee="alice")
    tm.create_task(id="TASK-DEV-002", role="DEV", feature="Implement feature B", assignee="bob")
    tm.transition("TASK-DEV-001", "IN_PROGRESS", actor="alice")
    tm.transition("TASK-DEV-002", "IN_PROGRESS", actor="bob")
    tm.transition("TASK-DEV-002", "REVIEW", actor="bob")
    return project_dir


# ============================================================
# Task CLI: transition
# ============================================================


class TestTransitionCommand:
    def test_transition_success(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            # Create task first
            result = runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test feature",
            ])
            assert result.exit_code == 0

            # Transition to IN_PROGRESS
            result = runner.invoke(task_group, [
                "transition", "TASK-DEV-001", "IN_PROGRESS",
            ])
            assert result.exit_code == 0
            assert "Transitioned" in result.output
            assert "IN_PROGRESS" in result.output

    def test_transition_with_reason(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            result = runner.invoke(task_group, [
                "transition", "TASK-DEV-001", "IN_PROGRESS",
                "-r", "Start development",
            ])
            assert result.exit_code == 0

    def test_transition_illegal(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            # TODO -> DONE is an illegal transition
            result = runner.invoke(task_group, [
                "transition", "TASK-DEV-001", "DONE",
            ])
            assert result.exit_code != 0

    def test_transition_not_found(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(task_group, [
                "transition", "TASK-DEV-999", "IN_PROGRESS",
            ])
            assert result.exit_code != 0
            assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_transition_json_output(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            result = runner.invoke(task_group, [
                "transition", "TASK-DEV-001", "IN_PROGRESS", "--json",
            ])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["ok"] is True


# ============================================================
# Task CLI: solidify
# ============================================================


class TestSolidifyCommand:
    def test_solidify_success(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "REVIEW"])

            result = runner.invoke(task_group, ["solidify", "TASK-DEV-001"])
            assert result.exit_code == 0
            assert "Solidified" in result.output
            assert "DONE" in result.output

    def test_solidify_not_in_review(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            # Try solidify in TODO status
            result = runner.invoke(task_group, ["solidify", "TASK-DEV-001"])
            assert result.exit_code != 0
            assert "Solidify failed" in result.output

    def test_solidify_not_found(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(task_group, ["solidify", "TASK-DEV-999"])
            assert result.exit_code != 0

    def test_solidify_json_output(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "REVIEW"])

            result = runner.invoke(task_group, ["solidify", "TASK-DEV-001", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["ok"] is True


# ============================================================
# Task CLI: rollback
# ============================================================


class TestRollbackCommand:
    def test_rollback_success(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])

            result = runner.invoke(task_group, ["rollback", "TASK-DEV-001"])
            assert result.exit_code == 0
            assert "Rolled back" in result.output

    def test_rollback_with_reason(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])

            result = runner.invoke(task_group, [
                "rollback", "TASK-DEV-001", "-r", "Need redesign",
            ])
            assert result.exit_code == 0
            assert "Need redesign" in result.output

    def test_rollback_from_todo(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            # TODO status cannot be rolled back
            result = runner.invoke(task_group, ["rollback", "TASK-DEV-001"])
            assert result.exit_code != 0

    def test_rollback_not_found(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(task_group, ["rollback", "TASK-DEV-999"])
            assert result.exit_code != 0

    def test_rollback_json_output(self, project_dir):
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])

            result = runner.invoke(task_group, ["rollback", "TASK-DEV-001", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["ok"] is True


# ============================================================
# Task CLI: Full lifecycle state machine test
# ============================================================


class TestFullLifecycle:
    def test_complete_lifecycle(self, project_dir):
        """TODO → IN_PROGRESS → REVIEW → solidify → DONE"""
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Implement feature A",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "REVIEW"])

            result = runner.invoke(task_group, ["solidify", "TASK-DEV-001"])
            assert result.exit_code == 0

            # Verify final status
            result = runner.invoke(task_group, ["show", "TASK-DEV-001", "--json"])
            data = json.loads(result.output)
            assert data["status"] == "DONE"

    def test_rollback_and_retry(self, project_dir):
        """IN_PROGRESS → REVIEW → rollback → IN_PROGRESS → REVIEW → solidify"""
        from vibecollab.cli.task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "test-feature",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "REVIEW"])

            # Rollback
            result = runner.invoke(task_group, [
                "rollback", "TASK-DEV-001", "-r", "Found bug",
            ])
            assert result.exit_code == 0

            # Re-submit for review
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "REVIEW"])
            result = runner.invoke(task_group, ["solidify", "TASK-DEV-001"])
            assert result.exit_code == 0


# ============================================================
# onboard Task/EventLog injection
# ============================================================


class TestOnboardInjection:
    def test_onboard_with_tasks_json(self, project_with_tasks):
        from vibecollab.cli.guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(onboard, ["--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)

            assert "task_summary" in data
            assert data["task_summary"]["total"] == 2
            assert data["task_summary"]["in_progress"] == 1
            assert data["task_summary"]["review"] == 1

            assert "active_tasks" in data
            assert len(data["active_tasks"]) == 2

    def test_onboard_with_tasks_rich(self, project_with_tasks):
        from vibecollab.cli.guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(onboard, [])
            assert result.exit_code == 0
            assert "Task Overview" in result.output

    def test_onboard_no_tasks(self, project_dir):
        from vibecollab.cli.guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(onboard, ["--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["task_summary"]["total"] == 0

    def test_onboard_events_json(self, project_with_tasks):
        from vibecollab.cli.guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(onboard, ["--json"])
            data = json.loads(result.output)
            assert "recent_events" in data
            # project_with_tasks created tasks + state transitions, should have events
            assert len(data["recent_events"]) > 0

    def test_onboard_events_rich(self, project_with_tasks):
        from vibecollab.cli.guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(onboard, [])
            assert result.exit_code == 0
            assert "Recent Events" in result.output


# ============================================================
# next Task-based recommendations
# ============================================================


class TestNextTaskRecommendations:
    def test_next_with_review_tasks(self, project_with_tasks):
        from vibecollab.cli.guide import next_step

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(next_step, ["--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)

            # Should have solidify recommendation
            action_types = [a["type"] for a in data["actions"]]
            assert "task_solidify" in action_types

    def test_next_no_tasks(self, project_dir):
        from vibecollab.cli.guide import next_step

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(next_step, ["--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            action_types = [a["type"] for a in data["actions"]]
            assert "task_solidify" not in action_types


# ============================================================
# MCP Server new Tools
# ============================================================


class TestMcpNewTools:
    def test_task_create_tool(self, project_dir):
        """task_create tool should use direct API to create tasks"""
        from vibecollab.agent.mcp_server import _get_managers

        im, tm, _ = _get_managers(project_dir)
        task = tm.create_task(
            id="TASK-DEV-001",
            role="DEV",
            feature="Test",
        )
        assert task.id == "TASK-DEV-001"
        assert task.role == "DEV"

    def test_task_transition_tool(self, project_dir):
        """task_transition tool should use direct API to transition tasks"""
        from vibecollab.agent.mcp_server import _get_managers
        from vibecollab.domain.task_manager import TaskStatus

        im, tm, _ = _get_managers(project_dir)
        # Create a task first
        tm.create_task(
            id="TASK-DEV-002",
            role="DEV",
            feature="Transition test",
        )
        result = tm.transition("TASK-DEV-002", TaskStatus.IN_PROGRESS)
        assert result.ok is True

    def test_start_conversation_lists_new_tools(self, project_dir):
        """start_conversation prompt should include new tools"""

        # Check for new tools in prompt tool list
        # Directly check strings in mcp_server.py source code
        import inspect

        import vibecollab.agent.mcp_server as mod
        source = inspect.getsource(mod)
        assert "task_create" in source
        assert "task_transition" in source
        assert "task_list" in source


# ============================================================
# _collect_project_context data completeness
# ============================================================


class TestCollectProjectContext:
    def test_context_includes_tasks(self, project_with_tasks):
        from vibecollab.cli.guide import _collect_project_context

        ctx = _collect_project_context(project_with_tasks / "project.yaml")
        assert "active_tasks" in ctx
        assert "task_summary" in ctx
        assert ctx["task_summary"]["total"] == 2
        assert len(ctx["active_tasks"]) == 2

    def test_context_includes_events(self, project_with_tasks):
        from vibecollab.cli.guide import _collect_project_context

        ctx = _collect_project_context(project_with_tasks / "project.yaml")
        assert "recent_events" in ctx
        assert len(ctx["recent_events"]) > 0

    def test_context_no_tasks(self, project_dir):
        from vibecollab.cli.guide import _collect_project_context

        ctx = _collect_project_context(project_dir / "project.yaml")
        assert ctx["task_summary"]["total"] == 0
        assert ctx["active_tasks"] == []

    def test_context_no_events(self, project_dir):
        from vibecollab.cli.guide import _collect_project_context

        ctx = _collect_project_context(project_dir / "project.yaml")
        assert ctx["recent_events"] == []
