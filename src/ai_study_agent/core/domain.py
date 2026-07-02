"""Domain types shared by the workbench modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class Mode(StrEnum):
    CHAT = "chat"
    RAG = "rag"
    AGENT = "agent"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MasteryLevel(StrEnum):
    NEW = "new"
    UNSURE = "unsure"
    MASTERED = "mastered"


class CapabilityKind(StrEnum):
    SKILL = "skill"
    MCP_TOOL = "mcp_tool"
    SUB_AGENT = "sub_agent"


@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class KnowledgeBase:
    id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class SourceDocument:
    id: str
    knowledge_base_id: str
    name: str
    source_uri: str
    content_type: str
    status: str = "pending"
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class Chunk:
    id: str
    knowledge_base_id: str
    source_document_id: str
    text: str
    index: int
    title: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeIndexBuild:
    knowledge_base_id: str
    document_count: int
    chunk_count: int
    status: str
    message: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    document_name: str
    score: float


@dataclass(frozen=True)
class QACard:
    id: str
    knowledge_base_id: str | None
    question: str
    answer: str
    source_chunk_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    mastery: MasteryLevel = MasteryLevel.NEW
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    kind: CapabilityKind
    description: str
    enabled: bool = True
