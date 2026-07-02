<script setup lang="ts">
import { Clock3, ScrollText } from '@lucide/vue'
</script>

<template>
  <section class="history-view" aria-label="问答历史">
    <div class="history-empty">
      <ScrollText :size="34" aria-hidden="true" />
      <h2>问答历史</h2>
      <p>这里后续会汇总 Chat、RAG 和 Agent 的历史记录。</p>
      <span><Clock3 :size="14" />等待后端存储接入</span>
    </div>
  </section>
</template>
