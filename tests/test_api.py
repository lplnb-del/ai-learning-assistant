from fastapi.testclient import TestClient

from ai_study_agent.api.main import create_app
from ai_study_agent.api.routers import chat as chat_router
from ai_study_agent.core.domain import Message, MessageRole


def test_health_endpoint_does_not_echo_secret(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-secret")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    client = TestClient(create_app())
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "status": "ok",
        "service": "ai-study-agent",
        "llm_configured": True,
        "model": "deepseek-v4-flash",
    }
    assert "test-secret" not in response.text


def test_core_router_status_endpoints_are_available():
    client = TestClient(create_app())

    expected_modes = {
        "/api/chat/status": "chat",
        "/api/knowledge/status": "knowledge",
        "/api/rag/status": "rag",
        "/api/cards/status": "cards",
        "/api/agents/status": "agent",
    }

    for path, mode in expected_modes.items():
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["mode"] == mode


def test_openapi_docs_include_api_routes():
    client = TestClient(create_app())
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health" in paths
    assert "/api/chat/status" in paths


def test_cors_allows_frontend_origin():
    client = TestClient(create_app())
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


class FakeChatGateway:
    def generate(self, messages, options=None):
        assert messages[-1].role == MessageRole.USER
        assert messages[-1].content == "你好"
        assert options is not None
        assert options.model == "deepseek-chat"
        return Message(role=MessageRole.ASSISTANT, content="你好，老大。")

    def stream(self, messages, options=None):
        assert messages[-1].content == "你好"
        yield "你好"
        yield "，老大。"


def test_chat_completion_uses_gateway(monkeypatch):
    monkeypatch.setattr(chat_router, "build_gateway", lambda: FakeChatGateway())
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    client = TestClient(create_app())

    response = client.post(
        "/api/chat/completions",
        json={
            "messages": [{"role": "user", "content": "你好"}],
            "thinking_depth": "快速",
            "model": "deepseek-chat",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "role": "assistant",
        "content": "你好，老大。",
        "model": "deepseek-chat",
    }


def test_chat_stream_returns_sse_events(monkeypatch):
    monkeypatch.setattr(chat_router, "build_gateway", lambda: FakeChatGateway())
    client = TestClient(create_app())

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"messages": [{"role": "user", "content": "你好"}]},
    ) as response:
        body = response.read().decode("utf-8")

    assert response.status_code == 200
    assert "event: message" in body
    assert '"content": "你好"' in body
    assert '"content": "，老大。"' in body
    assert "event: done" in body
