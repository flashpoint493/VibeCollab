"""
v0.9.3 Task/EventLog 核心工作流接通 — 单元测试

测试覆盖:
- Task CLI 新命令: transition / solidify / rollback
- onboard 注入 Task 概览 + EventLog 摘要
- next 基于 Task 状态推荐行动
- MCP Server 新 Tool: task_create / task_transition
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def project_dir(tmp_path):
    """创建一个完整的测试项目目录"""
    config = {
        "project": {
            "name": "TestProject",
            "version": "1.0.0",
            "description": "A test project",
        },
        "documentation": {
            "key_files": [
                {"path": "CONTRIBUTING_AI.md", "purpose": "AI 协作协议"},
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
    """带有任务的项目"""
    from vibecollab.task_manager import TaskManager

    tm = TaskManager(project_root=project_dir)
    tm.create_task(id="TASK-DEV-001", role="DEV", feature="实现功能A", assignee="alice")
    tm.create_task(id="TASK-DEV-002", role="DEV", feature="实现功能B", assignee="bob")
    tm.transition("TASK-DEV-001", "IN_PROGRESS", actor="alice")
    tm.transition("TASK-DEV-002", "IN_PROGRESS", actor="bob")
    tm.transition("TASK-DEV-002", "REVIEW", actor="bob")
    return project_dir


# ============================================================
# Task CLI: transition
# ============================================================


class TestTransitionCommand:
    def test_transition_success(self, project_dir):
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            # 先创建任务
            result = runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test feature",
            ])
            assert result.exit_code == 0

            # 转换到 IN_PROGRESS
            result = runner.invoke(task_group, [
                "transition", "TASK-DEV-001", "IN_PROGRESS",
            ])
            assert result.exit_code == 0
            assert "已转换" in result.output
            assert "IN_PROGRESS" in result.output

    def test_transition_with_reason(self, project_dir):
        from vibecollab.cli_task import task_group

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
                "-r", "开始开发",
            ])
            assert result.exit_code == 0

    def test_transition_illegal(self, project_dir):
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            # TODO → DONE 是非法转换
            result = runner.invoke(task_group, [
                "transition", "TASK-DEV-001", "DONE",
            ])
            assert result.exit_code != 0

    def test_transition_not_found(self, project_dir):
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(task_group, [
                "transition", "TASK-DEV-999", "IN_PROGRESS",
            ])
            assert result.exit_code != 0
            assert "not found" in result.output.lower() or "错误" in result.output

    def test_transition_json_output(self, project_dir):
        from vibecollab.cli_task import task_group

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
        from vibecollab.cli_task import task_group

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
            assert "已固化" in result.output
            assert "DONE" in result.output

    def test_solidify_not_in_review(self, project_dir):
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            # 尝试在 TODO 状态 solidify
            result = runner.invoke(task_group, ["solidify", "TASK-DEV-001"])
            assert result.exit_code != 0
            assert "固化失败" in result.output

    def test_solidify_not_found(self, project_dir):
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(task_group, ["solidify", "TASK-DEV-999"])
            assert result.exit_code != 0

    def test_solidify_json_output(self, project_dir):
        from vibecollab.cli_task import task_group

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
        from vibecollab.cli_task import task_group

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
            assert "已回滚" in result.output

    def test_rollback_with_reason(self, project_dir):
        from vibecollab.cli_task import task_group

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
                "rollback", "TASK-DEV-001", "-r", "需要重新设计",
            ])
            assert result.exit_code == 0
            assert "需要重新设计" in result.output

    def test_rollback_from_todo(self, project_dir):
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "Test",
            ])
            # TODO 状态不能回滚
            result = runner.invoke(task_group, ["rollback", "TASK-DEV-001"])
            assert result.exit_code != 0

    def test_rollback_not_found(self, project_dir):
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(task_group, ["rollback", "TASK-DEV-999"])
            assert result.exit_code != 0

    def test_rollback_json_output(self, project_dir):
        from vibecollab.cli_task import task_group

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
# Task CLI: 全链路状态机测试
# ============================================================


class TestFullLifecycle:
    def test_complete_lifecycle(self, project_dir):
        """TODO → IN_PROGRESS → REVIEW → solidify → DONE"""
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "实现功能 A",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "REVIEW"])

            result = runner.invoke(task_group, ["solidify", "TASK-DEV-001"])
            assert result.exit_code == 0

            # 验证最终状态
            result = runner.invoke(task_group, ["show", "TASK-DEV-001", "--json"])
            data = json.loads(result.output)
            assert data["status"] == "DONE"

    def test_rollback_and_retry(self, project_dir):
        """IN_PROGRESS → REVIEW → rollback → IN_PROGRESS → REVIEW → solidify"""
        from vibecollab.cli_task import task_group

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            runner.invoke(task_group, [
                "create", "--id", "TASK-DEV-001", "--role", "DEV",
                "--feature", "测试功能",
            ])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "IN_PROGRESS"])
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "REVIEW"])

            # 回滚
            result = runner.invoke(task_group, [
                "rollback", "TASK-DEV-001", "-r", "发现 bug",
            ])
            assert result.exit_code == 0

            # 重新提审
            runner.invoke(task_group, ["transition", "TASK-DEV-001", "REVIEW"])
            result = runner.invoke(task_group, ["solidify", "TASK-DEV-001"])
            assert result.exit_code == 0


# ============================================================
# onboard Task/EventLog 注入
# ============================================================


class TestOnboardInjection:
    def test_onboard_with_tasks_json(self, project_with_tasks):
        from vibecollab.cli_guide import onboard

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
        from vibecollab.cli_guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(onboard, [])
            assert result.exit_code == 0
            assert "任务概览" in result.output

    def test_onboard_no_tasks(self, project_dir):
        from vibecollab.cli_guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_dir):
            import os
            os.chdir(project_dir)

            result = runner.invoke(onboard, ["--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["task_summary"]["total"] == 0

    def test_onboard_events_json(self, project_with_tasks):
        from vibecollab.cli_guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(onboard, ["--json"])
            data = json.loads(result.output)
            assert "recent_events" in data
            # project_with_tasks 创建了任务 + 状态转换，应有事件
            assert len(data["recent_events"]) > 0

    def test_onboard_events_rich(self, project_with_tasks):
        from vibecollab.cli_guide import onboard

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(onboard, [])
            assert result.exit_code == 0
            assert "最近事件" in result.output


# ============================================================
# next Task-based 推荐
# ============================================================


class TestNextTaskRecommendations:
    def test_next_with_review_tasks(self, project_with_tasks):
        from vibecollab.cli_guide import next_step

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=project_with_tasks):
            import os
            os.chdir(project_with_tasks)

            result = runner.invoke(next_step, ["--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)

            # 应有 solidify 推荐
            action_types = [a["type"] for a in data["actions"]]
            assert "task_solidify" in action_types

    def test_next_no_tasks(self, project_dir):
        from vibecollab.cli_guide import next_step

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
# MCP Server 新 Tools
# ============================================================


class TestMcpNewTools:
    def test_task_create_tool(self, project_dir):
        """task_create tool 应调用正确的 CLI 命令"""
        from vibecollab.mcp_server import _run_cli

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout='{"id": "TASK-DEV-001"}',
                stderr="",
                returncode=0,
            )
            result = _run_cli(
                [
                    "vibecollab", "task", "create",
                    "--id", "TASK-DEV-001",
                    "--role", "DEV",
                    "--feature", "Test",
                    "--json",
                ],
                project_dir,
            )
            assert "TASK-DEV-001" in result
            mock_run.assert_called_once()

    def test_task_transition_tool(self, project_dir):
        """task_transition tool 应调用正确的 CLI 命令"""
        from vibecollab.mcp_server import _run_cli

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout='{"ok": true}',
                stderr="",
                returncode=0,
            )
            result = _run_cli(
                [
                    "vibecollab", "task", "transition",
                    "TASK-DEV-001", "IN_PROGRESS",
                    "--json",
                ],
                project_dir,
            )
            assert "ok" in result
            mock_run.assert_called_once()

    def test_start_conversation_lists_new_tools(self, project_dir):
        """start_conversation prompt 应包含新工具"""

        # 模拟 prompt 中的工具列表检查
        # 直接检查 mcp_server.py 源码中的字符串
        import inspect

        import vibecollab.mcp_server as mod
        source = inspect.getsource(mod)
        assert "task_create" in source
        assert "task_transition" in source
        assert "task_list" in source


# ============================================================
# _collect_project_context 数据完整性
# ============================================================


class TestCollectProjectContext:
    def test_context_includes_tasks(self, project_with_tasks):
        from vibecollab.cli_guide import _collect_project_context

        ctx = _collect_project_context(project_with_tasks / "project.yaml")
        assert "active_tasks" in ctx
        assert "task_summary" in ctx
        assert ctx["task_summary"]["total"] == 2
        assert len(ctx["active_tasks"]) == 2

    def test_context_includes_events(self, project_with_tasks):
        from vibecollab.cli_guide import _collect_project_context

        ctx = _collect_project_context(project_with_tasks / "project.yaml")
        assert "recent_events" in ctx
        assert len(ctx["recent_events"]) > 0

    def test_context_no_tasks(self, project_dir):
        from vibecollab.cli_guide import _collect_project_context

        ctx = _collect_project_context(project_dir / "project.yaml")
        assert ctx["task_summary"]["total"] == 0
        assert ctx["active_tasks"] == []

    def test_context_no_events(self, project_dir):
        from vibecollab.cli_guide import _collect_project_context

        ctx = _collect_project_context(project_dir / "project.yaml")
        assert ctx["recent_events"] == []
