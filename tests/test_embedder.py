"""
Tests for Embedder — Lightweight embedding abstraction layer
"""

import hashlib

import pytest

from vibecollab.insight.embedder import (
    Embedder,
    EmbedderConfig,
    PurePythonEmbedder,
)


# ---------------------------------------------------------------------------
# PurePythonEmbedder Tests
# ---------------------------------------------------------------------------

class TestPurePythonEmbedder:
    def test_dimensions(self):
        e = PurePythonEmbedder(dimensions=128)
        assert e.dimensions == 128
        assert e.model_name == "pure-python-trigram"

    def test_default_dimensions(self):
        e = PurePythonEmbedder()
        assert e.dimensions == 256

    def test_embed_text_returns_correct_length(self):
        e = PurePythonEmbedder(dimensions=64)
        vec = e.embed_text("hello world")
        assert len(vec) == 64
        assert all(isinstance(v, float) for v in vec)

    def test_embed_text_normalized(self):
        """Vectors should be L2 normalized"""
        e = PurePythonEmbedder(dimensions=128)
        vec = e.embed_text("test normalization")
        norm = sum(v * v for v in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_embed_empty_text(self):
        e = PurePythonEmbedder(dimensions=64)
        vec = e.embed_text("")
        assert len(vec) == 64
        assert all(v == 0.0 for v in vec)

    def test_embed_texts_batch(self):
        e = PurePythonEmbedder(dimensions=64)
        vecs = e.embed_texts(["hello", "world", "test"])
        assert len(vecs) == 3
        assert all(len(v) == 64 for v in vecs)

    def test_similar_texts_have_higher_similarity(self):
        """Similar texts should have higher cosine similarity"""
        e = PurePythonEmbedder(dimensions=256)
        v1 = e.embed_text("python programming language")
        v2 = e.embed_text("python programming tutorial")
        v3 = e.embed_text("whales swimming in the ocean")

        # Cosine similarity
        def cosine(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(x * x for x in b) ** 0.5
            return dot / (na * nb) if na > 0 and nb > 0 else 0

        sim_similar = cosine(v1, v2)
        sim_different = cosine(v1, v3)
        # Similar texts should have higher cosine
        assert sim_similar > sim_different

    def test_deterministic(self):
        """Same text should produce same vector"""
        e = PurePythonEmbedder(dimensions=128)
        v1 = e.embed_text("deterministic test")
        v2 = e.embed_text("deterministic test")
        assert v1 == v2

    def test_case_insensitive(self):
        """Case insensitive"""
        e = PurePythonEmbedder(dimensions=128)
        v1 = e.embed_text("Hello World")
        v2 = e.embed_text("hello world")
        assert v1 == v2

    def test_short_text(self):
        """Short text (<3 chars) should not crash"""
        e = PurePythonEmbedder(dimensions=64)
        v1 = e.embed_text("ab")
        v2 = e.embed_text("a")
        assert len(v1) == 64
        assert len(v2) == 64


# ---------------------------------------------------------------------------
# Embedder (unified entry) Tests
# ---------------------------------------------------------------------------

class TestEmbedder:
    def test_auto_backend_fallback_to_pure_python(self):
        """auto mode should fall back to pure_python when no external deps"""
        config = EmbedderConfig(backend="auto")
        embedder = Embedder(config)
        # In test env may not have sentence-transformers, should at least fall back to pure_python
        assert embedder.dimensions > 0
        assert embedder.model_name is not None

    def test_pure_python_explicit(self):
        config = EmbedderConfig(backend="pure_python", dimensions=128)
        embedder = Embedder(config)
        assert embedder.dimensions == 128
        assert embedder.model_name == "pure-python-trigram"

    def test_embed_text(self):
        config = EmbedderConfig(backend="pure_python", dimensions=64)
        embedder = Embedder(config)
        vec = embedder.embed_text("test text")
        assert len(vec) == 64

    def test_embed_texts(self):
        config = EmbedderConfig(backend="pure_python", dimensions=64)
        embedder = Embedder(config)
        vecs = embedder.embed_texts(["a", "b", "c"])
        assert len(vecs) == 3

    def test_caching(self):
        config = EmbedderConfig(backend="pure_python", dimensions=64)
        embedder = Embedder(config)
        v1 = embedder.embed_text("cached text")
        v2 = embedder.embed_text("cached text")
        assert v1 == v2
        # Should return from cache
        assert len(embedder._cache) == 1

    def test_batch_caching(self):
        """Batch embed should utilize cache"""
        config = EmbedderConfig(backend="pure_python", dimensions=64)
        embedder = Embedder(config)
        # Warm up cache
        embedder.embed_text("first")
        # Batch request contains cached and new entries
        vecs = embedder.embed_texts(["first", "second"])
        assert len(vecs) == 2
        assert len(embedder._cache) == 2

    def test_clear_cache(self):
        config = EmbedderConfig(backend="pure_python", dimensions=64)
        embedder = Embedder(config)
        embedder.embed_text("test")
        assert len(embedder._cache) == 1
        embedder.clear_cache()
        assert len(embedder._cache) == 0

    def test_unknown_backend_raises(self):
        config = EmbedderConfig(backend="nonexistent")
        with pytest.raises(ValueError, match="Unknown embedding backend"):
            Embedder(config)

    def test_openai_without_api_key_raises(self):
        config = EmbedderConfig(backend="openai", api_key="")
        with pytest.raises(ValueError, match="api_key"):
            Embedder(config)

    def test_default_config(self):
        """Default config should not crash"""
        embedder = Embedder()
        vec = embedder.embed_text("default config test")
        assert len(vec) > 0
