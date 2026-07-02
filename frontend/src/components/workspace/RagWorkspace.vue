<script setup lang="ts">
import { AlertCircle, BookMarked, BrainCog, Check, DatabaseZap, Library, Sparkles } from '@lucide/vue'
import { useRagWorkspace } from '../../composables/useRagWorkspace'
import FloatingPrompt from './FloatingPrompt.vue'
import RagSaveCardPanel from './RagSaveCardPanel.vue'

const rag = useRagWorkspace()


function splitMessageContent(content: string): string[] {
  return content.split('\n').filter(Boolean)
}

function sourceTypeLabel(sourceType: string): string {
  return sourceType === 'qa_card' ? '问答库' : '知识库'
}
</script>

<template>
  <section class="mode-workspace rag-workspace" aria-label="RAG 工作区">
    <div class="rag-control-strip">
      <div class="rag-kb-picker">
        <button type="button" class="rag-library-toggle" :disabled="rag.isLoadingBases.value || rag.isAsking.value" @click="rag.toggleQaLibraryPicker">
          <DatabaseZap :size="14" />
          {{ rag.selectedKnowledgeBases.value.length ? `知识库 ${rag.selectedKnowledgeBases.value.length} 已选` : '选择知识库' }}
        </button>
      </div>
      <label>
        Top K
        <input v-model.number="rag.topK.value" type="number" min="1" max="8" :disabled="rag.isAsking.value" />
      </label>
      <button type="button" class="rag-library-toggle" :disabled="rag.isAsking.value" @click="rag.toggleQaLibraryPicker">
        <BookMarked :size="14" />
        {{ rag.selectedQaLibraries.value.length ? `问答库 ${rag.selectedQaLibraries.value.length} 已选` : '选择问答库' }}
      </button>
      <span>{{ rag.selectedKnowledgeBases.value.length ? `跨 ${rag.selectedKnowledgeBases.value.length} 个知识库联合检索` : '本地混合检索：知识库 + 问答库' }}</span>
    </div>

    <div v-if="rag.isQaLibraryPickerOpen.value" class="rag-qa-library-panel">
      <header>
        <strong>选择知识库</strong>
        <span>可多选，跨库联合检索</span>
      </header>
      <label v-for="base in rag.knowledgeBases.value" :key="base.id" class="rag-qa-library-option">
        <input
          type="checkbox"
          :checked="rag.selectedKnowledgeBaseIds.value.includes(base.id)"
          :disabled="rag.isAsking.value"
          @change="rag.toggleKnowledgeBaseSelection(base.id)"
        />
        <span>{{ base.name }}</span>
        <small>{{ base.description || '知识库' }}</small>
      </label>
      <header style="margin-top: 10px;">
        <strong>参与参考的问答库</strong>
        <span>可多选，适合加入高频标准答案与面试表达</span>
      </header>
      <label v-for="library in rag.qaLibraries.value" :key="library.id" class="rag-qa-library-option">
        <input
          type="checkbox"
          :checked="rag.selectedQaLibraryIds.value.includes(library.id)"
          @change="rag.toggleQaLibrarySelection(library.id)"
        />
        <span>{{ library.name }}</span>
        <small>{{ library.description || '问答库' }}</small>
      </label>
      <p v-if="!rag.qaLibraries.value.length" class="resource-empty-text">还没有问答库，可先到 QA 卡片页创建。</p>
    </div>

    <div class="message-stream">
      <div class="rag-demo-questions" aria-label="RAG 演示问题">
        <button
          v-for="question in rag.demoQuestions"
          :key="question"
          type="button"
          :disabled="rag.isAsking.value"
          @click="rag.useDemoQuestion(question)"
        >
          {{ question }}
        </button>
      </div>

      <p v-if="rag.errorMessage.value" class="chat-error">
        <AlertCircle :size="16" />{{ rag.errorMessage.value }}
      </p>
      <p v-if="rag.cardMessage.value" class="resource-message resource-message-success">
        <Check :size="14" />{{ rag.cardMessage.value }}
      </p>

      <template v-for="message in rag.messages.value" :key="message.id">
        <div v-if="message.role === 'user'" class="user-message">{{ message.content }}</div>

        <template v-else>
          <div v-if="message.status" class="thinking-pill">
            <DatabaseZap :size="15" aria-hidden="true" />
            {{ message.status }}
          </div>

          <article class="assistant-message">
            <div class="assistant-avatar"><Sparkles :size="17" aria-hidden="true" /></div>
            <div class="assistant-content">
              <h3>基于知识库与问答库的回答</h3>
              <p v-for="(line, lineIndex) in splitMessageContent(message.content)" :key="`${message.id}-${lineIndex}`">
                {{ line }}
              </p>
              <div v-if="message.sources?.length" class="rag-source-list">
                <article v-for="(source, index) in message.sources" :key="source.chunk_id" class="rag-source-item">
                  <strong>[{{ index + 1 }}] {{ source.document_name }}</strong>
                  <span>{{ sourceTypeLabel(source.source_type) }} · {{ source.title || `#${source.chunk_index + 1}` }} · score {{ source.score.toFixed(1) }}</span>
                  <p>{{ source.excerpt }}</p>
                </article>
              </div>
              <div class="rag-actions">
                <button
                  type="button"
                  :disabled="rag.isSavingCard.value || Boolean(message.savedCardId) || !message.question"
                  @click="rag.openSavePanel(message.id)"
                >
                  <BrainCog :size="17" />{{ message.savedCardId ? '已保存到问答库' : '保存为问答库卡片' }}
                </button>
                <span><Library :size="14" />可混合参考知识库与问答库</span>
              </div>
              <RagSaveCardPanel
                v-if="rag.activeSaveMessageId.value === message.id && !message.savedCardId"
                :libraries="rag.qaLibraries.value"
                :selected-library-id="rag.saveCardLibraryId.value"
                :new-library-name="rag.saveCardNewLibraryName.value"
                :new-library-description="rag.saveCardNewLibraryDescription.value"
                :is-saving="rag.isSavingCard.value"
                @update-selected-library-id="rag.saveCardLibraryId.value = $event"
                @update-new-library-name="rag.saveCardNewLibraryName.value = $event"
                @update-new-library-description="rag.saveCardNewLibraryDescription.value = $event"
                @save="rag.saveAsCard(message.id)"
              />
            </div>
          </article>
        </template>
      </template>
    </div>
    <FloatingPrompt
      v-model="rag.input.value"
      mode="rag"
      :can-submit="rag.canSubmit.value"
      :is-streaming="rag.isAsking.value"
      @submit="rag.submit"
    />
  </section>
</template>
