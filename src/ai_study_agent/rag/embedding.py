"""Embedding providers for RAG retrieval."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol


class EmbeddingProvider(Protocol):
    name: str

    def embed(self, text: str) -> list[float]:
        """Return a deterministic embedding vector for text."""


class HashingEmbeddingProvider:
    """Small local embedding provider used before external embedding services are wired."""

    name = "local_hashing_embedding"

    def __init__(self, dimensions: int = 96) -> None:
        self._dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for token in tokenize_for_embedding(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return normalize_vector(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(left_item * right_item for left_item, right_item in zip(left, right, strict=True))


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(item * item for item in vector))
    if norm == 0:
        return vector
    return [item / norm for item in vector]


def tokenize_for_embedding(text: str) -> list[str]:
    lowered = text.lower()
    words = [token for token in re.findall(r"[a-z0-9_]+", lowered) if len(token) >= 2]
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", lowered)
    return [*words, *cjk_chars]
