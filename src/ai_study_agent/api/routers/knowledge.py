"""Knowledge base API routes."""

from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Query
from starlette import status

from ai_study_agent.api.errors import ApiError
from ai_study_agent.api.schemas.knowledge import (
    ChunkResponse,
    KnowledgeIndexBuildResponse,
    KnowledgeBaseCreateRequest,
    KnowledgeBaseResponse,
    PdfDocumentImportRequest,
    SourceDocumentResponse,
    TextDocumentImportRequest,
    TextDocumentImportResponse,
    UrlDocumentImportRequest,
)
from ai_study_agent.api.schemas.common import RouterStatusResponse
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Chunk, KnowledgeBase, KnowledgeIndexBuild, SourceDocument
from ai_study_agent.knowledge.service import KnowledgeService, KnowledgeServiceError

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/status", response_model=RouterStatusResponse)
def knowledge_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="knowledge",
        message="Knowledge router ready. SQLite metadata and text ingestion are available.",
    )


@router.post("/bases", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(request: KnowledgeBaseCreateRequest) -> KnowledgeBaseResponse:
    service = build_service()
    try:
        knowledge_base = service.create_knowledge_base(request.name, request.description)
    except KnowledgeServiceError as exc:
        raise ApiError("knowledge_error", str(exc)) from exc
    return _knowledge_base_response(knowledge_base)


@router.get("/bases", response_model=list[KnowledgeBaseResponse])
def list_knowledge_bases() -> list[KnowledgeBaseResponse]:
    return [_knowledge_base_response(item) for item in build_service().list_knowledge_bases()]


@router.delete("/bases/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(knowledge_base_id: str) -> None:
    service = build_service()
    try:
        service.delete_knowledge_base(knowledge_base_id)
    except KnowledgeServiceError as exc:
        raise ApiError("knowledge_error", str(exc), status_code=status.HTTP_404_NOT_FOUND) from exc


@router.post(
    "/bases/{knowledge_base_id}/documents/import-text",
    response_model=TextDocumentImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_text_document(
    knowledge_base_id: str,
    request: TextDocumentImportRequest,
) -> TextDocumentImportResponse:
    service = build_service()
    try:
        document, chunks = service.import_text_document(
            knowledge_base_id=knowledge_base_id,
            name=request.name,
            content=request.content,
            source_uri=request.source_uri,
            content_type=request.content_type,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
    except KnowledgeServiceError as exc:
        raise ApiError("knowledge_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return TextDocumentImportResponse(
        document=_source_document_response(document),
        chunks=[_chunk_response(chunk) for chunk in chunks],
        chunk_count=len(chunks),
    )


@router.post(
    "/bases/{knowledge_base_id}/documents/import-url",
    response_model=TextDocumentImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_url_document(
    knowledge_base_id: str,
    request: UrlDocumentImportRequest,
) -> TextDocumentImportResponse:
    service = build_service()
    try:
        document, chunks = service.import_url_document(
            knowledge_base_id=knowledge_base_id,
            url=request.url,
            name=request.name,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
    except KnowledgeServiceError as exc:
        raise ApiError("knowledge_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return TextDocumentImportResponse(
        document=_source_document_response(document),
        chunks=[_chunk_response(chunk) for chunk in chunks],
        chunk_count=len(chunks),
    )


@router.post(
    "/bases/{knowledge_base_id}/documents/import-pdf",
    response_model=TextDocumentImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_pdf_document(
    knowledge_base_id: str,
    request: PdfDocumentImportRequest,
) -> TextDocumentImportResponse:
    service = build_service()
    try:
        pdf_content = base64.b64decode(request.content_base64, validate=True)
    except binascii.Error as exc:
        raise ApiError("knowledge_error", "PDF 内容必须是有效的 base64", status_code=status.HTTP_400_BAD_REQUEST) from exc
    try:
        document, chunks = service.import_pdf_document(
            knowledge_base_id=knowledge_base_id,
            name=request.name,
            content=pdf_content,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
    except KnowledgeServiceError as exc:
        raise ApiError("knowledge_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return TextDocumentImportResponse(
        document=_source_document_response(document),
        chunks=[_chunk_response(chunk) for chunk in chunks],
        chunk_count=len(chunks),
    )


@router.get("/bases/{knowledge_base_id}/documents", response_model=list[SourceDocumentResponse])
def list_documents(knowledge_base_id: str) -> list[SourceDocumentResponse]:
    service = build_service()
    try:
        documents = service.list_documents(knowledge_base_id)
    except KnowledgeServiceError as exc:
        raise ApiError("knowledge_error", str(exc), status_code=status.HTTP_404_NOT_FOUND) from exc
    return [_source_document_response(document) for document in documents]


@router.post(
    "/bases/{knowledge_base_id}/index/rebuild",
    response_model=KnowledgeIndexBuildResponse,
)
def rebuild_index(knowledge_base_id: str) -> KnowledgeIndexBuildResponse:
    service = build_service()
    try:
        result = service.rebuild_index(knowledge_base_id)
    except KnowledgeServiceError as exc:
        raise ApiError("knowledge_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return _index_build_response(result)


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkResponse])
def list_chunks(document_id: str, limit: int = Query(default=20, ge=1, le=100)) -> list[ChunkResponse]:
    return [_chunk_response(chunk) for chunk in build_service().list_chunks(document_id, limit=limit)]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str) -> None:
    service = build_service()
    try:
        service.delete_document(document_id)
    except KnowledgeServiceError as exc:
        raise ApiError("knowledge_error", str(exc), status_code=status.HTTP_404_NOT_FOUND) from exc


def build_service() -> KnowledgeService:
    return KnowledgeService.from_config(AppConfig.from_env())


def _knowledge_base_response(knowledge_base: KnowledgeBase) -> KnowledgeBaseResponse:
    return KnowledgeBaseResponse(
        id=knowledge_base.id,
        name=knowledge_base.name,
        description=knowledge_base.description,
        created_at=knowledge_base.created_at,
        updated_at=knowledge_base.updated_at,
    )


def _source_document_response(document: SourceDocument) -> SourceDocumentResponse:
    return SourceDocumentResponse(
        id=document.id,
        knowledge_base_id=document.knowledge_base_id,
        name=document.name,
        source_uri=document.source_uri,
        content_type=document.content_type,
        status=document.status,
        error_message=document.error_message,
        created_at=document.created_at,
    )


def _index_build_response(result: KnowledgeIndexBuild) -> KnowledgeIndexBuildResponse:
    return KnowledgeIndexBuildResponse(
        knowledge_base_id=result.knowledge_base_id,
        document_count=result.document_count,
        chunk_count=result.chunk_count,
        status=result.status,
        message=result.message,
        created_at=result.created_at,
    )


def _chunk_response(chunk: Chunk) -> ChunkResponse:
    return ChunkResponse(
        id=chunk.id,
        knowledge_base_id=chunk.knowledge_base_id,
        source_document_id=chunk.source_document_id,
        index=chunk.index,
        title=chunk.title,
        text=chunk.text,
        metadata=chunk.metadata,
    )
