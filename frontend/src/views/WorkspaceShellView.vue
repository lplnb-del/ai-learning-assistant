<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, shallowRef } from 'vue'
import CardsView from '../components/cards/CardsView.vue'
import ConversationOverlay from '../components/history/ConversationOverlay.vue'
import KnowledgeView from '../components/knowledge/KnowledgeView.vue'
import AppShell from '../components/shell/AppShell.vue'
import FloatingPanel from '../components/shell/FloatingPanel.vue'
import SettingsOverlay from '../components/settings/SettingsOverlay.vue'
import InspectorPanel from '../components/workspace/InspectorPanel.vue'
import WorkspacePanel from '../components/workspace/WorkspacePanel.vue'
import { navItems } from '../config/workspace'
import type { ConversationSession } from '../types/conversations'
import type { MainView, WorkMode } from '../types/workspace'
import { useThemeController } from '../composables/useThemeController'
import { useConversationStore } from '../stores/conversations'

const activeView = shallowRef<MainView>('workspace')
const activeMode = shallowRef<WorkMode>('chat')
const renameSessionId = shallowRef('')
const renameTitle = shallowRef('')
const isRenameModalOpen = shallowRef(false)
const { resolvedTheme, toggleTheme } = useThemeController()
const conversationStore = useConversationStore()
const { activeIds, historyOverlayMode, isHistoryOverlayOpen, isSettingsOverlayOpen } = storeToRefs(conversationStore)

const currentConversations = computed(() => conversationStore.sessionsForMode(activeMode.value))
const currentActiveConversationId = computed(() => activeIds.value[activeMode.value])
const overlayConversations = computed(() => conversationStore.sessionsForMode(historyOverlayMode.value))

function selectView(view: MainView) {
  activeView.value = view
}

function selectMode(mode: WorkMode) {
  activeMode.value = mode
}

function createConversation() {
  activeView.value = 'workspace'
  conversationStore.createBlankSession(activeMode.value)
}

function selectConversation(sessionId: string) {
  const session = conversationStore.getSession(sessionId)
  if (!session) {
    return
  }

  activeMode.value = session.mode
  activeView.value = 'workspace'
  conversationStore.setActiveSession(session.mode, sessionId)
  conversationStore.closeHistoryOverlay()
}

function togglePinnedConversation(sessionId: string) {
  conversationStore.togglePinned(sessionId)
}

function renameConversation(sessionId: string, title: string) {
  conversationStore.renameSession(sessionId, title)
}

function openRenameConversation(session: ConversationSession) {
  renameSessionId.value = session.id
  renameTitle.value = session.title
  isRenameModalOpen.value = true
}

function closeRenameConversation() {
  isRenameModalOpen.value = false
  renameSessionId.value = ''
  renameTitle.value = ''
}

function submitRenameConversation() {
  if (!renameSessionId.value) {
    return
  }
  renameConversation(renameSessionId.value, renameTitle.value)
  closeRenameConversation()
}

function deleteConversation(sessionId: string) {
  const session = conversationStore.getSession(sessionId)
  if (!session) {
    return
  }
  conversationStore.deleteSession(session.mode, sessionId)
}

function createConversationForMode(mode: WorkMode) {
  activeMode.value = mode
  createConversation()
}
</script>

<template>
  <AppShell
    :items="navItems"
    :active-view="activeView"
    :active-mode="activeMode"
    :active-conversation-id="currentActiveConversationId"
    :conversations="currentConversations"
    :resolved-theme="resolvedTheme"
    @select-view="selectView"
    @open-settings="conversationStore.openSettingsOverlay()"
    @open-history="conversationStore.openHistoryOverlay(activeMode)"
    @create-conversation="createConversation"
    @select-conversation="selectConversation"
    @toggle-pinned-conversation="togglePinnedConversation"
    @delete-conversation="deleteConversation"
    @request-rename-conversation="openRenameConversation"
    @toggle-theme="toggleTheme"
  >
    <template v-if="activeView === 'workspace'">
      <WorkspacePanel :active-mode="activeMode" @select-mode="selectMode" @create-conversation="createConversation" />
      <InspectorPanel :active-mode="activeMode" />
    </template>

    <KnowledgeView v-else-if="activeView === 'knowledge'" />
    <CardsView v-else />
  </AppShell>

  <ConversationOverlay
    v-if="isHistoryOverlayOpen"
    :mode="historyOverlayMode"
    :conversations="overlayConversations"
    :active-conversation-id="activeIds[historyOverlayMode]"
    @close="conversationStore.closeHistoryOverlay()"
    @create-conversation="createConversationForMode(historyOverlayMode)"
    @select-conversation="selectConversation"
    @toggle-pinned="togglePinnedConversation"
    @delete-conversation="deleteConversation"
    @request-rename-conversation="openRenameConversation"
  />

  <SettingsOverlay v-if="isSettingsOverlayOpen" @close="conversationStore.closeSettingsOverlay()" />

  <FloatingPanel
    v-if="isRenameModalOpen"
    title="修改会话名称"
    subtitle="会话标题会优先使用这里的手动命名"
    @close="closeRenameConversation()"
  >
    <div class="settings-modal-stack">
      <label class="form-group">
        <span>会话名称</span>
        <input
          v-model="renameTitle"
          type="text"
          class="form-input"
          maxlength="40"
          placeholder="输入新的会话名称"
          @keydown.enter.prevent="submitRenameConversation()"
        />
      </label>
      <div class="settings-editor-actions">
        <button type="button" class="btn-retry" @click="closeRenameConversation()">取消</button>
        <button type="button" class="btn-save" @click="submitRenameConversation()">确认修改</button>
      </div>
    </div>
  </FloatingPanel>
</template>
