"""QA card API placeholders."""

from __future__ import annotations

from fastapi import APIRouter

from ai_study_agent.api.schemas.common import RouterStatusResponse

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/status", response_model=RouterStatusResponse)
def cards_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="cards",
        message="Cards router ready. Card storage will be wired after RAG answers are available.",
    )
