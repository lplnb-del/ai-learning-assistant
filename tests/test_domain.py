from ai_study_agent.core.domain import CapabilityKind, MasteryLevel, Mode, QACard


def test_modes_keep_product_boundaries():
    assert {mode.value for mode in Mode} == {"chat", "rag", "agent"}


def test_capability_kinds_are_agent_only_building_blocks():
    assert {kind.value for kind in CapabilityKind} == {"skill", "mcp_tool", "sub_agent"}


def test_qa_card_defaults_to_new_mastery():
    card = QACard(
        id="card-1",
        knowledge_base_id="kb-1",
        question="什么是 RAG？",
        answer="检索增强生成。",
    )

    assert card.mastery == MasteryLevel.NEW
    assert card.source_chunk_ids == []
    assert card.tags == []
