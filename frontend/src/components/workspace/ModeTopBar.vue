<script setup lang="ts">
import { MessageSquarePlus } from '@lucide/vue'
import { modeTabs } from '../../config/workspace'
import type { WorkMode } from '../../types/workspace'
import ModeTabs from './ModeTabs.vue'

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
  <header class="workspace-topbar">
    <ModeTabs :tabs="modeTabs" :active-mode="activeMode" @select-mode="emit('selectMode', $event)" />
    <button class="workspace-action-button" type="button" @click="emit('createConversation')">
      <MessageSquarePlus :size="16" aria-hidden="true" />
      <span>新建对话</span>
    </button>
  </header>
</template>
