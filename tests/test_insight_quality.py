"""
v0.9.4 Insight 质量与生命周期 — 单元测试

覆盖:
- find_duplicates: 去重检测 (精确匹配 / 标题相似 / 标签重叠 / 无重复 / 阈值)
- build_graph / to_mermaid: 全局关联图谱
- export_insights / import_insights: 导入导出 (全量/选择/注册表/冲突策略)
- CLI: graph / export / import / add --force
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from vibecollab.event_log import EventLog
from vibecollab.insight_manager import InsightManager


# ======================================================================
# Fixtures
# ======================================================================

@pytest.fixture
def tmp_project(tmp_path):
    """创建一个临时项目目录，带 project.yaml 和 .vibecollab/"""
    (tmp_path / "project.yaml").write_text(
        "project_name: TestProject\n", encoding="utf-8"
    )
    vibecollab_dir = tmp_path / ".vibecollab"
    vibecollab_dir.mkdir()
    return tmp_path


@pytest.fixture
def mgr(tmp_project):
    """返回一个带 EventLog 的 InsightManager"""
    event_log = EventLog(tmp_project / ".vibecollab" / "events.jsonl")
    return InsightManager(project_root=tmp_project, event_log=event_log)


@pytest.fixture
def populated_mgr(mgr):
    """预填充 3 个 Insight 的 InsightManager"""
    mgr.create(
        title="Windows GBK encoding fix",
        tags=["python", "encoding", "windows"],
        category="debug",
        body={"scenario": "Windows 终端编码", "approach": "使用 _compat.py 兼容层"},
        created_by="ocarina",
    )
    mgr.create(
        title="Pattern Engine architecture",
        tags=["architecture", "jinja2", "template"],
        category="technique",
        body={"scenario": "生成 Markdown 文档", "approach": "Jinja2 模板 + manifest.yaml"},
        created_by="alice",
        derived_from=["INS-001"],
    )
    mgr.create(
        title="MCP Server integration",
        tags=["mcp", "integration", "ide"],
        category="integration",
        body={"scenario": "IDE 集成", "approach": "Model Context Protocol"},
        created_by="bob",
    )
    return mgr


# ======================================================================
# TestFindDuplicates — 去重检测
# ======================================================================

class TestFindDuplicates:
    """测试 InsightManager.find_duplicates()"""

    def test_no_insights_returns_empty(self, mgr):
        result = mgr.find_duplicates("any title", ["any"])
        assert result == []

    def test_exact_fingerprint_match(self, populated_mgr):
        """精确内容匹配 → score=1.0"""
        result = populated_mgr.find_duplicates(
            title="Windows GBK encoding fix",
            tags=["python", "encoding", "windows"],
            body={"scenario": "Windows 终端编码", "approach": "使用 _compat.py 兼容层"},
        )
        assert len(result) == 1
        assert result[0]["score"] == 1.0
        assert result[0]["reason"] == "exact_content"

    def test_title_similarity(self, populated_mgr):
        """标题相似度检测"""
        result = populated_mgr.find_duplicates(
            title="Windows GBK encoding workaround",
            tags=["windows", "encoding"],
        )
        # 标题有重叠 (Windows, GBK, encoding), 标签也有重叠
        assert len(result) >= 1
        best = result[0]
        assert best["id"] == "INS-001"
        assert best["score"] > 0.5

    def test_tag_similarity(self, populated_mgr):
        """标签重叠检测（降低阈值以匹配纯标签重叠场景）"""
        result = populated_mgr.find_duplicates(
            title="Completely different title",
            tags=["python", "encoding", "windows", "gbk"],
            threshold=0.3,
        )
        # 标签有重叠 (python, encoding, windows)
        assert len(result) >= 1
        assert result[0]["id"] == "INS-001"

    def test_no_duplicates(self, populated_mgr):
        """完全不同的内容 → 无重复"""
        result = populated_mgr.find_duplicates(
            title="React hooks best practices",
            tags=["react", "frontend", "hooks"],
        )
        assert result == []

    def test_threshold_control(self, populated_mgr):
        """阈值过低 → 更多匹配"""
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
        """不传 body 时跳过指纹匹配"""
        result = populated_mgr.find_duplicates(
            title="Windows GBK encoding fix",
            tags=["python", "encoding", "windows"],
            # 不传 body → 不做指纹检查，走 Jaccard
        )
        assert len(result) >= 1
        # 不会返回 exact_fingerprint reason
        # (由于标题和标签完全匹配，score 应该很高)
        assert result[0]["score"] >= 0.6


# ======================================================================
# TestBuildGraph — 全局关联图谱
# ======================================================================

class TestBuildGraph:
    """测试 InsightManager.build_graph()"""

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
        """INS-003 是孤立节点"""
        graph = populated_mgr.build_graph()
        assert graph["stats"]["isolated_count"] == 1

    def test_components(self, populated_mgr):
        """3 节点，1 条边 → 2 个连通分量"""
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
    """测试 InsightManager.to_mermaid()"""

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
# TestExport — 导出
# ======================================================================

class TestExportInsights:
    """测试 InsightManager.export_insights()"""

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
        # 先使用一下 INS-001
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
# TestImport — 导入
# ======================================================================

class TestImportInsights:
    """测试 InsightManager.import_insights()"""

    def _make_bundle(self, populated_mgr):
        return populated_mgr.export_insights()

    def test_import_to_empty_project(self, tmp_path):
        """导入到空项目"""
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
        """skip 策略：跳过已存在的 ID"""
        bundle = populated_mgr.export_insights()
        results = populated_mgr.import_insights(bundle, imported_by="test", strategy="skip")
        assert len(results["skipped"]) == 3
        assert len(results["imported"]) == 0

    def test_import_rename(self, populated_mgr):
        """rename 策略：冲突时自动分配新 ID"""
        bundle = populated_mgr.export_insights(insight_ids=["INS-001"])
        results = populated_mgr.import_insights(bundle, imported_by="test", strategy="rename")
        assert len(results["renamed"]) == 1
        assert "INS-001" in results["renamed"]
        new_id = results["renamed"]["INS-001"]
        assert new_id != "INS-001"
        assert populated_mgr.get(new_id) is not None

    def test_import_overwrite(self, populated_mgr):
        """overwrite 策略：覆盖已有"""
        bundle = populated_mgr.export_insights(insight_ids=["INS-001"])
        # 修改标题
        bundle["insights"][0]["title"] = "Updated title"
        results = populated_mgr.import_insights(bundle, imported_by="test", strategy="overwrite")
        assert "INS-001" in results["imported"]
        ins = populated_mgr.get("INS-001")
        assert ins.title == "Updated title"

    def test_import_invalid_format(self, mgr):
        results = mgr.import_insights({"format": "wrong"}, imported_by="test")
        assert results["errors"] == ["Invalid bundle format"]

    def test_import_sets_source_project(self, tmp_path):
        """导入时自动设置来源项目"""
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
        """导入时合并注册表使用计数"""
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
# TestCLI — CLI 命令
# ======================================================================

class TestCLIGraph:
    """测试 vibecollab insight graph"""

    def test_graph_text(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, ["graph"])
        assert result.exit_code == 0
        assert "3 nodes" in result.output
        assert "1 edges" in result.output

    def test_graph_json(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, ["graph", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["stats"]["node_count"] == 3

    def test_graph_mermaid(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, ["graph", "--format", "mermaid"])
        assert result.exit_code == 0
        assert "graph LR" in result.output


class TestCLIExportImport:
    """测试 vibecollab insight export / import"""

    def test_export_stdout(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
        runner = CliRunner()
        result = runner.invoke(insight, ["export"])
        assert result.exit_code == 0
        data = yaml.safe_load(result.output)
        assert data["format"] == "vibecollab-insight-export"
        assert data["count"] == 3

    def test_export_to_file(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
        runner = CliRunner()
        out_path = str(tmp_project / "export.yaml")
        result = runner.invoke(insight, ["export", "-o", out_path])
        assert result.exit_code == 0
        assert Path(out_path).exists()

    def test_import_file(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
        runner = CliRunner()

        # 先导出
        out_path = str(tmp_project / "bundle.yaml")
        runner.invoke(insight, ["export", "-o", out_path])

        # 导入 (skip 策略 → 全部跳过)
        result = runner.invoke(insight, ["import", out_path])
        assert result.exit_code == 0
        assert "Skipped" in result.output

    def test_import_invalid_file(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
        runner = CliRunner()
        # 不存在的文件
        result = runner.invoke(insight, ["import", "nonexistent.yaml"])
        assert result.exit_code == 1

    def test_import_rename_strategy(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
        runner = CliRunner()

        out_path = str(tmp_project / "bundle.yaml")
        runner.invoke(insight, ["export", "--ids", "INS-001", "-o", out_path])

        result = runner.invoke(insight, ["import", out_path, "--strategy", "rename"])
        assert result.exit_code == 0
        assert "Renamed" in result.output


class TestCLIAddDedup:
    """测试 vibecollab insight add 的去重检测"""

    def test_add_detects_duplicate(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
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
        from vibecollab.cli_insight import insight
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
        assert "已创建" in result.output or "INS-004" in result.output

    def test_add_no_duplicate_passes(self, populated_mgr, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from vibecollab.cli_insight import insight
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
        assert "已创建" in result.output
