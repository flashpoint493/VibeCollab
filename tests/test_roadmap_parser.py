"""Tests for the RoadmapParser module — ROADMAP.md ↔ Task integration."""

import json

import pytest
from click.testing import CliRunner

from vibecollab.domain.roadmap_parser import (
    MILESTONE_FORMAT_HINT,
    MILESTONE_HEADER_RE,
    TASK_ID_RE,
    Milestone,
    MilestoneItem,
    RoadmapParser,
    RoadmapStatus,
)
from vibecollab.domain.task_manager import Task, TaskManager, TaskStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ROADMAP = """\
# Project Roadmap

## Current Phase

### v0.9.3 - Core Task/EventLog workflow integration

- [x] Task CLI completion TASK-DEV-001
- [ ] onboard inject active Task overview TASK-DEV-002
- [x] MCP Server enhancement TASK-DEV-003

### v0.9.4 - Insight quality and lifecycle

- [ ] Insight auto-dedup TASK-DEV-004
- [ ] Insight relation graph
- [x] Cross-project Insight portability

### v0.10.0 - Feature freeze + stability gate

- [ ] External project QA validation
- [ ] Test coverage >= 85%

## Completed

### v0.9.2 - Insight solidification signal enhancement ✅

- [x] insight suggest command
- [x] Signal snapshot

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
        assert MILESTONE_HEADER_RE.match("##### v0.9.3 - H5 too deep") is None

    def test_milestone_header_h4(self):
        """H4 headers should NOT match — only ### is accepted."""
        assert MILESTONE_HEADER_RE.match("#### v0.5.9 - Pattern Engine ✅") is None

    def test_milestone_header_h4_no_title(self):
        assert MILESTONE_HEADER_RE.match("#### v0.5.0") is None

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
        tm.create_task(id="TASK-DEV-001", role="DEV", feature="CLI fix")
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
        """Task DONE -> ROADMAP checkbox checked."""
        tm.create_task(id="TASK-DEV-002", role="DEV", feature="onboard")
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

        parser.sync(direction="roadmap_to_tasks")
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
        # TASK-DEV-001 is [x] in ROADMAP -> task_to_done
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

        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["status"])
        assert result.exit_code == 0
        assert "v0.9.3" in result.output

    def test_roadmap_status_json(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "milestones" in data

    def test_roadmap_parse_cli(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["parse"])
        assert result.exit_code == 0
        assert "v0.9.3" in result.output

    def test_roadmap_parse_json(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["parse", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any(ms["version"] == "v0.9.3" for ms in data)

    def test_roadmap_sync_dry_run_cli(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["sync", "--dry-run"])
        assert result.exit_code == 0

    def test_roadmap_status_empty(self, tmp_path, monkeypatch):
        """Status on project with no ROADMAP.md shows format hint."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "project.yaml").write_text("project:\n  name: test\n", encoding="utf-8")
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        (vc / "tasks.json").write_text("{}", encoding="utf-8")

        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["status"])
        assert result.exit_code == 0
        assert "No milestones found in ROADMAP.md" in result.output


# ---------------------------------------------------------------------------
# v0.9.7: H4 headers are NOT recognized — strict ### only
# ---------------------------------------------------------------------------

SAMPLE_ROADMAP_H4_ONLY = """\
# Project Roadmap

## Phase 2 - Multi-role

#### v0.5.9 - Pattern Engine ✅

- [x] PatternEngine implementation TASK-DEV-010
- [x] Template overlay

#### v0.5.8 - AI CLI

- [ ] AI ask/chat TASK-DEV-011
- [x] Agent mode TASK-DEV-012

## Future

### v0.10.0 - Release

- [ ] Final QA
"""


class TestH4HeadersRejected:
    """Verify that #### milestone headers are NOT parsed (strict ### only)."""

    @pytest.fixture
    def h4_project(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "ROADMAP.md").write_text(SAMPLE_ROADMAP_H4_ONLY, encoding="utf-8")
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        (vc / "tasks.json").write_text("{}", encoding="utf-8")
        return tmp_path

    def test_h4_milestones_ignored(self, h4_project):
        """Only ### v0.10.0 should be parsed; #### v0.5.x should be skipped."""
        parser = RoadmapParser(project_root=h4_project)
        milestones = parser.parse()
        versions = [ms.version for ms in milestones]
        assert "v0.5.9" not in versions
        assert "v0.5.8" not in versions
        assert "v0.10.0" in versions

    def test_h4_items_not_collected(self, h4_project):
        """Items under #### headers should not be collected."""
        parser = RoadmapParser(project_root=h4_project)
        milestones = parser.parse()
        assert len(milestones) == 1
        # Only "Final QA" under ### v0.10.0
        assert milestones[0].version == "v0.10.0"
        assert milestones[0].total == 1

    def test_h4_task_ids_not_collected(self, h4_project):
        """Task IDs under #### headers should not be linked."""
        parser = RoadmapParser(project_root=h4_project)
        milestones = parser.parse()
        all_ids = []
        for ms in milestones:
            for item in ms.items:
                all_ids.extend(item.task_ids)
        assert "TASK-DEV-010" not in all_ids
        assert "TASK-DEV-011" not in all_ids

    def test_only_h3_parsed_in_mixed(self, h4_project):
        """In mixed H3/H4 ROADMAP, only H3 milestones are returned."""
        parser = RoadmapParser(project_root=h4_project)
        milestones = parser.parse()
        assert len(milestones) == 1
        assert milestones[0].version == "v0.10.0"

    def test_h4_with_non_milestone_h3(self, tmp_path):
        """#### v0.5.0 is ignored; ### Non-milestone is also ignored."""
        docs = tmp_path / "docs"
        docs.mkdir()
        content = """\
#### v0.5.0 - Feature

- [x] Item A

### Non-milestone section

- [ ] Should not be in any milestone
"""
        (docs / "ROADMAP.md").write_text(content, encoding="utf-8")
        parser = RoadmapParser(project_root=tmp_path)
        milestones = parser.parse()
        assert len(milestones) == 0


# ---------------------------------------------------------------------------
# v0.9.7: Format hint tests
# ---------------------------------------------------------------------------

class TestFormatHint:
    """Test that format hints are shown in CLI when no milestones found."""

    def _setup_empty(self, tmp_path):
        """Setup project with ROADMAP that has no parseable milestones."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "ROADMAP.md").write_text(
            "# Roadmap\n\n## Phase 0\n\n#### M0: Init\n\n- [ ] Something\n",
            encoding="utf-8",
        )
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        (vc / "tasks.json").write_text("{}", encoding="utf-8")
        (tmp_path / "project.yaml").write_text(
            "project:\n  name: test\n", encoding="utf-8"
        )

    def test_parse_empty_shows_hint(self, tmp_path, monkeypatch):
        self._setup_empty(tmp_path)
        monkeypatch.chdir(tmp_path)
        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["parse"])
        assert result.exit_code == 0
        assert "No milestones found in ROADMAP.md" in result.output
        assert "### v0.1.0" in result.output
        assert "TASK-DEV-001" in result.output

    def test_status_empty_shows_hint(self, tmp_path, monkeypatch):
        self._setup_empty(tmp_path)
        monkeypatch.chdir(tmp_path)
        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["status"])
        assert result.exit_code == 0
        assert "### v0.1.0" in result.output

    def test_sync_empty_shows_hint(self, tmp_path, monkeypatch):
        self._setup_empty(tmp_path)
        monkeypatch.chdir(tmp_path)
        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["sync"])
        assert result.exit_code == 0
        assert "cannot sync" in result.output.lower()
        assert "### v0.1.0" in result.output

    def test_sync_empty_json_returns_empty(self, tmp_path, monkeypatch):
        self._setup_empty(tmp_path)
        monkeypatch.chdir(tmp_path)
        from vibecollab.cli.roadmap import roadmap_group
        runner = CliRunner()
        result = runner.invoke(roadmap_group, ["sync", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == []

    def test_format_hint_constant(self):
        """MILESTONE_FORMAT_HINT contains key format examples."""
        assert "### v0.1.0" in MILESTONE_FORMAT_HINT
        assert "TASK-DEV-001" in MILESTONE_FORMAT_HINT
        assert "- [ ]" in MILESTONE_FORMAT_HINT

    def test_init_template_parseable(self, tmp_path):
        """ROADMAP generated by vibecollab init should be parseable."""
        docs = tmp_path / "docs"
        docs.mkdir()
        # Simulate the new init template content
        init_roadmap = """\
# Test Roadmap

## Milestones

### v0.1.0 - Project initialization

- [ ] Define project direction
- [ ] Set up development environment
- [ ] Complete core decisions
"""
        (docs / "ROADMAP.md").write_text(init_roadmap, encoding="utf-8")
        parser = RoadmapParser(project_root=tmp_path)
        milestones = parser.parse()
        assert len(milestones) == 1
        assert milestones[0].version == "v0.1.0"
        assert milestones[0].total == 3
