<script setup lang="ts">
import { AlertCircle, Bot, Database, Loader2, Sparkles, Zap } from '@lucide/vue'
import { useAgentWorkspace } from '../../composables/useAgentWorkspace'
import FloatingPrompt from './FloatingPrompt.vue'
import PillSelect from './PillSelect.vue'

const agent = useAgentWorkspace()

function splitContent(content: string): string[] {
  return content.split('\n').filter(Boolean)
}
</script>

<template>
  <section class="mode-workspace agent-workspace" aria-label="Agent 工作区">
    <div class="agent-control-strip">
      <div class="agent-capability-picker">
        <label
          v-for="role in agent.roles.value"
          :key="role.id"
          class="agent-cap-option"
          :class="{ 'agent-cap-active': role.id === agent.selectedRoleId.value }"
        >
          <input
            type="radio"
            name="agent-role"
            :value="role.id"
            :checked="role.id === agent.selectedRoleId.value"
            @change="agent.selectedRoleId.value = role.id"
          />
          <Bot :size="16" />
          <span>{{ role.name }}</span>
        </label>
      </div>
      <div class="agent-toolbar-pickers">
        <div class="agent-kb-select">
          <Database :size="14" />
          <PillSelect
            v-model="agent.selectedKnowledgeBaseId.value"
            label="Agent 知识库"
            :options="[
              { value: '', label: '不参考知识库' },
              ...agent.knowledgeBases.value.map((base) => ({ value: base.id, label: base.name })),
            ]"
            :disabled="agent.isRunning.value"
          />
        </div>
      </div>
    </div>

    <p v-if="agent.selectedRole.value" class="agent-role-greeting">{{ agent.selectedRole.value.description }}</p>

    <div class="message-stream">
      <p v-if="agent.errorMessage.value" class="chat-error">
        <AlertCircle :size="16" />{{ agent.errorMessage.value }}
      </p>

      <div v-if="!agent.messages.value.length" class="agent-empty">
        <Bot :size="40" />
        <h2>选择一个角色，输入任务开始</h2>
        <p>Agent 模式现在按角色系统提示词工作，适合学习规划、面试模拟、练习设计和资料整理。</p>
      </div>

      <template v-for="message in agent.messages.value" :key="message.id">
        <div v-if="message.role === 'user'" class="user-message">{{ message.content }}</div>
        <article v-else class="assistant-message">
          <div class="assistant-avatar"><Sparkles :size="17" /></div>
          <div class="assistant-content">
            <div v-if="message.skillName" class="thinking-pill">
              <Zap :size="14" />{{ message.skillName }}
              <span v-if="message.contextUsed" class="context-badge">已参考知识库</span>
            </div>
            <p v-for="(line, i) in splitContent(message.content)" :key="`${message.id}-${i}`">{{ line }}</p>
          </div>
        </article>
      </template>

      <div v-if="agent.isRunning.value" class="thinking-pill">
        <Loader2 :size="14" class="spin" />正在执行...
      </div>
    </div>

    <FloatingPrompt
      v-model="agent.input.value"
      mode="agent"
      :can-submit="agent.canSubmit.value"
      :is-streaming="agent.isRunning.value"
      @submit="agent.submit"
    />
  </section>
</template>
