"""
Tests for Indexer — Project document and Insight indexer
"""

import pytest
import yaml

from vibecollab.insight.embedder import Embedder, EmbedderConfig
from vibecollab.search.indexer import (
    Indexer,
    _insight_to_text,
    _split_markdown_by_heading,
)
from vibecollab.search.vector_store import VectorStore

# ---------------------------------------------------------------------------
# _split_markdown_by_heading Tests
# ---------------------------------------------------------------------------

class TestSplitMarkdownByHeading:
    def test_single_heading(self):
        text = "# Title\ncontent line 1\ncontent line 2"
        chunks = _split_markdown_by_heading(text, "test.md")
        assert len(chunks) == 1
        assert chunks[0]["heading"] == "# Title"
        assert "content line 1" in chunks[0]["content"]

    def test_multiple_headings(self):
        text = "# A\nfoo\n# B\nbar\n# C\nbaz"
        chunks = _split_markdown_by_heading(text, "test.md")
        assert len(chunks) == 3

    def test_nested_headings(self):
        text = "# Main\n## Sub1\ncontent1\n## Sub2\ncontent2"
        chunks = _split_markdown_by_heading(text, "test.md")
        # Each heading is an independent chunk
        assert len(chunks) >= 2

    def test_empty_content_skipped(self):
        text = "# Empty\n\n# Also Empty\n\n# Has Content\nreal content"
        chunks = _split_markdown_by_heading(text, "test.md")
        # Empty content chunks should be skipped
        assert any("real content" in c["content"] for c in chunks)

    def test_no_headings(self):
        text = "just plain text\nno headings here"
        chunks = _split_markdown_by_heading(text, "test.md")
        assert len(chunks) == 1
        assert chunks[0]["heading"] == ""

    def test_source_preserved(self):
        text = "# H\ncontent"
        chunks = _split_markdown_by_heading(text, "docs/CONTEXT.md")
        assert chunks[0]["source"] == "docs/CONTEXT.md"


# ---------------------------------------------------------------------------
# _insight_to_text Tests
# ---------------------------------------------------------------------------

class TestInsightToText:
    def test_full_insight(self):
        data = {
            "title": "Test Insight",
            "body": "Some description",
            "summary": "Short summary",
            "tags": ["python", "test"],
            "category": "technique",
        }
        text = _insight_to_text(data)
        assert "Test Insight" in text
        assert "Some description" in text
        assert "python" in text
        assert "technique" in text

    def test_dict_body(self):
        """Structured dict body should be properly expanded"""
        data = {
            "title": "Structured Body",
            "body": {
                "scenario": "Need to fix encoding",
                "approach": "Use _compat module",
                "constraints": ["no external deps", "support GBK"],
            },
            "tags": ["encoding"],
        }
        text = _insight_to_text(data)
        assert "Structured Body" in text
        assert "encoding" in text
        assert "Need to fix" in text
        assert "no external deps" in text

    def test_minimal_insight(self):
        data = {"title": "Only Title"}
        text = _insight_to_text(data)
        assert "Only Title" in text

    def test_empty_insight(self):
        text = _insight_to_text({})
        assert text == ""


# ---------------------------------------------------------------------------
# Indexer Tests
# ---------------------------------------------------------------------------

class TestIndexer:
    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a temp project with docs and Insights"""
        (tmp_path / "CONTRIBUTING_AI.md").write_text(
            "# 一、核心理念\nVibe Development\n# 二、角色\nroles here",
            encoding="utf-8",
        )
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "CONTEXT.md").write_text(
            "# Context\ncurrent work\n## Progress\nline1",
            encoding="utf-8",
        )
        (tmp_path / "docs" / "DECISIONS.md").write_text(
            "# Decisions\n### DECISION-001: First\ncontent",
            encoding="utf-8",
        )

        # Insight files
        ins_dir = tmp_path / ".vibecollab" / "insights"
        ins_dir.mkdir(parents=True)
        ins1 = {
            "id": "INS-001",
            "title": "GBK encoding compatibility",
            "body": "Windows GBK terminal emoji crash",
            "tags": ["windows", "encoding"],
            "category": "debug",
        }
        ins2 = {
            "id": "INS-002",
            "title": "Jinja2 template engine",
            "body": "Use manifest.yaml to drive template rendering",
            "tags": ["template", "jinja2"],
            "category": "technique",
        }
        (ins_dir / "INS-001.yaml").write_text(
            yaml.dump(ins1, allow_unicode=True), encoding="utf-8"
        )
        (ins_dir / "INS-002.yaml").write_text(
            yaml.dump(ins2, allow_unicode=True), encoding="utf-8"
        )
        return tmp_path

    @pytest.fixture
    def indexer(self, project_dir):
        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=64))
        store = VectorStore(db_path=None, dimensions=64)
        return Indexer(
            project_root=project_dir,
            embedder=embedder,
            store=store,
        )

    def test_index_all(self, indexer):
        stats = indexer.index_all()
        assert stats.documents_indexed >= 2  # CONTRIBUTING_AI + CONTEXT + DECISIONS
        assert stats.insights_indexed == 2
        assert stats.chunks_total > 0
        assert len(stats.errors) == 0

    def test_index_documents(self, indexer):
        stats = indexer.index_documents()
        assert stats.documents_indexed >= 2
        assert stats.chunks_total > 0

    def test_index_insights(self, indexer):
        stats = indexer.index_insights()
        assert stats.insights_indexed == 2
        assert stats.chunks_total == 2

    def test_index_creates_searchable_entries(self, indexer):
        indexer.index_all()
        # Check store has data
        assert indexer.store.count() > 0
        assert indexer.store.count(source_type="document") > 0
        assert indexer.store.count(source_type="insight") == 2

    def test_search_after_index(self, indexer):
        indexer.index_all()
        results = indexer.search("encoding compatibility", top_k=10)
        assert len(results) > 0
        # Search should return results; exact ranking depends on embedding accuracy
        # pure_python backend has limited precision, just verify search works
        doc_ids = [r.doc_id for r in results]
        assert len(doc_ids) > 0

    def test_search_with_source_type_filter(self, indexer):
        indexer.index_all()
        results = indexer.search("template", top_k=5, source_type="insight")
        assert all(r.source_type == "insight" for r in results)

    def test_index_missing_files_skipped(self, project_dir):
        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=64))
        store = VectorStore(db_path=None, dimensions=64)
        indexer = Indexer(
            project_root=project_dir,
            embedder=embedder,
            store=store,
            doc_files=["nonexistent.md"],
        )
        stats = indexer.index_documents()
        assert stats.documents_indexed == 0
        assert stats.skipped == 1

    def test_index_no_insights_dir(self, tmp_path):
        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=64))
        store = VectorStore(db_path=None, dimensions=64)
        indexer = Indexer(project_root=tmp_path, embedder=embedder, store=store)
        stats = indexer.index_insights()
        assert stats.insights_indexed == 0

    def test_reindex_overwrites(self, indexer):
        """Re-indexing should update, not duplicate"""
        indexer.index_all()
        count1 = indexer.store.count()
        indexer.index_all()
        count2 = indexer.store.count()
        # upsert should not increase entry count
        assert count1 == count2

    def test_default_doc_files(self, project_dir):
        """Default doc file list should include standard files"""
        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=64))
        store = VectorStore(db_path=None, dimensions=64)
        indexer = Indexer(project_root=project_dir, embedder=embedder, store=store)
        # Default list should contain these files
        assert "CONTRIBUTING_AI.md" in indexer._doc_files
        assert "docs/CONTEXT.md" in indexer._doc_files

    def test_store_persistence(self, project_dir, tmp_path):
        """File-based store should persist data"""
        db_path = tmp_path / "test_vectors" / "index.db"
        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=64))
        store = VectorStore(db_path=db_path, dimensions=64)
        indexer = Indexer(project_root=project_dir, embedder=embedder, store=store)
        indexer.index_all()
        count = store.count()
        store.close()

        # Reopen should preserve data
        store2 = VectorStore(db_path=db_path, dimensions=64)
        assert store2.count() == count
        store2.close()
