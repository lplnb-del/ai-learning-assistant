"""Agent capability layer tests."""

from fastapi.testclient import TestClient

from ai_study_agent.api.main import create_app
from ai_study_agent.agent_capabilities.registry import CapabilityRegistry


def test_capability_registry_has_builtin_skills():
    registry = CapabilityRegistry()

    capabilities = registry.list_capabilities()

    assert len(capabilities) >= 4
    ids = {cap.id for cap in capabilities}
    assert "summarize" in ids
    assert "explain" in ids
    assert "quiz" in ids
    assert "generate_cards" in ids
    for cap in capabilities:
        assert cap.enabled is True
        assert cap.kind == "skill"


def test_capability_registry_get_skill():
    registry = CapabilityRegistry()

    skill = registry.get_skill("summarize")

    assert skill is not None
    assert skill.name == "总结提炼"
    assert len(skill.system_prompt) > 0


def test_capability_registry_returns_none_for_unknown():
    registry = CapabilityRegistry()

    assert registry.get_skill("nonexistent") is None


def test_agents_api_lists_capabilities(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "agent.sqlite3"))
    client = TestClient(create_app())

    response = client.get("/api/agents/capabilities")

    assert response.status_code == 200
    caps = response.json()
    assert len(caps) >= 4
    assert any(cap["id"] == "summarize" for cap in caps)
    assert any(cap["id"] == "explain" for cap in caps)


def test_agents_api_runs_skill(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "agent.sqlite3"))
    client = TestClient(create_app())

    response = client.post(
        "/api/agents/skills/explain/run",
        json={"input_text": "What is RAG?"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["skill_id"] == "explain"
    assert result["skill_name"] == "概念解释"
    assert len(result["output"]) > 0
    assert result["context_used"] is False


def test_agents_api_rejects_empty_input(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "agent.sqlite3"))
    client = TestClient(create_app())

    response = client.post(
        "/api/agents/skills/explain/run",
        json={"input_text": ""},
    )

    assert response.status_code == 422


def test_agents_api_rejects_unknown_skill(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "agent.sqlite3"))
    client = TestClient(create_app())

    response = client.post(
        "/api/agents/skills/nonexistent/run",
        json={"input_text": "test input"},
    )

    assert response.status_code == 400
    assert "未找到" in response.json()["message"]


def test_agents_api_runs_skill_with_knowledge_context(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "agent.sqlite3"))
    client = TestClient(create_app())
    kb = client.post("/api/knowledge/bases", json={"name": "RAG docs"}).json()
    client.post(
        f"/api/knowledge/bases/{kb['id']}/documents/import-text",
        json={
            "name": "rag.md",
            "content_type": "text/markdown",
            "content": "# RAG Intro\n\nRAG retrieves documents then generates answers." * 20,
        },
    )

    response = client.post(
        "/api/agents/skills/summarize/run",
        json={"input_text": "Summarize RAG", "knowledge_base_id": kb["id"]},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["skill_id"] == "summarize"
    assert len(result["output"]) > 0


def test_subagent_roles_are_defined():
    from ai_study_agent.agent_capabilities.subagents import list_roles, get_role

    roles = list_roles()
    assert len(roles) >= 4
    ids = {role.id for role in roles}
    assert "education_expert" in ids
    assert "interviewer" in ids
    assert "quiz_coach" in ids
    assert "summary_coach" in ids

    expert = get_role("education_expert")
    assert expert is not None
    assert expert.name == "教育专家"
    assert len(expert.system_prompt) > 0
    assert len(expert.greeting) > 0


def test_agents_api_lists_roles(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "agent.sqlite3"))
    client = TestClient(create_app())

    response = client.get("/api/agents/roles")

    assert response.status_code == 200
    roles = response.json()
    assert len(roles) >= 4
    assert any(role["id"] == "interviewer" for role in roles)
    assert any(role["id"] == "education_expert" for role in roles)


def test_agents_api_runs_skill_with_role(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "agent.sqlite3"))
    client = TestClient(create_app())

    response = client.post(
        "/api/agents/skills/explain/run",
        json={"input_text": "What is RAG?", "role_id": "education_expert"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["skill_id"] == "explain"
    assert len(result["output"]) > 0
