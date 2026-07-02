<script setup lang="ts">
import { AlertCircle, BrainCog, Check, DatabaseZap, Sparkles } from '@lucide/vue'
import { computed } from 'vue'
import { useRagWorkspace } from '../../composables/useRagWorkspace'
import PillSelect from './PillSelect.vue'
import FloatingPrompt from './FloatingPrompt.vue'

const rag = useRagWorkspace()
const knowledgeBaseOptions = computed(() =>
  rag.knowledgeBases.value.map((base) => ({
    value: base.id,
    label: base.name,
  })),
)

function splitMessageContent(content: string): string[] {
  return content.split('\n').filter(Boolean)
}
</script>

<template>
  <section class="mode-workspace rag-workspace" aria-label="RAG 工作区">
    <div class="rag-control-strip">
      <label>
        知识库
        <PillSelect
          v-model="rag.selectedKnowledgeBaseId.value"
          label="知识库"
          :options="knowledgeBaseOptions"
          placeholder="请选择"
          :disabled="rag.isLoadingBases.value || rag.isAsking.value"
        />
      </label>
      <label>
        Top K
        <input v-model.number="rag.topK.value" type="number" min="1" max="8" :disabled="rag.isAsking.value" />
      </label>
      <span>{{ rag.selectedKnowledgeBase.value?.description || '本地 chunk 检索' }}</span>
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
              <h3>基于知识库的回答</h3>
              <p v-for="(line, lineIndex) in splitMessageContent(message.content)" :key="`${message.id}-${lineIndex}`">
                {{ line }}
              </p>
              <div v-if="message.sources?.length" class="rag-source-list">
                <article v-for="(source, index) in message.sources" :key="source.chunk_id" class="rag-source-item">
                  <strong>[{{ index + 1 }}] {{ source.document_name }}</strong>
                  <span>#{{ source.chunk_index + 1 }} · score {{ source.score.toFixed(1) }}</span>
                  <p>{{ source.excerpt }}</p>
                </article>
              </div>
              <div class="rag-actions">
                <button type="button"><BrainCog :size="17" />保存为 QA 记忆卡片</button>
                <span><Check :size="14" />来源片段可追溯</span>
              </div>
            </div>
          </article>
        </template>
      </template>
    </div>
    <FloatingPrompt v-model="rag.input.value" mode="rag" :can-submit="rag.canSubmit.value" :is-streaming="rag.isAsking.value" @submit="rag.submit" />
  </section>
</template>
