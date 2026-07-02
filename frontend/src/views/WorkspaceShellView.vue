<script setup lang="ts">
import { shallowRef } from 'vue'
import CardsView from '../components/cards/CardsView.vue'
import HistoryView from '../components/history/HistoryView.vue'
import KnowledgeView from '../components/knowledge/KnowledgeView.vue'
import AppShell from '../components/shell/AppShell.vue'
import InspectorPanel from '../components/workspace/InspectorPanel.vue'
import WorkspacePanel from '../components/workspace/WorkspacePanel.vue'
import { navItems } from '../mock/workspace'
import type { MainView, WorkMode } from '../types/workspace'
import { useThemeController } from '../composables/useThemeController'

const activeView = shallowRef<MainView>('workspace')
const activeMode = shallowRef<WorkMode>('chat')
const { resolvedTheme, toggleTheme } = useThemeController()

function selectView(view: MainView) {
  activeView.value = view
}

function selectMode(mode: WorkMode) {
  activeMode.value = mode
}
</script>

<template>
  <AppShell
    :items="navItems"
    :active-view="activeView"
    :resolved-theme="resolvedTheme"
    @select-view="selectView"
    @toggle-theme="toggleTheme"
  >
    <template v-if="activeView === 'workspace'">
      <WorkspacePanel :active-mode="activeMode" @select-mode="selectMode" />
      <InspectorPanel :active-mode="activeMode" />
    </template>

    <KnowledgeView v-else-if="activeView === 'knowledge'" />
    <CardsView v-else-if="activeView === 'cards'" />
    <HistoryView v-else />
  </AppShell>
</template>
