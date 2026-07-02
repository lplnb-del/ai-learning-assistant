"""Local RAG retrieval and prompt assembly."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ai_study_agent.cards.repository import CardRepository
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import QACard, QALibrary, RetrievedChunk
from ai_study_agent.knowledge.repository import KnowledgeRepository
from ai_study_agent.rag.embedding import EmbeddingProvider, HashingEmbeddingProvider, cosine_similarity
from ai_study_agent.storage.sqlite import connect, initialize_database
from ai_study_agent.storage.vector_index import LocalVectorIndex


class RagServiceError(ValueError):
    """Raised when a RAG request cannot be answered."""


@dataclass(frozen=True)
class RagSourceItem:
    source_id: str
    source_type: str
    document_id: str
    document_name: str
    chunk_index: int
    title: str | None
    excerpt: str
    score: float


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    sources: list[RagSourceItem]
    prompt_preview: str
    retrieval_mode: str


class RagService:
    def __init__(
        self,
        repository: KnowledgeRepository,
        card_repository: CardRepository,
        vector_index: LocalVectorIndex,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._repository = repository
        self._card_repository = card_repository
        self._vector_index = vector_index
        self._embedding_provider = embedding_provider or HashingEmbeddingProvider()

    @classmethod
    def from_config(cls, config: AppConfig) -> "RagService":
        connection = connect(config.db_path)
        initialize_database(connection)
        return cls(KnowledgeRepository(connection), CardRepository(connection), LocalVectorIndex(config.chroma_dir))

    def answer_question(
        self,
        *,
        knowledge_base_ids: list[str],
        qa_library_ids: list[str] | None = None,
        question: str,
        top_k: int = 3,
    ) -> RagAnswer:
        cleaned_question = question.strip()
        if not cleaned_question:
            raise RagServiceError("问题不能为空")
        cleaned_kb_ids = [item.strip() for item in knowledge_base_ids if item.strip()]
        if not cleaned_kb_ids:
            raise RagServiceError("至少需要选择一个知识库")
        for kb_id in cleaned_kb_ids:
            if self._repository.get_knowledge_base(kb_id) is None:
                raise RagServiceError(f"知识库不存在：{kb_id}")

        selected_qa_library_ids = [item for item in (qa_library_ids or []) if item]
        qa_libraries = self._validate_qa_libraries(selected_qa_library_ids)

        query_embedding = self._embedding_provider.embed(cleaned_question)
        all_sources: list[RetrievedChunk] = []
        retrieval_mode_parts: list[str] = []
        for kb_id in cleaned_kb_ids:
            if self._repository.count_chunks(kb_id) == 0:
                continue
            kb_sources = self._vector_index.search(kb_id, query_embedding, top_k)
            if kb_sources:
                all_sources.extend(kb_sources)
                if "local_vector_index" not in retrieval_mode_parts:
                    retrieval_mode_parts.append("local_vector_index")
            elif self._vector_index.count_entries(kb_id) == 0:
                candidates = self._repository.list_chunks_for_knowledge_base(kb_id)
                ranked = _rank_chunks(candidates, cleaned_question, top_k, self._embedding_provider)
                all_sources.extend(ranked)
                mode_name = self._embedding_provider.name
                if mode_name not in retrieval_mode_parts:
                    retrieval_mode_parts.append(mode_name)
        sources = sorted(all_sources, key=lambda item: item.score, reverse=True)[:top_k]
        retrieval_mode = "+".join(retrieval_mode_parts) if retrieval_mode_parts else "no_results"

        card_sources = _rank_qa_cards(
            self._card_repository.list_cards(qa_library_id=None),
            qa_libraries,
            cleaned_question,
            top_k,
            self._embedding_provider,
        )
        combined_sources = [
            *[_chunk_source_item(source) for source in sources],
            *card_sources,
        ]
        combined_sources = sorted(combined_sources, key=lambda item: item.score, reverse=True)[:top_k]
        if card_sources:
            retrieval_mode = f"{retrieval_mode}+qa_library_hybrid"

        prompt_preview = _build_prompt(cleaned_question, combined_sources)
        return RagAnswer(
            answer=_build_local_answer(cleaned_question, combined_sources),
            sources=combined_sources,
            prompt_preview=prompt_preview,
            retrieval_mode=retrieval_mode,
        )

    def _validate_qa_libraries(self, qa_library_ids: list[str]) -> list[QALibrary]:
        libraries: list[QALibrary] = []
        for library_id in qa_library_ids:
            library = self._card_repository.get_library(library_id)
            if library is None:
                raise RagServiceError("问答库不存在")
            libraries.append(library)
        return libraries


def _rank_chunks(
    candidates: list[RetrievedChunk],
    question: str,
    top_k: int,
    embedding_provider: EmbeddingProvider,
) -> list[RetrievedChunk]:
    terms = _tokenize(question)
    question_vector = embedding_provider.embed(question)
    scored: list[RetrievedChunk] = []
    for item in candidates:
        text = f"{item.chunk.title or ''}\n{item.chunk.text}".lower()
        lexical_score = sum(text.count(term) for term in terms)
        semantic_score = cosine_similarity(question_vector, embedding_provider.embed(text))
        score = lexical_score + semantic_score
        if score > 0:
            scored.append(RetrievedChunk(chunk=item.chunk, document_name=item.document_name, score=round(score, 4)))
    return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


def _rank_qa_cards(
    cards: list[QACard],
    qa_libraries: list[QALibrary],
    question: str,
    top_k: int,
    embedding_provider: EmbeddingProvider,
) -> list[RagSourceItem]:
    if not qa_libraries:
        return []

    libraries_by_id = {library.id: library for library in qa_libraries}
    candidates = [card for card in cards if card.qa_library_id and card.qa_library_id in libraries_by_id]
    terms = _tokenize(question)
    question_vector = embedding_provider.embed(question)
    scored: list[RagSourceItem] = []
    for card in candidates:
        text = f"{card.question}\n{card.answer}".lower()
        lexical_score = sum(text.count(term) for term in terms)
        semantic_score = cosine_similarity(question_vector, embedding_provider.embed(text))
        score = lexical_score + semantic_score
        if score <= 0:
            continue
        library = libraries_by_id[card.qa_library_id]
        scored.append(
            RagSourceItem(
                source_id=card.id,
                source_type="qa_card",
                document_id=library.id,
                document_name=library.name,
                chunk_index=0,
                title=card.question,
                excerpt=_excerpt(card.answer, 220),
                score=round(score, 4),
            )
        )
    return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


def _tokenize(text: str) -> list[str]:
    lowered = text.lower()
    words = [token for token in re.findall(r"[a-z0-9_]+", lowered) if len(token) >= 2]
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", lowered)
    seen: set[str] = set()
    terms: list[str] = []
    for term in [*words, *cjk_chars]:
        if term not in seen:
            seen.add(term)
            terms.append(term)
    return terms or [lowered.strip()]


def _build_prompt(question: str, sources: list[RagSourceItem]) -> str:
    if not sources:
        return (
            "请只基于已选知识库和问答库回答问题。如果资料不足，明确说明不足。\n\n"
            f"问题：{question}\n\n"
            "资料片段：未检索到相关片段"
        )

    context = "\n\n".join(
        _prompt_source_block(index, source)
        for index, source in enumerate(sources, start=1)
    )
    return (
        "请只基于以下知识库片段和问答库卡片回答问题。如果资料不足，明确说明不足。\n\n"
        f"问题：{question}\n\n"
        f"资料片段：\n{context}"
    )


def _build_local_answer(question: str, sources: list[RagSourceItem]) -> str:
    if not sources:
        return (
            f"当前知识库没有检索到与“{question}”相关的片段。"
            "你可以换一个更贴近资料原文的关键词，或先到知识库/问答库补充资料。"
        )

    chunk_sources = [source for source in sources if source.source_type == "knowledge_chunk"]
    qa_sources = [source for source in sources if source.source_type == "qa_card"]
    lines = [
        f"基于当前知识库和问答库，我检索到 {len(sources)} 条相关参考。先给出本地资料摘要：",
        "",
    ]
    for index, source in enumerate(chunk_sources, start=1):
        lines.append(f"[知识库 {index}] {source.excerpt}")
    for index, source in enumerate(qa_sources, start=1):
        title = source.title or "问答卡片"
        lines.append(f"[问答库 {index}] {title}：{source.excerpt}")
    lines.extend(
        [
            "",
            "这一步使用本地 embedding 相似度检索、问答库匹配和 prompt 组装；接入 Chroma 与模型生成后，回答会升级为完整语义 RAG。",
        ]
    )
    return "\n".join(lines)


def _chunk_source_item(source: RetrievedChunk) -> RagSourceItem:
    return RagSourceItem(
        source_id=source.chunk.id,
        source_type="knowledge_chunk",
        document_id=source.chunk.source_document_id,
        document_name=source.document_name,
        chunk_index=source.chunk.index,
        title=source.chunk.title,
        excerpt=_excerpt(source.chunk.text, 220),
        score=source.score,
    )


def _prompt_source_block(index: int, source: RagSourceItem) -> str:
    if source.source_type == "qa_card":
        return f"[{index}] 问答库 {source.document_name}\n问题：{source.title or '未命名问题'}\n答案：{source.excerpt}"
    return f"[{index}] {source.document_name} #chunk_{source.chunk_index + 1}\n{source.excerpt}"


def _excerpt(text: str, limit: int) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized if len(normalized) <= limit else f"{normalized[:limit].rstrip()}..."
