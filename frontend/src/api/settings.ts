export interface ModelProviderConfig {
  provider: string
  preset?: string
  api_key?: string
  base_url?: string
  model?: string
}

export interface SettingsResponse {
  chat_provider: string
  chat_preset: string | null
  chat_model: string | null
  chat_base_url: string | null
  embedding_provider: string
  embedding_preset: string | null
  embedding_model: string | null
  embedding_base_url: string | null
}

export interface DetectedModel {
  id: string
  name: string
}

export interface ModelDetectionResponse {
  provider: string
  models: DetectedModel[]
  success: boolean
  message: string
}

export interface PresetInfo {
  key: string
  name: string
  base_url: string
  default_chat_model: string
  default_embedding_model: string
}

export interface PresetsResponse {
  presets: PresetInfo[]
}

export interface SubAgentRoleConfig {
  id: string
  name: string
  title: string
  description: string
  system_prompt: string
  greeting: string
  preferred_skills: string[]
  tags: string[]
}

export interface SubAgentRoleUpsertRequest {
  id?: string
  name: string
  title: string
  description: string
  system_prompt: string
  greeting: string
  preferred_skills: string[]
  tags: string[]
}

export interface SubAgentPromptGenerateResponse {
  system_prompt: string
  greeting: string
}

export interface McpServerConfig {
  id: string
  name: string
  description: string
  command: string
  enabled: boolean
}

export interface McpServerUpsertRequest {
  id?: string
  name: string
  description: string
  command: string
  enabled: boolean
}

export interface SkillConfigResponse {
  id: string
  name: string
  description: string
  enabled: boolean
  tags: string[]
  source: string
}

export interface SkillConfigUpsertRequest {
  id?: string
  name: string
  description: string
  enabled: boolean
  tags: string[]
  source: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function getSettings(): Promise<SettingsResponse> {
  return requestJson('/api/settings')
}

export async function updateChatModel(config: ModelProviderConfig): Promise<SettingsResponse> {
  return requestJson('/api/settings/chat-model', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
}

export async function updateEmbeddingModel(config: ModelProviderConfig): Promise<SettingsResponse> {
  return requestJson('/api/settings/embedding-model', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
}

export async function detectModels(
  provider: string,
  apiKey?: string,
  baseUrl?: string,
  preset?: string,
): Promise<ModelDetectionResponse> {
  return requestJson('/api/settings/detect-models', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key: apiKey, base_url: baseUrl, preset }),
  })
}

export async function getPresets(): Promise<PresetsResponse> {
  return requestJson('/api/settings/presets')
}

export async function listSubagents(): Promise<SubAgentRoleConfig[]> {
  return requestJson('/api/settings/subagents')
}

export async function saveSubagent(payload: SubAgentRoleUpsertRequest): Promise<SubAgentRoleConfig> {
  return requestJson('/api/settings/subagents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteSubagent(roleId: string): Promise<void> {
  await requestJson(`/api/settings/subagents/${roleId}`, { method: 'DELETE' })
}

export async function generateSubagentPrompt(roleName: string, mission: string): Promise<SubAgentPromptGenerateResponse> {
  return requestJson('/api/settings/subagents/generate-prompt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role_name: roleName, mission }),
  })
}

export async function listMcpServers(): Promise<McpServerConfig[]> {
  return requestJson('/api/settings/mcp-servers')
}

export async function saveMcpServer(payload: McpServerUpsertRequest): Promise<McpServerConfig> {
  return requestJson('/api/settings/mcp-servers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteMcpServer(serverId: string): Promise<void> {
  await requestJson(`/api/settings/mcp-servers/${serverId}`, { method: 'DELETE' })
}

export async function listSkillSettings(): Promise<SkillConfigResponse[]> {
  return requestJson('/api/settings/skills')
}

export async function saveSkillSetting(payload: SkillConfigUpsertRequest): Promise<SkillConfigResponse> {
  return requestJson('/api/settings/skills', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateSkillSetting(skillId: string, enabled: boolean): Promise<SkillConfigResponse> {
  return requestJson(`/api/settings/skills/${skillId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  })
}

export async function deleteSkillSetting(skillId: string): Promise<void> {
  await requestJson(`/api/settings/skills/${skillId}`, { method: 'DELETE' })
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
    const payload = (await response.json()) as { message?: string }
    return payload.message || `请求失败：HTTP ${response.status}`
  } catch {
    return `请求失败：HTTP ${response.status}`
  }
}
