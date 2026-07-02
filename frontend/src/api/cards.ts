export type MasteryLevel = 'new' | 'unsure' | 'mastered'

export interface QALibraryPayload {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export interface QALibraryCreatePayload {
  name: string
  description: string
}

export interface QACardPayload {
  id: string
  qa_library_id: string | null
  knowledge_base_id: string | null
  question: string
  answer: string
  source_chunk_ids: readonly string[]
  tags: readonly string[]
  mastery: MasteryLevel
  created_at: string
  updated_at: string
}

export interface QACardCreatePayload {
  qa_library_id?: string | null
  question: string
  answer: string
  knowledge_base_id?: string | null
  source_chunk_ids?: string[]
  tags?: string[]
}

interface ApiErrorPayload {
  message?: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function listQaLibraries(): Promise<QALibraryPayload[]> {
  return requestJson('/api/cards/libraries')
}

export async function createQaLibrary(payload: QALibraryCreatePayload): Promise<QALibraryPayload> {
  return requestJson('/api/cards/libraries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteQaLibrary(libraryId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/cards/libraries/${libraryId}`, { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
}

export async function listQaCards(params: {
  qaLibraryId?: string
  knowledgeBaseId?: string
  mastery?: MasteryLevel | ''
  tag?: string
} = {}): Promise<QACardPayload[]> {
  const search = new URLSearchParams()
  if (params.qaLibraryId) {
    search.set('qa_library_id', params.qaLibraryId)
  }
  if (params.knowledgeBaseId) {
    search.set('knowledge_base_id', params.knowledgeBaseId)
  }
  if (params.mastery) {
    search.set('mastery', params.mastery)
  }
  if (params.tag?.trim()) {
    search.set('tag', params.tag.trim())
  }
  const suffix = search.toString() ? `?${search.toString()}` : ''
  return requestJson(`/api/cards${suffix}`)
}

export async function createQaCard(payload: QACardCreatePayload): Promise<QACardPayload> {
  return requestJson('/api/cards', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateQaCardMastery(cardId: string, mastery: MasteryLevel): Promise<QACardPayload> {
  return requestJson(`/api/cards/${cardId}/mastery`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mastery }),
  })
}

export async function deleteQaCard(cardId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/cards/${cardId}`, { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
  return response.json() as Promise<T>
}

async function readApiError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload
    return payload.message || `请求失败：HTTP ${response.status}`
  } catch {
    return `请求失败：HTTP ${response.status}`
  }
}

export interface CardGenerateFromChunksPayload {
  qa_library_id: string
  chunk_ids: string[]
  knowledge_base_id?: string | null
  tags?: string[]
}

export interface CardGenerateFromDocumentPayload {
  qa_library_id: string
  document_id: string
  tags?: string[]
}

export interface CardGenerateResponsePayload {
  generated_count: number
  cards: QACardPayload[]
}

export async function generateCardsFromChunks(payload: CardGenerateFromChunksPayload): Promise<CardGenerateResponsePayload> {
  return requestJson('/api/cards/generate-from-chunks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function generateCardsFromDocument(payload: CardGenerateFromDocumentPayload): Promise<CardGenerateResponsePayload> {
  return requestJson('/api/cards/generate-from-document', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
