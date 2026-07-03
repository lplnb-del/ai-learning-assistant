import { computed, readonly, ref, shallowRef, watch } from 'vue'
import { streamChatCompletion, type ChatMessagePayload, type ThinkingDepth } from '../api/chat'
import { useConversationStore } from '../stores/conversations'
import { useModelSettingsStore } from '../stores/modelSettings'
import type { ChatConversationState, ChatViewMessage } from '../types/conversations'

function createEmptyConversationState(): ChatConversationState {
  return {
    messages: [],
    model: '',
    thinkingDepth: '标准',
    temperature: 0.7,
    keepContext: true,
    webSearch: true,
  }
}

function buildSessionTitle(messages: ChatViewMessage[]) {
  const assistantSummary = messages.find((message) => message.role === 'assistant' && message.content.trim())
  if (assistantSummary) {
    return normalizeSessionLabel(assistantSummary.content, '新建 Chat 对话')
  }

  const firstUserMessage = messages.find((message) => message.role === 'user' && message.content.trim())
  return firstUserMessage ? normalizeSessionLabel(firstUserMessage.content, '新建 Chat 对话') : '新建 Chat 对话'
}

function buildSessionPreview(messages: ChatViewMessage[]) {
  const lastMessage = [...messages].reverse().find((message) => message.content.trim())
  return lastMessage ? lastMessage.content.trim().slice(0, 40) : ''
}

export function useChatStream() {
  const conversationStore = useConversationStore()
  const modelSettingsStore = useModelSettingsStore()
  const messages = ref<ChatViewMessage[]>([])
  const input = shallowRef('')
  const errorMessage = shallowRef('')
  const isStreaming = shallowRef(false)
  const temperature = shallowRef(0.7)
  const model = shallowRef('deepseek-v4-flash')
  const thinkingDepth = shallowRef<ThinkingDepth>('标准')
  const keepContext = shallowRef(true)
  const webSearch = shallowRef(true)
  const activeSessionId = computed(() => conversationStore.activeIds.chat)
  const availableModels = computed(() => modelSettingsStore.chatModelOptions)

  const canSubmit = computed(() => input.value.trim().length > 0 && !isStreaming.value)
  const lastAssistantStatus = computed(() => {
    if (isStreaming.value) {
      return '正在连接模型流式输出...'
    }
    return findLastAssistantStatus(messages.value)
  })

  void modelSettingsStore.loadRemoteSettings()

  function hydrateFromSession() {
    const ensuredId = conversationStore.ensureSession('chat', {
      mode: 'chat',
      state: createEmptyConversationState(),
    })
    const session = conversationStore.getSession(ensuredId)
    if (!session || session.payload.mode !== 'chat') {
      return
    }

    messages.value = [...session.payload.state.messages]
    model.value = session.payload.state.model || modelSettingsStore.defaultChatModel
    thinkingDepth.value = session.payload.state.thinkingDepth
    temperature.value = session.payload.state.temperature
    keepContext.value = session.payload.state.keepContext
    webSearch.value = session.payload.state.webSearch
    input.value = ''
    errorMessage.value = ''
  }

  watch(activeSessionId, hydrateFromSession, { immediate: true })

  watch(
    [messages, model, thinkingDepth, temperature, keepContext, webSearch],
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
          mode: 'chat',
          state: {
            messages: [...messages.value],
            model: model.value,
            thinkingDepth: thinkingDepth.value,
            temperature: temperature.value,
            keepContext: keepContext.value,
            webSearch: webSearch.value,
          },
        },
      })
    },
    { deep: true },
  )

  watch(
    () => modelSettingsStore.defaultChatModel,
    (nextModel) => {
      if (!nextModel || model.value || messages.value.length > 0) {
        return
      }
      model.value = nextModel
    },
    { immediate: true },
  )

  async function submit() {
    const question = input.value.trim()
    if (!question || isStreaming.value) {
      return
    }

    errorMessage.value = ''
    input.value = ''
    isStreaming.value = true

    const userMessage: ChatViewMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
    }
    const assistantMessage: ChatViewMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      status: '正在生成回答',
    }
    messages.value = [...messages.value, userMessage, assistantMessage]

    try {
      await streamChatCompletion(
        {
          messages: buildPayloadMessages(messages.value),
          temperature: temperature.value,
          thinking_depth: thinkingDepth.value,
          model: model.value,
          keep_context: keepContext.value,
          web_search: webSearch.value,
        },
        {
          onToken(token) {
            assistantMessage.content += token
            messages.value = [...messages.value]
          },
          onError(message) {
            errorMessage.value = message
            assistantMessage.status = '生成失败'
            assistantMessage.content ||= message
            messages.value = [...messages.value]
          },
          onDone() {
            assistantMessage.status = '流式输出完成'
            messages.value = [...messages.value]
          },
        },
      )
    } catch (error) {
      const message = error instanceof Error ? error.message : '模型服务暂时不可用'
      errorMessage.value = message
      assistantMessage.status = '生成失败'
      assistantMessage.content ||= message
      messages.value = [...messages.value]
    } finally {
      isStreaming.value = false
    }
  }

  function setThinkingDepth(nextDepth: ThinkingDepth) {
    thinkingDepth.value = nextDepth
  }

  function toggleWebSearch() {
    webSearch.value = !webSearch.value
  }

  function toggleKeepContext() {
    keepContext.value = !keepContext.value
  }

  function startNewConversation() {
    conversationStore.createSession('chat', {
      mode: 'chat',
      state: createEmptyConversationState(),
    })
  }

  return {
    messages: readonly(messages),
    input,
    errorMessage,
    isStreaming,
    temperature,
    model,
    thinkingDepth,
    keepContext,
    webSearch,
    canSubmit,
    lastAssistantStatus,
    availableModels,
    submit,
    startNewConversation,
    setThinkingDepth,
    toggleWebSearch,
    toggleKeepContext,
  }
}

function normalizeSessionLabel(content: string, fallback: string) {
  const normalized = content
    .replace(/[#>*`_-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  return normalized ? normalized.slice(0, 24) : fallback
}

function buildPayloadMessages(messages: ChatViewMessage[]): ChatMessagePayload[] {
  return messages
    .filter((message) => message.content.trim())
    .map((message) => ({
      role: message.role,
      content: message.content,
    }))
}

function findLastAssistantStatus(messages: ChatViewMessage[]): string | undefined {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index]
    if (message.role === 'assistant') {
      return message.status
    }
  }
  return undefined
}
