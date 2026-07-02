"""RAG API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RagQuestionRequest(BaseModel):
    knowledge_base_id: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=8)


class RagSourceResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    title: str | None
    excerpt: str
    score: float


class RagQuestionResponse(BaseModel):
    answer: str
    sources: list[RagSourceResponse]
    prompt_preview: str
    retrieval_mode: str
