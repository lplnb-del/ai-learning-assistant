"""Settings API routes for model configuration."""

from __future__ import annotations

from fastapi import APIRouter
from starlette import status

from ai_study_agent.api.errors import ApiError
from ai_study_agent.api.schemas.common import RouterStatusResponse
from ai_study_agent.api.schemas.settings import (
    DetectedModel,
    ModelDetectionRequest,
    ModelDetectionResponse,
    ModelProviderConfig,
    SettingsResponse,
)
from ai_study_agent.core.config import AppConfig
from ai_study_agent.llm.model_factory import (
    detect_deepseek_models,
    detect_ollama_models,
    detect_openai_models,
)

router = APIRouter(prefix="/settings", tags=["settings"])

# Runtime settings storage (in-memory for MVP, persist later)
_runtime_settings: dict[str, ModelProviderConfig] = {}


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
    return SettingsResponse(
        chat_provider=chat.provider if chat else ("deepseek" if config.has_llm_key else "local"),
        chat_model=(chat.model if chat else config.deepseek_model) or None,
        chat_base_url=chat.base_url if chat else config.deepseek_base_url,
        embedding_provider=embedding.provider if embedding else ("deepseek" if config.has_llm_key else "local"),
        embedding_model=(embedding.model if embedding else config.embedding_model) or None,
        embedding_base_url=embedding.base_url if embedding else None,
    )


@router.put("/chat-model", response_model=SettingsResponse)
def update_chat_model(request: ModelProviderConfig) -> SettingsResponse:
    _runtime_settings["chat"] = request
    return get_settings()


@router.put("/embedding-model", response_model=SettingsResponse)
def update_embedding_model(request: ModelProviderConfig) -> SettingsResponse:
    _runtime_settings["embedding"] = request
    return get_settings()


@router.post("/detect-models", response_model=ModelDetectionResponse)
def detect_models(request: ModelDetectionRequest) -> ModelDetectionResponse:
    try:
        if request.provider == "ollama":
            base_url = request.base_url or "http://localhost:11434"
            models = detect_ollama_models(base_url)
            return ModelDetectionResponse(
                provider="ollama",
                models=[DetectedModel(id=m.id, name=m.name, provider=m.provider) for m in models],
                success=True,
                message=f"检测到 {len(models)} 个本地模型" if models else "未检测到本地模型，请确认 Ollama 已启动",
            )
        elif request.provider == "deepseek":
            if not request.api_key:
                return ModelDetectionResponse(
                    provider="deepseek",
                    models=[],
                    success=False,
                    message="需要提供 DeepSeek API Key",
                )
            models = detect_deepseek_models(request.api_key)
            return ModelDetectionResponse(
                provider="deepseek",
                models=[DetectedModel(id=m.id, name=m.name, provider=m.provider) for m in models],
                success=True,
                message=f"检测到 {len(models)} 个模型" if models else "未检测到模型，请检查 API Key",
            )
        elif request.provider == "openai":
            if not request.api_key:
                return ModelDetectionResponse(
                    provider="openai",
                    models=[],
                    success=False,
                    message="需要提供 OpenAI API Key",
                )
            base_url = request.base_url or "https://api.openai.com/v1"
            models = detect_openai_models(request.api_key, base_url)
            return ModelDetectionResponse(
                provider="openai",
                models=[DetectedModel(id=m.id, name=m.name, provider=m.provider) for m in models],
                success=True,
                message=f"检测到 {len(models)} 个模型" if models else "未检测到模型，请检查 API Key",
            )
        else:
            return ModelDetectionResponse(
                provider=request.provider,
                models=[],
                success=False,
                message=f"不支持的 provider: {request.provider}",
            )
    except Exception as exc:
        return ModelDetectionResponse(
            provider=request.provider,
            models=[],
            success=False,
            message=f"检测失败: {str(exc)[:100]}",
        )


def get_runtime_chat_config() -> ModelProviderConfig | None:
    return _runtime_settings.get("chat")


def get_runtime_embedding_config() -> ModelProviderConfig | None:
    return _runtime_settings.get("embedding")
