"""Model factory for creating Chat and Embedding models.

Supports multiple providers:
- deepseek: DeepSeek API (OpenAI-compatible)
- openai: OpenAI API
- ollama: Local Ollama models
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelInfo:
    id: str
    name: str
    provider: str
    available: bool = True


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


def create_chat_model(config: ProviderConfig) -> Any:
    """Create a LangChain chat model based on provider config."""
    if config.provider == "ollama":
        from langchain_ollama import ChatOllama
        base_url = config.base_url or "http://localhost:11434"
        return ChatOllama(
            model=config.model or "qwen2.5:7b",
            base_url=base_url,
            temperature=0.7,
        )
    elif config.provider in ("deepseek", "openai"):
        from langchain_openai import ChatOpenAI
        base_url = config.base_url
        if config.provider == "deepseek" and not base_url:
            base_url = "https://api.deepseek.com"
        return ChatOpenAI(
            model=config.model or "deepseek-chat",
            openai_api_key=config.api_key or "sk-placeholder",
            openai_api_base=base_url,
            temperature=0.7,
        )
    else:
        raise ValueError(f"不支持的 provider: {config.provider}")


def create_embedding_model(config: ProviderConfig) -> Any:
    """Create a LangChain embedding model based on provider config."""
    if config.provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        base_url = config.base_url or "http://localhost:11434"
        return OllamaEmbeddings(
            model=config.model or "nomic-embed-text",
            base_url=base_url,
        )
    elif config.provider in ("deepseek", "openai"):
        from langchain_openai import OpenAIEmbeddings
        base_url = config.base_url
        if config.provider == "deepseek" and not base_url:
            base_url = "https://api.deepseek.com"
        return OpenAIEmbeddings(
            model=config.model or "text-embedding-v3",
            openai_api_key=config.api_key or "sk-placeholder",
            openai_api_base=base_url,
        )
    else:
        raise ValueError(f"不支持的 provider: {config.provider}")


def detect_ollama_models(base_url: str = "http://localhost:11434") -> list[ModelInfo]:
    """Detect available models from local Ollama instance."""
    import urllib.request
    import json

    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            return [
                ModelInfo(
                    id=model.get("name", ""),
                    name=model.get("name", ""),
                    provider="ollama",
                    available=True,
                )
                for model in models
            ]
    except Exception:
        return []


def detect_openai_models(api_key: str, base_url: str = "https://api.openai.com/v1") -> list[ModelInfo]:
    """Detect available models from OpenAI-compatible API."""
    import urllib.request
    import json

    try:
        req = urllib.request.Request(
            f"{base_url}/models",
            method="GET",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            return [
                ModelInfo(
                    id=model.get("id", ""),
                    name=model.get("id", ""),
                    provider="openai",
                    available=True,
                )
                for model in models
            ]
    except Exception:
        return []


def detect_deepseek_models(api_key: str) -> list[ModelInfo]:
    """Detect available models from DeepSeek API."""
    return detect_openai_models(api_key, "https://api.deepseek.com/v1")
