"""QA library, review card, and card generation service."""

from __future__ import annotations

import json as _json
import re as _re

from ai_study_agent.cards.repository import CardRepository
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import MasteryLevel, Message, MessageRole, QACard, QALibrary, Chunk
from ai_study_agent.knowledge.repository import KnowledgeRepository
from ai_study_agent.llm.deepseek import DeepSeekGateway
from ai_study_agent.storage.sqlite import connect, initialize_database


class CardServiceError(ValueError):
    """Raised when QA library or card input is invalid."""


class CardService:
    def __init__(
        self,
        cards: CardRepository,
        knowledge: KnowledgeRepository,
        llm_gateway: DeepSeekGateway | None = None,
    ) -> None:
        self._cards = cards
        self._knowledge = knowledge
        self._llm = llm_gateway

    @classmethod
    def from_config(cls, config: AppConfig) -> "CardService":
        connection = connect(config.db_path)
        initialize_database(connection)
        llm = DeepSeekGateway(config) if config.has_llm_key else None
        return cls(CardRepository(connection), KnowledgeRepository(connection), llm)

    def create_library(self, name: str, description: str = "") -> QALibrary:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise CardServiceError("问答库名称不能为空")
        return self._cards.create_library(name=cleaned_name, description=description.strip())

    def list_libraries(self) -> list[QALibrary]:
        return self._cards.list_libraries()

    def delete_library(self, library_id: str) -> None:
        if not self._cards.delete_library(library_id):
            raise CardServiceError("问答库不存在")

    def create_card(
        self,
        *,
        qa_library_id: str | None = None,
        knowledge_base_id: str | None = None,
        question: str,
        answer: str,
        source_chunk_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> QACard:
        cleaned_q = question.strip()
        cleaned_a = answer.strip()
        if not cleaned_q:
            raise CardServiceError("问题不能为空")
        if not cleaned_a:
            raise CardServiceError("答案不能为空")
        cleaned_lib = (qa_library_id or "").strip() or None
        cleaned_kb = (knowledge_base_id or "").strip() or None
        if cleaned_lib and self._cards.get_library(cleaned_lib) is None:
            raise CardServiceError("问答库不存在")
        if cleaned_kb and self._knowledge.get_knowledge_base(cleaned_kb) is None:
            raise CardServiceError("知识库不存在")
        return self._cards.create_card(
            qa_library_id=cleaned_lib,
            knowledge_base_id=cleaned_kb,
            question=cleaned_q,
            answer=cleaned_a,
            source_chunk_ids=_clean_list(source_chunk_ids),
            tags=_clean_list(tags),
        )

    def list_cards(
        self,
        *,
        qa_library_id: str | None = None,
        knowledge_base_id: str | None = None,
        mastery: MasteryLevel | None = None,
        tag: str | None = None,
    ) -> list[QACard]:
        cleaned_lib = (qa_library_id or "").strip() or None
        cleaned_kb = (knowledge_base_id or "").strip() or None
        if cleaned_lib and self._cards.get_library(cleaned_lib) is None:
            raise CardServiceError("问答库不存在")
        return self._cards.list_cards(
            qa_library_id=cleaned_lib,
            knowledge_base_id=cleaned_kb,
            mastery=mastery,
            tag=(tag or "").strip() or None,
        )

    def update_mastery(self, card_id: str, mastery: MasteryLevel) -> QACard:
        card = self._cards.update_mastery(card_id, mastery)
        if card is None:
            raise CardServiceError("卡片不存在")
        return card

    def delete_card(self, card_id: str) -> None:
        if not self._cards.delete_card(card_id):
            raise CardServiceError("卡片不存在")

    def generate_cards_from_chunks(
        self,
        *,
        qa_library_id: str,
        chunk_ids: list[str],
        knowledge_base_id: str | None = None,
        tags: list[str] | None = None,
    ) -> list[QACard]:
        cleaned_lib = qa_library_id.strip()
        if not cleaned_lib:
            raise CardServiceError("问答库 ID 不能为空")
        if self._cards.get_library(cleaned_lib) is None:
            raise CardServiceError("问答库不存在")
        cleaned_ids = _clean_list(chunk_ids)
        if not cleaned_ids:
            raise CardServiceError("至少需要提供一个 chunk ID")
        chunks = self._knowledge.list_chunks_by_ids(cleaned_ids)
        if not chunks:
            raise CardServiceError("未找到指定的 chunks")
        cleaned_kb = (knowledge_base_id or "").strip() or None
        cleaned_tags = _clean_list(tags)
        qa_pairs = self._generate_qa_pairs(chunks)
        created: list[QACard] = []
        for pair in qa_pairs:
            card = self._cards.create_card(
                qa_library_id=cleaned_lib,
                knowledge_base_id=cleaned_kb,
                question=pair["question"],
                answer=pair["answer"],
                source_chunk_ids=list(cleaned_ids),
                tags=cleaned_tags,
            )
            created.append(card)
        return created

    def generate_cards_from_document(
        self,
        *,
        qa_library_id: str,
        document_id: str,
        tags: list[str] | None = None,
    ) -> list[QACard]:
        cleaned_doc = document_id.strip()
        if not cleaned_doc:
            raise CardServiceError("文档 ID 不能为空")
        chunks = self._knowledge.list_chunks(cleaned_doc)
        if not chunks:
            raise CardServiceError("该文档没有可生成的 chunks")
        return self.generate_cards_from_chunks(
            qa_library_id=qa_library_id,
            chunk_ids=[c.id for c in chunks],
            knowledge_base_id=chunks[0].knowledge_base_id,
            tags=tags,
        )

    def _generate_qa_pairs(self, chunks: list[Chunk]) -> list[dict[str, str]]:
        if self._llm is None:
            return self._local_generate_qa_pairs(chunks)
        try:
            return self._llm_generate_qa_pairs(chunks)
        except Exception:
            return self._local_generate_qa_pairs(chunks)

    def _local_generate_qa_pairs(self, chunks: list[Chunk]) -> list[dict[str, str]]:
        pairs: list[dict[str, str]] = []
        for chunk in chunks:
            text = chunk.text.strip()
            title = chunk.title or ""
            if not text:
                continue
            question = (
                f"请解释{title}的核心概念：{text[:60]}..."
                if title
                else f"请解释以下内容的核心概念：{text[:80]}..."
            )
            answer = text[:500] if len(text) > 500 else text
            pairs.append({"question": question, "answer": answer})
        return pairs

    def _llm_generate_qa_pairs(self, chunks: list[Chunk]) -> list[dict[str, str]]:
        context_blocks: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            title_part = f"[{chunk.title}] " if chunk.title else ""
            context_blocks.append(f"source {idx}: {title_part}{chunk.text}")
        context_text = "\n\n".join(context_blocks)
        prompt = (
            "You are an expert at generating educational QA cards. "
            "Based on the following knowledge chunks, generate 1 high-quality Q&A pair per chunk.\n"
            "Requirements:\n"
            "1. Questions should be specific, clear, suitable for student self-testing or interview prep\n"
            "2. Answers should be concise and accurate, 100-300 characters\n"
            "3. Return as a JSON array, each item with 'question' and 'answer' fields\n"
            "4. Return ONLY the JSON, no other text\n\n"
            f"Knowledge chunks:\n{context_text}\n\n"
            "Generate QA card JSON array:"
        )
        message = Message(role=MessageRole.USER, content=prompt)
        response = self._llm.generate([message])
        content = response.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        pairs = _json.loads(content)
        if not isinstance(pairs, list):
            return self._local_generate_qa_pairs(chunks)
        validated: list[dict[str, str]] = []
        for pair in pairs:
            if isinstance(pair, dict) and "question" in pair and "answer" in pair:
                validated.append({
                    "question": str(pair["question"]).strip(),
                    "answer": str(pair["answer"]).strip(),
                })
        return validated if validated else self._local_generate_qa_pairs(chunks)


def _clean_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        item = value.strip()
        if item and item not in seen:
            cleaned.append(item)
            seen.add(item)
    return cleaned
