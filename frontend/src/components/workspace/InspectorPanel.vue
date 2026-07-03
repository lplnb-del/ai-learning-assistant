<script setup lang="ts">
import { BookMarked, Bot, Info, SearchX } from '@lucide/vue'
import type { WorkMode } from '../../types/workspace'

interface Props {
  activeMode: WorkMode
}

defineProps<Props>()
</script>

<template>
  <aside class="inspector-panel" aria-label="Inspector Panel">
    <header class="inspector-header">
      <Info :size="17" aria-hidden="true" />
      <span v-if="activeMode === 'chat'">上下文信息</span>
      <span v-else-if="activeMode === 'rag'">检索调试信息</span>
      <span v-else>Agent 工作流监控</span>
    </header>

    <div v-if="activeMode === 'chat'" class="inspector-content">
      <div class="inspector-empty">
        <Bot :size="22" aria-hidden="true" />
        <strong>暂无会话调试信息</strong>
        <p>开始一次真实对话后，这里再展示模型状态和上下文摘要。</p>
      </div>
    </div>

    <div v-else-if="activeMode === 'rag'" class="inspector-content">
      <div class="inspector-empty">
        <SearchX :size="22" aria-hidden="true" />
        <strong>暂无检索调试信息</strong>
        <p>选择知识库并提交问题后，这里再展示真实检索摘要与来源概览。</p>
      </div>
    </div>

    <div v-else class="inspector-content">
      <div class="inspector-empty">
        <BookMarked :size="22" aria-hidden="true" />
        <strong>暂无 Agent 编排日志</strong>
        <p>当前版本先提供技能执行结果，多步骤编排监控会在后续里程碑补齐。</p>
      </div>
    </div>
  </aside>
</template>
