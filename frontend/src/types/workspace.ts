import type { Component } from 'vue'

export type MainView = 'workspace' | 'knowledge' | 'cards' | 'history'
export type WorkMode = 'chat' | 'rag' | 'agent'

export interface NavItem {
  id: MainView
  label: string
  icon: Component
  group: 'workspace' | 'resources'
}

export interface ModeTab {
  id: WorkMode
  label: string
  icon: Component
}

export interface MessageBlock {
  role: 'user' | 'assistant'
  title?: string
  content: string[]
  status?: string
}

export interface SourceSnippet {
  id: string
  title: string
  source: string
  score?: string
  excerpt: string
  marker?: string
}

export interface AgentStep {
  id: string
  title: string
  detail: string
  status: 'completed' | 'running'
  icon: Component
  tone: 'purple' | 'blue' | 'red'
}

export interface KnowledgeDocument {
  id: string
  name: string
  meta: string
  status: string
  statusTone: 'success' | 'info'
}

export interface FlashCard {
  tag: string
  question: string
  answer: string[]
}
