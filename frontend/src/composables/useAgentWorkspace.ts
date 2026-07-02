import { computed, onMounted, ref, shallowRef } from 'vue'
import {
  listAgentCapabilities,
  runAgentSkill,
  type AgentCapabilityPayload,
} from '../api/agents'
import { listKnowledgeBases, type KnowledgeBasePayload } from '../api/knowledge'

export interface AgentMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  skillId?: string
  skillName?: string
  contextUsed?: boolean
}

export function useAgentWorkspace() {
  const capabilities = ref<AgentCapabilityPayload[]>([])
  const knowledgeBases = ref<KnowledgeBasePayload[]>([])
  const messages = ref<AgentMessage[]>([])
  const selectedSkillId = shallowRef('')
  const selectedKnowledgeBaseId = shallowRef('')
  const input = shallowRef('')
  const isRunning = shallowRef(false)
  const errorMessage = shallowRef('')

  const selectedSkill = computed(
    () => capabilities.value.find((cap) => cap.id === selectedSkillId.value) ?? null,
  )
  const canSubmit = computed(
    () => input.value.trim().length > 0 && Boolean(selectedSkillId.value) && !isRunning.value,
  )

  onMounted(() => {
    void initialize()
  })

  async function initialize() {
    try {
      const [caps, bases] = await Promise.all([listAgentCapabilities(), listKnowledgeBases()])
      capabilities.value = caps
      knowledgeBases.value = bases
      if (!selectedSkillId.value && caps.length) {
        selectedSkillId.value = caps[0].id
      }
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '加载能力列表失败'
    }
  }

  async function submit() {
    const question = input.value.trim()
    if (!canSubmit.value || !question) return

    errorMessage.value = ''
    input.value = ''
    isRunning.value = true

    const userMessage: AgentMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
    }
    messages.value = [...messages.value, userMessage]

    try {
      const result = await runAgentSkill(selectedSkillId.value, {
        input_text: question,
        knowledge_base_id: selectedKnowledgeBaseId.value || undefined,
        top_k: 3,
      })
      const assistantMessage: AgentMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.output,
        skillId: result.skill_id,
        skillName: result.skill_name,
        contextUsed: result.context_used,
      }
      messages.value = [...messages.value, assistantMessage]
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '执行失败'
    } finally {
      isRunning.value = false
    }
  }

  return {
    capabilities,
    knowledgeBases,
    messages,
    selectedSkillId,
    selectedKnowledgeBaseId,
    selectedSkill,
    input,
    isRunning,
    errorMessage,
    canSubmit,
    initialize,
    submit,
  }
}
