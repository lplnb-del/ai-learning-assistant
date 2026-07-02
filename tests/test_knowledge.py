from fastapi.testclient import TestClient

from ai_study_agent.api.main import create_app
from ai_study_agent.ingestion.pdf_loader import PdfExtractResult, extract_pdf_text
from ai_study_agent.ingestion.text_splitter import split_text
from ai_study_agent.ingestion.url_loader import UrlFetchResult, fetch_url_text
from ai_study_agent.storage.sqlite import connect, initialize_database


def test_sqlite_schema_initializes_idempotently(tmp_path):
    db_path = tmp_path / "knowledge.sqlite3"
    connection = connect(str(db_path))

    initialize_database(connection)
    initialize_database(connection)

    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"knowledge_bases", "source_documents", "document_chunks"} <= tables


def test_split_text_extracts_markdown_title_and_overlap():
    text = "# RAG 入门\n\n" + "检索增强生成。" * 90

    chunks = split_text(text, chunk_size=220, chunk_overlap=30)

    assert len(chunks) >= 2
    assert chunks[0].title == "RAG 入门"
    assert chunks[0].metadata["char_start"] == "0"
    assert int(chunks[1].metadata["char_start"]) < int(chunks[0].metadata["char_end"])


def test_knowledge_api_creates_base_and_imports_markdown(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())

    create_response = client.post(
        "/api/knowledge/bases",
        json={"name": "项目文档", "description": "用于 RAG 演示"},
    )
    assert create_response.status_code == 201
    knowledge_base = create_response.json()
    assert knowledge_base["name"] == "项目文档"

    import_response = client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "rag.md",
            "content_type": "text/markdown",
            "content": "# RAG 入门\n\n" + "RAG 会先检索资料，再组织答案。" * 60,
            "chunk_size": 240,
            "chunk_overlap": 40,
        },
    )
    assert import_response.status_code == 201
    payload = import_response.json()
    assert payload["document"]["status"] == "indexed"
    assert payload["chunk_count"] == len(payload["chunks"])
    assert payload["chunks"][0]["title"] == "RAG 入门"
    assert payload["chunks"][0]["source_document_id"] == payload["document"]["id"]

    list_response = client.get(f"/api/knowledge/bases/{knowledge_base['id']}/documents")
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "rag.md"

    chunks_response = client.get(f"/api/knowledge/documents/{payload['document']['id']}/chunks")
    assert chunks_response.status_code == 200
    assert chunks_response.json()[0]["text"]


def test_knowledge_api_rejects_unsupported_document_type(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "资料库"}).json()

    response = client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "paper.pdf",
            "content_type": "application/pdf",
            "content": "fake pdf text",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "knowledge_error"
    assert "Markdown 和 TXT" in response.json()["message"]


def test_knowledge_api_rejects_invalid_chunk_config(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "资料库"}).json()

    response = client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "note.txt",
            "content_type": "text/plain",
            "content": "hello " * 80,
            "chunk_size": 200,
            "chunk_overlap": 200,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "knowledge_error"
    assert "chunk_overlap" in response.json()["message"]


def test_knowledge_api_deletes_document_and_chunks(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "资料库"}).json()
    imported = client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "note.md",
            "content_type": "text/markdown",
            "content": "# Note\n\n" + "hello " * 80,
        },
    ).json()

    response = client.delete(f"/api/knowledge/documents/{imported['document']['id']}")

    assert response.status_code == 204
    documents = client.get(f"/api/knowledge/bases/{knowledge_base['id']}/documents").json()
    chunks = client.get(f"/api/knowledge/documents/{imported['document']['id']}/chunks").json()
    assert documents == []
    assert chunks == []


def test_knowledge_api_deletes_base_with_cascade(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "资料库"}).json()
    client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "note.txt",
            "content_type": "text/plain",
            "content": "hello " * 80,
        },
    )

    response = client.delete(f"/api/knowledge/bases/{knowledge_base['id']}")

    assert response.status_code == 204
    assert client.get("/api/knowledge/bases").json() == []


def test_knowledge_api_imports_url_with_fetcher(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))

    def fake_fetch_url_text(url: str):
        assert url == "https://example.com/rag"
        return UrlFetchResult(
            title="RAG URL",
            text="# URL RAG\n\n" + "web content " * 80,
            content_type="text/html",
        )

    monkeypatch.setattr("ai_study_agent.knowledge.service.fetch_url_text", fake_fetch_url_text)
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "资料库"}).json()

    response = client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-url",
        json={
            "url": "https://example.com/rag",
            "chunk_size": 240,
            "chunk_overlap": 40,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["document"]["name"] == "RAG URL"
    assert payload["document"]["source_uri"] == "https://example.com/rag"
    assert payload["chunk_count"] >= 1


def test_knowledge_api_imports_pdf_with_extractor(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))

    def fake_extract_pdf_text(content: bytes, file_name: str):
        assert content == b"%PDF fake content"
        assert file_name == "rag.pdf"
        return PdfExtractResult(
            title="RAG PDF",
            text="# PDF RAG\n\n" + "pdf content " * 80,
            page_count=1,
        )

    monkeypatch.setattr("ai_study_agent.knowledge.service.extract_pdf_text", fake_extract_pdf_text)
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "资料库"}).json()

    response = client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-pdf",
        json={
            "name": "rag.pdf",
            "content_base64": "JVBERiBmYWtlIGNvbnRlbnQ=",
            "chunk_size": 240,
            "chunk_overlap": 40,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["document"]["name"] == "rag.pdf"
    assert payload["document"]["content_type"] == "application/pdf"
    assert payload["chunks"][0]["title"] == "PDF RAG"
    assert payload["chunk_count"] >= 1


def test_knowledge_api_rebuilds_index_from_chunks(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    monkeypatch.setenv("AI_STUDY_AGENT_CHROMA_DIR", str(tmp_path / "chroma"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "资料库"}).json()
    client.post(
        f"/api/knowledge/bases/{knowledge_base['id']}/documents/import-text",
        json={
            "name": "note.md",
            "content_type": "text/markdown",
            "content": "# Note\n\n" + "hello " * 80,
            "chunk_size": 240,
            "chunk_overlap": 40,
        },
    )

    response = client.post(f"/api/knowledge/bases/{knowledge_base['id']}/index/rebuild")

    assert response.status_code == 200
    payload = response.json()
    assert payload["knowledge_base_id"] == knowledge_base["id"]
    assert payload["document_count"] == 1
    assert payload["chunk_count"] >= 1
    assert payload["status"] == "indexed"
    assert list((tmp_path / "chroma").glob("*.json"))


def test_knowledge_api_rejects_rebuild_without_chunks(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_STUDY_AGENT_DB_PATH", str(tmp_path / "knowledge.sqlite3"))
    client = TestClient(create_app())
    knowledge_base = client.post("/api/knowledge/bases", json={"name": "空资料库"}).json()

    response = client.post(f"/api/knowledge/bases/{knowledge_base['id']}/index/rebuild")

    assert response.status_code == 400
    assert response.json()["code"] == "knowledge_error"
    assert "chunks" in response.json()["message"]


def test_pdf_loader_rejects_invalid_pdf():
    try:
        extract_pdf_text(b"not a pdf", "broken.pdf")
    except ValueError as exc:
        assert "PDF 文件无法解析" in str(exc)
    else:
        raise AssertionError("invalid PDF should be rejected")


def test_url_loader_rejects_localhost():
    try:
        fetch_url_text("http://localhost/internal")
    except ValueError as exc:
        assert "本机地址" in str(exc)
    else:
        raise AssertionError("localhost URL should be rejected")
