<script setup lang="ts">
import { AlertCircle, Check, Sparkles } from '@lucide/vue'
import PillSelect from './PillSelect.vue'
import { useChatStream } from '../../composables/useChatStream'
import FloatingPrompt from './FloatingPrompt.vue'

const {
  messages,
  input,
  errorMessage,
  isStreaming,
  temperature,
  model,
  thinkingDepth,
  keepContext,
  webSearch,
  canSubmit,
  lastAssistantStatus,
  availableModels,
  submit,
  setThinkingDepth,
  toggleKeepContext,
  toggleWebSearch,
} = useChatStream()
</script>

<template>
  <section class="mode-workspace chat-workspace" aria-label="Chat 工作区">
    <div class="message-stream">
      <div v-if="!messages.length && !isStreaming && !errorMessage" class="workspace-empty">
        <Sparkles :size="30" aria-hidden="true" />
        <h2>开始一段新对话</h2>
        <p>输入你的问题，模型回复会从这里开始累计。</p>
      </div>

      <article
        v-for="message in messages"
        :key="message.id"
        :class="message.role === 'user' ? 'user-message' : 'assistant-message'"
      >
        <template v-if="message.role === 'user'">
          {{ message.content }}
        </template>
        <template v-else>
          <div class="assistant-avatar"><Sparkles :size="17" aria-hidden="true" /></div>
          <div class="assistant-content">
            <p>{{ message.content || '...' }}</p>
            <div v-if="message.status" class="chat-status-line">
              <Check v-if="message.status.includes('完成')" :size="15" aria-hidden="true" />
              <span v-else class="ai-dot"></span>
              {{ message.status }}
            </div>
          </div>
        </template>
      </article>

      <div v-if="isStreaming" class="thinking-pill">
        <span class="ai-dot"></span>
        {{ lastAssistantStatus }}
      </div>

      <div v-if="errorMessage" class="chat-error">
        <AlertCircle :size="17" aria-hidden="true" />
        {{ errorMessage }}
      </div>
    </div>
    <div class="chat-control-strip" aria-label="Chat 设置">
      <label>
        <span>模型</span>
        <PillSelect v-model="model" label="模型" :options="availableModels" :disabled="isStreaming" />
      </label>
      <div class="segmented-control" aria-label="思考深度">
        <button
          v-for="depth in ['快速', '标准', '深度']"
          :key="depth"
          type="button"
          :class="{ 'segment-active': thinkingDepth === depth }"
          :disabled="isStreaming"
          @click="setThinkingDepth(depth)"
        >
          {{ depth }}
        </button>
      </div>
      <label class="range-control">
        <span>温度 {{ temperature.toFixed(1) }}</span>
        <input v-model.number="temperature" type="range" min="0" max="2" step="0.1" :disabled="isStreaming" />
      </label>
      <label class="toggle-control">
        <input type="checkbox" :checked="keepContext" :disabled="isStreaming" @change="toggleKeepContext" />
        <span>上下文</span>
      </label>
      <label class="toggle-control">
        <input type="checkbox" :checked="webSearch" :disabled="isStreaming" @change="toggleWebSearch" />
        <span>联网</span>
      </label>
    </div>
    <FloatingPrompt
      v-model="input"
      mode="chat"
      :can-submit="canSubmit"
      :is-streaming="isStreaming"
      @submit="submit"
    />
  </section>
</template>
