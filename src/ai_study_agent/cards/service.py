"""QA library and review card service."""

from __future__ import annotations

from ai_study_agent.cards.repository import CardRepository
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import MasteryLevel, QACard, QALibrary
from ai_study_agent.knowledge.repository import KnowledgeRepository
from ai_study_agent.storage.sqlite import connect, initialize_database


class CardServiceError(ValueError):
    """Raised when QA library or card input is invalid."""


class CardService:
    def __init__(self, cards: CardRepository, knowledge: KnowledgeRepository) -> None:
        self._cards = cards
        self._knowledge = knowledge

    @classmethod
    def from_config(cls, config: AppConfig) -> "CardService":
        connection = connect(config.db_path)
        initialize_database(connection)
        return cls(CardRepository(connection), KnowledgeRepository(connection))

    def create_library(self, name: str, description: str = "") -> QALibrary:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise CardServiceError("问答库名称不能为空")
        return self._cards.create_library(name=cleaned_name, description=description.strip())

    def list_libraries(self) -> list[QALibrary]:
        return self._cards.list_libraries()

    def delete_library(self, library_id: str) -> None:
        deleted = self._cards.delete_library(library_id)
        if not deleted:
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
        cleaned_question = question.strip()
        cleaned_answer = answer.strip()
        if not cleaned_question:
            raise CardServiceError("问题不能为空")
        if not cleaned_answer:
            raise CardServiceError("答案不能为空")

        cleaned_qa_library_id = (qa_library_id or "").strip() or None
        cleaned_knowledge_base_id = (knowledge_base_id or "").strip() or None

        if cleaned_qa_library_id and self._cards.get_library(cleaned_qa_library_id) is None:
            raise CardServiceError("问答库不存在")
        if cleaned_knowledge_base_id and self._knowledge.get_knowledge_base(cleaned_knowledge_base_id) is None:
            raise CardServiceError("知识库不存在")

        return self._cards.create_card(
            qa_library_id=cleaned_qa_library_id,
            knowledge_base_id=cleaned_knowledge_base_id,
            question=cleaned_question,
            answer=cleaned_answer,
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
        cleaned_qa_library_id = (qa_library_id or "").strip() or None
        cleaned_knowledge_base_id = (knowledge_base_id or "").strip() or None
        if cleaned_qa_library_id and self._cards.get_library(cleaned_qa_library_id) is None:
            raise CardServiceError("问答库不存在")
        return self._cards.list_cards(
            qa_library_id=cleaned_qa_library_id,
            knowledge_base_id=cleaned_knowledge_base_id,
            mastery=mastery,
            tag=(tag or "").strip() or None,
        )

    def update_mastery(self, card_id: str, mastery: MasteryLevel) -> QACard:
        card = self._cards.update_mastery(card_id, mastery)
        if card is None:
            raise CardServiceError("卡片不存在")
        return card

    def delete_card(self, card_id: str) -> None:
        deleted = self._cards.delete_card(card_id)
        if not deleted:
            raise CardServiceError("卡片不存在")


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
