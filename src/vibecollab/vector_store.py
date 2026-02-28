"""
VectorStore — 本地持久化向量存储

默认使用 SQLite 存储向量和元数据，纯 Python 余弦相似度计算。
零外部依赖方案。

存储路径: .vibecollab/vectors/index.db
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
    """向量文档 — 存储一条已索引的文本及其向量"""

    doc_id: str  # 唯一标识，如 "insight:INS-001" 或 "doc:CONTEXT.md"
    text: str
    vector: List[float]
    source: str = ""  # 来源文件路径
    source_type: str = ""  # "insight" | "document" | "code"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """搜索结果"""

    doc_id: str
    text: str
    score: float  # 余弦相似度，0~1
    source: str = ""
    source_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """纯 Python 余弦相似度"""
    if len(a) != len(b):
        raise ValueError(f"向量维度不匹配: {len(a)} vs {len(b)}")

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def _pack_vector(vector: List[float]) -> bytes:
    """将 float 列表打包为 bytes（用于 SQLite blob 存储）"""
    return struct.pack(f"{len(vector)}f", *vector)


def _unpack_vector(data: bytes) -> List[float]:
    """从 bytes 解包为 float 列表"""
    count = len(data) // 4  # float32 = 4 bytes
    return list(struct.unpack(f"{count}f", data))


class VectorStore:
    """SQLite 向量存储

    表结构:
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
            # 内存模式（测试用）
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
        """插入或更新一条向量文档"""
        if len(doc.vector) != self._dimensions:
            raise ValueError(
                f"向量维度不匹配: 期望 {self._dimensions}, 得到 {len(doc.vector)}"
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
        """批量插入/更新，返回受影响行数"""
        count = 0
        for doc in docs:
            if len(doc.vector) != self._dimensions:
                logger.warning(
                    "跳过 %s: 维度不匹配 (%d vs %d)",
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
        """向量相似度搜索

        Args:
            query_vector: 查询向量
            top_k: 返回结果数量上限
            source_type: 过滤来源类型
            min_score: 最低相似度阈值
        """
        if len(query_vector) != self._dimensions:
            raise ValueError(
                f"查询向量维度不匹配: 期望 {self._dimensions}, 得到 {len(query_vector)}"
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
        """根据 doc_id 获取单条文档"""
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
        """删除单条文档"""
        cursor = self._conn.execute("DELETE FROM vectors WHERE doc_id = ?", (doc_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def delete_by_source_type(self, source_type: str) -> int:
        """按来源类型批量删除"""
        cursor = self._conn.execute(
            "DELETE FROM vectors WHERE source_type = ?", (source_type,)
        )
        self._conn.commit()
        return cursor.rowcount

    def count(self, source_type: Optional[str] = None) -> int:
        """统计文档数量"""
        if source_type:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM vectors WHERE source_type = ?", (source_type,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) FROM vectors").fetchone()
        return row[0] if row else 0

    def list_doc_ids(self, source_type: Optional[str] = None) -> List[str]:
        """列出所有 doc_id"""
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
        """关闭数据库连接"""
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
