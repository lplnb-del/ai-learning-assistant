export type ChatRole = 'user' | 'assistant' | 'system'
export type ThinkingDepth = '快速' | '标准' | '深度'

export interface ChatMessagePayload {
  role: ChatRole
  content: string
}

export interface ChatRequestPayload {
  messages: ChatMessagePayload[]
  temperature: number
  thinking_depth: ThinkingDepth
  model?: string
  keep_context: boolean
  web_search: boolean
}

export interface ChatResponsePayload {
  role: 'assistant'
  content: string
  model: string
}

export interface ApiErrorPayload {
  code: string
  message: string
  details?: Record<string, string>
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function createChatCompletion(payload: ChatRequestPayload): Promise<ChatResponsePayload> {
  const response = await fetch(`${API_BASE_URL}/api/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await readApiError(response))
  }

  return response.json() as Promise<ChatResponsePayload>
}

export async function streamChatCompletion(
  payload: ChatRequestPayload,
  handlers: {
    onToken: (token: string) => void
    onError: (message: string) => void
    onDone: () => void
  },
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok || !response.body) {
    throw new Error(await readApiError(response))
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        break
      }
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() ?? ''
      for (const event of events) {
        handleSseEvent(event, handlers)
      }
    }
    if (buffer.trim()) {
      handleSseEvent(buffer, handlers)
    }
  } finally {
    reader.releaseLock()
  }
}

async function readApiError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload
    return payload.message || `请求失败：HTTP ${response.status}`
  } catch {
    return `请求失败：HTTP ${response.status}`
  }
}

function handleSseEvent(
  rawEvent: string,
  handlers: {
    onToken: (token: string) => void
    onError: (message: string) => void
    onDone: () => void
  },
) {
  const eventType = rawEvent
    .split('\n')
    .find((line) => line.startsWith('event:'))
    ?.replace('event:', '')
    .trim()
  const data = rawEvent
    .split('\n')
    .find((line) => line.startsWith('data:'))
    ?.replace('data:', '')
    .trim()

  if (!eventType || !data) {
    return
  }

  const payload = JSON.parse(data) as { content?: string; message?: string }
  if (eventType === 'message' && payload.content) {
    handlers.onToken(payload.content)
  }
  if (eventType === 'error') {
    handlers.onError(payload.message || '模型服务暂时不可用')
  }
  if (eventType === 'done') {
    handlers.onDone()
  }
}
