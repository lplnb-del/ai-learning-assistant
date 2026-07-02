from fastapi.testclient import TestClient

from ai_study_agent.api.main import create_app
from ai_study_agent.storage.sqlite import connect, initialize_database


def test_sqlite_schema_includes_qa_libraries_and_cards(tmp_path):
    connection = connect(str(tmp_path / "cards.sqlite3"))

    initialize_database(connection)

    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"qa_libraries", "qa_cards"} <= tables


def test_cards_api_manages_libraries_and_cards(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "cards.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "项目资料"}).json()

    create_library_response = client.post(
        "/api/cards/libraries",
        json={"name": "后端面试问答", "description": "沉淀常见问答"},
    )
    assert create_library_response.status_code == 201
    library = create_library_response.json()
    assert library["name"] == "后端面试问答"

    create_card_response = client.post(
        "/api/cards",
        json={
            "qa_library_id": library["id"],
            "knowledge_base_id": knowledge_base["id"],
            "question": "RAG 是什么？",
            "answer": "RAG 会先检索资料，再组织回答。",
            "source_chunk_ids": ["chunk-1", "chunk-1", "chunk-2"],
            "tags": ["RAG", "RAG", "面试"],
        },
    )

    assert create_card_response.status_code == 201
    card = create_card_response.json()
    assert card["qa_library_id"] == library["id"]
    assert card["mastery"] == "new"
    assert card["source_chunk_ids"] == ["chunk-1", "chunk-2"]
    assert card["tags"] == ["RAG", "面试"]

    list_cards_response = client.get(f"/api/cards?qa_library_id={library['id']}&tag=RAG")
    assert list_cards_response.status_code == 200
    assert [item["id"] for item in list_cards_response.json()] == [card["id"]]

    update_response = client.patch(f"/api/cards/{card['id']}/mastery", json={"mastery": "mastered"})
    assert update_response.status_code == 200
    assert update_response.json()["mastery"] == "mastered"

    list_libraries_response = client.get("/api/cards/libraries")
    assert list_libraries_response.status_code == 200
    assert list_libraries_response.json()[0]["id"] == library["id"]

    delete_card_response = client.delete(f"/api/cards/{card['id']}")
    assert delete_card_response.status_code == 204
    assert client.get(f"/api/cards?qa_library_id={library['id']}").json() == []

    delete_library_response = client.delete(f"/api/cards/libraries/{library['id']}")
    assert delete_library_response.status_code == 204
    assert client.get("/api/cards/libraries").json() == []


def test_cards_api_rejects_unknown_library(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "cards.sqlite3"))
    client = TestClient(create_app())

    response = client.post(
        "/api/cards",
        json={
            "qa_library_id": "missing",
            "question": "问题",
            "answer": "答案",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "cards_error"
    assert "问答库不存在" in response.json()["message"]


def test_cards_api_generates_from_document(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "cards.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "RAG 资料库"}).json()
    import_result = client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "rag-intro.md",
            "content_type": "text/markdown",
            "content": "# RAG 入门\n\nRAG 会先检索资料，再把命中的上下文交给大模型组织答案。\n\n## 核心流程\n\n1. 用户提问\n2. 检索相关 chunks\n3. 组装 prompt\n4. 调用 LLM 生成回答",
            "chunk_size": 200,
            "chunk_overlap": 40,
        },
    )
    assert import_result.status_code == 201
    document = import_result.json()["document"]

    library = client.post("/api/cards/libraries", json={"name": "RAG 问答库"}).json()

    response = client.post(
        "/api/cards/generate-from-document",
        json={
            "qa_library_id": library["id"],
            "document_id": document["id"],
            "tags": ["RAG", "自动生成"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["generated_count"] >= 1
    assert len(payload["cards"]) == payload["generated_count"]
    for card in payload["cards"]:
        assert card["qa_library_id"] == library["id"]
        assert card["knowledge_base_id"] == knowledge_base["id"]
        assert "RAG" in card["tags"]
        assert "自动生成" in card["tags"]
        assert card["mastery"] == "new"
        assert len(card["question"]) > 0
        assert len(card["answer"]) > 0


def test_cards_api_generates_from_chunks(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "cards.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "RAG 资料库"}).json()
    import_result = client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "rag-intro.md",
            "content_type": "text/markdown",
            "content": "# RAG 入门\n\nRAG 会先检索资料，再把命中的上下文交给大模型组织答案。\n\n## 核心流程\n\n1. 用户提问\n2. 检索相关 chunks\n3. 组装 prompt\n4. 调用 LLM 生成回答",
            "chunk_size": 200,
            "chunk_overlap": 40,
        },
    )
    assert import_result.status_code == 201
    chunks = import_result.json()["chunks"]
    chunk_ids = [chunk["id"] for chunk in chunks[:2]]

    library = client.post("/api/cards/libraries", json={"name": "RAG 问答库"}).json()

    response = client.post(
        "/api/cards/generate-from-chunks",
        json={
            "qa_library_id": library["id"],
            "chunk_ids": chunk_ids,
            "knowledge_base_id": knowledge_base["id"],
            "tags": ["选中生成"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["generated_count"] >= 1
    assert len(payload["cards"]) == payload["generated_count"]
    for card in payload["cards"]:
        assert card["qa_library_id"] == library["id"]
        assert "选中生成" in card["tags"]


def test_cards_api_rejects_empty_chunk_ids(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "cards.sqlite3"))
    client = TestClient(create_app())
    library = client.post("/api/cards/libraries", json={"name": "测试问答库"}).json()

    response = client.post(
        "/api/cards/generate-from-chunks",
        json={
            "qa_library_id": library["id"],
            "chunk_ids": [],
        },
    )

    assert response.status_code == 422


def test_cards_api_rejects_unknown_document(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "cards.sqlite3"))
    client = TestClient(create_app())
    library = client.post("/api/cards/libraries", json={"name": "测试问答库"}).json()

    response = client.post(
        "/api/cards/generate-from-document",
        json={
            "qa_library_id": library["id"],
            "document_id": "nonexistent-doc-id",
        },
    )

    assert response.status_code == 400
    assert "文档" in response.json()["message"]
