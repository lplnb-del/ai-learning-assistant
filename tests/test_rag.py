from fastapi.testclient import TestClient

from ai_study_agent.api.main import create_app
from ai_study_agent.rag.embedding import HashingEmbeddingProvider, cosine_similarity


def test_hashing_embedding_is_deterministic_and_normalized():
    provider = HashingEmbeddingProvider(dimensions=32)

    first = provider.embed("RAG retrieval augmented generation")
    second = provider.embed("RAG retrieval augmented generation")

    assert first == second
    assert round(cosine_similarity(first, first), 6) == 1
    assert cosine_similarity(first, provider.embed("completely different")) <= 1


def _import_text(client, kb_id, name, content):
    return client.post(
        f"/api/knowledge/bases/{kb_id}/documents/import-text",
        json={
            "name": name,
            "content_type": "text/markdown",
            "content": content,
        },
    )


CONTENT_A = "# RAG Intro\n\nRAG retrieves documents then uses context to generate answers." * 20
CONTENT_B = "# Redis\n\nRedis supports RDB and AOF persistence mechanisms." * 20
CONTENT_C = "# Python Basics\n\nPython is an interpreted high-level programming language." * 20
CONTENT_D = "# RAG Introduction\n\nRAG retrieves relevant documents and uses them to generate answers." * 20


def test_rag_api_answers_with_local_sources(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    kb = client.post("/api/knowledge/bases", json={"name": "RAG library"}).json()
    _import_text(client, kb["id"], "rag.md", CONTENT_A)
    response = client.post("/api/rag/ask", json={"knowledge_base_ids": [kb["id"]], "question": "How does RAG answer?", "top_k": 2})
    assert response.status_code == 200
    p = response.json()
    assert p["retrieval_mode"] == "local_hashing_embedding"
    assert len(p["sources"]) > 0
    assert p["sources"][0]["document_name"] == "rag.md"


def test_rag_api_uses_persistent_vector_index(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    monkeypatch.setenv("AI_STUDY_AGENT_CHROMA_DIR", str(tmp_path / "chroma"))
    client = TestClient(create_app())
    kb = client.post("/api/knowledge/bases", json={"name": "RAG library"}).json()
    _import_text(client, kb["id"], "rag.md", CONTENT_A)
    client.post(f"/api/knowledge/bases/{kb['id']}/index/rebuild")
    response = client.post("/api/rag/ask", json={"knowledge_base_ids": [kb["id"]], "question": "How does RAG answer?", "top_k": 2})
    assert response.status_code == 200
    assert response.json()["retrieval_mode"] == "local_vector_index"


def test_rag_api_can_mix_qa_library_sources(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    kb = client.post("/api/knowledge/bases", json={"name": "RAG library"}).json()
    qa = client.post("/api/cards/libraries", json={"name": "Interview QA"}).json()
    _import_text(client, kb["id"], "rag.md", CONTENT_A)
    client.post("/api/cards", json={"qa_library_id": qa["id"], "question": "What does RAG do first?", "answer": "RAG retrieves then generates.", "tags": ["RAG"]})
    response = client.post("/api/rag/ask", json={"knowledge_base_ids": [kb["id"]], "qa_library_ids": [qa["id"]], "question": "What does RAG do first?", "top_k": 3})
    assert response.status_code == 200
    p = response.json()
    assert "qa_library_hybrid" in p["retrieval_mode"]


def test_rag_api_returns_empty_for_knowledge_base_without_chunks(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    kb = client.post("/api/knowledge/bases", json={"name": "Empty"}).json()
    response = client.post("/api/rag/ask", json={"knowledge_base_ids": [kb["id"]], "question": "Any?"})
    assert response.status_code == 200
    assert response.json()["sources"] == []


def test_rag_api_returns_no_match_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    kb = client.post("/api/knowledge/bases", json={"name": "RAG library"}).json()
    _import_text(client, kb["id"], "redis.md", CONTENT_B)
    response = client.post("/api/rag/ask", json={"knowledge_base_ids": [kb["id"]], "question": "xyznotfound", "top_k": 3})
    assert response.status_code == 200
    assert response.json()["sources"] == []


def test_rag_api_supports_multi_knowledge_base_retrieval(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    kb1 = client.post("/api/knowledge/bases", json={"name": "Python docs"}).json()
    kb2 = client.post("/api/knowledge/bases", json={"name": "RAG docs"}).json()
    _import_text(client, kb1["id"], "python.md", CONTENT_C)
    _import_text(client, kb2["id"], "rag.md", CONTENT_D)
    response = client.post("/api/rag/ask", json={"knowledge_base_ids": [kb1["id"], kb2["id"]], "question": "How does RAG work?", "top_k": 3})
    assert response.status_code == 200
    p = response.json()
    assert len(p["sources"]) > 0
    names = {s["document_name"] for s in p["sources"]}
    assert "rag.md" in names


def test_rag_api_rejects_empty_knowledge_base_ids(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    response = client.post("/api/rag/ask", json={"knowledge_base_ids": [], "question": "test"})
    assert response.status_code == 422
