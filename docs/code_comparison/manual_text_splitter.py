"""
这是手写的 Text Splitter 实现，用于与 LangChain 的实现进行对比。
"""

import re
from dataclasses import dataclass

@dataclass(frozen=True)
class TextChunkDraft:
    index: int
    text: str
    title: str | None
    metadata: dict[str, str]

def split_text(text: str, *, chunk_size: int = 800, chunk_overlap: int = 120) -> list[TextChunkDraft]:
    if chunk_size < 200:
        raise ValueError("chunk_size 不能小于 200")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap 不能小于 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")

    # 简化：假设传入的 text 已经是 clean 过的
    cleaned = text
    if not cleaned:
        return []

    sections = _split_into_sections(cleaned)
    chunks: list[TextChunkDraft] = []
    current_text = ""
    current_title: str | None = None

    for title, paragraph in sections:
        candidate = paragraph if not current_text else f"{current_text}\n\n{paragraph}"
        if len(candidate) <= chunk_size:
            current_text = candidate
            current_title = current_title or title
            continue
        if current_text:
            chunks.extend(_window_chunk(current_text, current_title, chunk_size, chunk_overlap, len(chunks)))
        current_text = paragraph
        current_title = title

    if current_text:
        chunks.extend(_window_chunk(current_text, current_title, chunk_size, chunk_overlap, len(chunks)))

    return chunks

def _split_into_sections(text: str) -> list[tuple[str | None, str]]:
    title: str | None = None
    sections: list[tuple[str | None, str]] = []
    buffer: list[str] = []

    for block in text.split("\n\n"):
        heading = _extract_heading(block)
        if heading:
            if buffer:
                sections.append((title, "\n\n".join(buffer).strip()))
                buffer = []
            title = heading
        buffer.append(block.strip())

    if buffer:
        sections.append((title, "\n\n".join(buffer).strip()))
    return [(item_title, body) for item_title, body in sections if body]

def _extract_heading(block: str) -> str | None:
    first_line = block.splitlines()[0].strip()
    match = re.match(r"^(#{1,6})\s+(.+)$", first_line)
    return match.group(2).strip() if match else None

def _window_chunk(
    text: str,
    title: str | None,
    chunk_size: int,
    chunk_overlap: int,
    start_index: int,
) -> list[TextChunkDraft]:
    chunks: list[TextChunkDraft] = []
    cursor = 0
    index = start_index
    while cursor < len(text):
        end = min(cursor + chunk_size, len(text))
        chunk_text = text[cursor:end].strip()
        if chunk_text:
            chunks.append(
                TextChunkDraft(
                    index=index,
                    text=chunk_text,
                    title=title,
                    metadata={"char_start": str(cursor), "char_end": str(end)},
                )
            )
            index += 1
        if end >= len(text):
            break
        cursor = max(end - chunk_overlap, cursor + 1)
    return chunks
