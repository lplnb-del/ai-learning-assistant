<script setup lang="ts">
import { ArrowUp, BookOpen, Mic, Paperclip, Plug, Wrench } from '@lucide/vue'
import type { WorkMode } from '../../types/workspace'

interface Props {
  mode: WorkMode
  canSubmit?: boolean
  isStreaming?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  submit: []
}>()

const model = defineModel<string>({ default: '' })

const placeholders: Record<WorkMode, string> = {
  chat: '输入你想探讨的问题...',
  rag: '继续基于该知识库追问...',
  agent: '输入你想拆解的复杂目标...',
}
</script>

<template>
  <div class="floating-prompt">
    <div class="pill-input">
      <textarea
        v-model="model"
        rows="1"
        :placeholder="placeholders[props.mode]"
        aria-label="输入问题"
        :disabled="props.isStreaming"
        @keydown.enter.exact.prevent="emit('submit')"
      ></textarea>
      <div class="prompt-toolbar">
        <div class="prompt-tools">
          <template v-if="mode === 'chat'">
            <button type="button" aria-label="上传文件"><Paperclip :size="20" /></button>
            <button type="button" aria-label="语音输入"><Mic :size="20" /></button>
          </template>
          <template v-else-if="mode === 'rag'">
            <button type="button" aria-label="查阅全库文档"><BookOpen :size="20" /></button>
          </template>
          <template v-else>
            <button class="prompt-chip" type="button"><Plug :size="16" />MCP Tools</button>
            <button class="prompt-chip" type="button"><Wrench :size="16" />Skills</button>
          </template>
        </div>

        <button class="send-button" type="button" aria-label="发送" :disabled="!props.canSubmit" @click="emit('submit')">
          <ArrowUp :size="20" aria-hidden="true" />
        </button>
      </div>
    </div>
    <p v-if="mode === 'chat'" class="prompt-note">AI 可能会犯错。请核对重要信息。</p>
  </div>
</template>
