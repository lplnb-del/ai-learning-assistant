"""Service contracts for the staged implementation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import Protocol

from ai_study_agent.core.domain import (
    Capability,
    Chunk,
    KnowledgeBase,
    Message,
    QACard,
    SourceDocument,
)


class LLMGateway(Protocol):
    def generate(self, messages: Sequence[Message]) -> Message:
        """Return a complete assistant message."""

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        """Yield assistant tokens for streaming output."""


class KnowledgeService(Protocol):
    def list_knowledge_bases(self) -> Sequence[KnowledgeBase]:
        """Return available knowledge bases."""

    def create_knowledge_base(self, name: str, description: str = "") -> KnowledgeBase:
        """Create a knowledge base."""


class IngestionService(Protocol):
    def import_text(self, knowledge_base_id: str, name: str, text: str) -> SourceDocument:
        """Import text content into a knowledge base."""

    def split_document(self, document: SourceDocument) -> Sequence[Chunk]:
        """Split an imported document into chunks."""


class RagService(Protocol):
    def answer(self, knowledge_base_id: str, question: str) -> tuple[str, Sequence[Chunk]]:
        """Answer a question and return supporting chunks."""


class CardService(Protocol):
    def save_card(self, card: QACard) -> QACard:
        """Persist a QA card."""

    def list_cards(self, knowledge_base_id: str | None = None) -> Sequence[QACard]:
        """Return saved QA cards."""


class CapabilityRegistry(Protocol):
    def list_capabilities(self) -> Iterable[Capability]:
        """Return Agent-only capabilities."""


class AgentOrchestrator(Protocol):
    def run(self, goal: str, capabilities: Sequence[str]) -> str:
        """Run a multi-step Agent task."""
