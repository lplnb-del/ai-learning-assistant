<script setup lang="ts">
import { AlertCircle, Check, Database, Layers, MousePointerClick, Trash2 } from '@lucide/vue'
import type { QACardPayload, QALibraryPayload, MasteryLevel } from '../../api/cards'
import type { KnowledgeBasePayload } from '../../api/knowledge'

const props = defineProps<{
  selectedLibrary: QALibraryPayload | null
  cards: readonly QACardPayload[]
  selectedCard: QACardPayload | null
  selectedCardId: string
  selectedKnowledgeBaseId: string
  selectedMastery: MasteryLevel | ''
  tagFilter: string
  cardPosition: number
  isFlipped: boolean
  isSaving: boolean
  errorMessage: string
  successMessage: string
  knowledgeBases: readonly KnowledgeBasePayload[]
}>()

const emit = defineEmits<{
  updateSelectedKnowledgeBaseId: [value: string]
  updateSelectedMastery: [value: MasteryLevel | '']
  updateTagFilter: [value: string]
  applyFilters: []
  selectCard: [cardId: string]
  toggleFlip: []
  removeSelectedCard: []
  setMastery: [mastery: MasteryLevel]
}>()

function splitAnswer(answer: string): string[] {
  return answer.split('\n').filter(Boolean)
}

function knowledgeBaseName(knowledgeBaseId: string | null): string {
  return props.knowledgeBases.find((base) => base.id === knowledgeBaseId)?.name ?? '未关联知识库'
}
</script>

<template>
  <main class="review-stage">
    <header>
      <span>{{ selectedLibrary?.name || '尚未选择问答库' }} · {{ cardPosition }} / {{ cards.length }}</span>
      <button type="button" :disabled="!selectedCard" @click="emit('removeSelectedCard')">
        <Trash2 :size="16" />删除卡片
      </button>
    </header>

    <div class="card-filter-strip stage-filter-strip">
      <select
        :value="selectedKnowledgeBaseId"
        :disabled="isSaving"
        @change="emit('updateSelectedKnowledgeBaseId', String(($event.target as HTMLSelectElement).value))"
      >
        <option value="">全部知识库关联</option>
        <option v-for="base in knowledgeBases" :key="base.id" :value="base.id">{{ base.name }}</option>
      </select>
      <select
        :value="selectedMastery"
        :disabled="isSaving"
        @change="emit('updateSelectedMastery', (($event.target as HTMLSelectElement).value || '') as MasteryLevel | '')"
      >
        <option value="">全部状态</option>
        <option value="new">新卡</option>
        <option value="unsure">模糊</option>
        <option value="mastered">掌握</option>
      </select>
      <input
        :value="tagFilter"
        type="text"
        placeholder="标签筛选"
        @input="emit('updateTagFilter', String(($event.target as HTMLInputElement).value))"
        @keydown.enter="emit('applyFilters')"
      />
      <button type="button" class="inline-filter-button" :disabled="isSaving" @click="emit('applyFilters')">应用筛选</button>
    </div>

    <div v-if="cards.length" class="card-picker-row">
      <button
        v-for="card in cards"
        :key="card.id"
        class="card-chip"
        :class="{ 'card-chip-active': card.id === selectedCardId }"
        type="button"
        @click="emit('selectCard', card.id)"
      >
        {{ card.question }}
      </button>
    </div>

    <p v-if="errorMessage" class="resource-message resource-message-error">
      <AlertCircle :size="15" />{{ errorMessage }}
    </p>
    <p v-if="successMessage" class="resource-message resource-message-success">
      <Check :size="15" />{{ successMessage }}
    </p>

    <div
      v-if="selectedCard"
      class="flashcard"
      :class="{ 'flashcard-flipped': isFlipped }"
      role="button"
      tabindex="0"
      @click="emit('toggleFlip')"
      @keydown.enter="emit('toggleFlip')"
      @keydown.space.prevent="emit('toggleFlip')"
    >
      <div class="flashcard-front">
        <div class="flashcard-meta">
          <span># {{ selectedCard.tags[0] || selectedCard.mastery }}</span>
          <span><Database :size="13" />{{ knowledgeBaseName(selectedCard.knowledge_base_id) }}</span>
        </div>
        <h2>{{ selectedCard.question }}</h2>
        <p><MousePointerClick :size="16" />点击翻转查看答案</p>
      </div>
      <div class="flashcard-back">
        <h3>参考答案</h3>
        <p v-for="line in splitAnswer(selectedCard.answer)" :key="line">{{ line }}</p>
      </div>
    </div>
    <div v-else class="flashcard-empty">
      <Layers :size="34" />
      <h2>这个问答库里还没有可复习的卡片</h2>
      <p>你可以手动创建一张卡片，或者从 RAG 回答里保存到当前问答库。</p>
    </div>

    <div class="memory-actions">
      <button class="score-red" type="button" :disabled="!selectedCard || isSaving" @click="emit('setMastery', 'new')">
        <strong>重来</strong><span>new</span>
      </button>
      <button class="score-yellow" type="button" :disabled="!selectedCard || isSaving" @click="emit('setMastery', 'unsure')">
        <strong>模糊</strong><span>unsure</span>
      </button>
      <button class="score-green" type="button" :disabled="!selectedCard || isSaving" @click="emit('setMastery', 'mastered')">
        <strong>掌握</strong><span>mastered</span>
      </button>
    </div>
  </main>
</template>
