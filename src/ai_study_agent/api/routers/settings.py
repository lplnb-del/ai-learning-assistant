"""Settings API routes for model, subagent, MCP, and skills configuration."""

from __future__ import annotations

from fastapi import APIRouter

from ai_study_agent.api.schemas.common import RouterStatusResponse
from ai_study_agent.api.schemas.settings import (
    DetectedModel,
    McpServerConfig,
    McpServerUpsertRequest,
    ModelDetectionRequest,
    ModelDetectionResponse,
    ModelProviderConfig,
    PresetInfo,
    PresetsResponse,
    SettingsResponse,
    SkillConfigResponse,
    SkillConfigToggleRequest,
    SkillConfigUpsertRequest,
    SubAgentPromptGenerateRequest,
    SubAgentPromptGenerateResponse,
    SubAgentRoleConfig,
    SubAgentRoleUpsertRequest,
)
from ai_study_agent.core.config import AppConfig
from ai_study_agent.llm.model_factory import (
    OPENAI_COMPATIBLE_PRESETS,
    ProviderConfig,
    create_chat_model,
    detect_huggingface_models,
    detect_ollama_models,
    detect_openai_compatible_models,
)
from ai_study_agent.settings.service import SettingsConsoleService

router = APIRouter(prefix="/settings", tags=["settings"])


def _service() -> SettingsConsoleService:
    return SettingsConsoleService(AppConfig.from_env())


def _resolve_base_url(config: ModelProviderConfig) -> str | None:
    if config.base_url:
        return config.base_url
    if config.preset and config.preset in OPENAI_COMPATIBLE_PRESETS:
        return OPENAI_COMPATIBLE_PRESETS[config.preset]["base_url"]
    return None


def _merge_with_base_url(config: ModelProviderConfig) -> ModelProviderConfig:
    return ModelProviderConfig(
        provider=config.provider,
        preset=config.preset,
        api_key=config.api_key,
        base_url=_resolve_base_url(config),
        model=config.model,
    )


@router.get("/status", response_model=RouterStatusResponse)
def settings_status() -> RouterStatusResponse:
    return RouterStatusResponse(
        mode="settings",
        message="Settings router ready. Model, subagent, MCP, and skills configuration are available.",
    )


@router.get("", response_model=SettingsResponse)
def get_settings() -> SettingsResponse:
    config = AppConfig.from_env()
    service = _service()
    chat = service.get_chat_config()
    embedding = service.get_embedding_config()

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
    _service().save_model_config("chat", request)
    return get_settings()


@router.put("/embedding-model", response_model=SettingsResponse)
def update_embedding_model(request: ModelProviderConfig) -> SettingsResponse:
    _service().save_model_config("embedding", request)
    return get_settings()


@router.get("/presets", response_model=PresetsResponse)
def list_presets() -> PresetsResponse:
    return PresetsResponse(
        presets=[
            PresetInfo(
                key=key,
                name=info["name"],
                base_url=info["base_url"],
                default_chat_model=info["default_chat_model"],
                default_embedding_model=info["default_embedding_model"],
            )
            for key, info in OPENAI_COMPATIBLE_PRESETS.items()
        ]
    )


@router.post("/detect-models", response_model=ModelDetectionResponse)
def detect_models(request: ModelDetectionRequest) -> ModelDetectionResponse:
    try:
        if request.provider == "ollama":
            base_url = request.base_url or "http://localhost:11434"
            models = detect_ollama_models(base_url)
            return ModelDetectionResponse(
                provider="ollama",
                models=[DetectedModel(id=model.id, name=model.name) for model in models],
                success=True,
                message=f"检测到 {len(models)} 个本地模型" if models else "未检测到本地模型，请确认 Ollama 已启动",
            )

        if request.provider == "openai_compatible":
            if not request.api_key:
                return ModelDetectionResponse(
                    provider="openai_compatible",
                    models=[],
                    success=False,
                    message="需要提供 API Key",
                )
            base_url = _resolve_base_url(ModelProviderConfig(**request.model_dump()))
            if not base_url:
                return ModelDetectionResponse(
                    provider="openai_compatible",
                    models=[],
                    success=False,
                    message="需要提供 base_url 或选择预设服务",
                )
            models = detect_openai_compatible_models(request.api_key, base_url)
            return ModelDetectionResponse(
                provider="openai_compatible",
                models=[DetectedModel(id=model.id, name=model.name) for model in models],
                success=True,
                message=f"检测到 {len(models)} 个模型" if models else "未检测到模型，请检查 API Key 和 Base URL",
            )

        if request.provider == "huggingface":
            models = detect_huggingface_models()
            return ModelDetectionResponse(
                provider="huggingface",
                models=[DetectedModel(id=model.id, name=model.name) for model in models],
                success=True,
                message=f"推荐 {len(models)} 个嵌入模型，首次使用将自动下载",
            )

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


@router.get("/subagents", response_model=list[SubAgentRoleConfig])
def list_subagents() -> list[SubAgentRoleConfig]:
    return [SubAgentRoleConfig(**role.__dict__) for role in _service().list_subagents()]


@router.post("/subagents", response_model=SubAgentRoleConfig)
def save_subagent(request: SubAgentRoleUpsertRequest) -> SubAgentRoleConfig:
    role = _service().save_subagent(request.model_dump())
    return SubAgentRoleConfig(**role.__dict__)


@router.delete("/subagents/{role_id}")
def delete_subagent(role_id: str) -> dict[str, bool]:
    _service().delete_subagent(role_id)
    return {"ok": True}


@router.post("/subagents/generate-prompt", response_model=SubAgentPromptGenerateResponse)
def generate_subagent_prompt(request: SubAgentPromptGenerateRequest) -> SubAgentPromptGenerateResponse:
    system_prompt, greeting = _generate_subagent_prompt(request.role_name, request.mission)
    return SubAgentPromptGenerateResponse(system_prompt=system_prompt, greeting=greeting)


@router.get("/mcp-servers", response_model=list[McpServerConfig])
def list_mcp_servers() -> list[McpServerConfig]:
    return [McpServerConfig(**item) for item in _service().list_mcp_servers()]


@router.post("/mcp-servers", response_model=McpServerConfig)
def save_mcp_server(request: McpServerUpsertRequest) -> McpServerConfig:
    return McpServerConfig(**_service().save_mcp_server(request.model_dump()))


@router.delete("/mcp-servers/{server_id}")
def delete_mcp_server(server_id: str) -> dict[str, bool]:
    _service().delete_mcp_server(server_id)
    return {"ok": True}


@router.get("/skills", response_model=list[SkillConfigResponse])
def list_skill_settings() -> list[SkillConfigResponse]:
    return [SkillConfigResponse(**item) for item in _service().list_skill_settings()]


@router.post("/skills", response_model=SkillConfigResponse)
def save_skill_setting(request: SkillConfigUpsertRequest) -> SkillConfigResponse:
    return SkillConfigResponse(**_service().save_skill_setting(request.model_dump()))


@router.put("/skills/{skill_id}", response_model=SkillConfigResponse)
def update_skill_setting(skill_id: str, request: SkillConfigToggleRequest) -> SkillConfigResponse:
    return SkillConfigResponse(**_service().update_skill_setting(skill_id, request.enabled))


@router.delete("/skills/{skill_id}")
def delete_skill_setting(skill_id: str) -> dict[str, bool]:
    _service().delete_skill_setting(skill_id)
    return {"ok": True}


def get_runtime_chat_config() -> ModelProviderConfig | None:
    return _service().get_chat_config()


def get_runtime_embedding_config() -> ModelProviderConfig | None:
    return _service().get_embedding_config()


def _generate_subagent_prompt(role_name: str, mission: str) -> tuple[str, str]:
    service = _service()
    runtime_config = service.get_chat_config()
    if runtime_config:
        try:
            model = create_chat_model(
                ProviderConfig(
                    provider=runtime_config.provider,
                    api_key=runtime_config.api_key,
                    base_url=_resolve_base_url(runtime_config),
                    model=runtime_config.model,
                )
            )
            response = model.invoke(
                [
                    (
                        "system",
                        "你是一个提示词设计专家。请为学习型 AI 角色生成系统提示词和欢迎语。输出格式必须是 JSON，包含 system_prompt 和 greeting 字段。",
                    ),
                    (
                        "human",
                        f"角色名称：{role_name}\n核心使命：{mission}\n请生成适合学习助手场景的系统提示词和一句欢迎语。",
                    ),
                ]
            )
            content = getattr(response, "content", "")
            if isinstance(content, str) and content.strip().startswith("{"):
                import json

                parsed = json.loads(content)
                prompt = str(parsed.get("system_prompt", "")).strip()
                greeting = str(parsed.get("greeting", "")).strip()
                if prompt:
                    return prompt, greeting or f"你好，我是{role_name}。"
        except Exception:
            pass

    system_prompt = (
        f"你是{role_name}。\n"
        f"你的核心使命是：{mission}\n"
        "回答时请优先理解用户目标，给出结构清晰、可执行、面向学习场景的建议；"
        "如果用户提供了资料或上下文，请优先基于资料作答。"
    )
    greeting = f"你好，我是{role_name}。告诉我你的目标或资料，我会围绕“{mission}”来协助你。"
    return system_prompt, greeting
