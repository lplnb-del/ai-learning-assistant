<script setup lang="ts">
import SidebarNav from './SidebarNav.vue'
import type { ConversationSession } from '../../types/conversations'
import type { MainView, NavItem, WorkMode } from '../../types/workspace'

interface Props {
  items: NavItem[]
  activeView: MainView
  activeMode: WorkMode
  activeConversationId: string
  conversations: readonly ConversationSession[]
  resolvedTheme: 'light' | 'dark'
}

defineProps<Props>()

const emit = defineEmits<{
  selectView: [view: MainView]
  openSettings: []
  openHistory: []
  createConversation: []
  selectConversation: [sessionId: string]
  togglePinnedConversation: [sessionId: string]
  deleteConversation: [sessionId: string]
  requestRenameConversation: [session: ConversationSession]
  toggleTheme: []
}>()
</script>

<template>
  <div class="app-shell">
    <SidebarNav
      :items="items"
      :active-view="activeView"
      :active-mode="activeMode"
      :active-conversation-id="activeConversationId"
      :conversations="conversations"
      :resolved-theme="resolvedTheme"
      @select-view="emit('selectView', $event)"
      @open-settings="emit('openSettings')"
      @open-history="emit('openHistory')"
      @create-conversation="emit('createConversation')"
      @select-conversation="emit('selectConversation', $event)"
      @toggle-pinned-conversation="emit('togglePinnedConversation', $event)"
      @delete-conversation="emit('deleteConversation', $event)"
      @request-rename-conversation="emit('requestRenameConversation', $event)"
      @toggle-theme="emit('toggleTheme')"
    />
    <main class="workspace-frame">
      <slot />
    </main>
  </div>
</template>
