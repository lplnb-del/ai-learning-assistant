export interface KnowledgeBasePayload {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export interface KnowledgeBaseCreatePayload {
  name: string
  description: string
}

export interface SourceDocumentPayload {
  id: string
  knowledge_base_id: string
  name: string
  source_uri: string
  content_type: string
  status: string
  error_message: string | null
  created_at: string
}

export interface ChunkPayload {
  id: string
  knowledge_base_id: string
  source_document_id: string
  index: number
  title: string | null
  text: string
  metadata: Record<string, string>
}

export interface TextDocumentImportPayload {
  name: string
  content: string
  source_uri: string
  content_type: string
  chunk_size: number
  chunk_overlap: number
}

export interface UrlDocumentImportPayload {
  url: string
  name: string
  chunk_size: number
  chunk_overlap: number
}

export interface PdfDocumentImportPayload {
  name: string
  content_base64: string
  chunk_size: number
  chunk_overlap: number
}

export interface TextDocumentImportResult {
  document: SourceDocumentPayload
  chunks: ChunkPayload[]
  chunk_count: number
}

export interface KnowledgeIndexBuildPayload {
  knowledge_base_id: string
  document_count: number
  chunk_count: number
  status: string
  message: string
  created_at: string
}

interface ApiErrorPayload {
  message?: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function listKnowledgeBases(): Promise<KnowledgeBasePayload[]> {
  return requestJson('/api/knowledge/bases')
}

export async function createKnowledgeBase(payload: KnowledgeBaseCreatePayload): Promise<KnowledgeBasePayload> {
  return requestJson('/api/knowledge/bases', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteKnowledgeBase(knowledgeBaseId: string): Promise<void> {
  await requestEmpty(`/api/knowledge/bases/${knowledgeBaseId}`, { method: 'DELETE' })
}

export async function listKnowledgeDocuments(knowledgeBaseId: string): Promise<SourceDocumentPayload[]> {
  return requestJson(`/api/knowledge/bases/${knowledgeBaseId}/documents`)
}

export async function importTextDocument(
  knowledgeBaseId: string,
  payload: TextDocumentImportPayload,
): Promise<TextDocumentImportResult> {
  return requestJson(`/api/knowledge/bases/${knowledgeBaseId}/documents/import-text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function importUrlDocument(
  knowledgeBaseId: string,
  payload: UrlDocumentImportPayload,
): Promise<TextDocumentImportResult> {
  return requestJson(`/api/knowledge/bases/${knowledgeBaseId}/documents/import-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function importPdfDocument(
  knowledgeBaseId: string,
  payload: PdfDocumentImportPayload,
): Promise<TextDocumentImportResult> {
  return requestJson(`/api/knowledge/bases/${knowledgeBaseId}/documents/import-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function listDocumentChunks(documentId: string): Promise<ChunkPayload[]> {
  return requestJson(`/api/knowledge/documents/${documentId}/chunks`)
}

export async function deleteKnowledgeDocument(documentId: string): Promise<void> {
  await requestEmpty(`/api/knowledge/documents/${documentId}`, { method: 'DELETE' })
}

export async function rebuildKnowledgeIndex(knowledgeBaseId: string): Promise<KnowledgeIndexBuildPayload> {
  return requestJson(`/api/knowledge/bases/${knowledgeBaseId}/index/rebuild`, {
    method: 'POST',
  })
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
  return response.json() as Promise<T>
}

async function requestEmpty(path: string, init?: RequestInit): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(await readApiError(response))
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
