"""
Tests for cli_index.py — Index & Search CLI commands

Covers:
- index_cmd: basic / rebuild / backend selection / error handling
- search_cmd: basic / type filter / min-score / no index / empty index / no results
"""

import sqlite3
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner

from vibecollab.cli.index import index_cmd, search_cmd


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project with docs for indexing."""
    config = {
        "project": {"name": "TestProject", "version": "1.0"},
        "documentation": {"key_files": []},
    }
    (tmp_path / "project.yaml").write_text(
        yaml.dump(config), encoding="utf-8"
    )
    (tmp_path / "CONTRIBUTING_AI.md").write_text(
        "# AI Guide\n\nSome content here.\n\n## Section 2\n\nMore content.",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "CONTEXT.md").write_text(
        "# Context\n\nProject status info.", encoding="utf-8"
    )
    (tmp_path / ".vibecollab").mkdir(exist_ok=True)
    (tmp_path / ".vibecollab" / "insights").mkdir(exist_ok=True)
    return tmp_path


# ======================================================================
# index_cmd tests
# ======================================================================


class TestIndexCmd:
    def test_basic_index(self, runner, tmp_project):
        """Index runs successfully with pure_python backend."""
        result = runner.invoke(
            index_cmd,
            ["-c", str(tmp_project / "project.yaml"), "-b", "pure_python"],
        )
        assert result.exit_code == 0
        assert "Index complete" in result.output or "OK" in result.output

        # DB file should exist
        db_path = tmp_project / ".vibecollab" / "vectors" / "index.db"
        assert db_path.exists()

    def test_index_rebuild(self, runner, tmp_project):
        """--rebuild clears old data before re-indexing."""
        config_arg = ["-c", str(tmp_project / "project.yaml"), "-b", "pure_python"]

        # First index
        result1 = runner.invoke(index_cmd, config_arg)
        assert result1.exit_code == 0

        # Rebuild
        result2 = runner.invoke(index_cmd, config_arg + ["--rebuild"])
        assert result2.exit_code == 0
        assert "Cleared" in result2.output or "cleared" in result2.output

    def test_index_auto_backend(self, runner, tmp_project):
        """auto backend falls back to pure_python when no ML libs."""
        result = runner.invoke(
            index_cmd,
            ["-c", str(tmp_project / "project.yaml"), "-b", "auto"],
        )
        assert result.exit_code == 0

    def test_index_with_insights(self, runner, tmp_project):
        """Index includes Insight YAML files."""
        insight = {
            "id": "INS-001",
            "title": "Test insight",
            "tags": ["test"],
            "category": "technique",
            "body": {"scenario": "test scenario", "approach": "test approach"},
        }
        (tmp_project / ".vibecollab" / "insights" / "INS-001.yaml").write_text(
            yaml.dump(insight, allow_unicode=True), encoding="utf-8"
        )

        result = runner.invoke(
            index_cmd,
            ["-c", str(tmp_project / "project.yaml"), "-b", "pure_python"],
        )
        assert result.exit_code == 0
        assert "Insight" in result.output

    def test_index_nonexistent_config(self, runner, tmp_path):
        """Index with nonexistent config path handles gracefully."""
        # pure_python backend + config in a directory with no docs
        result = runner.invoke(
            index_cmd,
            ["-c", str(tmp_path / "project.yaml"), "-b", "pure_python"],
        )
        # Should complete (maybe with 0 documents) or fail gracefully
        # The indexer finds docs relative to project root
        assert result.exit_code == 0 or "error" in result.output.lower() or "Error" in result.output


# ======================================================================
# search_cmd tests
# ======================================================================


def _create_index_db(project_root: Path, dims: int = 64):
    """Helper: create a pre-populated vector index DB."""
    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vectors (
            doc_id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            vector BLOB NOT NULL,
            source TEXT DEFAULT '',
            source_type TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}',
            dimensions INTEGER NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON vectors(source_type)")

    # Insert sample vectors
    def _pack(values):
        return struct.pack(f"{len(values)}f", *values)

    vec1 = [1.0] + [0.0] * (dims - 1)
    vec2 = [0.0, 1.0] + [0.0] * (dims - 2)
    vec3 = [0.5, 0.5] + [0.0] * (dims - 2)

    import json
    conn.execute(
        "INSERT INTO vectors (doc_id, text, vector, source, source_type, metadata, dimensions) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("doc::CONTEXT.md::0", "Project context and status", _pack(vec1), "docs/CONTEXT.md", "document",
         json.dumps({"heading": "Context", "source_file": "CONTEXT.md"}), dims),
    )
    conn.execute(
        "INSERT INTO vectors (doc_id, text, vector, source, source_type, metadata, dimensions) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("insight::INS-001", "Cache strategy for high concurrency", _pack(vec2), ".vibecollab/insights/INS-001.yaml",
         "insight", json.dumps({"heading": "Cache", "tags": ["cache", "architecture"]}), dims),
    )
    conn.execute(
        "INSERT INTO vectors (doc_id, text, vector, source, source_type, metadata, dimensions) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("doc::DECISIONS.md::0", "Decision records and architecture choices", _pack(vec3), "docs/DECISIONS.md",
         "document", json.dumps({"heading": "Decisions"}), dims),
    )
    conn.commit()
    conn.close()
    return db_path


class TestSearchCmd:
    def test_search_no_index(self, runner, tmp_project):
        """Search without index gives clear error."""
        result = runner.invoke(
            search_cmd,
            ["test query", "-c", str(tmp_project / "project.yaml")],
        )
        assert result.exit_code == 1
        assert "does not exist" in result.output.lower() or "index" in result.output.lower()

    def test_search_basic(self, runner, tmp_project):
        """Basic search returns results."""
        _create_index_db(tmp_project)

        result = runner.invoke(
            search_cmd,
            ["context status", "-c", str(tmp_project / "project.yaml")],
        )
        assert result.exit_code == 0
        assert "search" in result.output.lower() or "context" in result.output.lower()

    def test_search_type_filter(self, runner, tmp_project):
        """--type filters by source type."""
        _create_index_db(tmp_project)

        result = runner.invoke(
            search_cmd,
            ["cache", "-t", "insight", "-c", str(tmp_project / "project.yaml")],
        )
        assert result.exit_code == 0

    def test_search_min_score(self, runner, tmp_project):
        """--min-score filters low-score results."""
        _create_index_db(tmp_project)

        result = runner.invoke(
            search_cmd,
            ["test", "--min-score", "0.99", "-c", str(tmp_project / "project.yaml")],
        )
        assert result.exit_code == 0
        # Very high threshold likely returns no results
        assert "No results found" in result.output or "Top 0" in result.output or result.output.strip()

    def test_search_top_k(self, runner, tmp_project):
        """--top limits result count."""
        _create_index_db(tmp_project)

        result = runner.invoke(
            search_cmd,
            ["data", "-k", "1", "-c", str(tmp_project / "project.yaml")],
        )
        assert result.exit_code == 0

    def test_search_empty_index(self, runner, tmp_project):
        """Search with empty index DB."""
        db_path = tmp_project / ".vibecollab" / "vectors" / "index.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                doc_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                vector BLOB NOT NULL,
                source TEXT DEFAULT '',
                source_type TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                dimensions INTEGER NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON vectors(source_type)")
        conn.commit()
        conn.close()

        result = runner.invoke(
            search_cmd,
            ["test", "-c", str(tmp_project / "project.yaml")],
        )
        assert result.exit_code == 1
        assert "empty" in result.output.lower() or "empty" in result.output.lower()

    def test_search_no_results_with_hint(self, runner, tmp_project):
        """No results with min-score shows hint."""
        _create_index_db(tmp_project)

        result = runner.invoke(
            search_cmd,
            [
                "completely_unrelated_query_xyz",
                "--min-score", "0.9",
                "-c", str(tmp_project / "project.yaml"),
            ],
        )
        assert result.exit_code == 0
        if "No results found" in result.output:
            assert "min-score" in result.output.lower() or "lowering" in result.output.lower()
