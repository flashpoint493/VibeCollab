"""
Tests for VectorStore — 本地持久化向量存储
"""

import json
import math

import pytest

from vibecollab.search.vector_store import (
    SearchResult,
    VectorDocument,
    VectorStore,
    _pack_vector,
    _unpack_vector,
    cosine_similarity,
)


# ---------------------------------------------------------------------------
# cosine_similarity Tests
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(cosine_similarity(a, b) + 1.0) < 1e-6

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 1.0]
        assert cosine_similarity(a, b) == 0.0

    def test_dimension_mismatch_raises(self):
        with pytest.raises(ValueError, match="维度不匹配"):
            cosine_similarity([1.0, 2.0], [1.0])


# ---------------------------------------------------------------------------
# pack/unpack Tests
# ---------------------------------------------------------------------------

class TestPackUnpack:
    def test_roundtrip(self):
        original = [1.0, 2.5, -3.14, 0.0]
        packed = _pack_vector(original)
        unpacked = _unpack_vector(packed)
        assert len(unpacked) == len(original)
        for a, b in zip(original, unpacked):
            assert abs(a - b) < 1e-5

    def test_empty(self):
        packed = _pack_vector([])
        unpacked = _unpack_vector(packed)
        assert unpacked == []


# ---------------------------------------------------------------------------
# VectorStore Core Tests
# ---------------------------------------------------------------------------

class TestVectorStore:
    @pytest.fixture
    def store(self):
        """内存模式 VectorStore"""
        return VectorStore(db_path=None, dimensions=4)

    @pytest.fixture
    def sample_doc(self):
        return VectorDocument(
            doc_id="test:001",
            text="hello world",
            vector=[1.0, 0.0, 0.0, 0.0],
            source="test.md",
            source_type="document",
            metadata={"tags": ["test"]},
        )

    def test_upsert_and_get(self, store, sample_doc):
        store.upsert(sample_doc)
        result = store.get("test:001")
        assert result is not None
        assert result.doc_id == "test:001"
        assert result.text == "hello world"
        assert result.source == "test.md"
        assert result.source_type == "document"
        assert result.metadata == {"tags": ["test"]}
        # 向量应一致（浮点精度）
        for a, b in zip(result.vector, sample_doc.vector):
            assert abs(a - b) < 1e-5

    def test_upsert_overwrites(self, store, sample_doc):
        store.upsert(sample_doc)
        updated = VectorDocument(
            doc_id="test:001",
            text="updated text",
            vector=[0.0, 1.0, 0.0, 0.0],
            source="new.md",
            source_type="insight",
        )
        store.upsert(updated)
        result = store.get("test:001")
        assert result.text == "updated text"
        assert result.source == "new.md"

    def test_get_nonexistent(self, store):
        assert store.get("nonexistent") is None

    def test_delete(self, store, sample_doc):
        store.upsert(sample_doc)
        assert store.delete("test:001") is True
        assert store.get("test:001") is None

    def test_delete_nonexistent(self, store):
        assert store.delete("nonexistent") is False

    def test_count(self, store):
        assert store.count() == 0
        store.upsert(VectorDocument("a", "text", [1, 0, 0, 0], source_type="doc"))
        store.upsert(VectorDocument("b", "text", [0, 1, 0, 0], source_type="insight"))
        assert store.count() == 2
        assert store.count(source_type="doc") == 1
        assert store.count(source_type="insight") == 1

    def test_list_doc_ids(self, store):
        store.upsert(VectorDocument("c", "text", [1, 0, 0, 0]))
        store.upsert(VectorDocument("a", "text", [0, 1, 0, 0]))
        store.upsert(VectorDocument("b", "text", [0, 0, 1, 0]))
        ids = store.list_doc_ids()
        assert ids == ["a", "b", "c"]  # sorted

    def test_list_doc_ids_filtered(self, store):
        store.upsert(VectorDocument("a", "t", [1, 0, 0, 0], source_type="doc"))
        store.upsert(VectorDocument("b", "t", [0, 1, 0, 0], source_type="insight"))
        assert store.list_doc_ids(source_type="doc") == ["a"]

    def test_delete_by_source_type(self, store):
        store.upsert(VectorDocument("a", "t", [1, 0, 0, 0], source_type="doc"))
        store.upsert(VectorDocument("b", "t", [0, 1, 0, 0], source_type="doc"))
        store.upsert(VectorDocument("c", "t", [0, 0, 1, 0], source_type="insight"))
        deleted = store.delete_by_source_type("doc")
        assert deleted == 2
        assert store.count() == 1

    def test_dimension_mismatch_raises(self, store):
        bad_doc = VectorDocument("bad", "text", [1.0, 0.0])  # 2 dims, 期望 4
        with pytest.raises(ValueError, match="维度不匹配"):
            store.upsert(bad_doc)

    def test_upsert_batch(self, store):
        docs = [
            VectorDocument(f"batch:{i}", f"text {i}", [float(i), 0, 0, 0])
            for i in range(5)
        ]
        count = store.upsert_batch(docs)
        assert count == 5
        assert store.count() == 5

    def test_upsert_batch_skips_bad_dimensions(self, store):
        docs = [
            VectorDocument("good", "ok", [1, 0, 0, 0]),
            VectorDocument("bad", "wrong dims", [1, 0]),  # 维度错误
        ]
        count = store.upsert_batch(docs)
        assert count == 1  # 只有 good 成功

    def test_context_manager(self):
        with VectorStore(db_path=None, dimensions=4) as store:
            store.upsert(VectorDocument("x", "t", [1, 0, 0, 0]))
            assert store.count() == 1


# ---------------------------------------------------------------------------
# VectorStore Search Tests
# ---------------------------------------------------------------------------

class TestVectorStoreSearch:
    @pytest.fixture
    def store_with_data(self):
        store = VectorStore(db_path=None, dimensions=4)
        # 4 个正交方向的文档
        store.upsert(VectorDocument("d1", "python programming", [1, 0, 0, 0], source_type="doc"))
        store.upsert(VectorDocument("d2", "java development", [0, 1, 0, 0], source_type="doc"))
        store.upsert(VectorDocument("i1", "debug tips", [0, 0, 1, 0], source_type="insight"))
        store.upsert(VectorDocument("i2", "test patterns", [0, 0, 0, 1], source_type="insight"))
        return store

    def test_exact_match(self, store_with_data):
        results = store_with_data.search([1, 0, 0, 0], top_k=1)
        assert len(results) == 1
        assert results[0].doc_id == "d1"
        assert abs(results[0].score - 1.0) < 1e-6

    def test_top_k_limit(self, store_with_data):
        results = store_with_data.search([1, 1, 1, 1], top_k=2)
        assert len(results) == 2

    def test_source_type_filter(self, store_with_data):
        results = store_with_data.search([1, 1, 1, 1], top_k=10, source_type="insight")
        assert all(r.source_type == "insight" for r in results)
        assert len(results) == 2

    def test_min_score_filter(self, store_with_data):
        # 查询 [1,0,0,0]，只有 d1 分数为 1.0，其余为 0
        results = store_with_data.search([1, 0, 0, 0], min_score=0.5)
        assert len(results) == 1
        assert results[0].doc_id == "d1"

    def test_results_sorted_by_score(self, store_with_data):
        # 查询偏向 d1 和 i1
        results = store_with_data.search([0.9, 0.0, 0.5, 0.0], top_k=4)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_empty_store(self):
        store = VectorStore(db_path=None, dimensions=4)
        results = store.search([1, 0, 0, 0])
        assert results == []

    def test_search_dimension_mismatch_raises(self, store_with_data):
        with pytest.raises(ValueError, match="维度不匹配"):
            store_with_data.search([1, 0])  # 2 dims, 期望 4

    def test_search_result_has_metadata(self):
        store = VectorStore(db_path=None, dimensions=2)
        store.upsert(VectorDocument(
            "m1", "text", [1, 0],
            metadata={"key": "value"},
        ))
        results = store.search([1, 0], top_k=1)
        assert results[0].metadata == {"key": "value"}


# ---------------------------------------------------------------------------
# VectorStore Persistence Tests
# ---------------------------------------------------------------------------

class TestVectorStorePersistence:
    def test_persist_and_reload(self, tmp_path):
        db_file = tmp_path / "vectors" / "index.db"
        # 写入
        with VectorStore(db_path=db_file, dimensions=4) as store:
            store.upsert(VectorDocument("p1", "persistent", [1, 0, 0, 0]))
            assert store.count() == 1

        # 重新加载
        with VectorStore(db_path=db_file, dimensions=4) as store2:
            assert store2.count() == 1
            doc = store2.get("p1")
            assert doc is not None
            assert doc.text == "persistent"

    def test_creates_parent_directories(self, tmp_path):
        db_file = tmp_path / "deep" / "nested" / "dir" / "index.db"
        store = VectorStore(db_path=db_file, dimensions=4)
        assert db_file.parent.exists()
        store.close()

    def test_db_path_property(self, tmp_path):
        db_file = tmp_path / "test.db"
        store = VectorStore(db_path=db_file, dimensions=4)
        assert store.db_path == db_file
        store.close()

    def test_memory_db_path_is_none(self):
        store = VectorStore(db_path=None, dimensions=4)
        assert store.db_path is None
        store.close()
