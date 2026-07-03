"""Settings API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelProviderConfig(BaseModel):
    """Configuration for a single model (chat or embedding).

    provider: "openai_compatible" | "ollama" | "huggingface"
    preset:   optional preset key for openai_compatible (e.g. "deepseek", "openai", "qwen")
              used to auto-fill base_url; if provided, base_url can be overridden.
    """
    provider: str = Field(description="openai_compatible | ollama | huggingface")
    preset: str | None = Field(default=None, max_length=50, description="Preset key for base_url auto-fill")
    api_key: str | None = Field(default=None, max_length=200)
    base_url: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=200)


class SettingsResponse(BaseModel):
    chat_provider: str
    chat_preset: str | None
    chat_model: str | None
    chat_base_url: str | None
    embedding_provider: str
    embedding_preset: str | None
    embedding_model: str | None
    embedding_base_url: str | None


class SubAgentRoleConfig(BaseModel):
    id: str
    name: str
    title: str
    description: str
    system_prompt: str
    greeting: str
    preferred_skills: list[str]
    tags: list[str]


class SubAgentRoleUpsertRequest(BaseModel):
    id: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    system_prompt: str = Field(min_length=1, max_length=12000)
    greeting: str = Field(default="", max_length=500)
    preferred_skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SubAgentPromptGenerateRequest(BaseModel):
    role_name: str = Field(min_length=1, max_length=80)
    mission: str = Field(min_length=1, max_length=600)


class SubAgentPromptGenerateResponse(BaseModel):
    system_prompt: str
    greeting: str


class McpServerConfig(BaseModel):
    id: str
    name: str
    description: str
    command: str
    enabled: bool


class McpServerUpsertRequest(BaseModel):
    id: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=300)
    command: str = Field(default="", max_length=300)
    enabled: bool = Field(default=False)


class SkillConfigResponse(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool
    tags: list[str]
    source: str


class SkillConfigUpsertRequest(BaseModel):
    id: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=300)
    enabled: bool = Field(default=True)
    tags: list[str] = Field(default_factory=list)
    source: str = Field(default="custom", max_length=120)


class SkillConfigToggleRequest(BaseModel):
    enabled: bool


class ModelDetectionRequest(BaseModel):
    """Request to detect available models.

    For openai_compatible: provide api_key + base_url (or preset).
    For ollama: provide base_url (default localhost:11434).
    For huggingface: no extra params needed.
    """
    provider: str = Field(description="openai_compatible | ollama | huggingface")
    preset: str | None = Field(default=None, max_length=50)
    api_key: str | None = Field(default=None, max_length=200)
    base_url: str | None = Field(default=None, max_length=500)


class DetectedModel(BaseModel):
    id: str
    name: str


class ModelDetectionResponse(BaseModel):
    provider: str
    models: list[DetectedModel]
    success: bool
    message: str


class PresetInfo(BaseModel):
    key: str
    name: str
    base_url: str
    default_chat_model: str
    default_embedding_model: str


class PresetsResponse(BaseModel):
    presets: list[PresetInfo]
