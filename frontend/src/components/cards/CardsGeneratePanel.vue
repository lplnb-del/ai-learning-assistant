<script setup lang="ts">
import { Sparkles, FileText, CheckSquare, Square } from '@lucide/vue'
import type { KnowledgeBasePayload, SourceDocumentPayload, ChunkPayload } from '../../api/knowledge'

defineProps<{
  knowledgeBases: readonly KnowledgeBasePayload[]
  availableDocuments: readonly SourceDocumentPayload[]
  availableChunks: readonly ChunkPayload[]
  selectedChunkIds: readonly string[]
  generateKnowledgeBaseId: string
  generateDocumentId: string
  generateTagsDraft: string
  isGenerating: boolean
  canGenerateFromDocument: boolean
  canGenerateFromChunks: boolean
}>()

const emit = defineEmits<{
  updateGenerateKnowledgeBaseId: [value: string]
  updateGenerateDocumentId: [value: string]
  updateGenerateTagsDraft: [value: string]
  loadDocuments: []
  loadChunks: []
  toggleChunkSelection: [chunkId: string]
  selectAllChunks: []
  clearChunkSelection: []
  generateFromDocument: []
  generateFromChunks: []
}>()
</script>

<template>
  <aside class="resource-config cards-generate-panel">
    <header>批量生成卡片</header>
    <div class="config-body card-generate-form">
      <label>
        选择知识库
        <select
          :value="generateKnowledgeBaseId"
          :disabled="isGenerating"
          @change="emit('updateGenerateKnowledgeBaseId', String(($event.target as HTMLSelectElement).value)); emit('loadDocuments')"
        >
          <option value="">请选择知识库</option>
          <option v-for="base in knowledgeBases" :key="base.id" :value="base.id">{{ base.name }}</option>
        </select>
      </label>
      <label v-if="availableDocuments.length">
        选择文档
        <select
          :value="generateDocumentId"
          :disabled="isGenerating"
          @change="emit('updateGenerateDocumentId', String(($event.target as HTMLSelectElement).value)); emit('loadChunks')"
        >
          <option v-for="doc in availableDocuments" :key="doc.id" :value="doc.id">{{ doc.name }}</option>
        </select>
      </label>
      <label>
        标签（逗号分隔）
        <input :value="generateTagsDraft" type="text" placeholder="例：RAG, 面试" @input="emit('updateGenerateTagsDraft', String(($event.target as HTMLInputElement).value))" />
      </label>

      <div v-if="availableChunks.length" class="chunk-selector">
        <div class="chunk-selector-header">
          <span>选择切片（{{ selectedChunkIds.length }} / {{ availableChunks.length }}）</span>
          <div class="chunk-selector-actions">
            <button type="button" class="chunk-action-btn" :disabled="isGenerating" @click="emit('selectAllChunks')">全选</button>
            <button type="button" class="chunk-action-btn" :disabled="isGenerating" @click="emit('clearChunkSelection')">清空</button>
          </div>
        </div>
        <div class="chunk-list">
          <button
            v-for="chunk in availableChunks"
            :key="chunk.id"
            class="chunk-item"
            :class="{ 'chunk-item-selected': selectedChunkIds.includes(chunk.id) }"
            type="button"
            :disabled="isGenerating"
            @click="emit('toggleChunkSelection', chunk.id)"
          >
            <component :is="selectedChunkIds.includes(chunk.id) ? CheckSquare : Square" :size="14" />
            <span class="chunk-title">{{ chunk.title || `切片 #${chunk.index + 1}` }}</span>
            <span class="chunk-preview">{{ chunk.text.slice(0, 80) }}...</span>
          </button>
        </div>
      </div>
    </div>
    <footer>
      <button type="button" :disabled="!canGenerateFromDocument || isGenerating" @click="emit('generateFromDocument')">
        <FileText :size="16" />从整篇文档生成
      </button>
      <button type="button" :disabled="!canGenerateFromChunks || isGenerating" @click="emit('generateFromChunks')">
        <Sparkles :size="16" />从选中切片生成
      </button>
    </footer>
  </aside>
</template>
