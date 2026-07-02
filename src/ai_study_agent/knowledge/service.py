"""Knowledge base service for local document ingestion."""

from __future__ import annotations

from uuid import uuid4

from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Chunk, KnowledgeBase, KnowledgeIndexBuild, SourceDocument
from ai_study_agent.ingestion.pdf_loader import PdfExtractResult, PdfLoadError, extract_pdf_text
from ai_study_agent.ingestion.text_splitter import (
    SUPPORTED_CONTENT_TYPES,
    clean_text,
    normalize_content_type,
    split_text,
)
from ai_study_agent.ingestion.url_loader import UrlFetchResult, UrlLoadError, fetch_url_text
from ai_study_agent.knowledge.repository import KnowledgeRepository
from ai_study_agent.rag.embedding import HashingEmbeddingProvider, LangChainEmbeddingProvider
from ai_study_agent.storage.sqlite import connect, initialize_database
from ai_study_agent.storage.vector_index import ChromaVectorStore, LocalVectorIndex, VectorIndexEntry


def _embed_chunk(provider, chunk):
    title = chunk.title or ""
    text = title + "\n" + chunk.text if title else chunk.text
    return provider.embed(text)


class KnowledgeServiceError(ValueError):
    """Raised when knowledge ingestion input is invalid."""


class KnowledgeService:
    def __init__(
        self,
        repository: KnowledgeRepository,
        vector_index: LocalVectorIndex,
        chroma_store: ChromaVectorStore | None = None,
        url_fetcher=None,
    ) -> None:
        self._repository = repository
        self._vector_index = vector_index
        self._chroma = chroma_store
        self._url_fetcher = url_fetcher or fetch_url_text

    @classmethod
    def from_config(cls, config: AppConfig) -> "KnowledgeService":
        connection = connect(config.db_path)
        initialize_database(connection)
        chroma_store: ChromaVectorStore | None = None
        if config.has_llm_key and config.embedding_model:
            try:
                embedding_provider = LangChainEmbeddingProvider(
                    api_key=config.deepseek_api_key,
                    base_url=config.deepseek_base_url,
                    model=config.embedding_model,
                )
                chroma_store = ChromaVectorStore(config.chroma_dir, embedding_provider)
            except Exception:
                chroma_store = None
        return cls(KnowledgeRepository(connection), LocalVectorIndex(config.chroma_dir), chroma_store)

    def create_knowledge_base(self, name: str, description: str = "") -> KnowledgeBase:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise KnowledgeServiceError("知识库名称不能为空")
        return self._repository.create_knowledge_base(cleaned_name, description.strip())

    def list_knowledge_bases(self) -> list[KnowledgeBase]:
        return self._repository.list_knowledge_bases()

    def delete_knowledge_base(self, knowledge_base_id: str) -> None:
        if self._chroma:
            try:
                self._chroma.delete_by_knowledge_base(knowledge_base_id)
            except Exception:
                pass
        deleted = self._repository.delete_knowledge_base(knowledge_base_id)
        if not deleted:
            raise KnowledgeServiceError("知识库不存在")

    def import_text_document(
        self,
        *,
        knowledge_base_id: str,
        name: str,
        content: str,
        source_uri: str = "",
        content_type: str = "text/plain",
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> tuple[SourceDocument, list[Chunk]]:
        knowledge_base = self._repository.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None:
            raise KnowledgeServiceError("知识库不存在")

        normalized_content_type = normalize_content_type(content_type, name)
        if normalized_content_type not in SUPPORTED_CONTENT_TYPES:
            raise KnowledgeServiceError("当前仅支持 Markdown 和 TXT 文档")

        return self._import_clean_text_document(
            knowledge_base_id=knowledge_base_id,
            name=name,
            content=content,
            source_uri=source_uri,
            content_type=normalized_content_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def import_url_document(
        self,
        *,
        knowledge_base_id: str,
        url: str,
        name: str = "",
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> tuple[SourceDocument, list[Chunk]]:
        try:
            fetched: UrlFetchResult = self._url_fetcher(url)
        except UrlLoadError as exc:
            raise KnowledgeServiceError(str(exc)) from exc

        document_name = name.strip() or fetched.title or url
        return self._import_clean_text_document(
            knowledge_base_id=knowledge_base_id,
            name=document_name,
            content=fetched.text,
            source_uri=url,
            content_type=fetched.content_type or "text/html",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def import_pdf_document(
        self,
        *,
        knowledge_base_id: str,
        name: str,
        content: bytes,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> tuple[SourceDocument, list[Chunk]]:
        try:
            extracted: PdfExtractResult = extract_pdf_text(content, name)
        except PdfLoadError as exc:
            raise KnowledgeServiceError(str(exc)) from exc

        document_name = name.strip() or extracted.title
        return self._import_clean_text_document(
            knowledge_base_id=knowledge_base_id,
            name=document_name,
            content=extracted.text,
            source_uri=document_name,
            content_type="application/pdf",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def _import_clean_text_document(
        self,
        *,
        knowledge_base_id: str,
        name: str,
        content: str,
        source_uri: str,
        content_type: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> tuple[SourceDocument, list[Chunk]]:
        knowledge_base = self._repository.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None:
            raise KnowledgeServiceError("知识库不存在")

        cleaned = clean_text(content)
        if not cleaned:
            raise KnowledgeServiceError("文档内容不能为空")

        try:
            drafts = split_text(cleaned, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        except ValueError as exc:
            raise KnowledgeServiceError(str(exc)) from exc
        if not drafts:
            raise KnowledgeServiceError("文档切分结果为空")

        document_id = str(uuid4())
        chunks = [
            Chunk(
                id=str(uuid4()),
                knowledge_base_id=knowledge_base_id,
                source_document_id=document_id,
                text=draft.text,
                index=draft.index,
                title=draft.title,
                metadata=draft.metadata,
            )
            for draft in drafts
        ]
        document = self._repository.create_document_with_chunks(
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            name=name.strip() or "未命名文档",
            source_uri=source_uri.strip() or name.strip(),
            content_type=content_type,
            text=cleaned,
            chunks=chunks,
        )
        persisted_chunks = [
            Chunk(
                id=chunk.id,
                knowledge_base_id=chunk.knowledge_base_id,
                source_document_id=document.id,
                text=chunk.text,
                index=chunk.index,
                title=chunk.title,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]
        return document, persisted_chunks

    def list_documents(self, knowledge_base_id: str) -> list[SourceDocument]:
        if self._repository.get_knowledge_base(knowledge_base_id) is None:
            raise KnowledgeServiceError("知识库不存在")
        return self._repository.list_documents(knowledge_base_id)

    def rebuild_index(self, knowledge_base_id: str) -> KnowledgeIndexBuild:
        if self._repository.get_knowledge_base(knowledge_base_id) is None:
            raise KnowledgeServiceError("知识库不存在")

        documents = self._repository.list_documents(knowledge_base_id)
        chunk_count = self._repository.count_chunks(knowledge_base_id)
        if not documents or chunk_count == 0:
            raise KnowledgeServiceError("当前知识库还没有可索引的 chunks")

        embedding_provider = HashingEmbeddingProvider()
        entries = [
            VectorIndexEntry(
                chunk_id=item.chunk.id,
                knowledge_base_id=item.chunk.knowledge_base_id,
                source_document_id=item.chunk.source_document_id,
                document_name=item.document_name,
                chunk_index=item.chunk.index,
                title=item.chunk.title,
                text=item.chunk.text,
                embedding=_embed_chunk(embedding_provider, item.chunk),
            )
            for item in self._repository.list_chunks_for_knowledge_base(knowledge_base_id)
        ]
        # Write to local JSON index (always)
        self._vector_index.rebuild(knowledge_base_id, entries)

        # Write to Chroma when available
        chroma_status = ""
        if self._chroma:
            try:
                from ai_study_agent.core.domain import Chunk as _Chunk
                all_chunks = self._repository.list_chunks_for_knowledge_base(knowledge_base_id)
                for item in all_chunks:
                    self._chroma.add_chunks(
                        knowledge_base_id=knowledge_base_id,
                        chunks=[item.chunk],
                        document_name=item.document_name,
                        embeddings=[_embed_chunk(embedding_provider, item.chunk)],
                    )
                chroma_status = " + Chroma"
            except Exception:
                chroma_status = " (Chroma 写入失败，已保留本地索引)"

        return KnowledgeIndexBuild(
            knowledge_base_id=knowledge_base_id,
            document_count=len(documents),
            chunk_count=len(entries),
            status="indexed",
            message=f"已写入向量索引{chroma_status}",
        )

    def delete_document(self, document_id: str) -> None:
        deleted = self._repository.delete_document(document_id)
        if not deleted:
            raise KnowledgeServiceError("文档不存在")

    def list_chunks(self, document_id: str, limit: int = 20) -> list[Chunk]:
        return self._repository.list_chunks(document_id, limit=limit)
