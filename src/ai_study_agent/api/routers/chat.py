"""Chat API routes."""

from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from starlette import status

from ai_study_agent.api.errors import ApiError
from ai_study_agent.api.schemas.chat import ChatRequest, ChatResponse
from ai_study_agent.api.schemas.common import RouterStatusResponse
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Message, MessageRole
from ai_study_agent.llm.deepseek import (
    ChatOptions,
    DeepSeekGateway,
    LLMConfigurationError,
    LLMGatewayError,
    build_chat_options,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/status", response_model=RouterStatusResponse)
def chat_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="chat",
        message="Chat router ready. Model calls are available through completion and stream endpoints.",
    )


@router.post("/completions", response_model=ChatResponse)
def create_chat_completion(request: ChatRequest) -> ChatResponse:
    gateway = build_gateway()
    try:
        assistant_message = gateway.generate(
            _to_domain_messages(request),
            options=_build_options(request),
        )
    except LLMConfigurationError as exc:
        raise ApiError(
            "llm_configuration_error",
            str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except LLMGatewayError as exc:
        raise ApiError(
            "llm_gateway_error",
            str(exc),
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc

    return ChatResponse(content=assistant_message.content, model=_response_model_name(request))


@router.post("/stream")
def stream_chat_completion(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def build_gateway() -> DeepSeekGateway:
    return DeepSeekGateway(AppConfig.from_env())


def _stream_events(request: ChatRequest) -> Iterator[str]:
    gateway = build_gateway()
    try:
        for chunk in gateway.stream(
            _to_domain_messages(request),
            options=_build_options(request),
        ):
            yield _sse("message", {"content": chunk})
        yield _sse("done", {"ok": True})
    except LLMConfigurationError as exc:
        yield _sse("error", {"code": "llm_configuration_error", "message": str(exc)})
    except LLMGatewayError as exc:
        yield _sse("error", {"code": "llm_gateway_error", "message": str(exc)})


def _to_domain_messages(request: ChatRequest) -> list[Message]:
    payload_messages = request.messages if request.keep_context else request.messages[-1:]
    return [
        Message(role=MessageRole(message.role), content=message.content)
        for message in payload_messages
    ]


def _build_options(request: ChatRequest) -> ChatOptions:
    return build_chat_options(
        request.thinking_depth,
        request.temperature,
        _requested_model(request),
    )


def _response_model_name(request: ChatRequest) -> str:
    return _requested_model(request) or AppConfig.from_env().deepseek_model


def _requested_model(request: ChatRequest) -> str | None:
    return request.model.strip() if request.model and request.model.strip() else None


def _sse(event: str, payload: dict[str, object]) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"
