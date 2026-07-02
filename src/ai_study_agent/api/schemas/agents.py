"""Agent API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai_study_agent.core.domain import CapabilityKind


class CapabilityResponse(BaseModel):
    id: str
    name: str
    kind: CapabilityKind
    description: str
    enabled: bool


class SubAgentRoleResponse(BaseModel):
    id: str
    name: str
    title: str
    description: str
    greeting: str
    preferred_skills: list[str]
    tags: list[str]


class SkillRunRequest(BaseModel):
    input_text: str = Field(min_length=1, max_length=10000)
    knowledge_base_id: str | None = Field(default=None, max_length=120)
    top_k: int = Field(default=3, ge=1, le=8)
    role_id: str | None = Field(default=None, max_length=60)


class SkillRunResponse(BaseModel):
    skill_id: str
    skill_name: str
    input_text: str
    output: str
    context_used: bool
