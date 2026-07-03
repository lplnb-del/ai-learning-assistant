import type { Component } from 'vue'

export type MainView = 'workspace' | 'knowledge' | 'cards'
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
