"""SQLite database initialization for local knowledge metadata."""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS knowledge_bases (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS source_documents (
        id TEXT PRIMARY KEY,
        knowledge_base_id TEXT NOT NULL,
        name TEXT NOT NULL,
        source_uri TEXT NOT NULL,
        content_type TEXT NOT NULL,
        status TEXT NOT NULL,
        error_message TEXT,
        content_hash TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS document_chunks (
        id TEXT PRIMARY KEY,
        knowledge_base_id TEXT NOT NULL,
        source_document_id TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        title TEXT,
        text TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
        FOREIGN KEY (source_document_id) REFERENCES source_documents(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS qa_libraries (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS qa_cards (
        id TEXT PRIMARY KEY,
        qa_library_id TEXT,
        knowledge_base_id TEXT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        source_chunk_ids_json TEXT NOT NULL DEFAULT '[]',
        tags_json TEXT NOT NULL DEFAULT '[]',
        mastery TEXT NOT NULL DEFAULT 'new',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (qa_library_id) REFERENCES qa_libraries(id) ON DELETE SET NULL,
        FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE SET NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_qa_libraries_updated_at ON qa_libraries(updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_source_documents_kb ON source_documents(knowledge_base_id)",
    "CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(source_document_id, chunk_index)",
    "CREATE INDEX IF NOT EXISTS idx_document_chunks_kb ON document_chunks(knowledge_base_id)",
    "CREATE INDEX IF NOT EXISTS idx_qa_cards_library ON qa_cards(qa_library_id)",
    "CREATE INDEX IF NOT EXISTS idx_qa_cards_kb ON qa_cards(knowledge_base_id)",
    "CREATE INDEX IF NOT EXISTS idx_qa_cards_mastery ON qa_cards(mastery)",
)


def connect(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    with connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _run_schema_migrations(connection)


def _run_schema_migrations(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info('qa_cards')").fetchall()
    }
    if columns and "qa_library_id" not in columns:
        connection.execute("ALTER TABLE qa_cards ADD COLUMN qa_library_id TEXT")
