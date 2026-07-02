"""URL fetching and lightweight HTML text extraction."""

from __future__ import annotations

import html
import ipaddress
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import ParseResult, urlparse


class UrlLoadError(ValueError):
    """Raised when a URL cannot be fetched or parsed safely."""


@dataclass(frozen=True)
class UrlFetchResult:
    title: str
    text: str
    content_type: str


class ReadableHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._title_open = False
        self._title: list[str] = []
        self._text: list[str] = []

    def handle_starttag(self, tag: str, _attrs) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if lowered == "title":
            self._title_open = True
        if lowered in {"p", "div", "section", "article", "h1", "h2", "h3", "li", "br"}:
            self._text.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if lowered == "title":
            self._title_open = False
        if lowered in {"p", "div", "section", "article", "h1", "h2", "h3", "li"}:
            self._text.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        normalized = html.unescape(data).strip()
        if not normalized:
            return
        if self._title_open:
            self._title.append(normalized)
        self._text.append(normalized)
        self._text.append(" ")

    @property
    def title(self) -> str:
        return _clean_whitespace(" ".join(self._title))

    @property
    def text(self) -> str:
        return _clean_whitespace("".join(self._text))


def fetch_url_text(url: str, *, timeout_seconds: int = 10, max_bytes: int = 1_500_000) -> UrlFetchResult:
    parsed = _validate_url(url)
    request = urllib.request.Request(
        parsed.geturl(),
        headers={"User-Agent": "ai-study-agent/0.1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get("content-type", "text/html")
            raw = response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise UrlLoadError(f"URL 返回 HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise UrlLoadError(f"URL 抓取失败：{exc.reason}") from exc

    if len(raw) > max_bytes:
        raise UrlLoadError("URL 内容过大")
    text = raw.decode(_detect_charset(content_type), errors="replace")
    if "html" in content_type.lower():
        parser = ReadableHtmlParser()
        parser.feed(text)
        return UrlFetchResult(
            title=parser.title or parsed.netloc,
            text=parser.text,
            content_type="text/html",
        )
    return UrlFetchResult(
        title=parsed.netloc,
        text=_clean_whitespace(text),
        content_type=content_type.split(";", 1)[0].strip() or "text/plain",
    )


def _validate_url(url: str) -> ParseResult:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise UrlLoadError("URL 必须是有效的 http(s) 地址")
    host = parsed.hostname or ""
    if host.lower() in {"localhost"}:
        raise UrlLoadError("不允许抓取本机地址")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return parsed
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise UrlLoadError("不允许抓取内网或本机地址")
    return parsed


def _detect_charset(content_type: str) -> str:
    match = re.search(r"charset=([^;\s]+)", content_type, flags=re.IGNORECASE)
    return match.group(1).strip("\"'") if match else "utf-8"


def _clean_whitespace(text: str) -> str:
    compact = re.sub(r"[ \t]+", " ", text)
    compact = re.sub(r"\n\s*\n\s*\n+", "\n\n", compact)
    compact = re.sub(r" *\n *", "\n", compact)
    return compact.strip()
