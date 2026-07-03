"""Text cleaning and chunking utilities for Markdown and plain text."""

from __future__ import annotations

import re
from dataclasses import dataclass

SUPPORTED_CONTENT_TYPES = {"text/markdown", "text/plain"}

@dataclass(frozen=True)
class TextChunkDraft:
    index: int
    text: str
    title: str | None
    metadata: dict[str, str]

def normalize_content_type(content_type: str, file_name: str = "") -> str:
    lowered = content_type.strip().lower()
    if lowered in SUPPORTED_CONTENT_TYPES:
        return lowered
    suffix = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
    if suffix in {"md", "markdown"}:
        return "text/markdown"
    if suffix == "txt":
        return "text/plain"
    return lowered or "text/plain"

def clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()

def split_text(text: str, *, chunk_size: int = 800, chunk_overlap: int = 120) -> list[TextChunkDraft]:
    if chunk_size < 200:
        raise ValueError("chunk_size 不能小于 200")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap 不能小于 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")

    cleaned = clean_text(text)
    if not cleaned:
        return []

    from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    
    # Extract headers first
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(cleaned)

    # Then split recursively
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        add_start_index=True
    )
    
    splits = text_splitter.split_documents(md_header_splits)

    chunks: list[TextChunkDraft] = []
    
    # Since we need char_start and char_end for backward compatibility
    # We will search the chunk in the original cleaned text to get approximate indices
    last_idx = 0
    
    for i, doc in enumerate(splits):
        # Determine the title from metadata extracted by MarkdownHeaderTextSplitter
        title = None
        for header_key in ["Header 3", "Header 2", "Header 1"]:
            if header_key in doc.metadata:
                title = doc.metadata[header_key]
                break
                
        chunk_text = doc.page_content.strip()
        
        char_start = doc.metadata.get("start_index", cleaned.find(chunk_text, last_idx))
        if char_start == -1:
            char_start = cleaned.find(chunk_text)
            if char_start == -1:
                char_start = last_idx
        
        char_end = char_start + len(chunk_text)
        last_idx = max(char_start, 0)
        
        metadata = {str(k): str(v) for k, v in doc.metadata.items()}
        metadata["char_start"] = str(char_start)
        metadata["char_end"] = str(char_end)

        chunks.append(
            TextChunkDraft(
                index=i,
                text=chunk_text,
                title=title,
                metadata=metadata,
            )
        )

    return chunks
