export interface ModelProviderConfig {
  provider: string
  api_key?: string
  base_url?: string
  model?: string
}

export interface SettingsResponse {
  chat_provider: string
  chat_model: string | null
  chat_base_url: string | null
  embedding_provider: string
  embedding_model: string | null
  embedding_base_url: string | null
}

export interface DetectedModel {
  id: string
  name: string
  provider: string
}

export interface ModelDetectionResponse {
  provider: string
  models: DetectedModel[]
  success: boolean
  message: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function getSettings(): Promise<SettingsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/settings`)
  if (!res.ok) throw new Error(`Failed to load settings: ${res.status}`)
  return res.json()
}

export async function updateChatModel(config: ModelProviderConfig): Promise<SettingsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/settings/chat-model`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!res.ok) throw new Error(`Failed to update chat model: ${res.status}`)
  return res.json()
}

export async function updateEmbeddingModel(config: ModelProviderConfig): Promise<SettingsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/settings/embedding-model`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!res.ok) throw new Error(`Failed to update embedding model: ${res.status}`)
  return res.json()
}

export async function detectModels(provider: string, apiKey?: string, baseUrl?: string): Promise<ModelDetectionResponse> {
  const res = await fetch(`${API_BASE_URL}/api/settings/detect-models`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key: apiKey, base_url: baseUrl }),
  })
  if (!res.ok) throw new Error(`Detection failed: ${res.status}`)
  return res.json()
}
