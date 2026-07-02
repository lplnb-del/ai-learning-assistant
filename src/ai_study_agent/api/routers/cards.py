"""QA card API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query
from starlette import status

from ai_study_agent.api.errors import ApiError
from ai_study_agent.api.schemas.cards import (
    CardGenerateFromChunksRequest,
    CardGenerateFromDocumentRequest,
    CardGenerateResponse,
    CardSourceTraceResponse,
    QACardCreateRequest,
    QACardMasteryUpdateRequest,
    QACardResponse,
    QALibraryCreateRequest,
    QALibraryResponse,
)
from ai_study_agent.api.schemas.common import RouterStatusResponse
from ai_study_agent.cards.service import CardService, CardServiceError
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Chunk, MasteryLevel, QACard, QALibrary

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/status", response_model=RouterStatusResponse)
def cards_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="cards",
        message="Cards router ready. QA libraries, card storage, and mastery updates are available.",
    )


@router.post("/libraries", response_model=QALibraryResponse, status_code=status.HTTP_201_CREATED)
def create_library(request: QALibraryCreateRequest) -> QALibraryResponse:
    service = build_service()
    try:
        library = service.create_library(request.name, request.description)
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return _library_response(library)


@router.get("/libraries", response_model=list[QALibraryResponse])
def list_libraries() -> list[QALibraryResponse]:
    return [_library_response(library) for library in build_service().list_libraries()]


@router.delete("/libraries/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_library(library_id: str) -> None:
    service = build_service()
    try:
        service.delete_library(library_id)
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_404_NOT_FOUND) from exc


@router.post("", response_model=QACardResponse, status_code=status.HTTP_201_CREATED)
def create_card(request: QACardCreateRequest) -> QACardResponse:
    service = build_service()
    try:
        card = service.create_card(
            qa_library_id=request.qa_library_id,
            question=request.question,
            answer=request.answer,
            knowledge_base_id=request.knowledge_base_id,
            source_chunk_ids=request.source_chunk_ids,
            tags=request.tags,
        )
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return _card_response(card)


@router.get("", response_model=list[QACardResponse])
def list_cards(
    qa_library_id: str | None = Query(default=None),
    knowledge_base_id: str | None = Query(default=None),
    mastery: MasteryLevel | None = Query(default=None),
    tag: str | None = Query(default=None),
) -> list[QACardResponse]:
    try:
        cards = build_service().list_cards(
            qa_library_id=qa_library_id,
            knowledge_base_id=knowledge_base_id,
            mastery=mastery,
            tag=tag,
        )
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return [_card_response(card) for card in cards]


@router.patch("/{card_id}/mastery", response_model=QACardResponse)
def update_card_mastery(card_id: str, request: QACardMasteryUpdateRequest) -> QACardResponse:
    service = build_service()
    try:
        card = service.update_mastery(card_id, request.mastery)
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_404_NOT_FOUND) from exc
    return _card_response(card)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: str) -> None:
    service = build_service()
    try:
        service.delete_card(card_id)
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_404_NOT_FOUND) from exc


@router.post("/generate-from-chunks", response_model=CardGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_cards_from_chunks(request: CardGenerateFromChunksRequest) -> CardGenerateResponse:
    service = build_service()
    try:
        cards = service.generate_cards_from_chunks(
            qa_library_id=request.qa_library_id,
            chunk_ids=request.chunk_ids,
            knowledge_base_id=request.knowledge_base_id,
            tags=request.tags,
        )
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return CardGenerateResponse(
        generated_count=len(cards),
        cards=[_card_response(card) for card in cards],
    )


@router.post("/generate-from-document", response_model=CardGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_cards_from_document(request: CardGenerateFromDocumentRequest) -> CardGenerateResponse:
    service = build_service()
    try:
        cards = service.generate_cards_from_document(
            qa_library_id=request.qa_library_id,
            document_id=request.document_id,
            tags=request.tags,
        )
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return CardGenerateResponse(
        generated_count=len(cards),
        cards=[_card_response(card) for card in cards],
    )


@router.get("/{card_id}/sources", response_model=list[CardSourceTraceResponse])
def trace_card_sources(card_id: str) -> list[CardSourceTraceResponse]:
    service = build_service()
    try:
        card = service.get_card(card_id)
    except CardServiceError as exc:
        raise ApiError("cards_error", str(exc), status_code=status.HTTP_404_NOT_FOUND) from exc
    if not card.source_chunk_ids:
        return []
    chunks = service.get_chunks_by_ids(card.source_chunk_ids)
    return [_chunk_trace_response(chunk) for chunk in chunks]


def build_service() -> CardService:
    return CardService.from_config(AppConfig.from_env())


def _library_response(library: QALibrary) -> QALibraryResponse:
    return QALibraryResponse(
        id=library.id,
        name=library.name,
        description=library.description,
        created_at=library.created_at,
        updated_at=library.updated_at,
    )


def _chunk_trace_response(chunk: Chunk) -> CardSourceTraceResponse:
    return CardSourceTraceResponse(
        chunk_id=chunk.id,
        knowledge_base_id=chunk.knowledge_base_id,
        source_document_id=chunk.source_document_id,
        chunk_index=chunk.index,
        title=chunk.title,
        text=chunk.text,
    )


def _card_response(card: QACard) -> QACardResponse:
    return QACardResponse(
        id=card.id,
        qa_library_id=card.qa_library_id,
        knowledge_base_id=card.knowledge_base_id,
        question=card.question,
        answer=card.answer,
        source_chunk_ids=card.source_chunk_ids,
        tags=card.tags,
        mastery=card.mastery,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )
