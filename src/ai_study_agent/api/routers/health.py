"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ai_study_agent.api.schemas.common import HealthResponse
from ai_study_agent.core.config import AppConfig

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    config = AppConfig.from_env()
    return HealthResponse(
        status="ok",
        service="ai-study-agent",
        llm_configured=config.has_llm_key,
        model=config.deepseek_model,
    )
