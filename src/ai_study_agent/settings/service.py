"""Persistent settings service backed by a JSON file."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from ai_study_agent.agent_capabilities.subagents import BUILTIN_ROLES, SubAgentRole
from ai_study_agent.api.schemas.settings import ModelProviderConfig
from ai_study_agent.core.config import AppConfig

SETTINGS_FILE_NAME = "settings_console.json"

_runtime_model_secrets: dict[str, str] = {}
LEGACY_AGENT_SKILL_IDS = {"summarize", "explain", "quiz", "generate_cards"}


def default_subagents() -> list[dict[str, Any]]:
    return [role_to_dict(role) for role in BUILTIN_ROLES]


def default_mcp_servers() -> list[dict[str, Any]]:
    return []


def default_skill_settings() -> list[dict[str, Any]]:
    return []


class SettingsConsoleService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._path = Path(config.db_path).resolve().parent / SETTINGS_FILE_NAME

    def get_chat_config(self) -> ModelProviderConfig | None:
        return self._read_model_config("chat")

    def get_embedding_config(self) -> ModelProviderConfig | None:
        return self._read_model_config("embedding")

    def save_model_config(self, target: str, config: ModelProviderConfig) -> None:
        state = self._load_state()
        serialized = config.model_dump()
        if serialized.get("api_key"):
            _runtime_model_secrets[target] = serialized["api_key"]
        serialized.pop("api_key", None)
        state["models"][target] = serialized
        self._save_state(state)

    def list_subagents(self) -> list[SubAgentRole]:
        state = self._load_state()
        return [dict_to_role(item) for item in state["subagents"]]

    def get_subagent(self, role_id: str) -> SubAgentRole | None:
        for role in self.list_subagents():
            if role.id == role_id:
                return role
        return None

    def save_subagent(self, payload: dict[str, Any]) -> SubAgentRole:
        state = self._load_state()
        role_payload = normalize_role_payload(payload)
        role_list = state["subagents"]
        for index, role in enumerate(role_list):
            if role["id"] == role_payload["id"]:
                role_list[index] = role_payload
                self._save_state(state)
                return dict_to_role(role_payload)
        role_list.append(role_payload)
        self._save_state(state)
        return dict_to_role(role_payload)

    def delete_subagent(self, role_id: str) -> None:
        state = self._load_state()
        state["subagents"] = [role for role in state["subagents"] if role["id"] != role_id]
        self._save_state(state)

    def list_mcp_servers(self) -> list[dict[str, Any]]:
        return deepcopy(self._load_state()["mcp_servers"])

    def save_mcp_server(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state()
        item = normalize_mcp_payload(payload)
        for index, server in enumerate(state["mcp_servers"]):
            if server["id"] == item["id"]:
                state["mcp_servers"][index] = item
                self._save_state(state)
                return item
        state["mcp_servers"].append(item)
        self._save_state(state)
        return item

    def delete_mcp_server(self, server_id: str) -> None:
        state = self._load_state()
        state["mcp_servers"] = [server for server in state["mcp_servers"] if server["id"] != server_id]
        self._save_state(state)

    def list_skill_settings(self) -> list[dict[str, Any]]:
        return deepcopy(self._load_state()["skills"])

    def save_skill_setting(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state()
        item = normalize_skill_payload(payload)
        for index, skill in enumerate(state["skills"]):
            if skill["id"] == item["id"]:
                state["skills"][index] = item
                self._save_state(state)
                return deepcopy(item)
        state["skills"].append(item)
        self._save_state(state)
        return deepcopy(item)

    def update_skill_setting(self, skill_id: str, enabled: bool) -> dict[str, Any]:
        state = self._load_state()
        for skill in state["skills"]:
            if skill["id"] == skill_id:
                skill["enabled"] = enabled
                self._save_state(state)
                return deepcopy(skill)
        raise KeyError(skill_id)

    def delete_skill_setting(self, skill_id: str) -> None:
        state = self._load_state()
        state["skills"] = [skill for skill in state["skills"] if skill["id"] != skill_id]
        self._save_state(state)

    def _read_model_config(self, target: str) -> ModelProviderConfig | None:
        state = self._load_state()
        raw = state["models"].get(target)
        if not raw:
            return None
        payload = dict(raw)
        secret = _runtime_model_secrets.get(target)
        if secret:
            payload["api_key"] = secret
        return ModelProviderConfig(**payload)

    def _load_state(self) -> dict[str, Any]:
        if not self._path.exists():
            state = default_state()
            self._save_state(state)
            return state

        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = default_state()
            self._save_state(state)
            return state

        return merge_with_defaults(data)

    def _save_state(self, state: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def default_state() -> dict[str, Any]:
    return {
        "models": {},
        "subagents": default_subagents(),
        "mcp_servers": default_mcp_servers(),
        "skills": default_skill_settings(),
    }


def merge_with_defaults(raw: dict[str, Any]) -> dict[str, Any]:
    state = default_state()
    if isinstance(raw.get("models"), dict):
        state["models"] = raw["models"]
    if isinstance(raw.get("subagents"), list) and raw["subagents"]:
        state["subagents"] = [normalize_role_payload(item) for item in raw["subagents"] if isinstance(item, dict)]
    if isinstance(raw.get("mcp_servers"), list):
        state["mcp_servers"] = [normalize_mcp_payload(item) for item in raw["mcp_servers"] if isinstance(item, dict)]
    if isinstance(raw.get("skills"), list):
        state["skills"] = [
            normalize_skill_payload(item)
            for item in raw["skills"]
            if isinstance(item, dict) and str(item.get("id", "")).strip() not in LEGACY_AGENT_SKILL_IDS
        ]
    return state


def role_to_dict(role: SubAgentRole) -> dict[str, Any]:
    return {
        "id": role.id,
        "name": role.name,
        "title": role.title,
        "description": role.description,
        "system_prompt": role.system_prompt,
        "greeting": role.greeting,
        "preferred_skills": list(role.preferred_skills),
        "tags": list(role.tags),
    }


def dict_to_role(payload: dict[str, Any]) -> SubAgentRole:
    normalized = normalize_role_payload(payload)
    return SubAgentRole(
        id=normalized["id"],
        name=normalized["name"],
        title=normalized["title"],
        description=normalized["description"],
        system_prompt=normalized["system_prompt"],
        greeting=normalized["greeting"],
        preferred_skills=normalized["preferred_skills"],
        tags=normalized["tags"],
    )


def normalize_role_payload(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip() or "未命名角色"
    role_id = slugify(str(payload.get("id") or name))
    title = str(payload.get("title") or name).strip() or name
    description = str(payload.get("description", "")).strip()
    system_prompt = str(payload.get("system_prompt", "")).strip()
    greeting = str(payload.get("greeting", "")).strip() or f"你好，我是{name}。"
    preferred_skills = [str(item).strip() for item in payload.get("preferred_skills", []) if str(item).strip()]
    tags = [str(item).strip() for item in payload.get("tags", []) if str(item).strip()]
    return {
        "id": role_id,
        "name": name,
        "title": title,
        "description": description,
        "system_prompt": system_prompt,
        "greeting": greeting,
        "preferred_skills": preferred_skills,
        "tags": tags,
    }


def normalize_mcp_payload(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip() or "未命名 MCP"
    server_id = slugify(str(payload.get("id") or name))
    return {
        "id": server_id,
        "name": name,
        "description": str(payload.get("description", "")).strip(),
        "command": str(payload.get("command", "")).strip(),
        "enabled": bool(payload.get("enabled", False)),
    }


def normalize_skill_payload(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip() or "未命名 Skill"
    skill_id = slugify(str(payload.get("id") or name))
    return {
        "id": skill_id,
        "name": name,
        "description": str(payload.get("description", "")).strip(),
        "enabled": bool(payload.get("enabled", True)),
        "tags": [str(item).strip() for item in payload.get("tags", []) if str(item).strip()],
        "source": str(payload.get("source", "custom")).strip() or "custom",
    }


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", value.strip()).strip("_")
    return cleaned.lower() or "custom_role"
