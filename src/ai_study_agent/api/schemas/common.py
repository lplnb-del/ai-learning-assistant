"""Common API schemas shared across routers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(description="Stable application-level error code.")
    message: str = Field(description="Human-readable error message.")
    details: dict[str, str] = Field(default_factory=dict, description="Optional safe error metadata.")


class HealthResponse(BaseModel):
    status: str
    service: str
    llm_configured: bool
    model: str


class RouterStatusResponse(BaseModel):
    mode: str
    status: str = "ready"
    message: str
