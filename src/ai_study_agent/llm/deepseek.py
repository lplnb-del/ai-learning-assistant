"""DeepSeek OpenAI-compatible chat gateway."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Message, MessageRole


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM gateway is missing required configuration."""


class LLMGatewayError(RuntimeError):
    """Raised when the remote LLM API returns an error or malformed response."""


@dataclass(frozen=True)
class ChatOptions:
    temperature: float = 0.7
    max_tokens: int = 1024
    model: str | None = None
    system_instruction: str | None = None


class DeepSeekGateway:
    def __init__(self, config: AppConfig, timeout_seconds: int = 60) -> None:
        self._config = config
        self._timeout_seconds = timeout_seconds

    def generate(self, messages: Sequence[Message], options: ChatOptions | None = None) -> Message:
        payload = self._build_payload(messages, options=options, stream=False)
        data = self._post_json(payload)
        content = _extract_message_content(data)
        return Message(role=MessageRole.ASSISTANT, content=content)

    def stream(self, messages: Sequence[Message], options: ChatOptions | None = None) -> Iterator[str]:
        payload = self._build_payload(messages, options=options, stream=True)
        for line in self._post_stream_lines(payload):
            chunk = _parse_sse_delta(line)
            if chunk:
                yield chunk

    def _build_payload(self, messages: Sequence[Message], options: ChatOptions | None, stream: bool) -> dict[str, Any]:
        issues = self._config.validate_llm()
        if issues:
            raise LLMConfigurationError("；".join(issues))

        options = options or ChatOptions()
        payload: dict[str, Any] = {
            "model": options.model or self._config.deepseek_model,
            "messages": _build_messages(messages, options),
            "temperature": options.temperature,
            "max_tokens": options.max_tokens,
            "stream": stream,
        }
        return payload

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = self._make_request(payload)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise LLMGatewayError(_format_http_error(exc)) from exc
        except urllib.error.URLError as exc:
            raise LLMGatewayError(f"DeepSeek API 请求失败：{exc.reason}") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise LLMGatewayError("DeepSeek API 返回了无法解析的 JSON") from exc

    def _post_stream_lines(self, payload: dict[str, Any]) -> Iterator[str]:
        request = self._make_request(payload)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if line:
                        yield line
        except urllib.error.HTTPError as exc:
            raise LLMGatewayError(_format_http_error(exc)) from exc
        except urllib.error.URLError as exc:
            raise LLMGatewayError(f"DeepSeek API 请求失败：{exc.reason}") from exc

    def _make_request(self, payload: dict[str, Any]) -> urllib.request.Request:
        api_key = self._config.deepseek_api_key
        if not api_key:
            raise LLMConfigurationError("缺少 DEEPSEEK_API_KEY")

        url = self._config.deepseek_base_url.rstrip("/") + "/chat/completions"
        body = json.dumps(payload).encode("utf-8")
        return urllib.request.Request(
            url=url,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )


def build_chat_options(depth: str, temperature: float, model: str | None = None) -> ChatOptions:
    if depth == "快速":
        return ChatOptions(
            temperature=temperature,
            max_tokens=768,
            model=model,
            system_instruction="请用简洁直接的方式回答，优先给出结论。",
        )
    if depth == "深度":
        return ChatOptions(
            temperature=temperature,
            max_tokens=2048,
            model=model,
            system_instruction="请先梳理问题结构，再给出分层、严谨、可执行的回答。",
        )
    return ChatOptions(
        temperature=temperature,
        max_tokens=1024,
        model=model,
        system_instruction="请在准确性和简洁性之间保持平衡。",
    )


def _build_messages(messages: Sequence[Message], options: ChatOptions) -> list[dict[str, str]]:
    payload_messages = [{"role": message.role.value, "content": message.content} for message in messages]
    if options.system_instruction:
        return [{"role": MessageRole.SYSTEM.value, "content": options.system_instruction}, *payload_messages]
    return payload_messages


def _extract_message_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMGatewayError("DeepSeek API 返回结构缺少 choices[0].message.content") from exc
    if not isinstance(content, str):
        raise LLMGatewayError("DeepSeek API 返回的 message.content 不是字符串")
    return content


def _parse_sse_delta(line: str) -> str | None:
    if not line.startswith("data:"):
        return None
    data = line.removeprefix("data:").strip()
    if data == "[DONE]":
        return None
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return None
    choices = payload.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    return content if isinstance(content, str) else None


def _format_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8")
    except Exception:
        body = ""
    if body:
        return f"DeepSeek API 返回 HTTP {exc.code}：{body[:300]}"
    return f"DeepSeek API 返回 HTTP {exc.code}"
