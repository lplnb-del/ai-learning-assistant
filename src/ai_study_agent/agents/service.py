"""Agent skill execution service."""

from __future__ import annotations

from dataclasses import dataclass

from ai_study_agent.agent_capabilities.registry import CapabilityRegistry, SkillDefinition
from ai_study_agent.agent_capabilities.subagents import SubAgentRole
from ai_study_agent.core.config import AppConfig
from ai_study_agent.core.domain import Message, MessageRole
from ai_study_agent.llm.deepseek import ChatOptions, DeepSeekGateway
from ai_study_agent.llm.model_factory import OPENAI_COMPATIBLE_PRESETS, ProviderConfig, create_chat_model
from ai_study_agent.rag.service import RagService
from ai_study_agent.settings.service import SettingsConsoleService


class AgentServiceError(ValueError):
    """Raised when an agent request cannot be fulfilled."""


@dataclass(frozen=True)
class SkillResult:
    skill_id: str
    skill_name: str
    input_text: str
    output: str
    context_used: bool


@dataclass(frozen=True)
class AgentResponseResult:
    role_id: str
    role_name: str
    input_text: str
    output: str
    context_used: bool


class AgentService:
    def __init__(
        self,
        registry: CapabilityRegistry,
        llm: DeepSeekGateway | None = None,
        rag: RagService | None = None,
        settings: SettingsConsoleService | None = None,
        config: AppConfig | None = None,
    ) -> None:
        self._registry = registry
        self._llm = llm
        self._rag = rag
        self._settings = settings
        self._config = config

    @classmethod
    def from_config(cls, config: AppConfig) -> "AgentService":
        from ai_study_agent.storage.sqlite import connect, initialize_database
        from ai_study_agent.knowledge.repository import KnowledgeRepository
        from ai_study_agent.cards.repository import CardRepository
        from ai_study_agent.rag.service import RagService
        from ai_study_agent.storage.vector_index import LocalVectorIndex

        registry = CapabilityRegistry()
        llm = DeepSeekGateway(config) if config.has_llm_key else None
        settings = SettingsConsoleService(config)
        rag = None
        try:
            connection = connect(config.db_path)
            initialize_database(connection)
            rag = RagService(KnowledgeRepository(connection), CardRepository(connection), LocalVectorIndex(config.chroma_dir))
        except Exception:
            pass
        return cls(registry, llm, rag, settings=settings, config=config)

    def list_roles(self) -> list[SubAgentRole]:
        return self._settings.list_subagents() if self._settings else []

    def get_role(self, role_id: str) -> SubAgentRole | None:
        return self._settings.get_subagent(role_id) if self._settings else None

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
        role_id: str | None = None,
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
            output = self._llm_execute(skill, cleaned_input, context, role_id)

        return SkillResult(
            skill_id=skill.id,
            skill_name=skill.name,
            input_text=cleaned_input,
            output=output,
            context_used=bool(context),
        )

    def respond(
        self,
        *,
        input_text: str,
        knowledge_base_id: str | None = None,
        top_k: int = 3,
        role_id: str | None = None,
    ) -> AgentResponseResult:
        cleaned_input = input_text.strip()
        if not cleaned_input:
            raise AgentServiceError("输入内容不能为空")

        role = self.get_role(role_id or "general_assistant") or self.list_roles()[0]
        context = self._build_context(cleaned_input, knowledge_base_id, top_k)

        if self._config is None:
            output = self._local_role_execute(role, cleaned_input, context)
        else:
            output = self._role_execute(role, cleaned_input, context)

        return AgentResponseResult(
            role_id=role.id,
            role_name=role.name,
            input_text=cleaned_input,
            output=output,
            context_used=bool(context),
        )

    def _build_context(self, input_text: str, knowledge_base_id: str | None, top_k: int) -> str:
        context = ""
        if knowledge_base_id and self._rag:
            try:
                rag_answer = self._rag.answer_question(
                    knowledge_base_ids=[knowledge_base_id],
                    question=input_text[:200],
                    top_k=top_k,
                )
                if rag_answer.sources:
                    context_parts = []
                    for source in rag_answer.sources[:3]:
                        context_parts.append(f"[{source.document_name}] {source.excerpt}")
                    context = "\n\n".join(context_parts)
            except Exception:
                context = ""
        return context

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

    def _local_role_execute(self, role: SubAgentRole, input_text: str, context: str) -> str:
        lines = [f"[{role.name}] 基于当前角色设定的本地分析：", ""]
        if context:
            lines.append("已从知识库检索到相关参考资料：")
            lines.append(context[:500])
            lines.append("")
        lines.append(f"角色使命：{role.description}")
        lines.append(f"用户输入：{input_text[:300]}")
        lines.append("")
        lines.append("当前处于本地降级模式；配置可用模型后，将按角色系统提示词生成更完整的回答。")
        return "\n".join(lines)

    def _llm_execute(self, skill: SkillDefinition, input_text: str, context: str, role_id: str | None = None) -> str:
        user_content = input_text
        if context:
            user_content = f"参考资料：\n{context}\n\n用户输入：\n{input_text}"

        system_prompt = skill.system_prompt
        if role_id:
            role = self.get_role(role_id)
            if role:
                system_prompt = f"{role.system_prompt}\n\n当前使用的工具：{skill.name}\n{skill.system_prompt}"

        messages = [
            Message(role=MessageRole.SYSTEM, content=system_prompt),
            Message(role=MessageRole.USER, content=user_content),
        ]
        options = ChatOptions(temperature=0.7, max_tokens=2048)
        response = self._llm.generate(messages, options)
        return response.content

    def _role_execute(self, role: SubAgentRole, input_text: str, context: str) -> str:
        runtime_config = self._settings.get_chat_config() if self._settings else None

        if runtime_config:
            try:
                base_url = runtime_config.base_url
                if not base_url and runtime_config.preset and runtime_config.preset in OPENAI_COMPATIBLE_PRESETS:
                    base_url = OPENAI_COMPATIBLE_PRESETS[runtime_config.preset]["base_url"]
                provider_config = ProviderConfig(
                    provider=runtime_config.provider,
                    api_key=runtime_config.api_key,
                    base_url=base_url,
                    model=runtime_config.model,
                )
                chat_model = create_chat_model(provider_config)
                user_content = input_text if not context else f"参考资料：\n{context}\n\n用户输入：\n{input_text}"
                response = chat_model.invoke(
                    [
                        ("system", role.system_prompt),
                        ("human", user_content),
                    ]
                )
                content = getattr(response, "content", "")
                if isinstance(content, str) and content.strip():
                    return content
            except Exception:
                pass

        if self._llm is not None:
            messages = [
                Message(role=MessageRole.SYSTEM, content=role.system_prompt),
                Message(
                    role=MessageRole.USER,
                    content=input_text if not context else f"参考资料：\n{context}\n\n用户输入：\n{input_text}",
                ),
            ]
            response = self._llm.generate(messages, ChatOptions(temperature=0.7, max_tokens=2048))
            return response.content

        return self._local_role_execute(role, input_text, context)
