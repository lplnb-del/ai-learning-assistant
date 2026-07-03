<script setup lang="ts">
import { Archive, MessageSquarePlus, PencilLine, Pin, PinOff, Trash2 } from '@lucide/vue'
import type { ConversationSession } from '../../types/conversations'
import type { WorkMode } from '../../types/workspace'

const props = defineProps<{
  mode: WorkMode
  conversations: readonly ConversationSession[]
  activeConversationId: string
}>()

const emit = defineEmits<{
  createConversation: []
  selectConversation: [sessionId: string]
  togglePinned: [sessionId: string]
  deleteConversation: [sessionId: string]
  requestRenameConversation: [session: ConversationSession]
  openOverlay: []
}>()

function modeLabel(mode: WorkMode) {
  const labels: Record<WorkMode, string> = {
    chat: 'Chat',
    rag: 'RAG',
    agent: 'Agent',
  }
  return labels[mode]
}
</script>

<template>
  <section class="conversation-dock" aria-label="对话历史">
    <header class="conversation-dock-header">
      <div>
        <p class="conversation-dock-title">{{ modeLabel(mode) }} 对话</p>
        <span>{{ conversations.length }} 条</span>
      </div>
      <div class="conversation-dock-actions">
        <button type="button" class="conversation-icon-button" aria-label="展开对话历史" @click="emit('openOverlay')">
          <Archive :size="15" aria-hidden="true" />
        </button>
        <button type="button" class="conversation-icon-button" aria-label="新建对话" @click="emit('createConversation')">
          <MessageSquarePlus :size="15" aria-hidden="true" />
        </button>
      </div>
    </header>

    <div v-if="conversations.length" class="conversation-dock-list">
      <article
        v-for="session in conversations.slice(0, 5)"
        :key="session.id"
        class="conversation-dock-item"
        :class="{ 'conversation-dock-item-active': session.id === activeConversationId }"
        @click="emit('selectConversation', session.id)"
      >
        <div class="conversation-dock-main">
          <strong>{{ session.title }}</strong>
          <span>{{ session.preview || '暂无内容' }}</span>
        </div>
        <div class="conversation-dock-item-actions">
          <button type="button" class="conversation-mini-button" aria-label="编辑会话名称" @click.stop="emit('requestRenameConversation', session)">
            <PencilLine :size="13" aria-hidden="true" />
          </button>
          <button type="button" class="conversation-mini-button" :aria-label="session.pinned ? '取消置顶' : '置顶对话'" @click.stop="emit('togglePinned', session.id)">
            <Pin v-if="!session.pinned" :size="13" aria-hidden="true" />
            <PinOff v-else :size="13" aria-hidden="true" />
          </button>
          <button type="button" class="conversation-mini-button" aria-label="删除对话" @click.stop="emit('deleteConversation', session.id)">
            <Trash2 :size="13" aria-hidden="true" />
          </button>
        </div>
      </article>
    </div>

    <div v-else class="conversation-dock-empty">
      <p>还没有对话，开始一条新的内容吧。</p>
    </div>
  </section>
</template>
