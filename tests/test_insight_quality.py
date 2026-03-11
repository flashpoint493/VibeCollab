"""
v0.9.4 Insight quality and lifecycle - unit tests

Coverage:
- find_duplicates: deduplication (exact match / title similarity / tag overlap / no duplicates / threshold)
- build_graph / to_mermaid: global association graph
- export_insights / import_insights: import/export (full/selective/registry/conflict strategies)
- CLI: graph / export / import / add --force
"""

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from vibecollab.domain.event_log import EventLog
from vibecollab.insight.manager import InsightManager

# ======================================================================
# Fixtures
# ======================================================================

@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with project.yaml and .vibecollab/"""
    (tmp_path / "project.yaml").write_text(
        "project_name: TestProject\n", encoding="utf-8"
    )
    vibecollab_dir = tmp_path / ".vibecollab"
    vibecollab_dir.mkdir()
    return tmp_path


@pytest.fixture
def mgr(tmp_project):
    """Return an InsightManager with EventLog"""
    event_log = EventLog(tmp_project / ".vibecollab" / "events.jsonl")
    return InsightManager(project_root=tmp_project, event_log=event_log)


@pytest.fixture
def populated_mgr(mgr):
    """Pre-populated InsightManager with 3 Insights"""
    mgr.create(
        title="Windows GBK encoding fix",
        tags=["python", "encoding", "windows"],
        category="debug",
        body={"scenario": "Windows terminal encoding", "approach": "Use _compat.py compatibility layer"},
        created_by="ocarina",
    )
    mgr.create(
        title="Pattern Engine architecture",
        tags=["architecture", "jinja2", "template"],
        category="technique",
        body={"scenario": "Generate Markdown docs", "approach": "Jinja2 templates + manifest.yaml"},
        created_by="alice",
        derived_from=["INS-001"],
    )
    mgr.create(
        title="MCP Server integration",
        tags=["mcp", "integration", "ide"],
        category="integration",
        body={"scenario": "IDE integration", "approach": "Model Context Protocol"},
        created_by="bob",
    )
    return mgr


# ======================================================================
# TestFindDuplicates - Deduplication detection
# ======================================================================

class TestFindDuplicates:
    """Test InsightManager.find_duplicates()"""

    def test_no_insights_returns_empty(self, mgr):
        result = mgr.find_duplicates("any title", ["any"])
        assert result == []

    def test_exact_fingerprint_match(self, populated_mgr):
        """Exact content match -> score=1.0"""
        result = populated_mgr.find_duplicates(
            title="Windows GBK encoding fix",
            tags=["python", "encoding", "windows"],
            body={"scenario": "Windows terminal encoding", "approach": "Use _compat.py compatibility layer"},
        )
        assert len(result) == 1
        assert result[0]["score"] == 1.0
        assert result[0]["reason"] == "exact_content"

    def test_title_similarity(self, populated_mgr):
        """Title similarity detection"""
        result = populated_mgr.find_duplicates(
            title="Windows GBK encoding workaround",
            tags=["windows", "encoding"],
        )
        # Title has overlap (Windows, GBK, encoding), tags also overlap
        assert len(result) >= 1
        best = result[0]
        assert best["id"] == "INS-001"
        assert best["score"] > 0.5

    def test_tag_similarity(self, populated_mgr):
        """Tag overlap detection (lowered threshold to match pure tag overlap scenario)"""
        result = populated_mgr.find_duplicates(
            title="Completely different title",
            tags=["python", "encoding", "windows", "gbk"],
            threshold=0.3,
        )
        # Tags have overlap (python, encoding, windows)
        assert len(result) >= 1
        assert result[0]["id"] == "INS-001"

    def test_no_duplicates(self, populated_mgr):
        """Completely different content -> no duplicates"""
        result = populated_mgr.find_duplicates(
            title="React hooks best practices",
            tags=["react", "frontend", "hooks"],
        )
        assert result == []

    def test_threshold_control(self, populated_mgr):
        """Too low threshold -> more matches"""
        result_high = populated_mgr.find_duplicates(
            title="encoding fix",
            tags=["python"],
            threshold=0.8,
        )
        result_low = populated_mgr.find_duplicates(
            title="encoding fix",
            tags=["python"],
            threshold=0.2,
        )
        assert len(result_low) >= len(result_high)

    def test_without_body(self, populated_mgr):
        """No body skips fingerprint matching"""
        result = populated_mgr.find_duplicates(
            title="Windows GBK encoding fix",
            tags=["python", "encoding", "windows"],
            # No body -> skip fingerprint check, use Jaccard
        )
        assert len(result) >= 1
        # Won't return exact_fingerprint reason
        # (Since title and tags fully match, score should be high)
        assert result[0]["score"] >= 0.6


# ======================================================================
# TestBuildGraph — Global association graph
# ======================================================================

class TestBuildGraph:
    """Test InsightManager.build_graph()"""

    def test_empty_graph(self, mgr):
        graph = mgr.build_graph()
        assert graph["nodes"] == []
        assert graph["edges"] == []
        assert graph["stats"]["node_count"] == 0

    def test_graph_with_edges(self, populated_mgr):
        """INS-002 derived_from INS-001"""
        graph = populated_mgr.build_graph()
        assert graph["stats"]["node_count"] == 3
        assert graph["stats"]["edge_count"] == 1
        assert graph["edges"][0]["from"] == "INS-001"
        assert graph["edges"][0]["to"] == "INS-002"

    def test_isolated_count(self, populated_mgr):
        """INS-003 is an isolated node"""
        graph = populated_mgr.build_graph()
        assert graph["stats"]["isolated_count"] == 1

    def test_components(self, populated_mgr):
        """3 nodes, 1 edge -> 2 connected components"""
        graph = populated_mgr.build_graph()
        assert graph["stats"]["components"] == 2

    def test_node_data(self, populated_mgr):
        graph = populated_mgr.build_graph()
        node_ids = {n["id"] for n in graph["nodes"]}
        assert node_ids == {"INS-001", "INS-002", "INS-003"}
        ins1 = next(n for n in graph["nodes"] if n["id"] == "INS-001")
        assert ins1["category"] == "debug"
        assert ins1["active"] is True


class TestToMermaid:
    """Test InsightManager.to_mermaid()"""

    def test_mermaid_output(self, populated_mgr):
        mermaid = populated_mgr.to_mermaid()
        assert mermaid.startswith("graph LR")
        assert "INS-001" in mermaid
        assert "INS-002" in mermaid
        assert "-->" in mermaid

    def test_mermaid_empty(self, mgr):
        mermaid = mgr.to_mermaid()
        assert mermaid == "graph LR"


# ======================================================================
# TestExport — Export
# ======================================================================

class TestExportInsights:
    """Test InsightManager.export_insights()"""

    def test_export_all(self, populated_mgr):
        bundle = populated_mgr.export_insights()
        assert bundle["format"] == "vibecollab-insight-export"
        assert bundle["version"] == "1"
        assert bundle["count"] == 3
        assert len(bundle["insights"]) == 3
        assert bundle["source_project"] == "TestProject"
        assert "registry" not in bundle

    def test_export_selected(self, populated_mgr):
        bundle = populated_mgr.export_insights(insight_ids=["INS-001", "INS-003"])
        assert bundle["count"] == 2
        ids = {ins["id"] for ins in bundle["insights"]}
        assert ids == {"INS-001", "INS-003"}

    def test_export_with_registry(self, populated_mgr):
        # First use INS-001
        populated_mgr.record_use("INS-001", "test_user")
        bundle = populated_mgr.export_insights(include_registry=True)
        assert "registry" in bundle
        assert "INS-001" in bundle["registry"]
        assert bundle["registry"]["INS-001"]["used_count"] == 1

    def test_export_empty(self, mgr):
        bundle = mgr.export_insights()
        assert bundle["count"] == 0
        assert bundle["insights"] == []


# ======================================================================
# TestImport - Import
# ======================================================================

class TestImportInsights:
    """Test InsightManager.import_insights()"""

    def _make_bundle(self, populated_mgr):
        return populated_mgr.export_insights()

    def test_import_to_empty_project(self, tmp_path):
        """Import to empty project"""
        (tmp_path / "project.yaml").write_text("project_name: Target\n")
        (tmp_path / ".vibecollab").mkdir()
        target_mgr = InsightManager(project_root=tmp_path)

        bundle = {
            "format": "vibecollab-insight-export",
            "version": "1",
            "insights": [
                {
                    "kind": "insight", "version": "1",
                    "id": "INS-001",
                    "title": "Test insight",
                    "tags": ["test"],
                    "category": "technique",
                    "body": {"scenario": "test", "approach": "test"},
                    "origin": {"created_by": "alice", "created_at": "2026-01-01"},
                }
            ],
        }
        results = target_mgr.import_insights(bundle, imported_by="bob")
        assert "INS-001" in results["imported"]
        assert target_mgr.get("INS-001") is not None

    def test_import_skip_existing(self, populated_mgr, tmp_project):
        """skip strategy: skip existing IDs"""
        bundle = populated_mgr.export_insights()
        results = populated_mgr.import_insights(bundle, imported_by="test", strategy="skip")
        assert len(results["skipped"]) == 3
        assert len(results["imported"]) == 0

    def test_import_rename(self, populated_mgr):
        """rename strategy: auto-assign new ID on conflict"""
        bundle = populated_mgr.export_insights(insight_ids=["INS-001"])
        results = populated_mgr.import_insights(bundle, imported_by="test", strategy="rename")
        assert len(results["renamed"]) == 1
        assert "INS-001" in results["renamed"]
        new_id = results["renamed"]["INS-001"]
        assert new_id != "INS-001"
        assert populated_mgr.get(new_id) is not None

    def test_import_overwrite(self, populated_mgr):
        """overwrite strategy: overwrite existing"""
        bundle = populated_mgr.export_insights(insight_ids=["INS-001"])
        # Modify title
        bundle["insights"][0]["title"] = "Updated title"
        results = populated_mgr.import_insights(bundle, imported_by="test", strategy="overwrite")
        assert "INS-001" in results["imported"]
        ins = populated_mgr.get("INS-001")
        assert ins.title == "Updated title"

    def test_import_invalid_format(self, mgr):
        results = mgr.import_insights({"format": "wrong"}, imported_by="test")
        assert results["errors"] == ["Invalid bundle format"]

    def test_import_sets_source_project(self, tmp_path):
        """Auto-set source project on import"""
        (tmp_path / "project.yaml").write_text("project_name: Target\n")
        (tmp_path / ".vibecollab").mkdir()
        target_mgr = InsightManager(project_root=tmp_path)

        bundle = {
            "format": "vibecollab-insight-export",
            "version": "1",
            "source_project": "SourceProject",
            "insights": [
                {
                    "kind": "insight", "version": "1",
                    "id": "INS-001",
                    "title": "Cross project insight",
                    "tags": ["cross"],
                    "category": "workflow",
                    "body": {"scenario": "test", "approach": "test"},
                    "origin": {"created_by": "alice", "created_at": "2026-01-01"},
                }
            ],
        }
        target_mgr.import_insights(bundle, imported_by="bob")
        ins = target_mgr.get("INS-001")
        assert ins.origin.source_project == "SourceProject"

    def test_import_with_registry(self, tmp_path):
        """Merge registry use counts on import"""
        (tmp_path / "project.yaml").write_text("project_name: Target\n")
        (tmp_path / ".vibecollab").mkdir()
        target_mgr = InsightManager(project_root=tmp_path)

        bundle = {
            "format": "vibecollab-insight-export",
            "version": "1",
            "insights": [
                {
                    "kind": "insight", "version": "1",
                    "id": "INS-001",
                    "title": "Test",
                    "tags": ["t"],
                    "category": "technique",
                    "body": {"scenario": "s", "approach": "a"},
                    "origin": {"created_by": "a", "created_at": "2026-01-01"},
                }
            ],
            "registry": {
                "INS-001": {"weight": 1.0, "used_count": 5},
            },
        }
        target_mgr.import_insights(bundle, imported_by="bob")
        entries, _ = target_mgr.get_registry()
        assert entries["INS-001"].used_count == 5


# ======================================================================
# TestCLI - CLI commands
# ======================================================================

class TestCLIGraph:
    """Test vibecollab insight graph"""

    def test_graph_text(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, ["graph"])
        assert result.exit_code == 0
        assert "3 nodes" in result.output
        assert "1 edges" in result.output

    def test_graph_json(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, ["graph", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["stats"]["node_count"] == 3

    def test_graph_mermaid(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, ["graph", "--format", "mermaid"])
        assert result.exit_code == 0
        assert "graph LR" in result.output


class TestCLIExportImport:
    """Test vibecollab insight export / import"""

    def test_export_stdout(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, ["export"])
        assert result.exit_code == 0
        data = yaml.safe_load(result.output)
        assert data["format"] == "vibecollab-insight-export"
        assert data["count"] == 3

    def test_export_to_file(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        out_path = str(tmp_project / "export.yaml")
        result = runner.invoke(insight, ["export", "-o", out_path])
        assert result.exit_code == 0
        assert Path(out_path).exists()

    def test_import_file(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()

        # Export first
        out_path = str(tmp_project / "bundle.yaml")
        runner.invoke(insight, ["export", "-o", out_path])

        # Import (skip strategy -> all skipped)
        result = runner.invoke(insight, ["import", out_path])
        assert result.exit_code == 0
        assert "Skipped" in result.output

    def test_import_invalid_file(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        # Non-existent file
        result = runner.invoke(insight, ["import", "nonexistent.yaml"])
        assert result.exit_code == 1

    def test_import_rename_strategy(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()

        out_path = str(tmp_project / "bundle.yaml")
        runner.invoke(insight, ["export", "--ids", "INS-001", "-o", out_path])

        result = runner.invoke(insight, ["import", out_path, "--strategy", "rename"])
        assert result.exit_code == 0
        assert "Renamed" in result.output


class TestCLIAddDedup:
    """Test vibecollab insight add deduplication detection"""

    def test_add_detects_duplicate(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, [
            "add",
            "-t", "Windows GBK encoding fix",
            "--tags", "python,encoding,windows",
            "-c", "debug",
            "-s", "same scenario",
            "-a", "same approach",
        ])
        assert result.exit_code == 1
        assert "duplicate" in result.output.lower()

    def test_add_force_bypasses_dedup(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, [
            "add",
            "-t", "Windows GBK encoding fix",
            "--tags", "python,encoding,windows",
            "-c", "debug",
            "-s", "same scenario",
            "-a", "same approach",
            "--force",
        ])
        assert result.exit_code == 0
        assert "Created" in result.output or "INS-004" in result.output

    def test_add_no_duplicate_passes(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli.insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, [
            "add",
            "-t", "Completely unique insight",
            "--tags", "unique,special",
            "-c", "workflow",
            "-s", "unique scenario",
            "-a", "unique approach",
        ])
        assert result.exit_code == 0
        assert "Created" in result.output
