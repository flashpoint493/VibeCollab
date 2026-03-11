"""
VectorStore - Local persistent vector storage

Uses SQLite by default to store vectors and metadata, with pure Python cosine similarity.
Zero external dependency solution.

Storage path: .vibecollab/vectors/index.db
"""

from __future__ import annotations

import json
import logging
import math
import sqlite3
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Vector document -- stores an indexed text and its vector"""

    doc_id: str  # Unique ID, e.g. "insight:INS-001" or "doc:CONTEXT.md"
    text: str
    vector: List[float]
    source: str = ""  # Source file path
    source_type: str = ""  # "insight" | "document" | "code"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Search result"""

    doc_id: str
    text: str
    score: float  # Cosine similarity, 0~1
    source: str = ""
    source_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Pure Python cosine similarity"""
    if len(a) != len(b):
        raise ValueError(f"Vector dimension mismatch: {len(a)} vs {len(b)}")

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def _pack_vector(vector: List[float]) -> bytes:
    """Pack float list to bytes (for SQLite blob storage)"""
    return struct.pack(f"{len(vector)}f", *vector)


def _unpack_vector(data: bytes) -> List[float]:
    """Unpack bytes to float list"""
    count = len(data) // 4  # float32 = 4 bytes
    return list(struct.unpack(f"{count}f", data))


class VectorStore:
    """SQLite vector store

    Table schema:
        vectors(
            doc_id TEXT PRIMARY KEY,
            text TEXT,
            vector BLOB,
            source TEXT,
            source_type TEXT,
            metadata TEXT,  -- JSON
            dimensions INTEGER
        )
    """

    def __init__(self, db_path: Optional[Path] = None, dimensions: int = 256):
        self._dimensions = dimensions

        if db_path is None:
            # In-memory mode (for testing)
            self._db_path = None
            self._conn = sqlite3.connect(":memory:")
        else:
            self._db_path = Path(db_path)
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._db_path))

        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self._conn.execute("""
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
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_type ON vectors(source_type)
        """)
        self._conn.commit()

    def upsert(self, doc: VectorDocument) -> None:
        """Insert or update a vector document"""
        if len(doc.vector) != self._dimensions:
            raise ValueError(
                f"Vector dimension mismatch: expected {self._dimensions}, got {len(doc.vector)}"
            )

        self._conn.execute(
            """
            INSERT INTO vectors (doc_id, text, vector, source, source_type, metadata, dimensions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
                text = excluded.text,
                vector = excluded.vector,
                source = excluded.source,
                source_type = excluded.source_type,
                metadata = excluded.metadata,
                dimensions = excluded.dimensions
            """,
            (
                doc.doc_id,
                doc.text,
                _pack_vector(doc.vector),
                doc.source,
                doc.source_type,
                json.dumps(doc.metadata, ensure_ascii=False),
                self._dimensions,
            ),
        )
        self._conn.commit()

    def upsert_batch(self, docs: Sequence[VectorDocument]) -> int:
        """Batch insert/update, return affected row count"""
        count = 0
        for doc in docs:
            if len(doc.vector) != self._dimensions:
                logger.warning(
                    "Skipping %s: dimension mismatch (%d vs %d)",
                    doc.doc_id,
                    len(doc.vector),
                    self._dimensions,
                )
                continue
            self._conn.execute(
                """
                INSERT INTO vectors (doc_id, text, vector, source, source_type, metadata, dimensions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    text = excluded.text,
                    vector = excluded.vector,
                    source = excluded.source,
                    source_type = excluded.source_type,
                    metadata = excluded.metadata,
                    dimensions = excluded.dimensions
                """,
                (
                    doc.doc_id,
                    doc.text,
                    _pack_vector(doc.vector),
                    doc.source,
                    doc.source_type,
                    json.dumps(doc.metadata, ensure_ascii=False),
                    self._dimensions,
                ),
            )
            count += 1
        self._conn.commit()
        return count

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        source_type: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        """Vector similarity search

        Args:
            query_vector: Query vector
            top_k: Maximum number of results
            source_type: Filter by source type
            min_score: Minimum similarity threshold
        """
        if len(query_vector) != self._dimensions:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self._dimensions}, got {len(query_vector)}"
            )

        if source_type:
            rows = self._conn.execute(
                "SELECT doc_id, text, vector, source, source_type, metadata "
                "FROM vectors WHERE source_type = ?",
                (source_type,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT doc_id, text, vector, source, source_type, metadata FROM vectors"
            ).fetchall()

        results = []
        for row in rows:
            doc_id, text, vec_blob, source, stype, meta_json = row
            stored_vector = _unpack_vector(vec_blob)
            score = cosine_similarity(query_vector, stored_vector)
            if score >= min_score:
                results.append(
                    SearchResult(
                        doc_id=doc_id,
                        text=text,
                        score=score,
                        source=source,
                        source_type=stype,
                        metadata=json.loads(meta_json) if meta_json else {},
                    )
                )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def get(self, doc_id: str) -> Optional[VectorDocument]:
        """Get a single document by doc_id"""
        row = self._conn.execute(
            "SELECT doc_id, text, vector, source, source_type, metadata "
            "FROM vectors WHERE doc_id = ?",
            (doc_id,),
        ).fetchone()

        if not row:
            return None

        doc_id, text, vec_blob, source, stype, meta_json = row
        return VectorDocument(
            doc_id=doc_id,
            text=text,
            vector=_unpack_vector(vec_blob),
            source=source,
            source_type=stype,
            metadata=json.loads(meta_json) if meta_json else {},
        )

    def delete(self, doc_id: str) -> bool:
        """Delete a single document"""
        cursor = self._conn.execute("DELETE FROM vectors WHERE doc_id = ?", (doc_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def delete_by_source_type(self, source_type: str) -> int:
        """Batch delete by source type"""
        cursor = self._conn.execute(
            "DELETE FROM vectors WHERE source_type = ?", (source_type,)
        )
        self._conn.commit()
        return cursor.rowcount

    def count(self, source_type: Optional[str] = None) -> int:
        """Count documents"""
        if source_type:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM vectors WHERE source_type = ?", (source_type,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) FROM vectors").fetchone()
        return row[0] if row else 0

    def list_doc_ids(self, source_type: Optional[str] = None) -> List[str]:
        """List all doc_ids"""
        if source_type:
            rows = self._conn.execute(
                "SELECT doc_id FROM vectors WHERE source_type = ? ORDER BY doc_id",
                (source_type,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT doc_id FROM vectors ORDER BY doc_id"
            ).fetchall()
        return [r[0] for r in rows]

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def db_path(self) -> Optional[Path]:
        return self._db_path

    def close(self):
        """Close database connection"""
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
