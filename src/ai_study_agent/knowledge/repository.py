"""SQLite repository for knowledge bases, source documents, and chunks."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from ai_study_agent.core.domain import Chunk, KnowledgeBase, RetrievedChunk, SourceDocument


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class KnowledgeRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create_knowledge_base(self, name: str, description: str = "") -> KnowledgeBase:
        now = utc_now_iso()
        knowledge_base = KnowledgeBase(
            id=str(uuid4()),
            name=name,
            description=description,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO knowledge_bases (id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (knowledge_base.id, knowledge_base.name, knowledge_base.description, now, now),
            )
        return knowledge_base

    def list_knowledge_bases(self) -> list[KnowledgeBase]:
        rows = self._connection.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM knowledge_bases
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [_knowledge_base_from_row(row) for row in rows]

    def get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase | None:
        row = self._connection.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM knowledge_bases
            WHERE id = ?
            """,
            (knowledge_base_id,),
        ).fetchone()
        return _knowledge_base_from_row(row) if row else None

    def delete_knowledge_base(self, knowledge_base_id: str) -> bool:
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM knowledge_bases WHERE id = ?",
                (knowledge_base_id,),
            )
        return cursor.rowcount > 0

    def create_document_with_chunks(
        self,
        *,
        document_id: str,
        knowledge_base_id: str,
        name: str,
        source_uri: str,
        content_type: str,
        text: str,
        chunks: list[Chunk],
    ) -> SourceDocument:
        now = utc_now_iso()
        document = SourceDocument(
            id=document_id,
            knowledge_base_id=knowledge_base_id,
            name=name,
            source_uri=source_uri,
            content_type=content_type,
            status="indexed",
            created_at=datetime.fromisoformat(now),
        )
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO source_documents (
                    id, knowledge_base_id, name, source_uri, content_type, status,
                    error_message, content_hash, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.knowledge_base_id,
                    document.name,
                    document.source_uri,
                    document.content_type,
                    document.status,
                    document.error_message,
                    content_hash,
                    now,
                    now,
                ),
            )
            self._connection.executemany(
                """
                INSERT INTO document_chunks (
                    id, knowledge_base_id, source_document_id, chunk_index,
                    title, text, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.id,
                        knowledge_base_id,
                        document.id,
                        chunk.index,
                        chunk.title,
                        chunk.text,
                        json.dumps(chunk.metadata, ensure_ascii=False),
                        now,
                    )
                    for chunk in chunks
                ],
            )
            self._connection.execute(
                "UPDATE knowledge_bases SET updated_at = ? WHERE id = ?",
                (now, knowledge_base_id),
            )
        return document

    def list_documents(self, knowledge_base_id: str) -> list[SourceDocument]:
        rows = self._connection.execute(
            """
            SELECT id, knowledge_base_id, name, source_uri, content_type, status,
                   error_message, created_at
            FROM source_documents
            WHERE knowledge_base_id = ?
            ORDER BY created_at DESC
            """,
            (knowledge_base_id,),
        ).fetchall()
        return [_source_document_from_row(row) for row in rows]

    def count_chunks(self, knowledge_base_id: str) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM document_chunks
            WHERE knowledge_base_id = ?
            """,
            (knowledge_base_id,),
        ).fetchone()
        return int(row["count"]) if row else 0

    def list_chunks_for_knowledge_base(self, knowledge_base_id: str) -> list[RetrievedChunk]:
        rows = self._connection.execute(
            """
            SELECT chunks.id, chunks.knowledge_base_id, chunks.source_document_id,
                   chunks.chunk_index, chunks.title, chunks.text, chunks.metadata_json,
                   documents.name AS document_name
            FROM document_chunks AS chunks
            JOIN source_documents AS documents ON documents.id = chunks.source_document_id
            WHERE chunks.knowledge_base_id = ?
            ORDER BY documents.created_at DESC, chunks.chunk_index
            """,
            (knowledge_base_id,),
        ).fetchall()
        return [
            RetrievedChunk(
                chunk=_chunk_from_row(row),
                document_name=row["document_name"],
                score=0,
            )
            for row in rows
        ]

    def delete_document(self, document_id: str) -> bool:
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM source_documents WHERE id = ?",
                (document_id,),
            )
        return cursor.rowcount > 0

    def list_chunks(self, document_id: str, limit: int = 20) -> list[Chunk]:
        rows = self._connection.execute(
            """
            SELECT id, knowledge_base_id, source_document_id, chunk_index,
                   title, text, metadata_json
            FROM document_chunks
            WHERE source_document_id = ?
            ORDER BY chunk_index
            LIMIT ?
            """,
            (document_id, limit),
        ).fetchall()
        return [_chunk_from_row(row) for row in rows]


def _knowledge_base_from_row(row: sqlite3.Row) -> KnowledgeBase:
    return KnowledgeBase(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _source_document_from_row(row: sqlite3.Row) -> SourceDocument:
    return SourceDocument(
        id=row["id"],
        knowledge_base_id=row["knowledge_base_id"],
        name=row["name"],
        source_uri=row["source_uri"],
        content_type=row["content_type"],
        status=row["status"],
        error_message=row["error_message"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _chunk_from_row(row: sqlite3.Row) -> Chunk:
    return Chunk(
        id=row["id"],
        knowledge_base_id=row["knowledge_base_id"],
        source_document_id=row["source_document_id"],
        text=row["text"],
        index=row["chunk_index"],
        title=row["title"],
        metadata=json.loads(row["metadata_json"]),
    )
