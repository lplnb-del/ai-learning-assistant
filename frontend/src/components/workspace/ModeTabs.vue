<script setup lang="ts">
import type { ModeTab, WorkMode } from '../../types/workspace'

interface Props {
  tabs: ModeTab[]
  activeMode: WorkMode
}

defineProps<Props>()

const emit = defineEmits<{
  selectMode: [mode: WorkMode]
}>()
</script>

<template>
  <div class="mode-tabs" aria-label="工作模式">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      class="mode-tab"
      :class="{ 'mode-tab-active': tab.id === activeMode }"
      type="button"
      @click="emit('selectMode', tab.id)"
    >
      <component :is="tab.icon" :size="17" aria-hidden="true" />
      <span>{{ tab.label }}</span>
    </button>
  </div>
</template>
