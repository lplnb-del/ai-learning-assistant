"""Agent capability registry with built-in skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ai_study_agent.core.domain import Capability, CapabilityKind, Message, MessageRole


class SkillRunner(Protocol):
    def run(self, input_text: str, context: str = "") -> str:
        """Execute the skill and return the result."""


@dataclass
class SkillDefinition:
    id: str
    name: str
    description: str
    system_prompt: str
    input_placeholder: str = ""
    tags: list[str] = field(default_factory=list)


BUILTIN_SKILLS: list[SkillDefinition] = [
    SkillDefinition(
        id="summarize",
        name="总结提炼",
        description="把输入内容总结为要点或提纲，适合快速复盘资料。",
        system_prompt=(
            "你是一个擅长总结的学习助手。请把用户提供的内容总结为清晰的要点或提纲。"
            "要求：1)保留核心概念和关键信息 2)使用条理清晰的结构 3)适合面试复习"
        ),
        input_placeholder="请总结以下内容...",
        tags=["总结", "复盘"],
    ),
    SkillDefinition(
        id="explain",
        name="概念解释",
        description="用简洁易懂的方式解释一个技术概念，适合学习新知识。",
        system_prompt=(
            "你是一个耐心的技术导师。请用简洁易懂的方式解释用户提出的技术概念。"
            "要求：1)先给一句话定义 2)再展开解释核心原理 3)给出一个实际例子 4)适合学生理解"
        ),
        input_placeholder="请解释一个概念，例如：什么是 RAG？",
        tags=["学习", "解释"],
    ),
    SkillDefinition(
        id="quiz",
        name="出题练习",
        description="基于输入内容生成练习题，适合检验掌握程度。",
        system_prompt=(
            "你是一个出题教练。请基于用户提供的内容生成 3-5 道练习题。"
            "要求：1)包含选择题和简答题 2)覆盖核心知识点 3)附带参考答案 4)难度适合面试准备"
        ),
        input_placeholder="请基于以下内容出题...",
        tags=["练习", "出题"],
    ),
    SkillDefinition(
        id="generate_cards",
        name="生成问答卡片",
        description="把输入内容转化为问答卡片格式，可直接保存到问答库。",
        system_prompt=(
            "你是一个问答卡片生成专家。请把用户提供的内容转化为问答卡片。"
            "要求：1)每张卡片包含问题和答案 2)问题具体明确 3)答案简洁准确（100-300字）"
            "4)用 JSON 数组格式返回，每项包含 question 和 answer 字段 5)只返回 JSON"
        ),
        input_placeholder="请把以下内容转化为问答卡片...",
        tags=["卡片", "生成"],
    ),
]


class CapabilityRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, SkillDefinition] = {skill.id: skill for skill in BUILTIN_SKILLS}

    def list_capabilities(self) -> list[Capability]:
        return [
            Capability(
                id=skill.id,
                name=skill.name,
                kind=CapabilityKind.SKILL,
                description=skill.description,
                enabled=True,
            )
            for skill in self._skills.values()
        ]

    def get_skill(self, skill_id: str) -> SkillDefinition | None:
        return self._skills.get(skill_id)

    def list_skill_definitions(self) -> list[SkillDefinition]:
        return list(self._skills.values())
