<script setup lang="ts">
import { Plus, Save } from '@lucide/vue'
import type { QALibraryPayload } from '../../api/cards'

defineProps<{
  libraries: readonly QALibraryPayload[]
  selectedLibraryId: string
  newLibraryName: string
  newLibraryDescription: string
  isSaving: boolean
}>()

const emit = defineEmits<{
  updateSelectedLibraryId: [value: string]
  updateNewLibraryName: [value: string]
  updateNewLibraryDescription: [value: string]
  save: []
}>()
</script>

<template>
  <div class="rag-save-panel">
    <label>
      保存到问答库
      <select
        :value="selectedLibraryId"
        :disabled="isSaving"
        @change="emit('updateSelectedLibraryId', String(($event.target as HTMLSelectElement).value))"
      >
        <option value="">请选择已有问答库</option>
        <option v-for="library in libraries" :key="library.id" :value="library.id">{{ library.name }}</option>
      </select>
    </label>

    <div class="rag-save-divider">或者直接新建</div>

    <label>
      新问答库名称
      <input
        :value="newLibraryName"
        type="text"
        placeholder="例如：RAG 面试问答"
        @input="emit('updateNewLibraryName', String(($event.target as HTMLInputElement).value))"
      />
    </label>
    <label>
      用途说明
      <input
        :value="newLibraryDescription"
        type="text"
        placeholder="例如：沉淀可直接复述的标准答案"
        @input="emit('updateNewLibraryDescription', String(($event.target as HTMLInputElement).value))"
      />
    </label>

    <button type="button" :disabled="isSaving" @click="emit('save')">
      <Save :size="15" />
      <Plus :size="14" />
      保存这条回答
    </button>
  </div>
</template>
