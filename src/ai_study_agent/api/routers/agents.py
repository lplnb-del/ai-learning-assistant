"""Agent API placeholders."""

from __future__ import annotations

from fastapi import APIRouter

from ai_study_agent.api.schemas.common import RouterStatusResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status", response_model=RouterStatusResponse)
def agents_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="agent",
        message="Agent router ready. Capability orchestration will be wired after the capability layer.",
    )
