"""Settings API routes for model configuration."""

from __future__ import annotations

from fastapi import APIRouter

from ai_study_agent.api.schemas.common import RouterStatusResponse
from ai_study_agent.api.schemas.settings import (
    DetectedModel,
    ModelDetectionRequest,
    ModelDetectionResponse,
    ModelProviderConfig,
    PresetInfo,
    PresetsResponse,
    SettingsResponse,
)
from ai_study_agent.core.config import AppConfig
from ai_study_agent.llm.model_factory import (
    OPENAI_COMPATIBLE_PRESETS,
    detect_huggingface_models,
    detect_ollama_models,
    detect_openai_compatible_models,
)

router = APIRouter(prefix="/settings", tags=["settings"])

# Runtime settings storage (in-memory for MVP, persist later)
_runtime_settings: dict[str, ModelProviderConfig] = {}


def _resolve_base_url(config: ModelProviderConfig) -> str | None:
    """Resolve base_url from explicit value or preset."""
    if config.base_url:
        return config.base_url
    if config.preset and config.preset in OPENAI_COMPATIBLE_PRESETS:
        return OPENAI_COMPATIBLE_PRESETS[config.preset]["base_url"]
    return None


@router.get("/status", response_model=RouterStatusResponse)
def settings_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="settings",
        message="Settings router ready. Model provider configuration and detection are available.",
    )


@router.get("", response_model=SettingsResponse)
def get_settings() -> SettingsResponse:
    config = AppConfig.from_env()
    chat = _runtime_settings.get("chat")
    embedding = _runtime_settings.get("embedding")

    if chat:
        chat_provider = chat.provider
        chat_preset = chat.preset
        chat_model = chat.model
        chat_base_url = _resolve_base_url(chat)
    else:
        chat_provider = "openai_compatible" if config.has_llm_key else "ollama"
        chat_preset = "deepseek" if config.has_llm_key else None
        chat_model = config.deepseek_model or None
        chat_base_url = config.deepseek_base_url if config.has_llm_key else None

    if embedding:
        emb_provider = embedding.provider
        emb_preset = embedding.preset
        emb_model = embedding.model
        emb_base_url = _resolve_base_url(embedding)
    else:
        emb_provider = "openai_compatible" if config.has_llm_key else "ollama"
        emb_preset = "deepseek" if config.has_llm_key else None
        emb_model = config.embedding_model or None
        emb_base_url = None

    return SettingsResponse(
        chat_provider=chat_provider,
        chat_preset=chat_preset,
        chat_model=chat_model,
        chat_base_url=chat_base_url,
        embedding_provider=emb_provider,
        embedding_preset=emb_preset,
        embedding_model=emb_model,
        embedding_base_url=emb_base_url,
    )


@router.put("/chat-model", response_model=SettingsResponse)
def update_chat_model(request: ModelProviderConfig) -> SettingsResponse:
    _runtime_settings["chat"] = request
    return get_settings()


@router.put("/embedding-model", response_model=SettingsResponse)
def update_embedding_model(request: ModelProviderConfig) -> SettingsResponse:
    _runtime_settings["embedding"] = request
    return get_settings()


@router.get("/presets", response_model=PresetsResponse)
def list_presets() -> PresetsResponse:
    """List available OpenAI-compatible service presets."""
    items = []
    for key, info in OPENAI_COMPATIBLE_PRESETS.items():
        items.append(PresetInfo(
            key=key,
            name=info["name"],
            base_url=info["base_url"],
            default_chat_model=info["default_chat_model"],
            default_embedding_model=info["default_embedding_model"],
        ))
    return PresetsResponse(presets=items)


@router.post("/detect-models", response_model=ModelDetectionResponse)
def detect_models(request: ModelDetectionRequest) -> ModelDetectionResponse:
    try:
        if request.provider == "ollama":
            base_url = request.base_url or "http://localhost:11434"
            models = detect_ollama_models(base_url)
            return ModelDetectionResponse(
                provider="ollama",
                models=[DetectedModel(id=m.id, name=m.name) for m in models],
                success=True,
                message=f"\u68c0\u6d4b\u5230 {len(models)} \u4e2a\u672c\u5730\u6a21\u578b" if models else "\u672a\u68c0\u6d4b\u5230\u672c\u5730\u6a21\u578b\uff0c\u8bf7\u786e\u8ba4 Ollama \u5df2\u542f\u52a8",
            )

        if request.provider == "openai_compatible":
            if not request.api_key:
                return ModelDetectionResponse(
                    provider="openai_compatible",
                    models=[],
                    success=False,
                    message="\u9700\u8981\u63d0\u4f9b API Key",
                )
            base_url = _resolve_base_url(request)
            if not base_url:
                return ModelDetectionResponse(
                    provider="openai_compatible",
                    models=[],
                    success=False,
                    message="\u9700\u8981\u63d0\u4f9b base_url \u6216\u9009\u62e9\u9884\u8bbe\u670d\u52a1",
                )
            models = detect_openai_compatible_models(request.api_key, base_url)
            return ModelDetectionResponse(
                provider="openai_compatible",
                models=[DetectedModel(id=m.id, name=m.name) for m in models],
                success=True,
                message=f"\u68c0\u6d4b\u5230 {len(models)} \u4e2a\u6a21\u578b" if models else "\u672a\u68c0\u6d4b\u5230\u6a21\u578b\uff0c\u8bf7\u68c0\u67e5 API Key \u548c Base URL",
            )

        if request.provider == "huggingface":
            models = detect_huggingface_models()
            return ModelDetectionResponse(
                provider="huggingface",
                models=[DetectedModel(id=m.id, name=m.name) for m in models],
                success=True,
                message=f"\u63a8\u8350 {len(models)} \u4e2a\u5d4c\u5165\u6a21\u578b\uff0c\u9996\u6b21\u4f7f\u7528\u5c06\u81ea\u52a8\u4e0b\u8f7d",
            )

        return ModelDetectionResponse(
            provider=request.provider,
            models=[],
            success=False,
            message=f"\u4e0d\u652f\u6301\u7684 provider: {request.provider}",
        )
    except Exception as exc:
        return ModelDetectionResponse(
            provider=request.provider,
            models=[],
            success=False,
            message=f"\u68c0\u6d4b\u5931\u8d25: {str(exc)[:100]}",
        )


def get_runtime_chat_config() -> ModelProviderConfig | None:
    return _runtime_settings.get("chat")


def get_runtime_embedding_config() -> ModelProviderConfig | None:
    return _runtime_settings.get("embedding")