"""Model factory for creating Chat and Embedding models.

Provider architecture:
- openai_compatible: Any service implementing OpenAI API protocol
  (DeepSeek, Moonshot, Zhipu, Qwen, Groq, vLLM, LiteLLM, etc.)
  User provides base_url + api_key.
- ollama: Local Ollama instance (no API key needed).
- huggingface: Local sentence-transformers for embeddings only.

Preset base_url templates are provided for common services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelInfo:
    id: str
    name: str
    available: bool = True


@dataclass(frozen=True)
class ProviderConfig:
    """Unified config for any provider.

    For openai_compatible: base_url + api_key + model are all required.
    For ollama: base_url (default http://localhost:11434) + model.
    For huggingface: model (HuggingFace model name, e.g. 'sentence-transformers/all-MiniLM-L6-v2').
    """
    provider: str  # "openai_compatible" | "ollama" | "huggingface"
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


# ---- Preset base_url templates for common OpenAI-compatible services ----

OPENAI_COMPATIBLE_PRESETS: dict[str, dict[str, str]] = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "default_chat_model": "deepseek-chat",
        "default_embedding_model": "text-embedding-v3",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_chat_model": "gpt-4o-mini",
        "default_embedding_model": "text-embedding-3-small",
    },
    "moonshot": {
        "name": "Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "default_chat_model": "moonshot-v1-8k",
        "default_embedding_model": "",
    },
    "zhipu": {
        "name": "Zhipu (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_chat_model": "glm-4-flash",
        "default_embedding_model": "embedding-3",
    },
    "qwen": {
        "name": "Qwen (DashScope)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_chat_model": "qwen-turbo",
        "default_embedding_model": "text-embedding-v3",
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "default_chat_model": "llama-3.3-70b-versatile",
        "default_embedding_model": "",
    },
    "siliconflow": {
        "name": "SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "default_chat_model": "Qwen/Qwen2.5-7B-Instruct",
        "default_embedding_model": "BAAI/bge-m3",
    },
    "vllm": {
        "name": "vLLM (本地/自部署)",
        "base_url": "http://localhost:8000/v1",
        "default_chat_model": "",
        "default_embedding_model": "",
    },
    "lmstudio": {
        "name": "LM Studio",
        "base_url": "http://localhost:1234/v1",
        "default_chat_model": "",
        "default_embedding_model": "",
    },
    "custom": {
        "name": "自定义 OpenAI 兼容",
        "base_url": "",
        "default_chat_model": "",
        "default_embedding_model": "",
    },
}


def get_presets() -> dict[str, dict[str, str]]:
    """Return available OpenAI-compatible presets."""
    return OPENAI_COMPATIBLE_PRESETS


def create_chat_model(config: ProviderConfig) -> Any:
    """Create a LangChain chat model.

    openai_compatible -> ChatOpenAI (works with any OpenAI-protocol service)
    ollama -> ChatOllama
    """
    if config.provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=config.model or "qwen2.5:7b",
            base_url=config.base_url or "http://localhost:11434",
            temperature=0.7,
        )

    if config.provider == "openai_compatible":
        if not config.base_url:
            raise ValueError("openai_compatible provider requires base_url")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.model or "gpt-4o-mini",
            openai_api_key=config.api_key or "sk-placeholder",
            openai_api_base=config.base_url,
            temperature=0.7,
        )

    raise ValueError(f"Unsupported chat provider: {config.provider}")


def create_embedding_model(config: ProviderConfig) -> Any:
    """Create a LangChain embedding model.

    openai_compatible -> OpenAIEmbeddings (works with any OpenAI-protocol embedding service)
    ollama -> OllamaEmbeddings
    huggingface -> HuggingFaceEmbeddings (local sentence-transformers)
    """
    if config.provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=config.model or "nomic-embed-text",
            base_url=config.base_url or "http://localhost:11434",
        )

    if config.provider == "openai_compatible":
        if not config.base_url:
            raise ValueError("openai_compatible provider requires base_url")
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=config.model or "text-embedding-3-small",
            openai_api_key=config.api_key or "sk-placeholder",
            openai_api_base=config.base_url,
        )

    if config.provider == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=config.model or "sentence-transformers/all-MiniLM-L6-v2",
        )

    raise ValueError(f"Unsupported embedding provider: {config.provider}")


def detect_ollama_models(base_url: str = "http://localhost:11434") -> list[ModelInfo]:
    """Detect available models from a local Ollama instance."""
    import json
    import urllib.request

    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [
                ModelInfo(id=m.get("name", ""), name=m.get("name", ""))
                for m in data.get("models", [])
            ]
    except Exception:
        return []


def detect_openai_compatible_models(
    api_key: str,
    base_url: str,
) -> list[ModelInfo]:
    """Detect models from any OpenAI-compatible /v1/models endpoint."""
    import json
    import urllib.request

    url = base_url.rstrip("/")
    if not url.endswith("/models"):
        url = f"{url}/models"

    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("data", [])
            return [
                ModelInfo(id=m.get("id", ""), name=m.get("id", ""))
                for m in items
            ]
    except Exception:
        return []


def detect_huggingface_models() -> list[ModelInfo]:
    """Return popular HuggingFace embedding models (no network call).

    These are commonly used sentence-transformers models.
    Actual download happens lazily when first used.
    """
    popular = [
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/all-mpnet-base-v2",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "BAAI/bge-small-zh-v1.5",
        "BAAI/bge-base-zh-v1.5",
        "BAAI/bge-large-zh-v1.5",
        "moka-ai/m3e-base",
        "text2vec-base-chinese",
    ]
    return [ModelInfo(id=name, name=name) for name in popular]