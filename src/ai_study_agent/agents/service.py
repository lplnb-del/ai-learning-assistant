"""Agent skill execution service."""

from __future__ import annotations

from dataclasses import dataclass

from ai_study_agent.agent_capabilities.registry import CapabilityRegistry, SkillDefinition
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Message, MessageRole
from ai_study_agent.llm.deepseek import ChatOptions, DeepSeekGateway
from ai_study_agent.rag.service import RagService


class AgentServiceError(ValueError):
    """Raised when an agent request cannot be fulfilled."""


@dataclass(frozen=True)
class SkillResult:
    skill_id: str
    skill_name: str
    input_text: str
    output: str
    context_used: bool


class AgentService:
    def __init__(
        self,
        registry: CapabilityRegistry,
        llm: DeepSeekGateway | None = None,
        rag: RagService | None = None,
    ) -> None:
        self._registry = registry
        self._llm = llm
        self._rag = rag

    @classmethod
    def from_config(cls, config: AppConfig) -> "AgentService":
        from ai_study_agent.storage.sqlite import connect, initialize_database
        from ai_study_agent.knowledge.repository import KnowledgeRepository
        from ai_study_agent.cards.repository import CardRepository
        from ai_study_agent.rag.service import RagService
        from ai_study_agent.storage.vector_index import LocalVectorIndex

        registry = CapabilityRegistry()
        llm = DeepSeekGateway(config) if config.has_llm_key else None
        rag = None
        try:
            connection = connect(config.db_path)
            initialize_database(connection)
            rag = RagService(KnowledgeRepository(connection), CardRepository(connection), LocalVectorIndex(config.chroma_dir))
        except Exception:
            pass
        return cls(registry, llm, rag)

    def list_capabilities(self):
        return self._registry.list_capabilities()

    def list_skills(self):
        return self._registry.list_skill_definitions()

    def run_skill(
        self,
        *,
        skill_id: str,
        input_text: str,
        knowledge_base_id: str | None = None,
        top_k: int = 3,
    ) -> SkillResult:
        cleaned_input = input_text.strip()
        if not cleaned_input:
            raise AgentServiceError("输入内容不能为空")

        skill = self._registry.get_skill(skill_id)
        if skill is None:
            raise AgentServiceError(f"未找到能力：{skill_id}")

        context = ""
        if knowledge_base_id and self._rag:
            try:
                rag_answer = self._rag.answer_question(
                    knowledge_base_ids=[knowledge_base_id],
                    question=cleaned_input[:200],
                    top_k=top_k,
                )
                if rag_answer.sources:
                    context_parts = []
                    for source in rag_answer.sources[:3]:
                        context_parts.append(f"[{source.document_name}] {source.excerpt}")
                    context = "\n\n".join(context_parts)
            except Exception:
                context = ""

        if self._llm is None:
            output = self._local_execute(skill, cleaned_input, context)
        else:
            output = self._llm_execute(skill, cleaned_input, context)

        return SkillResult(
            skill_id=skill.id,
            skill_name=skill.name,
            input_text=cleaned_input,
            output=output,
            context_used=bool(context),
        )

    def _local_execute(self, skill: SkillDefinition, input_text: str, context: str) -> str:
        lines = [f"[{skill.name}] 基于输入内容的本地分析：", ""]
        if context:
            lines.append("已从知识库检索到相关参考资料：")
            lines.append(context[:500])
            lines.append("")
        lines.append(f"输入内容摘要：{input_text[:300]}")
        lines.append("")
        lines.append("这一步使用本地模式；配置 DeepSeek API Key 后，将使用 LLM 生成更高质量的回答。")
        return "\n".join(lines)

    def _llm_execute(self, skill: SkillDefinition, input_text: str, context: str) -> str:
        user_content = input_text
        if context:
            user_content = f"参考资料：\n{context}\n\n用户输入：\n{input_text}"
        messages = [
            Message(role=MessageRole.SYSTEM, content=skill.system_prompt),
            Message(role=MessageRole.USER, content=user_content),
        ]
        options = ChatOptions(temperature=0.7, max_tokens=2048)
        response = self._llm.generate(messages, options)
        return response.content
