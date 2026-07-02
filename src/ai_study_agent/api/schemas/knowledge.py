"""Knowledge API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class TextDocumentImportRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=2_000_000)
    source_uri: str = Field(default="", max_length=500)
    content_type: str = Field(default="text/plain", max_length=80)
    chunk_size: int = Field(default=800, ge=200, le=3000)
    chunk_overlap: int = Field(default=120, ge=0, le=1000)


class UrlDocumentImportRequest(BaseModel):
    url: str = Field(min_length=8, max_length=1000)
    name: str = Field(default="", max_length=200)
    chunk_size: int = Field(default=800, ge=200, le=3000)
    chunk_overlap: int = Field(default=120, ge=0, le=1000)


class PdfDocumentImportRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    content_base64: str = Field(min_length=1, max_length=15_000_000)
    chunk_size: int = Field(default=800, ge=200, le=3000)
    chunk_overlap: int = Field(default=120, ge=0, le=1000)


class SourceDocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    name: str
    source_uri: str
    content_type: str
    status: str
    error_message: str | None
    created_at: datetime


class ChunkResponse(BaseModel):
    id: str
    knowledge_base_id: str
    source_document_id: str
    index: int
    title: str | None
    text: str
    metadata: dict[str, str]


class TextDocumentImportResponse(BaseModel):
    document: SourceDocumentResponse
    chunks: list[ChunkResponse]
    chunk_count: int


class KnowledgeIndexBuildResponse(BaseModel):
    knowledge_base_id: str
    document_count: int
    chunk_count: int
    status: str
    message: str
    created_at: datetime
