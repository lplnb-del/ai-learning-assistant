import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import { listSubAgentRoles, runAgentConversation, type SubAgentRolePayload } from '../api/agents'
import { listKnowledgeBases, type KnowledgeBasePayload } from '../api/knowledge'
import { useConversationStore } from '../stores/conversations'
import type { AgentConversationState, AgentMessage } from '../types/conversations'

function createEmptyConversationState(selectedRoleId = 'general_assistant'): AgentConversationState {
  return {
    messages: [],
    selectedSkillId: '',
    selectedKnowledgeBaseId: '',
    selectedRoleId,
  }
}

function buildSessionTitle(messages: AgentMessage[]) {
  const assistantSummary = messages.find((message) => message.role === 'assistant' && message.content.trim())
  if (assistantSummary) {
    return normalizeSessionLabel(assistantSummary.content, '新建 Agent 对话')
  }

  const firstUserMessage = messages.find((message) => message.role === 'user' && message.content.trim())
  return firstUserMessage ? normalizeSessionLabel(firstUserMessage.content, '新建 Agent 对话') : '新建 Agent 对话'
}

function buildSessionPreview(messages: AgentMessage[]) {
  const lastMessage = [...messages].reverse().find((message) => message.content.trim())
  return lastMessage ? lastMessage.content.trim().slice(0, 40) : ''
}

export function useAgentWorkspace() {
  const conversationStore = useConversationStore()
  const roles = ref<SubAgentRolePayload[]>([])
  const selectedRoleId = shallowRef('general_assistant')
  const knowledgeBases = ref<KnowledgeBasePayload[]>([])
  const messages = ref<AgentMessage[]>([])
  const selectedKnowledgeBaseId = shallowRef('')
  const input = shallowRef('')
  const isRunning = shallowRef(false)
  const errorMessage = shallowRef('')
  const activeSessionId = computed(() => conversationStore.activeIds.agent)

  const selectedRole = computed(() => roles.value.find((role) => role.id === selectedRoleId.value) ?? null)
  const canSubmit = computed(() => input.value.trim().length > 0 && Boolean(selectedRoleId.value) && !isRunning.value)

  onMounted(() => {
    void initialize()
  })

  function hydrateFromSession(defaultRoleId = 'general_assistant') {
    const ensuredId = conversationStore.ensureSession('agent', {
      mode: 'agent',
      state: createEmptyConversationState(defaultRoleId),
    })
    const session = conversationStore.getSession(ensuredId)
    if (!session || session.payload.mode !== 'agent') {
      return
    }

    messages.value = [...session.payload.state.messages]
    selectedRoleId.value = session.payload.state.selectedRoleId || defaultRoleId
    selectedKnowledgeBaseId.value = session.payload.state.selectedKnowledgeBaseId
    input.value = ''
    errorMessage.value = ''
  }

  async function initialize() {
    try {
      const [bases, roleList] = await Promise.all([listKnowledgeBases(), listSubAgentRoles()])
      roles.value = roleList
      knowledgeBases.value = bases
      hydrateFromSession(roleList[0]?.id ?? 'general_assistant')
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '加载 Agent 角色失败'
    }
  }

  watch(activeSessionId, () => {
    if (roles.value.length) {
      hydrateFromSession(roles.value[0]?.id ?? 'general_assistant')
    }
  })

  watch(
    [messages, selectedKnowledgeBaseId, selectedRoleId],
    () => {
      const sessionId = activeSessionId.value
      if (!sessionId) {
        return
      }
      const currentSession = conversationStore.getSession(sessionId)

      conversationStore.updateSession(sessionId, {
        title: currentSession?.titleManuallyEdited ? undefined : buildSessionTitle(messages.value),
        preview: buildSessionPreview(messages.value),
        payload: {
          mode: 'agent',
          state: {
            messages: [...messages.value],
            selectedSkillId: '',
            selectedKnowledgeBaseId: selectedKnowledgeBaseId.value,
            selectedRoleId: selectedRoleId.value,
          },
        },
      })
    },
    { deep: true },
  )

  async function submit() {
    const question = input.value.trim()
    if (!canSubmit.value || !question) {
      return
    }

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
      const result = await runAgentConversation({
        input_text: question,
        knowledge_base_id: selectedKnowledgeBaseId.value || undefined,
        role_id: selectedRoleId.value || undefined,
        top_k: 3,
      })

      const assistantMessage: AgentMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.output,
        skillName: result.role_name,
        contextUsed: result.context_used,
      }
      messages.value = [...messages.value, assistantMessage]
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '执行失败'
    } finally {
      isRunning.value = false
    }
  }

  function startNewConversation() {
    conversationStore.createSession('agent', {
      mode: 'agent',
      state: createEmptyConversationState(selectedRoleId.value || roles.value[0]?.id || 'general_assistant'),
    })
  }

  return {
    roles,
    selectedRoleId,
    selectedRole,
    knowledgeBases,
    messages,
    selectedKnowledgeBaseId,
    input,
    isRunning,
    errorMessage,
    canSubmit,
    initialize,
    startNewConversation,
    submit,
  }
}

function normalizeSessionLabel(content: string, fallback: string) {
  const normalized = content.replace(/[#>*`_-]/g, ' ').replace(/\s+/g, ' ').trim()
  return normalized ? normalized.slice(0, 24) : fallback
}
