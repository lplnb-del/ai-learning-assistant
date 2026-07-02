"""Local persistent vector index used as the Chroma adapter boundary."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ai_study_agent.core.domain import Chunk, RetrievedChunk
from ai_study_agent.rag.embedding import cosine_similarity


@dataclass(frozen=True)
class VectorIndexEntry:
    chunk_id: str
    knowledge_base_id: str
    source_document_id: str
    document_name: str
    chunk_index: int
    title: str | None
    text: str
    embedding: list[float]


class LocalVectorIndex:
    """JSON-backed vector index; replace this adapter with Chroma later."""

    def __init__(self, index_dir: str | Path) -> None:
        self._index_dir = Path(index_dir)

    def rebuild(self, knowledge_base_id: str, entries: list[VectorIndexEntry]) -> None:
        self._index_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "knowledge_base_id": knowledge_base_id,
            "entries": [_entry_to_dict(entry) for entry in entries],
        }
        path = self._index_path(knowledge_base_id)
        temp_path = path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(path)

    def search(self, knowledge_base_id: str, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        entries = self.load_entries(knowledge_base_id)
        scored = [
            RetrievedChunk(
                chunk=Chunk(
                    id=entry.chunk_id,
                    knowledge_base_id=entry.knowledge_base_id,
                    source_document_id=entry.source_document_id,
                    text=entry.text,
                    index=entry.chunk_index,
                    title=entry.title,
                ),
                document_name=entry.document_name,
                score=round(cosine_similarity(query_embedding, entry.embedding), 4),
            )
            for entry in entries
        ]
        return [item for item in sorted(scored, key=lambda item: item.score, reverse=True)[:top_k] if item.score > 0]

    def load_entries(self, knowledge_base_id: str) -> list[VectorIndexEntry]:
        path = self._index_path(knowledge_base_id)
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [_entry_from_dict(item) for item in payload.get("entries", [])]

    def count_entries(self, knowledge_base_id: str) -> int:
        return len(self.load_entries(knowledge_base_id))

    def _index_path(self, knowledge_base_id: str) -> Path:
        safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", knowledge_base_id)
        return self._index_dir / f"{safe_id}.json"


def _entry_to_dict(entry: VectorIndexEntry) -> dict[str, object]:
    return {
        "chunk_id": entry.chunk_id,
        "knowledge_base_id": entry.knowledge_base_id,
        "source_document_id": entry.source_document_id,
        "document_name": entry.document_name,
        "chunk_index": entry.chunk_index,
        "title": entry.title,
        "text": entry.text,
        "embedding": entry.embedding,
    }


def _entry_from_dict(payload: dict[str, object]) -> VectorIndexEntry:
    return VectorIndexEntry(
        chunk_id=str(payload["chunk_id"]),
        knowledge_base_id=str(payload["knowledge_base_id"]),
        source_document_id=str(payload["source_document_id"]),
        document_name=str(payload["document_name"]),
        chunk_index=int(payload["chunk_index"]),
        title=str(payload["title"]) if payload.get("title") is not None else None,
        text=str(payload["text"]),
        embedding=[float(item) for item in payload.get("embedding", [])],
    )
