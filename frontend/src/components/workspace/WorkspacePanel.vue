<script setup lang="ts">
import type { WorkMode } from '../../types/workspace'
import AgentWorkspace from './AgentWorkspace.vue'
import ChatWorkspace from './ChatWorkspace.vue'
import ModeTopBar from './ModeTopBar.vue'
import RagWorkspace from './RagWorkspace.vue'

interface Props {
  activeMode: WorkMode
}

defineProps<Props>()

const emit = defineEmits<{
  selectMode: [mode: WorkMode]
  createConversation: []
}>()
</script>

<template>
  <section class="workspace-surface" aria-label="AI 推理台">
    <ModeTopBar
      :active-mode="activeMode"
      @select-mode="emit('selectMode', $event)"
      @create-conversation="emit('createConversation')"
    />
    <ChatWorkspace v-if="activeMode === 'chat'" />
    <RagWorkspace v-else-if="activeMode === 'rag'" />
    <AgentWorkspace v-else />
  </section>
</template>
