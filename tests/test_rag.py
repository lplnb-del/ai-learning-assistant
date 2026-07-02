from fastapi.testclient import TestClient

from ai_study_agent.api.main import create_app
from ai_study_agent.rag.embedding import HashingEmbeddingProvider, cosine_similarity


def test_hashing_embedding_is_deterministic_and_normalized():
    provider = HashingEmbeddingProvider(dimensions=32)

    first = provider.embed("RAG 检索增强生成")
    second = provider.embed("RAG 检索增强生成")

    assert first == second
    assert round(cosine_similarity(first, first), 6) == 1
    assert cosine_similarity(first, provider.embed("完全不同")) <= 1


def test_rag_api_answers_with_local_sources(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "RAG 资料库"}).json()
    client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "rag.md",
            "content_type": "text/markdown",
            "content": "# RAG 入门\n\nRAG 会先检索资料，再把命中的上下文交给大模型组织答案。" * 20,
            "chunk_size": 240,
            "chunk_overlap": 40,
        },
    )

    response = client.post(
        "/api/rag/ask",
        json={
            "knowledge_base_id": knowledge_base["id"],
            "question": "RAG 是怎么回答问题的？",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_mode"] == "local_hashing_embedding"
    assert "本地资料摘要" in payload["answer"]
    assert payload["sources"][0]["document_name"] == "rag.md"
    assert payload["sources"][0]["score"] > 0
    assert "资料片段" in payload["prompt_preview"]


def test_rag_api_uses_persistent_vector_index(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    monkeypatch.setenv("AI_STUDY_AGENT_CHROMA_DIR", str(tmp_path / "chroma"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "RAG 资料库"}).json()
    client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "rag.md",
            "content_type": "text/markdown",
            "content": "# RAG 入门\n\nRAG 会先检索资料，再把命中的上下文交给大模型组织答案。" * 20,
            "chunk_size": 240,
            "chunk_overlap": 40,
        },
    )
    client.post(f"/api/knowledge/bases/{knowledge_base['id']}/index/rebuild")

    response = client.post(
        "/api/rag/ask",
        json={
            "knowledge_base_id": knowledge_base["id"],
            "question": "RAG 是怎么回答问题的？",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_mode"] == "local_vector_index"
    assert payload["sources"][0]["document_name"] == "rag.md"


def test_rag_api_rejects_empty_knowledge_base(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "空资料库"}).json()

    response = client.post(
        "/api/rag/ask",
        json={
            "knowledge_base_id": knowledge_base["id"],
            "question": "有什么资料？",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "rag_error"
    assert "chunks" in response.json()["message"]


def test_rag_api_returns_no_match_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "RAG 资料库"}).json()
    client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "redis.md",
            "content_type": "text/markdown",
            "content": "# Redis\n\nRedis 支持 RDB 和 AOF 两种持久化机制。" * 20,
        },
    )

    response = client.post(
        "/api/rag/ask",
        json={
            "knowledge_base_id": knowledge_base["id"],
            "question": "xyznotfound",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sources"] == []
    assert "没有检索到" in payload["answer"]
    assert "未检索到相关片段" in payload["prompt_preview"]
