"""Tests for workflow module — pre-built execution plan management."""

from pathlib import Path

import pytest
import yaml

from vibecollab.core.workflow import (
    WorkflowInfo,
    discover_workflows,
    find_workflow,
    get_workflow_plan,
    get_workflows_dir,
    list_workflow_categories,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_workflow(base_dir: Path, name: str, data: dict) -> Path:
    """Write a workflow YAML file and return its path."""
    workflows_dir = base_dir / ".vibecollab" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    workflow_file = workflows_dir / f"{name}.yaml"
    workflow_file.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return workflow_file


def _make_project(tmp_path: Path) -> Path:
    """Create a minimal project directory with workflows."""
    project = tmp_path / "project"
    project.mkdir()
    vibecollab_dir = project / ".vibecollab"
    vibecollab_dir.mkdir()
    return project


# ---------------------------------------------------------------------------
# TestWorkflowInfo
# ---------------------------------------------------------------------------


class TestWorkflowInfo:
    """Tests for WorkflowInfo data class."""

    def test_from_file_valid(self, tmp_path):
        data = {
            "name": "test-workflow",
            "description": "A test workflow",
            "version": "1.0",
            "category": "test",
            "steps": [{"action": "cli", "command": "echo hello"}],
        }
        wf_file = _write_workflow(tmp_path, "test-workflow", data)
        info = WorkflowInfo.from_file(wf_file)
        assert info is not None
        assert info.name == "test-workflow"
        assert info.description == "A test workflow"
        assert info.version == "1.0"
        assert info.category == "test"
        assert info.step_count == 1

    def test_from_file_missing_fields(self, tmp_path):
        """WorkflowInfo handles missing optional fields gracefully."""
        data = {
            "name": "minimal",
            "steps": [],
        }
        wf_file = _write_workflow(tmp_path, "minimal", data)
        info = WorkflowInfo.from_file(wf_file)
        assert info is not None
        assert info.name == "minimal"
        assert info.description == ""
        assert info.version == "unknown"
        assert info.category == "general"
        assert info.step_count == 0

    def test_from_file_invalid_yaml(self, tmp_path):
        """Invalid YAML returns None."""
        workflows_dir = tmp_path / ".vibecollab" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        wf_file = workflows_dir / "bad.yaml"
        wf_file.write_text("not: valid: yaml: [", encoding="utf-8")
        info = WorkflowInfo.from_file(wf_file)
        assert info is None

    def test_from_file_not_dict(self, tmp_path):
        """YAML that's not a dict returns None."""
        workflows_dir = tmp_path / ".vibecollab" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        wf_file = workflows_dir / "list.yaml"
        wf_file.write_text("- item1\n- item2", encoding="utf-8")
        info = WorkflowInfo.from_file(wf_file)
        assert info is None


# ---------------------------------------------------------------------------
# TestGetWorkflowsDir
# ---------------------------------------------------------------------------


class TestGetWorkflowsDir:
    """Tests for get_workflows_dir function."""

    def test_default_cwd(self):
        """Default uses current working directory."""
        path = get_workflows_dir()
        assert ".vibecollab" in str(path)
        assert "workflows" in str(path)

    def test_with_project_root(self, tmp_path):
        """Can specify project root."""
        path = get_workflows_dir(tmp_path)
        assert path == tmp_path / ".vibecollab" / "workflows"


# ---------------------------------------------------------------------------
# TestDiscoverWorkflows
# ---------------------------------------------------------------------------


class TestDiscoverWorkflows:
    """Tests for discover_workflows function."""

    def test_empty_directory(self, tmp_path):
        """Empty workflows directory returns empty list."""
        workflows_dir = tmp_path / ".vibecollab" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        workflows = discover_workflows(tmp_path)
        assert workflows == []

    def test_no_directory(self, tmp_path):
        """Missing workflows directory returns empty list."""
        workflows = discover_workflows(tmp_path)
        assert workflows == []

    def test_single_workflow(self, tmp_path):
        """Discover single workflow."""
        data = {
            "name": "test-wf",
            "description": "Test workflow",
            "steps": [{"action": "cli", "command": "echo test"}],
        }
        _write_workflow(tmp_path, "test-wf", data)
        workflows = discover_workflows(tmp_path)
        assert len(workflows) == 1
        assert workflows[0].name == "test-wf"

    def test_multiple_workflows_sorted(self, tmp_path):
        """Multiple workflows are sorted by name."""
        for name in ["zebra", "alpha", "beta"]:
            data = {"name": name, "steps": []}
            _write_workflow(tmp_path, name, data)
        workflows = discover_workflows(tmp_path)
        assert len(workflows) == 3
        names = [w.name for w in workflows]
        assert names == ["alpha", "beta", "zebra"]

    def test_ignores_non_yaml(self, tmp_path):
        """Non-YAML files are ignored."""
        workflows_dir = tmp_path / ".vibecollab" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "readme.txt").write_text("not a workflow")
        (workflows_dir / "script.py").write_text("print('hello')")
        workflows = discover_workflows(tmp_path)
        assert workflows == []


# ---------------------------------------------------------------------------
# TestFindWorkflow
# ---------------------------------------------------------------------------


class TestFindWorkflow:
    """Tests for find_workflow function."""

    def test_find_by_name(self, tmp_path):
        """Find workflow by name without extension."""
        data = {"name": "my-workflow", "steps": []}
        _write_workflow(tmp_path, "my-workflow", data)
        found = find_workflow("my-workflow", tmp_path)
        assert found is not None
        assert found.name == "my-workflow"

    def test_find_with_extension(self, tmp_path):
        """Find workflow with .yaml extension."""
        data = {"name": "my-workflow", "steps": []}
        _write_workflow(tmp_path, "my-workflow", data)
        found = find_workflow("my-workflow.yaml", tmp_path)
        assert found is not None
        assert found.name == "my-workflow"

    def test_find_not_found(self, tmp_path):
        """Returns None when workflow not found."""
        found = find_workflow("nonexistent", tmp_path)
        assert found is None

    def test_find_by_stem_match(self, tmp_path):
        """Find matches workflow file stem if name differs."""
        workflows_dir = tmp_path / ".vibecollab" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        # File named differently than internal name
        data = {"name": "internal-name", "steps": []}
        wf_file = workflows_dir / "file-name.yaml"
        wf_file.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        # Should find by internal name
        found = find_workflow("internal-name", tmp_path)
        assert found is not None


# ---------------------------------------------------------------------------
# TestGetWorkflowPlan
# ---------------------------------------------------------------------------


class TestGetWorkflowPlan:
    """Tests for get_workflow_plan function."""

    def test_get_plan_dict(self, tmp_path):
        """Get plan dictionary from workflow."""
        data = {
            "name": "test-plan",
            "steps": [{"action": "cli", "command": "echo test"}],
        }
        _write_workflow(tmp_path, "test-plan", data)
        plan = get_workflow_plan("test-plan", tmp_path)
        assert plan is not None
        assert plan["name"] == "test-plan"
        assert len(plan["steps"]) == 1

    def test_get_plan_not_found(self, tmp_path):
        """Returns None when workflow not found."""
        plan = get_workflow_plan("nonexistent", tmp_path)
        assert plan is None

    def test_get_plan_full_structure(self, tmp_path):
        """Plan includes all workflow fields."""
        data = {
            "name": "full-workflow",
            "description": "Full description",
            "version": "2.0",
            "category": "test",
            "steps": [
                {"action": "cli", "command": "step1"},
                {"action": "wait", "seconds": 1},
            ],
            "on_fail": "continue",
        }
        _write_workflow(tmp_path, "full-workflow", data)
        plan = get_workflow_plan("full-workflow", tmp_path)
        assert plan["description"] == "Full description"
        assert plan["version"] == "2.0"
        assert plan["category"] == "test"
        assert plan["on_fail"] == "continue"


# ---------------------------------------------------------------------------
# TestListWorkflowCategories
# ---------------------------------------------------------------------------


class TestListWorkflowCategories:
    """Tests for list_workflow_categories function."""

    def test_empty_list(self):
        """Empty list returns empty dict."""
        result = list_workflow_categories([])
        assert result == {}

    def test_single_category(self, tmp_path):
        """Group workflows by category."""
        wf1 = WorkflowInfo(
            name="wf1",
            description="",
            version="1",
            category="test",
            step_count=1,
            path=tmp_path / "wf1.yaml",
            raw={},
        )
        wf2 = WorkflowInfo(
            name="wf2",
            description="",
            version="1",
            category="test",
            step_count=1,
            path=tmp_path / "wf2.yaml",
            raw={},
        )
        result = list_workflow_categories([wf1, wf2])
        assert "test" in result
        assert len(result["test"]) == 2

    def test_multiple_categories(self, tmp_path):
        """Multiple categories are separated."""
        workflows = [
            WorkflowInfo(
                name="deploy",
                description="",
                version="1",
                category="release",
                step_count=1,
                path=tmp_path / "deploy.yaml",
                raw={},
            ),
            WorkflowInfo(
                name="test",
                description="",
                version="1",
                category="ci",
                step_count=1,
                path=tmp_path / "test.yaml",
                raw={},
            ),
            WorkflowInfo(
                name="lint",
                description="",
                version="1",
                category="ci",
                step_count=1,
                path=tmp_path / "lint.yaml",
                raw={},
            ),
        ]
        result = list_workflow_categories(workflows)
        assert len(result) == 2
        assert len(result["release"]) == 1
        assert len(result["ci"]) == 2

    def test_missing_category_defaults_to_general(self, tmp_path):
        """Workflows without category default to 'general'."""
        wf = WorkflowInfo(
            name="wf",
            description="",
            version="1",
            category="",  # empty category
            step_count=1,
            path=tmp_path / "wf.yaml",
            raw={},
        )
        result = list_workflow_categories([wf])
        assert "general" in result
        assert len(result["general"]) == 1


# ---------------------------------------------------------------------------
# Integration: Workflow + PlanRunner
# ---------------------------------------------------------------------------


class TestWorkflowPlanRunnerIntegration:
    """Integration tests: Workflow module with PlanRunner."""

    def test_run_workflow_from_discovery(self, tmp_path):
        """Discover and run a workflow."""
        from vibecollab.core.execution_plan import PlanRunner, load_plan

        project = tmp_path / "project"
        project.mkdir()
        (project / "README.md").write_text("# Test", encoding="utf-8")

        # Create a workflow that creates a file
        data = {
            "name": "create-file",
            "steps": [
                {
                    "action": "cli",
                    "command": "python -c \"open('output.txt','w').write('created')\"",
                },
                {"action": "assert", "file": "output.txt", "contains": "created"},
            ],
        }
        _write_workflow(project, "create-file", data)

        # Find and run the workflow
        found = find_workflow("create-file", project)
        assert found is not None

        plan = load_plan(found.path)
        runner = PlanRunner(project_root=project)
        result = runner.run(plan)
        assert result.success
        assert result.passed == 2

    def test_workflow_with_variables(self, tmp_path):
        """Workflow with variable passing between steps (prompt only)."""
        from vibecollab.core.execution_plan import PlanRunner, load_plan, HostResponse

        project = tmp_path / "project"
        project.mkdir()
        (project / "README.md").write_text("# Test", encoding="utf-8")

        # Variable substitution works in prompt steps
        data = {
            "name": "var-test",
            "host": "mock",
            "steps": [
                {"action": "cli", "command": "echo hello_var", "store_as": "msg"},
                {"action": "prompt", "message": "Process: {{msg}}"},
            ],
        }
        _write_workflow(project, "var-test", data)

        found = find_workflow("var-test", project)
        plan = load_plan(found.path)

        # Use mock host to capture variable substitution
        class MockHost:
            def __init__(self):
                self.received = []

            def send(self, message, context=None):
                self.received.append(message)
                return HostResponse(content="ok")

            def close(self):
                pass

        mock_host = MockHost()
        runner = PlanRunner(project_root=project, host=mock_host)
        result = runner.run(plan)
        assert result.success
        # Variable should be substituted in the prompt message
        assert "hello_var" in mock_host.received[0]
