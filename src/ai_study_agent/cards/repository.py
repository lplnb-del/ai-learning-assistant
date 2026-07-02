"""SQLite repository for QA libraries and review cards."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from uuid import uuid4

from ai_study_agent.core.domain import MasteryLevel, QACard, QALibrary
from ai_study_agent.knowledge.repository import utc_now_iso


class CardRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create_library(self, *, name: str, description: str = "") -> QALibrary:
        now = utc_now_iso()
        library = QALibrary(
            id=str(uuid4()),
            name=name,
            description=description,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO qa_libraries (id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (library.id, library.name, library.description, now, now),
            )
        return library

    def list_libraries(self) -> list[QALibrary]:
        rows = self._connection.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM qa_libraries
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [_library_from_row(row) for row in rows]

    def get_library(self, library_id: str) -> QALibrary | None:
        row = self._connection.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM qa_libraries
            WHERE id = ?
            """,
            (library_id,),
        ).fetchone()
        return _library_from_row(row) if row else None

    def delete_library(self, library_id: str) -> bool:
        with self._connection:
            cursor = self._connection.execute("DELETE FROM qa_libraries WHERE id = ?", (library_id,))
        return cursor.rowcount > 0

    def create_card(
        self,
        *,
        qa_library_id: str | None = None,
        knowledge_base_id: str | None = None,
        question: str,
        answer: str,
        source_chunk_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> QACard:
        now = utc_now_iso()
        card = QACard(
            id=str(uuid4()),
            qa_library_id=qa_library_id,
            knowledge_base_id=knowledge_base_id,
            question=question,
            answer=answer,
            source_chunk_ids=source_chunk_ids or [],
            tags=tags or [],
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO qa_cards (
                    id, qa_library_id, knowledge_base_id, question, answer, source_chunk_ids_json,
                    tags_json, mastery, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.id,
                    card.qa_library_id,
                    card.knowledge_base_id,
                    card.question,
                    card.answer,
                    json.dumps(card.source_chunk_ids, ensure_ascii=False),
                    json.dumps(card.tags, ensure_ascii=False),
                    card.mastery.value,
                    now,
                    now,
                ),
            )
            if card.qa_library_id:
                self._touch_library(card.qa_library_id, now)
        return card

    def list_cards(
        self,
        *,
        qa_library_id: str | None = None,
        knowledge_base_id: str | None = None,
        mastery: MasteryLevel | None = None,
        tag: str | None = None,
    ) -> list[QACard]:
        clauses: list[str] = []
        params: list[str] = []
        if qa_library_id:
            clauses.append("qa_library_id = ?")
            params.append(qa_library_id)
        if knowledge_base_id:
            clauses.append("knowledge_base_id = ?")
            params.append(knowledge_base_id)
        if mastery:
            clauses.append("mastery = ?")
            params.append(mastery.value)

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._connection.execute(
            f"""
            SELECT id, qa_library_id, knowledge_base_id, question, answer, source_chunk_ids_json,
                   tags_json, mastery, created_at, updated_at
            FROM qa_cards
            {where_clause}
            ORDER BY updated_at DESC
            """,
            params,
        ).fetchall()
        cards = [_card_from_row(row) for row in rows]
        if tag:
            return [card for card in cards if tag in card.tags]
        return cards

    def get_card(self, card_id: str) -> QACard | None:
        row = self._connection.execute(
            """
            SELECT id, qa_library_id, knowledge_base_id, question, answer, source_chunk_ids_json,
                   tags_json, mastery, created_at, updated_at
            FROM qa_cards
            WHERE id = ?
            """,
            (card_id,),
        ).fetchone()
        return _card_from_row(row) if row else None

    def update_mastery(self, card_id: str, mastery: MasteryLevel) -> QACard | None:
        now = utc_now_iso()
        existing = self.get_card(card_id)
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE qa_cards
                SET mastery = ?, updated_at = ?
                WHERE id = ?
                """,
                (mastery.value, now, card_id),
            )
            if cursor.rowcount > 0 and existing and existing.qa_library_id:
                self._touch_library(existing.qa_library_id, now)
        if cursor.rowcount == 0:
            return None
        return self.get_card(card_id)

    def delete_card(self, card_id: str) -> bool:
        existing = self.get_card(card_id)
        now = utc_now_iso()
        with self._connection:
            cursor = self._connection.execute("DELETE FROM qa_cards WHERE id = ?", (card_id,))
            if cursor.rowcount > 0 and existing and existing.qa_library_id:
                self._touch_library(existing.qa_library_id, now)
        return cursor.rowcount > 0

    def _touch_library(self, library_id: str, updated_at: str) -> None:
        self._connection.execute(
            "UPDATE qa_libraries SET updated_at = ? WHERE id = ?",
            (updated_at, library_id),
        )


def _card_from_row(row: sqlite3.Row) -> QACard:
    return QACard(
        id=row["id"],
        qa_library_id=row["qa_library_id"],
        knowledge_base_id=row["knowledge_base_id"],
        question=row["question"],
        answer=row["answer"],
        source_chunk_ids=json.loads(row["source_chunk_ids_json"]),
        tags=json.loads(row["tags_json"]),
        mastery=MasteryLevel(row["mastery"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _library_from_row(row: sqlite3.Row) -> QALibrary:
    return QALibrary(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
