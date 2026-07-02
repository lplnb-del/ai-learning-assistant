<script setup lang="ts">
import { Plus } from '@lucide/vue'
import type { QALibraryPayload } from '../../api/cards'
import type { KnowledgeBasePayload } from '../../api/knowledge'

defineProps<{
  selectedLibrary: QALibraryPayload | null
  questionDraft: string
  answerDraft: string
  tagsDraft: string
  cardKnowledgeBaseIdDraft: string
  knowledgeBases: readonly KnowledgeBasePayload[]
  canCreateCard: boolean
}>()

const emit = defineEmits<{
  updateQuestionDraft: [value: string]
  updateAnswerDraft: [value: string]
  updateTagsDraft: [value: string]
  updateCardKnowledgeBaseIdDraft: [value: string]
  createManualCard: []
}>()
</script>

<template>
  <aside class="resource-config card-create-panel">
    <header>录入卡片</header>
    <div class="config-body card-create-form">
      <label>
        保存到问答库
        <div class="readonly-input">{{ selectedLibrary?.name || '请先在左侧新建或选择问答库' }}</div>
      </label>
      <label>
        问题
        <textarea
          :value="questionDraft"
          @input="emit('updateQuestionDraft', String(($event.target as HTMLTextAreaElement).value))"
        />
      </label>
      <label>
        答案
        <textarea
          :value="answerDraft"
          @input="emit('updateAnswerDraft', String(($event.target as HTMLTextAreaElement).value))"
        />
      </label>
      <label>
        关联知识库
        <select
          :value="cardKnowledgeBaseIdDraft"
          @change="emit('updateCardKnowledgeBaseIdDraft', String(($event.target as HTMLSelectElement).value))"
        >
          <option value="">不关联</option>
          <option v-for="base in knowledgeBases" :key="base.id" :value="base.id">{{ base.name }}</option>
        </select>
      </label>
      <label>
        标签
        <input :value="tagsDraft" type="text" @input="emit('updateTagsDraft', String(($event.target as HTMLInputElement).value))" />
      </label>
    </div>
    <footer>
      <button type="button" :disabled="!canCreateCard" @click="emit('createManualCard')">
        <Plus :size="16" />创建卡片
      </button>
    </footer>
  </aside>
</template>
