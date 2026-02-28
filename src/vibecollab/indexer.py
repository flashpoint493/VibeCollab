"""
Indexer — 项目文档与 Insight 索引器

将文档拆分为段落级 chunk，通过 Embedder 生成向量，
存入 VectorStore，供语义搜索使用。

索引来源:
    - 项目文档: CONTRIBUTING_AI.md, CONTEXT.md, DECISIONS.md, ROADMAP.md, PRD.md
    - Insight YAML: 标题 + body + tags
    - 代码文件 (可选): docstring / 函数签名
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .embedder import Embedder, EmbedderConfig
from .vector_store import VectorDocument, VectorStore

logger = logging.getLogger(__name__)

# 默认索引的文档文件
DEFAULT_DOC_FILES = [
    "CONTRIBUTING_AI.md",
    "docs/CONTEXT.md",
    "docs/DECISIONS.md",
    "docs/ROADMAP.md",
    "docs/PRD.md",
    "docs/CHANGELOG.md",
]


@dataclass
class IndexStats:
    """索引统计"""

    documents_indexed: int = 0
    insights_indexed: int = 0
    chunks_total: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)


def _split_markdown_by_heading(text: str, source: str) -> List[Dict[str, str]]:
    """按 Markdown 标题切分文档为 chunk

    每个 chunk 包含一个标题和其下方内容，直到下一个同级或更高级标题。
    """
    lines = text.splitlines()
    chunks: List[Dict[str, str]] = []
    current_heading = ""
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            # 保存当前 chunk
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

    # 最后一个 chunk
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
    """将 Insight YAML 数据转为可索引文本"""
    parts = []
    title = insight_data.get("title", "")
    if title:
        parts.append(str(title))

    body = insight_data.get("body", "")
    if isinstance(body, dict):
        # 结构化 body (scenario/approach/validation/constraints)
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
        parts.append(f"标签: {', '.join(str(t) for t in tags)}")

    category = insight_data.get("category", "")
    if category:
        parts.append(f"分类: {category}")

    return "\n".join(parts)


class Indexer:
    """项目索引器

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
        """索引所有文档和 Insight"""
        stats = IndexStats()

        # 索引文档
        doc_stats = self.index_documents()
        stats.documents_indexed += doc_stats.documents_indexed
        stats.chunks_total += doc_stats.chunks_total
        stats.skipped += doc_stats.skipped
        stats.errors.extend(doc_stats.errors)

        # 索引 Insight
        ins_stats = self.index_insights()
        stats.insights_indexed += ins_stats.insights_indexed
        stats.chunks_total += ins_stats.chunks_total
        stats.errors.extend(ins_stats.errors)

        return stats

    def index_documents(self) -> IndexStats:
        """索引项目文档文件"""
        stats = IndexStats()

        for doc_file in self._doc_files:
            full_path = self._project_root / doc_file
            if not full_path.exists():
                stats.skipped += 1
                continue

            try:
                text = full_path.read_text(encoding="utf-8")
                if not text.strip():
                    stats.skipped += 1
                    continue

                chunks = _split_markdown_by_heading(text, doc_file)
                if not chunks:
                    stats.skipped += 1
                    continue

                # 批量 embed
                texts = [c["content"] for c in chunks]
                vectors = self._embedder.embed_texts(texts)

                docs = []
                for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    doc_id = f"doc:{doc_file}:{i}"
                    docs.append(VectorDocument(
                        doc_id=doc_id,
                        text=chunk["content"][:2000],  # 截断长文本
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
                logger.warning("索引文档失败: %s — %s", doc_file, e)

        return stats

    def index_insights(self) -> IndexStats:
        """索引 Insight YAML 文件"""
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

        # 批量 embed
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
        """语义搜索"""
        query_vector = self._embedder.embed_text(query)
        return self._store.search(
            query_vector,
            top_k=top_k,
            source_type=source_type,
            min_score=min_score,
        )
