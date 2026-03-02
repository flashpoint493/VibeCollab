"""
Tests for Embedder — 轻量 embedding 抽象层
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
        """向量应该是 L2 归一化的"""
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
        """相似文本应该有更高的余弦相似度"""
        e = PurePythonEmbedder(dimensions=256)
        v1 = e.embed_text("python programming language")
        v2 = e.embed_text("python programming tutorial")
        v3 = e.embed_text("鲸鱼在海洋中游泳")

        # 余弦相似度
        def cosine(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(x * x for x in b) ** 0.5
            return dot / (na * nb) if na > 0 and nb > 0 else 0

        sim_similar = cosine(v1, v2)
        sim_different = cosine(v1, v3)
        # 相似文本的余弦应该更高
        assert sim_similar > sim_different

    def test_deterministic(self):
        """同一文本应生成相同向量"""
        e = PurePythonEmbedder(dimensions=128)
        v1 = e.embed_text("deterministic test")
        v2 = e.embed_text("deterministic test")
        assert v1 == v2

    def test_case_insensitive(self):
        """大小写不敏感"""
        e = PurePythonEmbedder(dimensions=128)
        v1 = e.embed_text("Hello World")
        v2 = e.embed_text("hello world")
        assert v1 == v2

    def test_short_text(self):
        """短文本（<3 字符）不崩溃"""
        e = PurePythonEmbedder(dimensions=64)
        v1 = e.embed_text("ab")
        v2 = e.embed_text("a")
        assert len(v1) == 64
        assert len(v2) == 64


# ---------------------------------------------------------------------------
# Embedder (统一入口) Tests
# ---------------------------------------------------------------------------

class TestEmbedder:
    def test_auto_backend_fallback_to_pure_python(self):
        """auto 模式在无外部依赖时应降级到 pure_python"""
        config = EmbedderConfig(backend="auto")
        embedder = Embedder(config)
        # 在测试环境中可能没有 sentence-transformers，应至少降级到 pure_python
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
        # 应该从缓存返回
        assert len(embedder._cache) == 1

    def test_batch_caching(self):
        """批量 embed 应利用缓存"""
        config = EmbedderConfig(backend="pure_python", dimensions=64)
        embedder = Embedder(config)
        # 预热缓存
        embedder.embed_text("first")
        # 批量请求含已缓存和新的
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
        with pytest.raises(ValueError, match="未知的 embedding 后端"):
            Embedder(config)

    def test_openai_without_api_key_raises(self):
        config = EmbedderConfig(backend="openai", api_key="")
        with pytest.raises(ValueError, match="api_key"):
            Embedder(config)

    def test_default_config(self):
        """默认配置不应崩溃"""
        embedder = Embedder()
        vec = embedder.embed_text("default config test")
        assert len(vec) > 0
