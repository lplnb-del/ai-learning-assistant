<script setup lang="ts">
import { ChevronDown } from '@lucide/vue'
import { modeSettings, modeTabs } from '../../mock/workspace'
import type { WorkMode } from '../../types/workspace'
import ModeTabs from './ModeTabs.vue'

interface Props {
  activeMode: WorkMode
}

defineProps<Props>()

const emit = defineEmits<{
  selectMode: [mode: WorkMode]
}>()
</script>

<template>
  <header class="workspace-topbar">
    <ModeTabs :tabs="modeTabs" :active-mode="activeMode" @select-mode="emit('selectMode', $event)" />

    <div class="mode-settings" :class="`mode-settings-${activeMode}`">
      <button v-for="setting in modeSettings[activeMode]" :key="setting.label" class="mode-setting-button" type="button">
        <component :is="setting.icon" :size="16" aria-hidden="true" />
        <span>{{ setting.label }}</span>
        <ChevronDown v-if="activeMode !== 'agent'" :size="14" aria-hidden="true" />
      </button>
    </div>
  </header>
</template>
