"""Chroma vector store adapter for RAG retrieval.

Primary: Chroma via langchain-community (persistent, metadata filtering).
Fallback: Local JSON vector index (no external dependency).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ai_study_agent.core.domain import Chunk, RetrievedChunk
from ai_study_agent.rag.embedding import EmbeddingProvider, HashingEmbeddingProvider, cosine_similarity


class ChromaVectorStore:
    """Chroma-backed vector store using LangChain integration."""

    def __init__(self, persist_dir: str | Path, embedding_provider: EmbeddingProvider) -> None:
        from langchain_community.vectorstores import Chroma

        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_provider = embedding_provider

        class _LangChainEmbeddingAdapter:
            def __init__(self, provider: EmbeddingProvider):
                self._provider = provider
            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return self._provider.embed_batch(texts)
            def embed_query(self, text: str) -> list[float]:
                return self._provider.embed(text)

        self._chroma = Chroma(
            embedding_function=_LangChainEmbeddingAdapter(embedding_provider),
            persist_directory=str(self._persist_dir),
        )

    def add_chunks(self, knowledge_base_id: str, chunks: list[Chunk], document_name: str, embeddings: list[list[float]]) -> None:
        texts = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "knowledge_base_id": knowledge_base_id,
                "chunk_id": chunk.id,
                "source_document_id": chunk.source_document_id,
                "document_name": document_name,
                "chunk_index": str(chunk.index),
                "title": chunk.title or "",
            }
            for chunk in chunks
        ]
        ids = [f"{knowledge_base_id}_{chunk.id}" for chunk in chunks]
        self._chroma.add_texts(texts=texts, metadatas=metadatas, ids=ids, embeddings=embeddings)

    def search(self, knowledge_base_id: str, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        results = self._chroma.similarity_search_by_vector_with_relevance_scores(
            embedding=query_embedding,
            k=top_k,
            filter={"knowledge_base_id": knowledge_base_id},
        )
        retrieved: list[RetrievedChunk] = []
        for doc, score in results:
            meta = doc.metadata
            chunk = Chunk(
                id=meta.get("chunk_id", ""),
                knowledge_base_id=meta.get("knowledge_base_id", ""),
                source_document_id=meta.get("source_document_id", ""),
                text=doc.page_content,
                index=int(meta.get("chunk_index", 0)),
                title=meta.get("title") or None,
            )
            retrieved.append(RetrievedChunk(chunk=chunk, document_name=meta.get("document_name", ""), score=round(score, 4)))
        return retrieved

    def delete_by_knowledge_base(self, knowledge_base_id: str) -> None:
        try:
            self._chroma.delete(where={"knowledge_base_id": knowledge_base_id})
        except Exception:
            pass

    def count_entries(self, knowledge_base_id: str) -> int:
        try:
            results = self._chroma.get(where={"knowledge_base_id": knowledge_base_id})
            return len(results.get("ids", []))
        except Exception:
            return 0


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
    """JSON-backed vector index; used as fallback when Chroma is not available."""

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
