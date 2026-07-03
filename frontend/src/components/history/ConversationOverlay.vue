<script setup lang="ts">
import { MessageSquarePlus, PencilLine, Pin, PinOff, Trash2 } from '@lucide/vue'
import FloatingPanel from '../shell/FloatingPanel.vue'
import type { ConversationSession } from '../../types/conversations'
import type { WorkMode } from '../../types/workspace'

defineProps<{
  mode: WorkMode
  conversations: readonly ConversationSession[]
  activeConversationId: string
}>()

const emit = defineEmits<{
  close: []
  selectConversation: [sessionId: string]
  createConversation: []
  togglePinned: [sessionId: string]
  deleteConversation: [sessionId: string]
  requestRenameConversation: [session: ConversationSession]
}>()

function modeLabel(mode: WorkMode) {
  const labels: Record<WorkMode, string> = {
    chat: 'Chat',
    rag: 'RAG',
    agent: 'Agent',
  }
  return labels[mode]
}

function formatUpdatedAt(value: string) {
  return new Date(value).toLocaleString()
}
</script>

<template>
  <FloatingPanel
    :title="`${modeLabel(mode)} 对话历史`"
    subtitle="置顶、切换或删除当前模式下的对话记录"
    size="large"
    @close="emit('close')"
  >
    <div class="conversation-overlay-toolbar">
      <button type="button" class="overlay-primary-button" @click="emit('createConversation')">
        <MessageSquarePlus :size="16" aria-hidden="true" />
        <span>新建对话</span>
      </button>
    </div>

    <div v-if="conversations.length" class="conversation-overlay-list">
      <article
        v-for="session in conversations"
        :key="session.id"
        class="conversation-overlay-item"
        :class="{ 'conversation-overlay-item-active': session.id === activeConversationId }"
        @click="emit('selectConversation', session.id)"
      >
        <div class="conversation-overlay-main">
          <div class="conversation-overlay-meta">
            <strong>{{ session.title }}</strong>
            <time>{{ formatUpdatedAt(session.updatedAt) }}</time>
          </div>
          <p>{{ session.preview || '暂无内容' }}</p>
        </div>
        <div class="conversation-overlay-actions">
          <button type="button" class="conversation-mini-button" aria-label="编辑会话名称" @click.stop="emit('requestRenameConversation', session)">
            <PencilLine :size="14" aria-hidden="true" />
          </button>
          <button type="button" class="conversation-mini-button" :aria-label="session.pinned ? '取消置顶' : '置顶对话'" @click.stop="emit('togglePinned', session.id)">
            <Pin v-if="!session.pinned" :size="14" aria-hidden="true" />
            <PinOff v-else :size="14" aria-hidden="true" />
          </button>
          <button type="button" class="conversation-mini-button" aria-label="删除对话" @click.stop="emit('deleteConversation', session.id)">
            <Trash2 :size="14" aria-hidden="true" />
          </button>
        </div>
      </article>
    </div>

    <div v-else class="conversation-overlay-empty">
      <p>当前模式还没有任何对话，点击上方按钮开始新的会话。</p>
    </div>
  </FloatingPanel>
</template>
