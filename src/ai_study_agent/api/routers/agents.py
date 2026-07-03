"""Agent API routes."""

from __future__ import annotations

from fastapi import APIRouter
from starlette import status

from ai_study_agent.api.errors import ApiError
from ai_study_agent.api.schemas.agents import (
    AgentRespondRequest,
    AgentRespondResponse,
    CapabilityResponse,
    SkillRunRequest,
    SkillRunResponse,
    SubAgentRoleResponse,
)
from ai_study_agent.api.schemas.common import RouterStatusResponse
from ai_study_agent.agents.service import AgentService, AgentServiceError
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Capability

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status", response_model=RouterStatusResponse)
def agents_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="agent",
        message="Agent router ready. Skills and capability layer are available.",
    )


@router.get("/capabilities", response_model=list[CapabilityResponse])
def list_capabilities() -> list[CapabilityResponse]:
    return [_capability_response(cap) for cap in build_service().list_capabilities()]


@router.get("/roles", response_model=list[SubAgentRoleResponse])
def list_roles() -> list[SubAgentRoleResponse]:
    return [_role_response(role) for role in build_service().list_roles()]


@router.post("/skills/{skill_id}/run", response_model=SkillRunResponse, status_code=status.HTTP_200_OK)
def run_skill(skill_id: str, request: SkillRunRequest) -> SkillRunResponse:
    service = build_service()
    try:
        result = service.run_skill(
            skill_id=skill_id,
            input_text=request.input_text,
            knowledge_base_id=request.knowledge_base_id,
            top_k=request.top_k,
            role_id=request.role_id,
        )
    except AgentServiceError as exc:
        raise ApiError("agent_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc
    return SkillRunResponse(
        skill_id=result.skill_id,
        skill_name=result.skill_name,
        input_text=result.input_text,
        output=result.output,
        context_used=result.context_used,
    )


@router.post("/respond", response_model=AgentRespondResponse, status_code=status.HTTP_200_OK)
def respond(request: AgentRespondRequest) -> AgentRespondResponse:
    service = build_service()
    try:
        result = service.respond(
            input_text=request.input_text,
            knowledge_base_id=request.knowledge_base_id,
            top_k=request.top_k,
            role_id=request.role_id,
        )
    except AgentServiceError as exc:
        raise ApiError("agent_error", str(exc), status_code=status.HTTP_400_BAD_REQUEST) from exc

    return AgentRespondResponse(
        role_id=result.role_id,
        role_name=result.role_name,
        input_text=result.input_text,
        output=result.output,
        context_used=result.context_used,
    )


def build_service() -> AgentService:
    return AgentService.from_config(AppConfig.from_env())


def _role_response(role) -> SubAgentRoleResponse:
    return SubAgentRoleResponse(
        id=role.id,
        name=role.name,
        title=role.title,
        description=role.description,
        greeting=role.greeting,
        preferred_skills=role.preferred_skills,
        tags=role.tags,
    )


def _capability_response(capability: Capability) -> CapabilityResponse:
    return CapabilityResponse(
        id=capability.id,
        name=capability.name,
        kind=capability.kind,
        description=capability.description,
        enabled=capability.enabled,
    )
