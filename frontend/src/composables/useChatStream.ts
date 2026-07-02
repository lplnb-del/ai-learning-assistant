import { computed, readonly, ref, shallowRef } from 'vue'
import { streamChatCompletion, type ChatMessagePayload, type ThinkingDepth } from '../api/chat'

export interface ChatViewMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  status?: string
}

const initialMessages: ChatViewMessage[] = [
  {
    id: 'sample-user',
    role: 'user',
    content: '能不能帮我解释一下什么是 RAG？尽量通俗一点，最好结合生活中的例子。',
  },
  {
    id: 'sample-assistant',
    role: 'assistant',
    status: '静态示例，可直接输入问题调用真实模型',
    content:
      'RAG（检索增强生成）是一种让 AI 回答前先翻资料的技术。普通 Chat 像闭卷考试，只能凭已有记忆作答；RAG 更像开卷考试，会先检索可信资料，再组织答案。',
  },
]

export function useChatStream() {
  const messages = ref<ChatViewMessage[]>([...initialMessages])
  const input = shallowRef('')
  const errorMessage = shallowRef('')
  const isStreaming = shallowRef(false)
  const temperature = shallowRef(0.7)
  const model = shallowRef('deepseek-v4-flash')
  const thinkingDepth = shallowRef<ThinkingDepth>('标准')
  const keepContext = shallowRef(true)
  const webSearch = shallowRef(true)

  const canSubmit = computed(() => input.value.trim().length > 0 && !isStreaming.value)
  const lastAssistantStatus = computed(() => {
    if (isStreaming.value) {
      return '正在连接 DeepSeek 流式输出...'
    }
    return findLastAssistantStatus(messages.value)
  })

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
    submit,
    setThinkingDepth,
    toggleWebSearch,
    toggleKeepContext,
  }
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
