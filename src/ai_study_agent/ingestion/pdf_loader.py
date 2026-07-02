"""PDF text extraction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PdfLoadError(ValueError):
    """Raised when PDF content cannot be read as text."""


@dataclass(frozen=True)
class PdfExtractResult:
    title: str
    text: str
    page_count: int


def extract_pdf_text(content: bytes, file_name: str = "") -> PdfExtractResult:
    if not content:
        raise PdfLoadError("PDF 内容不能为空")

    try:
        reader = PdfReader(BytesIO(content))
    except (PdfReadError, ValueError, OSError) as exc:
        raise PdfLoadError("PDF 文件无法解析") from exc

    page_texts = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(page_text for page_text in page_texts if page_text)
    if not text.strip():
        raise PdfLoadError("PDF 未提取到可用文本")

    metadata_title = ""
    if reader.metadata and reader.metadata.title:
        metadata_title = str(reader.metadata.title).strip()
    fallback_title = Path(file_name).stem.strip()
    return PdfExtractResult(
        title=metadata_title or fallback_title or "PDF 文档",
        text=text,
        page_count=len(reader.pages),
    )
