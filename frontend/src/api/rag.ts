export interface RagQuestionPayload {
  knowledge_base_ids: string[]
  qa_library_ids: string[]
  question: string
  top_k: number
}

export interface RagSourcePayload {
  chunk_id: string
  source_type: string
  document_id: string
  document_name: string
  chunk_index: number
  title: string | null
  excerpt: string
  score: number
}

export interface RagAnswerPayload {
  answer: string
  sources: RagSourcePayload[]
  prompt_preview: string
  retrieval_mode: string
}

interface ApiErrorPayload {
  message?: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function askRagQuestion(payload: RagQuestionPayload): Promise<RagAnswerPayload> {
  const response = await fetch(`${API_BASE_URL}/api/rag/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await readApiError(response))
  }

  return response.json() as Promise<RagAnswerPayload>
}

async function readApiError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload
    return payload.message || `请求失败：HTTP ${response.status}`
  } catch {
    return `请求失败：HTTP ${response.status}`
  }
}
