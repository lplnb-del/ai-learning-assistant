<script setup lang="ts">
import { Layers, Plus, RefreshCw, Trash2 } from '@lucide/vue'
import type { QALibraryPayload } from '../../api/cards'

defineProps<{
  libraries: readonly QALibraryPayload[]
  selectedLibraryId: string
  libraryNameDraft: string
  libraryDescriptionDraft: string
  isLoading: boolean
  isSaving: boolean
  canCreateLibrary: boolean
}>()

const emit = defineEmits<{
  selectLibrary: [libraryId: string]
  updateLibraryNameDraft: [value: string]
  updateLibraryDescriptionDraft: [value: string]
  createLibrary: []
  removeSelectedLibrary: []
  refresh: []
}>()
</script>

<template>
  <aside class="resource-sidebar cards-sidebar">
    <header>
      <span>问答库</span>
      <button type="button" aria-label="刷新问答库" :disabled="isLoading" @click="emit('refresh')">
        <RefreshCw :size="16" />
      </button>
    </header>

    <div class="base-create-form">
      <input
        :value="libraryNameDraft"
        type="text"
        placeholder="新建问答库名称"
        @input="emit('updateLibraryNameDraft', String(($event.target as HTMLInputElement).value))"
      />
      <input
        :value="libraryDescriptionDraft"
        type="text"
        placeholder="用途说明"
        @input="emit('updateLibraryDescriptionDraft', String(($event.target as HTMLInputElement).value))"
      />
      <button type="button" class="sidebar-primary-button" :disabled="!canCreateLibrary" @click="emit('createLibrary')">
        <Plus :size="16" />新建问答库
      </button>
    </div>

    <button
      v-for="library in libraries"
      :key="library.id"
      class="resource-nav-button card-nav-button"
      :class="{ 'resource-nav-active': library.id === selectedLibraryId }"
      type="button"
      @click="emit('selectLibrary', library.id)"
    >
      <Layers :size="17" />
      <span>{{ library.name }}</span>
      <code>{{ library.description || '问答库' }}</code>
    </button>

    <button
      v-if="selectedLibraryId"
      type="button"
      class="sidebar-danger-button"
      :disabled="isSaving"
      @click="emit('removeSelectedLibrary')"
    >
      <Trash2 :size="15" />删除当前问答库
    </button>

    <p v-if="!libraries.length" class="resource-empty-text">先建一个问答库，再开始沉淀卡片。</p>
  </aside>
</template>
