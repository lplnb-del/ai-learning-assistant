import type { ThinkingDepth } from '../api/chat'
import type { RagSourcePayload } from '../api/rag'
import type { WorkMode } from './workspace'

export interface ChatViewMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  status?: string
}

export interface RagViewMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  status?: string
  sources?: readonly RagSourcePayload[]
  promptPreview?: string
  question?: string
  knowledgeBaseIds?: string[]
  savedCardId?: string
}

export interface AgentMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  skillId?: string
  skillName?: string
  contextUsed?: boolean
}

export interface ChatConversationState {
  messages: ChatViewMessage[]
  model: string
  thinkingDepth: ThinkingDepth
  temperature: number
  keepContext: boolean
  webSearch: boolean
}

export interface RagConversationState {
  messages: RagViewMessage[]
  selectedKnowledgeBaseIds: string[]
  selectedQaLibraryIds: string[]
  topK: number
}

export interface AgentConversationState {
  messages: AgentMessage[]
  selectedSkillId: string
  selectedKnowledgeBaseId: string
  selectedRoleId: string
}

export type ConversationPayload =
  | { mode: 'chat'; state: ChatConversationState }
  | { mode: 'rag'; state: RagConversationState }
  | { mode: 'agent'; state: AgentConversationState }

export interface ConversationSession {
  id: string
  mode: WorkMode
  title: string
  preview: string
  titleManuallyEdited?: boolean
  pinned: boolean
  updatedAt: string
  payload: ConversationPayload
}
