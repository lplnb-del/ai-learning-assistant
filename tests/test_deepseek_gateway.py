import json

import pytest

from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Message, MessageRole
from ai_study_agent.llm.deepseek import (
    ChatOptions,
    DeepSeekGateway,
    LLMConfigurationError,
    build_chat_options,
)


def _config(api_key: str | None = "unit-test-key") -> AppConfig:
    return AppConfig(
        deepseek_api_key=api_key,
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-v4-flash",
        embedding_model=None,
        db_path="data/test.sqlite3",
        chroma_dir="data/chroma",
    )


def test_config_validates_missing_key_without_echoing_secret():
    issues = _config(api_key=None).validate_llm()

    assert issues == ["缺少 DEEPSEEK_API_KEY"]


def test_gateway_builds_openai_compatible_payload():
    gateway = DeepSeekGateway(_config())
    messages = [Message(role=MessageRole.USER, content="你好")]

    payload = gateway._build_payload(messages, ChatOptions(temperature=0.2, max_tokens=128), stream=True)

    assert payload["model"] == "deepseek-v4-flash"
    assert payload["messages"] == [{"role": "user", "content": "你好"}]
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 128
    assert payload["stream"] is True
    assert "thinking" not in payload
    assert "reasoning_effort" not in payload


def test_gateway_rejects_missing_key_before_request():
    gateway = DeepSeekGateway(_config(api_key=None))

    with pytest.raises(LLMConfigurationError):
        gateway._build_payload([Message(role=MessageRole.USER, content="你好")], None, stream=False)


def test_stream_parses_sse_content(monkeypatch):
    gateway = DeepSeekGateway(_config())
    messages = [Message(role=MessageRole.USER, content="你好")]
    event = {"choices": [{"delta": {"content": "你好，老大"}}]}

    monkeypatch.setattr(gateway, "_post_stream_lines", lambda payload: [f"data: {json.dumps(event)}", "data: [DONE]"])

    assert list(gateway.stream(messages)) == ["你好，老大"]


def test_depth_mapping_changes_generation_budget():
    fast = build_chat_options("快速", temperature=0.3)
    deep = build_chat_options("深度", temperature=0.3)

    assert fast.max_tokens < deep.max_tokens
    assert "简洁" in (fast.system_instruction or "")
    assert "分层" in (deep.system_instruction or "")
