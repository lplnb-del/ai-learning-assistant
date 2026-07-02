"""Chat API schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ChatRole = Literal["user", "assistant", "system"]
ThinkingDepth = Literal["快速", "标准", "深度"]


class ChatMessagePayload(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    messages: list[ChatMessagePayload] = Field(min_length=1, max_length=40)
    temperature: float = Field(default=0.7, ge=0, le=2)
    thinking_depth: ThinkingDepth = "标准"
    model: str | None = Field(default=None, max_length=80)
    keep_context: bool = True
    web_search: bool = False


class ChatResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str
    model: str
