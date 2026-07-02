<script setup lang="ts">
import SidebarNav from './SidebarNav.vue'
import type { MainView, NavItem } from '../../types/workspace'

interface Props {
  items: NavItem[]
  activeView: MainView
  resolvedTheme: 'light' | 'dark'
}

defineProps<Props>()

const emit = defineEmits<{
  selectView: [view: MainView]
  toggleTheme: []
}>()
</script>

<template>
  <div class="app-shell">
    <SidebarNav
      :items="items"
      :active-view="activeView"
      :resolved-theme="resolvedTheme"
      @select-view="emit('selectView', $event)"
      @toggle-theme="emit('toggleTheme')"
    />
    <main class="workspace-frame">
      <slot />
    </main>
  </div>
</template>
