<script setup lang="ts">
import { Check, FileText, Globe, History, Info, Settings2, TextQuote } from '@lucide/vue'
import { chatSources, ragSources } from '../../mock/workspace'
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
      <section class="inspector-section">
        <p class="section-label">当前会话状态</p>
        <div class="metric-card">
          <span>模型</span><strong>DeepSeek-V3</strong>
          <span>消耗 Tokens</span><strong>1,248</strong>
          <span>ID</span><code>cht_8f2a9x</code>
        </div>
      </section>

      <section class="inspector-section">
        <p class="section-label"><Globe :size="14" />联网来源 (3)</p>
        <article v-for="source in chatSources" :key="source.id" class="source-card">
          <strong>{{ source.title }}</strong>
          <span>{{ source.source }}</span>
          <p>{{ source.excerpt }}</p>
        </article>
      </section>
    </div>

    <div v-else-if="activeMode === 'rag'" class="inspector-content">
      <section class="inspector-section">
        <p class="section-label section-between">检索策略 <Settings2 :size="14" /></p>
        <div class="metric-card">
          <span>Top K</span><strong>3 个片段</strong>
          <span>Rerank 重排</span><strong class="success-text">BGE-Reranker</strong>
        </div>
      </section>

      <section class="inspector-section">
        <p class="section-label"><TextQuote :size="14" />引用来源 (2)</p>
        <article v-for="source in ragSources" :key="source.id" class="chunk-card">
          <div class="chunk-header">
            <span><FileText :size="13" />{{ source.title }}</span>
            <strong>{{ source.score }}</strong>
          </div>
          <p>{{ source.excerpt }}</p>
          <footer><code>{{ source.source }}</code><mark>{{ source.marker }}</mark></footer>
        </article>
      </section>
    </div>

    <div v-else class="inspector-content">
      <section class="inspector-section">
        <p class="section-label">编排器状态</p>
        <pre class="json-card">{"status":"running"}
{
  "current_node": "subagent_educator",
  "steps_completed": 3,
  "tools_called": ["rag_search", "web_search"]
}</pre>
      </section>

      <section class="inspector-section">
        <p class="section-label"><History :size="14" />工具执行日志</p>
        <div class="tool-log">
          <article>
            <Check :size="13" />
            <div><strong>WebSearch: LangChain LCEL</strong><span>获取到 4620 tokens 网页文本内容</span></div>
          </article>
          <article>
            <Check :size="13" />
            <div><strong>RAG: Backend Guide</strong><span>成功检索，置信度得分 0.89</span></div>
          </article>
        </div>
      </section>
    </div>
  </aside>
</template>
