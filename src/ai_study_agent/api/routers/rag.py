"""RAG API routes."""

from __future__ import annotations

from fastapi import APIRouter
from starlette import status

from ai_study_agent.api.errors import ApiError
from ai_study_agent.api.schemas.common import RouterStatusResponse
from ai_study_agent.api.schemas.rag import RagQuestionRequest, RagQuestionResponse, RagSourceResponse
from ai_study_agent.core.config import AppConfig
from ai_study_agent.rag.service import RagAnswer, RagService, RagServiceError, RagSourceItem

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/status", response_model=RouterStatusResponse)
def rag_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="rag",
        message="RAG router ready. Local chunk retrieval and prompt assembly are available.",
    )


@router.post("/ask", response_model=RagQuestionResponse)
def ask_rag_question(request: RagQuestionRequest) -> RagQuestionResponse:
    service = build_service()
    try:
        answer = service.answer_question(
            knowledge_base_id=request.knowledge_base_id,
            qa_library_ids=request.qa_library_ids,
            question=request.question,
            top_k=request.top_k,
        )
    except RagServiceError as exc:
        raise ApiError("rag_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return _question_response(answer)


def build_service() -> RagService:
    return RagService.from_config(AppConfig.from_env())


def _question_response(answer: RagAnswer) -> RagQuestionResponse:
    return RagQuestionResponse(
        answer=answer.answer,
        sources=[_source_response(source) for source in answer.sources],
        prompt_preview=answer.prompt_preview,
        retrieval_mode=answer.retrieval_mode,
    )


def _source_response(source: RagSourceItem) -> RagSourceResponse:
    return RagSourceResponse(
        chunk_id=source.source_id,
        source_type=source.source_type,
        document_id=source.document_id,
        document_name=source.document_name,
        chunk_index=source.chunk_index,
        title=source.title,
        excerpt=source.excerpt,
        score=source.score,
    )
