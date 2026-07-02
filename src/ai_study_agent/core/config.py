"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class AppConfig:
    deepseek_api_key: str | None
    deepseek_base_url: str
    deepseek_model: str
    embedding_model: str | None
    db_path: str
    chroma_dir: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        env_file = _load_dotenv_values(Path(".env"))
        return cls(
            deepseek_api_key=_empty_to_none(_get_config_value("DEEPSEEK_API_KEY", env_file)),
            deepseek_base_url=_get_config_value("DEEPSEEK_BASE_URL", env_file, "https://api.deepseek.com"),
            deepseek_model=_get_config_value("DEEPSEEK_MODEL", env_file, "deepseek-v4-flash"),
            embedding_model=_empty_to_none(_get_config_value("EMBEDDING_MODEL", env_file)),
            db_path=_get_config_value("AI_STUDY_AGENT_DB_PATH", env_file, "data/ai_study_agent.sqlite3"),
            chroma_dir=_get_config_value("AI_STUDY_AGENT_CHROMA_DIR", env_file, "data/chroma"),
        )

    @property
    def has_llm_key(self) -> bool:
        return bool(self.deepseek_api_key)

    def validate_llm(self) -> list[str]:
        issues: list[str] = []
        if not self.deepseek_api_key:
            issues.append("缺少 DEEPSEEK_API_KEY")
        parsed = urlparse(self.deepseek_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            issues.append("DEEPSEEK_BASE_URL 必须是有效的 http(s) URL")
        if not self.deepseek_model.strip():
            issues.append("DEEPSEEK_MODEL 不能为空")
        return issues


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _get_config_value(key: str, env_file: dict[str, str], default: str | None = None) -> str | None:
    return os.getenv(key) or env_file.get(key) or default


def _load_dotenv_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _strip_quotes(value.strip())
    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
