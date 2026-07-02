export interface SubAgentRolePayload {
  id: string
  name: string
  title: string
  description: string
  greeting: string
  preferred_skills: string[]
  tags: string[]
}

export interface AgentCapabilityPayload {
  id: string
  name: string
  kind: string
  description: string
  enabled: boolean
}

export interface SkillRunPayload {
  input_text: string
  knowledge_base_id?: string | null
  top_k?: number
  role_id?: string | null
}

export interface SkillRunResultPayload {
  skill_id: string
  skill_name: string
  input_text: string
  output: string
  context_used: boolean
}

interface ApiErrorPayload {
  message?: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export async function listSubAgentRoles(): Promise<SubAgentRolePayload[]> {
  return requestJson('/api/agents/roles')
}

export async function listAgentCapabilities(): Promise<AgentCapabilityPayload[]> {
  return requestJson('/api/agents/capabilities')
}

export async function runAgentSkill(skillId: string, payload: SkillRunPayload): Promise<SkillRunResultPayload> {
  return requestJson(`/api/agents/skills/${skillId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
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
