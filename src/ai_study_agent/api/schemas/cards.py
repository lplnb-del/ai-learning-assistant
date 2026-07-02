"""QA library and card API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ai_study_agent.core.domain import MasteryLevel


class QALibraryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)


class QALibraryResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class QACardCreateRequest(BaseModel):
    qa_library_id: str | None = Field(default=None, max_length=120)
    knowledge_base_id: str | None = Field(default=None, max_length=120)
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=6000)
    source_chunk_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list, max_length=12)


class QACardMasteryUpdateRequest(BaseModel):
    mastery: MasteryLevel


class QACardResponse(BaseModel):
    id: str
    qa_library_id: str | None
    knowledge_base_id: str | None
    question: str
    answer: str
    source_chunk_ids: list[str]
    tags: list[str]
    mastery: MasteryLevel
    created_at: datetime
    updated_at: datetime

class CardGenerateFromChunksRequest(BaseModel):
    qa_library_id: str = Field(min_length=1, max_length=120)
    chunk_ids: list[str] = Field(min_length=1, max_length=50)
    knowledge_base_id: str | None = Field(default=None, max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=12)


class CardGenerateFromDocumentRequest(BaseModel):
    qa_library_id: str = Field(min_length=1, max_length=120)
    document_id: str = Field(min_length=1, max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=12)


class CardGenerateResponse(BaseModel):
    generated_count: int
    cards: list[QACardResponse]

class CardSourceTraceResponse(BaseModel):
    chunk_id: str
    knowledge_base_id: str
    source_document_id: str
    chunk_index: int
    title: str | None
    text: str
