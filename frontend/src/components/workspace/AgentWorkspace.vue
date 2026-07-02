<script setup lang="ts">
import { AlertCircle, Bot, Database, Lightbulb, Loader2, Sparkles, Zap } from '@lucide/vue'
import { useAgentWorkspace } from '../../composables/useAgentWorkspace'
import FloatingPrompt from './FloatingPrompt.vue'

const agent = useAgentWorkspace()

function splitContent(content: string): string[] {
  return content.split('\n').filter(Boolean)
}

const skillIcons: Record<string, typeof Bot> = {
  summarize: Sparkles,
  explain: Lightbulb,
  quiz: Zap,
  generate_cards: Bot,
}
</script>

<template>
  <section class="mode-workspace agent-workspace" aria-label="Agent 工作区">
    <div class="agent-control-strip">
      <div class="agent-capability-picker">
        <label v-for="cap in agent.capabilities.value" :key="cap.id" class="agent-cap-option" :class="{ 'agent-cap-active': cap.id === agent.selectedSkillId.value }">
          <input
            type="radio"
            name="agent-skill"
            :value="cap.id"
            :checked="cap.id === agent.selectedSkillId.value"
            @change="agent.selectedSkillId.value = cap.id"
          />
          <component :is="skillIcons[cap.id] || Bot" :size="16" />
          <span>{{ cap.name }}</span>
        </label>
      </div>
      <div class="agent-kb-select">
        <Database :size="14" />
        <select v-model="agent.selectedKnowledgeBaseId.value" :disabled="agent.isRunning.value">
          <option value="">不参考知识库</option>
          <option v-for="base in agent.knowledgeBases.value" :key="base.id" :value="base.id">{{ base.name }}</option>
        </select>
      </div>
    </div>

    <div class="agent-role-strip">
      <span class="agent-role-label">角色模式</span>
      <label class="agent-role-option" :class="{ 'agent-role-active': !agent.selectedRoleId.value }">
        <input type="radio" name="agent-role" value="" :checked="!agent.selectedRoleId.value" @change="agent.selectedRoleId.value = ''" />
        <span>通用</span>
      </label>
      <label
        v-for="role in agent.roles.value"
        :key="role.id"
        class="agent-role-option"
        :class="{ 'agent-role-active': role.id === agent.selectedRoleId.value }"
      >
        <input type="radio" name="agent-role" :value="role.id" :checked="role.id === agent.selectedRoleId.value" @change="agent.selectedRoleId.value = role.id" />
        <span>{{ role.name }}</span>
      </label>
    </div>

    <p v-if="agent.selectedRole.value" class="agent-role-greeting">{{ agent.selectedRole.value.greeting }}</p>
    <p v-else-if="agent.selectedSkill.value" class="agent-skill-desc">{{ agent.selectedSkill.value.description }}</p>

    <div class="message-stream">
      <p v-if="agent.errorMessage.value" class="chat-error">
        <AlertCircle :size="16" />{{ agent.errorMessage.value }}
      </p>

      <div v-if="!agent.messages.value.length" class="agent-empty">
        <Bot :size="40" />
        <h2>选择一个能力，输入内容开始</h2>
        <p>Agent 模式提供总结、解释、出题、生成卡片等学习专用能力。</p>
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
