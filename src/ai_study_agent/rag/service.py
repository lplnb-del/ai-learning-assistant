"""Local RAG retrieval and prompt assembly."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import RetrievedChunk
from ai_study_agent.knowledge.repository import KnowledgeRepository
from ai_study_agent.rag.embedding import EmbeddingProvider, HashingEmbeddingProvider, cosine_similarity
from ai_study_agent.storage.sqlite import connect, initialize_database
from ai_study_agent.storage.vector_index import LocalVectorIndex


class RagServiceError(ValueError):
    """Raised when a RAG request cannot be answered."""


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    sources: list[RetrievedChunk]
    prompt_preview: str
    retrieval_mode: str


class RagService:
    def __init__(
        self,
        repository: KnowledgeRepository,
        vector_index: LocalVectorIndex,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._repository = repository
        self._vector_index = vector_index
        self._embedding_provider = embedding_provider or HashingEmbeddingProvider()

    @classmethod
    def from_config(cls, config: AppConfig) -> "RagService":
        connection = connect(config.db_path)
        initialize_database(connection)
        return cls(KnowledgeRepository(connection), LocalVectorIndex(config.chroma_dir))

    def answer_question(self, *, knowledge_base_id: str, question: str, top_k: int = 3) -> RagAnswer:
        cleaned_question = question.strip()
        if not cleaned_question:
            raise RagServiceError("问题不能为空")
        if self._repository.get_knowledge_base(knowledge_base_id) is None:
            raise RagServiceError("知识库不存在")

        if self._repository.count_chunks(knowledge_base_id) == 0:
            raise RagServiceError("当前知识库还没有可检索的 chunks")

        query_embedding = self._embedding_provider.embed(cleaned_question)
        sources = self._vector_index.search(knowledge_base_id, query_embedding, top_k)
        retrieval_mode = "local_vector_index"
        if not sources and self._vector_index.count_entries(knowledge_base_id) == 0:
            candidates = self._repository.list_chunks_for_knowledge_base(knowledge_base_id)
            sources = _rank_chunks(candidates, cleaned_question, top_k, self._embedding_provider)
            retrieval_mode = self._embedding_provider.name
        prompt_preview = _build_prompt(cleaned_question, sources)
        return RagAnswer(
            answer=_build_local_answer(cleaned_question, sources),
            sources=sources,
            prompt_preview=prompt_preview,
            retrieval_mode=retrieval_mode,
        )


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


def _build_prompt(question: str, sources: list[RetrievedChunk]) -> str:
    if not sources:
        return (
            "请只基于知识库片段回答问题。如果资料不足，明确说明不足。\n\n"
            f"问题：{question}\n\n"
            "资料片段：未检索到相关片段"
        )

    context = "\n\n".join(
        f"[{index}] {source.document_name} #chunk_{source.chunk.index + 1}\n{source.chunk.text}"
        for index, source in enumerate(sources, start=1)
    )
    return (
        "请只基于以下知识库片段回答问题。如果资料不足，明确说明不足。\n\n"
        f"问题：{question}\n\n"
        f"资料片段：\n{context}"
    )


def _build_local_answer(question: str, sources: list[RetrievedChunk]) -> str:
    if not sources:
        return (
            f"当前知识库没有检索到与“{question}”相关的片段。"
            "你可以换一个更贴近资料原文的关键词，或先到知识库导入更多文档。"
        )

    lines = [
        f"基于当前知识库，我检索到 {len(sources)} 个相关片段。先给出本地资料摘要：",
        "",
    ]
    for index, source in enumerate(sources, start=1):
        excerpt = _excerpt(source.chunk.text, 180)
        lines.append(f"[{index}] {excerpt}")
    lines.extend(
        [
            "",
            "这一步使用本地 embedding 相似度检索和 prompt 组装；接入 Chroma 与模型生成后，回答会升级为完整语义 RAG。",
        ]
    )
    return "\n".join(lines)


def _excerpt(text: str, limit: int) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized if len(normalized) <= limit else f"{normalized[:limit].rstrip()}..."
