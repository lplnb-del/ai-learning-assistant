"""Settings API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelProviderConfig(BaseModel):
    provider: str = Field(description="deepseek | openai | ollama")
    api_key: str | None = Field(default=None, max_length=200)
    base_url: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=100)


class SettingsResponse(BaseModel):
    chat_provider: str
    chat_model: str | None
    chat_base_url: str | None
    embedding_provider: str
    embedding_model: str | None
    embedding_base_url: str | None


class ModelDetectionRequest(BaseModel):
    provider: str = Field(description="deepseek | openai | ollama")
    api_key: str | None = Field(default=None, max_length=200)
    base_url: str | None = Field(default=None, max_length=500)


class DetectedModel(BaseModel):
    id: str
    name: str
    provider: str


class ModelDetectionResponse(BaseModel):
    provider: str
    models: list[DetectedModel]
    success: bool
    message: str
