"""
Indexer - Project document and Insight indexer

Splits documents into paragraph-level chunks, generates vectors via Embedder,
and stores them in VectorStore for semantic search.

Index sources:
    - Project docs: CONTRIBUTING_AI.md, CONTEXT.md, DECISIONS.md, ROADMAP.md, PRD.md
    - Insight YAML: title + body + tags
    - Code files (optional): docstring / function signatures
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from ..insight.embedder import Embedder, EmbedderConfig
from .vector_store import VectorDocument, VectorStore

logger = logging.getLogger(__name__)

# Default document files to index (YAML-first, Markdown fallback)
DEFAULT_DOC_FILES = [
    "CONTRIBUTING_AI.md",
    "docs/context.yaml",
    "docs/CONTEXT.md",
    "docs/decisions.yaml",
    "docs/DECISIONS.md",
    "docs/roadmap.yaml",
    "docs/ROADMAP.md",
    "docs/prd.yaml",
    "docs/PRD.md",
    "docs/changelog.yaml",
    "docs/CHANGELOG.md",
]


@dataclass
class IndexStats:
    """Index statistics"""

    documents_indexed: int = 0
    insights_indexed: int = 0
    chunks_total: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)


def _split_markdown_by_heading(text: str, source: str) -> List[Dict[str, str]]:
    """Split Markdown document into chunks by heading

    Each chunk contains a heading and its content until the next same-level or higher-level heading.
    """
    lines = text.splitlines()
    chunks: List[Dict[str, str]] = []
    current_heading = ""
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            # Save current chunk
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    chunks.append({
                        "heading": current_heading,
                        "content": content,
                        "source": source,
                    })
            current_heading = stripped
            current_lines = [line]
        else:
            current_lines.append(line)

    # Last chunk
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            chunks.append({
                "heading": current_heading,
                "content": content,
                "source": source,
            })

    return chunks


def _insight_to_text(insight_data: dict) -> str:
    """Convert Insight YAML data to indexable text"""
    parts = []
    title = insight_data.get("title", "")
    if title:
        parts.append(str(title))

    body = insight_data.get("body", "")
    if isinstance(body, dict):
        # Structured body (scenario/approach/validation/constraints)
        for key, val in body.items():
            if isinstance(val, list):
                parts.append(f"{key}: {'; '.join(str(v) for v in val)}")
            elif val:
                parts.append(f"{key}: {val}")
    elif body:
        parts.append(str(body))

    summary = insight_data.get("summary", "")
    if summary:
        parts.append(str(summary))

    tags = insight_data.get("tags", [])
    if tags:
        parts.append(f"Tags: {', '.join(str(t) for t in tags)}")

    category = insight_data.get("category", "")
    if category:
        parts.append(f"Category: {category}")

    return "\n".join(parts)


def _split_yaml_by_keys(text: str, source: str) -> List[Dict[str, str]]:
    """Split YAML document into chunks by top-level keys

    Each chunk contains a key and its serialized value.
    """
    try:
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            return [{"heading": source, "content": text, "source": source}]
    except Exception:
        return [{"heading": source, "content": text, "source": source}]

    chunks: List[Dict[str, str]] = []
    for key, value in data.items():
        if key in ("kind", "version"):
            continue
        if isinstance(value, list):
            content = "\n".join(
                yaml.dump(item, allow_unicode=True, default_flow_style=False).strip()
                if isinstance(item, dict) else str(item)
                for item in value
            )
        elif isinstance(value, dict):
            content = yaml.dump(value, allow_unicode=True, default_flow_style=False).strip()
        else:
            content = str(value) if value else ""

        if content.strip():
            chunks.append({
                "heading": f"{source}:{key}",
                "content": content,
                "source": source,
            })

    return chunks


class Indexer:
    """Project indexer

    Usage:
        indexer = Indexer(project_root)
        stats = indexer.index_all()
    """

    def __init__(
        self,
        project_root: Path,
        embedder: Optional[Embedder] = None,
        store: Optional[VectorStore] = None,
        doc_files: Optional[List[str]] = None,
    ):
        self._project_root = project_root
        self._doc_files = doc_files or list(DEFAULT_DOC_FILES)

        # Embedder
        if embedder:
            self._embedder = embedder
        else:
            self._embedder = Embedder(EmbedderConfig(backend="auto"))

        # VectorStore
        if store:
            self._store = store
        else:
            db_path = project_root / ".vibecollab" / "vectors" / "index.db"
            self._store = VectorStore(db_path=db_path, dimensions=self._embedder.dimensions)

    @property
    def store(self) -> VectorStore:
        return self._store

    @property
    def embedder(self) -> Embedder:
        return self._embedder

    def index_all(self) -> IndexStats:
        """Index all documents and Insights"""
        stats = IndexStats()

        # Index documents
        doc_stats = self.index_documents()
        stats.documents_indexed += doc_stats.documents_indexed
        stats.chunks_total += doc_stats.chunks_total
        stats.skipped += doc_stats.skipped
        stats.errors.extend(doc_stats.errors)

        # Index Insights
        ins_stats = self.index_insights()
        stats.insights_indexed += ins_stats.insights_indexed
        stats.chunks_total += ins_stats.chunks_total
        stats.errors.extend(ins_stats.errors)

        return stats

    def index_documents(self) -> IndexStats:
        """Index project document files (YAML-first, skip MD if YAML exists)"""
        stats = IndexStats()

        # Deduplicate: if both .yaml and .md exist, only index .yaml
        seen_stems: set = set()
        effective_files: List[str] = []
        for doc_file in self._doc_files:
            stem = doc_file.rsplit(".", 1)[0].lower().replace("/", "_")
            full_path = self._project_root / doc_file
            if not full_path.exists():
                stats.skipped += 1
                continue
            if stem in seen_stems:
                stats.skipped += 1
                continue
            seen_stems.add(stem)
            effective_files.append(doc_file)

        for doc_file in effective_files:
            full_path = self._project_root / doc_file

            try:
                text = full_path.read_text(encoding="utf-8")
                if not text.strip():
                    stats.skipped += 1
                    continue

                # Choose splitter based on file extension
                if doc_file.endswith((".yaml", ".yml")):
                    chunks = _split_yaml_by_keys(text, doc_file)
                else:
                    chunks = _split_markdown_by_heading(text, doc_file)
                if not chunks:
                    stats.skipped += 1
                    continue

                # Batch embed
                texts = [c["content"] for c in chunks]
                vectors = self._embedder.embed_texts(texts)

                docs = []
                for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    doc_id = f"doc:{doc_file}:{i}"
                    docs.append(VectorDocument(
                        doc_id=doc_id,
                        text=chunk["content"][:2000],  # Truncate long text
                        vector=vector,
                        source=doc_file,
                        source_type="document",
                        metadata={"heading": chunk["heading"]},
                    ))

                self._store.upsert_batch(docs)
                stats.documents_indexed += 1
                stats.chunks_total += len(docs)

            except Exception as e:
                stats.errors.append(f"{doc_file}: {e}")
                logger.warning("Failed to index document: %s -- %s", doc_file, e)

        return stats

    def index_insights(self) -> IndexStats:
        """Index Insight YAML files"""
        stats = IndexStats()
        insights_dir = self._project_root / ".vibecollab" / "insights"

        if not insights_dir.exists():
            return stats

        insight_files = sorted(insights_dir.glob("INS-*.yaml"))
        if not insight_files:
            return stats

        docs = []
        texts = []
        for ins_file in insight_files:
            try:
                with open(ins_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data:
                    continue

                ins_id = data.get("id", ins_file.stem)
                text = _insight_to_text(data)
                if not text.strip():
                    continue

                texts.append(text)
                docs.append({
                    "ins_id": ins_id,
                    "text": text,
                    "file": str(ins_file.relative_to(self._project_root)),
                    "data": data,
                })

            except Exception as e:
                stats.errors.append(f"{ins_file.name}: {e}")

        if not texts:
            return stats

        # Batch embed
        vectors = self._embedder.embed_texts(texts)

        vec_docs = []
        for doc_info, vector in zip(docs, vectors):
            vec_docs.append(VectorDocument(
                doc_id=f"insight:{doc_info['ins_id']}",
                text=doc_info["text"][:2000],
                vector=vector,
                source=doc_info["file"],
                source_type="insight",
                metadata={
                    "title": doc_info["data"].get("title", ""),
                    "tags": doc_info["data"].get("tags", []),
                    "category": doc_info["data"].get("category", ""),
                },
            ))

        count = self._store.upsert_batch(vec_docs)
        stats.insights_indexed = count
        stats.chunks_total += count

        return stats

    def search(
        self,
        query: str,
        top_k: int = 10,
        source_type: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List:
        """Semantic search"""
        query_vector = self._embedder.embed_text(query)
        return self._store.search(
            query_vector,
            top_k=top_k,
            source_type=source_type,
            min_score=min_score,
        )
