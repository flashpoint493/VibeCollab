"""Tests for the RoadmapParser module — ROADMAP.md ↔ Task integration."""

import json

import pytest
from click.testing import CliRunner

from vibecollab.roadmap_parser import (
    MILESTONE_HEADER_RE,
    TASK_ID_RE,
    Milestone,
    MilestoneItem,
    RoadmapParser,
    RoadmapStatus,
)
from vibecollab.task_manager import Task, TaskManager, TaskStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ROADMAP = """\
# Project Roadmap

## Current Phase

### v0.9.3 - Task/EventLog 核心工作流接通

- [x] Task CLI 补齐 TASK-DEV-001
- [ ] onboard 注入活跃 Task 概览 TASK-DEV-002
- [x] MCP Server 增强 TASK-DEV-003

### v0.9.4 - Insight 质量与生命周期

- [ ] Insight 自动去重 TASK-DEV-004
- [ ] Insight 关联图谱
- [x] 跨项目 Insight 可移植性

### v0.10.0 - 功能冻结 + 稳定性门槛

- [ ] 外部项目 QA 验证
- [ ] 测试覆盖率 ≥ 85%

## Completed

### v0.9.2 - Insight 沉淀信号增强 ✅

- [x] insight suggest 命令
- [x] 信号快照

---
"""


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temp project with ROADMAP.md and tasks.json."""
    docs = tmp_path / "docs"
    docs.mkdir()
    roadmap = docs / "ROADMAP.md"
    roadmap.write_text(SAMPLE_ROADMAP, encoding="utf-8")

    vc_dir = tmp_path / ".vibecollab"
    vc_dir.mkdir()
    (vc_dir / "tasks.json").write_text("{}", encoding="utf-8")

    return tmp_path


@pytest.fixture
def tm(tmp_project):
    """TaskManager for the temp project."""
    return TaskManager(project_root=tmp_project)


@pytest.fixture
def parser(tmp_project, tm):
    """RoadmapParser with TaskManager."""
    return RoadmapParser(project_root=tmp_project, task_manager=tm)


# ---------------------------------------------------------------------------
# Regex tests
# ---------------------------------------------------------------------------

class TestRegex:
    """Test regex patterns used by the parser."""

    def test_milestone_header_basic(self):
        m = MILESTONE_HEADER_RE.match("### v0.9.3 - Some Title")
        assert m
        assert m.group(1) == "v0.9.3"
        assert m.group(2) == "Some Title"

    def test_milestone_header_no_title(self):
        m = MILESTONE_HEADER_RE.match("### v1.0.0")
        assert m
        assert m.group(1) == "v1.0.0"
        assert m.group(2) is None

    def test_milestone_header_with_check(self):
        m = MILESTONE_HEADER_RE.match("### v0.9.2 - Done ✅")
        assert m
        assert m.group(1) == "v0.9.2"
        assert m.group(2) == "Done"

    def test_milestone_header_two_part_version(self):
        m = MILESTONE_HEADER_RE.match("### v0.9 - Two Part")
        assert m
        assert m.group(1) == "v0.9"

    def test_milestone_header_not_matching(self):
        assert MILESTONE_HEADER_RE.match("## v0.9.3 - H2 header") is None
        assert MILESTONE_HEADER_RE.match("### Not a version") is None

    def test_task_id_re(self):
        ids = TASK_ID_RE.findall("- [x] Fix bug TASK-DEV-001 and TASK-PM-012")
        assert ids == ["TASK-DEV-001", "TASK-PM-012"]

    def test_task_id_re_no_match(self):
        ids = TASK_ID_RE.findall("- [x] No task reference here")
        assert ids == []


# ---------------------------------------------------------------------------
# Parse tests
# ---------------------------------------------------------------------------

class TestParse:
    """Test ROADMAP.md parsing."""

    def test_parse_milestones(self, parser):
        milestones = parser.parse()
        versions = [ms.version for ms in milestones]
        assert "v0.9.3" in versions
        assert "v0.9.4" in versions
        assert "v0.10.0" in versions
        assert "v0.9.2" in versions

    def test_parse_items_count(self, parser):
        milestones = parser.parse()
        ms_map = {ms.version: ms for ms in milestones}

        assert ms_map["v0.9.3"].total == 3
        assert ms_map["v0.9.4"].total == 3
        assert ms_map["v0.10.0"].total == 2
        assert ms_map["v0.9.2"].total == 2

    def test_parse_done_count(self, parser):
        milestones = parser.parse()
        ms_map = {ms.version: ms for ms in milestones}

        assert ms_map["v0.9.3"].done == 2
        assert ms_map["v0.9.4"].done == 1
        assert ms_map["v0.9.2"].done == 2

    def test_parse_task_ids(self, parser):
        milestones = parser.parse()
        ms_map = {ms.version: ms for ms in milestones}

        all_task_ids = []
        for item in ms_map["v0.9.3"].items:
            all_task_ids.extend(item.task_ids)
        assert "TASK-DEV-001" in all_task_ids
        assert "TASK-DEV-002" in all_task_ids
        assert "TASK-DEV-003" in all_task_ids

    def test_parse_progress(self, parser):
        milestones = parser.parse()
        ms_map = {ms.version: ms for ms in milestones}

        assert ms_map["v0.9.3"].progress_pct == pytest.approx(66.7, abs=0.1)
        assert ms_map["v0.9.2"].progress_pct == 100.0

    def test_parse_no_roadmap(self, tmp_path):
        p = RoadmapParser(project_root=tmp_path)
        assert p.parse() == []

    def test_parse_empty_milestone(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "ROADMAP.md").write_text("### v1.0.0 - Empty\n\nSome text\n", encoding="utf-8")
        p = RoadmapParser(project_root=tmp_path)
        milestones = p.parse()
        assert len(milestones) == 1
        assert milestones[0].total == 0
        assert milestones[0].progress_pct == 0.0


# ---------------------------------------------------------------------------
# Status tests
# ---------------------------------------------------------------------------

class TestStatus:
    """Test per-milestone status aggregation."""

    def test_status_without_tasks(self, parser):
        status = parser.status()
        assert isinstance(status, RoadmapStatus)
        assert status.total_items > 0
        assert status.total_tasks_linked > 0  # task IDs found in ROADMAP

    def test_status_with_tasks(self, parser, tm):
        tm.create_task(id="TASK-DEV-001", role="DEV", feature="CLI fix")
        tm.create_task(id="TASK-DEV-002", role="DEV", feature="onboard inject")

        status = parser.status()
        ms_map = {ms["version"]: ms for ms in status.milestones}
        assert ms_map["v0.9.3"]["linked_tasks"] == 3

    def test_status_unlinked_tasks(self, parser, tm):
        tm.create_task(id="TASK-DEV-099", role="DEV", feature="Unlinked")
        status = parser.status()
        assert "TASK-DEV-099" in status.unlinked_task_ids

    def test_status_to_dict(self, parser):
        status = parser.status()
        d = status.to_dict()
        assert "milestones" in d
        assert "total_items" in d
        assert "unlinked_task_ids" in d

    def test_status_task_breakdown(self, parser, tm):
        t = tm.create_task(id="TASK-DEV-001", role="DEV", feature="CLI fix")
        tm.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="test")

        parser._milestones = None  # force re-parse
        status = parser.status()
        ms_map = {ms["version"]: ms for ms in status.milestones}
        breakdown = ms_map["v0.9.3"].get("task_breakdown", {})
        assert breakdown.get("IN_PROGRESS", 0) >= 1


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------

class TestSync:
    """Test bidirectional sync."""

    def test_sync_no_task_manager(self, tmp_project):
        p = RoadmapParser(project_root=tmp_project, task_manager=None)
        actions = p.sync()
        assert actions == []

    def test_sync_tasks_to_roadmap(self, parser, tm):
        """Task DONE → ROADMAP checkbox checked."""
        t = tm.create_task(id="TASK-DEV-002", role="DEV", feature="onboard")
        tm.transition("TASK-DEV-002", TaskStatus.IN_PROGRESS, actor="test")
        tm.transition("TASK-DEV-002", TaskStatus.REVIEW, actor="test")
        tm.transition("TASK-DEV-002", TaskStatus.DONE, actor="test")

        actions = parser.sync(direction="tasks_to_roadmap")
        action_ids = [a.task_id for a in actions]
        assert "TASK-DEV-002" in action_ids

        # Verify the ROADMAP file was updated
        roadmap_text = (parser.roadmap_file).read_text(encoding="utf-8")
        for line in roadmap_text.splitlines():
            if "TASK-DEV-002" in line:
                assert "[x]" in line
                break

    def test_sync_roadmap_to_tasks(self, parser, tm):
        """ROADMAP [x] → task marked DONE."""
        t = tm.create_task(id="TASK-DEV-001", role="DEV", feature="CLI fix")
        assert t.status == TaskStatus.TODO

        actions = parser.sync(direction="roadmap_to_tasks")
        # TASK-DEV-001 is [x] in ROADMAP, should be synced to DONE
        task = tm.get_task("TASK-DEV-001")
        assert task.status == TaskStatus.DONE

    def test_sync_dry_run(self, parser, tm):
        """Dry run doesn't modify anything."""
        tm.create_task(id="TASK-DEV-001", role="DEV", feature="CLI fix")
        actions = parser.sync(direction="roadmap_to_tasks", dry_run=True)
        assert len(actions) > 0
        # Task should still be TODO
        task = tm.get_task("TASK-DEV-001")
        assert task.status == TaskStatus.TODO

    def test_sync_sets_milestone_field(self, parser, tm):
        """Sync should set milestone field on task."""
        tm.create_task(id="TASK-DEV-002", role="DEV", feature="onboard")
        parser.sync(direction="tasks_to_roadmap")
        task = tm.get_task("TASK-DEV-002")
        assert task.milestone == "v0.9.3"

    def test_sync_both_direction(self, parser, tm):
        """Both direction sync works."""
        tm.create_task(id="TASK-DEV-001", role="DEV", feature="CLI fix")
        tm.create_task(id="TASK-DEV-002", role="DEV", feature="onboard")
        # Make TASK-DEV-002 DONE for tasks→roadmap
        tm.transition("TASK-DEV-002", TaskStatus.IN_PROGRESS, actor="test")
        tm.transition("TASK-DEV-002", TaskStatus.REVIEW, actor="test")
        tm.transition("TASK-DEV-002", TaskStatus.DONE, actor="test")

        actions = parser.sync(direction="both")
        types = {a.type for a in actions}
        # TASK-DEV-001 is [x] in ROADMAP → task_to_done
        # TASK-DEV-002 is DONE → checkbox_check
        assert len(actions) >= 1


# ---------------------------------------------------------------------------
# Milestone dataclass tests
# ---------------------------------------------------------------------------

class TestMilestoneDataclass:
    """Test Milestone and MilestoneItem dataclasses."""

    def test_milestone_progress_empty(self):
        ms = Milestone(version="v1.0.0", title="Empty", line_number=1)
        assert ms.total == 0
        assert ms.done == 0
        assert ms.progress_pct == 0.0

    def test_milestone_item(self):
        item = MilestoneItem(
            line_number=10,
            text="- [x] Some task TASK-DEV-001",
            checked=True,
            task_ids=["TASK-DEV-001"],
        )
        assert item.checked
        assert item.task_ids == ["TASK-DEV-001"]

    def test_milestone_progress_calculation(self):
        ms = Milestone(version="v1.0.0", title="Test", line_number=1, items=[
            MilestoneItem(line_number=2, text="a", checked=True),
            MilestoneItem(line_number=3, text="b", checked=False),
            MilestoneItem(line_number=4, text="c", checked=True),
        ])
        assert ms.total == 3
        assert ms.done == 2
        assert ms.progress_pct == pytest.approx(66.7, abs=0.1)


# ---------------------------------------------------------------------------
# Task milestone field tests
# ---------------------------------------------------------------------------

class TestTaskMilestoneField:
    """Test the milestone field on Task dataclass."""

    def test_task_milestone_default(self):
        t = Task(id="TASK-DEV-001", role="DEV", feature="test")
        assert t.milestone == ""

    def test_task_milestone_explicit(self):
        t = Task(id="TASK-DEV-001", role="DEV", feature="test", milestone="v0.9.3")
        assert t.milestone == "v0.9.3"

    def test_task_milestone_roundtrip(self):
        t = Task(id="TASK-DEV-001", role="DEV", feature="test", milestone="v0.10.0")
        d = t.to_dict()
        assert d["milestone"] == "v0.10.0"
        restored = Task.from_dict(d)
        assert restored.milestone == "v0.10.0"

    def test_task_milestone_from_dict_missing(self):
        """from_dict with no milestone key defaults to empty."""
        t = Task.from_dict({"id": "TASK-DEV-001", "role": "DEV", "feature": "test"})
        assert t.milestone == ""

    def test_task_create_with_milestone(self, tm):
        t = tm.create_task(id="TASK-DEV-100", role="DEV", feature="test",
                           milestone="v0.9.3")
        assert t.milestone == "v0.9.3"

    def test_task_list_filter_by_milestone(self, tm):
        tm.create_task(id="TASK-DEV-101", role="DEV", feature="a", milestone="v0.9.3")
        tm.create_task(id="TASK-DEV-102", role="DEV", feature="b", milestone="v0.10.0")
        tm.create_task(id="TASK-DEV-103", role="DEV", feature="c")

        result = tm.list_tasks(milestone="v0.9.3")
        assert len(result) == 1
        assert result[0].id == "TASK-DEV-101"

        result_all = tm.list_tasks()
        assert len(result_all) == 3


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

class TestCLI:
    """Test CLI commands for roadmap integration."""

    def test_roadmap_status_cli(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        # Create a minimal project.yaml
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli_roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["status"])
        assert result.exit_code == 0
        assert "v0.9.3" in result.output

    def test_roadmap_status_json(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli_roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "milestones" in data

    def test_roadmap_parse_cli(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli_roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["parse"])
        assert result.exit_code == 0
        assert "v0.9.3" in result.output

    def test_roadmap_parse_json(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli_roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["parse", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any(ms["version"] == "v0.9.3" for ms in data)

    def test_roadmap_sync_dry_run_cli(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli_roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["sync", "--dry-run"])
        assert result.exit_code == 0

    def test_roadmap_status_empty(self, tmp_path, monkeypatch):
        """Status on project with no ROADMAP.md."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        (vc / "tasks.json").write_text("{}", encoding="utf-8")

        from vibecollab.cli_roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["status"])
        assert result.exit_code == 0
        assert "未在 ROADMAP.md 中发现里程碑" in result.output
