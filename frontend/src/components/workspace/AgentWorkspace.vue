<script setup lang="ts">
import { Loader2, Sparkles } from '@lucide/vue'
import { agentAnswer, agentSteps } from '../../mock/workspace'
import FloatingPrompt from './FloatingPrompt.vue'
</script>

<template>
  <section class="mode-workspace" aria-label="Agent 工作区">
    <div class="message-stream">
      <div class="user-message agent-goal">
        请帮我制定一份“大模型应用开发”的学习路线，并结合知识库中的 RAG 文档补充最新 LangChain 最佳实践。
      </div>

      <div class="agent-timeline">
        <div v-for="step in agentSteps" :key="step.id" class="agent-step" :class="`agent-step-${step.tone}`">
          <div class="agent-step-icon">
            <component :is="step.icon" :size="18" aria-hidden="true" />
          </div>
          <div>
            <p class="agent-step-title">
              {{ step.title }}
              <span :class="['status-badge', `status-${step.status}`]">
                <Loader2 v-if="step.status === 'running'" :size="12" aria-hidden="true" />
                {{ step.status }}
              </span>
            </p>
            <p class="agent-step-detail">{{ step.detail }}</p>
          </div>
        </div>
      </div>

      <article class="assistant-message">
        <div class="assistant-avatar"><Sparkles :size="17" aria-hidden="true" /></div>
        <div class="assistant-content agent-answer">
          <p v-for="line in agentAnswer" :key="line">{{ line }}</p>
          <div class="streaming-dots" aria-label="正在生成">
            <span></span><span></span><span></span>
          </div>
        </div>
      </article>
    </div>
    <FloatingPrompt mode="agent" />
  </section>
</template>
