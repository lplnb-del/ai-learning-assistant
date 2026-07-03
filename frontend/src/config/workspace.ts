import {
  BookMarked,
  BookOpenCheck,
  BrainCog,
  Library,
  MessageCircleQuestion,
  Workflow,
} from '@lucide/vue'
import type { ModeTab, NavItem } from '../types/workspace'

export const navItems: NavItem[] = [
  { id: 'workspace', label: 'AI 推理台', icon: Library, group: 'workspace' },
  { id: 'knowledge', label: '知识库管理', icon: BookMarked, group: 'resources' },
  { id: 'cards', label: 'QA 记忆卡片', icon: BrainCog, group: 'resources' },
]

export const modeTabs: ModeTab[] = [
  { id: 'chat', label: 'Chat', icon: MessageCircleQuestion },
  { id: 'rag', label: 'RAG', icon: BookOpenCheck },
  { id: 'agent', label: 'Agent', icon: Workflow },
]
