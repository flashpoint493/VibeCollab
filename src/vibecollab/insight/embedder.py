"""
Embedder -- Lightweight embedding abstraction layer

Supports two backends:
    - "openai": OpenAI text-embedding-3-small API (requires httpx + API key)
    - "local": sentence-transformers local model (requires pip install vibe-collab[embedding])

Default backend auto-selects by availability: local > openai > fail
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Single embedding result"""

    text: str
    vector: List[float]
    model: str
    dimensions: int


class EmbedderBackend(ABC):
    """Embedding backend abstract base class"""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch compute text embedding vectors"""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Single text embedding"""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Vector dimensions"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model name"""


class OpenAIEmbedder(EmbedderBackend):
    """OpenAI text-embedding API backend"""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
        dimensions: Optional[int] = None,
    ):
        try:
            import httpx  # noqa: F401
        except ImportError:
            raise ImportError(
                "OpenAI embedding requires httpx. Install: pip install vibe-collab[llm]"
            )
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._dimensions = dimensions or 1536

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        import httpx

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict = {"input": texts, "model": self._model}
        if self._dimensions:
            payload["dimensions"] = self._dimensions

        resp = httpx.post(
            f"{self._base_url}/embeddings",
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        # Sort by index to ensure consistent order
        embeddings = sorted(data["data"], key=lambda x: x["index"])
        return [e["embedding"] for e in embeddings]

    def embed_text(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model


class LocalEmbedder(EmbedderBackend):
    """sentence-transformers local model backend"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "Local embedding requires sentence-transformers. "
                "Install: pip install vibe-collab[embedding]"
            )
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._dims = self._model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return [e.tolist() for e in embeddings]

    def embed_text(self, text: str) -> List[float]:
        embedding = self._model.encode(text, show_progress_bar=False)
        return embedding.tolist()

    @property
    def dimensions(self) -> int:
        return self._dims

    @property
    def model_name(self) -> str:
        return self._model_name


class PurePythonEmbedder(EmbedderBackend):
    """Pure Python lightweight embedding (based on character n-gram hashing)

    Zero external dependency solution. Accuracy is far lower than real embedding models,
    but sufficient to provide better text similarity search than pure tag matching.

    Algorithm: character trigram -> hash -> normalize to fixed-dimension vector
    """

    def __init__(self, dimensions: int = 256):
        self._dims = dimensions

    def _text_to_vector(self, text: str) -> List[float]:
        text = text.lower().strip()
        vector = [0.0] * self._dims

        if not text:
            return vector

        # Character trigram hashing
        for i in range(max(1, len(text) - 2)):
            trigram = text[i : i + 3]
            h = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dims
            vector[idx] += 1.0

        # L2 normalization
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]

    def embed_text(self, text: str) -> List[float]:
        return self._text_to_vector(text)

    @property
    def dimensions(self) -> int:
        return self._dims

    @property
    def model_name(self) -> str:
        return "pure-python-trigram"


@dataclass
class EmbedderConfig:
    """Embedder configuration"""

    backend: str = "auto"  # "auto" | "openai" | "local" | "pure_python"
    model: str = ""  # Backend-specific model name
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    dimensions: int = 0  # 0 = backend default
    cache_dir: Optional[str] = None


class Embedder:
    """Embedder unified entry point

    Auto-selects backend by availability:
        1. If sentence-transformers available -> local
        2. If API key + httpx available -> openai
        3. Otherwise -> pure_python (zero-dependency fallback)
    """

    def __init__(self, config: Optional[EmbedderConfig] = None):
        self._config = config or EmbedderConfig()
        self._backend = self._create_backend()
        self._cache: Dict[str, List[float]] = {}

    def _create_backend(self) -> EmbedderBackend:
        backend = self._config.backend

        if backend == "auto":
            return self._auto_select()
        elif backend == "openai":
            return self._create_openai()
        elif backend == "local":
            return self._create_local()
        elif backend == "pure_python":
            dims = self._config.dimensions or 256
            return PurePythonEmbedder(dimensions=dims)
        else:
            raise ValueError(f"Unknown embedding backend: {backend}")

    def _auto_select(self) -> EmbedderBackend:
        # Prefer local model
        try:
            return self._create_local()
        except ImportError:
            pass

        # Try OpenAI
        if self._config.api_key:
            try:
                return self._create_openai()
            except ImportError:
                pass

        # Fallback to pure Python
        logger.info("No embedding dependencies found, using pure_python fallback")
        dims = self._config.dimensions or 256
        return PurePythonEmbedder(dimensions=dims)

    def _create_openai(self) -> OpenAIEmbedder:
        if not self._config.api_key:
            raise ValueError("OpenAI embedding requires api_key")
        return OpenAIEmbedder(
            api_key=self._config.api_key,
            model=self._config.model or "text-embedding-3-small",
            base_url=self._config.base_url,
            dimensions=self._config.dimensions or 1536,
        )

    def _create_local(self) -> LocalEmbedder:
        model = self._config.model or "all-MiniLM-L6-v2"
        return LocalEmbedder(model_name=model)

    @property
    def backend(self) -> EmbedderBackend:
        return self._backend

    @property
    def dimensions(self) -> int:
        return self._backend.dimensions

    @property
    def model_name(self) -> str:
        return self._backend.model_name

    def embed_text(self, text: str) -> List[float]:
        cache_key = hashlib.md5(text.encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]
        vector = self._backend.embed_text(text)
        self._cache[cache_key] = vector
        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        results = []
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cache_key = hashlib.md5(text.encode("utf-8")).hexdigest()
            if cache_key in self._cache:
                results.append(self._cache[cache_key])
            else:
                results.append([])  # Placeholder
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            new_vectors = self._backend.embed_texts(uncached_texts)
            for idx, text, vec in zip(uncached_indices, uncached_texts, new_vectors):
                cache_key = hashlib.md5(text.encode("utf-8")).hexdigest()
                self._cache[cache_key] = vec
                results[idx] = vec

        return results

    def clear_cache(self):
        self._cache.clear()
